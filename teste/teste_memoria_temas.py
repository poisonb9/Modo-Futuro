# -*- coding: utf-8 -*-
"""Memoria de temas: o motor sabe o que o canal ja' publicou (27/09/2026).

POR QUE EXISTE: no @modofuturo cada historia repetida rendeu menos (poeira
1.011 -> 327, maquina de 400 mi 730 -> 366). As frases abaixo sao
REFORMULACOES de temas ja' publicados (tem de marcar) e pautas NOVAS de
_privado/PAUTAS_MODOFUTURO.md (nao pode marcar). E, como no item 5, NADA e'
descartado: so' marca e reordena.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from engine import memoria_temas as m  # noqa: E402

falhas = []


def checar(ok, msg):
    print(("  ok    " if ok else "  FALHA ") + msg)
    if not ok:
        falhas.append(msg)


print("[1] a memoria existe e tem o canal")
checar(len(m.publicados("modofuturo")) >= 80, f"{len(m.publicados('modofuturo'))} publicados no modofuturo")
checar(m.publicados("canal-que-nao-existe") == [], "canal desconhecido: memoria vazia")

print("\n[2] reformulacao de tema ja' contado -> marca")
for t in ["Uma única poeira pode arruinar milhões em chips",
          "O erro microscópico que custa meio milhão na Intel",
          "A máquina de 400 milhões que só a Holanda sabe fazer"]:
    s, _ = m.mais_parecido(t, "modofuturo")
    checar(s >= m.LIMIAR, f"{s:.0%}  {t[:50]}")

print("\n[3] NEGATIVO: pauta nova -> nao marca")
for t in ["Espelhos da Zeiss: os mais lisos do planeta",
          "A usina nuclear que vai voltar a funcionar só para a IA",
          "O chip que um estudante fez na garagem"]:
    s, _ = m.mais_parecido(t, "modofuturo")
    checar(s < m.LIMIAR, f"{s:.0%}  {t[:50]}")

print("\n[4] marcar NAO descarta, so' reordena")
cl = [{"titulo": "Uma única poeira pode arruinar milhões em chips", "nota": 95},
      {"titulo": "O chip que um estudante fez na garagem", "nota": 90}]
out = m.marcar([dict(c) for c in cl], "modofuturo")
checar(len(out) == 2, "os dois continuam")
checar(out[0].get("tema_repetido") and out[0]["nota"] == 95 - m.PENALIDADE, "repetido marcado, -8 na ordem")
checar("tema_repetido" not in out[1], "novo sem marca")

print("\n[5] o bloco do prompt lista os publicados")
b = m.bloco_prompt("modofuturo")
checar("JA' PUBLICADOS NESTE CANAL" in b and "poeira" in b.lower(), "bloco com a lista")
checar(m.bloco_prompt(None) == "", "sem canal, sem bloco")

print("\ntudo verde" if not falhas else f"\n{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
