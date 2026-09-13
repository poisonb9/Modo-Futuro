# -*- coding: utf-8 -*-
"""O laco registra o que saiu, e NAO finge saber o que nao sabe."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import resultado  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


d = Path(tempfile.mkdtemp())
resultado.PUBLICADOS = d / "pub.jsonl"
resultado.PEDIDOS = d / "ped.jsonl"

print("1. anota o que foi publicado, com a queda MEDIDA no momento")
# ⭐ Sem a queda registrada na hora nao da' pra perguntar depois "desconto de
# quanto move o clique?" — o preco de hoje ja' nao e' o de quando saiu.
resultado.anotar_publicado(
    {"_id": 11, "nome": "Descascador de legumes", "preco": "R$ 20,71",
     "_queda": 12.0, "_vendas": 14377, "fonte": "aliexpress"},
    "cozinha.importada", "garimpo")
linha = json.loads(resultado.PUBLICADOS.read_text(encoding="utf-8").splitlines()[0])
for c in ("id", "nome", "canal", "onde", "preco", "queda", "vendas", "quando"):
    checar(c in linha, f"guarda {c}")
checar(linha["queda"] == 12.0, "a queda e' a do momento da publicacao")
checar(linha["onde"] == "garimpo", "diz por qual boca saiu")

print("\n2. o placar conta por canal")
resultado.anotar_publicado({"_id": 12, "nome": "Pote", "_queda": 0},
                           "cozinha.importada", "telegram")
resultado.anotar_publicado({"_id": 13, "nome": "Batom", "_queda": 30.0},
                           "truque.importado", "garimpo")
p = resultado.placar()
checar(p["produtos_publicados"] == 3, "tres produtos distintos")
checar(p["por_canal"]["cozinha.importada"]["publicados"] == 2, "cozinha: 2")
checar(p["por_canal"]["cozinha.importada"]["com_queda"] == 1,
       "so' um deles tinha queda medida")

print("\n3. ⭐ NEGATIVO — zero pedido NAO e' erro")
# ⚠️ `405 — The result is empty` e' consulta valida com zero resultados.
# Tratar como falha faria o placar parecer quebrado enquanto a operacao
# simplesmente ainda nao vendeu — que e' o estado de hoje.
checar(p["pedidos"] == 0, "zero pedidos hoje")
checar(resultado.STATUS_VALE == "Payment Completed",
       "so' pedido PAGO conta (criado e nao pago nao e' venda)")

print("\n4. ⭐ NEGATIVO — o modulo NAO atribui venda a canal")
# ⚠️ O pedido do AliExpress nao diz por onde a pessoa chegou. Ha' UM
# tracking_id pra operacao inteira. Um placar que dissesse "o canal X vendeu
# N" estaria inventando — e seria o tipo de numero em que se investe dinheiro.
fonte = Path("engine/resultado.py").read_text(encoding="utf-8")
checar("tracking_id por canal" in fonte,
       "o codigo diz que falta tracking_id por canal")
checar("NAO CRUZA PRODUTO COM PEDIDO" in fonte,
       "e diz explicitamente que nao cruza")
saida = resultado.placar()
checar("vendas_por_canal" not in saida,
       "o placar nao expoe campo de venda por canal (nao existe)")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
