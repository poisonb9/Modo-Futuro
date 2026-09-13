# -*- coding: utf-8 -*-
"""Mercado Livre: radar de pauta, mais vendidos e link de afiliado.

## O QUE ELE E', E O QUE ELE NAO E'

⭐ O ML **nao e' fonte de achadinho** — os mais vendidos dele sao papel
higienico, sabao em po e lencol: a cesta de compras do pais. O que ele da' de
unico e' (1) o que o Brasil esta' procurando HOJE e (2) comissao de ate' 16%
com entrega em dois dias, contra 7% e tres semanas do AliExpress.

## ⚠️ O `/sites/MLB/search` ESTA' FECHADO (403) — e nao adianta insistir

Medido em 13/09/2026 com token valido. O que responde e' outra coisa, e por
sorte e' melhor pro nosso caso:

    /trends/MLB                       o que se procura agora
    /highlights/MLB/category/{id}     os mais vendidos da categoria
    /products/{id}                    ficha do produto
    /products/search                  catalogo

## O LINK DE AFILIADO — MEDIDO, NAO SUPOSTO

⭐ Basta pendurar `matt_word` e `matt_tool` na URL do produto. Nao e' preciso
o gerador deles nem o parametro `ref`.

⚠️ E ISTO FOI PROVADO, nao deduzido: em 13/09/2026 o Bryan abriu um link
montado assim e o proprio Mercado Livre mostrou a barra de afiliado com
"GANHOS 16%". Barra de afiliado so' aparece quando o contexto e' reconhecido.
Era o modo de falha mais caro possivel — link que abre a pagina e nao atribui
nada — e por isso nao entrou no motor antes de ter prova.

## ⚠️ O COOKIE E' DE 24 HORAS

Curto pro funil `video -> perfil -> bio -> loja`: a venda de sabado sobre um
clipe de quinta NAO e' nossa. Isso nao se conserta no codigo; se conserta na
chamada do clipe, que precisa gerar clique no mesmo dia.
"""
from __future__ import annotations

import os
import time
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://api.mercadolibre.com"
TIMEOUT_S = 25

# Categoria do ML -> canal nosso. So' as que rendem conteudo.
#
# ⚠️ NEM TODA CATEGORIA VIRA CANAL. "Alimentos e Bebidas" vende muito e nao
# rende clipe nenhum: ninguem assiste a um video sobre sabao em po. A escolha
# aqui e' editorial, e por isso e' curta.
CATEGORIAS = {
    "truque.importado":        [("MLB1246", "Beleza e Cuidado Pessoal")],
    "cozinha.importada":       [("MLB1574", "Casa, Móveis e Decoração")],
    "achadinhos.instantaneos": [("MLB1574", "Casa, Móveis e Decoração"),
                                ("MLB1051", "Celulares e Telefones")],
    "fatura.chora":            [("MLB1000", "Eletrônicos e Áudio"),
                                ("MLB1648", "Informática")],
    "atefalhar":               [("MLB1276", "Esportes e Fitness")],
}

_cache: dict[str, tuple[str, float]] = {}


def token() -> str:
    """Token de aplicacao (client_credentials), com cache.

    ⚠️ VALE 6 HORAS e o cache existe pra nao pedir um por chamada: o ML conta
    pedido de token no rate limit, e queimar cota pedindo credencial seria
    perder chamada que deveria ser de produto.
    """
    agora = time.time()
    if "t" in _cache and _cache["t"][1] > agora + 60:
        return _cache["t"][0]
    cid = os.getenv("MELI_CLIENT_ID")
    sec = os.getenv("MELI_CLIENT_SECRET")
    if not (cid and sec):
        raise RuntimeError("faltam MELI_CLIENT_ID / MELI_CLIENT_SECRET no .env")
    r = requests.post(f"{API}/oauth/token", timeout=TIMEOUT_S,
                      data={"grant_type": "client_credentials",
                            "client_id": cid, "client_secret": sec})
    r.raise_for_status()
    d = r.json()
    _cache["t"] = (d["access_token"], agora + int(d.get("expires_in", 21600)))
    return _cache["t"][0]


def _get(caminho: str, **params) -> dict | list:
    r = requests.get(API + caminho, params=params, timeout=TIMEOUT_S,
                     headers={"Authorization": "Bearer " + token()})
    r.raise_for_status()
    return r.json()


def com_afiliado(url: str) -> str:
    """Pendura a nossa tag na URL do produto.

    ⚠️ PRESERVA os parametros que ja' existem e NAO duplica a tag se ela ja'
    estiver la'. URL de produto do ML costuma vir com `?pdp_filters=...`, e
    jogar fora a query original leva junto a variacao escolhida do produto.

    ⚠️ E SEM TAG, DEVOLVE VAZIO — nao a URL crua. Falha FECHADA: link sem tag
    abre a pagina normalmente e nao paga nada, e um post assim parece certo
    pra sempre. Melhor nao postar do que postar sem atribuir.
    """
    word = os.getenv("MELI_MATT_WORD")
    tool = os.getenv("MELI_MATT_TOOL")
    if not (word and tool and url):
        return ""
    p = urlparse(url)
    q = parse_qs(p.query, keep_blank_values=True)
    q["matt_word"] = [word]
    q["matt_tool"] = [tool]
    return urlunparse(p._replace(query=urlencode(q, doseq=True)))


def tendencias(quantos: int = 20) -> list[str]:
    """O que o Brasil esta' procurando agora. Pauta, nao produto."""
    return [x.get("keyword", "") for x in _get("/trends/MLB")[:quantos]]


def mais_vendidos(categoria: str, quantos: int = 12) -> list[dict]:
    """Os mais vendidos da categoria, ja' com preco e link de afiliado.

    ⚠️ O `/highlights` devolve so' o ID e o tipo — ITEM ou PRODUCT, e os dois
    se leem em endpoints DIFERENTES. Tratar tudo como item devolve 404 calado
    e a lista chega vazia sem ninguem entender por que.
    """
    d = _get(f"/highlights/MLB/category/{categoria}")
    saida = []
    for it in (d.get("content") or [])[:quantos]:
        iid, tipo = it.get("id"), it.get("type")
        try:
            if tipo == "PRODUCT":
                p = _get(f"/products/{iid}")
                nome = p.get("name")
                foto = (p.get("pictures") or [{}])[0].get("url", "")
                # ⚠️ O PRECO NAO ESTA' NO PRODUTO, e o `buy_box_winner` vem
                # `null` — medido em 13/09/2026. Produto de catalogo e' a
                # FICHA (um Cicaplast); quem tem preco e' o ANUNCIO de cada
                # vendedor, em /products/{id}/items. Ler o preco do produto
                # devolve None calado, e a lista chega vazia sem explicacao.
                itens = (_get(f"/products/{iid}/items")
                         .get("results") or [])
                if not itens:
                    continue
                # o primeiro e' o vencedor da buy box na ordem que o ML manda
                preco = itens[0].get("price")
                # ⚠️ E O PERMALINK DO PRODUTO VEM VAZIO. O link que funciona
                # e' o /p/{id} — foi com ele que o Bryan viu a barra de
                # afiliado com GANHOS 16%.
                url = f"https://www.mercadolivre.com.br/p/{iid}"
            else:
                p = _get(f"/items/{iid}")
                nome, preco = p.get("title"), p.get("price")
                url = p.get("permalink", "")
                foto = p.get("thumbnail", "")
        except requests.HTTPError:
            continue
        link = com_afiliado(url)
        if not (nome and preco and link):
            continue
        saida.append({
            "nome": nome, "link": link, "imagem": foto,
            "preco": f"R$ {float(preco):.2f}".replace(".", ","),
            "loja": "Mercado Livre", "_id": iid, "_tipo": tipo,
        })
    return saida
