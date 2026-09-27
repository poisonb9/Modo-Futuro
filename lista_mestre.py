# -*- coding: utf-8 -*-
"""LISTA MESTRE: todo video que foi ou vai ao ar, com canal, data e hora.

⭐ 27/09/2026 (dono: "crie uma lista mestre de todos os videos que estao sendo
postados, com data, horario e canal, para sempre termos o controle"). Antes o
controle estava espalhado: registro de clipes (o que foi CORTADO), manifesto
(o que foi PUBLICADO na release) e `publicados.json` (o que o Buffer ENVIOU,
sem canal e sem hora).

Le' o Buffer de TODOS os canais (enviados + agendados) e ACUMULA em
`estado/lista_mestre.json`, chaveado pelo id do post no Buffer — o que saiu
nunca some da lista, mesmo quando a consulta do Buffer para de devolver posts
antigos. Gera `estado/LISTA_MESTRE.csv` (abre no Excel/Sheets), do mais novo
para o mais antigo, em horario de Sao Paulo.

    python lista_mestre.py            # atualiza e imprime o resumo
Roda de hora em hora no workflow `desempenho.yml`.
"""
from __future__ import annotations

import csv
import datetime
import json
import os
from pathlib import Path

import agendar_buffer as ab

RAIZ = Path(__file__).resolve().parent
ARQ = RAIZ / "estado" / "lista_mestre.json"
CSV = RAIZ / "estado" / "LISTA_MESTRE.csv"
SP = datetime.timezone(datetime.timedelta(hours=-3))


def _posts(token: str, org: str, canal: str, status: str, teto: int = 6) -> list[dict]:
    saida, cursor = [], None
    for _ in range(teto):
        d = ab.consultar(token, """
          query($i: PostsInput!, $a: String){ posts(input:$i, after:$a){
            pageInfo { hasNextPage endCursor }
            edges { node { id text dueAt sentAt } } } }""",
            {"i": {"organizationId": org,
                   "filter": {"status": [status], "channelIds": [canal]}},
             "a": cursor})["posts"]
        saida += [e["node"] for e in d["edges"]]
        if not d["pageInfo"]["hasNextPage"]:
            break
        cursor = d["pageInfo"]["endCursor"]
    return saida


def _sp(iso: str | None) -> tuple[str, str]:
    if not iso:
        return "", ""
    t = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(SP)
    return t.strftime("%Y-%m-%d"), t.strftime("%H:%M")


def atualizar() -> dict:
    try:
        from conferir_postados import CANAIS
    except Exception:  # noqa: BLE001
        CANAIS = {}
    base = json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else {}
    agora = datetime.datetime.now(datetime.timezone.utc).isoformat()[:19]
    for nome, (org, canal, env) in CANAIS.items():
        token = (os.environ.get(env) or "").strip()
        if not token:
            print(f"  [!] {nome}: sem {env} — NAO lido")
            continue
        for status in ("sent", "scheduled"):
            try:
                posts = _posts(token, org, canal, status)
            except Exception as e:  # noqa: BLE001
                print(f"  [!] {nome} {status}: falhou ({str(e)[:60]})")
                continue
            for p in posts:
                quando = p.get("sentAt") if status == "sent" else p.get("dueAt")
                data, hora = _sp(quando)
                txt = (p.get("text") or "").strip()
                reg = base.get(p["id"], {})
                reg.update({"canal": nome, "status": "postado" if status == "sent" else "agendado",
                            "data": data, "hora": hora,
                            "titulo": txt.split("\n")[0].split("#")[0].strip()[:120],
                            "visto_em": agora})
                reg.setdefault("primeira_vez", agora)
                base[p["id"]] = reg
            print(f"  {nome:20} {status:9} {len(posts):3} post(s)")
            if status == "scheduled":
                # agendado que sumiu da fila sem virar "postado" foi APAGADO no
                # Buffer — nao pode ficar para sempre como "agendado"
                vivos = {p["id"] for p in posts}
                for pid, r in base.items():
                    if (r.get("canal") == nome and r.get("status") == "agendado"
                            and pid not in vivos and r.get("visto_em") != agora):
                        r["status"] = "removido"
    ARQ.parent.mkdir(parents=True, exist_ok=True)
    ARQ.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    linhas = sorted(base.items(), key=lambda kv: (kv[1]["data"], kv[1]["hora"]), reverse=True)
    with open(CSV, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["data", "hora (SP)", "canal", "status", "titulo", "id_buffer"])
        for pid, r in linhas:
            w.writerow([r["data"], r["hora"], r["canal"], r["status"], r["titulo"], pid])
    tot = {}
    for r in base.values():
        t = tot.setdefault(r["canal"], {"postado": 0, "agendado": 0, "removido": 0})
        t[r["status"]] = t.get(r["status"], 0) + 1
    print("\nLISTA MESTRE:", len(base), "videos")
    for c, t in sorted(tot.items()):
        print(f"  {c:20} postados {t['postado']:4}  agendados {t['agendado']:3}")
    return base


if __name__ == "__main__":
    atualizar()
