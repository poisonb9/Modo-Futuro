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

    UMA de cada vez    cadeado exclusivo, criado com O_EXCL (atomico)
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
    SENTINELA_YT_INTERVALO  segundos entre chamadas         (padrao: 900)
    SENTINELA_YT_ESPERA_MAX teto de espera na fila          (padrao: 3600)
    SENTINELA_YT_TETO_DIA   chamadas por dia                (padrao: 12)
    SENTINELA_YT_FREIO_H    horas de freio apos bot-check   (padrao: 24)

⚠️ O intervalo padrao de 15 min NAO e' medido — e' escolhido com folga. A
conta: cada fonte vira ~8 clipes e a operacao publica ~11 posts/dia, entao o
necessario e' 2 a 4 downloads por dia. 15 min x 12 cobre tres vezes isso.
Ser generoso aqui nao custa nada, e o que queimou a VPS foi RAJADA, nao
volume.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# O que o YouTube devolve quando decidiu que somos robo.
SINAIS_DE_BLOQUEIO = (
    "sign in to confirm you're not a bot",
    "sign in to confirm you’re not a bot",   # apostrofo tipografico
    "confirm you're not a bot",
    "confirm you’re not a bot",
    "this helps protect our community",
    "http error 429",
    "too many requests",
)


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


def intervalo() -> int:
    return _num("SENTINELA_YT_INTERVALO", 900)


def espera_max() -> int:
    return _num("SENTINELA_YT_ESPERA_MAX", 3600)


def teto_dia() -> int:
    return _num("SENTINELA_YT_TETO_DIA", 12)


def freio_h() -> int:
    return _num("SENTINELA_YT_FREIO_H", 24)


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


def puxar_freio(motivo: str, horas: int | None = None) -> None:
    h = freio_h() if horas is None else horas
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
    falta = max(0, intervalo() - (time.time() - ult)) if ult else 0
    return {
        "dir": str(_dir()),
        "freio": travado,
        "motivo": por_que,
        "ultima": (datetime.fromtimestamp(ult, timezone.utc)
                   .isoformat(timespec="seconds") if ult else None),
        "faltam_s": int(falta),
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
            try:
                nasceu = float(alvo.read_text(encoding="utf-8").split()[1])
            except Exception:
                nasceu = 0.0
            if time.time() - nasceu > max(600, limite_s):
                alvo.unlink(missing_ok=True)       # abandonado
                continue
            if time.time() >= limite:
                raise NaoConsegui(
                    f"cadeado ocupado por mais de {limite_s:.0f}s — outra "
                    f"chamada ao YouTube esta' em curso")
            time.sleep(2)


def esperar_vez(rotulo: str = "") -> None:
    """Segura aqui ate' ser a vez. Levanta se estiver travado.

    ⚠️ E' o coracao: quem chega dentro do intervalo NAO leva erro, ele DORME
    o que falta. Recusar faria cada chamador inventar seu proprio retry, e
    retry solto foi o que queimou a VPS.
    """
    travado, por_que = freio_ativo()
    if travado:
        raise Bloqueada(por_que)

    c = _contagem()
    if teto_dia() and c["n"] >= teto_dia():
        raise Bloqueada(f"teto do dia atingido ({c['n']}/{teto_dia()}) — "
                        f"volta amanha, em UTC")

    cadeado = _pegar_cadeado(espera_max())
    try:
        # ⚠️ Confere o freio DE NOVO com o cadeado na mao: entre a primeira
        # checagem e agora, quem estava na frente pode ter levado bot-check e
        # puxado o freio. Sem isto a fila inteira desfila em cima do bloqueio.
        travado, por_que = freio_ativo()
        if travado:
            raise Bloqueada(por_que)

        ult = float(_ler(_dir() / "ultima.json").get("quando", 0) or 0)
        falta = intervalo() - (time.time() - ult) if ult else 0
        if falta > 0:
            extra = f" — {rotulo}" if rotulo else ""
            print(f"[sentinela] a vez chega em {falta:.0f}s{extra}", flush=True)
            time.sleep(falta)

        _grav(_dir() / "ultima.json",
              {"quando": time.time(), "rotulo": str(rotulo)[:200],
               "pid": os.getpid()})
        c["n"] += 1
        _grav(_dir() / "contagem.json", c)
    finally:
        cadeado.unlink(missing_ok=True)


def e_bloqueio(texto: str) -> bool:
    t = (texto or "").lower()
    return any(s in t for s in SINAIS_DE_BLOQUEIO)


def rodar(cmd: list[str], rotulo: str = "") -> int:
    """Espera a vez, roda o comando, e PUXA O FREIO se vier bot-check."""
    esperar_vez(rotulo or " ".join(cmd[:2]))
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
        puxar_freio(motivo)
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
