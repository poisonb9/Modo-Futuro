# -*- coding: utf-8 -*-
"""O AliExpress nos deixa LER os pedidos gerados? Roda na nuvem.

⚠️ Esta e' a pergunta que decide o desenho do laco de medicao. Se der pra ler
pedido, a gente fecha o ciclo com VENDA. Se nao der, o melhor disponivel e' o
clique — que e' bem pior, porque clique nao paga nada.

⚠️ NAO IMPRIME VALOR NENHUM de pedido: o log do Actions e' publico.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import aliexpress  # noqa: E402

ate = date.today()
de = ate - timedelta(days=30)
fmt = "%Y-%m-%d %H:%M:%S"

# ⚠️ Os dois endpoints EXISTEM — na 1a tentativa reclamaram de PARAMETRO, nao
# de permissao ("pattern of input params is invalid" e "status is mandatory").
# Entao o que falta e' acertar a forma, e vale tentar mais de uma.
tentativas = [
    ("aliexpress.affiliate.order.listbyindex",
     {"start_time": de.strftime(fmt), "end_time": ate.strftime(fmt),
      "status": "Payment Completed", "page_size": "20"}),
    ("aliexpress.affiliate.order.listbyindex",
     {"start_time": de.strftime(fmt), "end_time": ate.strftime(fmt),
      "status": "", "page_size": "20"}),
    ("aliexpress.affiliate.order.list",
     {"start_time": de.strftime(fmt), "end_time": ate.strftime(fmt),
      "status": "Payment Completed", "page_no": "1", "page_size": "20",
      "fields": "order_number"}),
]
for metodo, extra in tentativas:
    print("")
    print("--- " + metodo + "  status=" + repr(extra.get("status")))
    try:
        r = aliexpress.chamar(metodo, **extra)
    except Exception as e:
        print("  ESTOUROU:", type(e).__name__, str(e)[:100])
        continue
    if "error_response" in r:
        e = r["error_response"]
        print("  RECUSOU:", e.get("code"), e.get("sub_msg") or e.get("msg"))
        continue
    chave = next((k for k in r if k.endswith("_response")), None)
    corpo = (r.get(chave) or {}).get("resp_result", r.get(chave) or {})
    print("  resp_code:", corpo.get("resp_code"), "|", corpo.get("resp_msg"))
    res = corpo.get("result") or {}
    print("  chaves do result:", sorted(res)[:8])
    for k in ("total_record_count", "current_record_count"):
        if k in res:
            print(f"  {k}: {res[k]}")
