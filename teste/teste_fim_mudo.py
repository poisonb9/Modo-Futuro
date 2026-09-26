# -*- coding: utf-8 -*-
"""Fim mudo: a ultima frase da dublagem sumia (RETOMADA §1.1).

POR QUE EXISTE

26/09/2026. As trilhas guardadas na previa (engine/diagnostico.py) mostraram
a mistura do fundo saindo 82,4 s para uma dublagem de 85,3 s — conteudo
identico ate' ali (correlacao 1,0), e depois nada. O ffmpeg 6.1 do runner
perde ~3 s do fim (lookahead do loudnorm); o `preencher_com_original` perdia
outros ~3 s: o "zero digital" de 4-7 s em cima da ultima legenda. O ffmpeg 8
local nao tem o defeito — por isso este teste confere a RECEITA (folga +
corte exato) alem do resultado.

  [1] com `dur`, cada entrada ganha folga ANTES do loudnorm e a saida e'
      cortada em `dur` exato
  [2] audio real: a mistura tem o tamanho da dublagem e o ultimo segundo
      ainda tem a voz
  [3] preencher_com_original: tamanho da maior entrada, voz no fim
  [4] a trava: mistura mais curta que a dublagem e' DESCARTADA (a fala vai
      inteira, sem fundo) — pega o defeito mesmo se voltar por outro caminho
  [5] NEGATIVO: sem `dur` o filtro e' o de antes

Roda com: python teste/teste_fim_mudo.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import cauda, fundo  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


T = Path(tempfile.mkdtemp())


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def rms_tom(arq, a, b):
    """nivel do tom de 440 Hz (a 'voz') entre a e b s."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-ss", str(a), "-t", str(b - a), "-i", str(arq),
                        "-af", "bandpass=f=440:width_type=h:w=40,astats=metadata=0",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"RMS level dB:\s*(-?[\d.]+|-inf)", r.stderr)
    return float(m[-1]) if m and m[-1] != "-inf" else -200.0


print("[1] a receita no filtro")
f = fundo.filtro_mix(20.0, [(2.0, 3.0)], dur=12.5)
ins = re.findall(r"\[(\d):a\]([^;]*)", f)
checar(all(corpo.startswith("apad=pad_dur=") and "loudnorm" in corpo for _, corpo in ins),
       "toda entrada tem folga antes do loudnorm")
checar(f.endswith("[m];[m]atrim=end=12.500[a]"), "saida cortada em dur exato")
f3 = fundo.filtro_mix(None, None, 0.16, [], dur=12.5)
checar(f3.count("apad=pad_dur=") == 3 and f3.endswith("atrim=end=12.500[a]"),
       "tambem com a voz original (3 entradas)")

print("\n[2] audio real: mistura do fundo")
# 'voz' ate' o fim: tom de 10 a 12,5 s (a ULTIMA frase), fundo de ruido
ff("-f", "lavfi", "-i", "sine=f=440:d=12.5", "-af",
   "volume='if(between(t,10,12.5),1,0)':eval=frame", "-ar", "44100", str(T / "d.wav"))
ff("-f", "lavfi", "-i", "anoisesrc=d=12.6:c=pink:a=0.1", "-ar", "44100", "-ac", "2",
   str(T / "f.wav"))
dur = fundo._duracao(T / "d.wav")
ff("-i", str(T / "f.wav"), "-i", str(T / "d.wav"), "-filter_complex",
   fundo.filtro_mix(None, None, dur=dur), "-map", "[a]", "-ar", "44100", str(T / "m.wav"))
dm = fundo._duracao(T / "m.wav")
checar(abs(dm - dur) < 0.05, f"mistura {dm:.2f}s = dublagem {dur:.2f}s")
checar(rms_tom(T / "m.wav", 11.4, 12.3) > -30, "a ultima frase esta' no ultimo segundo")

print("\n[3] preencher_com_original")
r = cauda.preencher_com_original(T / "f.wav", T / "m.wav", [{"fim": 12.4}], T / "fim.wav")
df = fundo._duracao(T / "fim.wav") if r else 0
checar(r is not None and abs(df - max(dur, fundo._duracao(T / "f.wav"))) < 0.05,
       f"tamanho da maior entrada ({df:.2f}s)")
checar(r is not None and rms_tom(T / "fim.wav", 11.4, 12.3) > -30,
       "a ultima frase continua la'")

print("\n[4] a trava: mistura curta e' descartada")
ff("-i", str(T / "m.wav"), "-t", "9.5", str(T / "curta.wav"))
checar(fundo.inteira(T / "curta.wav", T / "d.wav") is False, "3 s mais curta = descartada")
checar(fundo.inteira(T / "m.wav", T / "d.wav") is True, "do tamanho certo = aceita")
checar(fundo.inteira(T / "nao_existe.wav", T / "d.wav") is True, "sem medida nao barra")

print("\n[5] NEGATIVO: sem dur, o filtro de antes")
checar("apad" not in fundo.filtro_mix(6.0) and fundo.filtro_mix(6.0).endswith("normalize=0[a]"),
       "sem folga nem corte")

print(f"\n{'FALHOU: ' + str(len(falhas)) if falhas else 'tudo verde'}")
sys.exit(1 if falhas else 0)
