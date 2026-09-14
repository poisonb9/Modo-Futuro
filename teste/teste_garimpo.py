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
checar(abs(u2[99][0] - 44.90) < 0.01, "ultimo preco = 44,90 (nao o menor)")

print("")
print("11. ⭐ VOLUME CONFIRMA PRECO — e por isso ele entra na serie")
# ⭐ Dos mentores de trading do acervo: queda com volume SUBINDO e'
# oportunidade; a mesma queda com volume CAINDO e' produto morrendo. Sem o
# volume as duas ficam identicas na serie.
garimpo.PRECOS.write_text("", encoding="utf-8")
u3 = {}
V = dict(BOM, product_id=77, target_sale_price="80.00", lastest_volume="1000")
checar(garimpo.guardar_preco(V, "2026-09-13", u3), "1o ponto grava")
import json as _j
d0 = _j.loads(garimpo.PRECOS.read_text(encoding="utf-8").splitlines()[0])
for campo in ("vol", "nota", "com", "desc_loja", "de_loja", "nome", "cat"):
    checar(campo in d0, f"guarda {campo}")
checar(d0["vol"] == 1000, "o volume e' o da API")

print("")
print("12. NEGATIVO — volume so' conta quando mexe DE VERDADE")
# ⚠️ Preco anda em degraus; volume anda TODO DIA. Sem piso, o volume gravaria
# uma linha por dia e desfaria a economia inteira.
checar(not garimpo.guardar_preco(dict(V, lastest_volume="1050"),
                                 "2026-09-14", u3),
       "volume +5%: NAO grava (abaixo do piso de 10%)")
checar(garimpo.guardar_preco(dict(V, lastest_volume="1200"),
                             "2026-09-15", u3),
       "volume +20%: grava, mesmo com o preco igual")
n = len([x for x in garimpo.PRECOS.read_text(encoding="utf-8").splitlines() if x.strip()])
checar(n == 2, f"tres visitas viraram duas linhas ({n})")

print("")
print("13. o nome so' na PRIMEIRA linha")
# ⚠️ Repetir o nome em cada ponto desfaria a economia. O id liga o resto.
d1 = _j.loads(garimpo.PRECOS.read_text(encoding="utf-8").splitlines()[1])
checar("nome" not in d1, "a segunda linha nao repete o nome")
checar(garimpo.nomes()[77] == BOM["product_title"][:90],
       "e o nome e' lido da primeira linha")

print("")
print("14. ⭐ ESCALADA E' TENDENCIA, e nao se confunde com NIVEL")
# ⭐ Volume alto e' passado; volume acelerando e' futuro. O campeao saturado e
# o produto decolando sao perguntas diferentes, e as listas PODEM nao se
# cruzar. Confundir as duas faz a gente publicar sempre o mesmo item velho.
garimpo.PRECOS.write_text("", encoding="utf-8")
def _p(pid, vol, quando, preco="50.00", nome="Produto"):
    garimpo.guardar_preco(
        {"product_id": pid, "target_sale_price": preco, "lastest_volume": str(vol),
         "product_title": nome, "shop_name": "X"}, quando, {})
# gigante parado: muito volume, sem crescimento
_p(1, 40000, "2026-09-10", nome="Gigante saturado")
_p(1, 40200, "2026-09-15", nome="Gigante saturado")
# pequeno decolando
_p(2, 500, "2026-09-10", nome="Decolando")
_p(2, 2000, "2026-09-15", nome="Decolando")
esc = garimpo.escalada()
ids = [x["id"] for x in esc]
checar(2 in ids, "o que acelerou entra na escalada")
checar(ids[0] == 2, "e vem em PRIMEIRO, na frente do gigante")
camp = [c["id"] for c in garimpo.campeoes()]
checar(1 in camp, "o gigante e' campeao (nivel)")
checar(2 not in camp, "e o decolando NAO e' — as listas sao diferentes")

print("")
print("15. NEGATIVO — ruido pequeno nao vira tendencia")
# ⚠️ Sem piso, um produto de 10 -> 30 vendas ganha da lista com +200% e nao
# significa nada.
_p(3, 10, "2026-09-10", nome="Ruido")
_p(3, 30, "2026-09-15", nome="Ruido")
checar(3 not in [x["id"] for x in garimpo.escalada()],
       "10 -> 30 vendas (+200%) NAO entra: abaixo do piso")

print("")
print("16. NEGATIVO — sem dois pontos nao ha' tendencia")
# ⚠️ Tendencia nao se inventa no primeiro dia.
_p(4, 9000, "2026-09-15", nome="So um ponto")
checar(4 not in [x["id"] for x in garimpo.escalada()],
       "um ponto so' nao vira escalada")
checar(4 in [c["id"] for c in garimpo.campeoes()],
       "mas ja' conta como campeao (nivel precisa de um ponto so')")

print("")
print("17. ⭐ O DINHEIRO ENTRA NA CONTA — e nao e' o volume que paga")
# ⭐ Pedido do Bryan em 13/09: "temos que lucrar muito". Ate' entao o garimpo
# ordenava por queda e VOLUME, e volume nao paga conta: o mais vendido pode
# ser o que menos rende. Mesmo esforco de video, retorno diferente.
checar(abs(garimpo.ganho_por_venda(38.66, 16.0) - 6.19) < 0.01,
       "Cicaplast 16%: R$ 6,19 por venda")
checar(abs(garimpo.ganho_por_venda(12.71, 7.0) - 0.89) < 0.01,
       "pincel 7%: R$ 0,89 por venda — 7x menos pelo mesmo video")
p = garimpo.potencial({"preco": "R$ 38,66", "_comissao": 16.0, "_vendas": 100000})
checar(p["_ganho"] == 6.19 and p["_potencial"] == 619000,
       "potencial = ganho x volume historico")

print("")
print("18. NEGATIVO — com comissao zero, o ganho e' zero (nao 'desconhecido')")
# ⚠️ Produto sem comissao nao rende nada. Tratar como desconhecido faria ele
# competir de igual pra igual com quem paga.
z = garimpo.potencial({"preco": "R$ 99,00", "_comissao": 0, "_vendas": 50000})
checar(z["_ganho"] == 0 and z["_potencial"] == 0, "sem comissao -> zero")

print("")
print("19. O DINHEIRO MANDA NA ORDEM — e o codigo diz o que ele NAO sabe")
# ⚠️ ESTA GUARDA MUDOU EM 14/09/2026, junto com a decisao do Bryan: a ordem
# passou a ser por dinheiro. O que ela protege NAO mudou — que a escolha
# continue declarada como escolha, e nao disfarçada de medicao.
#
# ⚠️ E o dinheiro aqui e' `_potencial` (ganho x volume), nao o preco nem o
# ganho sozinho: ordenar so' por ganho empurra pro item caro, que rende mais
# por unidade e vende menos.
fonte = Path("engine/garimpo.py").read_text(encoding="utf-8")
import re as _re  # noqa: E402
plano = _re.sub(r"[\s#]+", " ", fonte)
checar('key=lambda x: (x["_potencial"]' in fonte,
       "ordena pelo potencial, que cruza ganho com demanda")
# ⭐ O QUE NAO PODE SUMIR: a admissao de que nao medimos conversao. No dia em
# que houver venda por canal, esta ordem deixa de ser palpite — e ate" la'"
# o codigo tem de dizer que e' palpite.
checar("volume do MERCADO, nao o nosso" in plano,
       "o codigo admite que o volume nao e' nosso")
checar("deixa de ser escolha e vira pergunta" in plano or
       "vira pergunta respondida" in plano,
       "e diz o que faria a ordem virar medicao")
fonte = Path("engine/garimpo.py").read_text(encoding="utf-8")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
