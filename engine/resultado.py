# -*- coding: utf-8 -*-
"""O laco: o que foi publicado -> o que aconteceu.

    python -m engine.resultado --pedidos    le' os pedidos do AliExpress
    python -m engine.resultado --placar     cruza publicado x vendido

## O BURACO QUE ISTO FECHA

Ate' 13/09/2026 tres coisas existiam e NAO se falavam:

    a serie de preco    sabe que o produto X caiu 12% no dia 14
    o Supabase          sabe que o canal Y teve 30 cliques no dia 14
    ninguem             sabia QUAL produto o canal Y publicou no dia 14

Sem o meio, os outros dois sao anedota. Este modulo e' o meio.

## ⭐ E O LACO FECHA COM VENDA, NAO COM CLIQUE

Medido em 13/09/2026: `aliexpress.affiliate.order.listbyindex` responde
`405 — The result is empty` com `status="Payment Completed"`. 405 aqui e'
"consulta valida, zero resultados" — e zero e' o esperado, porque ainda nao
houve venda. A porta esta' aberta.

⚠️ E ISSO MUDA O QUE DA' PRA AFIRMAR. Clique nao paga nada; venda paga. Um
produto com muito clique e nenhuma venda nao e' sucesso — e' uma promessa que
a pagina do vendedor nao cumpriu, e sem o pedido a gente chamaria isso de
acerto.

## ⚠️ O QUE ESTE MODULO NAO FAZ, E NAO DEVE FINGIR QUE FAZ

Ele nao ATRIBUI a venda ao clipe. O AliExpress devolve o pedido, nao a origem
dele — a atribuicao por canal viria do `tracking_id`, e hoje ha' UM so'
(`default`) pra operacao inteira.

⭐ O conserto existe e e' simples: criar um tracking_id POR CANAL no Portals.
Ate' la', o que da' pra dizer e' "a operacao vendeu N" e nao "o canal Y vendeu
N" — e isso esta' escrito aqui pra ninguem ler a planilha errado.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import aliexpress

RAIZ = Path(__file__).resolve().parent.parent
PUBLICADOS = RAIZ / "estado" / "produtos_publicados.jsonl"
PEDIDOS = RAIZ / "estado" / "pedidos.jsonl"

# ⚠️ O status importa: so' "Payment Completed" e' venda de verdade. Pedido
# criado e nao pago nao e' nada, e contar isso inflaria o resultado — que e'
# justamente o numero que vai decidir onde investir esforco.
STATUS_VALE = "Payment Completed"


def anotar_publicado(produto: dict, canal: str, onde: str) -> None:
    """Registra que ESTE produto foi publicado NESTE canal, AGORA.

    ⚠️ E' A PECA QUE FALTAVA, e ela e' append-only: sem o registro do que saiu,
    o preco e o clique nunca se encontram. `onde` diz por qual boca — clipe,
    telegram ou pagina — porque o mesmo produto sai por mais de uma.
    """
    PUBLICADOS.parent.mkdir(parents=True, exist_ok=True)
    linha = {
        "id": produto.get("_id") or produto.get("product_id"),
        "nome": (produto.get("nome") or "")[:90],
        "canal": canal, "onde": onde,
        "preco": produto.get("preco", ""),
        # ⭐ a queda MEDIDA POR NOS no momento da publicacao. Sem isto nao da'
        # pra perguntar depois "desconto de quanto move o clique?".
        "queda": produto.get("_queda", 0),
        "vendas": produto.get("_vendas", 0),
        # ⭐ O GANHO PREVISTO NO MOMENTO DA PUBLICACAO. Sem ele nao da' pra
        # perguntar depois "o que a gente ACHOU que ia render bateu com o que
        # rendeu?" — e essa e' a pergunta que transforma a escolha de produto
        # de gosto em metodo.
        "ganho_previsto": produto.get("_ganho", 0),
        "comissao": produto.get("_comissao", 0),
        "fonte": produto.get("fonte", "aliexpress"),
        # ⭐ O LINK E A IMAGEM FICAM. Ate' 14/09/2026 este registro guardava
        # so' o que o placar precisava, e a vitrine do canal nao tinha de
        # onde tirar o produto pra mostrar — as paginas ficaram com cartao de
        # exemplo ("ainda nao e' real") enquanto 25 produtos ja' estavam
        # escolhidos.
        #
        # ⚠️ E O LINK NAO SE RECUPERA DEPOIS: ele carrega o tracking do
        # momento. Buscar o produto de novo amanha da' outro link, e o
        # `promotion_link` de uma busca velha nao volta.
        "link": produto.get("link", ""),
        "imagem": produto.get("imagem", ""),
        "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with PUBLICADOS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def _ler(arquivo: Path) -> list[dict]:
    if not arquivo.exists():
        return []
    saida = []
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            saida.append(json.loads(linha))
        except ValueError:
            # ⚠️ linha torta nao derruba o resto: JSONL existe pra isso
            continue
    return saida


def buscar_pedidos(dias: int = 30) -> list[dict]:
    """Os pedidos pagos dos ultimos `dias`. Guarda os novos e devolve todos.

    ⚠️ `405 — The result is empty` NAO E' ERRO: e' "consulta valida, zero
    pedidos". Tratar 405 como falha faria o placar parecer quebrado enquanto
    a operacao simplesmente ainda nao vendeu — que e' o estado de hoje.
    """
    fim = datetime.now(timezone.utc)
    ini = fim - timedelta(days=dias)
    fmt = "%Y-%m-%d %H:%M:%S"
    r = aliexpress.chamar(
        "aliexpress.affiliate.order.listbyindex",
        start_time=ini.strftime(fmt), end_time=fim.strftime(fmt),
        status=STATUS_VALE, page_size="50")
    corpo = (r.get("aliexpress_affiliate_order_listbyindex_response") or {}) \
        .get("resp_result", {})
    codigo = str(corpo.get("resp_code"))
    if codigo == "405":
        print("  (nenhum pedido no periodo — resposta valida, nao e' erro)")
        return _ler(PEDIDOS)
    if codigo != "200":
        print(f"  [!] pedidos: {codigo} {corpo.get('resp_msg')}")
        return _ler(PEDIDOS)

    ja = {p.get("order_number") for p in _ler(PEDIDOS)}
    novos = 0
    PEDIDOS.parent.mkdir(parents=True, exist_ok=True)
    with PEDIDOS.open("a", encoding="utf-8") as f:
        for o in (corpo.get("result", {}).get("orders", {})
                     .get("order", []) or []):
            if o.get("order_number") in ja:
                continue
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
            novos += 1
    print(f"  {novos} pedido(s) novo(s)")
    return _ler(PEDIDOS)


def placar() -> dict:
    """O que a operacao publicou, e o que voltou. Honesto sobre o que nao sabe.

    ⚠️ NAO CRUZA PRODUTO COM PEDIDO, e nao vai fingir que cruza. O pedido do
    AliExpress traz o produto vendido, mas NAO traz por qual canal a pessoa
    chegou — isso viria do tracking_id, e ha' um so' pra operacao inteira.
    """
    pubs = _ler(PUBLICADOS)
    peds = _ler(PEDIDOS)
    por_canal: dict[str, dict] = {}
    for p in pubs:
        c = por_canal.setdefault(p.get("canal", "?"),
                                 {"publicados": 0, "com_queda": 0, "quedas": []})
        c["publicados"] += 1
        q = float(p.get("queda") or 0)
        if q > 0:
            c["com_queda"] += 1
            c["quedas"].append(q)
    return {"por_canal": por_canal, "pedidos": len(peds),
            "produtos_publicados": len({p.get("id") for p in pubs})}


def main() -> None:
    a = argparse.ArgumentParser(description="o laco de resultado")
    a.add_argument("--pedidos", action="store_true")
    a.add_argument("--placar", action="store_true")
    a.add_argument("--dias", type=int, default=30)
    o = a.parse_args()

    if o.pedidos:
        print("lendo pedidos do AliExpress:")
        peds = buscar_pedidos(o.dias)
        print(f"  {len(peds)} pedido(s) no registro")

    if o.placar or not o.pedidos:
        p = placar()
        print(f"\nPUBLICADO: {p['produtos_publicados']} produto(s) distinto(s)")
        for canal, d in sorted(p["por_canal"].items()):
            med = (sum(d["quedas"]) / len(d["quedas"])) if d["quedas"] else 0
            print(f"  {canal:26} {d['publicados']:>3} posts | "
                  f"{d['com_queda']} com queda medida"
                  + (f" (media {med:.0f}%)" if med else ""))
        print(f"\nVENDIDO: {p['pedidos']} pedido(s) pago(s)")
        if not p["pedidos"]:
            print("  (zero e' o esperado enquanto nao houver venda)")
        # ⚠️ O AVISO VAI JUNTO DO NUMERO, sempre. Placar sem esta linha seria
        # lido como "o canal X vendeu N", e a atribuicao por canal NAO existe
        # enquanto houver um tracking_id so'.
        print("\n⚠️ o pedido nao diz por qual CANAL a pessoa chegou —")
        print("   falta um tracking_id por canal no Portals do AliExpress")


if __name__ == "__main__":
    main()
