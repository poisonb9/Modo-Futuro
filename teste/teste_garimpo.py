# -*- coding: utf-8 -*-
"""O garimpo filtra o que deve e NAO inventa desconto. Roda sem rede."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import garimpo, produto  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


# ⚠️ historico de mentira: sem isto o teste escreveria no estado de producao
garimpo.PRECOS = Path(tempfile.mkdtemp()) / "precos.jsonl"

BOM = {"product_id": 1, "product_title": "Organizador de gaveta 6 divisórias",
       "target_sale_price": "29.90", "evaluate_rate": "96.0",
       "lastest_volume": "3500", "commission_rate": "8.0",
       "product_main_image_url": "https://x/i.jpg", "shop_name": "Loja X",
       "promotion_link": "https://s.click.aliexpress.com/e/_abc",
       "product_detail_url": "https://pt.aliexpress.com/item/1.html",
       "original_price": "122.22"}

print("1. o produto bom passa")
checar(garimpo.serve(BOM, "achadinhos.instantaneos") is None, "passa")

print("\n2. NEGATIVO — cada corte reprova o seu caso")
casos = [("target_sale_price", "5.00", "barato"),
         ("target_sale_price", "480.00", "caro"),
         ("evaluate_rate", "70.0", "nota baixa"),
         ("lastest_volume", "9", "pouca venda"),
         ("commission_rate", "1.0", "comissao baixa"),
         ("product_main_image_url", "", "sem imagem")]
for campo, valor, oq in casos:
    m = garimpo.serve(dict(BOM, **{campo: valor}), "achadinhos.instantaneos")
    checar(m is not None, f"{oq} -> recusado ({m})")

print("\n3. ⭐ O DESCONTO NAO SAI DO 'de/por' DA LOJA")
# O produto traz original_price 122,22 e preco 29,90 — 76% pela conta da loja.
h = garimpo.historico()
queda, porque = garimpo.desconto_honesto(BOM, h)
checar(queda == 0.0,
       f"sem historico nosso -> desconto ZERO, nao 76% ({porque})")
checar("122" not in porque, "e nao repete o preco inflado da loja")

print("\n4. com historico NOSSO, o desconto aparece")
garimpo.guardar_preco(dict(BOM, target_sale_price="59.80"), "2026-09-01")
h = garimpo.historico()
queda, porque = garimpo.desconto_honesto(BOM, h)
checar(abs(queda - 50.0) < 0.1, f"caiu de 59,80 para 29,90 = 50% ({queda:.1f}%)")
checar("59" in porque, "e a explicacao cita o preco que NOS vimos")

print("\n5. NEGATIVO — preco que subiu nao vira desconto")
garimpo.guardar_preco(dict(BOM, product_id=2, target_sale_price="10.00"),
                      "2026-09-01")
q2, _ = garimpo.desconto_honesto(dict(BOM, product_id=2,
                                      target_sale_price="19.90"),
                                 garimpo.historico())
checar(q2 == 0.0, "subiu de 10 para 19,90 -> desconto 0, nao negativo")

print("\n6. a costura com o resto do motor (copia por nomes)")
p = garimpo.para_produto(BOM, 12.0)
norm = produto.normalizar(p)
checar(norm is not None, "o produto.normalizar aceita o que o garimpo monta")
checar(norm["link"].startswith("https://s.click.aliexpress.com"),
       "usa o promotion_link (com tracking), nao o link cru")
# ⚠️ caso negativo da costura: sem promotion_link ele NAO pode ficar vazio
sem = garimpo.para_produto(dict(BOM, promotion_link=""), 0)
checar(sem["link"] == BOM["product_detail_url"],
       "sem promotion_link, cai pro link cru (e nao vazio)")

print("\n7. faixa de preco e' por CANAL, nao global")
# R$ 120 serve pro fatura.chora e NAO serve pro achadinhos.instantaneos
caro = dict(BOM, target_sale_price="120.00")
checar(garimpo.serve(caro, "fatura.chora") is None, "R$120 serve no fatura")
checar(garimpo.serve(caro, "achadinhos.instantaneos") is not None,
       "R$120 NAO serve no instantaneos (a bio promete ate' R$50)")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
