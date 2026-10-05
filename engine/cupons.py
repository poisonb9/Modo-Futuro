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


def pagina_html() -> str:
    dados = json.dumps(cupons(), ensure_ascii=False).replace("</", "<\\/")
    return PAGINA.replace("__DADOS__", dados).replace("__FONTE__", FONTE_VIVA)


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
