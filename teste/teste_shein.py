# -*- coding: utf-8 -*-
"""A leitura do cartao da Shein. Sem rede e sem navegador."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import shein  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


H = "https://br.shein.com/Rick-and-Morty-X-SHEGLAM-p-846236.html?src=abc"
T = "SHEGLAM\n-53%\nRick and Morty X SHEGLAM Kit Gloss Labial Lip Honey\n(1000+)\nR$105,14"

print("1. le' o cartao inteiro")
p = shein.ler_cartao(T, H)
checar(p["codigo"] == "846236", "codigo do -p-")
checar(p["preco"] == "R$ 105,14", "preco")
checar(p["_desconto_loja"] == 53, "desconto da loja")
checar(p["_vendas"] == 1000, "vendas do (1000+)")
checar("SHEGLAM Kit Gloss" in p["nome"], "nome e' a linha mais longa")

print("\n2. ⭐ NEGATIVO — o link devolvido NAO e' de afiliado")
# ⚠️ O erro caro seria devolver o link cru como se pagasse. O campo se chama
# `link_cru` de proposito, e NAO existe campo `link` — quem for postar isso
# tem de tropecar, e nao herdar um link que nao paga.
checar("link" not in p, "nao existe campo 'link' (so' link_cru)")
checar("onelink" not in p["link_cru"], "e o link_cru nao finge ser onelink")
checar("?" not in p["link_cru"], "a query de rastreio deles foi tirada")

print("\n3. NEGATIVO — cartao incompleto nao vira produto")
checar(shein.ler_cartao(T, "") is None, "sem href -> None")
checar(shein.ler_cartao(T, "https://br.shein.com/x.html") is None,
       "href sem -p- -> None")
checar(shein.ler_cartao("SHEGLAM\n(1000+)", H) is None, "sem preco -> None")

print("\n4. sem vendas e sem desconto, ainda serve")
p2 = shein.ler_cartao("Batom liquido matte de longa duracao\nR$19,90", H)
checar(p2 is not None and p2["_vendas"] == 0 and p2["_desconto_loja"] == 0,
       "produto sem selo passa, com zeros")

print("\n5. os canais da Shein existem no garimpo")
from engine import garimpo  # noqa: E402
for c in shein.TERMOS:
    checar(c in garimpo.CANAIS, f"{c} tem perfil")
# ⚠️ E os que NAO estao sao decisao, nao esquecimento: a Shein nao tem
# eletronico nem suplemento que preste.
checar("atefalhar" not in shein.TERMOS, "atefalhar fica de fora (sem suplemento)")
checar("fatura.chora" not in shein.TERMOS, "fatura.chora fica de fora (sem eletronico)")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
