# -*- coding: utf-8 -*-
"""Qual fonte baixar a seguir, pelo desempenho medido de cada tema.

    python -X utf8 ferramentas/proxima_fonte.py [--canal truque.importado] [--marcar ID]

Le a lista de candidatos (arquivo privado) e o `desempenho.jsonl`. Regras:
  1. tema QUENTE (posts dos ultimos 4 dias com alcance >= 2x a mediana do
     canal) e com candidato livre -> vai primeiro.
  2. no maximo 1 fonte por tema por dia.
  3. senao, a ordem da lista.
Registra cada decisao em `_privado/serie/decisoes.jsonl` para medir depois.
"""
from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FONTES = RAIZ / "_privado" / "serie" / "fontes_make.json"
DECISOES = RAIZ / "_privado" / "serie" / "decisoes.jsonl"
DESEMPENHO = RAIZ / "desempenho.jsonl"
DIAS_QUENTE = 4
FATOR_QUENTE = 2.0


def _posts(canal: str) -> list[dict]:
    ult: dict[str, dict] = {}
    for linha in DESEMPENHO.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if d.get("canal") != canal:
            continue
        k = d.get("post_id")
        if k not in ult or d["lido_em"] > ult[k]["lido_em"]:
            ult[k] = d
    return list(ult.values())


def _alcance(d: dict) -> float:
    return float(d.get("views") or d.get("reach") or 0)


def temas_quentes(posts: list[dict], temas: dict[str, list[str]]) -> dict[str, float]:
    """{tema: fator sobre a mediana} dos temas acima de FATOR_QUENTE."""
    if not posts:
        return {}
    mediana = statistics.median([_alcance(p) for p in posts]) or 1.0
    corte = datetime.now(timezone.utc) - timedelta(days=DIAS_QUENTE)
    recentes = [p for p in posts
                if datetime.fromisoformat(p["publicado_em"].replace("Z", "+00:00")) >= corte]
    saida = {}
    for tema, chaves in temas.items():
        do_tema = [_alcance(p) for p in recentes
                   if any(c in (p.get("titulo") or "").lower() for c in chaves)]
        if do_tema and max(do_tema) >= FATOR_QUENTE * mediana:
            saida[tema] = round(max(do_tema) / mediana, 1)
    return saida


def escolher(dados: dict, posts: list[dict]) -> tuple[dict | None, str]:
    hoje = datetime.now().date().isoformat()
    # ⛔ 25/09/2026 (dono): "nunca baixe um video atras do outro". Ja' houve
    # download hoje -> nada hoje. E `nao_antes` segura o candidato ate' a data.
    if any(c.get("baixado_em") == hoje for c in dados["candidatos"]):
        return None, "ja' houve download hoje — o proximo so' amanha (regra: nunca em sequencia)"
    livres = [c for c in dados["candidatos"] if not c.get("usado")
              and (c.get("nao_antes") or "") <= hoje]
    if not livres:
        return None, "sem candidato liberado hoje (ver nao_antes) ou lista vazia"
    ja_hoje = {c["idol"] for c in dados["candidatos"] if c.get("baixado_em") == hoje}
    temas = dict(dados.get("idols_ja_postados", {}))
    for c in dados["candidatos"]:
        temas.setdefault(c["idol"], c.get("apelidos", [c["idol"]]))
    quentes = temas_quentes(posts, temas)
    for tema, fator in sorted(quentes.items(), key=lambda kv: -kv[1]):
        for c in livres:
            if c["idol"] == tema and tema not in ja_hoje:
                return c, f"tema QUENTE: {tema} a {fator}x a mediana nos ultimos {DIAS_QUENTE} dias"
    for c in livres:
        if c["idol"] not in ja_hoje:
            return c, "ordem da lista" + (f" (quentes sem candidato: {', '.join(quentes)})" if quentes else "")
    return None, "todos os temas livres ja' tiveram fonte hoje"


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--canal", default="truque.importado")
    a.add_argument("--marcar", metavar="ID", help="marca o candidato como baixado hoje")
    o = a.parse_args()
    dados = json.loads(FONTES.read_text(encoding="utf-8"))
    if o.marcar:
        for c in dados["candidatos"]:
            if c["id"] == o.marcar:
                c["usado"] = True
                c["baixado_em"] = datetime.now().date().isoformat()
        FONTES.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
        print("marcado:", o.marcar)
        return
    c, motivo = escolher(dados, _posts(o.canal))
    reg = {"quando": datetime.now().isoformat(timespec="minutes"),
           "escolhido": c and c["id"], "idol": c and c["idol"], "motivo": motivo}
    DECISOES.parent.mkdir(parents=True, exist_ok=True)
    with DECISOES.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    if c:
        print(f"PROXIMA: {c['rotulo']}  https://www.youtube.com/watch?v={c['id']}")
    print("motivo:", motivo)


if __name__ == "__main__":
    main()
