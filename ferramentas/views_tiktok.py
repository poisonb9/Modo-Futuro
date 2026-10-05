# -*- coding: utf-8 -*-
"""VIEWS de cada video no TikTok, sem API do TikTok e sem trabalho manual.

05/10/2026. O Buffer NAO devolve views (campo vazio em todos os posts de 14
dias). Mas devolve `externalLink` — o link do video publicado — e a PAGINA
PUBLICA do video traz `playCount`, curtidas, comentarios, shares e salvos no
JSON `__UNIVERSAL_DATA_FOR_REHYDRATION__` (medido: 843 e 648 views em dois
videos do Make). Mais o perfil: seguidores, curtidas totais e n. de videos.

Grava `estado/views_tiktok.jsonl` (uma linha por video por leitura) e
`estado/perfis_tiktok.jsonl` (uma por perfil por leitura).

    python -X utf8 ferramentas/views_tiktok.py            # todos os canais com token
    python -X utf8 ferramentas/views_tiktok.py --dias 14  # so' posts dos ultimos 14 dias
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import agendar_buffer as ab  # noqa: E402
from engine import canais_registro as cr  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "pt-BR,pt;q=0.9"}
DADOS = re.compile(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', re.S)
VIEWS = RAIZ / "estado" / "views_tiktok.jsonl"
PERFIS = RAIZ / "estado" / "perfis_tiktok.jsonl"


def _pagina(url: str) -> dict:
    r = requests.get(url, headers=UA, timeout=30)
    m = DADOS.search(r.text)
    return json.loads(m.group(1)).get("__DEFAULT_SCOPE__", {}) if m else {}


def video(url: str) -> dict | None:
    it = _pagina(url.split("?")[0]).get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct", {})
    st = it.get("stats")
    if not st:
        return None
    return {"views": int(st.get("playCount") or 0), "curtidas": int(st.get("diggCount") or 0),
            "comentarios": int(st.get("commentCount") or 0), "shares": int(st.get("shareCount") or 0),
            "salvos": int(st.get("collectCount") or 0), "duracao": (it.get("video") or {}).get("duration")}


def perfil(arroba: str) -> dict | None:
    st = _pagina(f"https://www.tiktok.com/@{arroba.lstrip('@')}").get(
        "webapp.user-detail", {}).get("userInfo", {}).get("stats")
    if not st:
        return None
    return {"seguidores": st.get("followerCount"), "curtidas_total": st.get("heartCount"),
            "videos": st.get("videoCount")}


def enviados(canal: str, dias: int) -> list[dict]:
    c = cr.CANAIS[canal]
    tok = (os.environ.get(c.env) or "").strip()
    if not tok:
        return []
    org = ab.consultar(tok, "query { account { organizations { id } } }")["account"]["organizations"][0]["id"]
    chs = ab.consultar(tok, """query($i: ChannelsInput!) { channels(input: $i) { id service } }""",
                       {"i": {"organizationId": org}})["channels"]
    tk = [x for x in chs if x["service"] == c.servico]
    if not tk:
        return []
    d = ab.consultar(tok, """query($i: PostsInput!) { posts(input: $i, first: 100) {
        edges { node { id sentAt externalLink text } } } }""",
        {"i": {"organizationId": org, "filter": {"status": ["sent"], "channelIds": [tk[0]["id"]]}}})
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    out = []
    for e in d["posts"]["edges"]:
        n = e["node"]
        if not n.get("externalLink") or not n.get("sentAt"):
            continue
        if datetime.fromisoformat(n["sentAt"].replace("Z", "+00:00")) < corte:
            continue
        out.append(n)
    return out


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--dias", type=int, default=21)
    o = a.parse_args()
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    resumo = []
    with VIEWS.open("a", encoding="utf-8") as fv, PERFIS.open("a", encoding="utf-8") as fp:
        for canal, c in cr.CANAIS.items():
            try:
                p = perfil(c.arroba)
                if p:
                    fp.write(json.dumps({"lido_em": agora, "canal": canal, "arroba": c.arroba, **p}) + "\n")
                posts = enviados(canal, o.dias)
            except Exception as e:  # noqa: BLE001 — um canal nao derruba os outros
                print(f"{canal:26} [!] {type(e).__name__}: {str(e)[:80]}")
                continue
            vs = []
            for n in posts:
                try:
                    v = video(n["externalLink"])
                except Exception:  # noqa: BLE001
                    v = None
                time.sleep(1.0)        # devagar: pagina publica, sem pressa
                if not v:
                    continue
                vs.append(v["views"])
                fv.write(json.dumps({"lido_em": agora, "canal": canal, "post_id": n["id"],
                                     "link": n["externalLink"].split("?")[0], "publicado_em": n["sentAt"],
                                     "titulo": (n.get("text") or "")[:90], **v}, ensure_ascii=False) + "\n")
            med = sorted(vs)[len(vs) // 2] if vs else 0
            resumo.append((canal, (p or {}).get("seguidores"), len(posts), len(vs), med, max(vs or [0])))
            print(f"{canal:26} seguidores {(p or {}).get('seguidores')!s:>6}  posts {len(posts):3}  "
                  f"lidos {len(vs):3}  views mediana {med:>6}  max {max(vs or [0]):>7}")
    if not resumo:
        print("nenhum canal lido (sem tokens do Buffer neste ambiente?)")


if __name__ == "__main__":
    main()
