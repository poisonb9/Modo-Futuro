"""Categorias dos produtos e o canal de cada uma (04/10/2026, dono).

Um produto ganha UMA categoria, e a categoria decide o canal das ofertas.
E' a mesma regra-mae da divisao por nicho (engine/ofertas.py, NICHO): cada
canal fala de um assunto so', porque e' isso que faz o seguidor ficar.

    fatura.chora (Pago Menos)        eletronicos
    achadinhos.instantaneos          casa e cozinha
    achadinhototal (Achei pra voce)  todo o resto

⭐ Ordem de decisao: 1) a loja, quando a loja inteira e' de um assunto so'
(Arno e' cozinha, Soldiers e' suplemento); 2) a categoria que o feed da loja
manda; 3) palavras do nome. O que nao casar cai em "outros" — aparece no
`resumo()` para a lista crescer, nunca some calado.

    python -X utf8 -m engine.categorias      # quantos produtos em cada uma
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# slug -> nome de exibicao
CATEGORIAS = {
    "eletronicos": "Eletrônicos e tecnologia",
    "casa_cozinha": "Casa e cozinha",
    "beleza": "Beleza e maquiagem",
    "saude_farmacia": "Saúde e farmácia",
    "suplementos": "Suplementos",
    "calcados": "Calçados",
    "moda": "Moda e roupas",
    "bolsas_acessorios": "Bolsas e acessórios",
    "esporte": "Esporte",
    "infantil": "Infantil",
    "automotivo": "Automotivo",
    "outros": "Outros",
}

CANAL_DA_CATEGORIA = {
    "eletronicos": "fatura.chora",
    "casa_cozinha": "achadinhos.instantaneos",
}
CANAL_PADRAO = "achadinhototal"

# A loja inteira e' de um assunto so'.
POR_LOJA = {
    "Arno BR": "casa_cozinha",
    "Brinox Shop BR": "casa_cozinha",
    "Stanley BR": "casa_cozinha",
    "Shark-Ninja BR": "casa_cozinha",
    "Soldiers Nutrition BR": "suplementos",
    "Drogal BR": "saude_farmacia",
    "Drogaria Venancio BR": "saude_farmacia",
    "Farmácias Indiana BR": "saude_farmacia",
    "Oceane BR": "beleza",
    "Camilovers BR": "beleza",
    "Clovis Calçados BR": "calcados",
    "Carraro BR": "calcados",
    "Lauri Esporte": "esporte",
    "Radiale Pneus": "automotivo",
}

# (padrao na categoria do feed OU no nome, minusculo) -> categoria. A primeira
# que casar ganha, entao o mais especifico vem antes.
PALAVRAS = [
    (r"infantil|kids|mother & kids|bebe|beb[eê]", "infantil"),
    (r"eletroport|home appliances|cozinha|panela|liquidific|air ?fryer|cafeteir|garrafa|"
     r"copo|caneca|home & garden|furniture|home improvement|casa inteligente", "casa_cozinha"),
    (r"comput|hardware|perif|gamer|games|[aá]udio|fone|headset|conectividade|energia|"
     r"celular|smartphone|phones|consumer electronics|c[aâ]mera|drone|seguran|telefonia|"
     r"monitor|notebook|teclado|mouse|office|escrit", "eletronicos"),
    (r"maquiagem|skincare|cabelo|beauty|perfum|batom", "beleza"),
    (r"bag|bolsa|satchel|shoulder|tote|hobo|transversal|acess[oó]rio|jewelry|rel[oó]gio",
     "bolsas_acessorios"),
    (r"t[eê]nis|sapato|sand[aá]lia|chinelo|bota|cal[cç]ado", "calcados"),
    (r"roupa|clothing|underwear|camiseta|vestido|cal[cç]a|feminino|masculino|unissex|"
     r"men|women", "moda"),
    (r"automo", "automotivo"),
]


def categoria_de(loja: str, categoria_feed: str = "", nome: str = "") -> str:
    if loja in POR_LOJA:
        return POR_LOJA[loja]
    for alvo in (categoria_feed, nome):
        t = (alvo or "").lower()
        for padrao, cat in PALAVRAS:
            if re.search(padrao, t):
                return cat
    return "outros"


def canal_de(categoria: str) -> str:
    return CANAL_DA_CATEGORIA.get(categoria, CANAL_PADRAO)


def resumo() -> dict[str, dict[str, int]]:
    """{categoria: {loja: n}} do catalogo Awin de hoje."""
    prods = json.load(open(RAIZ / "estado" / "awin_catalogo.json", encoding="utf-8"))["produtos"]
    out: dict[str, dict[str, int]] = {}
    for p in prods:
        c = categoria_de(p["loja"], p.get("categoria", ""), p.get("nome", ""))
        out.setdefault(c, {}).setdefault(p["loja"], 0)
        out[c][p["loja"]] += 1
    return out


if __name__ == "__main__":
    for cat, lojas in sorted(resumo().items(), key=lambda x: -sum(x[1].values())):
        print(f"{sum(lojas.values()):5}  {CATEGORIAS[cat]:28} -> {canal_de(cat):24} "
              + ", ".join(f"{l} {n}" for l, n in sorted(lojas.items(), key=lambda x: -x[1])))
