"""Investigador de defeitos nos produtos das ofertas (09/10/2026).

Passa nos produtos que estao NO AR ou AGENDADOS (estado/ofertas_feitas.jsonl,
ultimos N dias) e nas CANDIDATAS de hoje, e aponta defeito:

  foto_morta      foto principal fora do ar (404/403)
  link_quebrado   link de afiliado nao abre (>= 400 ou sem resposta)
  sumiu           produto saiu do catalogo atual (indisponivel / fora do feed)
  preco_subiu     preco de agora > anunciado + 5% (o comentario promete
                  "se mudar, eu aviso")
  replica         nome com cara de copia/replica (letras separadas por
                  hifen, "inspired", "replica", "1a linha")

Grava estado/defeitos_produtos.json e imprime o resumo. Nao muda nada:
quem corrige e' a guarda na origem (engine/ofertas.py).

    python -X utf8 ferramentas/investigar_produtos.py [--dias 14] [--sem-candidatas]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from engine import ofertas  # noqa: E402

SAIDA = RAIZ / "estado" / "defeitos_produtos.json"
TOLERANCIA_PRECO = 0.05
RE_REPLICA = re.compile(r"\b(?:[A-Z]{1,3}-){3,}[A-Z]{1,3}\b|inspired|r[ée]plica|1[ªa] ?linha|first copy",
                        re.IGNORECASE)


def _abre(url: str, faixa: bool = True) -> int:
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0 Safari/537.36"}
    if faixa:
        h["Range"] = "bytes=0-2047"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def _preco(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def investigar(dias: int = 14, candidatas: bool = True) -> dict:
    agora = ofertas.agora_todos()
    limite = (date.today() - timedelta(days=dias)).isoformat()
    no_ar: dict[str, dict] = {}
    for l in (RAIZ / "estado" / "ofertas_feitas.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            x = json.loads(l)
        except ValueError:
            continue
        if x.get("dia", "") >= limite:
            no_ar[str(x["id"])] = x          # o mais recente vence

    nomes: dict[str, str] = {}
    for l in (RAIZ / "estado" / "produtos_publicados.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            x = json.loads(l)
        except ValueError:
            continue
        if x.get("id"):
            nomes[str(x["id"])] = x.get("nome") or ""
    for pid, x in no_ar.items():
        x.setdefault("nome", nomes.get(pid) or nomes.get(pid.split(":", 1)[-1]) or "?")
    defeitos: list[dict] = []

    def checar(pid: str, base: dict, onde: str) -> list[dict]:
        out = []
        a = agora.get(pid)
        nome = (a or {}).get("nome") or base.get("nome") or "?"
        d = {"id": pid, "onde": onde, "canal": base.get("canal"), "nome": str(nome)[:80],
             "loja": (a or {}).get("loja")}
        if onde == "no_ar" and not a:
            out.append({**d, "defeito": "sumiu"})
            return out
        fotos = (a or {}).get("imagens") or []
        if isinstance(fotos, str):
            fotos = re.findall(r"https?://[^'\"\s\]]+", fotos)
        if fotos and _abre(fotos[0]) in (404, 410):
            out.append({**d, "defeito": "foto_morta", "url": fotos[0][:120]})
        link = (a or {}).get("link") or base.get("link")
        if link and onde == "no_ar":
            st = _abre(link, faixa=False)
            # 403/429 = bloqueio de robo / limite da loja (abre para gente);
            # 0 = sem resposta. So' 404/410 e' produto fora do ar de verdade.
            if st in (404, 410):
                out.append({**d, "defeito": "link_quebrado", "status": st})
        p_ag, p_an = _preco((a or {}).get("preco")), _preco(base.get("agora"))
        if onde == "no_ar" and p_ag and p_an and p_ag > p_an * (1 + TOLERANCIA_PRECO):
            out.append({**d, "defeito": "preco_subiu", "anunciado": p_an, "agora": p_ag})
        if RE_REPLICA.search(str(nome)):
            out.append({**d, "defeito": "replica"})
        return out

    tarefas = [(pid, x, "no_ar") for pid, x in no_ar.items()]
    if candidatas:
        tarefas += [(str(o["id"]), o, "candidata") for o in ofertas.candidatas(None)
                    if str(o["id"]) not in no_ar]
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(lambda t: checar(*t), tarefas):
            defeitos.extend(r)

    resumo: dict[str, dict[str, int]] = {}
    for d in defeitos:
        resumo.setdefault(d["onde"], {}).setdefault(d["defeito"], 0)
        resumo[d["onde"]][d["defeito"]] += 1
    rel = {"quando": datetime.now().isoformat(timespec="minutes"), "no_ar": len(no_ar),
           "candidatas": len(tarefas) - len(no_ar), "resumo": resumo, "defeitos": defeitos}
    SAIDA.write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    return rel


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=14)
    ap.add_argument("--sem-candidatas", action="store_true")
    a = ap.parse_args()
    rel = investigar(a.dias, not a.sem_candidatas)
    print(f"{rel['no_ar']} no ar/agendados, {rel['candidatas']} candidatas")
    for onde, r in rel["resumo"].items():
        print(f"  {onde}: " + ", ".join(f"{k} {v}" for k, v in sorted(r.items())))
    for d in rel["defeitos"]:
        if d["onde"] == "no_ar":
            extra = {k: v for k, v in d.items() if k not in ("id", "onde", "canal", "nome", "loja", "defeito")}
            print(f"  ⛔ {d['defeito']:<13} {d['canal']:<24} {d['id']:<20} {d['nome'][:45]} {extra or ''}")


if __name__ == "__main__":
    main()
