# -*- coding: utf-8 -*-
"""A/B da ABERTURA da narracao (28/09/2026, dono: "vamos fazer o teste A/B").

Grupo A = abertura de hoje. Grupo B = a regra `## Abertura (A/B)` e
`## Estrutura (A/B)` do guia de voz do canal (cozinha: prato pronto + o
detalhe especial na 1a frase). O grupo e' sorteado de forma ESTAVEL pelo
trecho (mesma fonte + mesmo inicio = mesmo grupo, igual ao ab_titulo) e vai
para o post.json (`ab_abertura`) para a medicao pelo export do Studio.

So' vale nos canais de CANAIS. Canal fora: sem grupo, env limpo.
"""
from __future__ import annotations

import hashlib
import os

CANAIS = {"cozinha.importada"}


def grupo(fonte: str, inicio_s) -> str:
    # sal diferente do ab_titulo: os dois sorteios nao podem andar juntos
    h = hashlib.sha1(f"abertura|{fonte}|{round(float(inicio_s or 0), 1)}".encode()).hexdigest()
    return "A" if int(h[:8], 16) % 2 == 0 else "B"


def aplicar(c: dict, fonte: str, canal: str | None) -> str | None:
    """Sorteia, grava em `c` e no env (lido por guia_voz). Devolve o grupo."""
    os.environ.pop("AB_ABERTURA", None)
    from . import canais_registro
    if canais_registro.canonico(canal) not in CANAIS:
        return None
    g = grupo(fonte, c.get("inicio_s"))
    c["ab_abertura"] = g
    os.environ["AB_ABERTURA"] = g
    return g
