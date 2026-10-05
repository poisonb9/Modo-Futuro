"""Cupons e promocoes ativas das lojas parceiras -> pagina /cupons.

⭐ 05/10/2026 (dono: "cupons atualizados no site — algo a mais que podemos
ofertar"; "de 3 em 3 horas se nao consumir nada").

Fontes (APIs gratuitas, zero token de IA):
- Awin `POST /publisher/{id}/promotions` — lojas em que somos afiliados, BR.
  Link = `urlTracking` (ja' com nosso id).
- AliExpress `hotproduct.query` — `promo_code_info` = cupom da LOJA dentro do
  Ali (codigo, valor, compra minima, validade). Link = `promotion_link`.

Atualizacao de 3 em 3 h SEM republicar o site: o upload do Pages substitui o
diretorio inteiro (~20 min por publicacao). Entao `cupons.yml` (GitHub, a cada
3 h) grava `estado/cupons.json` no repo publico, e a pagina /cupons le' esse
arquivo ao abrir (raw.githubusercontent). Os dados embutidos na pagina sao so'
o fallback de quando o GitHub nao responde.

Uso: python -X utf8 -m engine.cupons --gravar
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "estado" / "cupons.json"
FONTE_VIVA = "https://raw.githubusercontent.com/poisonb9/Modo-Futuro/main/estado/cupons.json"
_memo: list | None = None


def _awin() -> list[dict]:
    tok, pub = os.getenv("AWIN_TOKEN"), os.getenv("AWIN_PUBLISHER_ID")
    if not (tok and pub):
        raise RuntimeError("sem AWIN_TOKEN/AWIN_PUBLISHER_ID")
    todos, pg = [], 1
    while pg < 20:
        r = requests.post(
            f"https://api.awin.com/publisher/{pub}/promotions",
            headers={"Authorization": f"Bearer {tok}"},
            json={"filters": {"membership": "joined", "status": "active",
                              "type": "all", "regionCodes": ["BR"]},
                  "pagination": {"page": pg, "pageSize": 200}}, timeout=60)
        r.raise_for_status()
        lote = r.json().get("data", [])
        todos += lote
        if len(lote) < 200:
            break
        pg += 1
    return [{"loja": x["advertiser"]["name"].replace(" BR & LATAM", "").replace(" BR", ""),
             "tipo": x.get("type"), "titulo": (x.get("title") or "").strip(),
             "codigo": (x.get("voucher") or {}).get("code") or "",
             "fim": x.get("endDate") or "", "link": x.get("urlTracking") or x.get("url") or "",
             "termos": (x.get("terms") or "").strip(" .")} for x in todos]


def _brl(v: str) -> str:
    return "R$ " + f"{float(v):.2f}".replace(".", ",")


def _ali(paginas: int = 6) -> list[dict]:
    """Cupons de loja do AliExpress, 1 por (loja, codigo)."""
    from engine import aliexpress as a
    a.TIMEOUT_S = max(a.TIMEOUT_S, 90)
    vistos, saida = set(), []
    for pg in range(1, paginas + 1):
        try:
            r = a.chamar("aliexpress.affiliate.hotproduct.query", target_currency="BRL",
                         target_language="PT", ship_to_country="BR", page_size="50",
                         page_no=str(pg), sort="LAST_VOLUME_DESC")
        except Exception as e:
            print(f"  [!] ali pagina {pg}: {str(e)[:60]}")
            continue
        ps = (r.get("aliexpress_affiliate_hotproduct_query_response", {}).get("resp_result", {})
              .get("result", {}).get("products", {}).get("product", []))
        for p in ps:
            c = p.get("promo_code_info") or {}
            cod = c.get("promo_code")
            if not cod or (p.get("shop_id"), cod) in vistos:
                continue
            vistos.add((p.get("shop_id"), cod))
            m = re.search(r"over BRL ([\d.]+)\s*,\s*get BRL ([\d.]+) off", c.get("code_value", ""))
            titulo = (f"{_brl(m.group(2))} OFF acima de {_brl(m.group(1))}" if m
                      else c.get("code_value", "cupom da loja"))
            fim = c.get("code_availabletime_end", "")
            try:  # horario de Pequim (UTC+8) -> ISO UTC
                fim = (dt.datetime.strptime(fim, "%Y-%m-%d %H:%M:%S")
                       - dt.timedelta(hours=8)).replace(tzinfo=dt.timezone.utc).isoformat()
            except ValueError:
                fim = ""
            saida.append({"loja": f"AliExpress · {p.get('shop_name') or 'loja'}"[:60],
                          "tipo": "voucher", "titulo": titulo, "codigo": cod, "fim": fim,
                          "link": p.get("promotion_link") or p.get("product_detail_url") or "",
                          "termos": f"Vale na loja {p.get('shop_name') or ''} do AliExpress. "
                                    f"Ex.: {(p.get('product_title') or '')[:70]}"})
    return saida


def baixar() -> list[dict]:
    lista, erros = [], []
    for nome, f in (("Awin", _awin), ("AliExpress", _ali)):
        try:
            lista += f()
        except Exception as e:
            erros.append(f"{nome}: {str(e)[:60]}")
    if erros:
        print("  [!] cupons:", "; ".join(erros))
    if not lista:
        raise RuntimeError("nenhuma fonte respondeu")
    return lista


def cupons() -> list[dict]:
    """Ativos agora, cupom com codigo primeiro, depois quem vence antes."""
    global _memo
    if _memo is None:
        try:
            _memo = baixar()
            CACHE.write_text(json.dumps(_memo, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as e:
            print(f"  [!] cupons: fontes falharam ({str(e)[:70]}) — usando o ultimo bom")
            _memo = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else []
    agora = dt.datetime.now(dt.timezone.utc).isoformat()
    vivos = [c for c in _memo if c["link"] and (not c["fim"] or c["fim"] > agora)]
    return sorted(vivos, key=lambda c: (not c["codigo"], c["fim"] or "9"))


DOMINIO = "https://achadinhototal.com.br"
MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")


def grupo(loja: str) -> str:
    return "AliExpress" if loja.lower().startswith("aliexpress") else loja


def slug(loja: str) -> str:
    from engine.alertas import slug_loja
    return slug_loja(loja)


def lojas() -> dict[str, tuple[str, int]]:
    """{slug: (nome da loja, quantos cupons ativos)} — mais cupons primeiro."""
    cont: dict[str, list] = {}
    for c in cupons():
        g = grupo(c["loja"])
        cont.setdefault(slug(g), [g, 0])[1] += 1
    return {k: (v[0], v[1]) for k, v in sorted(cont.items(), key=lambda kv: -kv[1][1])}


def pagina_html(loja_slug: str | None = None, bot: str = "") -> str:
    """/cupons/ (todas) ou /cupons/<slug>/ (uma loja, ja' filtrada).

    ⭐ 05/10/2026 (plano do site que vende, frente 1c + 2): cada loja ganha
    pagina propria para o Google ("cupom kabum" e' busca de quem esta' pronto
    para comprar) e a lista VIP "receba antes de todo mundo" (Telegram/e-mail).
    ⛔ Pagina so' existe para loja com cupom ATIVO — sem cupom, sem pagina
    (nada de pagina vazia para o Google punir como conteudo fino)."""
    lista = cupons()
    todas = lojas()
    hoje = dt.date.today()
    mes = f"{MESES[hoje.month - 1]} de {hoje.year}"
    if loja_slug:
        nome, n = todas[loja_slug]
        com_cod = sum(1 for c in lista if slug(grupo(c["loja"])) == loja_slug and c["codigo"])
        titulo = f"Cupom {nome} hoje: {n} {'cupom' if n == 1 else 'cupons'} conferidos ({mes})"
        desc = (f"{n} cupons e promoções da {nome} ativos agora"
                + (f", {com_cod} com código" if com_cod else "")
                + ". Conferidos de hora em hora — copie o código e vá direto para a loja.")
        h1 = f"Cupons da <em>{html.escape(nome)}</em>"
        sub = (f"Os cupons ativos da {html.escape(nome)} agora, conferidos de hora em hora. "
               "Copie o código e vá direto para a loja.")
        canon = f"{DOMINIO}/cupons/{loja_slug}/"
        filtro, vip_loja = nome, f"da {html.escape(nome)}"
    else:
        n = len(lista)
        titulo = f"Cupons de desconto hoje: {n} cupons de {len(todas)} lojas ({mes})"
        desc = (f"{n} cupons e promoções ativas de {len(todas)} lojas, conferidos de hora em hora. "
                "Kabum, Arno, AliExpress, Nike e mais.")
        h1 = "Cupons de <em>desconto</em>"
        sub = "Os cupons ativos das lojas parceiras, num lugar só. Copie o código e vá direto para a loja."
        canon = f"{DOMINIO}/cupons/"
        filtro, vip_loja = "", "das lojas"
    links = "".join(
        f'<a href="/cupons/{s}/"{" aria-current=page" if s == loja_slug else ""}>'
        f'Cupom {html.escape(nm)} <small>({q})</small></a>' for s, (nm, q) in todas.items())
    trilha = [{"@type": "ListItem", "position": 1, "name": "Achadinho Total", "item": DOMINIO + "/"},
              {"@type": "ListItem", "position": 2, "name": "Cupons", "item": DOMINIO + "/cupons/"}]
    if loja_slug:
        trilha.append({"@type": "ListItem", "position": 3, "name": f"Cupom {todas[loja_slug][0]}", "item": canon})
    ld = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
                     "itemListElement": trilha}, ensure_ascii=False).replace("</", "<\\/")
    dados = json.dumps(lista, ensure_ascii=False).replace("</", "<\\/")
    esc = lambda t: html.escape(t, quote=True)
    return (PAGINA.replace("__TITULO__", esc(titulo)).replace("__DESC__", esc(desc))
            .replace("__CANON__", canon).replace("__LDJSON__", ld)
            .replace("__H1__", h1).replace("__SUB__", sub).replace("__VIP_LOJA__", vip_loja)
            .replace("__LINKS__", links).replace("__FILTRO__", filtro.replace('"', ""))
            .replace("__BOT__", re.sub(r"[^A-Za-z0-9_]", "", bot or ""))
            .replace("__DADOS__", dados).replace("__FONTE__", FONTE_VIVA))


PAGINA = (RAIZ / "engine" / "cupons_pagina.html").read_text(encoding="utf-8")


if __name__ == "__main__":
    import sys
    if "--gravar" in sys.argv:
        try:
            from dotenv import load_dotenv
            load_dotenv(RAIZ / ".env")
        except ImportError:
            pass
        lista = baixar()
        CACHE.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(lista)} cupons gravados ({sum(1 for c in lista if c['loja'].startswith('AliExpress'))} do AliExpress)")
