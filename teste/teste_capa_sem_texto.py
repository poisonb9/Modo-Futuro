# -*- coding: utf-8 -*-
"""A capa (quadro 0) nao pode ter texto queimado da fonte atras do titulo.

POR QUE EXISTE (27/09/2026, dono aprovou): a grade do @modofuturo e do
@achadinho.make misturava as nossas caixas de titulo com texto grande do video
original ("Futuro Tem Preço", "Está Fora do Jogo?"). A nitidez PREFERE esses
quadros (letra = borda). Os numeros abaixo sao os MEDIDOS com o EasyOCR nas
capas reais (% da area com letras fora da faixa do titulo, a cada ~0,6 s).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from engine import capa_nitida as c  # noqa: E402

falhas = []


def checar(ok, msg):
    print(("  ok    " if ok else "  FALHA ") + msg)
    if not ok:
        falhas.append(msg)


print("[1] quadro com texto nunca vira capa, mesmo sendo o mais nitido")
# SUJO_futuro medido: 3 / 23 / 43 / 3 — e os sujos sao os mais "nitidos"
am = [(0.0, 100.0, 3.1), (0.6, 400.0, 22.5), (1.2, 500.0, 42.7), (1.8, 110.0, 3.1)]
t, n, trocar = c.escolher(am)
checar(t in (0.0, 1.8), f"escolheu {t}s (nao 0,6/1,2 com texto)")

print("\n[2] quadro 0 sujo e ha' limpo: troca MESMO sem ganho de nitidez")
# SUJO_energia medido: 48 / 3 / 3 / 3
am = [(0.0, 300.0, 48.4), (0.6, 120.0, 3.2), (1.2, 110.0, 2.8), (1.8, 100.0, 3.1)]
t, n, trocar = c.escolher(am)
checar(trocar and t == 0.6, f"troca pro limpo mais nitido ({t}s)")

print("\n[3] NEGATIVO: limpo e sem ganho de nitidez -> nao mexe")
am = [(0.0, 100.0, 2.2), (0.6, 105.0, 2.3), (1.2, 108.0, 4.5)]
checar(not c.escolher(am)[2], "nao reprocessa a toa")

print("\n[4] sem OCR (None): volta ao criterio so' de nitidez")
am = [(0.0, 100.0, None), (0.6, 200.0, None)]
t, n, trocar = c.escolher(am)
checar(trocar and t == 0.6, "sem OCR, o mais nitido como antes")

print("\n[5] tudo sujo: nao inventa")
am = [(0.0, 100.0, 40.0), (0.6, 200.0, 30.0)]
checar(not c.escolher(am)[2], "sem quadro limpo, fica como esta'")

print("\ntudo verde" if not falhas else f"\n{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
