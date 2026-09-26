# -*- coding: utf-8 -*-
"""Final em loop (engine/loop_final.py + regra 12 da narração).

POR QUE EXISTE

26/09/2026, pedido do dono. O fim do vídeo funde no quadro 0 (acervo
F134044, F134046), e o roteiro dublado termina puxando pro começo, sem
despedida. Os clipes têm >= 65 s, então não é o loop invisível de 5-8 s
(F134045): o objetivo é tirar o SALTO da volta ao início.

  [1] o último quadro é o quadro 0 (a capa), o meio do vídeo não muda
  [2] a duração não muda (± 1 quadro)
  [3] a voz termina com fade (sem estalo), e antes do fim continua alta
  [4] NEGATIVO: LOOP_FINAL=0 deixa o arquivo intacto
  [5] main.py chama o loop DEPOIS da camada/cascata (última etapa visual)
  [6] a narração tem a regra 12; a tradução literal (Sem Anestesia) não

Roda com: python teste/teste_loop_final.py
"""
import hashlib
import importlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402
from engine import loop_final, midia  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])
T = Path(tempfile.mkdtemp())
v = T / "v.mp4"
# 1 s vermelho (o "quadro 0"), depois 5 s azul; tom de 440 Hz o tempo todo
subprocess.run(["ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", "color=c=red:s=360x640:r=30:d=1",
                "-f", "lavfi", "-i", "color=c=blue:s=360x640:r=30:d=5",
                "-f", "lavfi", "-i", "sine=f=440:d=6",
                "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
                "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-shortest", str(v)], check=True)
dur0 = midia.duracao(v)


def cor(seg, arq=v):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{seg:.3f}", "-i", str(arq),
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 3).mean(0)


def volume(ini, d, arq=v):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ini:.3f}", "-t", f"{d:.3f}",
                          "-i", str(arq), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float)
    return float(np.sqrt((a ** 2).mean())) if len(a) else 0.0


print("\n[4] NEGATIVO: desligado")
os.environ["LOOP_FINAL"] = "0"
importlib.reload(loop_final)
h = hashlib.md5(v.read_bytes()).hexdigest()
checar(loop_final.aplicar_no_lugar(v) is False and hashlib.md5(v.read_bytes()).hexdigest() == h,
       "LOOP_FINAL=0 não toca no arquivo")
os.environ.pop("LOOP_FINAL")
importlib.reload(loop_final)

print("\n[1][2][3] aplicado")
checar(loop_final.aplicar_no_lugar(v) is True, "aplicou")
dur1 = midia.duracao(v)
checar(abs(dur1 - dur0) <= 1 / 30 + 0.03, f"duração igual ({dur0:.3f} -> {dur1:.3f})")
fim, meio, comeco = cor(dur1 - 0.04), cor(3.0), cor(0.1)
print(f"       RGB começo {comeco.round()} | meio {meio.round()} | fim {fim.round()}")
checar(fim[0] > 150 and fim[2] < 100, "o último quadro é o vermelho do quadro 0")
checar(meio[2] > 150 and meio[0] < 100, "o meio continua azul")
checar(comeco[0] > 150, "o começo continua o mesmo")
antes, final = volume(dur1 - 1.0, 0.3), volume(dur1 - 0.05, 0.05)
print(f"       volume 1 s antes {antes:.0f} | últimos 50 ms {final:.0f}")
checar(antes > 1000, "a voz continua alta até perto do fim")
checar(final < antes * 0.5, "e termina com fade, sem estalo")

print("\n[5] ordem no main.py")
src = (RAIZ / "main.py").read_text(encoding="utf-8")
checar(src.index("loop_final.aplicar_no_lugar(_v)") > src.index("cascata.aplicar_no_lugar(_v"),
       "loop depois da camada/cascata")

print("\n[6] roteiro")
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")
from engine import traducao  # noqa: E402
checar("FINAL QUE VOLTA PRO COMEÇO" in traducao.PROMPT_NARRACAO, "narração tem a regra 12")
checar("FINAL QUE VOLTA PRO COMEÇO" not in traducao.PROMPT,
       "tradução literal (voice-over, fiel à fala) não tem")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
