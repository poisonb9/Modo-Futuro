# -*- coding: utf-8 -*-
"""O teto de cortes em voo segue a cota MEDIDA, nao um numero fixo.

Pergunta do Bryan em 01/09/2026: "se colocarmos mais um pra cortar, de 3 em 3,
sera' que da' problema?"

MEDIDO: 3 nao consome MAIS cota — consome mais RAPIDO. Os mesmos videos fazem
as mesmas chamadas (~3 a 6 por run). O que muda e' o PREJUIZO quando a cota
acaba: um run que morre ja' pagou corte, transcricao e as vezes render, 40 a
100 min de runner. Com 2 em voo perdem-se dois; com 3, tres.

⚠️ O TETO PEDIDO E' MAXIMO, NUNCA MINIMO. Cota folgada nao pode autorizar
passar do que o Bryan pediu — so' permite CHEGAR la'. Sem esta regra, uma
medicao otimista viraria os 10 runs paralelos de 31/08, que mataram nove.

⚠️ E SEM MEDIDA, NADA MUDA. Falha ABERTA: se a sonda nao devolver contagem, o
teto e' o que foi pedido. Um teto derivado de leitura ausente seria pior que
o numero fixo que ele substitui.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cortar_fila as cf  # noqa: E402

falhas = []
CASOS = [
    # (motivo da sonda, teto pedido, teto esperado, por que)
    ("7 de 14 chaves com cota (7 ok)", 3, 3, "cota folgada usa o teto pedido"),
    ("3 de 14 chaves com cota (3 ok, 11 sem cota)", 3, 2, "apertada desce pra 2"),
    ("1 de 14 chaves com cota (1 ok, 13 sem cota)", 3, 1, "no fim, um de cada vez"),
    ("0 de 14 chaves com cota", 3, 1, "sem chave util, um de cada vez"),
    # ⚠️ NEGATIVO: cota folgada NAO pode passar do pedido
    ("14 de 14 chaves com cota (14 ok)", 2, 2, "folgada nao ultrapassa o pedido"),
    ("14 de 14 chaves com cota (14 ok)", 1, 1, "pedido de 1 continua 1"),
    # ⚠️ NEGATIVO: sem contagem, nada muda
    ("sem chave pra sondar — seguindo sem sonda", 3, 3, "sem medida, teto pedido"),
]
for motivo, pedido, esperado, porque in CASOS:
    teto, _ = cf.teto_pela_cota(motivo, pedido)
    if teto != esperado:
        falhas.append(f"{porque}: esperava {esperado}, veio {teto} ({motivo[:34]})")

# o teto nunca pode ser zero — isso pararia a fila em silencio
for motivo, pedido, _, _ in CASOS:
    if cf.teto_pela_cota(motivo, pedido)[0] < 1:
        falhas.append(f"teto zerado para {motivo[:40]!r} — fila travaria calada")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_teto_adaptativo: {len(CASOS)} cenarios, teto entre 1 e o "
      "pedido, nunca acima e nunca zero")
