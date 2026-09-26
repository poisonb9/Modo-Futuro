# -*- coding: utf-8 -*-
"""Guarda da mistura do FUNDO original sob a dublagem (engine/fundo.py).

POR QUE EXISTE

Item 1 da dublagem (26/09/2026, "Aplica Demucs!!!!"). O Demucs so' roda na
nuvem; o que da' pra guardar aqui e' a MISTURA, com sinais sinteticos:
fundo = ruido rosa continuo, dublagem = tom de 1 a 3 s.

  [1] o fundo ABAIXA enquanto a voz fala e VOLTA na pausa (sidechain)
  [2] depois de `ate_s` o fundo SOME — a cauda devolve o original inteiro
      ali, e somar os dois dobraria o fundo
  [3] voice-over: o original abaixa so' durante a fala (era 0,18 fixo)
  [4] NEGATIVO: sem Demucs, `misturar` devolve None (falha aberta) e o
      clipe segue so' com a voz, como antes
  [5] desligado por padrao ate' o dono aprovar pela previa

Roda com: python teste/teste_fundo.py
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import fundo  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


T = Path(tempfile.mkdtemp())
ISO = "bandreject=f=440:width_type=h:w=60,"   # tira o tom: sobra so' o fundo


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def rms(arq, a, b):
    r = subprocess.run(["ffmpeg", "-v", "info", "-ss", str(a), "-t", str(b - a), "-i",
                        str(arq), "-af", ISO + "astats=metadata=0", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"RMS level dB:\s*(-?[\d.]+|-inf)", r.stderr)
    return float(m[-1]) if m and m[-1] != "-inf" else -200.0


print(__doc__.splitlines()[0])
ff("-f", "lavfi", "-i", "anoisesrc=d=8:c=pink:a=0.3", "-ar", "44100", "-ac", "2", str(T / "f.wav"))
ff("-f", "lavfi", "-i", "sine=f=440:d=8", "-af",
   "volume='if(between(t,1,3),1,0)':eval=frame", "-ar", "44100", str(T / "d.wav"))

ff("-i", str(T / "f.wav"), "-i", str(T / "d.wav"), "-filter_complex",
   fundo.filtro_mix(6.0), "-map", "[a]", str(T / "mix.wav"))
antes, fala, depois, fim = (rms(T / "mix.wav", 0.2, 0.9), rms(T / "mix.wav", 1.3, 2.7),
                            rms(T / "mix.wav", 3.6, 4.9), rms(T / "mix.wav", 6.3, 7.8))
print(f"       pausa {antes:.1f} | fala {fala:.1f} | pausa {depois:.1f} | fim {fim:.1f} dB")

print("\n[1] ducking")
checar(fala < antes - 8, f"fundo abaixa >8 dB com a voz ({antes - fala:.1f} dB)")
checar(abs(depois - antes) < 3, "fundo volta na pausa")
checar(antes > -40, "na pausa o fundo é AUDÍVEL (não sumiu de vez)")

print("\n[2] corte onde a cauda entra")
checar(fim < -90, "depois de ate_s o fundo some")
ff("-i", str(T / "f.wav"), "-i", str(T / "d.wav"), "-filter_complex",
   fundo.filtro_mix(None), "-map", "[a]", str(T / "sem_corte.wav"))
checar(rms(T / "sem_corte.wav", 6.3, 7.8) > -40, "NEGATIVO: sem ate_s o fundo segue até o fim")

print("\n[3] voice-over com ducking")
ff("-i", str(T / "f.wav"), "-i", str(T / "d.wav"), "-filter_complex",
   fundo.filtro_voice_over() + ";[vo]anull[a]", "-map", "[a]", str(T / "vo.wav"))
p, f_ = rms(T / "vo.wav", 0.2, 0.9), rms(T / "vo.wav", 1.3, 2.7)
checar(f_ < p - 8, f"original abaixa na fala ({p - f_:.1f} dB) e é audível na pausa ({p:.1f} dB)")

print("\n[4] NEGATIVO: sem Demucs, falha aberta")
real = fundo.MODELO
fundo.MODELO = "modelo_que_nao_existe"
checar(fundo.misturar(T / "f.wav", T / "d.wav", T / "x.wav") is None,
       "misturar devolve None e não levanta")
fundo.MODELO = real

print("\n[5] desligado por padrão")
checar(os.environ.get("FUNDO_ORIGINAL") == "1" or fundo.LIGADO is False,
       "sem FUNDO_ORIGINAL=1, LIGADO é False")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
