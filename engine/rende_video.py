# -*- coding: utf-8 -*-
""""Isso rende video?" — o corte editorial, em primeira versao.

## O QUE ESTE MODULO ADMITE SOBRE SI MESMO

⚠️ **Isto NAO e' julgamento editorial. E' um proxy grosseiro dele.** O corte
de verdade e' do Bryan, olhando a lista. O que esta' aqui tira o obvio pra ele
nao gastar atencao com papel higienico — nada alem disso.

E' importante estar escrito, porque a tentacao de daqui a um mes vai ser
tratar a saida disto como veredito. Nao e'. Quando houver medicao de quais
produtos renderam view, ESSA medicao substitui este arquivo.

## A IDEIA, e ela veio de um contraste medido

⭐ **No AliExpress, vender muito e' sinal de QUALIDADE. No Mercado Livre,
vender muito e' sinal de COMMODITY.**

O pincel Kabuki com 32 mil vendas no AliExpress e' raro: alguem descobriu e a
coisa presta. O papel higienico Neve em 1o lugar no Mercado Livre e' o oposto:
todo mundo ja' compra no automatico, e ninguem assiste a um video sobre isso.

Achadinho e' o que a pessoa NAO sabia que existia. Ser o mais vendido do pais
e' evidencia CONTRA isso.

## O QUE ELE OLHA

1. reposicao — o que acaba e se recompra sem pensar
2. marca de supermercado — quem ja' esta' no carrinho nao precisa de descoberta
3. o produto explica o que faz em uma frase? (nao da' pra medir; nao entra)

⚠️ O item 3 e' o que realmente separa, e e' justamente o que eu nao sei
escrever. Fica registrado como o buraco que ele e'.
"""
from __future__ import annotations

import re

# ⚠️ REPOSICAO, e nao "categoria ruim". Papel higienico nao e' um produto
# pior que uma creatina — ele so' nao precisa ser apresentado a ninguem.
REPOSICAO = (
    "papel higiênico", "papel higienico", "sabão em pó", "sabao em po",
    "amaciante", "detergente", "desinfetante", "água sanitária",
    "agua sanitaria", "sabão líquido", "sabao liquido", "alvejante",
    "tira manchas", "percarbonato", "guardanapo", "papel toalha",
    "fralda", "absorvente", "ração", "racao", "areia para gato",
    "café em pó", "cafe em po", "açúcar", "acucar", "arroz", "feijão",
    "óleo de soja", "oleo de soja", "leite em pó", "leite em po",
)

# ⚠️ E' sobre o produto ser CONHECIDO, nao sobre a marca ser ruim. O Boticario
# faz bom perfume; so' que ninguem precisa de um video pra saber que ele
# existe. A descoberta ja' aconteceu ha' trinta anos.
JA_CONHECIDO = (
    "o boticário", "o boticario", "natura", "avon", "eudora", "omo",
    "ariel", "ypê", "ype", "veja", "pinho sol", "neve", "personal",
    "sadia", "nestlé", "nestle", "coca-cola", "heineken", "skol",
)


def rende(nome: str) -> tuple[bool, str]:
    """(rende video?, por que). O `por que` existe pra calibrar."""
    t = (nome or "").lower()
    if not t.strip():
        return False, "sem nome"
    for termo in REPOSICAO:
        if termo in t:
            return False, f"reposição ({termo}) — não precisa de descoberta"
    for marca in JA_CONHECIDO:
        # ⚠️ `\b` de proposito: "neve" casaria dentro de "neveira" e de
        # qualquer palavra com essas letras. Filtro que casa demais reprova o
        # que deveria passar, e isso e' invisivel — o produto so' some.
        if re.search(rf"\b{re.escape(marca)}\b", t):
            return False, f"marca de supermercado ({marca}) — já está no carrinho"
    return True, "passa"


def peneirar(produtos: list[dict]) -> tuple[list[dict], list[tuple[str, str]]]:
    """Separa o que rende do que nao rende. Devolve (passaram, recusados)."""
    passaram, fora = [], []
    for p in produtos:
        ok, porque = rende(p.get("nome", ""))
        (passaram if ok else fora).append(p if ok else (p.get("nome", ""), porque))
    return passaram, fora
