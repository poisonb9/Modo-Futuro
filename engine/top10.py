# -*- coding: utf-8 -*-
"""Páginas "Top 10 do Mercado Livre" por nicho -> /top10/<nicho>/ e /top10/.

⭐ 05/10/2026 (dono: "página top 10 do mercado livre por nicho, bem caprichada").
Acervo marketing-e-oferta: "top 10 dos mais vendidos do Mercado Livre por nicho"
é a tática de conteúdo mais citada entre afiliados do ML (atrai busca do Google e
converte porque a pessoa já chega decidida a comprar).

Fonte: `estado/ml_vitrine.json` (de hora em hora). A ORDEM é a dos mais vendidos
do próprio Mercado Livre na categoria (`/highlights`) — o ranking é deles, não
nosso; a página diz isso. Preço com data e hora (regra da contra-capa).

O cookie do ML é de 24 h a partir do CLIQUE: por isso o selo "oferta de hoje".
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VITRINE = RAIZ / "estado" / "ml_vitrine.json"
MODELO = RAIZ / "engine" / "top10_pagina.html"

NICHOS = {  # area da vitrine -> (slug, titulo, emoji, frase)
    "Academia": ("academia", "Academia e suplementos", "💪", "whey, creatina, acessórios de treino"),
    "Eletrônicos": ("eletronicos", "Eletrônicos e tecnologia", "⚡", "fones, carregadores, smartwatch, games"),
    "Beleza": ("beleza", "Beleza e maquiagem", "💄", "maquiagem, skincare, cabelo"),
    "Saúde": ("saude", "Saúde e bem-estar", "🩺", "vitaminas, cuidados, bem-estar"),
    "Casa": ("casa", "Casa e organização", "🏠", "organização, ferramentas, decoração"),
    "Cozinha": ("cozinha", "Cozinha e eletroportáteis", "🍳", "air fryer, utensílios, eletroportáteis"),
    "Infantil": ("infantil", "Bebês e brinquedos", "🧸", "brinquedos, bebê, criança"),
    "Pet": ("pet", "Pet", "🐾", "cachorro, gato, acessórios"),
}
MINIMO = 6
# ⛔ 05/10/2026: a categoria do ML "Beleza e Cuidado Pessoal" abria com papel
# higienico em 1o. Cesta basica nao e' "top de beleza" — fica fora do Top 10.
FORA = ("papel higien", "fralda", "absorvente", "umedecid", "sabao em po",
        "amaciante", "detergente", "desodorante aerosol", "aparelho de barbear descart",
        "lava roupas", "papel toalha", "guardanapo", "saco de lixo", "agua sanitaria",
        # ⛔ regra do dono: remedio NAO (suplemento sim) — inclusive remedio de pet
        "bravecto", "nexgard", "simparic", "credeli", "vermifugo", "antipulga",
        "comp. mastigavel", "comprimido mastigavel", "dipirona", "paracetamol", "ibuprofeno")


def _raiz(n: str) -> str:
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    return " ".join(n.split()[:4])


def _brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def listas() -> dict[str, list[dict]]:
    inst = json.loads(VITRINE.read_text(encoding="utf-8"))
    por: dict[str, list[dict]] = {}
    vistos: dict[str, set] = {}
    for p in inst.get("produtos") or []:
        a = p.get("categoria")
        if a not in NICHOS or not p.get("link") or not p.get("imagem") or p.get("remedio"):
            continue
        n = unicodedata.normalize("NFKD", p.get("nome") or "").encode("ascii", "ignore").decode().lower()
        if any(f in n for f in FORA):
            continue
        r = _raiz(p.get("nome") or "")
        if r in vistos.setdefault(a, set()):
            continue
        vistos[a].add(r)
        if len(por.setdefault(a, [])) < 10:
            por[a].append(p)
    return {a: l for a, l in por.items() if len(l) >= MINIMO}


def _cartoes(lista: list[dict], quando: str) -> str:
    e = html.escape
    out = []
    for i, p in enumerate(lista, 1):
        preco = float(p["preco"])
        de = float(p.get("de_loja") or 0)
        desc = round((1 - preco / de) * 100) if de > preco else 0
        motivos = [f"#{i} entre os mais vendidos da categoria no Mercado Livre"]
        if 0 < desc <= 60:
            motivos.append(f"{desc}% abaixo do preço riscado da loja")
        motivos.append("link direto no anúncio deste preço")
        img = e(p["imagem"].replace("http://", "https://", 1))
        out.append(f'''<li class="item" id="p{i}">
  <span class="pos">{i}</span>
  <a class="foto" href="{e(p["link"])}" target="_blank" rel="sponsored noopener" data-i="{i}"><img src="{img}" alt="{e(p["nome"][:90])}" loading="{"eager" if i < 3 else "lazy"}"></a>
  <div class="info">
    {'<img class="selo-img" src="/baloes/selo_mais_vendido_p.webp" alt="Mais vendido" width="150">' if i == 1 else '<img class="selo-img" src="/baloes/selo_oferta_de_hoje_p.webp" alt="Oferta de hoje" width="150">'}
    <h3>{e(p["nome"])}</h3>
    <ul class="motivos">{"".join(f"<li>{e(m)}</li>" for m in motivos)}</ul>
    <div class="preco">{f'<s>{_brl(de)}</s>' if 0 < desc <= 60 else ''}<b>{_brl(preco)}</b>{f'<em>-{desc}%</em>' if 0 < desc <= 60 else ''}</div>
    <small>preço visto em {quando} · pode mudar na loja</small>
    <a class="btn-ouro" href="{e(p["link"])}" target="_blank" rel="sponsored noopener" data-i="{i}">Ver no Mercado Livre <span class="seta" aria-hidden="true">→</span></a>
  </div>
</li>''')
    return "\n".join(out)


def _ld(lista: list[dict], titulo: str, url: str) -> str:
    d = {"@context": "https://schema.org", "@type": "ItemList", "name": titulo, "url": url,
         "itemListElement": [{"@type": "ListItem", "position": i, "name": p["nome"], "url": p["link"]}
                             for i, p in enumerate(lista, 1)]}
    return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")


def paginas() -> dict[str, str]:
    """{caminho relativo: html} — 'top10/index.html' e 'top10/<slug>/index.html'."""
    inst = json.loads(VITRINE.read_text(encoding="utf-8"))
    q = dt.datetime.fromisoformat(inst["quando"]).astimezone(dt.timezone(dt.timedelta(hours=-3)))
    quando = q.strftime("%d/%m às %Hh")
    mes = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
           "setembro", "outubro", "novembro", "dezembro"][q.month - 1]
    modelo = MODELO.read_text(encoding="utf-8")
    ls = listas()
    saida = {}
    nav = "".join(f'<a href="/top10/{NICHOS[a][0]}/">{NICHOS[a][2]} {html.escape(NICHOS[a][1])}</a>'
                  for a in NICHOS if a in ls)
    for a, lista in ls.items():
        slug, nome, emoji, frase = NICHOS[a]
        titulo = f"Top {len(lista)} {nome} mais vendidos no Mercado Livre ({mes} {q.year})"
        url = f"https://achadinhototal.com.br/top10/{slug}/"
        corpo = (modelo.replace("__TITULO__", html.escape(titulo))
                 .replace("__H1__", f'Top {len(lista)} <em>{html.escape(nome)}</em>')
                 .replace("__SUB__", html.escape(f"Os mais vendidos do Mercado Livre em {frase} — na ordem do próprio Mercado Livre, com o preço conferido em {quando}."))
                 .replace("__EMOJI__", emoji)
                 .replace("__NAV__", nav)
                 .replace("__ITENS__", _cartoes(lista, quando))
                 .replace("__LD__", _ld(lista, titulo, url))
                 .replace("__NICHO__", slug)
                 .replace("__CANON__", url))
        saida[f"top10/{slug}/index.html"] = corpo
    # indice
    cards = "".join(
        f'<li class="item nicho"><a class="ir" href="/top10/{NICHOS[a][0]}/">{NICHOS[a][2]} Top {len(ls[a])} {html.escape(NICHOS[a][1])} →</a></li>'
        for a in NICHOS if a in ls)
    saida["top10/index.html"] = (modelo.replace("__TITULO__", f"Top 10 do Mercado Livre por nicho ({mes} {q.year})")
                                 .replace("__H1__", "Top 10 do <em>Mercado Livre</em>")
                                 .replace("__SUB__", html.escape(f"Os mais vendidos de cada categoria, na ordem do próprio Mercado Livre, conferidos em {quando}."))
                                 .replace("__EMOJI__", "🏆").replace("__NAV__", nav).replace("__ITENS__", cards)
                                 .replace("__LD__", "{}").replace("__NICHO__", "indice")
                                 .replace("__CANON__", "https://achadinhototal.com.br/top10/"))
    return saida


def slug_do_nicho(area: str) -> str:
    return NICHOS.get(area, ("",))[0]


if __name__ == "__main__":
    for k, v in paginas().items():
        print(k, len(v))
