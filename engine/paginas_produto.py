# -*- coding: utf-8 -*-
"""Páginas por produto (/p/<slug>/) e listas "Melhores X até R$ Y" (/melhores/).

⭐ 05/10/2026 — plano do site que vende (handoff/PLANO_SITE_VENDAS_2026.md, 1d e 1e).
Acervo (+acervo): site novo ranqueia com páginas que respondem a UMA busca de
quem quer comprar, com resposta direta de 2–3 frases no topo e tabela de dados.

⛔ GUARDA ANTI-PUNIÇÃO ("scaled content abuse"): só ganha página o produto com
DADO PRÓPRIO — ≥ 7 dias de histórico de preço que nós medimos, foto e link.
Lista "melhores" só sai com ≥ 5 itens. Remédio fica de fora (regra do dono).

⭐ PRODUTO QUE SUMIU NÃO VIRA 404: o registro `estado/paginas_produto.json`
guarda o último dado de cada página; quem saiu do catálogo continua no ar com
o aviso "não encontramos mais este preço" + parecidos (link quebrado pune).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REGISTRO = RAIZ / "estado" / "paginas_produto.json"
DOMINIO = "https://achadinhototal.com.br"
MAX_PAGINAS = 500
MIN_DIAS = 7
MIN_LISTA = 5
FAIXAS = (50, 100, 200, 300, 500, 1000)
MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")
REMEDIO_PALAVRAS = ("comprimido", "capsulas gelatinosas", "mg c/", "dipirona", "paracetamol",
                    "ibuprofeno", "losartana", "omeprazol", "antialerg", "xarope",
                    "bravecto", "nexgard", "simparic", "credeli", "vermifugo", "antipulga")
e = html.escape


# ---------------------------------------------------------------- utilidades
def _ascii(t: str) -> str:
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()


def slug_do(nome: str, pid) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", _ascii(nome)).strip("-")
    base = "-".join(base.split("-")[:9])[:64].strip("-") or "produto"
    return f"{base}-{hashlib.sha1(str(pid).encode()).hexdigest()[:6]}"


def _brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _num(preco) -> float:
    if isinstance(preco, (int, float)):
        return float(preco)
    s = re.sub(r"[^\d,\.]", "", str(preco or ""))
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _dm(dia: str) -> str:
    return f"{dia[8:10]}/{dia[5:7]}"


def _remedio(p: dict) -> bool:
    n = _ascii(p.get("nome", ""))
    if any(r in n for r in REMEDIO_PALAVRAS):
        return True
    try:
        from engine.ml_vitrine import _e_remedio
        return _e_remedio(p.get("nome", ""))
    except Exception:                                     # noqa: BLE001
        return False


def _slug_area(a: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _ascii(a)).strip("-") or "outros"


# ---------------------------------------------------------------- seleção
def escolher(cartoes: list[dict], por_dia: dict) -> list[dict]:
    """Os produtos que ganham página: ≥ 7 dias de série, foto, link, sem remédio.
    Mais dias de série primeiro (mais dado próprio), depois cliques e vendas."""
    vistos, out = set(), []
    por_dia = {str(k): v for k, v in por_dia.items()}   # ids do Ali vêm int na série e str no cartão
    for p in cartoes:
        pid = p.get("id")
        if pid in (None, "") or pid in vistos:
            continue
        dias = por_dia.get(str(pid)) or {}
        if len(dias) < MIN_DIAS or not p.get("imagem") or not p.get("link") or not p.get("nome"):
            continue
        if _num(p.get("preco")) <= 0 or _remedio(p):
            continue
        vistos.add(pid)
        # o preço de HOJE entra na série (senão "menor" pode ficar acima do preço atual)
        hoje = dt.date.today().isoformat()
        dias = dict(dias); dias[hoje] = min(dias.get(hoje, 1e12), _num(p.get("preco")))
        out.append((p, dias))
    out.sort(key=lambda t: (-min(len(t[1]), 60), -int(t[0].get("cliques_30") or 0),
                            -int(t[0].get("vendas") or 0)))
    return [dict(p, _dias=d, pg=slug_do(p["nome"], p["id"])) for p, d in out[:MAX_PAGINAS]]


def estatisticas(dias: dict, preco_hoje: float) -> dict:
    ks = sorted(dias)
    vals = [dias[k] for k in ks]
    ult30 = [dias[k] for k in ks[-30:]]
    menor = min(vals); maior = max(vals)
    media = sum(ult30) / len(ult30)
    return {"desde": ks[0], "n": len(ks), "menor": menor, "dia_menor": ks[vals.index(menor)],
            "maior": maior, "dia_maior": ks[vals.index(maior)], "media30": media,
            "vs_media": (preco_hoje / media - 1) * 100 if media else 0.0,
            "pontos": list(zip(ks, vals))}


def veredito(s: dict, preco: float) -> tuple[str, str]:
    """(selo curto, resposta direta de 2–3 frases) — 'É uma boa hora?'"""
    v = s["vs_media"]
    if preco <= s["menor"] * 1.005:
        return ("menor preço que já vimos",
                f"Sim. {_brl(preco)} é o menor preço que registramos em {s['n']} dias de acompanhamento "
                f"— {abs(v):.0f}% abaixo da média dos últimos 30 dias ({_brl(s['media30'])}).")
    if v <= -5:
        return (f"{abs(v):.0f}% abaixo da média",
                f"Sim, está bom. Hoje sai {abs(v):.0f}% abaixo da média de 30 dias ({_brl(s['media30'])}). "
                f"O menor que já vimos foi {_brl(s['menor'])} em {_dm(s['dia_menor'])}.")
    if v >= 5:
        return (f"{v:.0f}% acima da média",
                f"Melhor esperar. Hoje está {v:.0f}% acima da média de 30 dias ({_brl(s['media30'])}) "
                f"e já esteve por {_brl(s['menor'])} em {_dm(s['dia_menor'])}. Ative o aviso e a gente te chama quando cair.")
    return ("no preço de sempre",
            f"Está no preço normal: perto da média de 30 dias ({_brl(s['media30'])}). "
            f"O menor que vimos foi {_brl(s['menor'])} em {_dm(s['dia_menor'])}; se quiser esperar, ative o aviso.")


# ---------------------------------------------------------------- gráfico
def grafico_svg(pontos: list[tuple[str, float]]) -> str:
    W, H, m = 640, 220, 34
    vals = [v for _, v in pontos]
    lo, hi = min(vals), max(vals)
    if hi - lo < 0.01:
        lo, hi = lo * 0.95, hi * 1.05
    n = len(pontos)
    xs = [m + (W - 2 * m) * i / max(1, n - 1) for i in range(n)]
    ys = [H - m - (H - 2 * m) * (v - lo) / (hi - lo) for v in vals]
    linha = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"{xs[0]:.1f},{H - m} " + linha + f" {xs[-1]:.1f},{H - m}"
    im = vals.index(min(vals))
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Gráfico do histórico de preço: de {_brl(vals[0])} '
            f'em {_dm(pontos[0][0])} a {_brl(vals[-1])} em {_dm(pontos[-1][0])}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d4a937" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="#d4a937" stop-opacity="0"/></linearGradient></defs>'
            f'<line x1="{m}" y1="{H - m}" x2="{W - m}" y2="{H - m}" stroke="#ece6d6"/>'
            f'<text x="{m}" y="{m - 12}" class="ax">{_brl(hi)}</text><text x="{m}" y="{H - m + 20}" class="ax">{_dm(pontos[0][0])}</text>'
            f'<text x="{W - m}" y="{H - m + 20}" class="ax" text-anchor="end">{_dm(pontos[-1][0])}</text>'
            f'<polygon points="{area}" fill="url(#g)"/><polyline points="{linha}" fill="none" stroke="#b8901f" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<circle cx="{xs[im]:.1f}" cy="{ys[im]:.1f}" r="5" fill="#1e8449"/>'
            f'<text x="{xs[im]:.1f}" y="{ys[im] + 22:.1f}" class="ax mn" text-anchor="middle">menor {_brl(vals[im])}</text>'
            f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="5" fill="#14131a"/></svg>')


# ---------------------------------------------------------------- casca
CSS = """:root{--tinta:#14131a;--suave:#6b6878;--fundo:#f7f4ec;--caixa:#fff;--ouro:#d4a937;--ouro2:#f3d77a;--linha:#ece6d6;--preto:#0f0e13;--verde:#1e8449}
*{box-sizing:border-box}body{margin:0;background:var(--fundo);color:var(--tinta);font:15px/1.55 Poppins,system-ui,sans-serif;overflow-x:hidden}
a{color:inherit}.topo{background:radial-gradient(120% 140% at 50% -20%,#2a2618 0%,var(--preto) 60%);color:#fff;padding:16px 16px 64px}
.in{max-width:880px;margin:0 auto}.migalha{font-size:13px;color:#cfc8b3}.migalha a{color:#cfc8b3;text-decoration:none}.migalha a:hover{color:#fff}
h1{font:800 clamp(24px,4.6vw,38px)/1.12 Poppins,sans-serif;margin:12px 0 6px;letter-spacing:-.5px}h1 em{font-style:normal;color:var(--ouro2)}
.sub{color:#cfc8b3;margin:0}main{max-width:880px;margin:-44px auto 0;padding:0 16px 80px;position:relative}
.cx{background:var(--caixa);border:1px solid var(--linha);border-radius:20px;padding:18px;margin-bottom:16px;box-shadow:0 10px 30px rgba(20,16,30,.06)}
.prod{display:grid;grid-template-columns:220px 1fr;gap:20px}.prod img{width:100%;aspect-ratio:1;object-fit:contain;border-radius:14px;border:1px solid var(--linha);background:#fff}
.preco b{font:800 34px Poppins,sans-serif}.selo{display:inline-block;background:var(--preto);color:var(--ouro2);border-radius:999px;padding:3px 12px;font:700 12px/1.7 Poppins,sans-serif;text-transform:uppercase;letter-spacing:.3px}
.selo.bom{background:#e6f6ec;color:var(--verde)}small,.cinza{color:var(--suave);font-size:12.5px}
.btn{display:inline-flex;align-items:center;gap:8px;margin:10px 8px 0 0;background:var(--preto);color:var(--ouro2);border:1.5px solid var(--ouro);border-radius:999px;padding:11px 20px;font-weight:700;text-decoration:none}
.btn:hover{filter:brightness(1.15)}.btn.cl{background:#fff;color:var(--tinta);border-color:var(--linha)}
.resp{font-size:16px;margin:6px 0 0}h2{font:700 19px/1.3 Poppins,sans-serif;margin:0 0 10px}
svg{width:100%;height:auto;display:block}.ax{font:12px Poppins,sans-serif;fill:#6b6878}.ax.mn{fill:#1e8449;font-weight:700}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--linha);vertical-align:middle}
th{font-size:12px;color:var(--suave);text-transform:uppercase;letter-spacing:.4px}td img{width:54px;height:54px;object-fit:contain;border-radius:8px;border:1px solid var(--linha);background:#fff}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}.grade a{display:block;text-decoration:none;background:#fff;border:1px solid var(--linha);border-radius:14px;padding:10px;font-size:13px}
.grade img{width:100%;aspect-ratio:1;object-fit:contain}.grade b{display:block;margin-top:4px}
.cupom{background:#fffbea;border-color:#f3e3a6}.fora{background:#fff1f0;border-color:#f5c6c2}
details{border-top:1px solid var(--linha);padding:10px 0}summary{font-weight:600;cursor:pointer}
footer{max-width:880px;margin:0 auto;padding:0 16px 40px;font-size:13px;color:var(--suave)}footer a{margin-right:12px}
@media(max-width:600px){.prod{grid-template-columns:1fr}.prod img{max-width:260px;margin:0 auto}.esc{display:none}}"""


def casca(titulo: str, desc: str, canon: str, h1: str, sub: str, migalha: str, corpo: str,
          ld: list[dict], imagem: str = "") -> str:
    lds = "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace("</", "<\\/")
                  + "</script>" for x in ld)
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canon}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website"><meta property="og:title" content="{e(titulo)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}">{f'<meta property="og:image" content="{e(imagem)}">' if imagem else ''}
<meta name="theme-color" content="#0f0e13"><link rel="icon" href="/icone.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">
{lds}<style>{CSS}</style>
<header class="topo"><div class="in"><nav class="migalha">{migalha}</nav><h1>{h1}</h1><p class="sub">{sub}</p></div></header>
<main>{corpo}</main>
<footer><a href="/">Ofertas de hoje</a><a href="/melhores/">Melhores por preço</a><a href="/cupons/">Cupons</a><a href="/top10/">Top 10 ML</a><a href="/privacidade">Privacidade</a>
<p>Preços acompanhados pelo Achadinho Total. Links de afiliado: podemos ganhar comissão, sem custo extra para você. O preço pode mudar na loja.</p></footer>
<script>document.addEventListener("click",function(v){{var a=v.target.closest("a[data-ev]");if(a&&window.posthog)posthog.capture(a.dataset.ev,{{pagina:location.pathname}})}});</script>
</html>"""


def _migalha(*itens) -> tuple[str, dict]:
    partes, lista = [], []
    for i, (nome, url) in enumerate(itens, 1):
        partes.append(f'<a href="{url}">{e(nome)}</a>' if url else e(nome))
        lista.append({"@type": "ListItem", "position": i, "name": nome, **({"item": DOMINIO + url} if url else {})})
    return " › ".join(partes), {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": lista}


# ---------------------------------------------------------------- /p/<slug>/
def pagina_produto(p: dict, s: dict, parecidos: list[dict], cupons_loja: tuple[str, int] | None,
                   bot: str, quando: str, fora: bool = False) -> str:
    preco = _num(p["preco"]); loja = p.get("loja") or "loja"; nome = p["nome"]
    area = p.get("canal") or "Ofertas"
    selo, resposta = veredito(s, preco)
    url = f"{DOMINIO}/p/{p['pg']}/"
    img = (p.get("imagem") or "").replace("http://", "https://", 1)
    mig, ld_mig = _migalha(("Início", "/"), (f"Melhores {area}", f"/melhores/#{_slug_area(area)}"), (nome[:60], None))
    titulo = f"{nome[:70]}: histórico de preço e menor preço ({_brl(s['menor'])})"
    desc = (f"{nome[:90]} por {_brl(preco)} na {loja}. Acompanhamos há {s['n']} dias: menor {_brl(s['menor'])}, "
            f"média de 30 dias {_brl(s['media30'])}. Veja o gráfico e ative o aviso de queda.")
    bom = preco <= s["media30"] * 0.95
    aviso = (f'<a class="btn cl" data-ev="p_avise" href="https://t.me/{bot}?start=alerta_{e(str(p["id"]))}" rel="noopener">🔔 Me avise se cair</a>'
             if bot else "")
    cup = ""
    if cupons_loja:
        sl, (nl, q) = cupons_loja
        cup = (f'<section class="cx cupom"><h2>🎟️ {q} cupo{"m" if q == 1 else "ns"} da {e(nl)} ativo{"" if q == 1 else "s"} hoje</h2>'
               f'<p>Antes de comprar, veja se algum cupom baixa ainda mais esse preço.</p>'
               f'<a class="btn" data-ev="p_cupom" href="/cupons/{sl}/">Ver cupons da {e(nl)} →</a></section>')
    topo_fora = ('<section class="cx fora"><b>Não encontramos mais este preço na loja.</b> O produto pode ter saído de linha '
                 'ou mudado de anúncio. Veja os parecidos abaixo ou ative o aviso para saber se voltar.</section>') if fora else ""
    par = "".join(f'<a href="/p/{x["pg"]}/"><img src="{e(x["imagem"].replace("http://", "https://", 1))}" alt="" loading="lazy">'
                  f'{e(x["nome"][:60])}<b>{e(x["preco"])}</b></a>' for x in parecidos)
    corpo = f"""{topo_fora}<section class="cx prod"><img src="{e(img)}" alt="{e(nome[:100])}" width="220" height="220">
<div><span class="selo{' bom' if bom else ''}">{e(selo)}</span>
<div class="preco"><b>{_brl(preco)}</b> <span class="cinza">na {e(loja)}{'' if fora else ' · conferido em ' + e(quando)}</span></div>
<p class="resp"><strong>É uma boa hora para comprar?</strong> {e(resposta)}</p>
{'' if fora else f'<a class="btn" data-ev="p_loja" href="{e(p["link"])}" target="_blank" rel="sponsored noopener">Ver na {e(loja)} →</a>'}{aviso}</div></section>
<section class="cx"><h2>Histórico de preço ({s['n']} dias)</h2>{grafico_svg(s['pontos'][-90:])}
<table><tr><th>Menor preço</th><th>Maior preço</th><th>Média 30 dias</th><th>Acompanhando desde</th></tr>
<tr><td><b>{_brl(s['menor'])}</b><br><small>{_dm(s['dia_menor'])}</small></td><td>{_brl(s['maior'])}<br><small>{_dm(s['dia_maior'])}</small></td>
<td>{_brl(s['media30'])}</td><td>{_dm(s['desde'])}</td></tr></table>
<p class="cinza">Registramos o preço deste produto na {e(loja)} várias vezes por dia; cada dia vale o menor preço visto. Nada de "de/por" inventado: o desconto é medido contra o preço que nós vimos.</p></section>
{cup}
{f'<section class="cx"><h2>Parecidos em {e(area)}</h2><div class="grade">{par}</div></section>' if par else ''}
<section class="cx"><h2>Perguntas frequentes</h2>
<details open><summary>Qual o menor preço de {e(nome[:60])}?</summary><p>O menor preço que registramos foi {_brl(s['menor'])}, em {_dm(s['dia_menor'])}.</p></details>
<details><summary>Como funciona o aviso de queda?</summary><p>Você toca em "Me avise se cair", o Telegram abre e pronto: quando o preço baixar, mandamos mensagem. Sem cadastro.</p></details>
<details><summary>O preço é o mesmo na loja?</summary><p>Conferimos de hora em hora, mas a loja pode mudar o preço a qualquer momento. Vale sempre o preço da {e(loja)} na hora da compra.</p></details></section>"""
    offer = {"@type": "Offer", "price": f"{preco:.2f}", "priceCurrency": "BRL", "url": url,
             "availability": "https://schema.org/" + ("OutOfStock" if fora else "InStock"),
             "seller": {"@type": "Organization", "name": loja}}
    ld = [{"@context": "https://schema.org", "@type": "Product", "name": nome, "image": [img], "url": url,
           "offers": offer}, ld_mig,
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": f"Qual o menor preço de {nome[:60]}?",
               "acceptedAnswer": {"@type": "Answer", "text": f"O menor preço que registramos foi {_brl(s['menor'])}, em {_dm(s['dia_menor'])}."}}]}]
    h1 = f"{e(nome[:90])} <em>— histórico de preço</em>"
    sub = f"{s['n']} dias acompanhando · menor {_brl(s['menor'])} · hoje {_brl(preco)}"
    return casca(titulo, desc, url, h1, sub, mig, corpo, ld, img)


# ---------------------------------------------------------------- /melhores/
def listas_melhores(escolhidos: list[dict]) -> list[dict]:
    """Por área: a MENOR faixa de preço com ≥ 5 itens, e a seguinte (se ≥ 5 novos)."""
    por: dict[str, list[dict]] = {}
    for p in escolhidos:
        por.setdefault(p.get("canal") or "Ofertas", []).append(p)
    out = []
    for area, ps in por.items():
        usadas = 0
        for y in FAIXAS:
            dentro = [p for p in ps if _num(p["preco"]) <= y]
            if len(dentro) >= MIN_LISTA and len(dentro) - usadas >= 3:
                dentro.sort(key=lambda p: (_num(p["preco"]) / (estatisticas(p["_dias"], _num(p["preco"]))["media30"] or 1),
                                           -int(p.get("vendas") or 0)))
                out.append({"area": area, "ate": y, "itens": dentro[:10],
                            "slug": f"{_slug_area(area)}-ate-{y}-reais"})
                usadas = len(dentro)
                if sum(1 for o in out if o["area"] == area) >= 2:
                    break
    return out


def pagina_lista(l: dict, quando: str, mes: str) -> str:
    area, y = l["area"], l["ate"]
    url = f"{DOMINIO}/melhores/{l['slug']}/"
    titulo = f"Melhores {area.lower()} até R$ {y} ({mes}): preço acompanhado"
    mig, ld_mig = _migalha(("Início", "/"), ("Melhores por preço", "/melhores/"), (f"{area} até R$ {y}", None))
    linhas = []
    for i, p in enumerate(l["itens"], 1):
        s = estatisticas(p["_dias"], _num(p["preco"]))
        selo, _ = veredito(s, _num(p["preco"]))
        linhas.append(f'<tr><td>{i}</td><td><img src="{e(p["imagem"].replace("http://", "https://", 1))}" alt="" loading="lazy"></td>'
                      f'<td><a href="/p/{p["pg"]}/"><b>{e(p["nome"][:80])}</b></a><br><small>{e(p.get("loja") or "")} · {e(selo)}</small></td>'
                      f'<td><b>{e(p["preco"])}</b></td><td class="esc">{_brl(s["menor"])}</td><td class="esc">{s["n"]} dias</td></tr>')
    top = l["itens"][0]
    resp = (f"Pelo preço de hoje comparado com o histórico, o destaque é {top['nome'][:70]} por {top['preco']}. "
            f"A lista tem {len(l['itens'])} produtos de {area.lower()} até R$ {y}, ordenados por quanto estão abaixo da própria média de 30 dias.")
    corpo = (f'<section class="cx"><p class="resp"><strong>Qual comprar?</strong> {e(resp)}</p></section>'
             f'<section class="cx"><h2>Comparativo (preços conferidos em {e(quando)})</h2><table><tr><th>#</th><th></th><th>Produto</th>'
             f'<th>Hoje</th><th class="esc">Menor visto</th><th class="esc">Histórico</th></tr>{"".join(linhas)}</table>'
             f'<p class="cinza">Toque no produto para ver o gráfico de preço e o aviso de queda.</p></section>')
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": titulo, "url": url,
           "itemListElement": [{"@type": "ListItem", "position": i, "url": f"{DOMINIO}/p/{p['pg']}/", "name": p["nome"]}
                               for i, p in enumerate(l["itens"], 1)]}, ld_mig]
    return casca(titulo, f"{len(l['itens'])} {area.lower()} até R$ {y} comparados pelo histórico de preço: menor preço visto, média e preço de hoje.",
                 url, f"Melhores <em>{e(area.lower())}</em> até R$ {y}",
                 f"Comparados pelo histórico de preço real · {mes}", mig, corpo, ld)


def indice_melhores(ls: list[dict], mes: str) -> str:
    por: dict[str, list[dict]] = {}
    for l in ls:
        por.setdefault(l["area"], []).append(l)
    blocos = "".join(f'<section class="cx" id="{_slug_area(a)}"><h2>{e(a)}</h2>'
                     + "".join(f'<a class="btn cl" href="/melhores/{l["slug"]}/">Até R$ {l["ate"]} →</a>' for l in v)
                     + "</section>" for a, v in sorted(por.items()))
    mig, ld_mig = _migalha(("Início", "/"), ("Melhores por preço", None))
    return casca(f"Melhores produtos por faixa de preço ({mes}) — Achadinho Total",
                 "Listas dos melhores produtos até R$ 50, R$ 100, R$ 200 e mais, comparados pelo histórico de preço real.",
                 f"{DOMINIO}/melhores/", "Melhores <em>por preço</em>",
                 "Cada lista compara o preço de hoje com o histórico que nós medimos", mig, blocos, [ld_mig])


# ---------------------------------------------------------------- orquestra
def gerar(cartoes: list[dict], por_dia: dict, bot: str = "") -> tuple[dict[str, str], list[tuple[str, str]], dict[str, str]]:
    """({caminho: html}, [(url, lastmod)], {id: slug}) — chamado pelo publicador."""
    agora = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3)))
    quando = agora.strftime("%d/%m às %Hh"); mes = f"{MESES[agora.month - 1]} {agora.year}"
    try:
        from engine import cupons as _cup
        cup = {nl.lower(): (sl, (nl, q)) for sl, (nl, q) in _cup.lojas().items()}
    except Exception:                                     # noqa: BLE001
        cup = {}
    esc = escolher(cartoes, por_dia)
    reg = json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.exists() else {}
    por_area: dict[str, list[dict]] = {}
    for p in esc:
        por_area.setdefault(p.get("canal") or "Ofertas", []).append(p)
    saida, mapa, slugs = {}, [], {}
    for p in esc:
        s = estatisticas(p["_dias"], _num(p["preco"]))
        viz = [x for x in por_area[p.get("canal") or "Ofertas"] if x is not p][:6]
        c = cup.get((p.get("loja") or "").lower())
        saida[f"p/{p['pg']}/index.html"] = pagina_produto(p, s, viz, c, bot, quando)
        mapa.append((f"/p/{p['pg']}/", s["pontos"][-1][0]))
        slugs[str(p["id"])] = p["pg"]
        reg[str(p["id"])] = {k: p.get(k) for k in ("nome", "preco", "imagem", "loja", "canal", "id", "pg")} | {
            "_dias": p["_dias"], "visto": agora.date().isoformat()}
    # quem saiu do catálogo: página continua, com aviso (sem 404)
    for pid, r in reg.items():
        if pid in slugs or not r.get("_dias"):
            continue
        s = estatisticas(r["_dias"], _num(r["preco"]))
        viz = (por_area.get(r.get("canal") or "Ofertas") or esc)[:6]
        saida[f"p/{r['pg']}/index.html"] = pagina_produto(dict(r, link=""), s, viz, None, bot, quando, fora=True)
        mapa.append((f"/p/{r['pg']}/", r.get("visto") or s["pontos"][-1][0]))
    ls = listas_melhores(esc)
    for l in ls:
        saida[f"melhores/{l['slug']}/index.html"] = pagina_lista(l, quando, mes)
        mapa.append((f"/melhores/{l['slug']}/", agora.date().isoformat()))
    if ls:
        saida["melhores/index.html"] = indice_melhores(ls, mes)
        mapa.append(("/melhores/", agora.date().isoformat()))
    REGISTRO.write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
    print(f"paginas_produto: {len(esc)} /p/ no catalogo + {len(reg) - len(esc)} fora · {len(ls)} listas /melhores/")
    return saida, mapa, slugs
