# -*- coding: utf-8 -*-
"""Selo 1: o MESMO produto em outra loja, lado a lado, com a diferenca. Sem rede.

## POR QUE EXISTE (17/09/2026)

Bryan aprovou "R$ 12 mais barato que no Mercado Livre". A dedupe e' POR loja
(os dois cartoes ficam); este passo faz cada um apontar pro irmao.

⭐ Casos: (1) foto IDENTICA (mesma URL) em duas lojas vira par sem modelo, com
`dif` correto nos dois lados; (2) ⛔ NEGATIVO: mesma foto na MESMA loja NAO e'
par (isso e' a dedupe, nao este selo); fotos diferentes sem vetor NAO viram
par; (3) todo cartao sai com `tambem_em` (lista, vazia quando nao ha').
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import duplicata  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


# sem rede: o vetor nao e' calculado (URL vazia => None), so' a URL identica conta
real = duplicata.vetor_da_imagem
duplicata.vetor_da_imagem = lambda url, cache: None
duplicata._gravar = lambda d: None
try:
    print("1. FOTO IDENTICA EM DUAS LOJAS = PAR, COM A DIFERENCA NOS DOIS LADOS")
    a = {"loja": "AliExpress", "preco": "R$ 37,00", "link": "a", "imagem": "https://x/1.jpg"}
    b = {"loja": "Mercado Livre", "preco": "R$ 49,90", "link": "b", "imagem": "https://x/1.jpg"}
    n = duplicata.pares_entre_lojas([a, b])
    checar(n == 2, f"dois cartoes ganharam irmao ({n})")
    checar(a["tambem_em"] == [{"loja": "Mercado Livre", "preco": "R$ 49,90", "link": "b", "dif": 12.9}],
           f"o Ali aponta pro ML com dif +12,90: {a['tambem_em']}")
    checar(b["tambem_em"][0]["dif"] == -12.9, "o ML aponta pro Ali com dif -12,90")

    print()
    print("2. ⛔ NEGATIVO: mesma loja NAO e' par; foto diferente sem vetor NAO e' par")
    c = {"loja": "AliExpress", "preco": "R$ 30,00", "link": "c", "imagem": "https://x/1.jpg"}
    d = {"loja": "Mercado Livre", "preco": "R$ 30,00", "link": "d", "imagem": "https://x/2.jpg"}
    n = duplicata.pares_entre_lojas([a, c, d])
    checar(n == 0 and a["tambem_em"] == [] and c["tambem_em"] == [] and d["tambem_em"] == [],
           "nenhum par: a-c mesma loja, a-d fotos diferentes")

    print()
    print("3. TODO CARTAO SAI COM `tambem_em`")
    e = {"loja": "Nike", "preco": "R$ 1,00", "link": "e"}
    duplicata.pares_entre_lojas([e])
    checar(e["tambem_em"] == [], "sem imagem: lista vazia, chave presente")
finally:
    duplicata.vetor_da_imagem = real

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
