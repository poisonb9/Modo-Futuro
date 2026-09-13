# -*- coding: utf-8 -*-
"""O corte editorial tira o obvio e NAO tira o que rende."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import rende_video as rv  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


print("1. NEGATIVO — o que a pessoa ja' compra no automatico NAO rende")
# ⚠️ Sao nomes REAIS que o /highlights devolveu em 13/09/2026.
for nome in ("Papel Higiênico Supreme Folha Tripla 24 Rolos Neve",
             "Papel Higiênico Neve Toque Da Seda Folha Dupla 30 M",
             "Sabão Líquido Omo Lavagem Perfeita 900ml Refil",
             "Percarbonato De Sódio 100% Puro Tira Manchas Alvejante",
             "O Boticário Insensatez Deo Colônia 100ml"):
    ok, porque = rv.rende(nome)
    checar(not ok, f"{nome[:38]}… -> fora ({porque})")

print("\n2. ⭐ E O QUE RENDE TEM DE PASSAR — senao o filtro so' esvazia a lista")
for nome in ("Creatina 250g Suplemento Monohidratada em pó 100%",
             "Creme Multirreparador Pele Sensível Cicaplast Baume B5+",
             "Conjunto de pincéis de maquiagem profissional Kabuki",
             "Cortador de Melancia em Aço Inoxidável 2 em 1",
             "20 Peças de Organizadores de Cabos Adesivos",
             "Omegafor Plus 120 Cápsulas Ômega 3 Vitafor"):
    ok, porque = rv.rende(nome)
    checar(ok, f"{nome[:40]}… -> passa")

print("\n3. NEGATIVO — o filtro nao pode casar DENTRO de outra palavra")
# ⚠️ "neve" esta' em "neveira"; "veja" em "vejam". Filtro que casa demais
# reprova calado, e o produto so' some da lista sem ninguem notar.
for nome in ("Geladeira Neveira Portátil 12v para Carro",
             "Óculos de sol Vejam Style unissex"):
    ok, porque = rv.rende(nome)
    checar(ok, f"{nome[:36]}… -> passa (nao casou dentro da palavra)")

print("\n4. sem nome, nao rende")
checar(not rv.rende("")[0], "vazio -> fora")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
