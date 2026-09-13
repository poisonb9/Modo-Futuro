# -*- coding: utf-8 -*-
"""Da' pra acompanhar um produto ESPECIFICO pelo id? Roda na nuvem.

⚠️ Isto decide se a lista de vigia pode ser de PRODUTOS ou so' de PALAVRAS.
Por palavra, o "mais vendido de hoje" pode ser outro item amanha e a serie
troca de dono sem ninguem notar. Por id, a serie e' do produto.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import aliexpress  # noqa: E402

# pega dois ids reais de uma busca, e tenta ler os dois de uma vez
r = aliexpress.chamar("aliexpress.affiliate.product.query",
                      keywords="fone bluetooth", page_size="3",
                      target_currency="BRL", target_language="PT",
                      ship_to_country="BR", tracking_id="default")
prods = (r["aliexpress_affiliate_product_query_response"]["resp_result"]
          ["result"]["products"]["product"])
ids = ",".join(str(p["product_id"]) for p in prods[:2])
print("ids de teste:", ids)

d = aliexpress.chamar("aliexpress.affiliate.productdetail.get",
                      product_ids=ids, target_currency="BRL",
                      target_language="PT", ship_to_country="BR",
                      tracking_id="default",
                      fields="product_title,target_sale_price,lastest_volume")
if "error_response" in d:
    e = d["error_response"]
    print("RECUSOU:", e.get("code"), e.get("sub_msg") or e.get("msg"))
    sys.exit(1)
corpo = d["aliexpress_affiliate_productdetail_get_response"]["resp_result"]
print("resp_code:", corpo.get("resp_code"), "|", corpo.get("resp_msg"))
lista = (corpo.get("result", {}).get("products", {}).get("product", []) or [])
print("produtos devolvidos:", len(lista), "(pedi 2)")
if lista:
    print("campos:", sorted(lista[0])[:10])
    print("tem volume?", "lastest_volume" in lista[0])
