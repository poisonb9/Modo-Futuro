# -*- coding: utf-8 -*-
"""Sem rosto -> segue o movimento em tela cheia; pulso na palavra de ênfase.

POR QUE EXISTE

26/09/2026, prévia da ILLIT (run 36206642639): em 2 de 16 quadros o crop
ficou em close na nuca, porque a pessoa virou e o detector perdeu o rosto.
⛔ A 1ª correção (plano aberto: 16:9 pequeno sobre fundo desfocado) foi
REPROVADA pelo dono: "fica um vídeo pequeno na tela vertical". Agora, sem
rosto por >= 1,2 s num clipe que TEM rosto, o crop 9:16 continua em tela
cheia e segue o movimento. E cada frase ganha um pulso de +5% na palavra
mais forte (acervo F133628).

  [1] trechos_sem_rosto: junta amostras seguidas, ignora buraco curto
  [2] NEGATIVO: clipe quase sem rosto (receita) não entra nessa regra
  [3] o movimento só entra DENTRO dos trechos; o render é SEMPRE tela cheia
      (nada de split/overlay/fundo desfocado — NEGATIVO do plano aberto)
  [4] ênfase: número > "!" > palavra longa; longe do corte; conectivo não
  [5] o pulso sobe e desce (triângulo) e some fora da janela

Roda com: python teste/teste_enquadramento_sem_rosto_enfase.py
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
t = enquadrar.trechos_sem_rosto()
print(f"       {t}")
checar(t == [(2.0, 4.0), (10.0, 11.5)], "2,0-4,0 e 10,0-11,5; o 7,0 isolado fica de fora")

print("\n[2] NEGATIVO: clipe sem rosto quase nenhum")
enquadrar.ULTIMA_ANALISE["cobertura"] = 0.1
checar(enquadrar.trechos_sem_rosto() == [], "cobertura 10% = regra não entra")
enquadrar.ULTIMA_ANALISE = {}
checar(enquadrar.trechos_sem_rosto() == [], "sem análise = regra não entra")

print("\n[3] movimento só no buraco, e tela cheia sempre")
rosto = [(0.0, 0.3), (1.5, 0.3), (4.5, 0.3), (6.0, 0.3)]
mov = [(0.5, 0.9), (2.0, 0.8), (3.0, 0.8), (5.0, 0.9)]
c = enquadrar.preencher_com_movimento(rosto, mov, [(2.0, 4.0)])
checar(c == [(0.0, 0.3), (1.5, 0.3), (2.0, 0.8), (3.0, 0.8), (4.5, 0.3), (6.0, 0.3)],
       f"só os pontos de 2,0 e 3,0 entram ({c})")
f = enquadrar.filtro_vertical(1920, 1080, c)
checar("split" not in f and "overlay" not in f and "boxblur" not in f,
       "sem fundo desfocado nem vídeo pequeno (plano aberto reprovado)")
T = Path(tempfile.mkdtemp())
src = T / "s.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                "nullsrc=s=1920x1080:r=30:d=6,geq=lum='random(1)*255':cb=128:cr=128",
                "-pix_fmt", "yuv420p", str(src)], check=True)
render.midia.fps = lambda _b: 30.0
out = T / "o.mp4"
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf",
                    f + render._zoom_por_frase(src, 1080, 1920, [1.0], [2.2]), str(out)],
                   capture_output=True, text=True)
checar(r.returncode == 0, f"ffmpeg aceita {r.stderr[-160:]}")


def detalhe(seg, y0, y1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(seg), "-i", str(out),
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(1920, 1080).astype(float)
    return float(np.abs(np.diff(img[y0:y1], axis=1)).mean())


topo = [detalhe(s, 80, 400) for s in (0.5, 2.5, 3.5, 5.0)]
print(f"       detalhe no topo em 0,5/2,5/3,5/5,0 s: {[round(x) for x in topo]}")
checar(min(topo) > 20, "imagem de verdade no topo o tempo todo (tela cheia)")

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
