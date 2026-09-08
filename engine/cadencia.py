# -*- coding: utf-8 -*-
"""Um download por vez na maquina inteira, com intervalo entre TODOS eles.

Ordem do Bryan em 08/09/2026:

    "Os downloads nunca podem coincidir de nenhum canal. Sempre respeitando
     intervalos para que a gente nunca perca esse privilegio que acabamos de
     conseguir. Crie uma guarda infalivel pra isso."

O privilegio e' concreto e foi MEDIDO no mesmo dia: esta maquina baixa do
YouTube sem espera, sem CAPTCHA e sem 429 — 85 MB em ~1 minuto. O runner do
GitHub nao consegue (IP de datacenter), e e' por isso que o `cortar.yml`
nunca teve um success na vida. Se este IP for degradado, o projeto perde o
UNICO caminho de download que funciona, e nao ha' plano B.

## POR QUE A GUARDA NAO PODE MORAR NO LACO

O `baixar_em_intervalos` ja' espera entre um video e o seguinte. Isso protege
UMA rodada, e so'. Nao protege:

  - duas rodadas de canais diferentes disparadas em sequencia pelo
    `ciclo_semanal --todos` (era exatamente o caso, e por isso esta guarda
    nasceu);
  - a tarefa agendada rodando enquanto alguem baixa a mao;
  - dois processos simultaneos por engano;
  - qualquer chamador NOVO que ainda nao existe.

Por isso a trava vive no ponto por onde TODO download passa, e nao em quem
chama. Quem chama nao precisa saber que ela existe — e' o unico jeito de ela
nao ser contornada sem querer.

## AS DUAS GARANTIAS

    EXCLUSAO   um download por vez na maquina, entre processos. Arquivo de
               trava com o PID de quem segura.
    INTERVALO  espera minima entre o FIM de um download e o INICIO do
               proximo, seja qual for o canal. Carimbo global em disco.

⚠️ "INFALIVEL" NAO EXISTE, e prometer isso seria pior que nao ter guarda.
O que da' pra garantir e' que ela FALHA FECHADA: em toda duvida, ela ESPERA
em vez de baixar.

  - estado ilegivel ou corrompido -> trata como "acabei de baixar agora" e
    espera o intervalo inteiro;
  - relogio pra tras (o carimbo esta' no futuro) -> espera o intervalo
    inteiro, em vez de concluir "ja' passou tempo demais";
  - trava presa por processo que morreu -> so' e' tomada quando o PID
    comprovadamente nao existe mais, e ainda assim respeitando o intervalo.

O caso que ela NAO cobre: outro programa nesta maquina baixando do YouTube
por fora do projeto. Nenhuma trava daqui alcanca isso.
"""
from __future__ import annotations

import json
import os
import random
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESTADO = RAIZ / "estado" / "cadencia_download.json"
TRAVA = RAIZ / "estado" / "cadencia_download.lock"

# Intervalo minimo entre QUALQUER par de downloads, de qualquer canal.
#
# ⚠️ O NUMERO NAO E' MEDIDO — nao houve bloqueio pra calibrar contra. Vem da
# ordem de grandeza que funcionou com as 40+ legendas do projeto do livro, e
# e' o mesmo padrao do `baixar_em_intervalos`. Se um dia aparecer um 429 de
# verdade, ESTE e' o numero pra subir, e ai' ele passa a ser medido.
INTERVALO_S = 180

# Sorteio em cima do intervalo. Cadencia exata e' assinatura de robo: o
# proprio ritmo constante denuncia, mesmo sendo lento.
JITTER = 0.30

# Quanto esperar pela trava antes de desistir. Uma rodada de 5 videos leva
# ~15 min; 40 min cobre isso com folga e ainda impede espera eterna.
ESPERA_MAX_TRAVA_S = 2400

# De quanto em quanto tempo reconferir se a trava vagou.
SONDA_S = 5


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _vivo(pid: int) -> bool:
    """O processo ainda existe?

    ⚠️ NA DUVIDA, RESPONDE QUE SIM. Dizer "morreu" sobre um processo vivo
    libera a trava e produz exatamente o download simultaneo que esta guarda
    existe pra impedir. O custo do erro contrario e' esperar demais.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True          # existe, mas e' de outro usuario
    except OSError:
        return False
    except Exception:
        return True          # nao sei -> considero vivo


def _ler_estado() -> dict:
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _quando_foi_o_ultimo() -> datetime | None:
    """Fim do ultimo download. None quando nao da' pra saber."""
    d = _ler_estado()
    try:
        q = datetime.fromisoformat(str(d["ultimo"]).replace("Z", "+00:00"))
    except Exception:
        return None
    return q if q.tzinfo else q.replace(tzinfo=timezone.utc)


def _gravar_fim(canal: str) -> None:
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(
        {"ultimo": _agora().isoformat(timespec="seconds"),
         "por": canal or "?", "pid": os.getpid()},
        ensure_ascii=False, indent=1), encoding="utf-8")


def espera_devida() -> float:
    """Quantos segundos ainda faltam pra poder baixar. 0 = pode agora."""
    alvo = INTERVALO_S * (1 + random.uniform(-JITTER, JITTER))
    ultimo = _quando_foi_o_ultimo()
    if ultimo is None:
        # ⚠️ Sem carimbo legivel, o seguro e' assumir que acabou de haver um
        # download. Nunca "nunca houve" — essa leitura otimista e' a que
        # produz duas rodadas coladas depois de um estado corrompido.
        return alvo if ESTADO.exists() else 0.0
    passou = (_agora() - ultimo).total_seconds()
    if passou < 0:
        # Carimbo no futuro: relogio mexeu. Espera tudo.
        return alvo
    return max(0.0, alvo - passou)


@contextmanager
def vez(canal: str = "", motivo: str = "", avisar=print):
    """Segura a vez de baixar: trava a maquina e cumpre o intervalo.

    Use SEMPRE em volta do download, nunca em volta da rodada inteira — o
    intervalo e' entre downloads, nao entre lotes.
    """
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    fd = None
    while fd is None:
        try:
            # O_EXCL: quem cria, ganha. E' atomico, entao dois processos nao
            # podem "criar" o mesmo arquivo ao mesmo tempo.
            fd = os.open(str(TRAVA), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            dono = 0
            try:
                dono = int((TRAVA.read_text(encoding="utf-8").split()[0]))
            except Exception:
                dono = 0
            if dono and not _vivo(dono):
                avisar(f"    [cadencia] trava presa pelo PID {dono}, que nao "
                       f"existe mais — assumindo")
                try:
                    TRAVA.unlink()
                except Exception:
                    pass
                continue
            if time.time() - inicio > ESPERA_MAX_TRAVA_S:
                raise TimeoutError(
                    f"outro download segura a vez ha' mais de "
                    f"{ESPERA_MAX_TRAVA_S // 60} min (PID {dono or '?'}). "
                    f"NAO baixei — dois ao mesmo tempo e' o que a guarda "
                    f"existe pra impedir.")
            avisar(f"    [cadencia] outro download em curso (PID {dono or '?'}); "
                   f"aguardando a vez")
            time.sleep(SONDA_S)
    try:
        os.write(fd, f"{os.getpid()} {canal} {motivo}".encode("utf-8"))
        os.close(fd)
        fd = None
        falta = espera_devida()
        if falta > 0:
            avisar(f"    [cadencia] {falta:.0f}s ate' poder baixar de novo "
                   f"(intervalo global, qualquer canal)")
            time.sleep(falta)
        yield
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass
        # ⚠️ O carimbo e' gravado ANTES de soltar a trava. Na ordem inversa,
        # outro processo poderia pegar a trava e ler um carimbo velho.
        _gravar_fim(canal)
        try:
            TRAVA.unlink()
        except Exception:
            pass
