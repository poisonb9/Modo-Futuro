# -*- coding: utf-8 -*-
"""Plano aberto sem rosto + pulso de zoom na palavra de ênfase.

POR QUE EXISTE

26/09/2026, aprovado pelo dono depois da prévia da ILLIT (run 36206642639):
em 2 de 16 quadros o crop ficou em close na nuca/cabelo, porque a pessoa virou
e o detector perdeu o rosto. Agora, sem rosto por >= 1,2 s num clipe que TEM
rosto, o quadro abre (16:9 inteiro sobre o próprio vídeo desfocado). E cada
frase ganha um pulso de +5% no início da palavra mais forte (acervo F133628).

  [1] trechos_abertos: junta amostras seguidas, ignora buraco curto
  [2] NEGATIVO: clipe quase sem rosto (receita) não abre nunca
  [3] render real: no trecho aberto o topo é fundo desfocado; fora, é crop
  [4] ênfase: número > "!" > palavra longa; longe do corte; conectivo não
  [5] o pulso sobe e desce (triângulo) e some fora da janela

Roda com: python teste/teste_enquadramento_aberto_enfase.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402
from engine import enquadrar, render  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])

print("\n[1] trechos sem rosto")
enquadrar.ULTIMA_ANALISE = {"passo": 0.5, "cobertura": 0.8,
                            "sem_rosto": [2.0, 2.5, 3.0, 3.5, 7.0, 10.0, 10.5, 11.0]}
t = enquadrar.trechos_abertos()
print(f"       {t}")
checar(t == [(2.0, 4.0), (10.0, 11.5)], "2,0-4,0 e 10,0-11,5; o 7,0 isolado fica de fora")

print("\n[2] NEGATIVO: clipe sem rosto quase nenhum")
enquadrar.ULTIMA_ANALISE["cobertura"] = 0.1
checar(enquadrar.trechos_abertos() == [], "cobertura 10% = não abre")
enquadrar.ULTIMA_ANALISE = {}
checar(enquadrar.trechos_abertos() == [], "sem análise = não abre")

print("\n[3] render real")
T = Path(tempfile.mkdtemp())
src = T / "s.mp4"
# fonte 16:9 de RUÍDO (detalhe em todo pixel) — o fundo desfocado perde isso
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                "nullsrc=s=1920x1080:r=30:d=4,geq=lum='random(1)*255':cb=128:cr=128",
                "-pix_fmt", "yuv420p", str(src)], check=True)
f = enquadrar.filtro_vertical(1920, 1080, [(0.0, 0.5), (4.0, 0.5)], [(2.0, 3.0)])
render.midia.fps = lambda _b: 30.0
mov = render._zoom_por_frase(src, 1080, 1920, [1.0], [2.2])
out = T / "o.mp4"
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", f + mov,
                    str(out)], capture_output=True, text=True)
checar(r.returncode == 0, f"ffmpeg aceita a cadeia com split/overlay + zoompan {r.stderr[-160:]}")


def quadro(seg):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(seg), "-i", str(out),
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080).astype(float)


def detalhe_topo(img):
    faixa = img[80:400]          # topo: no aberto é só fundo desfocado
    return float(np.abs(np.diff(faixa, axis=1)).mean())


normal, aberto = detalhe_topo(quadro(0.5)), detalhe_topo(quadro(2.5))
print(f"       detalhe no topo: crop {normal:.1f} | aberto {aberto:.1f}")
checar(aberto < normal * 0.5, "no trecho aberto o topo é fundo desfocado")
checar(detalhe_topo(quadro(3.5)) > aberto * 2, "depois do trecho volta o crop")

print("\n[4] palavra de ênfase")
ps = [{"palavra": w, "inicio": 0.5 * i, "fim": 0.5 * i + 0.45} for i, w in enumerate(
    "e aqui a gente tem incrivelmente 400 pessoas que".split())]
e = render.enfases_da_fala(ps, [])
checar(e == [3.0], f"número ganha da palavra longa ({e})")
ps2 = [{"palavra": w, "inicio": 0.5 * i, "fim": 0.5 * i + 0.45} for i, w in enumerate(
    "ela ficou muito assustada demais".split())]
checar(render.enfases_da_fala(ps2, []) == [1.5], "sem número: a mais longa (assustada)")
checar(render.enfases_da_fala(ps2, [1.7]) == [], "colada no corte (< 0,5 s) não pulsa")
fracas = [{"palavra": w, "inicio": 0.5 * i, "fim": 0.5 * i + 0.4} for i, w in enumerate(
    "e a o de um que".split())]
checar(render.enfases_da_fala(fracas, []) == [], "só conectivo = sem pulso")

print("\n[5] forma do pulso")
AMB = {"_gte": lambda a, b: 1 if a >= b else 0, "_mod": lambda a, b: a % b,
       "min": min, "max": max, "abs": abs}


def expr(enf):
    z = re.search(r"z='([^']+)'", render._zoom_por_frase(src, 1080, 1920, [], enf)).group(1)
    return z.replace("gte(", "_gte(").replace("mod(", "_mod(")


com, sem = expr([2.0]), expr([])


def pulso(on):   # só o pulso: zoom com ênfase menos zoom sem
    return eval(com, {**AMB, "on": on}) - eval(sem, {**AMB, "on": on})


print(f"       59:{pulso(59):.3f} 63:{pulso(63):.3f} 66:{pulso(66):.3f} "
      f"69:{pulso(69):.3f} 80:{pulso(80):.3f}")
checar(abs(pulso(66) - 0.05) < 1e-6, "no pico +5% (2,0 s * 30 + meia janela = quadro 66)")
checar(pulso(59) < 1e-9 and pulso(80) < 1e-9, "fora da janela, zero")
checar(0 < pulso(63) < pulso(66) and 0 < pulso(69) < pulso(66), "sobe e desce sem salto")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
