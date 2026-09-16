# -*- coding: utf-8 -*-
"""A terceira perna: ModelScope, so' pra TEXTO.

    python -m engine.modelscope --fumaca      prova que a perna esta' de pe'

Existe porque modelo gratis nao e' contrato. Em 13/09/2026 o
`llama-3.3-70b:free` saiu do plano do OpenRouter no meio de uma sessao; em
14/09 as 14 chaves do OpenRouter estavam esgotadas as 11h; em 04/08 as 15
chaves do Gemini secaram num dia so'. Duas pernas que caem no mesmo dia deixam
o motor sem nenhuma.

⛔ TEXTO, E SO' TEXTO. Para imagem esta porta ja' reprovou, medido em
15/09/2026: `Qwen/Qwen-Image-Edit` levou ~9 min na fila, ignorou o fundo
pedido, caiu pra 760x1280 e trocou a cor dos pinceis.

## ⚠️ AS QUATRO ARMADILHAS DESTA API, TODAS MEDIDAS EM 16/09/2026

**1. `stream` NAO e' opcional.** Sem ele a resposta volta **200** com
`choices: null` e `usage` todo zerado. Um 200 oco, que `r.raise_for_status()`
aprova e que so' estoura la' na frente, num `TypeError` que nao diz nada sobre
a causa. E' a mesma familia do `/icone.png` que respondia 200 servindo HTML.

**2. A resposta vem com o encoding errado.** Sem `r.encoding = "utf-8"` antes
de iterar, `iter_lines(decode_unicode=True)` adivinha latin-1 e "criança" chega
como "criancÌ§a". Nada levanta: o nome so' vai pro ar torto.

**3. O host e' o `.ai`, NUNCA o `.cn`.** Sao dois, e o token e' de um so'. O
`.cn` recusa a mesma chave dizendo apenas "authentication failed", que esconde
a causa; o `.ai` diz o que fazer.

**4. Token sozinho da' 401.** Falta vincular a conta Alibaba Cloud em
`modelscope.ai/my/settings/account`. A sequencia de erros e' a historia:
`401 authentication failed -> 401 bind your account -> 400 no provider -> 200`.

## ⭐ E O CUSTO E' DE FILA, NAO DE ITEM

Medido com o lote real de 12 titulos: **33,6 s de fila e 1,7 s de geracao**.
Um titulo sozinho custou os mesmos ~35 s. Entao mandar lote grande e' de graca
aqui, e mandar um por vez e' o desperdicio.

⚠️ Isso tambem diz onde ela NAO serve: em qualquer lugar que precise de
resposta rapida. Como ULTIMA reserva, 35 s e' barato; como primeira via,
seria o motor inteiro esperando.
"""
from __future__ import annotations

import json

# ⛔ O `.ai`. Ver armadilha 3 no cabecalho.
URL = "https://api-inference.modelscope.ai/v1/chat/completions"
CATALOGO = "https://api-inference.modelscope.ai/v1/models"

# ⚠️ ESCOLHIDO POR MEDICAO, nao por nome. Em 16/09/2026, contra o lote real de
# 12 titulos do catalogo:
#
#   Qwen/Qwen3.5-35B-A3B    200   35,3 s   12 de 12 linhas lidas
#   stepfun-ai/Step-3.5-Flash 200 145,9 s   (um titulo so')
#   zai-org/GLM-4.7-Flash   429   "acesso excessivo, tente mais tarde"
#   Qwen/Qwen3.5-27B        timeout aos 90 s
#
# ⭐ O MoE de 35B com 3B ativos e' o que cabe: densidade suficiente pro
# portugues e barato o bastante pra sair da fila.
MODELO = "Qwen/Qwen3.5-35B-A3B"

# ⚠️ GENEROSO DE PROPOSITO. A fila e' de ~35 s e ja' foi vista em 145 s; um
# tempo apertado aqui transformaria a reserva em reserva que nunca responde.
TEMPO_S = 180
TENTATIVAS_MAX = 3


def _rotador():
    """O anel de chaves, ou None se nao ha' nenhuma.

    ⚠️ `keys.Rotador` LEVANTA quando nao acha chave, e isto aqui e' a ULTIMA
    reserva de uma cascata: ela nao pode derrubar o motor por nao existir.
    Quem nao tem chave do ModelScope tem de continuar com as duas pernas de
    cima, nao ficar sem nenhuma.
    """
    from . import keys
    try:
        return keys.Rotador("MODELSCOPE_API_KEY")
    except RuntimeError:
        return None


def perguntar(texto: str, temperatura: float = 0.0,
              tentativa: int = 1, rot=None) -> str | None:
    """Manda a pergunta e devolve o texto. None se nao deu.

    ⚠️ FALHA ABERTA PRA QUEM CHAMA, como toda perna de cascata: devolver None
    e' dizer "nao sei", e quem chama decide o que fazer. O que esta funcao
    nunca faz e' devolver texto que ela nao recebeu.
    """
    import requests

    rot = rot or _rotador()
    if rot is None or not len(rot):
        return None
    chave = rot.proxima()
    pedaços: list[str] = []
    try:
        with requests.post(
            URL,
            headers={"Authorization": "Bearer " + chave.strip(),
                     "Content-Type": "application/json"},
            # ⛔ `stream: True` OBRIGATORIO. Ver armadilha 1 no cabecalho.
            json={"model": MODELO, "temperature": temperatura, "stream": True,
                  "messages": [{"role": "user", "content": texto}]},
            timeout=TEMPO_S, stream=True,
        ) as r:
            if r.status_code in (401, 429):
                # ⚠️ O 429 daqui e' do MODELO, nao da chave ("该模型当前访问量
                # 过大" — modelo com acesso excessivo). Queimar a chave mesmo
                # assim e' de proposito: o rodizio vira espera barata, e a
                # chave volta quando o anel der a volta.
                print(f"  [!] modelscope {r.status_code}: "
                      f"{r.text[:110]}")
                rot.queimar(chave)
                if tentativa >= min(TENTATIVAS_MAX, len(rot)):
                    return None
                return perguntar(texto, temperatura, tentativa + 1, rot)
            r.raise_for_status()
            # ⛔ ANTES DE ITERAR. Ver armadilha 2 no cabecalho.
            r.encoding = "utf-8"
            for linha in r.iter_lines(decode_unicode=True):
                if not linha or not linha.startswith("data: "):
                    continue
                corpo = linha[6:].strip()
                if corpo == "[DONE]":
                    break
                try:
                    d = json.loads(corpo)
                except ValueError:
                    continue
                escolhas = d.get("choices") or [{}]
                pedaço = (escolhas[0].get("delta") or {}).get("content") or ""
                if pedaço:
                    pedaços.append(pedaço)
    except Exception as e:
        # ⚠️ O NOME DA EXCECAO NAO BASTA, e o corpo tambem vai junto: mesma
        # licao de 14/09/2026 no `combina.py`. "HTTPError" pode ser cota,
        # sobrecarga ou prompt recusado, e a decisao depende de qual.
        corpo = getattr(getattr(e, "response", None), "text", "")
        print(f"  [!] modelscope falhou ({type(e).__name__}) {corpo[:110]}")
        return None

    # ⛔ RESPOSTA VAZIA E' None, NAO "". Devolver a string vazia faria o
    # `resposta or proxima_perna()` de quem chama funcionar por acidente, e o
    # `if resposta is None` falhar em silencio. As duas leituras tem de
    # concordar.
    texto_final = "".join(pedaços).strip()
    return texto_final or None


def fumaca() -> int:
    """Prova que a perna esta' de pe', e imprime o que mediu."""
    import time
    rot = _rotador()
    if rot is None:
        print("sem MODELSCOPE_API_KEY no .env — a perna nao existe aqui")
        return 1
    print(f"{len(rot)} chave(s) no anel, modelo {MODELO}")
    t0 = time.time()
    r = perguntar("Responda com uma linha so', em portugues do Brasil: "
                  "quanto e' 7 vezes 6? Formato: 7x6=<numero>")
    gasto = time.time() - t0
    print(f"  resposta em {gasto:.1f}s: {r!r}")
    if r is None:
        print("REPROVOU: sem resposta")
        return 1
    # ⛔ O CASO NEGATIVO MORA AQUI. Uma fumaca que so' conferisse "veio texto"
    # passaria com a API devolvendo qualquer coisa — inclusive o 200 oco, que
    # foi exatamente o defeito que esta perna quase herdou. Pedir uma conta
    # cuja resposta eu conheco separa "a porta abriu" de "a porta abriu e do
    # outro lado tem um modelo".
    if "42" not in r:
        print("REPROVOU: respondeu, mas nao a pergunta — isto nao e' sucesso")
        return 1
    print("verde")
    return 0


if __name__ == "__main__":
    import argparse
    import sys
    a = argparse.ArgumentParser(description="a terceira perna (texto)")
    a.add_argument("--fumaca", action="store_true")
    o = a.parse_args()
    sys.exit(fumaca() if o.fumaca else 0)
