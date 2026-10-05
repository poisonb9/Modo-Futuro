"""Relatório SEMANAL do Google (e do site) no Telegram do dono.

⭐ 05/10/2026 (dono: "pode montar um relatório semanal para avaliarmos").
Roda toda segunda no GitHub Actions (.github/workflows/relatorio_seo.yml).

O que mede:
1. O MAPA no ar: quantos endereços no sitemap (/p/, /melhores/, /cupons/...).
2. SAÚDE: amostra de 25 endereços do mapa — todos têm de responder 200.
3. GOOGLE (Search Console), se o segredo GSC_CREDENCIAIS existir (conta de serviço
   adicionada como usuária da propriedade): cliques, impressões, posição média,
   CTR dos últimos 7 dias contra os 7 anteriores; top 10 buscas e top 10 páginas;
   e as páginas com MUITA impressão e POUCO clique (onde melhorar título/descrição).
   Sem o segredo, o relatório diz o que falta em vez de inventar número.
4. CLIQUES PARA AS LOJAS (Supabase), quando der para ler.

Uso: python ferramentas/relatorio_seo.py [--simular]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import re
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
DOMINIO = "https://achadinhototal.com.br"
PROPRIEDADE = "sc-domain:achadinhototal.com.br"


def mapa() -> list[str]:
    xml = requests.get(DOMINIO + "/sitemap.xml", timeout=60).text
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def saude(urls: list[str], n: int = 25) -> list[str]:
    ruins = []
    for u in random.sample(urls, min(n, len(urls))):
        try:
            c = requests.get(u, timeout=40).status_code
        except Exception as e:                            # noqa: BLE001
            c = str(e)[:30]
        if c != 200:
            ruins.append(f"{c} {u.replace(DOMINIO, '')}")
    return ruins


def _gsc():
    cred = os.environ.get("GSC_CREDENCIAIS", "").strip()
    if not cred:
        return None
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    info = json.loads(cred)
    c = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    return build("searchconsole", "v1", credentials=c, cache_discovery=False)


def _consulta(sc, ini: dt.date, fim: dt.date, dims: list[str], n: int = 10) -> list[dict]:
    r = sc.searchanalytics().query(siteUrl=PROPRIEDADE, body={
        "startDate": ini.isoformat(), "endDate": fim.isoformat(),
        "dimensions": dims, "rowLimit": n}).execute()
    return r.get("rows") or []


def google() -> list[str]:
    sc = _gsc()
    if sc is None:
        return ["⚠️ Search Console ainda NÃO conectado (falta o segredo GSC_CREDENCIAIS).",
                "Passo a passo em handoff/PLANO_SITE_VENDAS_2026.md, seção 5."]
    fim = dt.date.today() - dt.timedelta(days=3)          # o GSC atrasa ~2-3 dias
    ini = fim - dt.timedelta(days=6)
    ant_fim, ant_ini = ini - dt.timedelta(days=1), ini - dt.timedelta(days=7)
    tot = (_consulta(sc, ini, fim, []) or [{}])[0]
    ant = (_consulta(sc, ant_ini, ant_fim, []) or [{}])[0]

    def linha(nome, k, fmt):
        a, b = tot.get(k, 0), ant.get(k, 0)
        seta = "↑" if a > b else ("↓" if a < b else "=")
        return f"{nome}: {fmt(a)} ({seta} antes {fmt(b)})"
    out = [f"GOOGLE ({ini:%d/%m}–{fim:%d/%m})",
           linha("Cliques", "clicks", lambda v: f"{v:.0f}"),
           linha("Impressões", "impressions", lambda v: f"{v:.0f}"),
           linha("CTR", "ctr", lambda v: f"{v * 100:.1f}%"),
           linha("Posição média", "position", lambda v: f"{v:.1f}")]
    q = _consulta(sc, ini, fim, ["query"])
    if q:
        out.append("\nTop buscas:")
        out += [f"• {r['keys'][0]} — {r['clicks']:.0f} cl / {r['impressions']:.0f} imp / pos {r['position']:.0f}" for r in q]
    pg = _consulta(sc, ini, fim, ["page"], 200)
    if pg:
        out.append("\nTop páginas:")
        out += [f"• {r['keys'][0].replace(DOMINIO, '')} — {r['clicks']:.0f} cl / {r['impressions']:.0f} imp" for r in pg[:10]]
        mel = [r for r in pg if r["impressions"] >= 50 and r["ctr"] < 0.02][:5]
        if mel:
            out.append("\nMuita gente vê e pouca clica (melhorar título/descrição):")
            out += [f"• {r['keys'][0].replace(DOMINIO, '')} — {r['impressions']:.0f} imp, CTR {r['ctr'] * 100:.1f}%" for r in mel]
    try:
        sm = sc.sitemaps().get(siteUrl=PROPRIEDADE, feedpath=DOMINIO + "/sitemap.xml").execute()
        for c in sm.get("contents") or []:
            out.append(f"\nSitemap: {c.get('submitted')} enviados · {c.get('indexed', '?')} indexados (dado do Google)")
    except Exception:                                     # noqa: BLE001
        pass
    return out


def cliques() -> list[str]:
    try:
        from engine import cliques as _cl
        d = _cl.por_produto(7)
        tot = sum(v["cliques"] for v in d.values())
        return [f"CLIQUES PARA AS LOJAS (7 dias): {tot} em {len(d)} produtos"]
    except Exception as e:                                # noqa: BLE001
        return [f"(cliques para as lojas: não li — {str(e)[:60]})"]


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--simular", action="store_true")
    a = a.parse_args()
    urls = mapa()
    tipos = {"/p/": 0, "/melhores/": 0, "/cupons/": 0, "/top10/": 0}
    for u in urls:
        for t in tipos:
            if u.replace(DOMINIO, "").startswith(t):
                tipos[t] += 1
    ruins = saude(urls)
    partes = [f"📈 RELATÓRIO SEMANAL DO SITE — {dt.date.today():%d/%m/%Y}",
              f"MAPA NO AR: {len(urls)} endereços · " + " · ".join(f"{k} {v}" for k, v in tipos.items()),
              "SAÚDE: 25 endereços testados, " + ("todos 200 ✅" if not ruins else f"{len(ruins)} com problema ❌\n" + "\n".join(ruins)),
              ""] + google() + [""] + cliques()
    msg = "\n".join(partes)
    print(msg)
    if not a.simular:
        from engine import telegram
        print("telegram:", telegram.enviar(msg[:telegram.LIMITE_MSG]))


if __name__ == "__main__":
    main()
