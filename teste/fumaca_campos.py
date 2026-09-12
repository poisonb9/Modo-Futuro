# -*- coding: utf-8 -*-
"""Quais campos o product.query devolve? Roda na NUVEM.

⚠️ IMPRIME SO' OS NOMES DOS CAMPOS, nao os valores: o log do Actions e'
publico e a resposta traz link com o nosso tracking.

⚠️ E ISTO NAO E' CURIOSIDADE. Escrever o garimpo chutando nome de campo e' a
causa da familia de defeitos mais cara deste motor: copia por nome que nao
bate morre CALADA, sem erro nenhum, e o campo chega vazio na outra ponta.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import aliexpress  # noqa: E402

r = aliexpress.chamar("aliexpress.affiliate.product.query",
                      keywords="fone bluetooth", page_size="2",
                      target_currency="BRL", target_language="PT",
                      ship_to_country="BR", tracking_id="default")
res = r["aliexpress_affiliate_product_query_response"]["resp_result"]
print("resp_code:", res.get("resp_code"))
result = res.get("result", {})
print("chaves do result:", sorted(result))
prods = result.get("products", {}).get("product", [])
print("produtos:", len(prods))
if prods:
    print("\nCAMPOS DE UM PRODUTO:")
    for c in sorted(prods[0]):
        v = prods[0][c]
        tipo = type(v).__name__
        # ⚠️ so' o TAMANHO do valor, nunca o valor
        print(f"  {c:34} {tipo:6} ({len(str(v))} chars)")
