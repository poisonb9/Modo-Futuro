# -*- coding: utf-8 -*-
"""Guarda de QUEM recebe a camada de balões (engine/camada.py).

POR QUE EXISTE

26/09/2026, dono: tirou a cascata de selos ("só vamos usar balão"), mandou
estender os balões a todos ("estende a todos") e o avião com a faixa também
("quero o avião com faixa em todos os canais"). Com a cascata desligada, canal
fora de `CANAIS` fica SEM CTA NENHUM — e nada no render reclama disso.

Roda com: python teste/teste_camada_canais.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import camada, cascata  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])
SETE = ("modofuturo", "semanestesia.pod", "atefalhar", "achadinhos.instantaneos",
        "truque.importado", "cozinha.importada", "fatura.chora")

print("\n[1] os sete canais recebem balões E avião")
for c in SETE:
    checar(camada.ligado(c) and camada.com_aviao(c), f"{c}: balões + avião")
checar(camada.ligado("@atefalhar"), "o @ também resolve")

print("\n[2] nenhum canal fica sem CTA (cascata desligada => camada obrigatória)")
checar(all(camada.ligado(c) or cascata.ligado(c) for c in SETE),
       "todo canal tem camada ou cascata")

print("\n[3] NEGATIVO: canal desconhecido não liga")
checar(not camada.ligado("canal_que_nao_existe"), "desconhecido: sem camada")

print("\n[4] o avião entra no plano de um clipe de 60 s; sem ele, só a parte A")
checar([k for k, _ in camada.plano(60, "tiktok", aviao=True)] == ["a", "b"], "com avião: a + b")
checar([k for k, _ in camada.plano(60, "tiktok", aviao=False)] == ["a"], "sem avião: só a")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
