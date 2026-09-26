# -*- coding: utf-8 -*-
"""Capa nitida: o quadro 0 do 9:16 passa a ser o mais nitido dos 2 s do titulo.

    python -m engine.capa_nitida --video c.mp4

## POR QUE EXISTE

A capa do TikTok (grade do perfil) e' o PRIMEIRO QUADRO do video — a API do
Buffer so' deixa escolher o quadro, nao mandar imagem (render.py). E o primeiro
quadro do corte e' o que calhar: borrado de movimento, olho fechado, meio de
transicao. O acervo manda cuidar desse quadro (F132220, F100190).

Decisao do dono em 26/09/2026 (opcao "a"): procurar o melhor quadro SO' dentro
dos 2 s do titulo — ali a imagem e' limpa (a legenda so' entra depois do
titulo e os baloes aos 3 s), entao a capa continua sendo titulo + imagem.

Um quadro (1/fps, ~33 ms) nao se percebe assistindo, mas vira a capa. O audio
atrasa o mesmo quadro, pra nao dessincronizar. So' mexe se o melhor quadro for
CLARAMENTE mais nitido que o atual (`GANHO_MIN`); senao nao reprocessa nada.
Falha aberta.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

LIGADO = os.environ.get("CAPA_NITIDA", "1") != "0"
GANHO_MIN = 1.15
PASSO_S = 0.15


def nota_quadro(img) -> float:
    """Nitidez (variancia das bordas) com penalidade de exposicao ruim."""
    from PIL import ImageFilter, ImageStat
    g = img.convert("L")
    nit = ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0]
    media = ImageStat.Stat(g).mean[0]
    if media < 35 or media > 220:
        nit *= 0.5
    return nit


def melhor_instante(video: Path, ate_s: float) -> tuple[float, float, float]:
    """(instante do melhor quadro, nota dele, nota do quadro 0)."""
    from PIL import Image
    pasta = Path(tempfile.mkdtemp(prefix="capa_"))
    t, notas = 0.0, []
    while t < ate_s - 0.05:
        f = pasta / f"q_{int(t * 1000):05d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video),
                        "-frames:v", "1", "-vf", "scale=360:-2", str(f)],
                       check=True, capture_output=True, timeout=60)
        if f.exists():
            notas.append((t, nota_quadro(Image.open(f))))
        t += PASSO_S
    if not notas:
        raise RuntimeError("nenhum quadro lido")
    melhor = max(notas, key=lambda x: x[1])
    return melhor[0], melhor[1], notas[0][1]


def aplicar_no_lugar(video: Path) -> bool:
    if not LIGADO:
        return False
    from . import midia
    from .render import TITULO_SEGUNDOS
    video = Path(video)
    novo = video.with_name(video.stem + "_capa.mp4")
    try:
        t, nota, nota0 = melhor_instante(video, TITULO_SEGUNDOS)
        if t < 0.05 or nota < nota0 * GANHO_MIN:
            return False
        fps = midia.fps(video)
        q = 1.0 / fps
        ms = max(1, round(q * 1000))
        filtro = (f"[0:v]split[a][b];[b]trim=start={t:.3f}:duration={q:.5f},"
                  f"setpts=PTS-STARTPTS[c];[c][a]concat=n=2:v=1:a=0[v];"
                  f"[0:a]adelay={ms}:all=1[au]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                        "-filter_complex", filtro, "-map", "[v]", "-map", "[au]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", str(novo)],
                       check=True, capture_output=True, timeout=900)
        if not novo.exists() or novo.stat().st_size < 1000:
            raise RuntimeError("saida vazia")
        print(f"      capa: quadro de {t:.2f}s ({nota / max(nota0, 1e-9):.2f}x mais nitido "
              "que o 1o) virou o quadro 0")
    except Exception as e:
        print(f"      [!] capa nitida nao aplicada ({type(e).__name__})")
        novo.unlink(missing_ok=True)
        return False
    video.unlink(missing_ok=True)
    novo.rename(video)
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    print(aplicar_no_lugar(Path(ap.parse_args().video)))
