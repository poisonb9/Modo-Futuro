# -*- coding: utf-8 -*-
"""O que as pessoas procuraram no site e nao acharam — e o que fazer com isso.

## POR QUE EXISTE

Ordem do Bryan em 16/09/2026: *"meu amigo entrou no site e pesquisou por
macbook e nao tinha nada. Eu queria que nos soubessemos disso, que o proximo
radar ja' viesse com o item, e que, se nao tiver fonte, isso me fosse mostrado
no fechamento do dia."*

## O CICLO

    pagina (todos.html)     anota {termo, resultados, categoria} no Supabase
                            quando a pessoa para de digitar — so' INSERT
    este modulo             le' as buscas com 0 resultado ainda nao olhadas,
                            procura em CADA fonte, e:
                              achou      -> lista os candidatos (o pedido sob
                                            demanda publica; regra A de 16/09)
                              nao achou  -> marca `sem_fonte` e entra no
                                            fechamento do dia

## ⚠️ QUEM LE' O BANCO

A pagina usa a chave publica e as politicas so' deixam ela INSERIR. Ler e
marcar e' com a chave mestra (`SUPABASE_PAT`), pela Management API — o mesmo
caminho do `supabase/rodar_sql.py`. Roda AQUI, nao na nuvem: o PAT nao esta'
nos secrets do workflow, e nao deve estar ate' o Bryan decidir.

## ⚠️ O QUE E' "SEM FONTE"

So' depois de perguntar as TRES: AliExpress (`product.query`), Mercado Livre
(`buscar`, com expansao por marca) e o instantaneo do Awin. Uma fonte fora
do ar NAO e' "sem fonte" — e' "nao sei", e a busca fica pendente pra proxima
rodada. Marcar sem_fonte por cima de um 429 seria o mesmo erro que apagou 49
precos em 15/09.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

RAIZ = Path(__file__).resolve().parent.parent
REF = "lwtqfwkfcknzyyzmuymg"
# ⚠️ Fica versionado: e' o registro do que a operacao NAO consegue vender.
SEM_FONTE = RAIZ / "estado" / "buscas_sem_fonte.jsonl"


def _sql(query: str, params: list | None = None) -> list:
    pat = os.getenv("SUPABASE_PAT")
    if not pat:
        raise SystemExit("falta SUPABASE_PAT no .env — e' a chave mestra, ver supabase/rodar_sql.py")
    # ⚠️ A Management API nao aceita parametros: o termo entra na query. Ele
    # e' texto de estranho, entao vai escapado do unico jeito que o SQL
    # entende — aspas dobradas. Nunca f-string crua com o termo.
    for p in params or []:
        query = query.replace("?", "'" + str(p).replace("'", "''") + "'", 1)
    req = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{REF}/database/query",
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={"Authorization": f"Bearer {pat}",
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def pendentes(dias: int = 7) -> list[dict]:
    """Termos com 0 resultado ainda nao olhados, agrupados, mais buscados
    primeiro. `vezes` e' quantas pessoas (ou tentativas) pediram."""
    return _sql(
        "select lower(trim(termo)) as termo, count(*) as vezes, "
        "       max(quando) as ultima, array_agg(id) as ids "
        "from busca where atendida is null and resultados = 0 "
        "  and quando > now() - make_interval(days => " + str(int(dias)) + ") "
        "  and nota is distinct from 'TESTE' "
        "group by 1 order by vezes desc, ultima desc")


def marcar(ids: list[int], como: str, nota: str = "") -> None:
    if not ids:
        return
    lista = ",".join(str(int(i)) for i in ids)
    _sql("update busca set atendida = ?, atendida_em = now(), nota = ? "
         f"where id in ({lista})", [como, nota[:200]])


def _aliexpress(termo: str, canal: str = "") -> list[dict]:
    from . import aliexpress, garimpo
    r = aliexpress.chamar(
        "aliexpress.affiliate.product.query", keywords=termo, page_size="10",
        target_currency="BRL", target_language="PT", ship_to_country="BR",
        tracking_id=garimpo.tracking_de(canal) if canal else "default",
        sort="LAST_VOLUME_DESC")
    res = (r.get("aliexpress_affiliate_product_query_response", {})
            .get("resp_result", {}))
    if str(res.get("resp_code")) != "200":
        raise RuntimeError(f"aliexpress: {res.get('resp_msg')}")
    prods = (res.get("result", {}).get("products", {}).get("product", []) or [])
    saida = []
    for p in prods[:5]:
        try:
            preco = float(p.get("target_sale_price") or 0)
        except (TypeError, ValueError):
            continue
        if preco <= 0:
            continue
        saida.append({"fonte": "AliExpress", "nome": p.get("product_title", "")[:70],
                      "preco": preco, "vendas": int(garimpo._num(p.get("lastest_volume"))),
                      "link": p.get("promotion_link", "")})
    return sorted(saida, key=lambda x: x["preco"])


def _mercadolivre(termo: str, canal: str = "") -> list[dict]:
    from . import mercadolivre
    return [{"fonte": "Mercado Livre", "nome": x["nome"][:70], "preco": x["preco_num"],
             "vendas": x["vendedores"], "link": x["link"]}
            for x in mercadolivre.buscar(termo, quantos=5, canal=canal)]


def _awin(termo: str) -> list[dict]:
    arq = RAIZ / "estado" / "awin_catalogo.json"
    if not arq.exists():
        return []
    palavras = [w for w in termo.lower().split() if len(w) >= 3]
    saida = []
    for p in json.loads(arq.read_text(encoding="utf-8")).get("produtos") or []:
        nome = (p.get("nome") or "").lower()
        if palavras and all(w in nome for w in palavras):
            saida.append({"fonte": p.get("loja") or "Awin", "nome": p["nome"][:70],
                          "preco": float(p["preco"]), "vendas": 0, "link": p["link"]})
    return sorted(saida, key=lambda x: x["preco"])[:5]


PERGUNTA_JUIZ = (
    "Alguem procurou \"{termo}\" numa loja. Abaixo, candidatos numerados. "
    "Responda SO' com os numeros dos que SAO esse produto (o item em si, "
    "novo), separados por virgula. Exclua acessorio, capa, cabo, peca, "
    "suporte, adesivo, livro ou qualquer coisa PARA o produto em vez do "
    "produto. Se nenhum for, responda 0." + chr(10) + chr(10) + "{lista}"
)


def pertinentes(termo: str, achados: list[dict]) -> tuple[list[dict], bool]:
    """(os que SAO o produto, julgado?). Sem modelo, devolve todos e False.

    ⛔ O DEFEITO QUE ISTO CONSERTA, medido em 16/09/2026: "macbook" voltou
    "com fonte" — capa de teclado, hub USB e capa de notebook. Acessorio
    PARA o produto nao e' o produto, e chamar isso de atendido e' o erro a
    nosso favor que ninguem reclama: o amigo do Bryan entra, ve' uma capa e
    sai. A busca por texto sempre traz o acessorio junto (e' mais barato e
    tem mais vendedor); quem separa e' o juiz.

    ⚠️ "Nao julgado" e' um estado, nao um sim: quem chama mostra os achados
    com o aviso, e NAO marca a busca como atendida por cima dele.
    """
    if not achados:
        return [], True
    from . import modelo_texto
    lista = chr(10).join(f"{i+1}. {a['nome'][:90]}" for i, a in enumerate(achados))
    texto = modelo_texto.perguntar(PERGUNTA_JUIZ.format(termo=termo, lista=lista))
    if texto is None:
        return achados, False
    import re as _re
    nums = {int(n) for n in _re.findall(r"\d+", texto)}
    return [a for i, a in enumerate(achados) if (i + 1) in nums], True


def procurar(termo: str, canal: str = "") -> tuple[list[dict], list[str], bool]:
    """(achados que SAO o produto, fontes que FALHARAM, julgado?).

    Falha de fonte nao e' ausencia; achado sem juiz nao e' atendimento.
    """
    achados, falhas = [], []
    for nome, fn in (("AliExpress", lambda: _aliexpress(termo, canal)),
                     ("Mercado Livre", lambda: _mercadolivre(termo, canal)),
                     ("Awin", lambda: _awin(termo))):
        try:
            achados += fn()
        except Exception as e:                       # noqa: BLE001
            falhas.append(f"{nome}: {type(e).__name__} {str(e)[:60]}")
    achados, julgado = pertinentes(termo, achados)
    return achados, falhas, julgado


def atender(dias: int = 7, canal: str = "") -> list[dict]:
    """Passa por cada busca pendente. Devolve o relato (um dict por termo)."""
    relato = []
    for b in pendentes(dias):
        termo = b["termo"]
        achados, falhas, julgado = procurar(termo, canal)
        linha = {"termo": termo, "vezes": b["vezes"], "achados": achados,
                 "falhas": falhas, "ids": b["ids"], "julgado": julgado}
        if achados and julgado:
            linha["estado"] = "com fonte"
        elif achados:
            linha["estado"] = "pendente (achados SEM juiz — conferir a mao)"
        elif falhas or not julgado:
            # ⚠️ fica pendente: nao sabemos, e "nao sei" nao vira "nao existe"
            linha["estado"] = "pendente (fonte fora do ar)"
        else:
            linha["estado"] = "sem fonte"
            marcar(b["ids"], "sem_fonte", "nenhuma das 3 fontes")
            SEM_FONTE.parent.mkdir(parents=True, exist_ok=True)
            with SEM_FONTE.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"termo": termo, "vezes": b["vezes"],
                                    "quando": date.today().isoformat()},
                                   ensure_ascii=False) + "\n")
        relato.append(linha)
    return relato


def fechamento(dias: int = 1) -> str:
    """O bloco do fim do dia: o que procuraram, o que faltou, o que nao tem
    fonte. Texto pronto pro Telegram/handoff."""
    tot = _sql("select count(*) as buscas, count(distinct lower(trim(termo))) as termos, "
               "sum(case when resultados = 0 then 1 else 0 end) as vazias "
               "from busca where quando > now() - make_interval(days => "
               + str(int(dias)) + ") and nota is distinct from 'TESTE'")[0]
    top = _sql("select lower(trim(termo)) as termo, count(*) as vezes, "
               "min(resultados) as res, max(atendida) as atendida "
               "from busca where quando > now() - make_interval(days => "
               + str(int(dias)) + ") and nota is distinct from 'TESTE' "
               "group by 1 order by vezes desc limit 15")
    linhas = [f"BUSCAS NO SITE — ultimas {dias*24}h",
              f"  {tot['buscas'] or 0} buscas · {tot['termos'] or 0} termos · "
              f"{tot['vazias'] or 0} sem resultado"]
    for t in top:
        marca = ("SEM FONTE" if t["atendida"] == "sem_fonte"
                 else "publicada" if t["atendida"] == "publicada"
                 else "vazia" if (t["res"] or 0) == 0 else f"{t['res']} na tela")
        linhas.append(f"  {t['vezes']:>3}x  {t['termo'][:40]:40} {marca}")
    return "\n".join(linhas)


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="buscas do site: pendentes, atender, fechamento")
    a.add_argument("--pendentes", action="store_true", help="so' lista o que falta olhar")
    a.add_argument("--atender", action="store_true", help="procura fonte pra cada pendente")
    a.add_argument("--fechamento", action="store_true", help="o bloco do fim do dia")
    a.add_argument("--dias", type=int, default=7)
    a.add_argument("--canal", default="")
    o = a.parse_args()
    if o.fechamento:
        print(fechamento(max(1, min(o.dias, 30)) if o.dias != 7 else 1))
        return
    if o.atender:
        for r in atender(o.dias, o.canal):
            print(f"\n{r['vezes']}x {r['termo']!r} — {r['estado']}")
            for x in r["achados"][:6]:
                print(f"   R$ {x['preco']:>8.2f}  {x['fonte']:13} {x['nome'][:52]}")
                print(f"              {x['link'][:100]}")
            for f in r["falhas"]:
                print(f"   [!] {f}")
        return
    for b in pendentes(o.dias):
        print(f"{b['vezes']:>3}x  {b['termo']}")


if __name__ == "__main__":
    main()
