# -*- coding: utf-8 -*-
"""Balao EXCLUSIVO do e-mail de aviso de preco: um SINO dourado metalizado.

    python -X utf8 ferramentas/baloes/gerar_balao_sino.py [quantas=3]

Sai em Desktop/inauguracao/email_sino_<n>.png (fundo branco). Depois:
    python -X utf8 ferramentas/baloes/recorte_branco.py <arquivo>
para tirar o fundo (preserva a fita branca).

⭐ POR QUE UM SINO (25/09/2026): o botao do aviso no site e no canal e' 🔔.
O e-mail que chega dizendo "baixou" fecha o circulo com o MESMO simbolo —
e nenhum outro lugar usa este balao: ele so' existe no e-mail.

⚠️ MESMA LINGUAGEM dos inaug_*.png (foil dourado com detalhe vermelho,
fita branca em espiral, fundo branco chapado), senao o balao destoa da marca.

Cloudflare Workers AI, flux-2-dev (o melhor medido em 08/08). ⚠️ EXIGE
multipart/form-data — JSON devolve 400. ~110-170 s por imagem e queima cota
rapido: por isso poucas por rodada, girando as contas CF_API_TOKEN(_N).
"""
from __future__ import annotations

import base64
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")

MODELO = "@cf/black-forest-labs/flux-2-dev"
SAIDA = Path.home() / "Desktop" / "inauguracao"

PROMPT = (
    "a single inflatable metallic gold foil party balloon shaped like a classic "
    "notification bell, glossy mylar texture with realistic crinkled seams and "
    "puffy inflated edges, a small shiny red foil clapper ball at the bottom of "
    "the bell and a small red foil bow on top, bright specular highlights, the "
    "balloon floats upright with a thin curly white satin ribbon hanging from "
    "the knot below, product photo, centered, full balloon visible, plain pure "
    "white background, soft studio lighting, no text, no letters, no numbers, "
    "no logo, no other objects"
)


def contas() -> list[tuple[str, str]]:
    pares = []
    if os.getenv("CF_API_TOKEN") and os.getenv("CF_ACCOUNT_ID"):
        pares.append((os.getenv("CF_API_TOKEN"), os.getenv("CF_ACCOUNT_ID")))
    i = 2
    while os.getenv(f"CF_API_TOKEN_{i}") and os.getenv(f"CF_ACCOUNT_ID_{i}"):
        pares.append((os.getenv(f"CF_API_TOKEN_{i}"), os.getenv(f"CF_ACCOUNT_ID_{i}")))
        i += 1
    return pares


def gerar(destino: Path, semente: int) -> bool:
    for token, conta in contas():
        url = f"https://api.cloudflare.com/client/v4/accounts/{conta}/ai/run/{MODELO}"
        campos = {"prompt": (None, PROMPT), "width": (None, "1024"),
                  "height": (None, "1024"), "seed": (None, str(semente))}
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {token}"},
                              files=campos, timeout=300)
        except requests.RequestException as e:
            print(f"  rede: {e}")
            continue
        if r.status_code == 429:
            print(f"  conta ...{conta[-4:]} sem cota, proxima")
            continue
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}: {r.text[:160]}")
            continue
        img = (r.json().get("result") or {}).get("image")
        if not img:
            print(f"  resposta sem imagem: {r.text[:160]}")
            continue
        destino.write_bytes(base64.b64decode(img))
        print(f"  ok -> {destino}")
        return True
    return False


def main() -> None:
    quantas = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    if not contas():
        raise SystemExit("nenhuma CF_API_TOKEN/CF_ACCOUNT_ID no .env")
    SAIDA.mkdir(parents=True, exist_ok=True)
    for n in range(1, quantas + 1):
        print(f"sino {n}/{quantas}...")
        t = time.time()
        if not gerar(SAIDA / f"email_sino_{n}.png", semente=1000 + n):
            raise SystemExit("todas as contas falharam ou sem cota — tentar amanha")
        print(f"  {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
