# -*- coding: utf-8 -*-
"""Mercado Livre: radar de pauta, mais vendidos e link de afiliado.

## O QUE ELE E', E O QUE ELE NAO E'

⭐ O ML **nao e' fonte de achadinho** — os mais vendidos dele sao papel
higienico, sabao em po e lencol: a cesta de compras do pais. O que ele da' de
unico e' (1) o que o Brasil esta' procurando HOJE e (2) comissao de ate' 16%
com entrega em dois dias, contra 7% e tres semanas do AliExpress.

## ⚠️ O `/sites/MLB/search` ESTA' FECHADO (403) — e nao adianta insistir

Medido em 13/09/2026 com token valido. O que responde e' outra coisa, e por
sorte e' melhor pro nosso caso:

    /trends/MLB                       o que se procura agora
    /highlights/MLB/category/{id}     os mais vendidos da categoria
    /products/{id}                    ficha do produto
    /products/search                  catalogo

## O LINK DE AFILIADO — MEDIDO, NAO SUPOSTO

⭐ Basta pendurar `matt_word` e `matt_tool` na URL do produto. Nao e' preciso
o gerador deles nem o parametro `ref`.

⚠️ E ISTO FOI PROVADO, nao deduzido: em 13/09/2026 o Bryan abriu um link
montado assim e o proprio Mercado Livre mostrou a barra de afiliado com
"GANHOS 16%". Barra de afiliado so' aparece quando o contexto e' reconhecido.
Era o modo de falha mais caro possivel — link que abre a pagina e nao atribui
nada — e por isso nao entrou no motor antes de ter prova.

## ⚠️ O COOKIE E' DE 24 HORAS

Curto pro funil `video -> perfil -> bio -> loja`: a venda de sabado sobre um
clipe de quinta NAO e' nossa. Isso nao se conserta no codigo; se conserta na
chamada do clipe, que precisa gerar clique no mesmo dia.
"""
from __future__ import annotations

import os
import time
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import requests
from dotenv import load_dotenv

load_dotenv()

API = "https://api.mercadolibre.com"
TIMEOUT_S = 25

# Categoria do ML -> canal nosso. So' as que rendem conteudo.
#
# ⚠️ NEM TODA CATEGORIA VIRA CANAL. "Alimentos e Bebidas" vende muito e nao
# rende clipe nenhum: ninguem assiste a um video sobre sabao em po. A escolha
# aqui e' editorial, e por isso e' curta.
CATEGORIAS = {
    "truque.importado":        [("MLB1246", "Beleza e Cuidado Pessoal")],
    "cozinha.importada":       [("MLB1574", "Casa, Móveis e Decoração")],
    "achadinhos.instantaneos": [("MLB1574", "Casa, Móveis e Decoração"),
                                ("MLB1051", "Celulares e Telefones")],
    "fatura.chora":            [("MLB1000", "Eletrônicos e Áudio"),
                                ("MLB1648", "Informática")],
    "atefalhar":               [("MLB1276", "Esportes e Fitness")],
}

# ⛔ SUBCATEGORIAS QUE NUNCA ENTRAM — a causa do papel higienico.
#
# ⚠️ MEDIDO em 15/09/2026: puxar `MLB1246` (Beleza e Cuidado Pessoal) devolveu
# "Papel Higienico Folha Tripla" e "Papel Higienico Toque da Seda" nos dois
# primeiros lugares. Nao e' defeito do ML — e' que a categoria MAE tem 13
# filhas, e `Higiene Pessoal` e `Farmacia` estao entre elas.
#
# ⭐ E o motivo de vetar e' o mesmo que ja' esta' escrito no topo deste modulo:
# no ML, muito vendido significa COMMODITY. Ninguem assiste a um clipe sobre
# papel higienico, por mais que ele venda.
FORA = {
    "MLB198312",   # Higiene Pessoal  <- o papel higienico mora aqui
    "MLB431646",   # Farmacia
    "MLB264751",   # Artigos para Cabeleireiros (profissional, nao achadinho)
    "MLB264787",   # Barbearia (idem)
}

# Onde a comissao vista no hub fica anotada.
#
# ⚠️ ELA NAO VEM DA API. Medido em 15/09/2026: a ficha do produto nao tem
# nenhum campo de comissao, e `/affiliate-program/commissions`,
# `/affiliates/items`, `/users/me/affiliate` e `/marketplace/affiliate/items`
# respondem 404. Os "GANHOS EXTRAS 26%" existem SO' na tela do hub.
#
# ⭐ Por isso a comissao e' ANOTADA A MAO, com a data em que foi vista — e
# vale por prazo, igual ao preco. A pagina nunca afirma "este produto paga
# 26%"; afirma "em 15/09 pagava 26%, conferido por nos". E' a mesma trava de
# honestidade do preco reconferido em 48h, e pela mesma razao: o que envelhece
# SAI SOZINHO, sem ninguem precisar decidir.
VALIDADE_COMISSAO_DIAS = 14
# ⛔ DOMINIOS QUE A BUSCA POR TEXTO TRAZ E NAO SAO O PRODUTO: "air fryer"
# devolve o livro de receitas na frente da fritadeira (medido 16/09/2026).
FORA_DOMINIOS = {"MLB-BOOKS", "MLB-EBOOKS", "MLB-MAGAZINES"}

_cache: dict[str, tuple[str, float]] = {}

# ⭐ COMISSAO-BASE DO PROGRAMA, por CATEGORIA-RAIZ (afiliado generalista).
#
# Decisao do Bryan em 16/09/2026: "vamos por a base de comissao que o site ja'
# nos oferece" — em vez de exigir anotacao a mao (regra de 15/09) pra cada
# produto. A anotacao do hub continua valendo como "ganhos extras", por cima.
#
# ⚠️ FONTE: documentacao de afiliados reproduzida em Hostinger (18/12/2025) e
# Serasa; a tabela oficial fica no hub, atras de login (403 daqui). BATE COM A
# MEDICAO: o "GANHOS 16%" visto na tela em 13/09 era um produto de Beleza.
# `direta` = a pessoa comprou O produto divulgado; `indireta` = comprou outra
# coisa dentro do cookie. O ganho previsto usa a DIRETA.
#
# ⚠️ Raiz que nao esta' aqui recebe 0 — nao um chute. E' o lado que nao mente.
COMISSAO_BASE = {   # id da raiz: (direta, indireta)
    "MLB1246": (16.0, 8.0),   # Beleza e Cuidado Pessoal
    "MLB1430": (16.0, 8.0),   # Calçados, Roupas e Bolsas
    "MLB1276": (16.0, 8.0),   # Esportes e Fitness
    "MLB1574": (8.0, 4.0),    # Casa, Móveis e Decoração
    "MLB263532": (8.0, 4.0),  # Ferramentas
    "MLB1132": (8.0, 4.0),    # Brinquedos e Hobbies
    "MLB1384": (8.0, 4.0),    # Bebês
    "MLB3937": (8.0, 4.0),    # Joias e Relógios
    "MLB3025": (8.0, 4.0),    # Livros, Revistas e Comics
    "MLB1144": (8.0, 4.0),    # Games
    "MLB5672": (8.0, 4.0),    # Acessórios para Veículos
    "MLB1500": (8.0, 4.0),    # Construção
    "MLB1000": (4.0, 2.0),    # Eletrônicos, Áudio e Vídeo
    "MLB1051": (4.0, 2.0),    # Celulares e Telefones
    "MLB1648": (4.0, 2.0),    # Informática
    "MLB5726": (4.0, 2.0),    # Eletrodomésticos
    "MLB1039": (4.0, 2.0),    # Câmeras e Acessórios
    "MLB1403": (0.0, 0.0),    # Alimentos e Bebidas
}

_raizes: dict[str, str] | None = None


def _arquivo_raizes():
    from pathlib import Path as _P
    return _P(__file__).resolve().parent.parent / "estado" / "ml_raizes.json"


def raiz_da_categoria(category_id: str) -> str:
    """Id da categoria-raiz de `category_id` (ex.: MLB73055 -> MLB5726).

    ⚠️ Com cache em disco: sao ~30 mil categorias e a raiz nunca muda; sem
    cache cada produto custaria uma chamada a mais pra sempre.
    """
    global _raizes
    import json as _j
    if _raizes is None:
        arq = _arquivo_raizes()
        try:
            _raizes = _j.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
        except ValueError:
            _raizes = {}
    if not category_id:
        return ""
    if category_id in _raizes:
        return _raizes[category_id]
    try:
        caminho = _get(f"/categories/{category_id}").get("path_from_root") or []
    except requests.HTTPError:
        return ""
    raiz = caminho[0]["id"] if caminho else ""
    if raiz:
        _raizes[category_id] = raiz
        arq = _arquivo_raizes()
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(_j.dumps(_raizes, ensure_ascii=False, indent=0), encoding="utf-8")
    return raiz


def comissao_base(category_id: str) -> float:
    """A comissao DIRETA da raiz desta categoria, em %. 0 se desconhecida."""
    return COMISSAO_BASE.get(raiz_da_categoria(category_id), (0.0, 0.0))[0]


def _arquivo_comissao():
    from pathlib import Path as _P
    return _P(__file__).resolve().parent.parent / "estado" / "comissao_ml.json"


def comissoes() -> dict:
    """{id_do_produto: {"pct": 26.0, "visto": "2026-09-15"}}"""
    import json
    arq = _arquivo_comissao()
    if not arq.exists():
        return {}
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def anotar_comissao(id_produto: str, pct: float, quando: str = "") -> None:
    """Grava o que foi VISTO no hub. `quando` vazio = hoje."""
    import json
    from datetime import date
    d = comissoes()
    d[str(id_produto)] = {"pct": float(pct), "visto": quando or date.today().isoformat()}
    arq = _arquivo_comissao()
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def comissao_valida(id_produto: str) -> dict | None:
    """Devolve a comissao se ela ainda esta' dentro do prazo, senao None.

    ⛔ Fora do prazo NAO e' "provavelmente ainda vale": e' desconhecido. O
    produto sai do catalogo por isso — melhor sumir do que afirmar um numero
    que ninguem conferiu.
    """
    from datetime import date, timedelta
    reg = comissoes().get(str(id_produto))
    if not reg:
        return None
    limite = (date.today() - timedelta(days=VALIDADE_COMISSAO_DIAS)).isoformat()
    return reg if str(reg.get("visto", "")) >= limite else None


def subcategorias_uteis(mae: str) -> list[tuple[str, str]]:
    """Filhas da categoria, menos as vetadas em `FORA`.

    ⚠️ Se a categoria nao tiver filhas, devolve ela mesma — assim quem chama
    nao precisa saber se desceu ou nao.
    """
    try:
        d = _get(f"/categories/{mae}")
    except Exception:
        return [(mae, mae)]
    filhas = d.get("children_categories") or []
    if not filhas:
        return [(mae, d.get("name", mae))]
    return [(c["id"], c["name"]) for c in filhas if c["id"] not in FORA]


def token() -> str:
    """Token de aplicacao (client_credentials), com cache.

    ⚠️ VALE 6 HORAS e o cache existe pra nao pedir um por chamada: o ML conta
    pedido de token no rate limit, e queimar cota pedindo credencial seria
    perder chamada que deveria ser de produto.
    """
    agora = time.time()
    if "t" in _cache and _cache["t"][1] > agora + 60:
        return _cache["t"][0]
    cid = os.getenv("MELI_CLIENT_ID")
    sec = os.getenv("MELI_CLIENT_SECRET")
    if not (cid and sec):
        raise RuntimeError("faltam MELI_CLIENT_ID / MELI_CLIENT_SECRET no .env")
    r = requests.post(f"{API}/oauth/token", timeout=TIMEOUT_S,
                      data={"grant_type": "client_credentials",
                            "client_id": cid, "client_secret": sec})
    r.raise_for_status()
    d = r.json()
    _cache["t"] = (d["access_token"], agora + int(d.get("expires_in", 21600)))
    return _cache["t"][0]


def _get(caminho: str, tentativas: int = 4, **params) -> dict | list:
    """GET com espera no 429.

    ⚠️ O ML LIMITA POR APLICACAO, e a busca dirigida dispara 6 chamadas em
    paralelo: em 16/09/2026 a quarta medicao seguida tomou 429 no proprio
    `/products/search`. 429 nao e' "nao tem" — e' "espera". Sem isto, dentro
    dos fios ele virava "ficha sem vendedor" em silencio, que e' exatamente a
    classe de defeito que apagou 49 precos em 15/09.
    """
    for i in range(tentativas):
        r = requests.get(API + caminho, params=params, timeout=TIMEOUT_S,
                         headers={"Authorization": "Bearer " + token()})
        if r.status_code == 429 and i < tentativas - 1:
            time.sleep(1.5 * (i + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("inalcancavel")


# ⭐ ETIQUETA POR CANAL — o `matt_word` E' o campo de rastreamento do ML.
#
# ⚠️ ESTES NOMES FORAM CONFERIDOS NA TELA em 15/09/2026, em
# `/afiliados/adminlabel`. Nao sao os que eu sugeri: sao os que o ML GRAVOU.
# Escrever aqui um nome que nao existe la' e' o modo de falha mais caro —
# link que abre a pagina e nao paga, e o post parece certo pra sempre.
#
# ⭐ E sao de proposito os MESMOS nomes previstos pro tracking_id do
# AliExpress (`engine/garimpo.py`). Se as duas plataformas divergirem, o
# relatorio de venda por canal tem de ser traduzido na mao pra sempre.
#
# ⚠️ O painel tem etiquetas duplicadas (`faturachora` e `pagomenos`,
# `cozinhaimportada` e `achadinhochef`...). Ficamos com a familia que bate com
# o AliExpress; as outras existem e nao atrapalham, mas NAO devem ser usadas.
ETIQUETAS: dict[str, str] = {
    "truque.importado":        "achadinhomake",
    "cozinha.importada":       "achadinhochef",
    "achadinhos.instantaneos": "instantaneos",
    "fatura.chora":            "pagomenos",
    "atefalhar":               "atefalhar",
}


def etiqueta_de(canal: str) -> str:
    """A etiqueta deste canal, ou a da conta enquanto ele nao tiver uma.

    ⚠️ Falha ABERTA de proposito, ao contrario do AliExpress: aqui o
    `matt_word` e' texto livre e a conta ja' atribui com `bryanexpand` — o
    clique de 13/09 foi contado no painel com ele. Cair no padrao perde a
    separacao por canal, mas NAO perde a comissao.
    """
    return ETIQUETAS.get(canal) or (os.getenv("MELI_MATT_WORD") or "")


def com_afiliado(url: str, canal: str = "") -> str:
    """Pendura a nossa tag na URL do produto.

    ⭐ `canal` escolhe a etiqueta (ver `ETIQUETAS`). Sem canal, usa a da conta.

    ⚠️ PRESERVA os parametros que ja' existem e NAO duplica a tag se ela ja'
    estiver la'. URL de produto do ML costuma vir com `?pdp_filters=...`, e
    jogar fora a query original leva junto a variacao escolhida do produto.

    ⚠️ E SEM TAG, DEVOLVE VAZIO — nao a URL crua. Falha FECHADA: link sem tag
    abre a pagina normalmente e nao paga nada, e um post assim parece certo
    pra sempre. Melhor nao postar do que postar sem atribuir.
    """
    word = etiqueta_de(canal)
    tool = os.getenv("MELI_MATT_TOOL")
    if not (word and tool and url):
        return ""
    p = urlparse(url)
    q = parse_qs(p.query, keep_blank_values=True)
    q["matt_word"] = [word]
    q["matt_tool"] = [tool]
    return urlunparse(p._replace(query=urlencode(q, doseq=True)))


def tendencias(quantos: int = 20) -> list[str]:
    """O que o Brasil esta' procurando agora. Pauta, nao produto."""
    return [x.get("keyword", "") for x in _get("/trends/MLB")[:quantos]]


def mais_vendidos(categoria: str, quantos: int = 12, canal: str = "") -> list[dict]:
    """Os mais vendidos da categoria, ja' com preco e link de afiliado.

    ⚠️ O `/highlights` devolve so' o ID e o tipo — ITEM ou PRODUCT, e os dois
    se leem em endpoints DIFERENTES. Tratar tudo como item devolve 404 calado
    e a lista chega vazia sem ninguem entender por que.
    """
    d = _get(f"/highlights/MLB/category/{categoria}")
    saida = []
    for it in (d.get("content") or [])[:quantos]:
        iid, tipo = it.get("id"), it.get("type")
        try:
            if tipo == "PRODUCT":
                p = _get(f"/products/{iid}")
                nome = p.get("name")
                foto = (p.get("pictures") or [{}])[0].get("url", "")
                # ⚠️ O PRECO NAO ESTA' NO PRODUTO, e o `buy_box_winner` vem
                # `null` — medido em 13/09/2026. Produto de catalogo e' a
                # FICHA (um Cicaplast); quem tem preco e' o ANUNCIO de cada
                # vendedor, em /products/{id}/items. Ler o preco do produto
                # devolve None calado, e a lista chega vazia sem explicacao.
                itens = (_get(f"/products/{iid}/items")
                         .get("results") or [])
                if not itens:
                    continue
                # o primeiro e' o vencedor da buy box na ordem que o ML manda
                preco = itens[0].get("price")
                # ⚠️ E O PERMALINK DO PRODUTO VEM VAZIO. O link que funciona
                # e' o /p/{id} — foi com ele que o Bryan viu a barra de
                # afiliado com GANHOS 16%.
                url = f"https://www.mercadolivre.com.br/p/{iid}"
            else:
                p = _get(f"/items/{iid}")
                nome, preco = p.get("title"), p.get("price")
                url = p.get("permalink", "")
                foto = p.get("thumbnail", "")
        except requests.HTTPError:
            continue
        link = com_afiliado(url, canal)
        if not (nome and preco and link):
            continue
        # ⭐ A comissao VISTA no hub, se ainda estiver no prazo. Fora do prazo
        # vem None, e `so_monetizados()` tira o produto do catalogo.
        com = comissao_valida(iid)
        saida.append({
            "nome": nome, "link": link, "imagem": foto,
            "preco": f"R$ {float(preco):.2f}".replace(".", ","),
            "loja": "Mercado Livre", "_id": iid, "_tipo": tipo,
            "comissao": (com or {}).get("pct"),
            "comissao_vista_em": (com or {}).get("visto", ""),
        })
    return saida


PERGUNTA_EXPANSAO = (
    "Alguem pediu este produto numa loja brasileira: \"{termo}\". "
    "Escreva de 3 a 5 buscas curtas para o catalogo do Mercado Livre que "
    "encontrem o produto de verdade (nao pecas, nao acessorios, nao livros), "
    "cada uma com uma MARCA comum no Brasil e, se fizer sentido, uma "
    "especificacao (potencia, litros, tamanho). Uma por linha, sem numerar, "
    "sem comentario. Exemplo para 'liquidificador': liquidificador Mondial "
    "550W / liquidificador Philips Walita / liquidificador Oster 1400W"
)


def expandir(termo: str) -> list[str]:
    """Termo generico -> buscas com marca/especificacao. [] se nao deu.

    ⭐ E' O CONSERTO DO UNICO CASO RUIM da busca dirigida (medido em
    16/09/2026): "liquidificador" tem 150 fichas no catalogo e 2 com
    vendedor; "liquidificador mondial" tem 8 em 20. A marca e' o que separa
    ficha real de fantasma, e o modelo sabe quais marcas existem no Brasil.

    ⚠️ Gemini primeiro, OpenRouter de reserva — o MESMO rodizio de chaves do
    `nome_produto`, com as mesmas regras (429 queima a chave, nao a rodada).
    Sem nenhum dos dois, devolve [] e a busca segue so' com o termo e as
    marcas que as proprias fichas trazem — mais lenta, nao errada.

    ⛔ O QUE SAI DO MODELO E' SUGESTAO DE BUSCA, nunca produto: cada linha
    ainda passa pelo catalogo e pelos anuncios. Modelo nao inventa preco aqui
    porque nao ha' onde inventar.
    """
    from . import modelo_texto
    pergunta = PERGUNTA_EXPANSAO.format(termo=termo.strip())
    texto = modelo_texto.perguntar(pergunta)
    saida = []
    for ln in (texto or "").splitlines():
        ln = ln.strip().lstrip("-*0123456789. ").strip()
        if 3 <= len(ln) <= 80 and ln.lower() != termo.lower():
            saida.append(ln)
    return saida[:5]


def buscar(termo: str, quantos: int = 8, canal: str = "",
           candidatos: int = 50, paginas: int = 3,
           expandir_termo: bool = True) -> list[dict]:
    """Busca DIRIGIDA por produto — o caminho do pedido sob demanda.

    ⭐ E' ISTO que o ML tem de bom pra operacao (decisao do Bryan em 16/09/2026:
    "quando for um pedido assim e tiver em diversas lojas, publica o melhor de
    cada canal"). Os mais vendidos dele sao sabao em po'; a busca por nome e'
    onde ele vira loja brasileira com entrega rapida ao lado do AliExpress.

    ⚠️ O `/sites/MLB/search` continua 403 (reconferido em 16/09/2026, com e
    sem token). O que abre e' o `/products/search` — o CATALOGO, fichas sem
    preco — e o preco vem de `/products/{id}/items`, um anuncio por vendedor.

    ⛔ DUAS ARMADILHAS MEDIDAS em 16/09/2026:

    1. Termo generico ("liquidificador") devolve FICHAS FANTASMA na frente:
       50 fichas, ZERO com vendedor — cada `/items` responde 404 "No winners
       found". Nao e' erro nosso nem token: e' catalogo sem anuncio. Por isso
       o 404 aqui e' "pula", nao "estoura", e por isso `candidatos` > `quantos`.
    2. O PRIMEIRO anuncio NAO E' O MAIS BARATO: `[72, 149.99]`, `[289, 127,
       309]`. `mais_vendidos` le o primeiro (buy box); aqui o que vale e' o
       MENOR — o pedido e' "melhor preco possivel".

    3. O `/items` NAO TRAZ `sold_quantity` (medido: 22 campos, nenhum de
       venda). O unico sinal de "produto real" e' QUANTOS VENDEDORES a ficha
       tem: a Elgin tinha 18, o "liquidificador de R$ 500" tinha 1. Ficha de
       1 vendedor so' entra se nao houver nada com 2 ou mais.
    4. A busca por texto traz LIVRO ("Receitas na Air Fryer", MLB-BOOKS) na
       frente de fritadeira. O `domain_id` da ficha e' quem separa.

    ⚠️ Custo: ~0,8 s por ficha (UMA chamada — a foto ja' vem na busca), e o
    ACERTO e' de 10-15% em qualquer corte (medido: 2/20 com `q`, 3/20 com
    `q`+dominio, `domain_id` sozinho da' 400). Serial, 50 candidatos = 40 s
    pra 5 produtos. As chamadas sao independentes, entao vao em PARALELO
    (6 fios): 50 candidatos em ~8 s. E' o preco da velocidade que o pedido
    exige; nao chamar em loop.
    """
    from concurrent.futures import ThreadPoolExecutor

    def _itens(r):
        try:
            return r, _get(f"/products/{r['id']}/items").get("results") or []
        except requests.HTTPError as e:
            # ⛔ SO' O 404 ("No winners found") significa ficha sem vendedor.
            # Qualquer outro erro e' falta de INFORMACAO, nao ausencia de
            # produto — e sobe, pra ninguem publicar "nao achei" por cima
            # de um 429.
            if e.response is not None and e.response.status_code == 404:
                return r, []
            raise

    # ⚠️ PAGINA ATE' ENCHER A COTA. Termo generico ("liquidificador") tem as
    # fichas reais (Mondial, Philips...) alem da primeira pagina de 50: com
    # uma pagina so' veio 1 produto. `paginas` e' o teto de tempo (~15 s cada).
    pares = []
    vistos: set[str] = set()
    # ⭐ PRIMEIRO AS BUSCAS EXPANDIDAS PELO MODELO (marca + especificacao):
    # sao as que acertam. A paginacao do termo cru vem depois, so' se faltar.
    if expandir_termo:
        for sug in expandir(termo):
            try:
                d = _get("/products/search", status="active", site_id="MLB",
                         q=sug, limit=20)
            except requests.HTTPError:
                continue
            novas = [r for r in (d.get("results") or [])
                     if r.get("id") and r["id"] not in vistos
                     and (r.get("domain_id") or "") not in FORA_DOMINIOS]
            vistos.update(r["id"] for r in novas)
            with ThreadPoolExecutor(max_workers=4) as ex:
                pares += list(ex.map(_itens, novas))
        if sum(1 for _r, it in pares if len(it) >= 2) >= quantos:
            paginas = 0
    for pg in range(paginas):
        d = _get("/products/search", status="active", site_id="MLB",
                 q=termo, limit=min(candidatos, 50), offset=pg * candidatos)
        fichas = [r for r in (d.get("results") or [])
                  if r.get("id") and r["id"] not in vistos
                  and (r.get("domain_id") or "") not in FORA_DOMINIOS]
        vistos.update(r["id"] for r in fichas)
        if not fichas:
            break
        with ThreadPoolExecutor(max_workers=4) as ex:
            pares += list(ex.map(_itens, fichas))
        if sum(1 for _r, it in pares if len(it) >= 2) >= quantos:
            break

    # ⭐ SEGUNDA PASSADA POR MARCA. Termo generico e' pobre no catalogo
    # ("liquidificador": 150 fichas, 2 com vendedor), mas termo + marca e'
    # rico ("liquidificador mondial": 8 de 20). As marcas nao vem de lista
    # nossa — vem do atributo BRAND das fichas que a propria busca devolveu,
    # entao servem pra qualquer produto sem ninguem manter tabela.
    if sum(1 for _r, it in pares if len(it) >= 2) < quantos:
        from collections import Counter as _C
        marcas = _C()
        for r, _it in pares:
            for at in r.get("attributes") or []:
                if at.get("id") == "BRAND" and at.get("value_name"):
                    marcas[at["value_name"]] += 1
        for marca, _n in marcas.most_common(3):
            d = _get("/products/search", status="active", site_id="MLB",
                     q=f"{termo} {marca}", limit=20)
            novas = [r for r in (d.get("results") or [])
                     if r.get("id") and r["id"] not in vistos
                     and (r.get("domain_id") or "") not in FORA_DOMINIOS]
            vistos.update(r["id"] for r in novas)
            with ThreadPoolExecutor(max_workers=4) as ex:
                pares += list(ex.map(_itens, novas))

    brutos = []
    for r, itens in pares:
        pid = r["id"]
        precos = [float(i["price"]) for i in itens
                  if i.get("price") and float(i["price"]) > 0]
        if not precos:
            continue
        menor = min(precos)
        vencedor = next((i for i in itens
                         if float(i.get("price") or 0) == menor), itens[0])
        nome = r.get("name")
        link = com_afiliado(f"https://www.mercadolivre.com.br/p/{pid}", canal)
        if not (nome and link):
            continue
        com = comissao_valida(pid)
        cat = vencedor.get("category_id") or ""
        base = comissao_base(cat)
        brutos.append({
            "nome": nome, "link": link,
            "imagem": (r.get("pictures") or [{}])[0].get("url", ""),
            "preco": f"R$ {menor:.2f}".replace(".", ","),
            "preco_num": menor,
            "vendedores": len(itens),
            "frete_gratis": bool((vencedor.get("shipping") or {}).get("free_shipping")),
            "dominio": r.get("domain_id") or "",
            "categoria_ml": cat,
            "loja": "Mercado Livre", "_id": pid, "_tipo": "PRODUCT",
            # ⭐ a BASE do programa pela categoria-raiz; a anotacao do hub,
            # quando existir e estiver no prazo, e' o "ganhos extras" por cima
            "comissao_base": base,
            "comissao": (com or {}).get("pct") or base,
            "comissao_vista_em": (com or {}).get("visto", ""),
        })
    # ⭐ O DOMINIO MAJORITARIO DA BUSCA E' O PRODUTO PEDIDO. "liquidificador"
    # devolve 109 fichas em MLB-BLENDERS e 6 em ..._DRIVE_COUPLINGS — e as
    # pecas (acoplador a R$ 9,50, lamina) sao justamente as que tem vendedor
    # e ficariam em primeiro por preco. Quem pediu liquidificador nao quer
    # o arraste do copo. Ficha de dominio minoritario so' entra se o
    # majoritario nao tiver produto real.
    from collections import Counter
    dominios = Counter(r.get("domain_id") or "" for r, _it in pares)
    principal = dominios.most_common(1)[0][0] if dominios else ""
    do_principal = [x for x in brutos if x["dominio"] == principal]
    if do_principal:
        brutos = do_principal
    reais = [x for x in brutos if x["vendedores"] >= 2] or brutos
    reais.sort(key=lambda x: x["preco_num"])
    return reais[:quantos]


def fichas_atual(ids: list[str]) -> dict[str, tuple]:
    """{id: (MENOR preco agora, QUANTOS vendedores, frete gratis?, seller_id)}.
    Ficha sem vendedor fica de fora.

    ⭐ O NUMERO DE VENDEDORES E' A PROVA SOCIAL DO ML (17/09/2026). A API
    nao da' vendas; da' a lista de anuncios do produto, um por vendedor — e
    esse numero a pessoa CONFERE na pagina da loja ("13 vendedores"). Entra
    na serie como `vol`, e o cartao mostra "+N vendedores desde dd/mm"
    quando cresceu, ou "N vendedores na loja" quando nao.

    ⭐ E' a porta da reconferencia de hora em hora (`engine/precos.py`) para
    produto do ML: a MESMA regra do AliExpress — o que nao respondeu fica
    com a leitura anterior, o que respondeu vira instantaneo.

    ⚠️ Uma chamada por produto (`/products/{id}/items`), em 4 fios com
    espera no 429. 100 produtos = ~25 s. E o preco e' o MENOR anuncio, igual
    a `buscar`: o comprador que clica ve' a lista de vendedores e escolhe o
    mais barato; anunciar o buy box seria anunciar mais caro.

    ⛔ 404 ("No winners found") = ficha sem vendedor HOJE: nao entra, e a
    trava de 24h da pagina a derruba sozinha. Qualquer outro erro SOBE.
    """
    from concurrent.futures import ThreadPoolExecutor

    def _um(pid):
        try:
            itens = _get(f"/products/{pid}/items").get("results") or []
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return pid, None
            raise
        precos = [float(i["price"]) for i in itens
                  if i.get("price") and float(i["price"]) > 0]
        if not precos:
            return pid, None
        # ⭐ O anuncio MAIS BARATO manda: e' ele que a pessoa ve' primeiro.
        # Dele saem frete gratis e o vendedor (regua v2, 17/09/2026).
        barato = min((i for i in itens if i.get("price") and float(i["price"]) > 0),
                     key=lambda i: float(i["price"]))
        return pid, (min(precos), len(precos),
                     bool((barato.get("shipping") or {}).get("free_shipping")),
                     barato.get("seller_id"))

    with ThreadPoolExecutor(max_workers=4) as ex:
        return {pid: v for pid, v in ex.map(_um, ids) if v is not None}


# ⭐ REPUTACAO DO VENDEDOR — o "termometro" (Ecommerce na Pratica; regua v2).
# `level_id` vai de 1_red a 5_green; `power_seller_status` e' null, silver,
# gold, platinum. Uma chamada por VENDEDOR (cache no processo), nao por
# produto.
_REP_CACHE: dict = {}


def reputacao(seller_id) -> dict:
    """{"nivel": 1..5 ou 0, "power": "silver"|..|"", "positivas": 0..1 ou None}"""
    if seller_id in (None, ""):
        return {}
    if seller_id in _REP_CACHE:
        return _REP_CACHE[seller_id]
    try:
        u = _get(f"/users/{seller_id}")
    except Exception:                                 # noqa: BLE001
        return {}
    rep = u.get("seller_reputation") or {}
    lvl = str(rep.get("level_id") or "")
    try:
        nivel = int(lvl.split("_")[0]) if lvl and lvl[0].isdigit() else 0
    except ValueError:
        nivel = 0
    pos = ((rep.get("transactions") or {}).get("ratings") or {}).get("positive")
    r = {"nivel": nivel, "power": rep.get("power_seller_status") or "",
         "positivas": float(pos) if pos is not None else None}
    _REP_CACHE[seller_id] = r
    return r


def preco_atual(ids: list[str]) -> dict[str, float]:
    """{id: MENOR preco anunciado agora} — a mesma chamada, so' o preco."""
    return {pid: v[0] for pid, v in fichas_atual(ids).items()}


def so_monetizados(produtos: list[dict]) -> list[dict]:
    """Deixa passar apenas o que TEM comissao anotada e dentro do prazo.

    ⭐ Ordem de decisao do Bryan em 15/09/2026: *"postar no site so' o que
    monetizar pra nos do ML, e quando parar de monetizar some do site"*.

    ⚠️ A regra automatica que ele imaginou NAO existe: a API nao devolve
    comissao (medido — ficha sem campo, quatro rotas de afiliado em 404) e o
    painel NAO exporta. Entao o sinal e' a anotacao a mao, e o que a substitui
    e' o PRAZO — `VALIDADE_COMISSAO_DIAS`: sem reconferir, o produto sai
    sozinho.

    ⛔ Nao afrouxar isso para "manter o catalogo cheio". Catalogo grande com
    comissao velha e' pior que catalogo pequeno — e' a mesma razao pela qual o
    preco reconferido em 48h ja' derruba produto bom.
    """
    # ⭐ Desde 16/09/2026 a comissao-BASE do programa conta (decisao do
    # Bryan). Fica de fora so' quem esta' em raiz que paga 0 (Alimentos) ou
    # cuja raiz nao se conhece — 0 e' "nao sei", e "nao sei" nao publica.
    return [p for p in produtos if float(p.get("comissao") or 0) > 0]


def por_canal(canal: str, quantos: int = 12) -> list[dict]:
    """Mais vendidos das SUBCATEGORIAS uteis do canal, sem as vetadas.

    ⚠️ Puxar a categoria MAE e' o que trazia papel higienico — ver `FORA`.
    """
    saida, vistos = [], set()
    for mae, _nome in CATEGORIAS.get(canal, []):
        for cid, _cn in subcategorias_uteis(mae):
            for p in mais_vendidos(cid, quantos, canal):
                if p["_id"] in vistos:
                    continue
                vistos.add(p["_id"])
                saida.append(p)
    return saida


def main() -> None:
    """`python -m engine.mercadolivre --buscar "air fryer 4 litros" --canal cozinha.importada`"""
    import argparse
    a = argparse.ArgumentParser(description="Mercado Livre: busca dirigida")
    a.add_argument("--buscar", metavar="TERMO", help="o produto pedido")
    a.add_argument("--canal", default="", help="etiqueta do canal no link")
    a.add_argument("--quantos", type=int, default=5)
    o = a.parse_args()
    if not o.buscar:
        a.print_help()
        return
    r = buscar(o.buscar, quantos=o.quantos, canal=o.canal)
    if not r:
        print("ml: nada com vendedor pra esse termo — tenta com a marca junto")
        return
    for x in r:
        print(f"{x['preco']:>11}  {x['vendedores']:>2} vend  "
              f"{'frete gratis' if x['frete_gratis'] else '            '}  "
              f"{x['nome'][:56]}")
        print(f"             {x['link']}")


if __name__ == "__main__":
    main()
