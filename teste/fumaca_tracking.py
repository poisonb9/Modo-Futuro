# -*- coding: utf-8 -*-
"""Qual tracking_id existe nesta conta? Roda na NUVEM.

⚠️ A API do AliExpress nao tem "liste meus tracking ids". O jeito de
descobrir e' TENTAR gerar um link com cada candidato: o invalido e' recusado
com mensagem propria, e o valido devolve o link.

⚠️ E ISTO IMPORTA MAIS DO QUE PARECE: `link.generate` com tracking_id errado
pode devolver um link que ABRE A PAGINA NORMALMENTE e nao paga nada. Falhar
aqui, no teste, e' o unico lugar barato de falhar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import aliexpress  # noqa: E402

# Uma URL qualquer do AliExpress serve de cobaia: o que se testa e' o
# tracking_id, nao o produto.
ALVO = "https://pt.aliexpress.com/item/1005006568047850.html"
CANDIDATOS = ["default", "achadinho", "achadinhototal", "modofuturo",
              "bryan", "tiktok"]

print("testando tracking_id, um por um\n")
achou = []
for t in CANDIDATOS:
    try:
        r = aliexpress.chamar("aliexpress.affiliate.link.generate",
                              promotion_link_type="0", source_values=ALVO,
                              tracking_id=t)
    except Exception as e:
        print(f"  {t:16} ESTOUROU: {type(e).__name__}")
        continue
    if "error_response" in r:
        e = r["error_response"]
        print(f"  {t:16} recusado: {e.get('code')} {e.get('sub_msg') or e.get('msg')}")
        continue
    corpo = r.get("aliexpress_affiliate_link_generate_response", {})
    res = corpo.get("resp_result", {})
    if str(res.get("resp_code")) != "200":
        print(f"  {t:16} resp_code {res.get('resp_code')}: {res.get('resp_msg')}")
        continue
    links = res.get("result", {}).get("promotion_links", {}).get("promotion_link", [])
    if links:
        # ⚠️ NAO imprime o link: ele carrega o nosso tracking e o log e' publico.
        print(f"  {t:16} ✅ VALIDO — gerou {len(links)} link(s)")
        achou.append(t)
    else:
        print(f"  {t:16} respondeu, mas sem link (tracking provavelmente invalido)")

print("\nvalidos:", ", ".join(achou) if achou else "NENHUM")
sys.exit(0 if achou else 1)
