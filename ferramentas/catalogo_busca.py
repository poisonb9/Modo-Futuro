# -*- coding: utf-8 -*-
"""Sobe o catalogo INTEIRO para a tabela de busca do site (supabase/15).

05/10/2026 (dono): a busca do site acha o produto no acervo inteiro, na hora,
mesmo que ele nao esteja na vitrine.

Fontes: o feed completo da Awin (lido em memoria, nada gravado em disco —
dono: "nao temos muito espaco") + a vitrine do Mercado Livre
(estado/ml_vitrine.json). Lojas em FORA_DO_SITE ficam de fora tambem aqui.

Roda na VPS (tarefa ModoFuturo_Catalogo_Busca, 1x por dia): a chave mestra do
banco (SUPABASE_PAT) so' existe aqui, de proposito.

    python -X utf8 ferramentas/catalogo_busca.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAIZ / ".env")
from engine import awin, buscas_site  # noqa: E402

LOTE = 800


def _lit(v) -> str:
    if v is None:
        return "null"
    return "'" + str(v).replace("'", "''") + "'"


def linhas() -> list[tuple]:
    import publicar_bio as pb
    fora = set(pb.FORA_DO_SITE)
    out = {}
    for p in awin.catalogo(teto=0):
        if p["loja"] in fora or not p.get("link") or not p.get("nome"):
            continue
        img = (p.get("imagem") or "").replace("http://", "https://", 1)
        if "noimage" in img:
            img = ""
        out["awin:" + str(p["id"])] = (p["nome"][:300], p["loja"].removesuffix(" BR"),
                                      (p.get("categoria") or "")[:120], p["preco"], img, p["link"])
    try:
        ml = json.loads((RAIZ / "estado" / "ml_vitrine.json").read_text(encoding="utf-8"))
        for p in ml.get("produtos") or []:
            out[str(p["id"])] = (p["nome"][:300], "Mercado Livre", p.get("categoria") or "",
                                 p["preco"], p.get("imagem") or "", p["link"])
    except (OSError, ValueError):
        print("catalogo_busca: sem ml_vitrine.json")
    return [(k, *v) for k, v in out.items()]


def _sql_teimoso(q: str, tentativas: int = 5):
    """A Management API derrubou a conexao no meio da 1a subida (05/10,
    WinError 10054). Lote e' idempotente (upsert): tenta de novo."""
    import time
    for i in range(tentativas):
        try:
            return buscas_site._sql(q)
        except Exception as e:  # noqa: BLE001
            if i == tentativas - 1:
                raise
            print(f"\n  [!] lote falhou ({type(e).__name__}) — de novo em {5 * (i + 1)} s")
            time.sleep(5 * (i + 1))


def subir(rows: list[tuple]) -> None:
    for i in range(0, len(rows), LOTE):
        valores = ",".join(
            "(" + ",".join([_lit(r[0]), _lit(r[1]), _lit(r[2]), _lit(r[3]),
                            f"{float(r[4]):.2f}", _lit(r[5]), _lit(r[6])]) + ",now())"
            for r in rows[i:i + LOTE])
        _sql_teimoso(
            "insert into catalogo_busca (id,nome,loja,categoria,preco,imagem,link,atualizado) values "
            + valores + " on conflict (id) do update set nome=excluded.nome, loja=excluded.loja, "
            "categoria=excluded.categoria, preco=excluded.preco, imagem=excluded.imagem, "
            "link=excluded.link, atualizado=now()")
        print(f"  {min(i + LOTE, len(rows))}/{len(rows)}", end="\r")
    # o que nao veio em 3 dias saiu do feed: sai da busca
    buscas_site._sql("delete from catalogo_busca where atualizado < now() - interval '3 days'")


def main() -> None:
    rows = linhas()
    if len(rows) < 1000:
        raise SystemExit(f"catalogo_busca: so' {len(rows)} produtos — feed falhou, nada mudado")
    subir(rows)
    n = buscas_site._sql("select count(*) n, pg_size_pretty(pg_total_relation_size('catalogo_busca')) tam "
                         "from catalogo_busca")[0]
    print(f"\ncatalogo_busca: {n['n']} produtos na busca ({n['tam']} no banco)")


if __name__ == "__main__":
    main()
