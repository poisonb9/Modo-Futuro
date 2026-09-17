# -*- coding: utf-8 -*-
"""Tendências do Mercado Livre — o que o Brasil busca, por categoria.

    python -m engine.tendencias_ml --guardar     baixa e grava estado/ml_tendencias.json
    python -m engine.tendencias_ml               mostra o que esta' gravado

## POR QUE EXISTE (regua v2, 17/09/2026)

Ecommerce na Pratica, 6 videos [DEMONSTRADO]: "use a pagina de Tendencias
do Mercado Livre — e entre nas CATEGORIAS e subcategorias, nunca a tela
inicial, que e' generica". E' demanda medida, de graca:
`GET /trends/MLB` (geral) e `GET /trends/MLB/{categoria}`.

## O QUE ELA FAZ AQUI

1. **Momento da regua** (+0,3): produto cujo nome contem um termo em alta.
2. **Pauta**: `--pauta` lista os termos em alta que NAO casam com nada do
   catalogo — e' onde o garimpo devia procurar.

⚠️ E' RUIDOSA de proposito: "capivara", "rastrear meu pedido", "hello kitty"
aparecem. Termo curto (< 4 letras) e frases de navegacao saem; o resto fica,
porque o casamento exige o termo INTEIRO dentro do nome do produto — ruido
solto nao casa com nada.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESTADO = RAIZ / "estado" / "ml_tendencias.json"

# ⭐ as raizes que tocam as nossas areas (ids fixos do site MLB)
RAIZES = {
    "MLB1574": "Casa, Móveis e Decoração",
    "MLB1246": "Beleza e Cuidado Pessoal",
    "MLB1000": "Eletrônicos, Áudio e Vídeo",
    "MLB1648": "Informática",
    "MLB1276": "Esportes e Fitness",
    "MLB263532": "Ferramentas",
    "MLB5672": "Acessórios para Veículos",
    "MLB1144": "Games",
    "MLB1051": "Celulares e Telefones",
    "MLB1403": "Alimentos e Bebidas",
}
NAVEGACAO = re.compile(r"rastrear|meu pedido|ofertas? hoje|frete gr|cupom|promo[cç][aã]o|black friday|dia d[aoe]s?\b", re.I)


def normal(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", t.lower()).strip()


def guardar() -> dict:
    from . import mercadolivre as ml
    termos: dict[str, list[str]] = {}
    geral = [x.get("keyword", "") for x in ml._get("/trends/MLB")]
    termos["geral"] = geral
    for cid, nome in RAIZES.items():
        try:
            termos[nome] = [x.get("keyword", "") for x in ml._get(f"/trends/MLB/{cid}")]
        except Exception as e:                        # noqa: BLE001
            print(f"tendencias: {nome} falhou ({type(e).__name__})")
    limpos = sorted({normal(t) for L in termos.values() for t in L
                     if len(normal(t)) >= 4 and not NAVEGACAO.search(t)})
    dados = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "por_categoria": termos, "termos": limpos}
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"tendencias: {len(limpos)} termos de {len(termos)} listas -> {ESTADO.name}")
    return dados


def termos() -> list[str]:
    try:
        return list(json.loads(ESTADO.read_text(encoding="utf-8")).get("termos") or [])
    except (OSError, ValueError):
        return []


def especifico(t: str) -> bool:
    """Termo que nomeia um PRODUTO, nao uma categoria. Medido em 17/09:
    palavra solta ("cabo", "controle", "chaveiro", "notebook") casava com 15-27
    produtos a toa — e' prateleira, nao demanda. So' 2+ palavras conta
    ("caixa organizadora", "adaptador vga para hdmi"). Sinal raro e forte."""
    return " " in t


def em_alta(nome: str, lista: list[str] | None = None) -> str:
    """O termo em alta contido no nome do produto, ou "". Termo INTEIRO, com
    borda de palavra — "pato" nao casa com "sapato" — e ESPECIFICO."""
    n = " " + normal(nome) + " "
    for t in (lista if lista is not None else termos()):
        if especifico(t) and (" " + t + " ") in n:
            return t
    return ""


def pauta(nomes: list[str]) -> list[str]:
    """Termos em alta que nao casam com NENHUM nome do catalogo."""
    ts = termos()
    usados = {em_alta(n, ts) for n in nomes}
    return [t for t in ts if t not in usados]


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="tendencias do Mercado Livre")
    a.add_argument("--guardar", action="store_true")
    a.add_argument("--pauta", action="store_true", help="termos em alta sem produto no catalogo")
    o = a.parse_args()
    if o.guardar:
        guardar()
    if o.pauta:
        arq = RAIZ / "estado" / "produtos_publicados.jsonl"
        nomes = []
        if arq.exists():
            for l in arq.read_text(encoding="utf-8").splitlines():
                try:
                    nomes.append(json.loads(l).get("nome", ""))
                except ValueError:
                    pass
        p = pauta(nomes)
        print(f"{len(p)} termo(s) em alta sem produto no catalogo:")
        print("  " + " · ".join(p[:80]))
    if not (o.guardar or o.pauta):
        t = termos()
        print(f"{len(t)} termos gravados: " + " · ".join(t[:40]))


if __name__ == "__main__":
    main()
