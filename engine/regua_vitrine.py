# -*- coding: utf-8 -*-
"""A Nota de Vitrine (regua_vitrine): uma regua so' para o que sobe, a ordem, o fogo e o ML.

## DE ONDE VEM (17/09/2026)

`CRITERIOS_DA_VITRINE.md` — 429 fichas do banco Maestros da IA traduzidas
para os dados que JA' medimos. Decisao do Bryan: **35/30** (Rende antes de
Confianca, por pouco).

    VITRINE = 35·Rende + 30·Confianca + 20·Momento + 15·Mostravel

- Rende      = o que rende por venda (preco x comissao), na regua da PROPRIA
               loja (o Kabum a 2% nao e' medido pela regua do Ali a 9%).
               Hormozi (margem, EPC); meticsmedia (organico aceita margem menor).
- Confianca  = Ali: 60% da % positivas (>= 95 cheio, 90-95 metade —
               meticsmedia: ">= 90, ideal > 95") + 40% do volume de vendas
               (>= 1.000 cheio, >= 100 metade — "so' entra quem ja' vende");
               ML: vendedores (>= 5 cheio, 2-4 metade);
               externa: ZERO ate' haver dado (o feed Awin nao traz review em
               loja nenhuma — medido em 17/09). Zero aqui e' honesto, nao
               e' castigo.
- Momento    = Movers and Shakers: queda medida por nos + crescimento do
               volume (vendidos no Ali, vendedores no ML). "Queda com volume
               subindo e' oportunidade" (garimpo).
- Mostravel  = da' video: views do post quando houver; senao, ter imagem.

## ⛔ O QUE ESTA REGUA NAO FAZ

Nao tira nada da SERIE nem da loja: tira da VITRINE (ordem, fogo, 2a
posicao). Piso e' "fora da vitrine", nunca "fora do dado".
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

PESOS = {"rende": 35, "confianca": 30, "momento": 20, "mostravel": 15}

# pisos: fora da vitrine (ordem por nota = 0), com o motivo nomeado
PISO_NOTA_ALI = 90.0
PISO_VENDEDORES_ML = 2
COMMODITY_VENDEDORES = 30

LOJAS_COM_NOTA = ("AliExpress",)
LOJAS_COM_VENDEDORES = ("Mercado Livre",)


def _f(x) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def referencias(dados: list[dict]) -> dict[str, float]:
    """{loja: ganho de referencia} — o p90 do `ganho` na loja. E' a regua de
    Rende: ganho / referencia, teto 1. Loja sem produto com ganho > 0 fica
    com referencia 0 (e Rende 0 para todos os dela)."""
    por_loja: dict[str, list[float]] = {}
    for p in dados:
        g = _f(p.get("ganho"))
        if g > 0:
            por_loja.setdefault(p.get("loja") or "", []).append(g)
    ref: dict[str, float] = {}
    for loja, gs in por_loja.items():
        gs.sort()
        ref[loja] = gs[min(len(gs) - 1, int(round(0.9 * (len(gs) - 1))))]
    return ref


# ⭐ FAIXA DE IMPULSO: Jungle Scout (US$ 19-100), meticsmedia (US$ 20-100) e o
# teto de R$ 150 do Bryan. Acima dela o clique converte menos — o ganho por
# venda continua alto, mas a VENDA e' menos provavel. Medido em 17/09: sem
# isto o topo inteiro ficava entre R$ 134 e R$ 244.
IMPULSO_TETO = 150.0
IMPULSO_ACIMA = 0.7


def _preco(p: dict) -> float:
    try:
        return float(str(p.get("preco", "0")).replace("R$", "").replace(".", "")
                     .replace(",", ".").strip() or 0)
    except ValueError:
        return 0.0


def rende(p: dict, ref: dict[str, float]) -> float:
    r = ref.get(p.get("loja") or "", 0.0)
    if r <= 0:
        return 0.0
    base = min(1.0, _f(p.get("ganho")) / r)
    return base * (IMPULSO_ACIMA if _preco(p) > IMPULSO_TETO else 1.0)


def confianca(p: dict) -> float:
    loja = p.get("loja") or ""
    if loja in LOJAS_COM_NOTA:
        n = _f(p.get("nota"))
        parte_nota = 1.0 if n >= 95 else 0.5 if n >= 90 else 0.0
        # ⭐ PROVA SOCIAL = VOLUME (meticsmedia: "ordene por pedidos; so' entra
        # quem ja' vende"). Medido em 17/09: sem isto o topo virava "os mais
        # caros" e os carregadores de R$ 8 com milhares de vendas sumiam.
        v = int(_f(p.get("vendas")))
        parte_vol = 1.0 if v >= 1000 else 0.5 if v >= 100 else 0.0
        return 0.6 * parte_nota + 0.4 * parte_vol
    if loja in LOJAS_COM_VENDEDORES:
        v = p.get("vendedores") or []
        hoje = int(v[0]) if v else 0
        parte_vend = 1.0 if hoje >= 5 else 0.5 if hoje >= PISO_VENDEDORES_ML else 0.0
        # ⭐ v2 (17/09): o "termometro" do vendedor (Ecommerce na Pratica) e
        # frete gratis, medidos na reconferencia horaria. Sem reputacao no
        # instantaneo (pagina velha), a parte dela e' 0 — nao e' castigo, e'
        # falta de dado; o peso volta pros vendedores.
        rep = p.get("reputacao") or {}
        nivel = int(rep.get("nivel") or 0)
        parte_rep = 1.0 if nivel >= 5 else 0.6 if nivel == 4 else 0.0
        parte_frete = 1.0 if p.get("frete_gratis") else 0.0
        if rep:
            conf = 0.5 * parte_rep + 0.3 * parte_vend + 0.2 * parte_frete
        else:
            conf = 0.8 * parte_vend + 0.2 * parte_frete
        # ⚠️ CURVA B: > 30 vendedores e' commodity (guerra de preco, margem
        # zero — ENP; e "muito vendido no ML nao rende video", memoria 14/09)
        if hoje > COMMODITY_VENDEDORES:
            conf *= 0.8
        return conf
    # ⚠️ externa (Awin): sem review no feed, sem decreto. O que existe e' a
    # REPUTACAO DA LOJA no Reclame Aqui, lida a mao pelo Bryan (o site
    # bloqueia leitura automatica — medido 17/09: 403 e desafio anti-bot) e
    # guardada com data em estado/reputacao_lojas.json. Escala do RA:
    # >= 8 otimo, 7-8 bom, 6-7 regular, < 6 ruim. Sem numero = 0.
    return _reputacao(loja)


REPUTACAO = Path(__file__).resolve().parent.parent / "estado" / "reputacao_lojas.json"
REPUTACAO_VALIDADE_DIAS = 60


def _reputacao(loja: str) -> float:
    try:
        d = json.loads(REPUTACAO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0.0
    r = d.get(loja) or {}
    try:
        nota = float(r.get("nota") or 0)
        em = date.fromisoformat(str(r.get("em") or ""))
    except (TypeError, ValueError):
        return 0.0
    if (date.today() - em).days > REPUTACAO_VALIDADE_DIAS:
        return 0.0            # numero velho nao e' numero
    return 1.0 if nota >= 8 else 0.7 if nota >= 7 else 0.4 if nota >= 6 else 0.0


def momento(p: dict) -> float:
    q = _f(p.get("queda"))
    parte_queda = 1.0 if q >= 15 else 0.6 if q >= 5 else 0.0
    cresc = 0.0
    vendeu = p.get("vendeu") or []
    if vendeu and int(vendeu[0]) >= 20:
        cresc = 1.0
    vend = p.get("vendedores") or []
    if len(vend) >= 2 and int(vend[1]) >= 1:
        cresc = max(cresc, 0.7)
    # ⚠️ quem SUBIU e ainda esta' abaixo do maior (ja_esteve) nao e'
    # momento: e' o oposto. A pagina ja' rebaixa por 0,7; aqui e' 0.
    if p.get("ja_esteve") and (p["ja_esteve"] or {}).get("preco"):
        parte_queda = 0.0
    return min(1.0, 0.6 * parte_queda + 0.4 * cresc)


def mostravel(p: dict) -> float:
    if _f(p.get("views_acima_da_mediana")) > 0:
        return 1.0
    return 0.5 if p.get("imagem") else 0.0


def piso(p: dict) -> str:
    """Motivo de ficar FORA da vitrine, ou "" se passa."""
    loja = p.get("loja") or ""
    if loja in LOJAS_COM_NOTA and p.get("nota") not in (None, "", 0, 0.0):
        if _f(p.get("nota")) < PISO_NOTA_ALI:
            return f"nota {_f(p.get('nota')):.0f}% < {PISO_NOTA_ALI:.0f}%"
    if loja in LOJAS_COM_VENDEDORES:
        v = p.get("vendedores") or []
        if v and int(v[0]) < PISO_VENDEDORES_ML:
            return f"{int(v[0])} vendedor(es) < {PISO_VENDEDORES_ML}"
    return ""


def nota(p: dict, ref: dict[str, float]) -> tuple[float, dict[str, float], str]:
    """(0-100, eixos 0-1, motivo do piso ou ""). Com piso, a nota e' 0."""
    eixos = {"rende": rende(p, ref), "confianca": confianca(p),
             "momento": momento(p), "mostravel": mostravel(p)}
    motivo = piso(p)
    total = 0.0 if motivo else round(sum(PESOS[k] * v for k, v in eixos.items()), 1)
    return total, eixos, motivo


def pontuar(dados: list[dict]) -> dict[str, float]:
    """Escreve `vitrine_nota` (0-100) e `vitrine_fora` (motivo) em cada
    cartao. Devolve as referencias por loja (pra relato)."""
    ref = referencias(dados)
    for p in dados:
        total, eixos, motivo = nota(p, ref)
        p["vitrine_nota"] = total
        p["vitrine_fora"] = motivo
    return ref
