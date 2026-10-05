"""Cupons e promocoes ativas das lojas parceiras (Awin) -> pagina /cupons.

⭐ 05/10/2026 (dono: "cupons atualizados no site — algo a mais que podemos
ofertar"). Fonte: Awin `POST /publisher/{id}/promotions` (so' lojas em que
somos afiliados, ativas, Brasil). O link e' o `urlTracking` (ja' com nosso id).

⚠️ Falha da API nao derruba a publicacao: usa o ultimo bom de
`estado/cupons.json`, e cupom vencido e' filtrado na hora de montar.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "estado" / "cupons.json"
_memo: list | None = None


def _baixar() -> list[dict]:
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


def cupons() -> list[dict]:
    """Ativos agora, cupom com codigo primeiro, depois quem vence antes."""
    global _memo
    if _memo is None:
        try:
            _memo = _baixar()
            CACHE.write_text(json.dumps(_memo, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as e:
            print(f"  [!] cupons: Awin falhou ({str(e)[:70]}) — usando o ultimo bom")
            _memo = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else []
    agora = dt.datetime.now(dt.timezone.utc).isoformat()
    vivos = [c for c in _memo if c["link"] and (not c["fim"] or c["fim"] > agora)]
    return sorted(vivos, key=lambda c: (not c["codigo"], c["fim"] or "9"))


def _validade(fim: str) -> str:
    if not fim:
        return ""
    f = dt.datetime.fromisoformat(fim).astimezone(dt.timezone(dt.timedelta(hours=-3)))
    dias = (f.date() - (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3)).date()).days
    if dias <= 0:
        return "vence hoje"
    if dias == 1:
        return "vence amanhã"
    return f"até {f:%d/%m}"


def pagina_html() -> str:
    lista = cupons()
    lojas = sorted({c["loja"] for c in lista})
    e = html.escape
    cards = []
    for c in lista:
        cod = (f'<button class="cod" data-c="{e(c["codigo"])}">{e(c["codigo"])}<span>copiar</span></button>'
               if c["codigo"] else '<span class="sem">sem código — o desconto já vem no link</span>')
        cards.append(
            f'<article data-l="{e(c["loja"])}"><header><b>{e(c["loja"])}</b>'
            f'<i class="{"urg" if "vence" in _validade(c["fim"]) else ""}">{e(_validade(c["fim"]))}</i></header>'
            f'<h2>{e(c["titulo"])}</h2>{cod}'
            + (f'<p class="t">{e(c["termos"][:160])}</p>' if len(c["termos"]) > 3 else "")
            + f'<a href="{e(c["link"])}" target="_blank" rel="sponsored noopener" data-loja="{e(c["loja"])}">Ir para a loja →</a></article>')
    chips = "".join(f'<button class="f" data-l="{e(l)}">{e(l)}</button>' for l in lojas)
    hoje = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3)).strftime("%d/%m %H:%M")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cupons de desconto — Achadinho Total</title>
<meta name="description" content="Cupons e promoções ativas das lojas parceiras, conferidos todo dia.">
<link rel="icon" href="/icone.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--tinta:#14131a;--suave:#6b6878;--fundo:#faf8f3;--caixa:#fff;--ouro:#e7c35a;--linha:#ece7da}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fundo);color:var(--tinta);font:15px/1.45 Poppins,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:24px 16px 80px}}
.topo a{{color:var(--suave);text-decoration:none;font-size:14px}}
h1{{font-size:clamp(26px,5vw,38px);margin:10px 0 4px}}.sub{{color:var(--suave);margin:0 0 18px}}
.filtros{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}}
.f{{border:1px solid var(--linha);background:var(--caixa);border-radius:999px;padding:7px 14px;font:500 13.5px Poppins;cursor:pointer;color:var(--tinta)}}
.f[aria-pressed=true]{{background:var(--tinta);color:#fff;border-color:var(--tinta)}}
.grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}}
article{{background:var(--caixa);border:1px solid var(--linha);border-radius:18px;padding:16px;display:flex;flex-direction:column;gap:10px}}
article header{{display:flex;justify-content:space-between;align-items:center;font-size:13px}}
article i{{font-style:normal;color:var(--suave)}}article i.urg{{color:#c0392b;font-weight:600}}
h2{{font-size:16px;margin:0;line-height:1.3}}
.cod{{display:flex;justify-content:space-between;align-items:center;border:2px dashed var(--ouro);background:#fffaf0;border-radius:12px;padding:10px 12px;font:700 16px ui-monospace,monospace;letter-spacing:.5px;cursor:pointer;color:var(--tinta)}}
.cod span{{font:500 12px Poppins;color:var(--suave)}}.cod.ok span{{color:#1e8449}}
.sem{{font-size:13px;color:var(--suave)}}.t{{font-size:12px;color:var(--suave);margin:0}}
article a{{margin-top:auto;text-align:center;background:var(--tinta);color:#fff;text-decoration:none;border-radius:12px;padding:10px;font-weight:600}}
footer{{color:var(--suave);font-size:12px;margin-top:26px;text-align:center}}
</style>
<main>
<div class="topo"><a href="/">← Achadinho Total</a></div>
<h1>Cupons de desconto</h1>
<p class="sub">{len(lista)} cupons e promoções ativos nas lojas parceiras · conferido em {hoje}</p>
<div class="filtros"><button class="f" data-l="" aria-pressed="true">Todas</button>{chips}</div>
<div class="grade">{"".join(cards) or "<p>Nenhum cupom ativo agora — volte amanhã.</p>"}</div>
<footer>Os links são de afiliado: a loja nos paga uma comissão e você não paga nada a mais. Cupons podem acabar antes do prazo. <a href="/privacidade">Privacidade</a></footer>
</main>
<script>
try{{if(localStorage.getItem("nao_contar")==="1"&&window.posthog){{posthog.opt_out_capturing()}}}}catch(e){{}}
document.querySelectorAll(".f").forEach(function(b){{b.onclick=function(){{
 document.querySelectorAll(".f").forEach(function(x){{x.setAttribute("aria-pressed",x===b)}});
 document.querySelectorAll("article").forEach(function(a){{a.hidden=!!b.dataset.l&&a.dataset.l!==b.dataset.l}});
 try{{posthog.capture("cupom_filtro",{{loja:b.dataset.l}})}}catch(e){{}}}}}});
document.querySelectorAll(".cod").forEach(function(b){{b.onclick=function(){{
 try{{navigator.clipboard.writeText(b.dataset.c)}}catch(e){{}}
 b.classList.add("ok");b.querySelector("span").textContent="copiado ✓";
 try{{posthog.capture("cupom_copiado",{{codigo:b.dataset.c,loja:b.closest("article").dataset.l}})}}catch(e){{}}}}}});
document.querySelectorAll("article a").forEach(function(a){{a.addEventListener("click",function(){{
 try{{posthog.capture("cupom_clique",{{loja:a.dataset.loja}})}}catch(e){{}}}})}});
</script>
</html>
"""
