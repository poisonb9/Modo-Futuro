# -*- coding: utf-8 -*-
"""Awin: ver o estado das candidaturas sem abrir o painel.

    python -m engine.awin              o placar: aprovado, pendente, recusado
    python -m engine.awin --links      o link de afiliado de cada aprovado

## ⚠️ O QUE ESTE MODULO RESOLVE

Candidatura no Awin nao avisa quando muda. A aprovacao chega por e-mail, e
e-mail se perde — e um anunciante aprovado que ninguem percebeu e' comissao
parada. Aqui o estado se le' em dois segundos.

⚠️ E A MAQUINA ALCANCA O AWIN, ao contrario do AliExpress (ver
`engine/aliexpress.py`): `api.awin.com` responde 401 sem token, que e'
resposta. Entao isto roda aqui mesmo.

## ⚠️ O TOKEN E' DE LEITURA E ESCRITA — TRATE COMO SENHA

Ele vive no `.env`, que nao e' versionado. Nunca no repositorio: este e'
publico.
"""
from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://api.awin.com"
# ⚠️ O `joined` e' o que importa: so' anunciante aprovado gera comissao.
# `pending` e' expectativa, e confundir os dois faz a gente publicar produto
# de loja que ainda nao nos aceitou — link que leva a lugar nenhum.
RELACOES = ("joined", "pending", "rejected", "suspended")


def _credencial() -> tuple[str, str]:
    t = os.getenv("AWIN_TOKEN")
    p = os.getenv("AWIN_PUBLISHER_ID")
    if not (t and p):
        raise RuntimeError(
            "faltam AWIN_TOKEN / AWIN_PUBLISHER_ID no .env "
            "(o token sai em Conta -> Credenciais de API)")
    return t, p


def programas(relacao: str = "joined") -> list[dict]:
    tok, pid = _credencial()
    r = requests.get(f"{API}/publishers/{pid}/programmes",
                     params={"relationship": relacao},
                     headers={"Authorization": "Bearer " + tok}, timeout=30)
    r.raise_for_status()
    return r.json()


def link(destino: str, id_anunciante: int) -> str:
    """O link de afiliado pra uma pagina da loja.

    ⚠️ `awclick.php` com `mid` (o anunciante) e `id` (nos) e' o formato que o
    Awin rastreia. Link sem o `id` funciona e NAO paga — e' o jeito mais
    silencioso de perder comissao, porque a pagina abre normalmente.
    """
    _, pid = _credencial()
    from urllib.parse import quote
    return (f"https://www.awin1.com/cread.php?awinmid={id_anunciante}"
            f"&awinaffid={pid}&ued={quote(destino, safe='')}")


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="estado das candidaturas no Awin")
    a.add_argument("--links", action="store_true",
                   help="mostra o link de afiliado dos aprovados")
    o = a.parse_args()

    for rel in RELACOES:
        try:
            d = programas(rel)
        except requests.HTTPError as e:
            print(f"{rel:10} — {e}")
            continue
        print(f"\n{rel.upper()}: {len(d)}")
        for x in sorted(d, key=lambda y: y.get("name") or ""):
            print(f"   {x.get('name')}  ({x.get('primarySector') or 'sem setor'})")
            if o.links and rel == "joined":
                print("      ", link(x.get("displayUrl", ""), x["id"]))


if __name__ == "__main__":
    main()
