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


PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cupons de desconto — Achadinho Total</title>
<meta name="description" content="Cupons e promoções ativas das lojas parceiras, conferidos de hora em hora.">
<link rel="icon" href="/icone.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--tinta:#14131a;--suave:#6b6878;--fundo:#faf8f3;--caixa:#fff;--ouro:#e7c35a;--linha:#ece7da}
*{box-sizing:border-box}body{margin:0;background:var(--fundo);color:var(--tinta);font:15px/1.45 Poppins,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 80px}
.topo a{color:var(--suave);text-decoration:none;font-size:14px}
h1{font-size:clamp(26px,5vw,38px);margin:10px 0 4px}.sub{color:var(--suave);margin:0 0 18px}
.filtros{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.f{border:1px solid var(--linha);background:var(--caixa);border-radius:999px;padding:7px 14px;font:500 13.5px Poppins,sans-serif;cursor:pointer;color:var(--tinta)}
.f[aria-pressed=true]{background:var(--tinta);color:#fff;border-color:var(--tinta)}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
article{background:var(--caixa);border:1px solid var(--linha);border-radius:18px;padding:16px;display:flex;flex-direction:column;gap:10px}
article header{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:13px}
article i{font-style:normal;color:var(--suave);white-space:nowrap}article i.urg{color:#c0392b;font-weight:600}
h2{font-size:16px;margin:0;line-height:1.3}
.cod{display:flex;justify-content:space-between;align-items:center;border:2px dashed var(--ouro);background:#fffaf0;border-radius:12px;padding:10px 12px;font:700 16px ui-monospace,monospace;letter-spacing:.5px;cursor:pointer;color:var(--tinta)}
.cod span{font:500 12px Poppins,sans-serif;color:var(--suave)}.cod.ok span{color:#1e8449}
.sem{font-size:13px;color:var(--suave)}.t{font-size:12px;color:var(--suave);margin:0}
article a{margin-top:auto;text-align:center;background:var(--tinta);color:#fff;text-decoration:none;border-radius:12px;padding:10px;font-weight:600}
footer{color:var(--suave);font-size:12px;margin-top:26px;text-align:center}footer a{color:inherit}
</style>
<main>
<div class="topo"><a href="/">← Achadinho Total</a></div>
<h1>Cupons de desconto</h1>
<p class="sub" id="sub"></p>
<div class="filtros" id="filtros"></div>
<div class="grade" id="grade"></div>
<footer>Os links são de afiliado: a loja nos paga uma comissão e você não paga nada a mais. Cupons podem acabar antes do prazo. <a href="/privacidade">Privacidade</a></footer>
</main>
<script>
(function(){
var DADOS=__DADOS__, filtro="";
function ev(n,p){try{if(localStorage.getItem("nao_contar")==="1"){window.posthog&&posthog.opt_out_capturing();return}window.posthog&&posthog.capture(n,p||{})}catch(e){}}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function validade(fim){if(!fim)return"";var f=new Date(fim),h=new Date();
 var d=Math.round((new Date(f.toDateString())-new Date(h.toDateString()))/864e5);
 return d<=0?"vence hoje":d===1?"vence amanhã":"até "+f.toLocaleDateString("pt-BR",{day:"2-digit",month:"2-digit"})}
function grupo(l){return l.indexOf("AliExpress")===0?"AliExpress":l}
function desenhar(lista){
 var agora=new Date().toISOString();
 lista=lista.filter(function(c){return c.link&&(!c.fim||c.fim>agora)})
  .sort(function(a,b){return (!a.codigo)-(!b.codigo)||String(a.fim||"9").localeCompare(String(b.fim||"9"))});
 document.getElementById("sub").textContent=lista.length+" cupons e promoções ativos nas lojas parceiras · atualizado de hora em hora";
 var lojas={};lista.forEach(function(c){lojas[grupo(c.loja)]=(lojas[grupo(c.loja)]||0)+1});
 var fs=document.getElementById("filtros");fs.innerHTML="";
 [""].concat(Object.keys(lojas).sort()).forEach(function(l){
  var b=el("button","f",l?l+" "+lojas[l]:"Todas");b.setAttribute("aria-pressed",l===filtro);
  b.onclick=function(){filtro=l;desenhar(lista);ev("cupom_filtro",{loja:l})};fs.appendChild(b)});
 var g=document.getElementById("grade");g.innerHTML="";
 lista.filter(function(c){return !filtro||grupo(c.loja)===filtro}).forEach(function(c){
  var a=el("article"),h=el("header"),v=validade(c.fim);
  h.appendChild(el("b",null,c.loja));h.appendChild(el("i",v.indexOf("vence")===0?"urg":"",v));a.appendChild(h);
  a.appendChild(el("h2",null,c.titulo));
  if(c.codigo){var b=el("button","cod",c.codigo);var s=el("span",null,"copiar");b.appendChild(s);
   b.onclick=function(){try{navigator.clipboard.writeText(c.codigo)}catch(e){}b.classList.add("ok");s.textContent="copiado ✓";ev("cupom_copiado",{codigo:c.codigo,loja:c.loja})};a.appendChild(b)}
  else a.appendChild(el("span","sem","sem código — o desconto já vem no link"));
  if(c.termos&&c.termos.length>3)a.appendChild(el("p","t",c.termos.slice(0,160)));
  var k=el("a",null,"Ir para a loja →");k.href=c.link;k.target="_blank";k.rel="sponsored noopener";
  k.onclick=function(){ev("cupom_clique",{loja:c.loja})};a.appendChild(k);g.appendChild(a)});
 if(!g.children.length)g.appendChild(el("p",null,"Nenhum cupom ativo agora — volte daqui a pouco."));
}
desenhar(DADOS);
fetch("__FONTE__?t="+Date.now()).then(function(r){return r.ok?r.json():null}).then(function(d){if(d&&d.length)desenhar(d)}).catch(function(){});
})();
</script>
</html>
"""


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
