# -*- coding: utf-8 -*-
"""Guarda da capa nítida (engine/capa_nitida.py).

POR QUE EXISTE

26/09/2026, decisão do dono (opção "a"): o quadro 0 — a capa do TikTok — passa
a ser o mais nítido dos 2 s do título, em vez do que calhar.

  [1] começo borrado -> o quadro 0 vira um quadro nítido
  [2] ganha só 1 quadro; áudio e vídeo continuam do mesmo tamanho (sincronia)
  [3] NEGATIVO: vídeo já nítido desde o início não é reprocessado

Roda com: python teste/teste_capa_nitida.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from PIL import Image  # noqa: E402
from engine import capa_nitida, midia  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def dur(arq, sel):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries",
                        "stream=duration", "-of", "csv=p=0", str(arq)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def quadro0(arq):
    f = Path(tempfile.mkdtemp()) / "q.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(arq), "-frames:v", "1",
                    "-vf", "scale=360:-2", str(f)], check=True)
    return capa_nitida.nota_quadro(Image.open(f))


def video(destino, borrado_ate):
    blur = f",boxblur=12:enable='lt(t,{borrado_ate})'" if borrado_ate else ""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"testsrc2=s=540x960:r=30:d=4{blur}", "-f", "lavfi", "-i",
                    "sine=f=440:d=4", "-c:v", "libx264", "-preset", "ultrafast",
                    "-c:a", "aac", "-shortest", str(destino)], check=True)
    return destino


print(__doc__.splitlines()[0])
T = Path(tempfile.mkdtemp())

print("\n[1] começo borrado")
v = video(T / "b.mp4", 1.0)
antes, dv0 = quadro0(v), dur(v, "v:0")
checar(capa_nitida.aplicar_no_lugar(v), "aplicou")
depois = quadro0(v)
print(f"       nota do quadro 0: {antes:.0f} -> {depois:.0f}")
checar(depois > antes * 2, "o quadro 0 ficou nítido")

print("\n[2] um quadro a mais, áudio junto")
q = 1 / midia.fps(v)
checar(abs(dur(v, "v:0") - (dv0 + q)) < q * 1.5, "vídeo ganhou ~1 quadro")
checar(abs(dur(v, "a:0") - dur(v, "v:0")) < 0.1, "áudio e vídeo do mesmo tamanho")

print("\n[3] NEGATIVO: já nítido não mexe")
v2 = video(T / "n.mp4", 0)
m = v2.stat().st_mtime_ns
checar(capa_nitida.aplicar_no_lugar(v2) is False and v2.stat().st_mtime_ns == m,
       "arquivo intocado")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
