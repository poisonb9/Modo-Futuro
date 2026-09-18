# -*- coding: utf-8 -*-
"""ApiCallLimit de um segundo nao pode matar a rodada da hora. Sem rede.

MEDIDO em 18/09/2026: 07:35 e 10:56 UTC, lote 3 de 4, `"ApiCallLimit" ...
"this ban will last 1 seconds"`, e a rodada inteira estourava.

O que protege:
1. limite UMA vez -> espera, tenta de novo, e o lote entra;
2. ⛔ limite DUAS vezes -> estoura como antes (silencio custou 49 produtos);
3. resposta boa -> uma chamada so', sem espera.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import precos, aliexpress  # noqa: E402
import time  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


LIMITE = {"error_response": {"type": "ISV", "code": "ApiCallLimit",
                             "msg": "Api access frequency exceeds the limit. this ban will last 1 seconds"}}


def bom(ids):
    return {"aliexpress_affiliate_productdetail_get_response": {"resp_result": {"result": {"products": {"product": [
        {"product_id": int(i), "target_sale_price": "9.90", "product_main_image_url": "m",
         "product_small_image_urls": {"string": ["m", "e1"]}} for i in ids]}}}}}


_chamar, _sleep, _respiro = aliexpress.chamar, time.sleep, precos.RESPIRO_LIMITE_S
try:
    time.sleep = lambda s: None
    precos.RESPIRO_LIMITE_S = 0

    print("1. limite uma vez -> tenta de novo e o lote entra")
    fila = [LIMITE, "bom"]
    chamadas = []
    def _uma(metodo, **k):
        chamadas.append(k["product_ids"])
        r = fila.pop(0)
        return bom(k["product_ids"].split(",")) if r == "bom" else r
    aliexpress.chamar = _uma
    r = precos.puxar(["1", "2"])
    checar(r == {"1": 9.9, "2": 9.9}, f"os dois precos vieram ({r})")
    checar(len(chamadas) == 2, f"duas chamadas, nao uma ({len(chamadas)})")
    checar(precos.ULTIMAS_FOTOS.get("1") == ["e1"], "e as fotos extras vieram junto")

    print("2. ⛔ limite duas vezes -> estoura (nunca em silencio)")
    fila = [LIMITE, LIMITE]
    aliexpress.chamar = _uma
    estourou = ""
    try:
        precos.puxar(["1"])
    except RuntimeError as e:
        estourou = str(e)
    checar("ApiCallLimit" in estourou, "levantou RuntimeError com o envelope do Ali")

    print("3. resposta boa -> uma chamada so'")
    chamadas = []
    aliexpress.chamar = lambda metodo, **k: (chamadas.append(1), bom(k["product_ids"].split(",")))[1]
    precos.puxar(["7"])
    checar(len(chamadas) == 1, "sem limite, sem segunda chamada")
finally:
    aliexpress.chamar, time.sleep, precos.RESPIRO_LIMITE_S = _chamar, _sleep, _respiro

print()
print("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde")
sys.exit(1 if falhas else 0)
