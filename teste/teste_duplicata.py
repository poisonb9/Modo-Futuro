"""Guarda da dedupe de produto repetido no catalogo.

⚠️ OFFLINE: os vetores sao injetados. O que se prova aqui e' a DECISAO, nao
o modelo de visao.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from engine import duplicata  # noqa: E402

falhas = []


def checar(cond, oque):
    print(("  ok   " if cond else "  FALHA ") + oque)
    if not cond:
        falhas.append(oque)


def _com_vetores(mapa):
    """Substitui a ida a' rede por vetores conhecidos."""
    velho = duplicata.vetor_da_imagem
    duplicata.vetor_da_imagem = lambda url, cache: mapa.get(url)
    return velho


print("1. MESMA FOTO = MESMO PRODUTO, SEM PRECISAR DE MODELO")
_v = _com_vetores({})
try:
    r = duplicata.sem_repetidos([
        {"nome": "Ralador caro", "preco": "R$ 105,49", "imagem": "foto_a.jpg"},
        {"nome": "Ralador barato", "preco": "R$ 101,67", "imagem": "foto_a.jpg"},
    ])
    checar(len(r) == 1, "dois anuncios com a MESMA foto viram um cartao")
    # ⚠️ Nao e' detalhe: mostrar o mais caro de dois anuncios identicos e'
    # cobrar a mais de quem confiou no catalogo.
    checar(r and r[0]["nome"] == "Ralador barato", "e fica o MAIS BARATO")
finally:
    duplicata.vetor_da_imagem = _v

print("\n2. FOTOS DIFERENTES, PRODUTO IGUAL -> UNE")
_v = _com_vetores({"a.jpg": [1.0, 0.0, 0.0], "b.jpg": [0.99, 0.14, 0.0]})
try:
    r = duplicata.sem_repetidos([
        {"nome": "Espelho caro", "preco": "R$ 53,71", "imagem": "a.jpg"},
        {"nome": "Espelho barato", "preco": "R$ 47,99", "imagem": "b.jpg"},
    ])
    checar(len(r) == 1 and r[0]["nome"] == "Espelho barato",
           "fotos parecidas acima do limiar viram um cartao, o mais barato")
finally:
    duplicata.vetor_da_imagem = _v

print("\n3. O CASO NEGATIVO — PRODUTO DIFERENTE NAO PODE SUMIR")
# ⛔ Este e' o teste que importa. Uma funcao que devolve sempre 1 item
# passaria nos dois blocos acima. E o custo do erro aqui e' assimetrico:
# fundir demais TIRA UM ACHADO do catalogo e o comprador nunca sabe que ele
# existiu. Medido em 15/09: "pinceis x esponjas" tem nomes parecidissimos
# (jaccard 0,50) e sao produtos distintos.
_v = _com_vetores({"p.jpg": [1.0, 0.0, 0.0], "e.jpg": [0.30, 0.95, 0.0]})
try:
    r = duplicata.sem_repetidos([
        {"nome": "Conjunto de pinceis", "preco": "R$ 12,80", "imagem": "p.jpg"},
        {"nome": "Conjunto de esponjas", "preco": "R$ 13,52", "imagem": "e.jpg"},
    ])
    checar(len(r) == 2, "pinceis e esponjas continuam sendo DOIS achados")
finally:
    duplicata.vetor_da_imagem = _v

print("\n4. SEM VETOR, NAO REMOVE (falha ABERTA)")
# ⚠️ Rede ruim nao pode esvaziar o catalogo: cartao repetido e' feio,
# catalogo vazio e' quebrado.
_v = _com_vetores({})
try:
    r = duplicata.sem_repetidos([
        {"nome": "A", "preco": "R$ 10,00", "imagem": "x.jpg"},
        {"nome": "B", "preco": "R$ 20,00", "imagem": "y.jpg"},
    ])
    checar(len(r) == 2, "sem vetor os dois ficam, em vez de sumirem")
finally:
    duplicata.vetor_da_imagem = _v

print("\n5. A ORDEM DO CATALOGO NAO MUDA")
# ⚠️ A dedupe ordena por preco POR DENTRO para escolher o mais barato, mas
# devolver nessa ordem mudaria a vitrine sem ninguem ter pedido.
_v = _com_vetores({})
try:
    entrada = [{"nome": "caro", "preco": "R$ 90,00", "imagem": "1.jpg"},
               {"nome": "barato", "preco": "R$ 10,00", "imagem": "2.jpg"},
               {"nome": "medio", "preco": "R$ 50,00", "imagem": "3.jpg"}]
    r = duplicata.sem_repetidos(entrada)
    checar([x["nome"] for x in r] == ["caro", "barato", "medio"],
           "a ordem de entrada e' preservada")
finally:
    duplicata.vetor_da_imagem = _v

print("\n6. O LIMIAR E' MAIS APERTADO QUE O DA GUARDA DE FIDELIDADE")
from engine import fidelidade  # noqa: E402
checar(duplicata.LIMIAR > fidelidade.LIMIAR,
       f"dedupe {duplicata.LIMIAR} > fidelidade {fidelidade.LIMIAR}")
_fonte = Path("engine/duplicata.py").read_text(encoding="utf-8")
checar("assimetrico" in _fonte or "assimetric" in _fonte,
       "e o modulo explica POR QUE o custo do erro e' assimetrico")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
