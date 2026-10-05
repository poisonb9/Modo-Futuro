# -*- coding: utf-8 -*-
"""Vitrine do Mercado Livre: os MAIS VENDIDOS de cada categoria, na loja.

04/10/2026 (dono): "estamos perdendo muito ouro que esta' no Mercado Livre e
nao esta' na nossa loja, as pessoas compram muito pelo Mercado Livre... temos
que ter uma loja bem abastecida com o portfolio do Mercado Livre."

⭐ O `/highlights` (mais vendidos da categoria) foi descartado em 15/09 PARA
VIDEO — mais vendido do ML e' commodity, ninguem assiste a clipe de papel
higienico (engine/mercadolivre.py). Para a LOJA e' o contrario: commodity com
entrega em 2 dias e comissao de ate' 16% e' exatamente o que o amigo do dono
compra. Este modulo e' a loja; o garimpo continua sendo o video.

    python -X utf8 -m engine.ml_vitrine --guardar     # nuvem, 1x por dia
    python -X utf8 -m engine.ml_vitrine               # so' mostra

Grava `estado/ml_vitrine.json` no MESMO formato do `awin_catalogo.json`
(loja "Mercado Livre"), e o `paginas/publicar_bio.py` monta a categoria
externa "Mercado Livre" a partir dele. Cada produto tambem ganha ponto na
serie de precos (`precos_vistos.jsonl`), para a queda medida e o grafico.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from . import mercadolivre as ml

RAIZ = Path(__file__).resolve().parent.parent
ESTADO = RAIZ / "estado" / "ml_vitrine.json"
LOJA = "Mercado Livre"
POR_CATEGORIA = 20

# Categoria do ML -> area da nossa loja (o menu "Categoria").
# ⭐ SAUDE vem com as FILHAS (suplemento mora la' dentro) — pedido do dono:
# "quero muitos produtos de multivitaminicos... isso vende muito".
CATEGORIAS = {
    "MLB264586": "Saúde",            # Saúde (suplementos, cuidados)
    "MLB1246": "Beleza",             # Beleza e Cuidado Pessoal
    "MLB1276": "Academia",           # Esportes e Fitness
    "MLB1574": "Casa",               # Casa, Móveis e Decoração
    "MLB5726": "Cozinha",            # Eletrodomésticos
    "MLB1000": "Eletrônicos",        # Eletrônicos, Áudio e Vídeo
    "MLB1648": "Eletrônicos",        # Informática
    "MLB1051": "Eletrônicos",        # Celulares e Telefones
    "MLB1144": "Eletrônicos",        # Games
    "MLB263532": "Casa",             # Ferramentas
    "MLB1384": "Infantil",           # Bebês
    "MLB1132": "Infantil",           # Brinquedos e Hobbies
    "MLB1071": "Pet",                # Animais
    "MLB1430": "Moda",               # Calçados, Roupas e Bolsas
    "MLB1747": "Automotivo",         # Acessórios para Veículos
}
# com filhas: os mais vendidos da MAE escondem nichos inteiros (suplemento
# some atras de fralda e termometro). Cada filha entra com POR_FILHA.
COM_FILHAS = {"MLB264586", "MLB1246", "MLB1276"}
POR_FILHA = 10


def _num(v) -> float:
    """"R$ 1.234,56" (formato do mais_vendidos) -> 1234.56."""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v or "").replace("R$", "").strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _filhas(cat: str) -> list[str]:
    try:
        d = ml._get(f"/categories/{cat}")
    except Exception as e:  # noqa: BLE001
        print(f"  [!] filhas de {cat}: {type(e).__name__}")
        return []
    return [c["id"] for c in d.get("children_categories") or []
            if c["id"] not in ml.FORA]


def colher() -> list[dict]:
    vistos: dict[str, dict] = {}
    for cat, area in CATEGORIAS.items():
        alvos = [(cat, POR_CATEGORIA)]
        if cat in COM_FILHAS:
            alvos += [(f, POR_FILHA) for f in _filhas(cat)]
        for alvo, n in alvos:
            try:
                prods = ml.mais_vendidos(alvo, n)
            except Exception as e:  # noqa: BLE001 — uma categoria nao derruba as outras
                print(f"  [!] {alvo}: {type(e).__name__} {str(e)[:60]}")
                continue
            for p in prods:
                pid = str(p.get("_id") or p.get("id") or "")
                if not pid or pid in vistos:
                    continue
                vistos[pid] = {
                    "id": pid, "nome": (p.get("nome") or "").strip(),
                    "preco": _num(p.get("preco")),
                    "imagem": p.get("imagem") or p.get("foto") or "",
                    "link": p.get("link") or "", "loja": LOJA,
                    "categoria": area, "categoria_ml": alvo,
                    "comissao": float(p.get("comissao") or ml.comissao_base(alvo) or 0),
                    "marca": "", "de_loja": _num(p.get("de")), "origem": "mercadolivre",
                }
            print(f"  {alvo} ({area}): +{len(prods)}  total {len(vistos)}")
            time.sleep(0.5)   # o ML limita por aplicacao (429 medido em 16/09)
    return [p for p in vistos.values() if p["nome"] and p["preco"] > 0 and p["link"]]


def guardar() -> dict:
    prods = colher()
    if not prods:
        raise SystemExit("ml_vitrine: nada colhido — instantaneo anterior mantido")
    inst = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "produtos": prods}
    ESTADO.write_text(json.dumps(inst, ensure_ascii=False), encoding="utf-8")
    try:
        from . import precos
        n = precos.anotar_serie({p["id"]: (p["preco"], 0) for p in prods}, LOJA)
        print(f"ml_vitrine: serie +{n}")
    except Exception as e:  # noqa: BLE001
        print(f"ml_vitrine: serie nao anotada ({type(e).__name__})")
    por: dict[str, int] = {}
    for p in prods:
        por[p["categoria"]] = por.get(p["categoria"], 0) + 1
    print(f"ml_vitrine: {len(prods)} produtos — " + ", ".join(f"{k} {v}" for k, v in sorted(por.items())))
    return inst


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--guardar", action="store_true")
    o = a.parse_args()
    if o.guardar:
        guardar()
    else:
        for p in colher()[:30]:
            print(f"{p['categoria']:12} R$ {p['preco']:>8.2f}  {p['nome'][:60]}")


if __name__ == "__main__":
    main()
