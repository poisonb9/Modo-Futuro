"""Marca a palavra de maior impacto em cada grupo de legenda, via Gemini.

Padrão visto numa referência (Erica Bruno, TikTok, 02/08/2026): a legenda
fica branca por padrão e só UMA palavra por grupo ganha cor sólida — não é
a palavra sendo falada acendendo tipo karaokê, é uma escolha editorial de
qual palavra "pesa mais" na frase (verbo de ação, pronome direto, urgência).
Pedimos pro Gemini marcar essa palavra, numa chamada só por clipe (não uma
por grupo — o clipe inteiro tem ~20-30 grupos, uma chamada só é suficiente
e mais barato).
"""
import json
import re
import time

import requests

import config
from . import keys

PROMPT = """Você edita legendas de vídeos virais de TikTok em português do Brasil.
Abaixo está uma lista numerada de trechos curtos de legenda (cada um até 3
palavras), na ordem em que aparecem no vídeo. Para CADA trecho, escolha a
palavra de MAIOR IMPACTO editorial pra destacar com cor — o tipo de palavra
que uma editora profissional destacaria pra prender atenção (verbo de ação
forte, pronome direto tipo "você", superlativo, palavra de urgência ou
revelação). Nem todo trecho precisa ter destaque: se nenhuma palavra se
destacar claramente, responda -1 pra esse trecho.

Responda SOMENTE um array JSON de inteiros, um por trecho, na mesma ordem,
com o ÍNDICE (começando em 0) da palavra escolhida dentro do trecho, ou -1.
Sem markdown, sem comentário, sem texto antes ou depois do array.

Trechos:
{trechos}"""


def _extrair_json(saida: str) -> str:
    saida = saida.strip()
    saida = re.sub(r"^```(json)?", "", saida).strip()
    saida = re.sub(r"```$", "", saida).strip()
    return saida


def marcar(grupos: list[list[dict]]) -> list[int | None]:
    """Devolve, por grupo, o índice (0-based) da palavra destacada, ou None."""
    if not grupos:
        return []

    trechos = "\n".join(
        f"{i}: " + " ".join(p["palavra"] for p in g)
        for i, g in enumerate(grupos)
    )

    rot = keys.gemini()
    for _ in range(len(rot) * 2):
        chave = rot.proxima()
        try:
            r = requests.post(
                f"{config.GEMINI_URL}/models/{config.GEMINI_MODELO}:generateContent?key={chave}",
                json={
                    "contents": [{"parts": [{"text": PROMPT.format(trechos=trechos)}]}],
                    "generationConfig": {"temperature": 0.4},
                },
                timeout=60,
            )
            if r.status_code in (429, 403):
                rot.queimar(chave)
                continue
            r.raise_for_status()
            saida = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            arr = json.loads(_extrair_json(saida))
            if not isinstance(arr, list) or len(arr) != len(grupos):
                raise ValueError(f"esperava lista de {len(grupos)}, veio {arr!r}")
            return [
                (int(idx) if 0 <= int(idx) < len(g) else None)
                for idx, g in zip(arr, grupos)
            ]
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (429, 403):
                rot.queimar(chave)
                continue
            print(f"   [!] destaque: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"   [!] destaque: {e}")
            time.sleep(1)

    print("   [!] destaque de palavra falhou em todas as chaves — legenda sem cor")
    return [None] * len(grupos)
