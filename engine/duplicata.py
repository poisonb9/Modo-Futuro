# -*- coding: utf-8 -*-
"""Tira do catalogo o MESMO produto anunciado duas vezes.

## O PROBLEMA, MEDIDO EM 15/09/2026

O catalogo mostrava o mesmo Ralador de queijo duas vezes (R$ 105,49 e
R$ 101,67), com a MESMA foto e os dois marcados "novo". O Bryan viu no
iPhone: *"olha como existem produtos repetidos, isso nao pode acontecer"*.

A dedupe que existia era por `id` do anuncio — e dois lojistas vendendo o
mesmo produto tem ids diferentes. Ela nunca teve como pegar isso.

## ⛔ POR QUE NAO DA' PRA USAR O NOME

Foi a primeira ideia, e a medicao a derrubou. Sobreposicao de palavras
(Jaccard) sobre os 66 produtos do catalogo:

    0,50   "Conjunto de pinceis"  x  "Conjunto de esponjas"   DIFERENTES
    0,45   "Espelho de vaidade"   x  "Espelho de Maquiagem"   O MESMO

⛔ O par que NAO pode ser unido pontua MAIS ALTO que o par que precisa ser
unido. Nao existe limiar de nome que acerte os dois — qualquer corte erra de
um lado. Mesmo padrao do detector invertido de `engine/fidelidade.py`: a
pergunta e' semantica e nao se responde contando palavras.

## ⭐ O QUE FUNCIONA — a mesma medida da guarda de fidelidade

`engine/fidelidade.py` ja' separa "mesmo produto" de "produto diferente" com
folga medida:

    mesmo produto      min 0,9593
    produto diferente  max 0,5861      margem 0,37

E' a mesma pergunta, entao e' a mesma ferramenta. Aqui o limiar e' mais
APERTADO que o da guarda (0,93 contra 0,85) de proposito: reprovar um clipe
por engano custa um clipe; **fundir dois produtos diferentes tira um achado
do catalogo e o comprador nunca sabe que ele existiu**.

## ⚠️ QUANDO HA' DUPLICATA, FICA O MAIS BARATO

Nao e' detalhe de implementacao: e' o que a pagina promete. Mostrar o mais
caro de dois anuncios identicos e' cobrar a mais de quem confiou no catalogo.
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "estado" / "vetores_produto.json"

# ⚠️ MAIS APERTADO que o da guarda (0,85). Ver o cabecalho: o custo do erro
# aqui e' assimetrico — fundir demais some com achado, fundir de menos so'
# mostra um cartao repetido.
LIMIAR = 0.93


def _cache() -> dict:
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def _gravar(d: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(d), encoding="utf-8")


def vetor_da_imagem(url: str, cache: dict) -> list | None:
    """Embedding da foto do anuncio, com cache por URL.

    ⚠️ O cache nao e' luxo: sao 66 produtos e cada vetor custa um download
    mais uma chamada de rede. Sem ele, montar a pagina ficaria lento o
    bastante para alguem "otimizar" desligando a dedupe.
    """
    if not url:
        return None
    if url in cache:
        return cache[url]
    try:
        import io

        import requests
        from PIL import Image

        from engine import fidelidade
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content))
        v = fidelidade._vetor(im).tolist()
    except Exception:
        # ⚠️ FALHA ABERTA: sem vetor, o produto NAO e' removido. Rede ruim
        # nao pode esvaziar o catalogo — cartao repetido e' feio, catalogo
        # vazio e' quebrado.
        return None
    cache[url] = v
    return v


def _parecidos(a: list, b: list) -> float:
    sa = sum(x * x for x in a) ** 0.5
    sb = sum(x * x for x in b) ** 0.5
    if not sa or not sb:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (sa * sb)


def _preco(p: dict) -> float:
    t = str(p.get("preco", "")).replace("R$", "").strip()
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return float("inf")


def sem_repetidos(produtos: list[dict]) -> list[dict]:
    """Um cartao por produto real. Fica o mais barato de cada grupo.

    ⭐ A FOTO IDENTICA e' atalho, nao substituto: quando dois anuncios usam
    exatamente a mesma URL de imagem, sao o mesmo produto sem precisar de
    modelo nenhum. Isso resolve parte dos casos de graca; o resto vai pro
    embedding.
    """
    cache = _cache()
    fim: list[dict] = []
    vetores: list[list | None] = []
    # ⚠️ GRAVA NO MEIO DO CAMINHO, e nao so' no fim. MEDIDO em 15/09/2026:
    # uma rodada de 124 produtos levou mais de 15 minutos, morreu num
    # `timeout` perto do fim e perdeu os 122 vetores que ja' tinha buscado —
    # trabalho de REDE, o mais caro que este modulo faz. Gravar a cada 10 faz
    # a proxima tentativa recomecar de onde parou.
    #
    # ⭐ E nao e' so' contra timeout: vale pra queda de rede, Ctrl+C e runner
    # efemero. O cache e' o unico lugar onde esse trabalho existe.
    novos = 0
    for p in sorted(produtos, key=_preco):     # o mais barato chega primeiro
        img = p.get("imagem", "")
        # atalho 1: mesma foto, mesmo produto
        if any(img and img == q.get("imagem") for q in fim):
            continue
        antes = len(cache)
        v = vetor_da_imagem(img, cache)
        if len(cache) > antes:
            novos += 1
            if novos % 10 == 0:
                _gravar(cache)
        if v is not None and any(
                w is not None and _parecidos(v, w) >= LIMIAR for w in vetores):
            continue
        fim.append(p)
        vetores.append(v)
    _gravar(cache)
    # ⚠️ Devolve na ORDEM ORIGINAL. Ordenar por preco aqui mudaria a vitrine
    # sem ninguem ter pedido — a ordem do catalogo e' decisao de quem monta a
    # pagina, nao efeito colateral da dedupe.
    ficaram = {id(p) for p in fim}
    return [p for p in produtos if id(p) in ficaram]
