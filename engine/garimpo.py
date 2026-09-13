# -*- coding: utf-8 -*-
"""O garimpo: acha o produto que merece video.

    python -m engine.garimpo --canal truque.importado --ensaio

## O QUE ELE FAZ, E POR QUE NESTA ORDEM

    buscar -> filtrar -> guardar o preco -> julgar o desconto -> ranquear

⚠️ GUARDAR O PRECO VEM ANTES DE JULGAR O DESCONTO, e isso nao e' detalhe de
implementacao: sem historico NOSSO, a unica fonte de "desconto" e' o
`original_price` do vendedor — e ele e' inflado. Medido no Ad Center em
12/09/2026: fone a R$ 31,48 "de R$ 122,22", 74% de desconto. O de R$ 122
quase certamente nunca foi praticado.

⭐ A REGRA: **a gente so' chama de desconto o que caiu contra o preco que NOS
vimos.** Repetir o "de/por" da loja e' virar megafone de desconto falso, e
quem paga a conta e' a confianca do canal que acabou de abrir.

## ⚠️ O ADVANCED API NAO E' NECESSARIO

Eu disse ao Bryan que o `hotproduct.query` (Advanced) era o unico jeito de
ordenar por demanda real. Estava errado: o `lastest_volume` vem em CADA
produto do `product.query`, que e' Standard e ja' funciona. O Advanced
continua util pelo Smart Match, mas nao bloqueia nada.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from . import aliexpress
from . import rende_video

RAIZ = Path(__file__).resolve().parent.parent
PRECOS = RAIZ / "estado" / "precos_vistos.jsonl"

# canal interno -> o que procurar e em que faixa.
#
# ⚠️ A FAIXA DE PRECO E' PARTE DA IDENTIDADE DO CANAL, nao um filtro tecnico.
# O @achadinhos.instantaneos promete "de R$ 10 a R$ 50" na bio; produto de
# R$ 300 ali quebra a promessa mesmo sendo um bom produto.
CANAIS = {
    "truque.importado": {
        "termos": ["maquiagem", "pincel maquiagem", "skincare", "batom",
                   "organizador maquiagem"],
        "min": 10.0, "max": 120.0,
    },
    "cozinha.importada": {
        "termos": ["utensilio cozinha", "organizador cozinha", "cortador",
                   "forma silicone", "descascador"],
        "min": 10.0, "max": 150.0,
    },
    "achadinhos.instantaneos": {
        "termos": ["achadinhos casa", "organizador", "gadget util",
                   "acessorio celular"],
        "min": 10.0, "max": 50.0,
    },
    "fatura.chora": {
        "termos": ["eletronico promocao", "fone bluetooth", "smartwatch",
                   "carregador"],
        "min": 20.0, "max": 300.0,
    },
    "atefalhar": {
        "termos": ["acessorio academia", "luva treino", "faixa elastica",
                   "coqueteleira", "strap treino"],
        "min": 15.0, "max": 200.0,
    },
}

# ⚠️ OS CORTES SAO CONSERVADORES DE PROPOSITO. Produto ruim no canal custa
# mais que produto nenhum: a pessoa compra, se decepciona, e a culpa fica com
# quem indicou. Preferimos garimpar menos e acertar mais.
NOTA_MIN = 4.3          # evaluate_rate, em %
VOLUME_MIN = 100        # lastest_volume — quantos ja' venderam
COMISSAO_MIN = 3.0      # abaixo disso o video nao se paga


def _num(v, padrao=0.0) -> float:
    """Numero de campo que a API manda como TEXTO.

    ⚠️ Devolve o padrao em vez de estourar. Campo ausente e' comum e normal
    (`product_video_url` veio vazio no primeiro teste); derrubar o garimpo
    inteiro por causa de um produto sem nota seria trocar um problema pequeno
    por um grande.
    """
    try:
        return float(str(v).replace("%", "").replace(",", ".").strip())
    except (TypeError, ValueError):
        return padrao


def buscar(canal: str, por_termo: int = 20) -> list[dict]:
    """Os produtos crus deste canal, de todos os termos dele."""
    perfil = CANAIS.get(canal)
    if not perfil:
        raise KeyError(f"{canal!r} nao tem perfil de garimpo — ver CANAIS")
    vistos, saida = set(), []
    for termo in perfil["termos"]:
        r = aliexpress.chamar(
            "aliexpress.affiliate.product.query", keywords=termo,
            page_size=str(por_termo), target_currency="BRL",
            target_language="PT", ship_to_country="BR",
            tracking_id="default", sort="LAST_VOLUME_DESC")
        res = r.get("aliexpress_affiliate_product_query_response", {}) \
               .get("resp_result", {})
        if str(res.get("resp_code")) != "200":
            print(f"  [!] {termo!r}: {res.get('resp_msg')}")
            continue
        for p in (res.get("result", {}).get("products", {})
                     .get("product", []) or []):
            # ⚠️ DEDUP PELO product_id. O mesmo item aparece em varios termos,
            # e sem isto ele seria julgado e postado duas vezes.
            if p.get("product_id") in vistos:
                continue
            vistos.add(p.get("product_id"))
            saida.append(p)
    return saida


def serve(p: dict, canal: str) -> str | None:
    """None se o produto serve; senao, o MOTIVO da recusa.

    ⚠️ Devolve o motivo em vez de True/False pra o ensaio poder mostrar por
    que 90 de 100 cairam. Filtro que so' diz "nao" e' impossivel de calibrar.
    """
    perfil = CANAIS[canal]
    preco = _num(p.get("target_sale_price"))
    if not preco:
        return "sem preco"
    if preco < perfil["min"]:
        return f"barato demais (R$ {preco:.2f} < {perfil['min']:.0f})"
    if preco > perfil["max"]:
        return f"caro demais (R$ {preco:.2f} > {perfil['max']:.0f})"
    nota = _num(p.get("evaluate_rate"))
    if nota and nota < NOTA_MIN * 20:      # evaluate_rate vem em %, 0-100
        return f"nota baixa ({nota:.0f}%)"
    vol = int(_num(p.get("lastest_volume")))
    if vol < VOLUME_MIN:
        return f"pouca venda ({vol})"
    com = _num(p.get("commission_rate"))
    if com < COMISSAO_MIN:
        return f"comissao baixa ({com:.1f}%)"
    if not p.get("product_main_image_url"):
        return "sem imagem"
    return None


def guardar_preco(p: dict, quando: str | None = None) -> None:
    """Anota o preco visto hoje. Append-only.

    ⚠️ JSONL E APPEND, nunca reescrever: o historico E' o ativo. Um arquivo
    que se reescreve perde a serie no primeiro erro, e a serie so' se
    reconstroi esperando os dias de novo.
    """
    PRECOS.parent.mkdir(parents=True, exist_ok=True)
    linha = {"id": p.get("product_id"),
             "preco": _num(p.get("target_sale_price")),
             "loja": p.get("shop_name", ""),
             "quando": quando or f"{date.today():%Y-%m-%d}"}
    with PRECOS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def historico() -> dict[int, list[float]]:
    """product_id -> precos que NOS ja' vimos."""
    h: dict[int, list[float]] = {}
    if not PRECOS.exists():
        return h
    for linha in PRECOS.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            d = json.loads(linha)
        except ValueError:
            # ⚠️ Linha torta nao derruba a serie inteira. JSONL existe
            # justamente pra isso: o estrago fica na linha.
            continue
        if d.get("id") and d.get("preco"):
            h.setdefault(d["id"], []).append(float(d["preco"]))
    return h


def desconto_honesto(p: dict, h: dict[int, list[float]]) -> tuple[float, str]:
    """Quanto caiu contra o que NOS vimos. (percentual, explicacao)

    ⭐ ESTA FUNCAO E' O PONTO DO MODULO. O `original_price` da loja e' inflado
    — medido: R$ 31,48 "de R$ 122,22". Repetir isso e' anunciar desconto que
    nao existe.

    ⚠️ SEM HISTORICO, O DESCONTO E' ZERO. Nao e' "desconhecido" nem "usa o da
    loja": e' ZERO, e o post nao fala de desconto nenhum. Falha FECHADA, do
    lado que nao mente. Nos primeiros dias quase tudo vai dar zero, e isso
    esta' certo — a serie ainda nao existe.
    """
    antes = h.get(p.get("product_id"), [])
    hoje = _num(p.get("target_sale_price"))
    if not antes or not hoje:
        return 0.0, "sem histórico nosso ainda"
    maior = max(antes)
    if hoje >= maior:
        return 0.0, f"não caiu (já vimos por R$ {maior:.2f})"
    queda = (maior - hoje) / maior * 100
    return queda, f"caiu de R$ {maior:.2f} — preço que nós vimos"


def para_produto(p: dict, queda: float) -> dict:
    """Traduz o produto da API pro formato que o resto do motor ja' fala.

    ⚠️ ESTE E' O PONTO DE COSTURA, e e' onde este motor mais erra: copia por
    nome que nao bate morre CALADA. Os nomes da direita sao os do
    `engine/produto.py`; os da esquerda, os que a API devolve. Mudar um lado
    sem o outro nao levanta erro — o campo so' chega vazio la' na frente.
    """
    return {
        "nome": (p.get("product_title") or "").strip(),
        # ⚠️ O `promotion_link` JA' VEM na busca, com o nosso tracking. Nao e'
        # preciso chamar o link.generate: menos uma chamada e menos um lugar
        # onde o link pode sair sem tracking (e link sem tracking nao paga).
        "link": p.get("promotion_link") or p.get("product_detail_url") or "",
        "preco": f"R$ {_num(p.get('target_sale_price')):.2f}".replace(".", ","),
        "preco_em": f"{date.today():%Y-%m-%d}",
        "loja": p.get("shop_name", ""),
        "categoria": p.get("second_level_category_name", ""),
        "imagem": p.get("product_main_image_url", ""),
        "video": p.get("product_video_url", ""),
        # medidas que NAO vao pro post, mas explicam a escolha
        "_vendas": int(_num(p.get("lastest_volume"))),
        "_nota": _num(p.get("evaluate_rate")),
        "_comissao": _num(p.get("commission_rate")),
        "_queda": round(queda, 1),
    }


def garimpar(canal: str, quantos: int = 5,
             guardar: bool = True) -> tuple[list[dict], dict[str, int]]:
    """O garimpo de um canal. Devolve (escolhidos, por que os outros cairam)."""
    crus = buscar(canal)
    motivos: dict[str, int] = {}
    passaram = []
    for p in crus:
        # ⚠️ GUARDA O PRECO DE TODOS, inclusive dos recusados. O historico e'
        # sobre o PRODUTO, nao sobre a nossa decisao de hoje — e um item que
        # nao serve hoje pode servir quando o preco cair.
        if guardar:
            guardar_preco(p)
        motivo = serve(p, canal)
        if motivo:
            chave = motivo.split(" (")[0]
            motivos[chave] = motivos.get(chave, 0) + 1
            continue
        passaram.append(p)

    h = historico()
    saida = []
    for p in passaram:
        queda, _ = desconto_honesto(p, h)
        saida.append(para_produto(p, queda))

    # ⭐ ORDEM: queda de preco primeiro, depois VENDAS. Nota nao entra no
    # criterio de ordenacao porque ja' foi corte — e nota alta com 3 vendas
    # nao quer dizer nada.
    saida.sort(key=lambda x: (x["_queda"], x["_vendas"]), reverse=True)
    return saida[:quantos], motivos


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="o garimpo")
    a.add_argument("--canal", required=True, choices=sorted(CANAIS))
    a.add_argument("--quantos", type=int, default=5)
    a.add_argument("--ensaio", action="store_true",
                   help="nao grava o historico de preco")
    o = a.parse_args()
    achados, motivos = garimpar(o.canal, o.quantos, guardar=not o.ensaio)
    print(f"\nrecusados: " + ", ".join(f"{k} x{v}" for k, v in
                                       sorted(motivos.items(), key=lambda i: -i[1])))
    print(f"\n{len(achados)} escolhido(s) para {o.canal}:\n")
    for x in achados:
        print(f"  {x['nome'][:64]}")
        print(f"    {x['preco']} · {x['loja']} · {x['_vendas']} vendidos · "
              f"nota {x['_nota']:.0f}% · comissao {x['_comissao']:.1f}%"
              + (f" · CAIU {x['_queda']:.0f}%" if x["_queda"] else ""))


if __name__ == "__main__":
    main()


# ⚠️ O MERCADO LIVRE ENTRA COMO SEGUNDA FONTE, e nao como substituto. Os dois
# fazem coisas diferentes, e misturar sem dizer isso faria o canal de
# achadinho postar papel higienico:
#
#   AliExpress  o produto que vira video — barato, curioso, 30 mil vendidos
#   Mercado Livre  ticket maior, comissao 16% (contra 7%) e entrega em DOIS
#                  dias, nao tres semanas
#
# ⚠️ E O COOKIE DO ML E' DE 24 HORAS. Nao da' pra consertar aqui: se conserta
# na chamada do clipe, que precisa gerar clique no MESMO dia.

def do_mercado_livre(canal: str, quantos: int = 5) -> list[dict]:
    """Os mais vendidos do ML deste canal, ja' filtrados pela faixa de preco.

    ⚠️ REUSA O `serve()`? NAO — e de proposito. O ML nao devolve nota,
    volume nem comissao no mesmo formato, e forcar o filtro do AliExpress aqui
    reprovaria tudo por campo ausente. O corte que faz sentido nos dois e' a
    FAIXA DE PRECO, que e' promessa do canal; o resto e' proprio de cada fonte.
    """
    from . import mercadolivre as ml
    perfil = CANAIS.get(canal)
    if not perfil:
        return []
    saida = []
    for cat, _nome in ml.CATEGORIAS.get(canal, []):
        for p in ml.mais_vendidos(cat, 12):
            preco = _num(p["preco"].replace("R$", "").replace(",", ".").strip())
            if not (perfil["min"] <= preco <= perfil["max"]):
                continue
            # ⚠️ O CORTE EDITORIAL SO' VALE PRO MERCADO LIVRE, e de
            # proposito: no AliExpress vender muito e' sinal de qualidade
            # (alguem descobriu e presta); no ML e' sinal de commodity (todo
            # mundo ja' compra no automatico). O mesmo numero significa o
            # contrario em cada fonte.
            ok, porque = rende_video.rende(p["nome"])
            if not ok:
                print(f"  [editorial] fora: {p['nome'][:40]}… — {porque}")
                continue
            saida.append(dict(p, fonte="mercadolivre",
                              preco_em=f"{date.today():%Y-%m-%d}",
                              categoria=_nome, _vendas=0, _nota=0.0,
                              _comissao=16.0, _queda=0.0))
    return saida[:quantos]
