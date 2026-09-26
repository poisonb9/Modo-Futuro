# -*- coding: utf-8 -*-
"""Guarda do card de título PREMIUM (engine/render.py) e do título de tela
curto (engine/ab_titulo.py).

POR QUE EXISTE

Autópsia de 26/09/2026: o card estava a 4,0% da altura, MENOR que a legenda
premium (5,8%); o título do post (45-60 letras) ia inteiro pra tela e
encolhia até 55% em 3 linhas; a quebra enchia a linha e sobrava "mundo"
sozinho; o destaque era só caixa alta, sem cor.

⚠️ O QUE O PROTÓTIPO ENSINOU: com 51 letras até o premium sai MENOR que o
atual (maiúscula ocupa mais). A alavanca é o comprimento — por isso [5] e [6]
guardam o encurtamento, não só o desenho.

Roda com: python teste/teste_titulo_premium.py
"""
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

from engine import render, destaque, ab_titulo, modelo_texto  # noqa: E402
from PIL import Image  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


F = render.FONTE_TITULO_CAIXA
W, H = 1080, 1920
MAXPX = W * render.TITULO_MARGEM
IDEAL = round(H * render.TITULO_CORPO_FRAC)


def linhas(texto):
    ws = texto.split()
    enf = {w for w in ws if len(w) > 1 and w.isupper()}
    return render._linhas_premium([w.upper() for w in ws], enf, F, MAXPX, IDEAL)


print(__doc__.splitlines()[0])

print("\n[1] título curto: corpo cheio, sem órfã, destaque inteiro")
ls, corpo = linhas("A sala MAIS LIMPA do mundo")
print("       ", ls, corpo)
checar(corpo == IDEAL, f"corpo {corpo} = ideal {IDEAL} (5,4%)")
checar(all(len(l.split()) > 1 for l in ls), "nenhuma linha com UMA palavra sobrando")
checar(any("MAIS LIMPA" in l for l in ls), "'MAIS LIMPA' fica na mesma linha")
checar(not any(l.split()[-1].lower() in render._TITULO_FRACA for l in ls[:-1]),
       "nenhuma linha termina em palavra fraca")

print("\n[2] NEGATIVO: o card antigo tinha a órfã (o teste enxerga o defeito)")
velhas, _ = render._ajustar_titulo("A sala MAIS LIMPA do mundo", F, W, round(H * 0.040))
checar(len(velhas[-1].split()) == 1, f"quebra antiga deixava {velhas[-1]!r} sozinha")

print("\n[3] hierarquia: o título não é menor que a legenda")
from engine import legendas  # noqa: E402
checar(render.TITULO_CORPO_FRAC >= legendas._PREMIUM_CORPO * 0.9,
       f"título {render.TITULO_CORPO_FRAC:.1%} x legenda {legendas._PREMIUM_CORPO:.1%}")

print("\n[4] a pílula âmbar aparece só quando há destaque")
tmp = Path(tempfile.mkdtemp())


def ambar(texto):
    destaque.marcar_titulo = lambda t, _t=texto: _t
    im = Image.open(render.imagem_titulo(texto, W, H, tmp)).convert("RGB")
    return sum(1 for p in im.getdata() if p[0] > 240 and 190 < p[1] < 230 and p[2] < 40)


checar(ambar("China BANIDA dos microchips") > 2000, "com destaque: tem pílula")
checar(ambar("China banida dos microchips") == 0, "NEGATIVO sem destaque: nenhuma pílula")
checar(ambar("CHINA BANIDA DOS MICROCHIPS") == 0,
       "NEGATIVO título todo gritado: não vira pílula inteira")

print("\n[5] título longo vai pra tela ENCURTADO (os dois grupos)")
LONGO = "Por Que a China Foi Banida do Mercado de Microchips Avancados"
respostas = {}
modelo_texto.perguntar = lambda p, **k: respostas["r"]
ab_titulo.grupo = lambda f, i: "A"
respostas["r"] = "China banida dos microchips"
c = {"titulo": LONGO}
t = ab_titulo.aplicar(c, "x")
checar(t == "China banida dos microchips" and c["titulo_tela_curto"] is True,
       f"A: {t!r}")
ab_titulo.grupo = lambda f, i: "B"
respostas["r"] = "Por que a China foi banida dos chips?"
c = {"titulo": LONGO}
t = ab_titulo.aplicar(c, "x")
checar(t.endswith("?") and len(t) <= ab_titulo.MAX_CHARS + 5 and c["ab_titulo"] == "B",
       f"B: pergunta curta {t!r}")

print("\n[6] NEGATIVO: modelo fora ou resposta longa -> fica o original, marcado")
ab_titulo.grupo = lambda f, i: "A"
respostas["r"] = None
c = {"titulo": LONGO}
checar(ab_titulo.aplicar(c, "x") == LONGO and c["titulo_tela_curto"] is False,
       "modelo fora: título original, titulo_tela_curto=False")
respostas["r"] = "Um titulo que o modelo devolveu comprido demais pra caber na tela"
c = {"titulo": LONGO}
checar(ab_titulo.aplicar(c, "x") == LONGO, "resposta longa é recusada")
respostas["r"] = "Por que a China foi banida?"
c = {"titulo": LONGO}
checar(ab_titulo.aplicar(c, "x") == LONGO, "A não vira pergunta pelo encurtamento")
c = {"titulo": "A sala mais limpa do mundo"}
respostas["r"] = "NAO DEVIA SER CHAMADO"
checar(ab_titulo.aplicar(c, "x") == "A sala mais limpa do mundo",
       "título que já cabe não passa pelo modelo")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
