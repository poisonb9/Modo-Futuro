# -*- coding: utf-8 -*-
"""Ranking de desempenho POR CLIPE (nao por video-fonte).

    python -X utf8 ferramentas/ranking_clipes.py                 # top 30, todos os canais
    python -X utf8 ferramentas/ranking_clipes.py --canal truque.importado --top 15
    python -X utf8 ferramentas/ranking_clipes.py --vencedores     # so' os >= 2x o patamar do canal
    python -X utf8 ferramentas/ranking_clipes.py --json saida.json

⛔ POR QUE POR CLIPE. Somar as views de todos os clipes de uma fonte premia a
fonte que rendeu MAIS clipes, nao a que rendeu clipe BOM: medido em 25/09/2026,
sete clipes de ~500 viravam o "#2" da lista, enquanto por clipe so' existia um
vencedor de verdade (14.778) e o resto encostava no piso de ~500.

⭐ O QUE E' VENCEDOR: alcance >= FATOR x o PATAMAR do canal (3o quartil, so'
dos posts com JOVEM_DIAS ou mais). Cada canal tem seu piso; comparar o make com
o de chips pela escala absoluta misturaria publicos diferentes.

⛔ NAO A MEDIANA: medido em 25/09/2026, quase todo post encosta num patamar de
~500 e a mediana (~190) fica abaixo dele — 2x a mediana marcava 53 clipes como
vencedores, ou seja, o patamar inteiro.

⚠️ AS MEDIDAS, ditas sem enfeite:
  - `desempenho.jsonl` traz `views` vazio em todos os posts — o numero e' o
    ALCANCE (`reach`) do Buffer. E' ele que ordena.
  - Vale a ULTIMA leitura de cada post (pelo `lido_em`).
  - Post com menos de JOVEM_DIAS ainda esta' subindo: sai marcado, nao
    fora — tirar esconderia um vencedor nascendo.
  - O casamento com o manifesto (fonte, inicio do corte, url do mp4) e' pelo
    comeco do TITULO normalizado. O que nao casa sai com fonte "?".
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESEMPENHO = RAIZ / "desempenho.jsonl"
FATOR = 2.0
JOVEM_DIAS = 3
PREFIXO = 40          # caracteres do titulo normalizado usados no casamento


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").split("\n")[0].split("#")[0])
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def ultimas_leituras() -> list[dict]:
    ult: dict[str, dict] = {}
    for linha in DESEMPENHO.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        k = d.get("post_id")
        if k and (k not in ult or d.get("lido_em", "") > ult[k].get("lido_em", "")):
            ult[k] = d
    return list(ult.values())


def carregar_manifesto(arq: str | None) -> dict:
    if arq:
        return json.loads(Path(arq).read_text(encoding="utf-8"))
    sys.path.insert(0, str(RAIZ))
    import agendar_buffer as ab
    return ab.manifesto(ab._token_github())


def alcance(d: dict) -> int:
    return int(d.get("views") or d.get("reach") or 0)


def casar(posts: list[dict], man: dict) -> None:
    """Pendura em cada post o item do manifesto de mesmo titulo (ou nada)."""
    idx: dict[str, dict] = {}
    for chave, v in man.items():
        k = _norm(v.get("titulo") or v.get("legenda") or "")[:PREFIXO]
        if len(k) >= 12:
            idx.setdefault(k, dict(v, _chave=chave))
    for p in posts:
        k = _norm(p.get("titulo") or "")[:PREFIXO]
        p["_man"] = idx.get(k) or next(
            (v for kk, v in idx.items() if len(k) >= 12 and (kk.startswith(k) or k.startswith(kk))),
            None)


def montar(posts: list[dict]) -> list[dict]:
    agora = datetime.now(timezone.utc)
    def maduro(p: dict) -> bool:
        try:
            pub = datetime.fromisoformat(p["publicado_em"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            return False
        return (agora - pub).total_seconds() / 86400 >= JOVEM_DIAS

    medianas = {}                                   # o PATAMAR: 3o quartil
    for canal in {p.get("canal") for p in posts}:
        vals = [alcance(p) for p in posts
                if p.get("canal") == canal and alcance(p) > 0 and maduro(p)]
        medianas[canal] = (statistics.quantiles(vals, n=4)[2] if len(vals) >= 4
                           else (max(vals) if vals else 0))
    linhas = []
    for p in posts:
        a, med = alcance(p), medianas.get(p.get("canal")) or 0
        try:
            pub = datetime.fromisoformat(p["publicado_em"].replace("Z", "+00:00"))
            dias = (agora - pub).total_seconds() / 86400
        except (KeyError, ValueError):
            dias = None
        inter = int(p.get("curtidas") or 0) + int(p.get("comentarios") or 0) + int(p.get("shares") or 0)
        m = p.get("_man") or {}
        linhas.append({
            "alcance": a,
            "fator": round(a / med, 1) if med else None,
            "vencedor": bool(med) and a >= FATOR * med,
            "jovem": dias is not None and dias < JOVEM_DIAS,
            "dias": round(dias, 1) if dias is not None else None,
            "engaj_pct": round(100 * inter / a, 1) if a else None,
            "canal": p.get("canal"),
            "publicado": (p.get("publicado_em") or "")[:10],
            "titulo": (m.get("titulo") or p.get("titulo") or "").strip(),
            "fonte": m.get("fonte") or "?",
            "inicio_s": m.get("inicio_s"),
            "url": m.get("url"),
            "ab_titulo": m.get("ab_titulo"),
            "post_id": p.get("post_id"),
        })
    linhas.sort(key=lambda x: -x["alcance"])
    for i, l in enumerate(linhas, 1):
        l["pos"] = i
    return linhas, medianas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--canal")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--vencedores", action="store_true", help=f"so' os >= {FATOR}x o patamar do canal")
    ap.add_argument("--manifesto", help="manifesto.json local (padrao: o das releases)")
    ap.add_argument("--json", help="grava a lista inteira neste arquivo")
    a = ap.parse_args()

    posts = ultimas_leituras()
    if a.canal:
        posts = [p for p in posts if p.get("canal") == a.canal]
    try:
        casar(posts, carregar_manifesto(a.manifesto))
    except Exception as e:                            # noqa: BLE001
        print(f"[!] manifesto indisponivel ({type(e).__name__}) — ranking sem fonte/inicio")
        for p in posts:
            p["_man"] = None
    linhas, medianas = montar(posts)
    if a.json:
        Path(a.json).write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")

    casados = sum(1 for l in linhas if l["fonte"] != "?")
    print(f"{len(linhas)} clipe(s) medido(s); {casados} casado(s) com o manifesto")
    print("patamar (3o quartil) por canal: " + " · ".join(
        f"{c} {int(m)}" for c, m in sorted(medianas.items(), key=lambda x: -x[1])))
    print(f"vencedor = alcance >= {FATOR}x o patamar do canal · (j) = menos de {JOVEM_DIAS} dias no ar\n")
    mostrar = [l for l in linhas if l["vencedor"]] if a.vencedores else linhas
    print(f"{'#':>3} {'alcance':>7} {'x pat':>5} {'eng%':>5} {'canal':16} {'publicado':10}  titulo")
    for l in mostrar[:a.top]:
        marca = "★" if l["vencedor"] else " "
        print(f"{l['pos']:>3} {l['alcance']:>7} {l['fator'] or 0:>5} {l['engaj_pct'] or 0:>5} "
              f"{(l['canal'] or '')[:16]:16} {l['publicado']:10} {marca}{'(j)' if l['jovem'] else ''} "
              f"{l['titulo'][:58]}")
    if a.vencedores and not mostrar:
        print("  nenhum clipe passou da regua")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
