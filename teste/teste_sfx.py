# -*- coding: utf-8 -*-
"""Guarda dos efeitos sonoros do título (engine/sfx.py).

POR QUE EXISTE

26/09/2026 (análise premium, aprovada): "pop" quando o título entra e
"whoosh" quando ele sai, sintetizados pelo ffmpeg (sem arquivo de terceiro).

  [1] o som aparece nos dois instantes (0 s e fim do título), e não entre eles
  [2] o vídeo mantém a duração e a imagem (vídeo copiado, não reencodado)
  [3] NEGATIVO: SFX desligado não mexe no arquivo

Roda com: python teste/teste_sfx.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import midia, render, sfx  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def rms(arq, a, b):
    r = subprocess.run(["ffmpeg", "-v", "info", "-ss", str(a), "-t", str(b - a), "-i", str(arq),
                        "-af", "astats=metadata=0", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"RMS level dB:\s*(-?[\d.]+|-inf)", r.stderr)
    return float(m[-1]) if m and m[-1] != "-inf" else -200.0


print(__doc__.splitlines()[0])
T = Path(tempfile.mkdtemp())
v = T / "v.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x568:r=30:d=5",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "5",
                "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(v)], check=True)
dur0 = midia.duracao(v)

print("\n[1] som nos instantes certos")
checar(sfx.aplicar_no_lugar(v), "aplicou")
fim_tit = render.TITULO_SEGUNDOS
pop, meio, whoosh = rms(v, 0.0, 0.2), rms(v, 0.8, 1.4), rms(v, fim_tit - 0.1, fim_tit + 0.4)
print(f"       pop {pop:.1f} dB | entre {meio:.1f} dB | whoosh {whoosh:.1f} dB")
checar(pop > -45 and whoosh > -45, "os dois sons estão lá")
checar(meio < -80, "silêncio entre eles (nada de efeito sobrando)")

print("\n[2] duração e imagem intactas")
checar(abs(midia.duracao(v) - dur0) < 0.1, "mesma duração")

print("\n[3] NEGATIVO: desligado não mexe")
v2 = T / "v2.mp4"
v2.write_bytes(v.read_bytes())
antes = v2.stat().st_mtime_ns
sfx.LIGADO = False
checar(sfx.aplicar_no_lugar(v2) is False and v2.stat().st_mtime_ns == antes, "arquivo intocado")
sfx.LIGADO = True

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
