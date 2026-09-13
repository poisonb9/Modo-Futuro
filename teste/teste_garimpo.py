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


print("")
print("8. ⭐ SO' GRAVA QUANDO O PRECO MUDA")
# ⚠️ MEDIDO em 13/09: de 156 produtos vistos duas vezes, so' 9 mudaram. 94%
# das repeticoes eram lixo — e o arquivo e' COMMITADO todo dia.
garimpo.PRECOS.write_text("", encoding="utf-8")
u = {}
P9 = dict(BOM, product_id=99, target_sale_price="50.00")
checar(garimpo.guardar_preco(P9, "2026-09-13", u), "1a vez: grava (nao ha' antes)")
checar(not garimpo.guardar_preco(P9, "2026-09-14", u), "mesmo preco: NAO grava")
checar(garimpo.guardar_preco(dict(P9, target_sale_price="44.90"),
                             "2026-09-15", u), "preco mudou: grava")
checar(not garimpo.guardar_preco(dict(P9, target_sale_price="44.90"),
                                 "2026-09-16", u), "voltou a repetir: NAO grava")
n = len([x for x in garimpo.PRECOS.read_text(encoding="utf-8").splitlines() if x.strip()])
checar(n == 2, f"quatro visitas viraram duas linhas ({n})")

print("")
print("9. ⭐ E A SERIE CONTINUA CORRETA — a economia nao pode custar o dado")
# ⚠️ O desconto usa o MAIOR ja' visto; se a economia apagasse pontos, a queda
# sumiria. Aqui: viu por 50, caiu pra 44,90 -> 10,2%.
h = garimpo.historico()
q, porque = garimpo.desconto_honesto(dict(P9, target_sale_price="44.90"), h)
checar(abs(q - 10.2) < 0.2, f"queda de 50 para 44,90 = {q:.1f}%")
checar("50" in porque, "e cita o preco que NOS vimos")

print("")
print("10. NEGATIVO — ultimo_preco e' o ULTIMO, nao o menor")
# ⚠️ Confundir os dois faria a serie parar de gravar quedas sucessivas.
u2 = garimpo.ultimo_preco()
checar(abs(u2[99] - 44.90) < 0.01, f"ultimo = 44,90 (nao o menor nem o maior)")
print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
