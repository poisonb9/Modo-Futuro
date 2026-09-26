# -*- coding: utf-8 -*-
"""Efeitos sonoros discretos no 9:16: "pop" quando o titulo entra, "whoosh"
quando ele sai.

    python -m engine.sfx --video c.mp4          aplica no lugar
    python -m engine.sfx --amostra saida.wav    so' os sons, pra ouvir

## POR QUE EXISTE

Item aprovado na analise "o que falta pra ficar premium" (26/09/2026, +acervo):
os praticantes somam efeito sonoro a' musica e aos cortes pra dar ritmo
(F124199, F123450). O motor nao tinha nenhum — so' o sino da camada.

⚠️ OS SONS SAO SINTETIZADOS AQUI, pelo ffmpeg, e nao baixados: livres de
direito por construcao, identicos na maquina e na nuvem, e sem arquivo de
terceiro no repositorio (que e' publico).

⚠️ POUCO E BAIXO de proposito: dois sons por clipe, bem abaixo da voz. Efeito
a cada frase cansa e compete com a fala — o acervo fala em ritmo, nao em
barulho. Falha aberta: qualquer erro deixa o video como estava.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

LIGADO = os.environ.get("SFX", "1") != "0"

# (lavfi, volume relativo a' trilha)
SONS = {
    # pop: tom curto que sobe de 600 a ~1400 Hz e morre em 120 ms
    "pop": ("aevalsrc='0.9*sin(2*PI*(600*t+3300*t*t))*exp(-t*38)':d=0.12:s=44100", 0.35),
    # whoosh: ruido rosa filtrado, entra e sai em 0,45 s
    "whoosh": ("anoisesrc=d=0.45:c=pink:a=1.0:r=44100,highpass=f=500,lowpass=f=6000,"
               "afade=t=in:d=0.22,afade=t=out:st=0.22:d=0.23", 0.55),
}


def momentos() -> list[tuple[str, float]]:
    """(som, instante_s) no tempo do render, ANTES da velocidade por canal."""
    from .render import TITULO_SEGUNDOS
    return [("pop", 0.02), ("whoosh", max(0.0, TITULO_SEGUNDOS - 0.12))]


def _gerar(nome: str, destino: Path) -> Path:
    src, _ = SONS[nome]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", src,
                    "-ac", "2", str(destino)], check=True, capture_output=True, timeout=60)
    return destino


def aplicar_no_lugar(video: Path) -> bool:
    """Mistura os sons no audio do video, trocando o arquivo so' se der certo."""
    if not LIGADO:
        return False
    video = Path(video)
    novo = video.with_name(video.stem + "_sfx.mp4")
    try:
        pasta = Path(tempfile.mkdtemp(prefix="sfx_"))
        ms = momentos()
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video)]
        filtros, rot = [], []
        for j, (nome, t) in enumerate(ms, start=1):
            cmd += ["-i", str(_gerar(nome, pasta / f"{nome}.wav"))]
            atraso = int(t * 1000)
            filtros.append(f"[{j}:a]adelay={atraso}|{atraso},volume={SONS[nome][1]}[s{j}]")
            rot.append(f"[s{j}]")
        filtros.append(f"[0:a]{''.join(rot)}amix=inputs={len(rot) + 1}:"
                       f"duration=first:normalize=0[a]")
        cmd += ["-filter_complex", ";".join(filtros), "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                str(novo)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        if not novo.exists() or novo.stat().st_size < 1000:
            raise RuntimeError("saida vazia")
    except Exception as e:
        print(f"      [!] efeitos sonoros nao aplicados ({type(e).__name__})")
        novo.unlink(missing_ok=True)
        return False
    video.unlink(missing_ok=True)
    novo.rename(video)
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--amostra")
    a = ap.parse_args()
    if a.amostra:
        pasta = Path(tempfile.mkdtemp())
        partes = [_gerar(n, pasta / f"{n}.wav") for n in SONS]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *sum((["-i", str(p)] for p in partes), []),
                        "-filter_complex", "".join(f"[{i}:a]apad=pad_dur=0.6[p{i}];" for i in range(len(partes)))
                        + "".join(f"[p{i}]" for i in range(len(partes))) + f"concat=n={len(partes)}:v=0:a=1[o]",
                        "-map", "[o]", a.amostra], check=True)
        print(a.amostra)
    elif a.video:
        print(aplicar_no_lugar(Path(a.video)))
