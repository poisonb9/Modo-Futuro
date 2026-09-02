# -*- coding: utf-8 -*-
"""O seletor ordena por RITMO e recusa o que nao vale o dinheiro.

⚠️ ORDENAR POR VIEWS TOTAIS PREMIA O POST MAIS VELHO, sempre. Um post de tres
dias com 500 views nao esta' indo melhor que um de seis horas com 150 — esta'
ha' mais tempo no ar. E o Bryan impulsionou por intuicao; se o criterio for
errado, o mesmo dinheiro compra menos.

⚠️ CASO NEGATIVO 1 — POST NOVO NAO PODE SER DESCARTADO POR MERITO. A metrica
do Buffer atrasa (MEDIDO: 2,7h -> 49% do real; 22,6h -> 99%), entao um post de
6h parece fraco por defeito da LEITURA. Ele sai da lista por idade, nao por
desempenho — e a diferenca importa: um dia ele volta.

⚠️ CASO NEGATIVO 2 — ZERO VIEWS NAO E' OPORTUNIDADE BARATA. Medimos que os
dois posts com ritmo zero eram os dois sem imagem de comida na abertura.
Pagar pra distribuir o que nao segura ninguem e' comprar audiencia pra ela
sair.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import escolher_impulsionar as ei  # noqa: E402

falhas = []
POSTS = [
    {"canal": "a", "titulo": "velho e grande", "views": 500, "idade_h": 72,
     "por_hora": 500 / 72, "curtidas": 0, "shares": 0},
    {"canal": "a", "titulo": "maduro e rapido", "views": 300, "idade_h": 30,
     "por_hora": 300 / 30, "curtidas": 0, "shares": 0},
    {"canal": "a", "titulo": "novo demais", "views": 150, "idade_h": 6,
     "por_hora": 25.0, "curtidas": 0, "shares": 0},
    {"canal": "a", "titulo": "zerado", "views": 0, "idade_h": 40,
     "por_hora": 0.0, "curtidas": 0, "shares": 0},
    {"canal": "a", "titulo": "antigo demais", "views": 900, "idade_h": 24 * 9,
     "por_hora": 900 / (24 * 9), "curtidas": 0, "shares": 0},
]
bons, fora = ei.escolher(POSTS)
nomes = [p["titulo"] for p in bons]
motivos = {p["titulo"]: m for p, m in fora}

# 1. POSITIVO — o de maior RITMO ganha, mesmo tendo menos views totais
if not nomes or nomes[0] != "maduro e rapido":
    falhas.append(f"o de maior ritmo nao ficou em 1o: {nomes}")
if "velho e grande" in nomes and nomes.index("velho e grande") == 0:
    falhas.append("ordenou por total — o post velho ganhou so' por ser velho")

# 2. NEGATIVO — o novo sai por IDADE, e o motivo tem de dizer isso
if "novo demais" in nomes:
    falhas.append("post de 6h entrou — a metrica dele ainda esta' baixa")
elif "novo demais" not in motivos or "novo" not in motivos["novo demais"]:
    falhas.append("o post novo saiu sem o motivo certo (parece rejeicao "
                  "por desempenho, e nao e')")

# 3. NEGATIVO — zero views fora
if "zerado" in nomes:
    falhas.append("post com ZERO views entrou na lista")

# 4. NEGATIVO — velho demais fora
if "antigo demais" in nomes:
    falhas.append("post de 9 dias entrou — a entrega organica ja' acabou")

# 5. os limites existem e sao razoaveis
if ei.IDADE_MIN_H < 20:
    falhas.append(f"idade minima baixa demais ({ei.IDADE_MIN_H}h) — a metrica "
                  "ainda nao assentou")
if ei.IDADE_MAX_H < 24 * 3:
    falhas.append("idade maxima curta demais — descartaria post ainda vivo")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_seletor_impulso: ritmo manda, {len(fora)} descartados "
      "com motivo proprio")
