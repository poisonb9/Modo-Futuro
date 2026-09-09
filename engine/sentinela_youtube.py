# -*- coding: utf-8 -*-
"""Sentinela do YouTube: uma porta so', com fila, para TODA chamada.

    python -m engine.sentinela_youtube -- yt-dlp -f best URL
    python -m engine.sentinela_youtube --estado
    python -m engine.sentinela_youtube --soltar     (tira o freio a mao)

⚠️ POR QUE ELA EXISTE.

O que esta' em jogo NAO e' cota, e' a CONTA e o IP. Download paralelo e' o
padrao que o YouTube usa pra reconhecer robo, e a punicao chega como
`Sign in to confirm you're not a bot` — sem desfazer e sem dizer o motivo.
Foi o que aconteceu com a VPS em 09/09/2026.

Ordem do Bryan no mesmo dia: nunca mais de uma chamada consecutiva ou junta,
sempre intervalado, em QUALQUER projeto — video, legenda, metadado, qualquer
coisa. E quem chegar dentro do intervalo nao pode ser recusado: tem de entrar
numa FILA e achar seu lugar.

⚠️ O `engine/cadencia.py` ja' fazia parte disto e nao bastou: ele governa UM
repositorio, e o estouro veio de fora dele. Faltava o estado ser
COMPARTILHADO por todos os que falam com o YouTube.

## O QUE ELA GARANTE

    UMA de cada vez    o cadeado exclusivo (O_EXCL) fica NA MAO enquanto o
                       comando roda — ver `vez()`. ⚠️ Ate' 09/09/2026 isto era
                       falso: `esperar_vez()` soltava a porta ao voltar, e o
                       que sobrava era so' o intervalo entre INICIOS. Um
                       download de 40 min com intervalo de 10 tinha QUATRO
                       chamadas encavaladas — a simultaneidade que a sentinela
                       existe pra impedir, dentro da propria sentinela.
    INTERVALO          dorme o que falta desde a ultima chamada
    FILA, nao recusa   quem chega cedo espera a vez
    FALHA FECHADA      sem cadeado, nao passa. Nunca "vai assim mesmo"
    FREIO              ao ver bot-check, trava TUDO e nao tenta de novo

⚠️ ALCANCE, dito sem enfeite: o estado vive em disco, entao ela governa quem
compartilha esse disco. Numa maquina so', governa tudo. Entre maquinas (esta,
a VPS, os runners) so' governa se `SENTINELA_YT_DIR` apontar pra um sistema
de arquivos de verdade compartilhado — pasta sincronizada (Drive, Dropbox)
NAO serve: a sincronizacao demora e duas maquinas leem "livre" ao mesmo
tempo.

**O desenho robusto e' outro: uma maquina so' fala com o YouTube e as demais
pedem a ela.** Esta sentinela e' a porta dessa maquina.

## AJUSTES (variaveis de ambiente)

    SENTINELA_YT_DIR        onde mora o estado (padrao: ~/.sentinela_youtube)
    SENTINELA_YT_INTERVALO       segundos entre downloads de VIDEO (600)
    SENTINELA_YT_INTERVALO_LEVE  entre legenda/metadado/listagem   (300)
    SENTINELA_YT_ESPERA_MAX teto de espera na fila          (padrao: 3600)
    SENTINELA_YT_TETO_DIA   chamadas por dia                (padrao: 12)
    SENTINELA_YT_FREIO_H    horas de freio, pena CHEIA      (padrao: 24)
    SENTINELA_YT_FREIO_TAXA_LEVE_H  pena curta: 429 em chamada
                            LEVE (legenda/metadado)         (padrao: 3)

⚠️ DUAS SEVERIDADES, penas diferentes. `not a bot` e' suspeita no nivel da
CONTA e leva a pena CHEIA sempre, em qualquer peso. 429 e' limite de taxa,
transitorio — e so' quando vem de chamada LEVE leva a pena curta. 429 em
VIDEO continua com 24h: sessao longa em rajada e' o padrao que vira
bot-check. Vindo os dois sinais juntos, bot vence.

⚠️ O intervalo padrao de 15 min NAO e' medido — e' escolhido com folga. A
conta: cada fonte vira ~8 clipes e a operacao publica ~11 posts/dia, entao o
necessario e' 2 a 4 downloads por dia. 15 min x 12 cobre tres vezes isso.
Ser generoso aqui nao custa nada, e o que queimou a VPS foi RAJADA, nao
volume.
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# ⚠️ DUAS SEVERIDADES, penas diferentes. Ajustado em 09/09/2026 depois que um
# 429 numa LEGENDA custou 24h de freio.
#
#   BOT   "not a bot" e' suspeita no nivel da CONTA. E' o que derrubou a VPS.
#         Pena cheia SEMPRE, em qualquer peso. Nao se afrouxa.
#   TAXA  429 e' limite de taxa: transitorio, costuma passar em horas.
#
# A pena curta vale so' pra TAXA em chamada LEVE (legenda, metadado, listagem).
# Video em 429 continua com a pena cheia: sessao longa em rajada e' justamente
# o padrao que vira bot-check.
SINAIS_BOT = (
    "sign in to confirm you're not a bot",
    "sign in to confirm you’re not a bot",   # apostrofo tipografico
    "confirm you're not a bot",
    "confirm you’re not a bot",
    "this helps protect our community",
)
SINAIS_TAXA = (
    "http error 429",
    "too many requests",
)
SINAIS_DE_BLOQUEIO = SINAIS_BOT + SINAIS_TAXA


class Bloqueada(RuntimeError):
    """Freio puxado ou teto do dia. NAO tentar de novo."""


class NaoConsegui(RuntimeError):
    """Nao deu pra pegar a vez no teto de espera. Falha FECHADA."""


def _dir() -> Path:
    d = Path(os.getenv("SENTINELA_YT_DIR")
             or (Path.home() / ".sentinela_youtube"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _num(nome: str, padrao: int) -> int:
    try:
        return max(0, int(os.getenv(nome, padrao)))
    except ValueError:
        return padrao


# ⚠️ DUAS FAIXAS, UM CADEADO SO'. Ajustado em 09/09/2026 depois de o Bryan
# apontar o obvio: "15 min nao e' muito? eu preciso baixar legendas as vezes".
#
# Estava errado tratar uma legenda como um video de 700 MB. Para o YouTube um
# download de video e' uma sessao longa, com dezenas de requisicoes de
# segmento; uma legenda ou um metadado e' UMA requisicao curta. O que
# dispara o bot-check e' o padrao de requisicao, e os dois padroes sao
# diferentes.
#
#   PESADO  video      600s (10 min)
#   LEVE    legenda,   300s (5 min)  <- numero escolhido pelo Bryan
#           metadado,
#           listagem
#
# ⚠️ NENHUM DOS DOIS E' MEDIDO. Sao escolhas com folga: a operacao precisa de
# 2-4 videos por dia, e o que queimou a VPS foi RAJADA, nao volume.
#
# ⚠️ E O CADEADO CONTINUA UM SO'. As faixas mudam a ESPERA, nunca a
# simultaneidade: uma legenda nunca sai junto com um video. Duas faixas com
# dois cadeados seriam duas portas, que e' exatamente o que a sentinela
# existe pra impedir.
def intervalo(peso: str = "pesado") -> int:
    if peso == "leve":
        return _num("SENTINELA_YT_INTERVALO_LEVE", 300)
    return _num("SENTINELA_YT_INTERVALO", 600)


def espera_max() -> int:
    return _num("SENTINELA_YT_ESPERA_MAX", 3600)


def teto_dia() -> int:
    return _num("SENTINELA_YT_TETO_DIA", 12)


def freio_h() -> int:
    return _num("SENTINELA_YT_FREIO_H", 24)


def freio_taxa_leve_h() -> int:
    """Pena para 429 em chamada LEVE. Curta de proposito."""
    return _num("SENTINELA_YT_FREIO_TAXA_LEVE_H", 3)


def severidade(texto: str) -> str | None:
    """'bot', 'taxa' ou None. Bot vence: se os dois aparecem, e' bot."""
    t = (texto or "").lower()
    if any(x in t for x in SINAIS_BOT):
        return "bot"
    if any(x in t for x in SINAIS_TAXA):
        return "taxa"
    return None


def _ler(arq: Path) -> dict:
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except Exception:
        # ⚠️ Arquivo corrompido conta como "nao sei", nunca como "pode ir".
        return {}


def _grav(arq: Path, d: dict) -> None:
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    tmp.replace(arq)          # troca atomica: ninguem le' pela metade


def freio_ativo() -> tuple[bool, str]:
    """(travado, por_que).

    O freio e' o unico estado que RECUSA em vez de enfileirar: depois de um
    bot-check, esperar na fila e tentar de novo e' exatamente o que confirma
    o padrao de robo.
    """
    d = _ler(_dir() / "freio.json")
    ate = float(d.get("ate", 0) or 0)
    if ate > time.time():
        falta = int((ate - time.time()) / 60)
        quando = datetime.fromtimestamp(ate, timezone.utc)
        return True, (f"freio puxado ate' {quando:%d/%m %H:%M} UTC "
                      f"({falta} min) — motivo: {d.get('motivo', '?')}")
    return False, ""


def puxar_freio(motivo: str, horas: int | None = None,
                peso: str = "pesado") -> None:
    """Puxa o freio. A pena sai da SEVERIDADE do motivo e do PESO da chamada.

    ⚠️ `horas` explicito continua vencendo tudo — e' o que os ensaios usam.
    """
    if horas is None:
        h = (freio_taxa_leve_h()
             if severidade(motivo) == "taxa" and peso == "leve"
             else freio_h())
    else:
        h = horas
    _grav(_dir() / "freio.json",
          {"ate": time.time() + h * 3600, "motivo": str(motivo)[:300],
           "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")})


def soltar_freio() -> None:
    (_dir() / "freio.json").unlink(missing_ok=True)


def _hoje() -> str:
    return f"{datetime.now(timezone.utc):%Y-%m-%d}"


def _contagem() -> dict:
    d = _ler(_dir() / "contagem.json")
    return d if d.get("dia") == _hoje() else {"dia": _hoje(), "n": 0}


def estado() -> dict:
    travado, por_que = freio_ativo()
    ult = float(_ler(_dir() / "ultima.json").get("quando", 0) or 0)
    falta = max(0, intervalo("pesado") - (time.time() - ult)) if ult else 0
    return {
        "dir": str(_dir()),
        "freio": travado,
        "motivo": por_que,
        "ultima": (datetime.fromtimestamp(ult, timezone.utc)
                   .isoformat(timespec="seconds") if ult else None),
        "faltam_s": int(falta),
        "intervalo_leve_s": intervalo("leve"),
        "hoje": _contagem()["n"],
        "teto_dia": teto_dia(),
        "intervalo_s": intervalo(),
    }


def _pegar_cadeado(limite_s: float) -> Path:
    """Cadeado por arquivo com O_EXCL — atomico ate' em disco de rede.

    ⚠️ Cadeado ABANDONADO e' recolhido. Sem isso, um processo morto no meio
    deixa a porta trancada pra sempre e a operacao inteira para em silencio —
    pior que o problema que a sentinela resolve.
    """
    alvo = _dir() / "cadeado"
    limite = time.time() + limite_s
    while True:
        try:
            fd = os.open(str(alvo), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {time.time():.0f}".encode())
            os.close(fd)
            return alvo
        except FileExistsError:
            # ⚠️ CADEADO SEM CONTEUDO E' NOVO, NAO ABANDONADO. O arquivo nasce
            # VAZIO no `O_CREAT` e so' recebe o pid no `os.write` seguinte:
            # entre as duas linhas existe um instante em que outro processo le'
            # e nao acha carimbo nenhum.
            #
            # Com `nasceu = 0.0` esse instante virava "abandonado ha' 56 anos",
            # o cadeado recem-criado era APAGADO, e os dois processos seguiam —
            # DOIS downloads ao mesmo tempo, que e' exatamente o que esta
            # funcao existe pra impedir. Janela de microssegundos em disco
            # local; bem maior em disco de rede, que e' o caso que o `O_EXCL`
            # foi escolhido pra atender.
            #
            # O `st_mtime` e' carimbado pelo proprio sistema na CRIACAO, entao
            # ele responde mesmo quando o conteudo ainda nao chegou. Se nem
            # ele der (arquivo sumiu no meio), a hora de AGORA e' o palpite
            # seguro: trata como novo e espera, em vez de arrombar.
            try:
                nasceu = float(alvo.read_text(encoding="utf-8").split()[1])
            except Exception:
                try:
                    nasceu = alvo.stat().st_mtime
                except OSError:
                    nasceu = time.time()
            if time.time() - nasceu > max(600, limite_s):
                alvo.unlink(missing_ok=True)       # abandonado
                continue
            if time.time() >= limite:
                raise NaoConsegui(
                    f"cadeado ocupado por mais de {limite_s:.0f}s — outra "
                    f"chamada ao YouTube esta' em curso")
            time.sleep(2)


def _leve_esperando() -> bool:
    """Ha' uma chamada LEVE na fila agora?

    ⚠️ O marcador tem prazo. Se um processo leve morrer antes de passar, o
    arquivo ficaria la' e todo video esperaria por um fantasma pra sempre.
    """
    d = _ler(_dir() / "pedido_leve.json")
    return float(d.get("quando", 0) or 0) > time.time() - 120


def _marcar_leve(ligado: bool) -> None:
    if ligado:
        _grav(_dir() / "pedido_leve.json",
              {"quando": time.time(), "pid": os.getpid()})
    else:
        (_dir() / "pedido_leve.json").unlink(missing_ok=True)


def esperar_vez(rotulo: str = "", peso: str = "pesado") -> None:
    """Segura aqui ate' ser a vez. Levanta se estiver travado.

    ⚠️ E' o coracao: quem chega dentro do intervalo NAO leva erro, ele DORME
    o que falta. Recusar faria cada chamador inventar seu proprio retry, e
    retry solto foi o que queimou a VPS.

    ⚠️ QUEM DORME NAO SEGURA O CADEADO. Na primeira versao o processo pegava
    a porta e so' entao dormia o intervalo — e uma legenda ficava presa atras
    de um video por ate' 10 minutos, com a porta trancada a toa. Agora o
    cadeado e' tomado so' pra OLHAR o relogio e pra CARIMBAR; o sono
    acontece com a porta livre.

    ⚠️ E A LEGENDA TEM PREFERENCIA. Ordem do Bryan em 09/09: "para download
    de videos eu nao me importo, mas quando for legendas pode priorizar".
    Um pedido LEVE deixa um marcador; enquanto ele existir, chamada PESADA
    nao carimba, mesmo com o tempo dela cumprido. O video espera mais um
    pouco; a legenda passa na frente.
    """
    travado, por_que = freio_ativo()
    if travado:
        raise Bloqueada(por_que)

    c = _contagem()
    if teto_dia() and c["n"] >= teto_dia():
        raise Bloqueada(f"teto do dia atingido ({c['n']}/{teto_dia()}) — "
                        f"volta amanha, em UTC")

    if peso == "leve":
        _marcar_leve(True)
    limite = time.time() + espera_max()
    avisou = False
    try:
        while True:
            cadeado = _pegar_cadeado(60)
            try:
                # ⚠️ Confere o freio DE NOVO com o cadeado na mao: quem estava
                # na frente pode ter levado bot-check nesse meio-tempo. Sem
                # isto a fila inteira desfila em cima do bloqueio.
                travado, por_que = freio_ativo()
                if travado:
                    raise Bloqueada(por_que)

                ult = float(_ler(_dir() / "ultima.json").get("quando", 0) or 0)
                # ⚠️ O relogio e' UM so' e vale pra todo mundo: o intervalo
                # conta desde a ULTIMA chamada de QUALQUER peso. Se cada faixa
                # tivesse seu relogio, uma legenda logo depois de um video
                # pareceria espacada e nao estaria — a rajada que queimou a VPS.
                falta = intervalo(peso) - (time.time() - ult) if ult else 0
                cede = peso != "leve" and _leve_esperando()

                if falta <= 0 and not cede:
                    c = _contagem()          # relê: outro pode ter passado
                    if teto_dia() and c["n"] >= teto_dia():
                        raise Bloqueada(
                            f"teto do dia atingido ({c['n']}/{teto_dia()})")
                    _grav(_dir() / "ultima.json",
                          {"quando": time.time(), "rotulo": str(rotulo)[:200],
                           "peso": peso, "pid": os.getpid()})
                    c["n"] += 1
                    _grav(_dir() / "contagem.json", c)
                    return
            finally:
                cadeado.unlink(missing_ok=True)   # dorme com a porta LIVRE

            if time.time() >= limite:
                raise NaoConsegui(
                    f"nao consegui a vez em {espera_max()}s (peso={peso})")
            if not avisou:
                motivo = ("cedendo a vez pra uma legenda" if cede
                          else f"a vez chega em {max(0, falta):.0f}s")
                extra = f" — {rotulo}" if rotulo else ""
                print(f"[sentinela] {motivo}{extra}", flush=True)
                avisou = True
            time.sleep(min(max(1.0, falta if falta > 0 else 2.0), 5.0))
    finally:
        if peso == "leve":
            _marcar_leve(False)


_BATIDA_S = 60


@contextlib.contextmanager
def vez(rotulo: str = "", peso: str = "pesado"):
    """Espera a vez E SEGURA A PORTA enquanto o comando roda.

    ⚠️ E' ISTO que cumpre a ordem "uma de cada vez". O `esperar_vez()` sozinho
    so' espaca os INICIOS: ele solta o cadeado ao voltar, de proposito (quem
    dorme nao pode trancar a porta), e um download longo continuava rodando
    enquanto o proximo ja' era liberado. Com intervalo de 10 min e um podcast
    de 40, davam QUATRO downloads simultaneos.

        with sentinela.vez(f"baixar {url}"):
            roda(cmd)

    ⚠️ E O CADEADO BATE O PONTO. Quem segura reescreve o carimbo a cada
    `_BATIDA_S`, senao a propria regra de recolhimento (cadeado parado ha' mais
    de 600s e' abandonado) arrombaria a porta de um download de 40 minutos —
    trocando um defeito por outro pior, porque ninguem veria.

    Processo morto para de bater e o cadeado volta a ser recolhido como sempre.
    """
    esperar_vez(rotulo, peso)
    cadeado = _pegar_cadeado(espera_max())
    parar = threading.Event()

    def _bater():
        while not parar.wait(_BATIDA_S):
            try:
                cadeado.write_text(f"{os.getpid()} {time.time():.0f}",
                                   encoding="utf-8")
            except OSError:
                return

    batida = threading.Thread(target=_bater, daemon=True)
    batida.start()
    try:
        yield
    finally:
        parar.set()
        cadeado.unlink(missing_ok=True)


def e_bloqueio(texto: str) -> bool:
    t = (texto or "").lower()
    return any(s in t for s in SINAIS_DE_BLOQUEIO)


def peso_do_comando(cmd: list[str]) -> str:
    """LEVE quando o comando so' consulta; PESADO quando puxa midia.

    ⚠️ Na duvida, PESADO. Errar pra baixo custa 5 minutos de espera a mais;
    errar pra cima e' tratar um download de video como consulta, que e' o
    caminho de volta pro bot-check.
    """
    leves = ("--skip-download", "--write-sub", "--write-auto-sub",
             "--list-subs", "--print", "--dump-json", "--get-", "-F",
             "--list-formats", "--simulate", "-s")
    return "leve" if any(a in leves or a.startswith("--get-")
                         for a in cmd) else "pesado"


def rodar(cmd: list[str], rotulo: str = "", peso: str | None = None) -> int:
    """Espera a vez, roda o comando, e PUXA O FREIO se vier bot-check.

    ⚠️ Com `vez()`, nao `esperar_vez()`: a porta fica na mao ate' o comando
    terminar. Ver o cabecalho de `vez`.
    """
    with vez(rotulo or " ".join(cmd[:2]), peso or peso_do_comando(cmd)):
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    saida = (r.stdout or "") + (r.stderr or "")
    if r.stdout:
        print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="", file=sys.stderr)
    if e_bloqueio(saida):
        motivo = next((l for l in saida.splitlines() if e_bloqueio(l)),
                      "bot-check")
        puxar_freio(motivo, peso=peso or peso_do_comando(cmd))
        print(f"\n[sentinela] FREIO PUXADO por {freio_h()}h: {motivo[:120]}\n"
              f"[sentinela] nao tente de novo — tentar e' o que confirma o "
              f"padrao de robo.", file=sys.stderr)
    return r.returncode


def main() -> int:
    args = sys.argv[1:]
    if "--estado" in args:
        print(json.dumps(estado(), ensure_ascii=False, indent=1))
        return 0
    if "--soltar" in args:
        soltar_freio()
        print("freio solto.")
        return 0
    if "--" not in args:
        print("uso: python -m engine.sentinela_youtube -- <comando>",
              file=sys.stderr)
        return 2
    cmd = args[args.index("--") + 1:]
    if not cmd:
        print("nada pra rodar depois do --", file=sys.stderr)
        return 2
    try:
        return rodar(cmd)
    except (Bloqueada, NaoConsegui) as e:
        print(f"[sentinela] RECUSADO: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
