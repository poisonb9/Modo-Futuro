# -*- coding: utf-8 -*-
"""Cliente da API de afiliado do AliExpress.

## ⚠️ ESTA MAQUINA NAO ALCANCA OS GATEWAYS

Medido em 12/09/2026:

    api-sg.aliexpress.com   timeout no handshake TLS (15s)
    gw.api.taobao.com       timeout no handshake TLS (15s)
    api.aliexpress.com      302 — o site normal responde

O site do AliExpress responde e os dois gateways de API nao. Isso e' bloqueio
de saida pra esses hosts, e nao credencial errada. Por isso o teste de fumaca
roda na NUVEM (`.github/workflows/aliexpress_fumaca.yml`), e nao aqui.

⚠️ E' a mesma conclusao de sempre nesta operacao, por um motivo novo: o motor
pesado ja' roda na nuvem porque a maquina nao da' conta. Agora o garimpo roda
na nuvem porque a maquina nao ALCANCA. Escrever isto pra ninguem gastar uma
tarde achando que a chave esta' errada.

## A ASSINATURA

Padrao TOP (Taobao Open Platform): junta os parametros ORDENADOS por chave,
concatena `chave+valor` sem separador, e assina com HMAC-SHA256 do
`app_secret`, em hexadecimal MAIUSCULO.

⚠️ O `sign` NAO entra no calculo dele mesmo, e o `timestamp` e' em
MILISSEGUNDOS. Errar qualquer um dos dois da' a mesma mensagem generica de
assinatura invalida, sem dizer qual.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time

import requests

URL = "https://api-sg.aliexpress.com/sync"

# ⚠️ TIMEOUT CURTO DE PROPOSITO. Onde o host e' bloqueado, a conexao nao
# recusa: ela PENDURA ate' o limite. Com 40s, cinco categorias viram tres
# minutos de espera pra descobrir que nao ha' rota.
TIMEOUT_S = 20


class SemCredencial(RuntimeError):
    """Falta app_key/app_secret. Erro alto: seguir sem credencial faz a API
    responder um erro de autenticacao que parece problema de assinatura."""


def _credencial() -> tuple[str, str]:
    k = os.getenv("ALIEXPRESS_APP_KEY")
    s = os.getenv("ALIEXPRESS_APP_SECRET")
    if not (k and s):
        raise SemCredencial(
            "faltam ALIEXPRESS_APP_KEY / ALIEXPRESS_APP_SECRET — no .env aqui, "
            "e nos Secrets do repositorio pra rodar na nuvem")
    return k, s


def assinar(params: dict, segredo: str) -> str:
    """A assinatura TOP. Separada pra poder ser testada sem rede."""
    base = "".join(f"{c}{params[c]}" for c in sorted(params) if c != "sign")
    return hmac.new(segredo.encode("utf-8"), base.encode("utf-8"),
                    hashlib.sha256).hexdigest().upper()


def chamar(metodo: str, **extra) -> dict:
    """Uma chamada assinada. Devolve o JSON cru — quem le' decide o que fazer."""
    chave, segredo = _credencial()
    p = {k: v for k, v in extra.items() if v is not None}
    p.update({"app_key": chave, "method": metodo, "sign_method": "sha256",
              "timestamp": str(int(time.time() * 1000)), "format": "json",
              "v": "2.0"})
    p["sign"] = assinar(p, segredo)
    r = requests.post(URL, data=p, timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()
