# -*- coding: utf-8 -*-
"""A chave do AliExpress responde? Roda na nuvem (ver o workflow).

⚠️ NAO IMPRIME A RESPOSTA INTEIRA de proposito: ela traz link com o nosso
tracking, e o log do Actions e' publico neste repositorio. Imprime o que
prova a chamada — codigo de erro, quantos produtos vieram, o primeiro titulo.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import aliexpress  # noqa: E402


def olhar(nome, r):
    print(f"\n--- {nome}")
    if "error_response" in r:
        e = r["error_response"]
        print("  RECUSOU:", e.get("code"), "|", e.get("msg"),
              "|", e.get("sub_msg"))
        return False
    chave = next((k for k in r if k.endswith("_response")), None)
    corpo = r.get(chave, r)
    txt = json.dumps(corpo, ensure_ascii=False)
    print("  respondeu ok |", len(txt), "bytes")
    print("  chaves:", list(corpo)[:6])
    return True


ok = 0
# 1. categorias — a chamada mais simples do pacote Standard, sem tracking_id
try:
    ok += olhar("aliexpress.affiliate.category.get",
                aliexpress.chamar("aliexpress.affiliate.category.get"))
except Exception as e:
    print("\n--- category.get\n  ESTOUROU:", type(e).__name__, str(e)[:120])

# 2. busca de produto — e' o que o garimpo vai usar de verdade
try:
    r = aliexpress.chamar("aliexpress.affiliate.product.query",
                          keywords="kitchen gadget", page_size="3",
                          target_currency="BRL", target_language="PT",
                          ship_to_country="BR")
    if olhar("aliexpress.affiliate.product.query", r):
        ok += 1
        try:
            itens = (r["aliexpress_affiliate_product_query_response"]["resp_result"]
                      ["result"]["products"]["product"])
            print("  produtos:", len(itens))
            print("  1o titulo:", itens[0].get("product_title", "")[:70])
            print("  preco:", itens[0].get("target_sale_price"),
                  itens[0].get("target_sale_price_currency"))
        except (KeyError, IndexError, TypeError) as e:
            print("  (veio resposta, mas o caminho mudou:", type(e).__name__, ")")
except Exception as e:
    print("\n--- product.query\n  ESTOUROU:", type(e).__name__, str(e)[:120])

print(f"\n{ok} de 2 chamadas responderam")
sys.exit(0 if ok else 1)
