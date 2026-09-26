# -*- coding: utf-8 -*-
"""O FUNDO do original (musica, ambiente, risada) por baixo da dublagem.

    python -m engine.fundo --bruto trecho.mp4 --dublado voz.wav --saida mix.wav

## POR QUE EXISTE

Item 1 da dublagem (26/09/2026, dono: "Aplica Demucs!!!!"). Ate' aqui a
dublagem normal APAGAVA o audio original: a musica, o ambiente e as reacoes
sumiam, e o clipe virava uma voz sozinha sobre imagem. O Orca Dub chama isto
de "preservar audio de fundo" (acervo F128405); o acervo tambem poe o som
como uma das tres armas de retencao (F16919).

O Demucs (Meta, MIT, gratis) separa o original em VOZ e FUNDO. A voz
original sai; o fundo fica por baixo da dublagem, e ABAIXA sozinho enquanto
a dublagem fala (sidechain) e volta nas pausas.

## O ENCAIXE COM A CAUDA

`cauda.preencher_com_original` ja' devolve o som original INTEIRO depois da
ultima palavra. Se o fundo continuasse ali, sairia dobrado. Por isso o fundo
sai em fade no mesmo instante em que a cauda entra (`ate_s`).

## FALHA ABERTA

Demucs fora, erro, timeout: devolve None e o clipe sai como antes (so' a
voz). Um clipe sem fundo e' o de hoje; um clipe que nao sai e' pior.

⚠️ Tempo e memoria sao MEDIDOS a cada separacao e impressos no log
("[fundo] demucs ... s, pico ... MB") — a pergunta do dono foi se cabe nos
16 GB do runner, e a resposta tem de ser numero, nao estimativa.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ligado por env ate' o dono aprovar pela previa; depois vira True aqui
LIGADO = os.environ.get("FUNDO_ORIGINAL", "0") == "1"
MODELO = "htdemucs"
TIMEOUT_S = 900
# nivel do fundo nas PAUSAS, depois de normalizar as duas trilhas em -14 LUFS.
# Enquanto a voz fala, o sidechain derruba mais ~8-10 dB.
VOL_FUNDO = 0.45
FADE_S = 0.8
_LN = "loudnorm=I=-14:TP=-1.5:LRA=11"


def separar(bruto: Path, pasta: Path) -> Path | None:
    """O FUNDO (tudo menos a voz) do audio de `bruto`, em wav. None se falhar."""
    pasta.mkdir(parents=True, exist_ok=True)
    entrada = pasta / "orig.wav"
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(bruto), "-vn",
                        "-ac", "2", "-ar", "44100", str(entrada)],
                       check=True, capture_output=True, timeout=300)
        cmd = [sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", MODELO,
               "-d", "cpu", "-o", str(pasta), str(entrada)]
        # /usr/bin/time -v da' o PICO de memoria (so' no Linux do runner)
        medir = shutil.which("time") or ("/usr/bin/time" if Path("/usr/bin/time").exists() else None)
        if medir and sys.platform.startswith("linux"):
            cmd = [medir, "-v"] + cmd
        t0 = time.monotonic()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
        dt = time.monotonic() - t0
        pico = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", r.stderr or "")
        print(f"      [fundo] demucs {dt:.0f}s"
              + (f", pico {int(pico.group(1)) // 1024} MB" if pico else ""), flush=True)
        if r.returncode != 0:
            print(f"      [!] demucs falhou: {(r.stderr or '')[-200:]}", flush=True)
            return None
        fundo = pasta / MODELO / "orig" / "no_vocals.wav"
        return fundo if fundo.exists() else None
    except Exception as e:
        print(f"      [!] fundo indisponivel ({type(e).__name__}: {str(e)[:80]})", flush=True)
        return None


def filtro_mix(ate_s: float | None) -> str:
    """[0:a] = fundo, [1:a] = dublagem -> [a]. Exposto pro teste."""
    corte = ""
    if ate_s is not None and ate_s > 0:
        corte = (f",volume='if(gte(t,{ate_s:.3f}),0,1)':eval=frame,"
                 f"afade=t=out:st={max(0.0, ate_s - FADE_S):.3f}:d={FADE_S}")
    return (f"[0:a]{_LN},volume={VOL_FUNDO}{corte}[f];"
            f"[1:a]{_LN},asplit=2[d][sc];"
            f"[f][sc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[fd];"
            f"[d][fd]amix=inputs=2:duration=first:normalize=0[a]")


def misturar(bruto: Path, dublado: Path, destino: Path,
             ate_s: float | None = None) -> Path | None:
    """Dublagem + fundo original (com ducking). None = segue so' a dublagem."""
    pasta = Path(tempfile.mkdtemp(prefix="fundo_"))
    fundo = separar(Path(bruto), pasta)
    if fundo is None:
        return None
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(fundo), "-i", str(dublado),
                        "-filter_complex", filtro_mix(ate_s), "-map", "[a]",
                        "-ar", "44100", str(destino)],
                       check=True, capture_output=True, timeout=300)
        return Path(destino)
    except Exception as e:
        print(f"      [!] mistura do fundo falhou ({type(e).__name__})", flush=True)
        return None
    finally:
        shutil.rmtree(pasta / MODELO, ignore_errors=True)


def filtro_voice_over(vol_pausa: float = 0.55) -> str:
    """Voice-over: o ORIGINAL inteiro (com a voz da pessoa) abaixa so' enquanto
    a dublagem fala, em vez de ficar fixo a 0,18 o tempo todo.
    [0:a] = original, [1:a] = dublagem -> [vo] (sem loudnorm: o render poe)."""
    return (f"[0:a]{_LN},volume={vol_pausa}[o];"
            f"[1:a]{_LN},asplit=2[d][sc];"
            f"[o][sc]sidechaincompress=threshold=0.03:ratio=10:attack=15:release=400[od];"
            f"[od][d]amix=inputs=2:normalize=0[vo]")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bruto", required=True)
    ap.add_argument("--dublado", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()
    print(misturar(Path(a.bruto), Path(a.dublado), Path(a.saida), a.ate))
