# -*- coding: utf-8 -*-
"""Cliques por produto no site mae — o EPC medido, e o kill de 30 dias.

    python -m engine.cliques              cliques por produto, ultimos 30 dias
    python -m engine.cliques --dias 7

## POR QUE EXISTE (regua v2, 17/09/2026)

`clique_produto` no Supabase (supabase/08_clique_produto.sql) e' anotado pela
pagina em cada clique (cartao, irmao, topo, avise). Le' com a chave mestra
(SUPABASE_PAT, Management API) — a mesma porta de `engine/buscas_site.py`.
Roda AQUI, nao na nuvem, pelo mesmo motivo.

E' o dado que o Ecommerce na Pratica manda usar ("30 dias sem vender, sai")
e que Hormozi chama de ganho por clique. Ali e ML nao dao por produto; o
site da'.
"""
from __future__ import annotations

from . import buscas_site as _bs


def por_produto(dias: int = 30) -> dict[str, dict]:
    """{produto_id: {"cliques": n, "ultimo": iso, "loja": ..}} nos ultimos N dias."""
    linhas = _bs._sql(
        "select produto, max(loja) as loja, count(*) as cliques, max(quando) as ultimo "
        "from clique_produto where quando > now() - make_interval(days => "
        + str(int(dias)) + ") group by produto")
    return {str(r["produto"]): {"cliques": int(r["cliques"] or 0),
                                "ultimo": r.get("ultimo"), "loja": r.get("loja")}
            for r in linhas}


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="cliques por produto no site")
    a.add_argument("--dias", type=int, default=30)
    o = a.parse_args()
    d = por_produto(o.dias)
    print(f"{sum(v['cliques'] for v in d.values())} clique(s) em {len(d)} produto(s), {o.dias} dias")
    for pid, v in sorted(d.items(), key=lambda kv: -kv[1]["cliques"])[:30]:
        print(f"  {v['cliques']:>4}  {v['loja'] or '':14} {pid}")


if __name__ == "__main__":
    main()
