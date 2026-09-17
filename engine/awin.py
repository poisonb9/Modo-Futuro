# -*- coding: utf-8 -*-
"""Awin: ver o estado das candidaturas sem abrir o painel.

    python -m engine.awin              o placar: aprovado, pendente, recusado
    python -m engine.awin --links      o link de afiliado de cada aprovado

## ⚠️ O QUE ESTE MODULO RESOLVE

Candidatura no Awin nao avisa quando muda. A aprovacao chega por e-mail, e
e-mail se perde — e um anunciante aprovado que ninguem percebeu e' comissao
parada. Aqui o estado se le' em dois segundos.

⚠️ E A MAQUINA ALCANCA O AWIN, ao contrario do AliExpress (ver
`engine/aliexpress.py`): `api.awin.com` responde 401 sem token, que e'
resposta. Entao isto roda aqui mesmo.

## ⚠️ O TOKEN E' DE LEITURA E ESCRITA — TRATE COMO SENHA

Ele vive no `.env`, que nao e' versionado. Nunca no repositorio: este e'
publico.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

RAIZ = Path(__file__).resolve().parent.parent
# ⚠️ VERSIONADO de proposito (vai no commit do garimpo). Sem isso o runner
# efemero nasce sem linha de base todo dia, e "mudou desde ontem" viraria
# "mudou desde ha' cinco minutos" — ou seja, nunca avisaria nada.
ESTADO = RAIZ / "estado" / "awin_programas.json"
# ⭐ O INSTANTANEO DO CATALOGO AWIN — o que a pagina le'. Mesmo papel do
# `precos_agora.json` do AliExpress: quem publica NAO baixa feed; le' isto.
# Assim o publicador nao depende de rede nem da chave do feed, e a idade do
# arquivo (`quando`) e' a trava de honestidade — ver `publicar_bio`.
CATALOGO_ESTADO = RAIZ / "estado" / "awin_catalogo.json"
# ⚠️ A MESMA SERIE do AliExpress, com o id prefixado `awin:`. E' dela que a
# pagina tira `pontos`, grafico e queda — entao o produto do feed gradua
# sozinho de "novo no catalogo" para grafico quando juntar 3 dias, sem a
# pagina saber de onde ele veio. O prefixo evita colisao: os dois catalogos
# usam ids numericos.
PRECOS = RAIZ / "estado" / "precos_vistos.jsonl"

API = "https://api.awin.com"
# ⚠️ O `joined` e' o que importa: so' anunciante aprovado gera comissao.
# `pending` e' expectativa, e confundir os dois faz a gente publicar produto
# de loja que ainda nao nos aceitou — link que leva a lugar nenhum.
RELACOES = ("joined", "pending", "rejected", "suspended")


def _credencial() -> tuple[str, str]:
    t = os.getenv("AWIN_TOKEN")
    p = os.getenv("AWIN_PUBLISHER_ID")
    if not (t and p):
        raise RuntimeError(
            "faltam AWIN_TOKEN / AWIN_PUBLISHER_ID no .env "
            "(o token sai em Conta -> Credenciais de API)")
    return t, p


def programas(relacao: str = "joined") -> list[dict]:
    tok, pid = _credencial()
    r = requests.get(f"{API}/publishers/{pid}/programmes",
                     params={"relationship": relacao},
                     headers={"Authorization": "Bearer " + tok}, timeout=30)
    r.raise_for_status()
    return r.json()


def link(destino: str, id_anunciante: int) -> str:
    """O link de afiliado pra uma pagina da loja.

    ⚠️ `awclick.php` com `mid` (o anunciante) e `id` (nos) e' o formato que o
    Awin rastreia. Link sem o `id` funciona e NAO paga — e' o jeito mais
    silencioso de perder comissao, porque a pagina abre normalmente.
    """
    _, pid = _credencial()
    from urllib.parse import quote
    return (f"https://www.awin1.com/cread.php?awinmid={id_anunciante}"
            f"&awinaffid={pid}&ued={quote(destino, safe='')}")


def _instantaneo() -> dict:
    """{nome do anunciante: relacao} pra TODAS as relacoes, agora."""
    return {x.get("name") or str(x.get("id")): rel
            for rel in RELACOES for x in programas(rel)}


def _salvo() -> dict | None:
    if not ESTADO.exists():
        return None
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))["programas"]
    except (ValueError, KeyError):
        return None


def vigiar(avisar: bool = True) -> list[str]:
    """Compara com a ultima leitura e devolve as linhas do que MUDOU.

    ⭐ POR QUE ISTO EXISTE: candidatura aprovada nao avisa ninguem. A
    aprovacao chega por e-mail, e e-mail se perde — anunciante aprovado que
    ninguem percebeu e' comissao parada enquanto o canal publica AliExpress
    a 7%.

    ⚠️ PRIMEIRA LEITURA NAO AVISA NADA. Sem linha de base, as 28 pendentes
    de hoje seriam 28 "novidades" — e um aviso que grita na estreia ensina a
    ignorar o aviso. Grava a base e fica quieto.

    ⚠️ E SO' GRAVA SE A LEITURA DEU CERTO. Gravar apos falha apagaria a
    linha de base, e a proxima rodada acusaria mudanca que nao houve.
    """
    agora = _instantaneo()          # se estourar, nao grava nada: e' de proposito
    antes = _salvo()
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(
        {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "programas": agora}, ensure_ascii=False, indent=2) + chr(10),
        encoding="utf-8")
    if antes is None:
        print(f"awin: linha de base gravada ({len(agora)} anunciantes). "
              "Da proxima vez eu comparo.")
        return []

    linhas = []
    for nome, rel in sorted(agora.items()):
        rel_antes = antes.get(nome)
        if rel_antes == rel:
            continue
        if rel_antes is None:
            linhas.append(f"NOVO      {nome} ({rel})")
        elif rel == "joined":
            # ⭐ A unica linha que vale dinheiro hoje.
            linhas.append(f"APROVADO  {nome}  <- da pra publicar produto dele")
        else:
            linhas.append(f"mudou     {nome}: {rel_antes} -> {rel}")
    for nome in sorted(set(antes) - set(agora)):
        linhas.append(f"sumiu     {nome} (era {antes[nome]})")

    if linhas:
        print("awin mudou:")
        for L in linhas:
            print("   " + L)
        if avisar:
            # ⚠️ O MOTIVO DA RECUSA NAO VEM POR AQUI. A API de programmes so'
            # da' a relacao; o porque' chega no e-mail do Awin (medido em
            # 14/09/2026: a 365Rider recusou por "O site nao complementa a
            # marca do anunciante"). Entao o aviso manda olhar o e-mail em vez
            # de inventar uma explicacao.
            from . import telegram
            telegram.enviar("Awin mudou:" + chr(10) + chr(10)
                            + chr(10).join(linhas) + chr(10) + chr(10)
                            + "O motivo (se houve recusa) so' vem no e-mail.")
    else:
        print("awin: nada mudou.")
    return linhas

# ─────────────────────────────────────────────────────────────────────────
# CATALOGO — os produtos dos anunciantes aprovados
# ─────────────────────────────────────────────────────────────────────────

FEED_LISTA = "https://productdata.awin.com/datafeed/list/apikey/"


def _chave_feed() -> str:
    """A chave do FEED, que NAO e' o AWIN_TOKEN.

    ⛔ SAO DUAS CREDENCIAIS DIFERENTES, e trocar uma pela outra da' erro que
    parece "chave invalida" (medido em 16/09/2026):

        AWIN_TOKEN           formato com hifens, sai de ui.awin.com/awin-api
                             abre `programmes` e relatorios — NAO abre produto
        AWIN_FEED_API_KEY    32 caracteres sem hifen, e' o pedaco que vive
                             DENTRO da URL de download, entre /apikey/ e a
                             proxima barra. Sai de Ferramentas -> Crie um
                             Feed, na caixa de download do ultimo passo.

    ⚠️ A URL de download E' a credencial: quem tiver o link baixa os nossos
    feeds sem senha nenhuma. Nunca colar em chat, print ou commit.
    """
    k = os.getenv("AWIN_FEED_API_KEY")
    if not k:
        raise RuntimeError(
            "falta AWIN_FEED_API_KEY no .env — e' a chave do FEED, diferente "
            "do AWIN_TOKEN. Sai em Ferramentas -> Crie um Feed, dentro da URL "
            "de download (entre /apikey/ e a barra seguinte)")
    return k


def feeds() -> list[dict]:
    """Todos os feeds do catalogo Awin, com o nosso status em cada um.

    ⭐ POR QUE LER A LISTA EM VEZ DE GUARDAR URL DE FEED: a URL que o painel
    monta tem o filtro CONGELADO dentro dela (um `fid`, ou uma lista de
    categorias). Anunciante novo tem `fid` novo, e a URL velha nunca saberia
    dele — teriamos que voltar no painel a cada aprovacao. Esta lista traz o
    `Membership Status` AO VIVO e a URL de download pronta de cada um, entao
    aprovacao nova entra sozinha na proxima rodada.

    ⚠️ O STATUS AQUI E' `active`, NAO `joined` (medido em 16/09/2026). A API
    de `programmes` usa "joined"; este CSV usa "active". Filtrar por "joined"
    devolve ZERO e parece que nao temos nenhum anunciante aprovado.
    """
    r = requests.get(FEED_LISTA + _chave_feed(), timeout=120)
    r.raise_for_status()
    import csv
    import io
    return list(csv.DictReader(io.StringIO(r.text)))


def _preco(v) -> float:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return 0.0


def catalogo(teto: float = 0.0, piso: float = 0.0) -> list[dict]:
    """Os produtos de TODO anunciante aprovado, deduplicados.

    `teto` e `piso` em reais; 0 desliga o corte.

    ⚠️ DEDUPLICA POR `aw_product_id` PORQUE O MESMO ANUNCIANTE APARECE MAIS
    DE UMA VEZ. Medido em 16/09/2026: a Nike BR tem DOIS feeds, o 44669 (29
    colunas, 5.447 produtos) e o 93360 (35 colunas, 5.457). Os produtos se
    sobrepoem — sem deduplicar, o mesmo tenis sai duas vezes na pagina.

    ⭐ E FICA COM A LINHA MAIS COMPLETA, nao com a primeira. O 44669 nao
    preenche `in_stock`; o 93360 preenche. Manter a primeira que chegasse
    seria sorteio.

    ⚠️ `in_stock` VEIO 1 EM 100% DOS 5.457 do 93360, o que e' improvavel num
    catalogo de moda — provavelmente o campo e' fixo, nao medido. Entao ele
    NAO e' usado como garantia de estoque aqui: quem decide isso e' a pagina
    do produto no dia do clique.
    """
    linhas = [f for f in feeds()
              if (f.get("Membership Status") or "").strip().lower() == "active"]
    import csv
    import gzip
    import io as _io

    vistos: dict[str, dict] = {}
    for f in linhas:
        try:
            r = requests.get(f["URL"], timeout=300)
            r.raise_for_status()
            bruto = gzip.decompress(r.content).decode("utf-8", "replace")
        except Exception as e:                      # noqa: BLE001
            # ⚠️ Um feed que falha NAO derruba os outros: o catalogo do dia
            # sai menor, e o aviso diz qual faltou. Melhor pagina com uma
            # loja do que pagina nenhuma.
            print(f"   awin: feed {f.get('Feed ID')} "
                  f"({f.get('Advertiser Name')}) falhou — {str(e)[:80]}")
            continue
        for p in csv.DictReader(_io.StringIO(bruto)):
            pid = (p.get("aw_product_id") or "").strip()
            if not pid:
                continue
            anterior = vistos.get(pid)
            if anterior and sum(1 for v in anterior.values() if v) >= \
                    sum(1 for v in p.values() if v):
                continue
            vistos[pid] = p

    saida = []
    for p in vistos.values():
        preco = _preco(p.get("search_price"))
        if preco <= 0:
            continue
        if piso and preco < piso:
            continue
        if teto and preco > teto:
            continue
        saida.append({
            "id": p.get("aw_product_id"),
            "nome": (p.get("product_name") or "").strip(),
            "preco": preco,
            "imagem": (p.get("merchant_image_url")
                       or p.get("aw_image_url") or "").strip(),
            # ⛔ SEMPRE o aw_deep_link. O `merchant_deep_link` abre a mesma
            # pagina e NAO paga — e' o jeito mais silencioso de perder
            # comissao, porque para o leitor os dois sao identicos.
            "link": (p.get("aw_deep_link") or "").strip(),
            "loja": (p.get("merchant_name") or "").strip(),
            "categoria": (p.get("merchant_category")
                          or p.get("category_name") or "").strip(),
            "marca": (p.get("brand_name") or "").strip(),
            # ⭐ SEM historico de proposito. Produto de feed nasce sem serie
            # de precos nossa; quem der "queda de X%" aqui estaria inventando.
            # A pagina mostra o selo "novo no catalogo" ate' o
            # `guardar_preco` juntar tres leituras — ver `_serie_curta`.
            "origem": "awin",
        })
    saida.sort(key=lambda x: x["preco"])
    return saida


def _ultimo_ponto_por_id() -> dict[str, tuple[str, float]]:
    """{id: (ultimo dia, ultimo preco)} so' dos ids `awin:` da serie."""
    saida: dict[str, tuple[str, float]] = {}
    if not PRECOS.exists():
        return saida
    for linha in PRECOS.read_text(encoding="utf-8").splitlines():
        if '"awin:' not in linha:
            continue
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        i, q = str(d.get("id") or ""), (d.get("quando") or "")[:10]
        if not i.startswith("awin:") or not q:
            continue
        try:
            v = float(d.get("preco") or 0)
        except (TypeError, ValueError):
            continue
        antes = saida.get(i)
        if antes is None or q >= antes[0]:
            saida[i] = (q, v)
    return saida


def guardar_catalogo(teto: float = 0.0) -> dict:
    """Baixa o catalogo, grava o INSTANTANEO e alimenta a SERIE. Devolve o
    instantaneo.

    ⭐ E' ESTE COMANDO que roda na nuvem (workflow do garimpo), e nao o
    publicador: a chave do feed fica num lugar so', e a pagina nasce de um
    arquivo versionado que qualquer um pode conferir.

    ⚠️ A SERIE RECEBE UM PONTO POR PRODUTO POR DIA, e so' quando o preco
    mudou desde o ultimo ponto — a mesma regra do `garimpo.guardar_preco`.
    Sem isto, 900 linhas por dia iguais as de ontem so' engordariam o arquivo.
    Na estreia entram todos (nao ha' ponto anterior), e isso e' o certo: e' o
    dia 1 dos tres que o grafico exige.

    ⛔ FALHA FECHADA: se `catalogo()` nao devolver produto nenhum, NAO
    sobrescreve o instantaneo anterior. Um feed fora do ar viraria "a Nike
    sumiu do site" em silencio — e o instantaneo velho, com `quando` de
    ontem, e' recusado pelo publicador pela idade, que e' o aviso certo.
    """
    from datetime import date
    # ⭐ A SERIE RECEBE O FEED INTEIRO; o teto vale so' pro INSTANTANEO (o
    # que vai pro site). Ordem do Bryan em 17/09/2026: "mesmo que nao entre
    # na loja, temos que ter os dados de todos os produtos — informacao que
    # nao volta comprando precos". Medido no mesmo dia: 26.455 no feed,
    # 8.093 ate' R$ 150 — 18.362 ficavam sem historico nenhum.
    todos = catalogo(teto=0)
    prods = [p for p in todos if not teto or p["preco"] <= teto]
    if not prods:
        raise SystemExit("awin: catalogo vazio — instantaneo anterior mantido")
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inst = {"quando": agora, "teto": teto, "produtos": prods}
    CATALOGO_ESTADO.parent.mkdir(parents=True, exist_ok=True)
    CATALOGO_ESTADO.write_text(
        json.dumps(inst, ensure_ascii=False), encoding="utf-8")

    hoje = f"{date.today():%Y-%m-%d}"
    ultimo = _ultimo_ponto_por_id()
    novos = 0
    with PRECOS.open("a", encoding="utf-8") as f:
        for p in todos:
            i = "awin:" + str(p["id"])
            antes = ultimo.get(i)
            if antes and abs(antes[1] - p["preco"]) < 0.005:
                continue
            linha = {"id": i, "preco": p["preco"], "vol": 0,
                     "loja": p["loja"], "quando": hoje}
            if antes is None:
                linha["nome"] = p["nome"]
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            novos += 1
    lojas: dict[str, int] = {}
    for p in prods:
        lojas[p["loja"]] = lojas.get(p["loja"], 0) + 1
    print(f"awin: instantaneo com {len(prods)} produtos ("
          + ", ".join(f"{k} {v}" for k, v in lojas.items())
          + f"); feed inteiro {len(todos)}; serie +{novos} ponto(s)")
    return inst


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="estado das candidaturas no Awin")
    a.add_argument("--links", action="store_true",
                   help="mostra o link de afiliado dos aprovados")
    a.add_argument("--vigiar", action="store_true",
                   help="avisa so' o que MUDOU desde a ultima leitura")
    a.add_argument("--catalogo", action="store_true",
                   help="os produtos dos anunciantes aprovados")
    a.add_argument("--teto", type=float, default=0.0,
                   help="preco maximo em reais (0 = sem corte)")
    a.add_argument("--piso", type=float, default=0.0,
                   help="preco minimo em reais (0 = sem corte)")
    a.add_argument("--guardar", action="store_true",
                   help="grava estado/awin_catalogo.json e alimenta a serie "
                        "(e' o que roda na nuvem)")
    o = a.parse_args()

    if o.vigiar:
        vigiar()
        return

    if o.guardar:
        guardar_catalogo(teto=o.teto)
        return

    if o.catalogo:
        d = catalogo(teto=o.teto, piso=o.piso)
        if not d:
            print("awin: nenhum produto — ou nao ha' anunciante aprovado, "
                  "ou o corte de preco nao deixou nada passar.")
            return
        lojas: dict[str, int] = {}
        for x in d:
            lojas[x["loja"]] = lojas.get(x["loja"], 0) + 1
        print(f"awin: {len(d)} produtos  " + " | ".join(
            f"{k} {v}" for k, v in sorted(lojas.items(), key=lambda y: -y[1])))
        print(f"   preco: R$ {d[0]['preco']:.2f} a R$ {d[-1]['preco']:.2f}")
        for x in d[:10]:
            print(f"   R$ {x['preco']:>8.2f}  {x['nome'][:56]}")
        return

    for rel in RELACOES:
        try:
            d = programas(rel)
        except requests.HTTPError as e:
            print(f"{rel:10} — {e}")
            continue
        print(f"\n{rel.upper()}: {len(d)}")
        for x in sorted(d, key=lambda y: y.get("name") or ""):
            print(f"   {x.get('name')}  ({x.get('primarySector') or 'sem setor'})")
            if o.links and rel == "joined":
                print("      ", link(x.get("displayUrl", ""), x["id"]))


if __name__ == "__main__":
    main()
