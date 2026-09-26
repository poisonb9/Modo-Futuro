# -*- coding: utf-8 -*-
"""A dublagem acompanha o original até o fim (frases ANCORADAS).

POR QUE EXISTE

Medido em 26/09/2026 nas 12 últimas runs: de 71 clipes dublados, 70
terminavam a narração CEDO (2,5 a 35,7 s de silêncio no fim, típico ~19 s).
As frases eram emendadas desde 0 s com pausa ≤ 0,6 s. Agora cada frase
começa quando a fala original dela começa (`voz_clonada._ancorar`).

O Chatterbox não roda aqui: `_falar` vira um tom com ~0,4 s por palavra,
e o resto do `gerar_trilha` é o de verdade.

  [1] a última frase termina perto do fim da fala original (não 20 s antes)
  [2] frases não se sobrepõem
  [3] o timing da legenda bate com o áudio MEDIDO (silencedetect)
  [4] NEGATIVO: com DUB_ANCORAR=0 (modo antigo) a narração acaba cedo
  [5] frase longa que invade a próxima empurra, não sobrepõe

Roda com: python teste/teste_voz_ancorada.py
"""
import importlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def carregar(ancorar: bool):
    os.environ["DUB_ANCORAR"] = "1" if ancorar else "0"
    from engine import voz_clonada
    v = importlib.reload(voz_clonada)

    def falso(texto, destino, amostra, idioma, enfase=None):
        d = 0.4 * len(texto.split())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        f"sine=f=330:d={d:.2f}", "-ar", "24000", str(destino)], check=True)
        return destino
    v._falar = falso
    return v


# 60 s de clipe; o original fala em 4 blocos espalhados de 2 s a 55 s
SEG = [{"inicio": 2.0, "fim": 12.0, "texto": "Essa sala custa milhões. Uma poeira destrói tudo."},
       {"inicio": 16.0, "fim": 28.0, "texto": "O ar passa por filtros o tempo todo."},
       {"inicio": 31.0, "fim": 42.0, "texto": "Ninguém entra sem a roupa completa."},
       {"inicio": 45.0, "fim": 55.0, "texto": "E a pressão fica positiva sempre."}]
TOTAL = 60.0
amostra = Path(tempfile.mkdtemp()) / "a.wav"
amostra.write_bytes(b"x")


def silencios(arq):
    r = subprocess.run(["ffmpeg", "-i", str(arq), "-af", "silencedetect=n=-40dB:d=0.05",
                        "-f", "null", "-"], capture_output=True, text=True)
    ini = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return ini


print(__doc__.splitlines()[0])

v = carregar(True)
audio, timing = v.gerar_trilha(SEG, TOTAL, Path(tempfile.mkdtemp()), amostra)
fim_voz = timing[-1]["fim"]
print(f"       ancorada: {len(timing)} frases, voz de {timing[0]['inicio']:.1f}s a {fim_voz:.1f}s")

print("\n[1] cada frase que abre um segmento começa junto com a fala original dele")
inicios = [round(t["inicio"], 1) for t in timing]
print(f"       inícios {inicios} (original: 2, 16, 31, 45)")
for alvo in (2.0, 16.0, 31.0, 45.0):
    checar(any(abs(i - alvo) < 0.3 for i in inicios), f"tem frase começando em ~{alvo:.0f}s")
checar(fim_voz > 45, f"a voz vai até o último bloco ({fim_voz:.1f}s)")
checar(abs(v.midia.duracao(audio) - TOTAL) < 0.3, "trilha tem a duração do clipe")

print("\n[2] sem sobreposição")
checar(all(b["inicio"] >= a["fim"] - 1e-6 for a, b in zip(timing, timing[1:])),
       "cada frase começa depois da anterior terminar")

print("\n[3] timing == áudio medido")
entradas = silencios(audio)   # onde cada trecho de som COMEÇA
ok = all(any(abs(t["inicio"] - e) < 0.15 for e in entradas) for t in timing[1:])
checar(ok, "cada início do timing tem som começando ali (±0,15 s)")

print("\n[4] NEGATIVO: modo antigo acaba cedo")
v0 = carregar(False)
_, t0 = v0.gerar_trilha(SEG, TOTAL, Path(tempfile.mkdtemp()), amostra)
print(f"       antigo: voz termina em {t0[-1]['fim']:.1f}s")
checar(t0[-1]["fim"] < fim_voz - 10, "modo antigo termina >10 s antes")

print("\n[5] frase que invade empurra a próxima")
ini = v._ancorar([5.0, 2.0], [(0.0, 3.0), (3.0, 6.0)])
checar(ini[1] >= 5.0 + v._PAUSA_MIN_S - 1e-9, f"2a frase empurrada pra {ini[1]:.2f}s")

os.environ.pop("DUB_ANCORAR", None)
print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
