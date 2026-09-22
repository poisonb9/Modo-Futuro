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

# ⚠️ O TRACKING_ID E' O QUE DIZ *QUAL CANAL* VENDEU — e hoje ha' UM so'.
#
# O `promotion_link` ja' vem carimbado com o tracking_id que a busca pediu
# (ver `montar`), entao trocar o id AQUI e' o conserto inteiro da atribuicao
# por canal: nao ha' segundo lugar pra mexer.
#
# ⚠️ FALHA FECHADA DO LADO QUE PAGA: canal sem id cai no `default`, que e' o
# unico MEDIDO como valido (teste/fumaca_tracking.py, 12/09/2026). Inventar
# o nome do id seria pior que nao ter: `link.generate` com id errado devolve
# um link que ABRE A PAGINA NORMALMENTE e nao paga nada — a venda acontece e
# ninguem ve' que ela se perdeu.
#
# ⭐ PRA LIGAR: criar os ids em portals.aliexpress.com -> Ad Center ->
# Tracking ID, rodar `python teste/fumaca_tracking.py` com os nomes novos na
# lista de CANDIDATOS, e so' depois escrever aqui o que ELE aprovou.
# ⭐ LIGADO EM 15/09/2026. Os ids foram criados pelo Bryan em
# portals.aliexpress.com -> Ad Center -> Tracking ID, e cada um destes foi
# PROVADO por `teste/fumaca_tracking.py` antes de entrar aqui: o `link.generate`
# gerou link com todos. Na mesma rodada, `achadinho`, `bryan` e `tiktok` — que
# nao existem no painel — foram recusados com `402 TrackingId input parameter
# error`, que e' o caso negativo sem o qual a prova nao valeria nada.
TRACKING: dict[str, str] = {
    "truque.importado":        "achadinhomake",
    "cozinha.importada":       "achadinhochef",
    "achadinhos.instantaneos": "instantaneos",
    "fatura.chora":            "pagomenos",
    "atefalhar":               "atefalhar",
    "modofuturo":              "modofuturo",
    # ⛔ `semanestesia.pod` FICA COMENTADO: este id NAO existe no painel. Os
    # outros nove foram conferidos na tela (default, os cinco de canal,
    # modofuturo, achadinhototal, achadinhosfuturo e achadinhosfuturo2) e este
    # nao esta' entre eles. Escreve-lo aqui devolveria um link que ABRE A
    # PAGINA e nao paga — pior do que cair no `default`, porque a venda
    # aconteceria e ninguem veria que se perdeu.
    # "semanestesia.pod":      "semanestesia",
}
TRACKING_PADRAO = "default"


def tracking_de(canal: str) -> str:
    """O tracking_id deste canal, ou o `default` enquanto ele nao existir."""
    return TRACKING.get(canal) or TRACKING_PADRAO

# ⚠️ TERMO CURTO E GENERICO TRAZ O CATALOGO INTEIRO, e o AliExpress e' global:
# "cortador" devolveu tesoura de poda e alicate de unha pro canal de COZINHA,
# e "achadinhos casa" devolveu VAZIO (e' gorduroso de portugues brasileiro,
# nao existe no catalogo deles).
#
# ⭐ A REGRA QUE SOBROU DA PRIMEIRA RODADA: termo com DUAS PALAVRAS, sendo uma
# o objeto e a outra o contexto. "cortador" e' ambiguo; "cortador legumes" nao.
# Termo de uma palavra so' quando ele ja' e' o objeto inteiro ("espatula").
#
# ⚠️ E NAO USAR GIRIA NOSSA. "achadinho", "garimpo", "promo" sao palavras da
# nossa operacao, nao do catalogo. O vendedor chines nao escreve isso.
# ⚠️ OS TERMOS FORAM TRIPLICADOS EM 14/09/2026, a pedido do Bryan: o
# catalogo tinha 25 produtos e isso e' pouco pra uma vitrine — e pouco
# demais pro upsell, que fica sem candidato pra sugerir.
#
# ⚠️ E AMPLIAR A BUSCA NAO E' BAIXAR O FILTRO. O `serve()` continua igual:
# nota, volume, comissao, preco e imagem. Mais termos = mais CANDIDATOS
# examinados; quem entra continua passando pelas mesmas seis portas.
#
# ⭐ Cada termo novo segue a regra que a primeira rodada ensinou: DUAS
# palavras, uma o objeto e outra o contexto. Termo de uma palavra so'
# quando ele ja' e' o objeto inteiro.
CANAIS = {
    "truque.importado": {
        "termos": ["pincel maquiagem", "esponja maquiagem", "batom liquido",
                   "serum facial", "organizador maquiagem", "cilios postico",
                   "paleta sombra", "delineador caneta", "base liquida",
                   "corretivo facial", "mascara cilios", "iluminador facial",
                   "primer facial", "batom matte", "lapis sobrancelha",
                   "kit pinceis", "espelho maquiagem", "necessaire maquiagem",
                   "gloss labial", "rolo massagem facial"
                   ],
        "min": 10.0, "max": 120.0,
    },
    "cozinha.importada": {
        # ⚠️ "cortador" sozinho trouxe tesoura de poda e alicate de unha.
        "termos": ["cortador legumes", "organizador geladeira", "espatula",
                   "forma silicone", "descascador legumes", "pote hermetico",
                   "ralador queijo", "abridor lata", "tabua corte",
                   "escorredor macarrao", "porta tempero", "prensa alho",
                   "batedor manual", "luva forno", "organizador panela",
                   "saco silicone", "colher silicone", "peneira inox",
                   "termometro cozinha", "dosador tempero"
                   ],
        "min": 10.0, "max": 150.0,
    },
    "achadinhos.instantaneos": {
        # ⚠️ "achadinhos casa" devolveu VAZIO — e' giria nossa.
        "termos": ["organizador gaveta", "suporte celular", "luminaria led",
                   "organizador cabo", "gancho adesivo",
                   "organizador banheiro", "cabide roupa", "porta escova",
                   "fita led", "organizador sapato", "prateleira adesiva",
                   "porta chaves", "tapete antiderrapante", "dispenser sabonete",
                   "cesto roupa", "rodo pia", "suporte notebook",
                   "organizador maleta", "capa sofa"
                   ],
        "min": 10.0, "max": 50.0,
    },
    "fatura.chora": {
        "termos": ["fone bluetooth", "smartwatch", "carregador rapido",
                   "power bank", "caixa som bluetooth",
                   "fone ouvido", "mouse sem fio", "teclado bluetooth",
                   "hub usb", "cabo tipo c", "ring light",
                   "microfone lapela", "projetor portatil", "adaptador hdmi",
                   "cartao memoria", "carregador veicular", "rastreador bluetooth",
                   "balanca digital", "suporte monitor"
                   ],
        "min": 20.0, "max": 300.0,
    },
    "atefalhar": {
        "termos": ["luva academia", "faixa elastica treino", "coqueteleira",
                   "strap treino", "corda pular",
                   "halter ajustavel", "colchonete yoga", "rolo massagem",
                   "garrafa academia", "tornozeleira peso", "elastico exercicio",
                   "joelheira esportiva", "munhequeira treino", "bolsa academia",
                   "roda abdominal", "luva levantamento", "cinto lombar",
                   "massageador muscular", "barra fixa"
                   ],
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
            tracking_id=tracking_de(canal), sort="LAST_VOLUME_DESC")
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


# ⚠️ QUANTO O VOLUME PRECISA MUDAR pra valer uma linha nova. Preco muda em
# degraus; volume de vendas anda TODO DIA, e gravar cada passo devolveria o
# desperdicio que a economia de 13/09 acabou de tirar.
VOLUME_MUDOU_FRAC = 0.10


def guardar_preco(p: dict, quando: str | None = None,
                  ultimos: dict[int, tuple[float, int]] | None = None) -> bool:
    """Anota o ponto SO' SE mudou o preco ou o volume. Devolve se gravou.

    ⭐ PRECO SOZINHO NAO CONTA A HISTORIA — e isso vem dos mentores de trading
    que o Bryan ja' tem no acervo: VOLUME CONFIRMA PRECO. Uma queda com volume
    SUBINDO e' oportunidade; a mesma queda com volume CAINDO e' um produto
    morrendo. Sao coisas opostas e, so' com preco, ficam iguais na serie.

    ⚠️ MEDIDO em 13/09/2026 com 856 linhas: 156 produtos vistos duas vezes,
    apenas 9 mudaram de preco. Por isso a regra do ponto de mudanca — mas ela
    tem de valer pros DOIS eixos, senao o volume nunca entra ou entra sempre.

    ⚠️ E O NOME SO' NA PRIMEIRA LINHA. Antes de hoje a serie nao guardava nome
    nenhum: 698 produtos eram numeros orfaos, e a pergunta do Bryan ("temos
    medicao de PS5?") nao tinha como ser respondida.
    """
    pid = p.get("product_id")
    preco = _num(p.get("target_sale_price"))
    if not (pid and preco):
        return False
    vol = int(_num(p.get("lastest_volume")))
    antes = (ultimos or {}).get(pid)
    if antes is not None:
        p_antes, v_antes = antes
        mudou_preco = abs(p_antes - preco) >= 0.005
        mudou_vol = v_antes > 0 and abs(vol - v_antes) / v_antes >= VOLUME_MUDOU_FRAC
        if not (mudou_preco or mudou_vol):
            return False
    PRECOS.parent.mkdir(parents=True, exist_ok=True)
    linha = {"id": pid, "preco": preco,
             # ⭐ o par que da' sentido ao preco
             "vol": vol,
             "nota": _num(p.get("evaluate_rate")),
             "com": _num(p.get("commission_rate")),
             # ⚠️ O DESCONTO QUE A LOJA ALEGA, guardado PRA SER CONFERIDO —
             # nao pra ser repetido. Com a nossa serie ao lado da alegacao
             # dela, da' pra provar quando o "de/por" e' inflado.
             "desc_loja": _num(p.get("discount")),
             "de_loja": _num(p.get("target_original_price")),
             "loja": p.get("shop_name", ""),
             "quando": quando or f"{date.today():%Y-%m-%d}"}
    if antes is None:
        linha["nome"] = (p.get("product_title") or "")[:90]
        linha["cat"] = p.get("second_level_category_name", "")
    with PRECOS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    if ultimos is not None:
        ultimos[pid] = (preco, vol)
    return True


def nomes() -> dict[int, str]:
    """product_id -> nome, lido da primeira linha de cada serie."""
    n: dict[int, str] = {}
    if not PRECOS.exists():
        return n
    for linha in PRECOS.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if d.get("nome") and d.get("id") and d["id"] not in n:
            n[d["id"]] = d["nome"]
    return n


def ultimo_preco() -> dict[int, tuple[float, int]]:
    """product_id -> (ultimo preco, ultimo volume). O que mudou desde ontem.

    ⚠️ E' o ULTIMO, nao o menor. O `desconto_honesto` usa o MAIOR ja' visto;
    esta funcao responde outra pergunta — "mudou desde a ultima vez?" — e
    confundir as duas faria a serie parar de gravar quedas sucessivas.
    """
    u: dict[int, tuple[float, int]] = {}
    if not PRECOS.exists():
        return u
    for linha in PRECOS.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if d.get("id") and d.get("preco"):
            u[d["id"]] = (float(d["preco"]), int(d.get("vol") or 0))
    return u


_MEMO_HISTORICO: dict = {}


def historico() -> dict[int, list[float]]:
    """product_id -> UM preco por DIA que nos ja' vimos (o menor do dia).

    ## ⛔ POR QUE UM POR DIA, E POR QUE O MENOR

    ⚠️ Antes esta funcao juntava TODOS os precos numa lista so'. Mas o mesmo
    `id` recebe precos de ANUNCIOS DIFERENTES no mesmo dia — variante, kit
    maior, outro vendedor. O "Conjunto de pinceis" tinha quatro leituras em
    14/09: 12,56 · 25,08 · 12,80 · 12,57.

    O 25,08 virava `max(antes)` e `desconto_honesto` anunciava **queda de
    49%** num produto que nao caiu. Medido em 15/09/2026 nos 62 do catalogo:
    8 produtos afetados, e o espalhamento do dia batia quase 1:1 com a queda
    publicada (52%->51,9% · 50%->49,0% · 34%->34,0% · 32%->32,1%).

    ⛔ Dois deles eram os CAMPEOES que abrem a pagina (Carregador 120W e Fone
    Lenovo GM2 Pro). A vitrine anunciava desconto inexistente — o oposto do
    que o modulo inteiro existe pra garantir.

    ⭐ O MENOR do dia, e nao a media: entre duas variantes, a barata e' a
    conservadora, porque puxa a queda pra BAIXO. Errar a favor do desconto e'
    o erro que ninguem reclama e que destroi a credibilidade — e credibilidade
    de preco e' o unico ativo que esta pagina tem.
    """
    # ⚠️ MEMO POR ARQUIVO (18/09/2026). `preco_antes_de` chama isto POR
    # PRODUTO, e a serie tem 37 mil linhas: 0,5 s por chamada, 446 registros
    # do catalogo = 4 minutos so' de reler o mesmo arquivo. Foi o que deixou
    # `teste_vitrine_com_cartaz` "vermelho" desde 16/09 — nao falhava, morria
    # no tempo. A chave e' o mtime, o mesmo desenho de `_preco_hoje_num` na
    # pagina: rodada nova (ou RAIZ trocada no teste) invalida sozinha.
    if not PRECOS.exists():
        return {}
    chave = (str(PRECOS), PRECOS.stat().st_mtime, PRECOS.stat().st_size)
    if _MEMO_HISTORICO.get("chave") == chave:
        return _MEMO_HISTORICO["valor"]
    por_dia: dict[int, dict[str, float]] = {}
    maiores: dict[int, dict[str, float]] = {}
    for linha in PRECOS.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            d = json.loads(linha)
        except ValueError:
            # ⚠️ Linha torta nao derruba a serie inteira. JSONL existe
            # justamente pra isso: o estrago fica na linha.
            continue
        if not (d.get("id") and d.get("preco")):
            continue
        dia = str(d.get("quando") or "")[:10]
        if not dia:
            continue
        try:
            v = float(d["preco"])
        except (TypeError, ValueError):
            continue
        if v <= 0:
            continue
        dias = por_dia.setdefault(d["id"], {})
        dias[dia] = min(dias[dia], v) if dia in dias else v
        altos = maiores.setdefault(d["id"], {})
        altos[dia] = max(altos[dia], v) if dia in altos else v
    # ⭐ O PONTO SOLTO SAI AQUI TAMBEM (21/09/2026). Este historico alimenta
    # `maior_visto`, que e' o "de R$ X" riscado do cartaz do Telegram. Limpar
    # so' na pagina fazia o site dizer "sem queda" e o canal anunciar "de
    # R$ 21,73" do mesmo produto, no mesmo dia -- foi o
    # `teste_vitrine_com_cartaz` que pegou, e e' para isso que ele existe.
    # A regra mora em `engine/serie_limpa.py`: uma so' para os tres caminhos.
    from engine import serie_limpa
    por_dia = {i: serie_limpa.sem_ponto_solto(dd, i, maiores.get(i))
               for i, dd in por_dia.items()}
    valor = {i: [dias[k] for k in sorted(dias)] for i, dias in por_dia.items()}
    _MEMO_HISTORICO.clear()
    _MEMO_HISTORICO.update({"chave": chave, "valor": valor})
    return valor


def maior_visto(p: dict, h: dict[int, list[float]]) -> float:
    """O maior preco que NOS vimos deste produto. 0.0 se nao ha' serie.

    ⭐ EXTRAIDA DE `desconto_honesto` EM 15/09/2026, e pelo mesmo motivo que
    `_precos_por_dia` foi extraida do `_serie_de_precos` no dia anterior: dois
    usos dependem deste numero e NAO podem divergir. A queda publicada sai
    dele, e o "de R$ X" riscado no cartaz do Telegram sai dele.

    ⚠️ A ALTERNATIVA ERA RECONSTRUIR o preco antigo a partir do preco de hoje
    e da queda (`antes = hoje / (1 - queda/100)`). E' algebricamente certo e
    na pratica MENTE: a queda viaja arredondada em 1 casa, e a reconstrucao
    devolveu R$ 16,51 onde o preco visto foi R$ 16,50. Um centavo que nunca
    existiu, impresso numa imagem que nao se recalcula depois de salva.
    """
    antes = h.get(p.get("product_id"), [])
    return max(antes) if antes else 0.0


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
    hoje = _num(p.get("target_sale_price"))
    maior = maior_visto(p, h)
    if not maior or not hoje:
        return 0.0, "sem histórico nosso ainda"
    if hoje >= maior:
        return 0.0, f"não caiu (já vimos por R$ {maior:.2f})"
    queda = (maior - hoje) / maior * 100
    return queda, f"caiu de R$ {maior:.2f} — preço que nós vimos"


def para_produto(p: dict, queda: float, maior: float = 0.0) -> dict:
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
        # ⚠️ O PRECO ANTIGO SO' EXISTE SE A QUEDA EXISTIR, e e' o preco que NOS
        # vimos (`maior_visto`), nunca o `original_price` inflado da loja. Sem
        # queda o campo sai VAZIO — e vazio apaga o selo e o preco riscado no
        # cartaz. Falha fechada: ninguem anuncia desconto sem os dois numeros.
        "preco_antes": (f"R$ {maior:.2f}".replace(".", ",")
                        if queda > 0 and maior > 0 else ""),
        "preco_em": f"{date.today():%Y-%m-%d}",
        "loja": p.get("shop_name", ""),
        "categoria": p.get("second_level_category_name", ""),
        "imagem": p.get("product_main_image_url", ""),
        "video": p.get("product_video_url", ""),
        # ⚠️ O ID VIAJA JUNTO. Sem ele o registro do que foi publicado sai
        # com `id: null` — medido em 14/09/2026: 25 de 25 linhas assim. E o
        # id e' a unica chave que liga o produto publicado a` serie de preco
        # e ao pedido; sem ele nao da' pra perguntar "o que a gente publicou
        # vendeu?".
        "_id": p.get("product_id"),
        # medidas que NAO vao pro post, mas explicam a escolha
        "_vendas": int(_num(p.get("lastest_volume"))),
        "_nota": _num(p.get("evaluate_rate")),
        "_comissao": _num(p.get("commission_rate")),
        "_queda": round(queda, 1),
    }


def ganho_por_venda(preco: float, comissao_pct: float) -> float:
    """Quanto entra no nosso bolso por unidade vendida.

    ⚠️ ESTE NUMERO NAO EXISTIA NO MOTOR ATE' 13/09/2026, e e' o que o Bryan
    pediu: "temos que lucrar muito". O garimpo ordenava por QUEDA e por
    VOLUME — nunca por dinheiro.

    ⭐ A conta que faltava: pincel a R$ 12,71 com 7% da' R$ 0,89 por venda;
    Cicaplast a R$ 38,66 com 16% da' R$ 6,19. SETE VEZES pelo mesmo esforco de
    video.
    """
    return round(preco * comissao_pct / 100, 2)


def potencial(p: dict) -> dict:
    """Acrescenta a conta de dinheiro a um produto ja' montado.

    ⚠️ `_potencial` E' ORDEM DE GRANDEZA, NAO PREVISAO. Ele multiplica o ganho
    pelo volume HISTORICO do produto — que e' o que o mercado inteiro comprou,
    nao o que NOS vamos vender. Serve pra comparar dois produtos entre si;
    nao serve pra prometer faturamento.
    """
    preco = _num(str(p.get("preco", "")).replace("R$", "").replace(",", "."))
    com = float(p.get("_comissao") or 0)
    g = ganho_por_venda(preco, com)
    return dict(p, _ganho=g, _potencial=round(g * int(p.get("_vendas") or 0)))


def garimpar(canal: str, quantos: int = 8,
             guardar: bool = True) -> tuple[list[dict], dict[str, int]]:
    """O garimpo de um canal. Devolve (escolhidos, por que os outros cairam)."""
    crus = buscar(canal)
    # ⚠️ LE' O ULTIMO PRECO UMA VEZ SO'. Ler por produto reabriria o arquivo
    # centenas de vezes por rodada.
    ultimos = ultimo_preco() if guardar else None
    motivos: dict[str, int] = {}
    passaram = []
    for p in crus:
        # ⚠️ GUARDA O PRECO DE TODOS, inclusive dos recusados. O historico e'
        # sobre o PRODUTO, nao sobre a nossa decisao de hoje — e um item que
        # nao serve hoje pode servir quando o preco cair.
        if guardar:
            guardar_preco(p, ultimos=ultimos)
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
        saida.append(para_produto(p, queda, maior_visto(p, h)))

    saida = [potencial(x) for x in saida]
    # ⭐ ORDEM: DINHEIRO PRIMEIRO. Decisao do Bryan em 14/09/2026.
    #
    # ⚠️ E 'dinheiro' aqui NAO e' o preco, nem o ganho por unidade: e' o
    # `_potencial` — ganho por venda VEZES o volume que o produto ja' tem na
    # loja. Ordenar so' por ganho empurraria pro item caro, que rende mais
    # por unidade e vende menos; ordenar so' por volume traz o campeao que
    # paga R$ 0,89. O produto cruza os dois.
    #
    # ⭐ A CONTA QUE ISSO RESOLVE: pincel a R$ 12,71 com 7% da' R$ 0,89 por
    # venda; Cicaplast a R$ 38,66 com 16% da' R$ 6,19. SETE VEZES pelo mesmo
    # video — e ate' hoje a ordem punha os dois no mesmo balaio.
    #
    # ⚠️ O QUE ESTA ORDEM AINDA NAO SABE: conversao. `_potencial` usa o
    # volume do MERCADO, nao o nosso. O dia em que `engine/resultado.py`
    # tiver venda por canal, esta linha deixa de ser escolha e vira pergunta
    # respondida — e a queda volta a ser desempate, nao palpite.
    saida.sort(key=lambda x: (x["_potencial"], x["_queda"], x["_ganho"]),
               reverse=True)
    escolhidos = saida[:quantos]
    # ⚠️ ANOTA O QUE FOI ESCOLHIDO, e nao o que foi visto. Sem este registro a
    # serie de preco e os cliques do Supabase nunca se encontram — foi o
    # buraco que ficou aberto ate' 13/09/2026.
    if guardar:
        from . import resultado
        for x in escolhidos:
            resultado.anotar_publicado(x, canal, "garimpo")
    return escolhidos, motivos


def termos_ml_de_hoje(canal: str, por_dia: int = 3) -> list[str]:
    """Os termos do canal que o ML busca HOJE — rodizio pelo dia do ano.

    ⚠️ 3 por dia e nao os 20: cada busca dirigida custa 15-30 s e o ML
    limita por aplicacao (429 medido em 16/09). Em uma semana o canal
    inteiro passa; o AliExpress continua com os 20 de uma vez porque la' a
    busca e' uma chamada por termo.
    """
    termos = CANAIS.get(canal, {}).get("termos") or []
    if not termos:
        return []
    i = (date.today().timetuple().tm_yday * por_dia) % len(termos)
    return [termos[(i + k) % len(termos)] for k in range(min(por_dia, len(termos)))]


def garimpar_ml(canal: str, quantos: int = 4, guardar: bool = True) -> list[dict]:
    """O garimpo diario do ML: busca dirigida, registro e PRIMEIRO PONTO da serie.

    ⭐ O ponto da serie vai junto com o registro, e nao so' na proxima hora
    cheia: a pagina so' publica produto com leitura nas ultimas 24h — sem
    isto o produto entraria no catalogo e ficaria invisivel ate' o
    `precos.py` passar.
    """
    escolhidos = do_mercado_livre(canal, quantos, termos_ml_de_hoje(canal))
    print(f"ML {canal}: {len(escolhidos)} escolhido(s) de {termos_ml_de_hoje(canal)}")
    for x in escolhidos:
        print(f"   R$ {x['preco_num']:>8.2f}  {x['_comissao']:>4.0f}%  "
              f"{x['vendedores']:>2} vend  {x['nome'][:50]}")
    if guardar and escolhidos:
        from . import precos, resultado
        for x in escolhidos:
            resultado.anotar_publicado(x, canal, "garimpo-ml")
        # ⭐ (preco, vendedores): o numero de vendedores e' o `vol` do ML
        n = precos.anotar_serie({x["_id"]: (x["preco_num"], int(x.get("vendedores") or 0))
                                 for x in escolhidos}, "Mercado Livre")
        print(f"   registrados {len(escolhidos)}; serie +{n}")
    return escolhidos


# ⚠️ A VARREDURA EXISTE SO' PRA ALIMENTAR O HISTORICO DE PRECO. Nenhum destes
# termos vira post: sao categorias largas, escolhidas pra cobrir o que o
# publico brasileiro compra, e nao pra render video.
#
# ⭐ POR QUE VALE A PENA: historico de preco NAO SE COLETA DEPOIS. Cada dia
# que a gente nao guarda e' um dia perdido pra sempre. Um produto que hoje nao
# serve a nenhum canal pode servir em novembro — e ai' a serie dele ja' vai
# existir, em vez de comecar do zero.
#
# ⚠️ E FICOU BARATO SO' DEPOIS do `guardar_preco` passar a gravar apenas
# mudanca: varrer 300 produtos por dia gerando 300 linhas por dia era inchar
# o repositorio (o arquivo e' COMMITADO toda rodada). Gravando so' os pontos
# de mudanca, a varredura custa quase nada.
VARREDURA = [
    "cozinha utensilio", "organizador casa", "banheiro acessorio",
    "ferramenta manual", "pet acessorio", "bebe acessorio",
    "carro acessorio", "jardim ferramenta", "escritorio papelaria",
    "maquiagem kit", "cabelo acessorio", "unha decoracao",
    "academia acessorio", "camping acessorio", "bicicleta acessorio",
    "cabo usb", "suporte notebook", "teclado mouse",
    "decoracao parede", "iluminacao led", "cama mesa banho",
]


def varrer(por_termo: int = 20) -> tuple[int, int]:
    """Passa pelos termos largos so' pra guardar preco. (vistos, gravados).

    ⚠️ NAO FILTRA E NAO PUBLICA NADA. Se um dia isto comecar a devolver
    produto pro post, e' porque alguem confundiu as duas coisas — a varredura
    e' memoria, o garimpo e' curadoria.
    """
    ultimos = ultimo_preco()
    vistos = gravados = 0
    for termo in VARREDURA:
        try:
            r = aliexpress.chamar(
                "aliexpress.affiliate.product.query", keywords=termo,
                page_size=str(por_termo), target_currency="BRL",
                target_language="PT", ship_to_country="BR",
                # memoria de preco, nao vira link publicado: fica no padrao
                tracking_id="default", sort="LAST_VOLUME_DESC")
            res = r.get("aliexpress_affiliate_product_query_response", {}) \
                   .get("resp_result", {})
            if str(res.get("resp_code")) != "200":
                print(f"  [!] varredura {termo!r}: {res.get('resp_msg')}")
                continue
            for p in (res.get("result", {}).get("products", {})
                         .get("product", []) or []):
                vistos += 1
                if guardar_preco(p, ultimos=ultimos):
                    gravados += 1
        except Exception as e:
            # ⚠️ FALHA ABERTA: a varredura e' bonus. Derrubar a rodada do
            # garimpo por causa dela seria perder o que importa pelo que sobra.
            print(f"  [!] varredura {termo!r} estourou: {type(e).__name__}")
    return vistos, gravados


# ⚠️ A VIGIA E' OUTRA COISA DA VARREDURA, e confundir as duas esvazia as duas.
#
#   varredura  larga e anonima — guarda preco de MUITO produto, pra ter serie
#   vigia      curta e nominal — acompanha PRODUTOS ESPECIFICOS todo dia
#
# ⭐ PEDIDO DO BRYAN EM 13/09/2026: "uma lista extremamente seleta pra
# acompanharmos". O caso que ele deu foi PS5 — que NAO e' de nenhum canal
# nosso, e e' justamente esse o ponto: o `/trends/MLB` do Mercado Livre
# mostrou "controle ps5" entre o que o Brasil procura HOJE. Demanda existe
# fora dos nossos nichos, e acompanhar preco dela custa quase nada.
#
# ⚠️ SELETA QUER DIZER CURTA. Se esta lista crescer pra cinquenta itens ela
# vira varredura com outro nome, e perde o sentido: o valor dela e' poder
# olhar a serie de CADA UM e entender a historia.
VIGIA = [
    "controle ps5",
    "controle xbox",
    "fone bluetooth tws",
    "smartwatch amoled",
    "power bank 20000mah",
    "aspirador portatil",
    "air fryer acessorio",
    "projetor portatil",
    "webcam full hd",
    "ssd nvme",
]


def vigiar(por_termo: int = 8) -> list[dict]:
    """Acompanha os itens da VIGIA e devolve o que MUDOU de preco.

    ⚠️ Devolve so' as mudancas, nao a lista inteira. Uma vigia que imprime
    tudo todo dia vira ruido, e ruido diario ninguem le'.
    """
    ultimos = ultimo_preco()
    mudancas = []
    for termo in VIGIA:
        try:
            r = aliexpress.chamar(
                "aliexpress.affiliate.product.query", keywords=termo,
                page_size=str(por_termo), target_currency="BRL",
                target_language="PT", ship_to_country="BR",
                # memoria de preco, nao vira link publicado: fica no padrao
                tracking_id="default", sort="LAST_VOLUME_DESC")
            res = r.get("aliexpress_affiliate_product_query_response", {}) \
                   .get("resp_result", {})
            if str(res.get("resp_code")) != "200":
                continue
            for p in (res.get("result", {}).get("products", {})
                         .get("product", []) or []):
                antes = ultimos.get(p.get("product_id"))
                if guardar_preco(p, ultimos=ultimos) and antes is not None:
                    antes = antes[0]
                    agora = _num(p.get("target_sale_price"))
                    mudancas.append({
                        "termo": termo,
                        "nome": (p.get("product_title") or "")[:70],
                        "de": antes, "para": agora,
                        "var": round((agora - antes) / antes * 100, 1),
                    })
        except Exception as e:
            print(f"  [!] vigia {termo!r}: {type(e).__name__}")
    # maior QUEDA primeiro — subida tambem importa, mas nao e' pauta
    mudancas.sort(key=lambda m: m["var"])
    return mudancas


# ⚠️ QUANTAS VENDAS PRA ENTRAR NA LISTA DE CAMPEOES. 5 mil e' arbitrario hoje;
# vira medido quando houver venda nossa pra comparar.
CAMPEAO_VOLUME_MIN = 5000
CAMPEOES_MAX = 60


def campeoes(quantos: int = CAMPEOES_MAX) -> list[dict]:
    """Os produtos que mais vendem DENTRE os que ja' vimos. Sai dos dados.

    ⭐ A LISTA NAO E' CHUTADA, E' DERIVADA. Eu escolheria por intuicao e
    erraria — a varredura ja' passou por milhares de produtos e sabe quais
    vendem. Pedir a ela e' melhor do que eu adivinhar.

    ⚠️ E E' POR PRODUTO, NAO POR PALAVRA. Medido em 13/09/2026: o
    `productdetail.get` aceita varios ids de uma vez e devolve volume. Por
    palavra, o "mais vendido de hoje" pode ser outro item amanha e a serie
    troca de dono sem ninguem notar.
    """
    nom = nomes()
    melhor: dict[int, dict] = {}
    for d in _linhas():
        pid, vol = d.get("id"), int(d.get("vol") or 0)
        if not pid or vol < CAMPEAO_VOLUME_MIN:
            continue
        # o ponto mais recente manda: volume so' cresce, e o ultimo e' o maior
        if pid not in melhor or vol >= melhor[pid]["vol"]:
            melhor[pid] = {"id": pid, "vol": vol, "preco": d.get("preco"),
                           "nome": nom.get(pid, ""), "quando": d.get("quando")}
    ordenado = sorted(melhor.values(), key=lambda x: -x["vol"])
    return ordenado[:quantos]


def acompanhar_campeoes(por_vez: int = 20) -> int:
    """Le' os campeoes pelo ID e grava o ponto novo. Devolve quantos mudaram.

    ⚠️ EM LOTES de `por_vez`: o `productdetail.get` aceita varios ids de uma
    vez, e pedir um por um gastaria 60 chamadas onde 3 bastam.
    """
    alvos = campeoes()
    if not alvos:
        return 0
    ultimos = ultimo_preco()
    mudaram = 0
    for i in range(0, len(alvos), por_vez):
        lote = alvos[i:i + por_vez]
        ids = ",".join(str(x["id"]) for x in lote)
        try:
            r = aliexpress.chamar(
                "aliexpress.affiliate.productdetail.get", product_ids=ids,
                target_currency="BRL", target_language="PT",
                ship_to_country="BR", tracking_id="default")
            corpo = (r.get("aliexpress_affiliate_productdetail_get_response")
                     or {}).get("resp_result", {})
            if str(corpo.get("resp_code")) != "200":
                print(f"  [!] campeoes lote {i//por_vez+1}: "
                      f"{corpo.get('resp_code')} {corpo.get('resp_msg')}")
                continue
            for p in (corpo.get("result", {}).get("products", {})
                         .get("product", []) or []):
                if guardar_preco(p, ultimos=ultimos):
                    mudaram += 1
        except Exception as e:
            # ⚠️ falha aberta: perder um lote nao pode derrubar a rodada
            print(f"  [!] campeoes lote {i//por_vez+1}: {type(e).__name__}")
    return mudaram


def _linhas() -> list[dict]:
    if not PRECOS.exists():
        return []
    saida = []
    for linha in PRECOS.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            saida.append(json.loads(linha))
        except ValueError:
            continue
    return saida


# ⚠️ PISO DE VOLUME PRA ESCALADA. Sem ele, um produto que foi de 10 pra 30
# vendas ganha da lista inteira com +200% — e nao significa nada. O piso
# separa aceleracao de ruido.
ESCALADA_VOLUME_MIN = 300


def escalada(quantos: int = 20) -> list[dict]:
    """Os produtos cujo volume esta' ACELERANDO. Tendencia, nao nivel.

    ⭐ VOLUME ALTO E' PASSADO; VOLUME ACELERANDO E' FUTURO. O campeao com 26
    mil vendas pode estar saturado. O que foi de 800 pra 2000 numa semana e' o
    que esta' decolando — e e' esse que vira video antes de todo mundo.

    ⚠️ E' O MESMO PRINCIPIO DE NIVEL x MOMENTUM dos mentores de trading do
    acervo. Ninguem opera olhando so' o preco absoluto; olha-se a variacao. O
    `campeoes()` responde "quem vende muito"; esta funcao responde "quem esta'
    vendendo cada vez mais", e as duas listas PODEM NAO SE CRUZAR.

    ⚠️ PRECISA DE PELO MENOS DOIS PONTOS por produto — entao ela nasce vazia e
    so' ganha sentido depois de alguns dias de coleta. Isso nao e' defeito: e'
    o custo de medir tendencia, que nao se inventa no primeiro dia.
    """
    from datetime import datetime as _dt
    nom = nomes()
    serie: dict[int, list[tuple[str, int, float]]] = {}
    for d in _linhas():
        pid, vol = d.get("id"), int(d.get("vol") or 0)
        if pid and vol:
            serie.setdefault(pid, []).append(
                (d.get("quando", ""), vol, float(d.get("preco") or 0)))

    saida = []
    for pid, pontos in serie.items():
        if len(pontos) < 2:
            continue
        pontos.sort()
        (d0, v0, _), (d1, v1, p1) = pontos[0], pontos[-1]
        if v1 < ESCALADA_VOLUME_MIN or v0 <= 0 or v1 <= v0:
            continue
        try:
            dias = max(1, (_dt.fromisoformat(d1) - _dt.fromisoformat(d0)).days)
        except ValueError:
            dias = 1
        saida.append({
            "id": pid, "nome": nom.get(pid, ""),
            "de": v0, "para": v1, "dias": dias,
            "por_dia": round((v1 - v0) / dias),
            # ⭐ o percentual AO DIA e' o que compara produto grande com
            # pequeno; o absoluto sozinho so' devolve os gigantes de novo.
            "pct_dia": round((v1 - v0) / v0 * 100 / dias, 1),
            "preco": p1,
        })
    saida.sort(key=lambda x: -x["pct_dia"])
    return saida[:quantos]


def novos_no_topo(quantos: int = 15) -> list[dict]:
    """Produtos que APARECERAM no historico ja' vendendo muito.

    ⚠️ Complementa a escalada e nao se confunde com ela: a escalada precisa de
    dois pontos; este pega o item que entrou HOJE ja' grande — e um produto
    que surge do nada com 5 mil vendas e' tendencia tambem, so' que a gente
    nao viu a subida.
    """
    nom = nomes()
    primeiro: dict[int, dict] = {}
    for d in _linhas():
        pid = d.get("id")
        if pid and pid not in primeiro:
            primeiro[pid] = d
    de_hoje = [d for d in primeiro.values()
               if d.get("quando", "").startswith(f"{date.today():%Y-%m-%d}")
               and int(d.get("vol") or 0) >= CAMPEAO_VOLUME_MIN]
    de_hoje.sort(key=lambda d: -int(d.get("vol") or 0))
    return [{"id": d["id"], "nome": nom.get(d["id"], ""),
             "vol": int(d.get("vol") or 0), "preco": d.get("preco")}
            for d in de_hoje[:quantos]]


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="o garimpo")
    a.add_argument("--canal", choices=sorted(CANAIS))
    a.add_argument("--quantos", type=int, default=5)
    a.add_argument("--ensaio", action="store_true",
                   help="nao grava o historico de preco")
    a.add_argument("--varrer", action="store_true",
                   help="so' alimenta o historico, nao publica")
    a.add_argument("--vigiar", action="store_true",
                   help="acompanha a lista VIGIA e mostra o que mudou")
    a.add_argument("--campeoes", action="store_true",
                   help="acompanha, pelo ID, os que mais vendem")
    a.add_argument("--ml", action="store_true",
                   help="garimpo do Mercado Livre pro --canal (busca dirigida, "
                        "3 termos por dia em rodizio)")
    a.add_argument("--tendencia", action="store_true",
                   help="quem esta' ACELERANDO, e quem apareceu ja' grande")
    o = a.parse_args()
    if o.ml:
        if not o.canal:
            raise SystemExit("--ml precisa de --canal")
        garimpar_ml(o.canal, o.quantos, guardar=not o.ensaio)
        return
    if o.tendencia:
        esc = escalada()
        print(f"ESCALADA — {len(esc)} produto(s) acelerando:")
        for x in esc[:12]:
            print(f"  +{x['pct_dia']:>5.1f}%/dia  {x['de']} -> {x['para']} "
                  f"em {x['dias']}d  R$ {x['preco']:.2f}  {x['nome'][:40]}")
        if not esc:
            print("  (vazio: precisa de 2+ pontos por produto, e a coleta"
                  " de volume comecou em 13/09)")
        nov = novos_no_topo()
        print("")
        print(f"APARECERAM HOJE JA' GRANDES — {len(nov)}:")
        for x in nov[:10]:
            print(f"  {x['vol']:>7} vendas  R$ {x['preco']:>7.2f}  "
                  f"{x['nome'][:45]}")
        return
    if o.campeoes:
        alvos = campeoes()
        print(f"{len(alvos)} campeao(oes) acompanhados (>= "
              f"{CAMPEAO_VOLUME_MIN} vendas):")
        for x in alvos[:12]:
            print(f"  {x['vol']:>7} vendas  R$ {x['preco']:>7.2f}  "
                  f"{x['nome'][:52]}")
        print("")
        print(str(acompanhar_campeoes()) + " ponto(s) novo(s)")
        return
    if o.vigiar:
        for m in vigiar():
            seta = "caiu" if m["var"] < 0 else "subiu"
            print(f"  {seta} {abs(m['var']):5.1f}%  "
                  f"R$ {m['de']:.2f} -> R$ {m['para']:.2f}  {m['nome']}")
        return
    if o.varrer:
        v, g = varrer()
        print(f"varredura: {v} produtos vistos, {g} precos novos")
        return
    achados, motivos = garimpar(o.canal, o.quantos, guardar=not o.ensaio)
    print(f"\nrecusados: " + ", ".join(f"{k} x{v}" for k, v in
                                       sorted(motivos.items(), key=lambda i: -i[1])))
    print(f"\n{len(achados)} escolhido(s) para {o.canal}:\n")
    for x in achados:
        print(f"  {x['nome'][:64]}")
        print(f"    {x['preco']} · {x['loja']} · {x['_vendas']} vendidos · "
              f"nota {x['_nota']:.0f}% · comissao {x['_comissao']:.1f}%"
              + (f" · CAIU {x['_queda']:.0f}%" if x["_queda"] else ""))
        # ⭐ O DINHEIRO SAI NA MESMA LINHA DE LEITURA. Numero que nao aparece
        # nao e' considerado — e este e' o que o Bryan pediu pra nao perder
        # de vista.
        print(f"    ganho por venda: R$ {x.get('_ganho', 0):.2f}"
              f"  ·  potencial (ganho x volume): R$ {x.get('_potencial', 0):,}"
              .replace(",", "."))


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

def do_mercado_livre(canal: str, quantos: int = 5,
                     termos: list[str] | None = None) -> list[dict]:
    """Produtos do ML deste canal, pela BUSCA DIRIGIDA com os termos do canal.

    ⛔ NAO E' MAIS `mais_vendidos`: os mais vendidos do ML sao papel higienico
    e Elseve (medido 15/09). Desde 16/09/2026 a fonte e' `mercadolivre.buscar`
    com os MESMOS termos que o garimpo do AliExpress ja' usa por canal —
    produto real (2+ vendedores), menor anuncio, sem peca nem livro.

    ⚠️ REUSA O `serve()`? NAO — e de proposito. O ML nao devolve nota nem
    volume no formato do AliExpress. O corte comum e' a FAIXA DE PRECO do
    canal; o resto e' proprio de cada fonte.

    ⚠️ Custa ~15-30 s por termo (a busca pagina e expande por marca). Por
    isso `termos` e' um recorte: o garimpo diario passa uns 3 por canal, e
    o pedido sob demanda passa o termo pedido.
    """
    from . import mercadolivre as ml
    perfil = CANAIS.get(canal)
    if not perfil:
        return []
    saida, vistos = [], set()
    for termo in (termos or perfil["termos"][:3]):
        try:
            achados = ml.buscar(termo, quantos=6, canal=canal)
        except Exception as e:                       # noqa: BLE001
            print(f"  [!] ML {termo!r}: {type(e).__name__} {str(e)[:60]}")
            continue
        for p in achados:
            if p["_id"] in vistos:
                continue
            preco = p["preco_num"]
            if not (perfil["min"] <= preco <= perfil["max"]):
                continue
            vistos.add(p["_id"])
            com = float(p.get("comissao") or 0)
            saida.append(dict(p, fonte="mercadolivre",
                              preco_em=f"{date.today():%Y-%m-%d}",
                              categoria=termo, _vendas=p["vendedores"], _nota=0.0,
                              _comissao=com, _queda=0.0,
                              _ganho=round(preco * com / 100, 2)))
    saida = ml.so_monetizados(saida)
    # ⭐ O CORTE EDITORIAL VEM AQUI, sobre a lista INTEIRA e de uma vez so'.
    fica, cai = rende_video.peneirar_com_ia(saida)
    for nome, porque in cai:
        print(f"  [editorial] fora: {nome[:40]}… — {porque}")
    # ⭐ INTERCALA POR TERMO: sem isto os 4 do dia sairiam todos do primeiro
    # termo (medido 16/09: quatro peneiras). Um de cada, depois o segundo de
    # cada — a leva do dia tem variedade e cada termo ainda entra pelo mais
    # barato.
    por_termo: dict[str, list[dict]] = {}
    for x in fica:
        por_termo.setdefault(x["categoria"], []).append(x)
    rodizio: list[dict] = []
    while len(rodizio) < quantos and any(por_termo.values()):
        for fila in por_termo.values():
            if fila and len(rodizio) < quantos:
                rodizio.append(fila.pop(0))
    return rodizio
