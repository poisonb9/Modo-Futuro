# -*- coding: utf-8 -*-
"""Entre as fotos de um anuncio, qual e' a que NAO e' banner.

## O PROBLEMA (MAESTROS_DESIGN_DO_SITE.md, defeito 1, 18/09/2026)

A foto principal do AliExpress e' a que o lojista escolhe pra competir na
busca: "22 colors available~", "STRONG MAGNETIC FORCE", caixa com selo.
Num cartao escuro e limpo isso e' o banner que os Maestros mandam tirar da
pagina de produto (Analista de Loja Virtual EP.2). O `precos.py` passou a
guardar as outras fotos do anuncio (`imagens`); este modulo escolhe.

## ⛔ O EMBEDDING DA DEDUPE NAO SERVE, e o motivo e' de desenho

`fidelidade._vetor` RECORTA o produto (alfa) antes de embutir — foi feito
assim pra comparar produto com produto sem o fundo. O texto do banner fica
FORA do recorte, entao o vetor nao ve banner nenhum. MEDIDO em 18/09 nos 8
casos conhecidos: com recorte, a balanca "Simple but not simplistic" saiu
como a foto MAIS limpa do conjunto.

## O QUE MEDE — a imagem INTEIRA contra duas frases

O mesmo modelo (nemotron-embed-vl), sem recorte, e' comparado com uma frase
de foto limpa e uma de banner; a nota e' a diferenca dos cossenos. MEDIDO nos
8 casos (foto principal, vista a olho):

    BANNER  luva 22 colors +0,050 . teclado AJAZZ +0,050 . tesla TEKSY +0,047
            ralador na caixa +0,094 . balanca "Simple" +0,188 (texto discreto)
    LIMPO   balanca foto +0,193 . organizador panelas +0,166 . giratorio +0,120

Separa 4 dos 5 banners de todos os limpos; o que "erra" e' o texto pequeno
de duas linhas sobre um produto grande — que a olho tambem passa. E o uso
aqui e' RANKING dentro do mesmo anuncio, nao classificacao: entre as fotos
do mesmo produto, a de nota mais alta.

⚠️ Falha ABERTA: sem nota (rede, chave) fica a principal. Foto pior e' feia;
cartao sem foto e' quebrado.

## ⛔ NAO ESTA' LIGADO AO CARTAO — reprovou no caso negativo (18/09/2026, 13:20 UTC)

Com as fotos reais (rodada 13:11, 152 produtos com `imagens`), o ranking
dentro do mesmo anuncio foi olhado em 18 produtos, 8 trocas:

    MELHOR  luva (banner 22 cores -> a luva)  . carregador (banner -> na tomada)
            ventosa (STRONG MAGNETIC -> produto no branco)
    PIOR    teclado -> escolheu a PLACA DE POSICIONAMENTO (outro produto)
            oculos -> escolheu a foto com texto "One-handed operation"
            bolsa  -> escolheu a variante PRETA de uma bolsa marrom
    NEUTRO  tesla (banner -> outro banner) . fone ("Smaller" -> "Official")

3 em 8 erradas, e duas delas mostram OUTRA COISA no cartao — pior que o
banner. A nota mede "parece foto de produto limpa" e nao "e' ESTE produto
sem texto". O que falta e' (a) fidelidade ao produto (o vetor RECORTADO da
dedupe, cos >= 0,93 contra a principal) E (b) um medidor de texto de
verdade (OCR: area coberta por letras). Sem os dois, fica a principal.
"""
from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "estado" / "fotos_nota.json"

FRASE_LIMPA = "clean product photo on a plain background, no text, no banner, no labels"
FRASE_BANNER = "advertising banner with large text overlay and promotional labels"

# ⚠️ Troca a principal so' se a extra ganhar por esta margem. Sem ela, duas
# fotos igualmente limpas trocariam de lugar a cada publicacao por ruido.
MARGEM = 0.02
LADO = 448

_frases: dict[str, list[float]] = {}


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


def _embutir(entrada: str, tipo: str) -> list[float]:
    import requests

    from engine import fidelidade
    chave = os.getenv("NVIDIA_API_KEY")
    if not chave:
        raise RuntimeError("falta NVIDIA_API_KEY no .env")
    r = requests.post(fidelidade.URL, headers={"Authorization": f"Bearer {chave}"},
                      timeout=120,
                      json={"model": fidelidade.MODELO, "input": [entrada],
                            "encoding_format": "float", "input_type": tipo,
                            "truncate": "NONE"})
    r.raise_for_status()
    v = r.json()["data"][0]["embedding"]
    n = sum(x * x for x in v) ** 0.5
    return [x / n for x in v]


def _frase(texto: str) -> list[float]:
    if texto not in _frases:
        _frases[texto] = _embutir(texto, "query")
    return _frases[texto]


def nota(url: str, cache: dict | None = None) -> float | None:
    """Quao limpa e' a foto INTEIRA (sem recorte). None = nao deu pra medir."""
    if not url:
        return None
    c = cache if cache is not None else _cache()
    if url in c:
        return c[url]
    try:
        import requests
        from PIL import Image
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        im.thumbnail((LADO, LADO))
        bo = io.BytesIO()
        im.save(bo, "JPEG", quality=85)
        dado = "data:image/jpeg;base64," + base64.b64encode(bo.getvalue()).decode()
        v = _embutir(dado, "passage")
        ql, qb = _frase(FRASE_LIMPA), _frase(FRASE_BANNER)
        n = round(sum(a * b for a, b in zip(v, ql)) - sum(a * b for a, b in zip(v, qb)), 4)
    except Exception:
        return None
    c[url] = n
    if cache is None:
        _gravar(c)
    return n


def escolher(principal: str, extras: list[str], cache: dict | None = None) -> str:
    """A foto do cartao: a principal, a menos que uma extra seja mais limpa
    por MARGEM. Falha aberta pra principal."""
    if not extras:
        return principal
    np_ = nota(principal, cache)
    if np_ is None:
        return principal
    melhor, melhor_nota = principal, np_
    for u in extras:
        n = nota(u, cache)
        if n is not None and n > melhor_nota + MARGEM:
            melhor, melhor_nota = u, n
    return melhor
