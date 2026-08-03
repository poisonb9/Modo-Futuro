"""Geração de imagem via Pollinations (image.pollinations.ai) — grátis, sem
chave de API. Testado em 03/08/2026: modelo "flux" dá resultado cinematográfico
consistente (ver teste_imagens_ia/pollinations_1..3.png), embora só "sana"
apareça hoje em /models — "flux" continua respondendo 200, mantido aqui como
padrão, mas trocável caso pare de funcionar sem aviso (serviço sem contrato).
"""
import time
import urllib.parse
from pathlib import Path

import requests

URL_BASE = "https://image.pollinations.ai/prompt"
MODELO_PADRAO = "flux"


def gerar(prompt: str, destino: Path, *, largura: int = 1080, altura: int = 1920,
          modelo: str = MODELO_PADRAO, seed: int | None = None,
          tentativas: int = 4) -> Path:
    """Gera 1 imagem a partir do prompt e salva em `destino`. Levanta
    RuntimeError se todas as tentativas falharem."""
    params = {
        "width": largura,
        "height": altura,
        "model": modelo,
        "nologo": "true",
    }
    if seed is not None:
        params["seed"] = seed

    url = f"{URL_BASE}/{urllib.parse.quote(prompt)}?{urllib.parse.urlencode(params)}"

    ultimo_erro = None
    for tentativa in range(tentativas):
        try:
            r = requests.get(url, timeout=90)
            r.raise_for_status()
            if not r.headers.get("content-type", "").startswith("image/"):
                raise RuntimeError(f"resposta não é imagem: {r.headers.get('content-type')}")
            destino.write_bytes(r.content)
            return destino
        except Exception as e:
            ultimo_erro = e
            time.sleep(2 * (tentativa + 1))

    raise RuntimeError(f"geração de imagem falhou após {tentativas} tentativas: {ultimo_erro}")
