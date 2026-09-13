# -*- coding: utf-8 -*-
"""Shein: garimpo por navegador, porque a API interna e' assinada.

    python -m engine.shein --termo batom --quantos 8

## ⚠️ POR QUE NAVEGADOR, E NAO REQUISICAO HTTP

Medido em 13/09/2026, nesta ordem:

    GET  br.shein.com/pdsearch/<termo>        200, mas SEM produto no HTML
                                              (a lista e' montada por JS)
    POST /bff-api/product/get_products_by_...  403  (antibot na busca)
    POST /bff-api/category/get_select_prod...  200 no navegador,
                                              `code 836000` fora dele

A API interna existe e e' ASSINADA: ela quer cabecalhos de antibot que o
navegador gera. Reverter isso seria (a) fragil, porque a assinatura muda
quando eles quiserem, e (b) uma corrida que a gente perde. Navegador de
verdade le' a mesma pagina que qualquer pessoa ve', e nao quebra quando eles
trocarem o esquema de assinatura.

⚠️ E ISSO CUSTA: cada rodada abre um Chromium. Na nuvem tudo bem (o runner
tem folga); na maquina local NAO — ela ja' nao da' conta do que roda hoje.

## ⚠️ O LINK DE AFILIADO DA SHEIN NAO SE MONTA

Medido com dois links gerados pelo conversor deles:

    onelink.shein.com/52/61uhzk2hpbn5?ismg_ol=8Eq59aLMCJn_01_KOC-C
    onelink.shein.com/52/61ui0lk2vrpp?ismg_ol=5RaUjw3KPOC_01_KOC-C

FIXO: o `/52/` e o sufixo `_01_KOC-C` (KOC = o programa de criadores).
MUDA:  o codigo curto e o prefixo do `ismg_ol` — os dois nascem no servidor.

Entao este modulo entrega o produto e o **codigo** (o numero depois do `-p-`),
que e' o que o conversor deles aceita. A conversao continua sendo um passo do
Bryan — e' honesto dizer isso em vez de inventar um link que abre a pagina e
nao paga nada.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

BUSCA = "https://br.shein.com/pdsearch/{termo}/?sort=7"   # sort=7 = popular

# canal interno -> o que procurar la'.
#
# ⚠️ A SHEIN NAO SERVE A TODOS OS CANAIS. Ela e' moda, beleza e casa; nao tem
# eletronico nem suplemento que preste. Canal que nao esta' aqui simplesmente
# nao garimpa nela — melhor do que devolver lixo pra preencher lista.
TERMOS = {
    "truque.importado": ["batom", "pincel maquiagem", "paleta sombra",
                         "skincare", "perfume"],
    "cozinha.importada": ["utensilio cozinha", "organizador cozinha"],
    "achadinhos.instantaneos": ["organizador", "acessorio casa"],
}

# ⚠️ "(1000+)" e' como a Shein mostra vendas. O `+` importa: 1000+ nao e' 1000,
# e tratar como numero exato inventa precisao que o dado nao tem.
_VENDAS = re.compile(r"\((\d+)\+?\)")
_PRECO = re.compile(r"R\$\s*([\d.]+,\d{2})")
_DESC = re.compile(r"-(\d+)%")
_CODIGO = re.compile(r"-p-(\d+)")


def ler_cartao(texto: str, href: str) -> dict | None:
    """Um cartao de produto da busca vira produto nosso, ou None.

    ⚠️ SEPARADA DO NAVEGADOR DE PROPOSITO. E' aqui que mora a interpretacao do
    texto, e e' o unico pedaco testavel sem abrir Chromium. Misturar leitura de
    pagina com leitura de texto faria a guarda depender de rede.
    """
    if not href:
        return None
    cod = _CODIGO.search(href)
    preco = _PRECO.search(texto or "")
    if not (cod and preco):
        return None
    vendas = _VENDAS.search(texto or "")
    desconto = _DESC.search(texto or "")
    linhas = [l.strip() for l in (texto or "").splitlines() if l.strip()]
    # o nome e' a linha mais longa: marca e preco sao curtos
    nome = max(linhas, key=len) if linhas else ""
    return {
        "nome": nome,
        "codigo": cod.group(1),
        # ⚠️ LINK CRU, e nao de afiliado. O de afiliado so' sai do conversor
        # deles. Devolver este como se pagasse seria o erro caro.
        "link_cru": href.split("?")[0],
        "preco": "R$ " + preco.group(1),
        "loja": "Shein",
        "_desconto_loja": int(desconto.group(1)) if desconto else 0,
        "_vendas": int(vendas.group(1)) if vendas else 0,
        "fonte": "shein",
    }


def buscar(termo: str, quantos: int = 10) -> list[dict]:
    """Abre a busca num Chromium e le' os cartoes."""
    from playwright.sync_api import sync_playwright

    url = BUSCA.format(termo=termo.replace(" ", "%20"))
    achados: list[dict] = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--no-sandbox"])
        pag = nav.new_page(locale="pt-BR", user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"))
        try:
            pag.goto(url, wait_until="domcontentloaded", timeout=60000)
            # ⚠️ ESPERA O CARTAO, nao um tempo fixo. `sleep(5)` passa em rede
            # boa e falha calado em rede ruim — e falhar calado aqui devolve
            # lista vazia, que parece "nao achou nada".
            try:
                pag.wait_for_selector("a[href*='-p-']", timeout=45000)
            except Exception:
                # ⚠️ NAO ENGOLIR O TIMEOUT. "Nao achou produto" e "fui
                # barrado" sao coisas diferentes e a lista vazia parece a
                # mesma coisa nas duas. Sem isto, uma tarde se perde achando
                # que o seletor mudou quando o que houve foi bloqueio.
                print(f"  [!] nao apareceu produto em {pag.url}")
                print(f"      titulo: {pag.title()!r}")
                txt = (pag.inner_text("body") or "")[:400]
                print("      corpo: " + txt.replace(chr(10), " | "))
                raise
            pag.wait_for_timeout(2500)
            cartoes = pag.query_selector_all(
                "section [class*=product-card], div[class*=product-card]")
            vistos = set()
            for c in cartoes:
                try:
                    a = c.query_selector("a[href*='-p-']")
                    if not a:
                        continue
                    p = ler_cartao(c.inner_text(), a.get_attribute("href") or "")
                except Exception:
                    continue
                if not p or p["codigo"] in vistos:
                    continue
                vistos.add(p["codigo"])
                achados.append(p)
                if len(achados) >= quantos:
                    break
        finally:
            nav.close()
    return achados


def do_canal(canal: str, por_termo: int = 6) -> list[dict]:
    saida, vistos = [], set()
    for termo in TERMOS.get(canal, []):
        for p in buscar(termo, por_termo):
            if p["codigo"] not in vistos:
                vistos.add(p["codigo"])
                saida.append(p)
    return saida


def main() -> None:
    a = argparse.ArgumentParser(description="garimpo da Shein")
    a.add_argument("--termo")
    a.add_argument("--canal", choices=sorted(TERMOS))
    a.add_argument("--quantos", type=int, default=8)
    o = a.parse_args()
    achados = (do_canal(o.canal) if o.canal
               else buscar(o.termo or "batom", o.quantos))
    for p in achados:
        d = f" · -{p['_desconto_loja']}% (loja)" if p["_desconto_loja"] else ""
        v = f" · {p['_vendas']}+ vendidos" if p["_vendas"] else ""
        print(f"  {p['preco']:>11}{d}{v}")
        print(f"    {p['nome'][:70]}")
        print(f"    código p/ converter: {p['codigo']}")
    print(f"\n{len(achados)} produto(s)")
    # ⚠️ A LISTA DE CODIGOS SAI JUNTA, colavel de uma vez no conversor deles.
    # E' o que transforma "gerar na mao, um por um" em um Ctrl+V.
    if achados:
        print("\ncolar no conversor da Shein:")
        print("  " + "\n  ".join(p["codigo"] for p in achados))


if __name__ == "__main__":
    main()
