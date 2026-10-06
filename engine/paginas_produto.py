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
td b,.era,.caiu{white-space:nowrap}.era{color:var(--suave);font-size:12.5px}.caiu{font-style:normal;background:#e6f6ec;color:var(--verde);border-radius:8px;padding:1px 6px;font-weight:700;font-size:12px}
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
<footer><a href="/">Ofertas de hoje</a><a href="/melhores/">Melhores por preço</a><a href="/guias/">Guias</a><a href="/cupons/">Cupons</a><a href="/top10/">Top 10 ML</a><a href="/privacidade">Privacidade</a>
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
    par = "".join(f'<a href="/p/{x["pg"]}/"><img src="{e(x["imagem"].replace("http://", "https://", 1))}" alt="{e(x["nome"][:100])}" loading="lazy">'
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


def listas_especiais(esc: list[dict]) -> list[dict]:
    """⭐ 06/10/2026 (+acervo: rankings específicos + "mais vendidos"; nosso diferencial = histórico real).
    Só sai a lista com ≥ MIN_LISTA itens — nada de página magra."""
    com = []
    for p in esc:
        pr = _num(p["preco"]); st = estatisticas(p["_dias"], pr)
        com.append((p, pr, st))
    out = []
    rec = sorted([(p, pr, st) for p, pr, st in com if pr <= st["menor"] * 1.005 and st["vs_media"] <= -3],
                 key=lambda t: t[2]["vs_media"])
    if len(rec) >= MIN_LISTA:
        out.append({"area": "Especiais", "ate": 0, "slug": "menor-preco-ja-visto-hoje", "itens": [t[0] for t in rec[:20]],
                    "curto": "Menor preço já visto",
                    "titulo": "Menor preço já visto: produtos no mínimo histórico hoje ({mes})",
                    "h1": "No <em>menor preço</em> que já vimos",
                    "sub": "Atualizado de hora em hora · cada um está hoje no preço mais baixo do nosso histórico",
                    "desc": "Produtos que hoje estão no menor preço que já registramos, com gráfico do histórico e aviso de queda.",
                    "resposta": f"Hoje {len(rec)} produtos estão no menor preço que já registramos. Estão ordenados pelo tamanho da queda em relação à média de 30 dias."})
    qd = sorted([(p, pr, st) for p, pr, st in com if st["vs_media"] <= -8], key=lambda t: t[2]["vs_media"])
    if len(qd) >= MIN_LISTA:
        out.append({"area": "Especiais", "ate": 0, "slug": "maiores-quedas-de-preco", "itens": [t[0] for t in qd[:20]],
                    "curto": "Maiores quedas",
                    "titulo": "Maiores quedas de preço da semana ({mes}): comparadas com a média de 30 dias",
                    "h1": "As <em>maiores quedas</em> de preço",
                    "sub": "Queda medida contra a média de 30 dias do próprio produto — não contra preço riscado",
                    "desc": "Os produtos que mais caíram de preço em relação à própria média de 30 dias, com histórico real.",
                    "resposta": f"{len(qd)} produtos estão pelo menos 8% abaixo da própria média de 30 dias. O primeiro da lista é o que mais caiu."})
    ate20 = sorted([(p, pr, st) for p, pr, st in com if pr <= 20], key=lambda t: (t[2]["vs_media"], t[1]))
    if len(ate20) >= MIN_LISTA:
        out.append({"area": "Especiais", "ate": 20, "slug": "achadinhos-ate-20-reais", "itens": [t[0] for t in ate20[:20]],
                    "curto": "Achadinhos até R$ 20",
                    "titulo": "Achadinhos até R$ 20 ({mes}): AliExpress, Mercado Livre e mais, com preço acompanhado",
                    "h1": "Achadinhos <em>até R$ 20</em>",
                    "sub": "Baratinhos com histórico de preço real · os mais abaixo da média primeiro",
                    "desc": "Achadinhos até R$ 20 com histórico de preço: veja o menor preço já visto antes de comprar."})
    return out


def _era(s: dict) -> str:
    """⭐ 06/10/2026 (dono: "mostrar o preço que era e a % que caiu"). "Era" = média de 30 dias
    (a MESMA base da queda; nunca o "de" inflado da loja). Só aparece com queda ≥ 3%."""
    if s["vs_media"] > -3:
        return ""
    return (f'<br><s class="era">{_brl(s["media30"])}</s> '
            f'<em class="caiu">-{abs(s["vs_media"]):.0f}%</em>')


def pagina_lista(l: dict, quando: str, mes: str) -> str:
    area, y = l["area"], l["ate"]
    url = f"{DOMINIO}/melhores/{l['slug']}/"
    titulo = l.get("titulo", "").format(mes=mes) or f"Melhores {area.lower()} até R$ {y} ({mes}): preço acompanhado"
    mig, ld_mig = _migalha(("Início", "/"), ("Melhores por preço", "/melhores/"), (l.get("curto") or f"{area} até R$ {y}", None))
    linhas = []
    for i, p in enumerate(l["itens"], 1):
        s = estatisticas(p["_dias"], _num(p["preco"]))
        selo, _ = veredito(s, _num(p["preco"]))
        linhas.append(f'<tr><td>{i}</td><td><img src="{e(p["imagem"].replace("http://", "https://", 1))}" alt="{e(p["nome"][:100])}" loading="lazy"></td>'
                      f'<td><a href="/p/{p["pg"]}/"><b>{e(p["nome"][:80])}</b></a><br><small>{e(p.get("loja") or "")} · {e(selo)}</small></td>'
                      f'<td><b>{e(p["preco"])}</b>{_era(s)}</td><td class="esc">{_brl(s["menor"])}</td><td class="esc">{s["n"]} dias</td></tr>')
    top = l["itens"][0]
    resp = l.get("resposta") or (f"Pelo preço de hoje comparado com o histórico, o destaque é {top['nome'][:70]} por {top['preco']}. "
            f"A lista tem {len(l['itens'])} produtos de {area.lower()} até R$ {y}, ordenados por quanto estão abaixo da própria média de 30 dias.")
    corpo = (f'<section class="cx"><p class="resp"><strong>Qual comprar?</strong> {e(resp)}</p></section>'
             f'<section class="cx"><h2>Comparativo (preços conferidos em {e(quando)})</h2><table><tr><th>#</th><th></th><th>Produto</th>'
             f'<th>Hoje <small>(era)</small></th><th class="esc">Menor visto</th><th class="esc">Histórico</th></tr>{"".join(linhas)}</table>'
             f'<p class="cinza">Toque no produto para ver o gráfico de preço e o aviso de queda.</p></section>')
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": titulo, "url": url,
           "itemListElement": [{"@type": "ListItem", "position": i, "url": f"{DOMINIO}/p/{p['pg']}/", "name": p["nome"]}
                               for i, p in enumerate(l["itens"], 1)]}, ld_mig]
    return casca(titulo, l.get("desc") or f"{len(l['itens'])} {area.lower()} até R$ {y} comparados pelo histórico de preço: menor preço visto, média e preço de hoje.",
                 url, l.get("h1") or f"Melhores <em>{e(area.lower())}</em> até R$ {y}",
                 l.get("sub") or f"Comparados pelo histórico de preço real · {mes}", mig, corpo, ld)


def indice_melhores(ls: list[dict], mes: str) -> str:
    por: dict[str, list[dict]] = {}
    for l in ls:
        por.setdefault(l["area"], []).append(l)
    blocos = "".join(f'<section class="cx" id="{_slug_area(a)}"><h2>{e(a)}</h2>'
                     + "".join(f'<a class="btn cl" href="/melhores/{l["slug"]}/">{e(l.get("curto") or f"Até R$ {l[chr(97)+chr(116)+chr(101)]}")} →</a>' for l in v)
                     + "</section>" for a, v in sorted(por.items(), key=lambda kv: (kv[0] != "Especiais", kv[0])))
    mig, ld_mig = _migalha(("Início", "/"), ("Melhores por preço", None))
    return casca(f"Melhores produtos por faixa de preço ({mes}) — Achadinho Total",
                 "Listas dos melhores produtos até R$ 50, R$ 100, R$ 200 e mais, comparados pelo histórico de preço real.",
                 f"{DOMINIO}/melhores/", "Melhores <em>por preço</em>",
                 "Cada lista compara o preço de hoje com o histórico que nós medimos", mig, blocos, [ld_mig])


# ---------------------------------------------------------------- /guias/
# ⭐ 05/10/2026 (+acervo: autoridade por tema + "answer targets"). Cada guia é um
# CLUSTER: resposta direta no topo, critérios, tabela com os NOSSOS produtos do
# tema (preço de hoje x menor visto, link para /p/), listas /melhores/ e FAQ.
# As /p/ do tema linkam de volta para o guia. Novo nicho = novo item em GUIAS.
GUIAS = [{
    "slug": "como-escolher-fone-bluetooth",
    "termos": ("fone", "earbud", "headphone", "headset", "tws"),
    "fora": ("suporte", "capa ", "case ", "adaptador", "cabo ", "almofada", "espuma"),
    "curto": "fone Bluetooth",
    "titulo": "Como escolher fone Bluetooth bom e barato em {ano}: guia com preços acompanhados",
    "h1": "Como escolher um <em>fone Bluetooth</em>",
    "desc": "Bluetooth 5.3, bateria, ANC x ENC, IPX4, codec e modo jogo explicados em linguagem simples — e os fones que acompanhamos, com o menor preço já visto.",
    "resposta": ("Para a maioria das pessoas, o melhor custo-benefício é um fone sem fio (TWS) com Bluetooth 5.3, "
                 "pelo menos 5 horas de bateria por carga (20 h ou mais com o estojo) e resistência IPX4 a suor. "
                 "Cancelamento de ruído (ANC) só vale se você usa em ônibus, metrô ou avião — e em fone muito barato o \"ANC\" do anúncio costuma ser fraco."),
    "secoes": [
        ("1. Qual tipo de fone?", [
            "<b>Sem fio (TWS, os \"de estojo\"):</b> os mais vendidos; leves, cabem no bolso. Bom para o dia a dia e academia.",
            "<b>Headphone (de arco):</b> bateria bem maior (30–60 h) e som mais encorpado; bom para trabalho e viagem, ruim para treino.",
            "<b>Esportivo / gancho / condução óssea:</b> não cai na corrida; o de condução óssea deixa o ouvido livre (bom para rua), com menos grave."]),
        ("2. Versão do Bluetooth", [
            "5.0 ou mais já conecta estável. 5.2/5.3 gastam menos bateria e reconectam mais rápido. Abaixo de 5.0, evite.",
            "A versão do celular também conta: o fone usa o recurso que os DOIS têm."]),
        ("3. Bateria: leia os dois números", [
            "O anúncio costuma somar fone + estojo (\"30 horas\"). O que importa no dia é a carga POR USO: procure 5 h ou mais.",
            "Carga rápida (10 min = 1 h de uso) ajuda quem esquece de carregar."]),
        ("4. ANC x ENC — a confusão mais comum", [
            "<b>ANC</b> (cancelamento ativo de ruído) reduz o barulho que VOCÊ ouve.",
            "<b>ENC</b> (cancelamento de ruído ambiental) só limpa o seu MICROFONE nas ligações — não deixa o fone mais silencioso.",
            "Muitos anúncios baratos escrevem \"cancelamento de ruído\" falando de ENC. Confira qual dos dois está escrito."]),
        ("5. Suor e chuva (IPX)", [
            "IPX4: aguenta suor e respingo — o mínimo para academia. IPX5/IPX6: jato de água. IPX7: imersão rápida. Nenhum é para nadar, salvo se disser natação."]),
        ("6. Codec e modo jogo", [
            "iPhone: o codec AAC é o que importa. Android: aptX ou LDAC soam melhor, mas só se o celular suportar.",
            "Jogos e vídeos: \"modo jogo\" / baixa latência evita som atrasado em relação à imagem."]),
        ("7. Como não pagar caro", [
            "Fone é um dos produtos que mais oscilam de preço. Antes de comprar, veja o histórico: muitas vezes o mesmo modelo já esteve bem mais barato semanas antes.",
            "Na tabela abaixo, cada fone mostra o preço de hoje e o menor que já vimos. Se não estiver no menor, ative o aviso de queda na página do produto."]),
    ],
    "faq": [
        ("Qual a diferença entre ANC e ENC?", "ANC reduz o barulho que você ouve; ENC só limpa o seu microfone nas ligações."),
        ("Fone Bluetooth barato presta?", "Para ouvir música e vídeo no dia a dia, sim: com Bluetooth 5.3, bateria de 5 h+ e IPX4 já é bom. Não espere ANC forte em fone muito barato."),
        ("Bluetooth 5.3 faz diferença?", "Faz pouca no som; ajuda na bateria e na reconexão. Bluetooth 5.0 ou mais já é suficiente."),
        ("Qual fone é melhor para academia?", "Um TWS ou esportivo com IPX4 ou mais e bom encaixe (ponteiras de tamanhos diferentes ou gancho)."),
    ],
}]

GUIAS += [{
    "slug": "como-escolher-carregador-rapido-e-cabo-usb-c",
    "termos": ("carregador", "cabo usb", "cabo tipo c", "cabo colorido tipo c", "gan "),
    "fora": ("suporte", "organizador", "testador", "kit limpeza", "lanterna", "ventilador", "power bank", "fone"),
    "curto": "carregador rápido e cabo USB-C",
    "titulo": "Como escolher carregador rápido e cabo USB-C em {ano} (watts, PD, GaN): guia com preços acompanhados",
    "h1": "Como escolher <em>carregador rápido</em> e cabo USB-C",
    "desc": "Quantos watts seu celular aceita, o que é PD e PPS, quando vale GaN e qual cabo aguenta 60 W, 100 W ou 240 W — com o menor preço já visto.",
    "resposta": ("Veja quantos watts o seu celular aceita (a maioria fica entre 20 W e 45 W) e compre um carregador USB-C com Power Delivery (PD) "
                 "pelo menos dessa potência — um maior não estraga o celular, ele só puxa o que suporta. "
                 "O cabo também conta: para mais de 60 W ele precisa ser de 100 W ou 240 W (chip e-marker), senão a carga fica limitada."),
    "secoes": [
        ("1. Quantos watts você precisa?", [
            "iPhone: até ~20–30 W. Samsung: 25 W ou 45 W (\"Super Fast Charging\" pede PPS). Xiaomi/Motorola: alguns passam de 60 W, mas só com o carregador da marca.",
            "Notebook com USB-C: normalmente 45–100 W. Um carregador de 65 W+ resolve celular e notebook com o mesmo bloco."]),
        ("2. PD e PPS: os nomes que importam", [
            "<b>PD (Power Delivery)</b> é o padrão de carga rápida pelo USB-C — iPhone, Pixel, notebooks.",
            "<b>PPS</b> é uma extensão do PD que a Samsung usa para os 25/45 W. Sem PPS, o Samsung carrega, mas mais devagar.",
            "\"QC 3.0\" é um padrão antigo de USB-A: funciona, mas não é o ideal para celular novo."]),
        ("3. GaN vale a pena?", [
            "GaN é um material que deixa o carregador menor e mais frio na mesma potência. Para 65 W ou mais, vale: um GaN de 65 W tem o tamanho de um carregador comum de 20 W."]),
        ("4. Várias portas: leia a divisão", [
            "\"240 W com 5 portas\" é a soma. Ao ligar 2 ou 3 aparelhos juntos, cada porta recebe menos. Veja no anúncio a potência POR porta."]),
        ("5. O cabo certo", [
            "Cabo USB-C comum aguenta até 60 W (3 A). Para 100 W ou 240 W o cabo precisa dizer isso (5 A / e-marker).",
            "Cabo com visor digital mostra os watts reais — útil para conferir se a carga rápida está funcionando.",
            "Nylon trançado dura mais que o de borracha nas pontas, que é onde quebra."]),
        ("6. Segurança", [
            "Desconfie de carregador sem nenhuma marca, muito leve e muito barato para a potência anunciada. Proteções contra sobretensão e superaquecimento devem estar no anúncio."]),
        ("7. Como não pagar caro", [
            "Cabos e carregadores mudam muito de preço no AliExpress. Na tabela abaixo, cada um mostra o preço de hoje e o menor que já vimos."]),
    ],
    "faq": [
        ("Carregador mais forte estraga o celular?", "Não. O celular só puxa a potência que suporta; um carregador de 65 W carrega um iPhone a ~20 W."),
        ("Qual a diferença entre PD e PPS?", "PD é o padrão de carga rápida do USB-C; PPS é uma extensão dele que a Samsung usa para 25 W e 45 W."),
        ("Todo cabo USB-C faz carga rápida?", "Até 60 W, quase todos. Acima disso, só cabo de 100 W ou 240 W (5 A, com chip e-marker)."),
        ("O que é carregador GaN?", "Um carregador feito com nitreto de gálio: menor e mais frio na mesma potência."),
    ],
}, {
    "slug": "como-escolher-caixa-de-som-bluetooth",
    "termos": ("caixa de som", "caixinha de som", "speaker"),
    "fora": ("suporte", "capa "),
    "curto": "caixa de som Bluetooth",
    "titulo": "Como escolher caixa de som Bluetooth boa e barata em {ano}: guia com preços acompanhados",
    "h1": "Como escolher uma <em>caixa de som Bluetooth</em>",
    "desc": "Potência RMS x PMPO, bateria, IPX7, TWS (parear duas) e tamanho explicados — e as caixas que acompanhamos, com o menor preço já visto.",
    "resposta": ("Para usar em casa, no banho ou na praia, procure uma caixa com potência RMS (não PMPO) de 10 W ou mais, "
                 "bateria de 8 horas ou mais e resistência IPX7 se for perto de água. "
                 "Se quiser som mais forte sem pagar caro, escolha uma com função TWS: dá para parear duas iguais e tocar em estéreo."),
    "secoes": [
        ("1. Watts de verdade: RMS, não PMPO", [
            "RMS é a potência contínua real. PMPO é um número de pico, inflado (\"2000 W\" em caixa de bolso). Compare só RMS.",
            "5 W: quarto e banheiro. 10–20 W: sala e churrasco pequeno. 30 W+: área externa."]),
        ("2. Bateria", [
            "8 horas ou mais é bom para um dia fora. Volume alto e LED ligado consomem mais — o número do anúncio costuma ser em volume médio.",
            "Carregar por USB-C é mais prático do que por micro-USB."]),
        ("3. Água e poeira (IPX)", [
            "IPX4: respingo. IPX5/IPX6: jato d'água. IPX7: aguenta cair na piscina rapidamente. Para banho e praia, prefira IPX7."]),
        ("4. TWS: duas caixas em estéreo", [
            "Caixas com \"TWS\" pareiam com outra igual — dois lados, som mais cheio, pelo preço de duas pequenas."]),
        ("5. Extras que ajudam (ou não)", [
            "Microfone para viva-voz, rádio FM, entrada de cartão e LED são extras; não melhoram o som. Escolha pelo RMS, bateria e IPX primeiro."]),
        ("6. Como não pagar caro", [
            "Na tabela abaixo, cada caixa mostra o preço de hoje e o menor que já vimos. Se não estiver no menor, ative o aviso de queda."]),
    ],
    "faq": [
        ("O que é potência RMS?", "É a potência contínua real do alto-falante. É o único número de watts que dá para comparar entre caixas."),
        ("Caixa de som IPX7 pode molhar?", "Pode: aguenta respingo, chuva e uma queda rápida na água. Não é para ficar submersa."),
        ("O que é TWS em caixa de som?", "É a função de parear duas caixas iguais para tocar em estéreo."),
        ("Quantos watts para uma caixa de som boa?", "10 a 20 W RMS resolvem sala e área pequena; 5 W basta para quarto e banheiro."),
    ],
}]
GUIAS += [{
    "slug": "como-escolher-suporte-de-celular-para-carro",
    "termos": ("suporte magnetico", "suporte celular", "suporte para celular"),
    "fora": ("lavadora", "geladeira", "mesa", "bicicleta", "moto"),
    "curto": "suporte de celular para carro",
    "titulo": "Como escolher suporte de celular para carro em {ano} (magnético, ventosa ou saída de ar): guia com preços",
    "h1": "Como escolher <em>suporte de celular</em> para carro",
    "desc": "Saída de ar, ventosa ou adesivo no painel? Magnético ou garra? O que funciona com capinha e MagSafe — e os suportes que acompanhamos, com o menor preço já visto.",
    "resposta": ("Para a maioria dos carros, o suporte magnético de painel (adesivo) ou de saída de ar é o mais prático: encaixa com uma mão e não balança. "
                 "Se o seu celular é pesado ou a saída de ar é redonda e frágil, prefira ventosa no vidro ou painel. "
                 "Com suporte magnético, a capinha precisa ser fina ou ter MagSafe — senão use a placa metálica que vem junto."),
    "secoes": [
        ("1. Onde prender", [
            "<b>Saída de ar (clipe):</b> barato e fácil; em saída redonda ou frágil pode quebrar a aleta. No inverno o ar quente esquenta o celular.",
            "<b>Painel com adesivo:</b> firme e no campo de visão; o adesivo é difícil de tirar depois (veja se vem fita 3M).",
            "<b>Ventosa (vidro ou painel):</b> segura celular pesado; no sol forte a ventosa pode soltar — limpe a superfície antes."]),
        ("2. Magnético ou garra?", [
            "<b>Magnético:</b> encaixa e solta com uma mão. Precisa de MagSafe ou da plaquinha metálica entre o celular e a capa.",
            "<b>Garra (braços que fecham):</b> serve em qualquer celular e capa grossa, mas é mais lento de tirar."]),
        ("3. MagSafe e carregamento sem fio", [
            "Plaquinha metálica atrapalha o carregamento por indução. Se você carrega sem fio, prefira capa MagSafe ou suporte de garra."]),
        ("4. Rotação 360°", [
            "Útil para alternar entre vertical (mensagens) e horizontal (GPS). Confira se a articulação trava firme — a solta faz o celular cair na lombada."]),
        ("5. Segurança e lei", [
            "Posicione sem tapar a visão da via e longe do airbag. Mexer no celular dirigindo continua proibido — o suporte é para ver o GPS."]),
        ("6. Como não pagar caro", [
            "Na tabela abaixo, cada suporte mostra o preço de hoje e o menor que já vimos."]),
    ],
    "faq": [
        ("Suporte magnético estraga o celular?", "Não. Os ímãs desses suportes não afetam a memória nem a tela; podem só atrapalhar a bússola enquanto o celular está preso."),
        ("Suporte magnético funciona com capinha?", "Com capa fina ou MagSafe, sim. Em capa grossa, cole a plaquinha metálica por dentro ou por fora da capa."),
        ("Qual o melhor suporte de celular para carro?", "Para uso diário, magnético de painel ou saída de ar; para celular pesado ou capa grossa, ventosa com garra."),
    ],
}, {
    "slug": "como-escolher-fita-de-led",
    "termos": ("fita de led", "fita led"),
    "fora": (),
    "curto": "fita de LED",
    "titulo": "Como escolher fita de LED em {ano} (USB, app, Bluetooth, TV): guia com preços acompanhados",
    "h1": "Como escolher <em>fita de LED</em>",
    "desc": "USB ou fonte na tomada, controle por app ou remoto, RGB x branco, TV e quarto — o que olhar antes de comprar fita LED, com o menor preço já visto.",
    "resposta": ("Para TV, monitor e mesa, a fita LED USB (5 V) é a mais simples: liga na porta USB da TV e acende junto com ela. "
                 "Para quarto e sanca, prefira fita com fonte na tomada e controle por app (Bluetooth ou Wi-Fi). "
                 "Meça o comprimento antes — a maioria pode ser cortada nas marcas, mas não emendada sem conector."),
    "secoes": [
        ("1. Como ela liga", [
            "<b>USB (5 V):</b> TV, monitor, carro, mesa. Poucos metros (até ~5 m), brilho moderado.",
            "<b>Fonte na tomada (12 V/24 V):</b> quarto, sanca, cozinha. Mais metros e mais brilho."]),
        ("2. Controle", [
            "<b>Controle remoto (IR):</b> simples, precisa apontar.",
            "<b>App por Bluetooth:</b> cores, timer e modo música no celular, sem Wi-Fi.",
            "<b>Wi-Fi:</b> funciona com Alexa/Google e de fora de casa."]),
        ("3. Cor: RGB, branco ou RGBIC", [
            "RGB faz todas as cores, mas o \"branco\" sai azulado. Para iluminar de verdade (cozinha, leitura), escolha fita branca quente/fria ou RGBW.",
            "RGBIC mostra várias cores ao mesmo tempo (efeito arco-íris correndo)."]),
        ("4. Medida e instalação", [
            "Meça o contorno antes. Corte só nas marcas (tesourinha). Limpe a superfície com álcool — a fita adesiva solta em parede com poeira ou gordura.",
            "Em banheiro e área externa, use fita à prova d'água (IP65 ou mais)."]),
        ("5. Para TV: o tamanho", [
            "Regra prática: o perímetro da TV em metros. 32\": ~2 m · 43\": ~2,5 m · 50–55\": ~3 m · 65\": ~3,5–4 m."]),
        ("6. Como não pagar caro", [
            "Na tabela abaixo, cada fita mostra o preço de hoje e o menor que já vimos."]),
    ],
    "faq": [
        ("Fita LED USB pode ligar na TV?", "Pode: ela usa 5 V da porta USB e acende e apaga junto com a TV."),
        ("Pode cortar fita de LED?", "Pode, nas marcas indicadas (geralmente a cada 3 LEDs ou a cada 5–10 cm). O pedaço cortado só volta a funcionar com conector."),
        ("Quantos metros de fita LED para TV de 50 polegadas?", "Cerca de 3 metros para contornar a parte de trás."),
        ("Fita LED gasta muita energia?", "Não: alguns watts por metro, menos que uma lâmpada comum."),
    ],
}, {
    "slug": "como-escolher-luva-de-academia",
    "termos": ("luva", "luvas", "grip", "alcas de pulso"),
    "fora": ("boxe", "ciclismo", "cozinha", "jardinagem", "limpeza"),
    "curto": "luva de academia",
    "titulo": "Luva de academia, grip ou strap? Como escolher em {ano}: guia com preços acompanhados",
    "h1": "Luva, grip ou strap: como escolher para a <em>academia</em>",
    "desc": "Diferença entre luva, grip (luva sapo/palmar) e strap (alça de pulso), quando cada um ajuda e quando atrapalha — com o menor preço já visto.",
    "resposta": ("Se o problema é calo e mão escorregando, use um grip (protetor palmar) ou luva fina — protegem a palma sem engrossar a pegada. "
                 "Se o problema é a pegada cansar antes das costas no levantamento terra e na remada, use strap (alça de pulso). "
                 "Luva grossa e acolchoada aumenta o diâmetro da barra e pode até diminuir a força de pegada."),
    "secoes": [
        ("1. Luva", [
            "Protege toda a mão e evita calo. Prefira luva fina e com boa aderência; as muito acolchoadas deixam a barra \"mais grossa\".",
            "Luva com munhequeira (suporte para o punho) ajuda quem sente o punho no supino e no desenvolvimento."]),
        ("2. Grip (protetor palmar / \"luva sapo\")", [
            "Cobre só a palma, com furos para os dedos. Protege contra calo e dá aderência sem perder a sensação da barra. Muito usado em barra fixa e crossfit."]),
        ("3. Strap (alça de pulso)", [
            "Uma fita que dá a volta na barra e no punho. Serve para puxadas pesadas (terra, remada, puxada) quando a pegada cansa antes do músculo-alvo.",
            "Não use em todos os exercícios: treinar sem strap também fortalece a pegada."]),
        ("4. Magnésio", [
            "O pó/líquido de magnésio absorve o suor e melhora a aderência. Algumas academias não permitem o pó — o grip é a alternativa."]),
        ("5. Tamanho e lavagem", [
            "Luva tem que ficar justa (folgada dobra na palma e faz calo). Lave à mão e seque à sombra; neoprene e borracha ressecam no sol."]),
        ("6. Como não pagar caro", [
            "Na tabela abaixo, cada item mostra o preço de hoje e o menor que já vimos."]),
    ],
    "faq": [
        ("Luva de academia é necessária?", "Não é obrigatória; ajuda quem tem calo ou mão que escorrega. Para força de pegada, strap é mais útil nas puxadas pesadas."),
        ("Qual a diferença entre grip e strap?", "Grip protege a palma e melhora a aderência; strap é uma alça que prende o punho à barra para a pegada não falhar."),
        ("Luva tira calo da academia?", "Ajuda a prevenir; luva justa e fina ou grip protegem melhor do que luva grossa e folgada."),
    ],
}]

def _do_guia(g: dict, p: dict) -> bool:
    # palavra inteira no começo do termo: "fone" não casa "telefone"
    n = " " + re.sub(r"[^a-z0-9]+", " ", _ascii(p.get("nome", ""))) + " "
    tem = lambda t: (" " + t.strip() + (" " if t.endswith(" ") else "")) in n
    return any(tem(t) for t in g["termos"]) and not any(tem(f) for f in g["fora"])


def pagina_guia(g: dict, itens: list[dict], listas: list[dict], ano: int, quando: str) -> str:
    url = f"{DOMINIO}/guias/{g['slug']}/"
    titulo = g["titulo"].format(ano=ano)
    mig, ld_mig = _migalha(("Início", "/"), ("Guias", "/guias/"), (g["curto"].capitalize(), None))
    sec = "".join(f'<section class="cx"><h2>{h}</h2>' + "".join(f"<p>{t}</p>" for t in ps) + "</section>"
                  for h, ps in g["secoes"])
    linhas = []
    for x in sorted(itens, key=lambda x: _num(x["preco"]))[:20]:
        st = estatisticas(x["_dias"], _num(x["preco"]))
        selo, _ = veredito(st, _num(x["preco"]))
        linhas.append(f'<tr><td><img src="{e(x["imagem"].replace("http://", "https://", 1))}" alt="{e(x["nome"][:100])}" loading="lazy"></td>'
                      f'<td><a href="/p/{x["pg"]}/"><b>{e(x["nome"][:80])}</b></a><br><small>{e(x.get("loja") or "")} · {e(selo)}</small></td>'
                      f'<td><b>{e(x["preco"])}</b>{_era(st)}</td><td class="esc">{_brl(st["menor"])}</td></tr>')
    tab = (f'<section class="cx"><h2>Os modelos que acompanhamos (preços de {e(quando)})</h2><table><tr><th></th><th>Produto</th>'
           f'<th>Hoje</th><th class="esc">Menor visto</th></tr>{"".join(linhas)}</table>'
           f'<p class="cinza">Toque no produto para ver o gráfico de preço e ativar o aviso de queda.</p></section>') if linhas else ""
    ls = "".join(f'<a class="btn cl" href="/melhores/{l["slug"]}/">Melhores {e(l["area"].lower())} até R$ {l["ate"]} →</a>' for l in listas)
    faq = "".join(f"<details{' open' if i == 0 else ''}><summary>{e(q)}</summary><p>{e(r)}</p></details>" for i, (q, r) in enumerate(g["faq"]))
    corpo = (f'<section class="cx"><p class="resp"><strong>Resposta rápida:</strong> {e(g["resposta"])}</p></section>{sec}{tab}'
             + (f'<section class="cx"><h2>Listas por preço</h2>{ls}</section>' if ls else "")
             + f'<section class="cx"><h2>Perguntas frequentes</h2>{faq}</section>')
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": titulo, "url": url,
           "author": {"@type": "Organization", "name": "Achadinho Total"},
           "publisher": {"@type": "Organization", "name": "Achadinho Total"},
           "dateModified": dt.date.today().isoformat()}, ld_mig,
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in g["faq"]]}]
    return casca(titulo, g["desc"], url, g["h1"], f"Guia prático · atualizado em {quando}", mig, corpo, ld)


def indice_guias(gs: list[dict]) -> str:
    mig, ld_mig = _migalha(("Início", "/"), ("Guias", None))
    corpo = "".join(f'<section class="cx"><h2><a href="/guias/{g["slug"]}/">{e(g["titulo"].format(ano=dt.date.today().year))}</a></h2>'
                    f'<p>{e(g["desc"])}</p></section>' for g in gs)
    return casca("Guias de compra — Achadinho Total", "Guias simples para escolher bem e pagar menos, com preços acompanhados.",
                 f"{DOMINIO}/guias/", "Guias de <em>compra</em>", "Escolher bem e pagar menos", mig, corpo, [ld_mig])


def aplicar_guias(saida: dict, mapa: list, esc: list[dict], ls: list[dict], agora) -> int:
    quando = agora.strftime("%d/%m às %Hh")
    feitos = []
    for g in GUIAS:
        itens = [p for p in esc if _do_guia(g, p)]
        if len(itens) < 3:
            continue
        areas = {p.get("canal") for p in itens}
        saida[f"guias/{g['slug']}/index.html"] = pagina_guia(g, itens, [l for l in ls if l["area"] in areas], agora.year, quando)
        mapa.append((f"/guias/{g['slug']}/", agora.date().isoformat()))
        feitos.append(g)
        caixa = (f'<section class="cx cupom"><h2>📘 Guia: como escolher {e(g["curto"])}</h2><p>Os pontos que importam na compra, '
                 f'explicados — e os outros modelos com o menor preço já visto.</p><a class="btn" href="/guias/{g["slug"]}/">Ler o guia →</a></section>')
        alvo = '<section class="cx"><h2>Perguntas frequentes</h2>'
        for p in itens:
            k = f"p/{p['pg']}/index.html"
            if k in saida:
                saida[k] = saida[k].replace(alvo, caixa + alvo, 1)
    if feitos:
        saida["guias/index.html"] = indice_guias(feitos)
        mapa.append(("/guias/", agora.date().isoformat()))
    return len(feitos)


ULTIMAS_LISTAS: list[dict] = []
ICONES = {"menor-preco-ja-visto-hoje": "🏆", "maiores-quedas-de-preco": "📉", "achadinhos-ate-20-reais": "💰"}


def vitrine_listas_home(bot: str = "") -> str:
    """⭐ 06/10/2026 (dono: "listas antes dos anúncios, lugar de destaque"). Faixa no topo da home.
    Listas ABERTAS (Google indexa) + captura sem bloquear: "receba toda semana" (Telegram)."""
    esp = [l for l in ULTIMAS_LISTAS if l["area"] == "Especiais"]
    if not esp:
        return ""
    cards = "".join(
        f'<a class="lst-card" href="/melhores/{l["slug"]}/" data-ev="home_lista">'
        f'<span class="lst-ic">{ICONES.get(l["slug"], "⭐")}</span><b>{e(l["curto"])}</b>'
        f'<small>{len(l["itens"])} produtos · hoje</small></a>' for l in esp)
    cards += ('<a class="lst-card" href="/guias/" data-ev="home_lista"><span class="lst-ic">📘</span><b>Guias de compra</b>'
              '<small>escolher bem e pagar menos</small></a>'
              '<a class="lst-card" href="/melhores/" data-ev="home_lista"><span class="lst-ic">🗂️</span><b>Todas as listas</b>'
              '<small>por categoria e preço</small></a>')
    vip = ('<a class="lst-vip" href="https://t.me/achadinhototal" target="_blank" rel="noopener" data-ev="home_lista_vip">'
           '🔔 Receber as ofertas e as listas no Telegram →</a>')
    return f'<section class="lst" aria-label="Listas de hoje"><h2>As listas de hoje</h2><div class="lst-fila">{cards}</div>{vip}</section>'


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
        mapa.append((f"/p/{p['pg']}/", s["pontos"][-1][0], p["imagem"].replace("http://", "https://", 1), p["nome"]))
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
    ls = listas_especiais(esc) + listas_melhores(esc)
    global ULTIMAS_LISTAS
    ULTIMAS_LISTAS = ls
    for l in ls:
        saida[f"melhores/{l['slug']}/index.html"] = pagina_lista(l, quando, mes)
        mapa.append((f"/melhores/{l['slug']}/", agora.date().isoformat()))
    ng = aplicar_guias(saida, mapa, esc, ls, agora)
    if ls:
        saida["melhores/index.html"] = indice_melhores(ls, mes)
        mapa.append(("/melhores/", agora.date().isoformat()))
    REGISTRO.write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
    print(f"paginas_produto: {len(esc)} /p/ no catalogo + {len(reg) - len(esc)} fora · {len(ls)} listas /melhores/ · {ng} guia(s)")
    return saida, mapa, slugs
