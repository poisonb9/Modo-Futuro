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

# ⭐ ATALHO 2 (18/09/2026): MESMO NOME CURTO + FOTO NA MESMA FAMILIA.
#
# O Bryan viu no site duas "Balanca digital de cafe com timer e USB" (R$ 52,49
# e 51,99) e dois "Organizador de maquiagem giratorio 360" (preto e branco).
# A dedupe por foto NAO pega: sao fotos diferentes do mesmo produto. MEDIDO
# nos 139 do catalogo em 18/09:
#
#     mesmo nome curto, mesma loja:   balanca 0,742 . teclado 0,766 . giratorio 0,791
#     nomes diferentes, os mais parecidos: luva x luva 0,874 . tapete 3D x
#         tapete veludo 0,856 (PRODUTOS DIFERENTES) . carregadores 0,856
#
# ⛔ Nao existe limiar de FOTO que una os tres sem fundir o tapete: o par
# diferente pontua MAIS que os pares iguais. E' o mesmo achado do nome cru
# (Jaccard), so' que do outro lado.
#
# O que separa e' o NOME CURTO: ele nao e' o titulo do lojista, e' o nome que
# o publicador escreve por produto (`estado/nomes_curtos.json`), e dois
# anuncios com o MESMO nome curto na MESMA loja sao o mesmo produto. A foto
# entra so' como trava: acima do teto medido de "produto diferente" na guarda
# de fidelidade (0,5861), pra um nome curto repetido por engano nao fundir
# duas coisas que nao se parecem em nada.
#
# ⚠️ Caso negativo (teste 7): mesmo nome, foto abaixo da trava -> ficam os dois.
NOME_IGUAL_FOTO_MIN = 0.60


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
        # atalho 2: mesmo nome curto e foto da mesma familia (ver NOME_IGUAL_FOTO_MIN)
        nome = (p.get("nome") or "").strip().lower()
        if nome and v is not None and any(
                (q.get("nome") or "").strip().lower() == nome
                and w is not None and _parecidos(v, w) >= NOME_IGUAL_FOTO_MIN
                for q, w in zip(fim, vetores)):
            continue
        fim.append(p)
        vetores.append(v)
    _gravar(cache)
    # ⚠️ Devolve na ORDEM ORIGINAL. Ordenar por preco aqui mudaria a vitrine
    # sem ninguem ter pedido — a ordem do catalogo e' decisao de quem monta a
    # pagina, nao efeito colateral da dedupe.
    ficaram = {id(p) for p in fim}
    return [p for p in produtos if id(p) in ficaram]


def pares_entre_lojas(produtos: list[dict]) -> int:
    """Escreve `tambem_em` em cada cartao: o MESMO produto (pela foto, mesmo
    limiar da dedupe) em OUTRA loja, com preco, link e diferenca.

    ⭐ SELO 1 (Bryan, 17/09/2026): "R$ 12 mais barato que no Mercado Livre".
    A dedupe e' POR loja de proposito (o cliente escolhe prazo x preco);
    aqui e' o passo seguinte: os dois cartoes ficam, e cada um aponta pro
    irmao. E' a pergunta que a pessoa responde abrindo tres abas — a gente
    entrega pronta.

    ⚠️ Usa os vetores ja' em cache (a dedupe acabou de calcular): nao chama
    modelo por par. Foto identica (mesma URL) e' par sem modelo.
    Devolve quantos cartoes ganharam `tambem_em`.
    """
    cache = _cache()
    itens = []
    for p in produtos:
        p["tambem_em"] = []
        img = p.get("imagem", "")
        itens.append((p, img, vetor_da_imagem(img, cache) if img else None))
    _gravar(cache)
    n = 0
    for i, (a, ia, va) in enumerate(itens):
        for b, ib, vb in itens[i + 1:]:
            if (a.get("loja") or "") == (b.get("loja") or ""):
                continue
            mesmo = bool(ia and ia == ib) or (
                va is not None and vb is not None and _parecidos(va, vb) >= LIMIAR)
            if not mesmo:
                continue
            pa, pb = _preco(a), _preco(b)
            if pa == float("inf") or pb == float("inf"):
                continue
            a["tambem_em"].append({"loja": b.get("loja"), "preco": b.get("preco"),
                                   "link": b.get("link"), "dif": round(pb - pa, 2)})
            b["tambem_em"].append({"loja": a.get("loja"), "preco": a.get("preco"),
                                   "link": a.get("link"), "dif": round(pa - pb, 2)})
    for p, _, _ in itens:
        if p["tambem_em"]:
            n += 1
    return n
