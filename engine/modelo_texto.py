# -*- coding: utf-8 -*-
"""Uma pergunta de texto ao modelo, com o rodizio de chaves da casa.

⭐ Gemini primeiro, OpenRouter de reserva — as MESMAS chaves e as mesmas
regras do `nome_produto` (429 queima a chave, nao a rodada). Existe pra
`mercadolivre.expandir` e `buscas_site` nao carregarem duas copias do rodizio.

⚠️ 403 "project has been denied access" e' chave MORTA, nao seca (medido em
16/09/2026: 1 das 4 primeiras). Queima igual ao 429 — senao toda rodada
tropeca nela de novo.

⚠️ Devolve None quando nenhum dos dois respondeu. Quem chama decide o que
fazer sem modelo — e "sem modelo" nunca pode virar "sem produto".
"""
from __future__ import annotations

import requests

from . import keys, nome_produto as _np


def perguntar(pergunta: str, tentativas: int = 3) -> str | None:
    rot = keys.gemini()
    for _ in range(min(tentativas, len(rot))):
        chave = rot.proxima()
        try:
            r = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{_np.MODELO_GEMINI}:generateContent?key={chave.strip()}",
                json={"contents": [{"parts": [{"text": pergunta}]}],
                      "generationConfig": {"temperature": 0}},
                timeout=_np.TEMPO_S)
            if r.status_code in (403, 429):
                rot.queimar(chave)
                continue
            r.raise_for_status()
            texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            if texto and texto.strip():
                return texto
        except Exception as e:                       # noqa: BLE001
            print(f"  [!] gemini falhou ({type(e).__name__}) — proxima chave")
            continue
    # ⛔ SEM CHAVE DE RESERVA = None, nao excecao (26/09/2026). `keys.openrouter`
    # LEVANTA quando nao ha' chave; com o Gemini sem cota (5 previas em
    # paralelo), o A/B do titulo derrubava o CLIPE INTEIRO depois de 8 min de
    # dublagem ("NENHUM clipe sobreviveu"). O contrato acima e' devolver None.
    try:
        rot = keys.openrouter()
    except Exception as e:                           # noqa: BLE001
        print(f"  [!] sem modelo de reserva ({str(e)[:40]}) — segue sem resposta")
        return None
    for _ in range(min(tentativas, len(rot))):
        chave = rot.proxima()
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                              headers={"Authorization": "Bearer " + chave,
                                       "Content-Type": "application/json"},
                              json={"model": _np.MODELO, "temperature": 0,
                                    "messages": [{"role": "user", "content": pergunta}]},
                              timeout=_np.TEMPO_S)
            if r.status_code in (402, 429):
                rot.queimar(chave)
                continue
            r.raise_for_status()
            texto = r.json()["choices"][0]["message"]["content"]
            if texto and texto.strip():
                return texto
        except Exception as e:                       # noqa: BLE001
            print(f"  [!] openrouter falhou ({type(e).__name__}) — proxima chave")
            continue
    return None
