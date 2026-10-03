# -*- coding: utf-8 -*-
"""Gera um BALAO metalizado da casa (03/10/2026, dono: "baloes diferentes para as previas").

⚠️ Gemini NAO serve aqui: o plano gratuito tem cota ZERO para modelos de imagem
(medido 03/10: "limit: 0", GenerateRequestsPerDayPerProjectPerModel-FreeTier).
O caminho medido e' o do sino do e-mail (_privado/camada/gerar_balao_sino.py):
Cloudflare Workers AI flux-2-dev, multipart (JSON da' 400), girando CF_API_TOKEN(_N).
Fundo branco -> `recorte_branco.py` (preserva a fita) -> WEBP + versao _p.

    python -X utf8 ferramentas/baloes/gerar_balao.py camarim_photocard "a K-pop photocard ..."
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")
BALOES = RAIZ / "paginas" / "baloes"
MODELO = "@cf/black-forest-labs/flux-2-dev"
ESTILO = ("a single inflatable metallic foil party balloon shaped like {forma}, polished "
          "chrome silver mylar with gold foil details, realistic crinkled seams and puffy "
          "inflated edges, bright specular highlights, a thin curly gold ribbon hanging from "
          "the knot below, product photo, centered, full balloon visible, plain pure white "
          "background, soft studio lighting, no text, no letters, no numbers, no logo, "
          "no other objects")


def contas() -> list[tuple[str, str]]:
    pares = []
    if os.getenv("CF_API_TOKEN") and os.getenv("CF_ACCOUNT_ID"):
        pares.append((os.getenv("CF_API_TOKEN"), os.getenv("CF_ACCOUNT_ID")))
    i = 2
    while os.getenv(f"CF_API_TOKEN_{i}") and os.getenv(f"CF_ACCOUNT_ID_{i}"):
        pares.append((os.getenv(f"CF_API_TOKEN_{i}"), os.getenv(f"CF_ACCOUNT_ID_{i}")))
        i += 1
    return pares


def gerar(nome: str, forma: str, semente: int = 7) -> Path | None:
    prompt = ESTILO.format(forma=forma)
    for token, conta in contas():
        url = f"https://api.cloudflare.com/client/v4/accounts/{conta}/ai/run/{MODELO}"
        campos = {"prompt": (None, prompt), "width": (None, "1024"),
                  "height": (None, "1024"), "seed": (None, str(semente))}
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, files=campos, timeout=300)
        except requests.RequestException as e:
            print(f"  rede: {type(e).__name__}")
            continue
        if r.status_code == 429:
            print(f"  conta ...{conta[-4:]} sem cota, proxima")
            continue
        img = (r.json().get("result") or {}).get("image") if r.status_code == 200 else None
        if not img:
            print(f"  HTTP {r.status_code}: {r.text[:140]}")
            continue
        bruto = Path(tempfile.mkdtemp()) / f"{nome}.png"
        bruto.write_bytes(base64.b64decode(img))
        recorte = RAIZ / "ferramentas" / "baloes" / "recorte_branco.py"
        out = BALOES / f"{nome}.webp"
        subprocess.run([sys.executable, str(recorte), str(bruto), str(out), "600"], check=True)
        subprocess.run([sys.executable, str(recorte), str(bruto), str(BALOES / f"{nome}_p.webp"), "300"], check=True)
        bruto.unlink(missing_ok=True)
        print(f"  ok {nome}")
        return out
    print("  todas as contas falharam ou sem cota")
    return None


if __name__ == "__main__":
    gerar(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 7)
