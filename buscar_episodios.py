# -*- coding: utf-8 -*-
"""Acha os episodios ANTERIORES de um video que faz parte de uma serie.

Pedido do Bryan em 01/09/2026: um corte de "afundo e agachamento perfeito"
comeca com a apresentadora dizendo que e' o DIA 3 — e o canal nunca teve o
dia 1 nem o 2. "Vamos segurar, detectar, baixar e postar em ordem."

Este e' o terceiro passo. Os dois primeiros ja' existem: a selecao marca
`depende_de_anterior`, e o agendador segura o clipe.

## O QUE ELE FAZ, E O QUE NAO GARANTE

⚠️ ELE SO' PROPOE. Devolve os candidatos com link, para o Bryan olhar e
decidir. Baixar sozinho seria confiar num casamento por titulo que erra: um
"Day 2" do mesmo canal pode ser de outra serie, e uma serie pode nao ter
numero nenhum no titulo ("Leg day", "Push day", "Pull day").

⚠️ E A BUSCA E' DENTRO DO CANAL, nunca no YouTube inteiro. Episodio anterior
de uma serie e' da mesma pessoa; procurar solto traria video de outro criador
com titulo parecido, que e' o pior resultado possivel — parece certo e nao e'.

## COMO ELE ACHA

Duas passadas, da mais confiavel para a menos:

  1. NUMERO NO TITULO. Se o video atual tem "day 3" / "parte 3" / "ep 3",
     procura no mesmo canal os titulos com o mesmo padrao e numero MENOR.
     E' o unico caminho que da' ordem garantida.

  2. VIZINHANCA NO TEMPO. Sem numero, lista o que o canal publicou ANTES
     deste video, do mais proximo para o mais distante. Nao e' ordem de
     serie — e' ordem de publicacao, e o Bryan decide olhando.

⚠️ A DIFERENCA ENTRE AS DUAS E' DITA NA SAIDA. Apresentar palpite com a mesma
cara de certeza seria pior que nao buscar.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3"

# "day 3", "dia 3", "parte 3", "part 3", "ep 3", "episode 3", "#3"
PADRAO_NUM = re.compile(
    r"\b(day|dia|part|parte|ep|episode|episodio|week|semana)\s*#?\s*(\d{1,2})\b",
    re.IGNORECASE)


def _chaves() -> list[str]:
    """Mesma convencao do engine/keys.py."""
    ks = []
    if v := os.getenv("YOUTUBE_API_KEY"):
        ks.append(v.strip())
    for i in range(2, 41):
        if v := os.getenv(f"YOUTUBE_API_KEY_{i}"):
            ks.append(v.strip())
    if not ks:
        sys.exit("Nenhuma YOUTUBE_API_KEY no ambiente.")
    return ks


def _get(caminho: str, params: dict) -> dict:
    """GET com rodizio de chave. Erro de cota pula pra proxima."""
    ultimo = None
    for chave in _chaves():
        p = dict(params, key=chave)
        url = f"{API}/{caminho}?" + urllib.parse.urlencode(p)
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            ultimo = e
            continue
    raise RuntimeError(f"YouTube recusou em todas as chaves: {ultimo}")


def numero_do_titulo(titulo: str) -> tuple[str, int] | None:
    """('day', 3) se o titulo marcar posicao numa serie; None se nao."""
    m = PADRAO_NUM.search(titulo or "")
    return (m.group(1).lower(), int(m.group(2))) if m else None


def anteriores(video_id: str, quantos: int = 6) -> dict:
    """Candidatos a episodio anterior, com o metodo que os achou."""
    v = _get("videos", {"part": "snippet", "id": video_id})
    itens = v.get("items") or []
    if not itens:
        raise RuntimeError(f"video nao encontrado: {video_id}")
    snip = itens[0]["snippet"]
    canal_id, titulo, publicado = (snip["channelId"], snip["title"],
                                   snip["publishedAt"])

    marca = numero_do_titulo(titulo)
    achados, metodo = [], ""

    if marca:
        # ---- passada 1: mesmo padrao, numero MENOR ----------------------
        palavra, n = marca
        metodo = f"numero no titulo ('{palavra} {n}')"
        busca = _get("search", {"part": "snippet", "channelId": canal_id,
                                "q": palavra, "type": "video",
                                "maxResults": 50, "order": "date"})
        for it in busca.get("items", []):
            t = it["snippet"]["title"]
            outra = numero_do_titulo(t)
            if outra and outra[0] == palavra and outra[1] < n:
                achados.append({"n": outra[1], "id": it["id"]["videoId"],
                                "titulo": t,
                                "quando": it["snippet"]["publishedAt"][:10]})
        achados.sort(key=lambda x: x["n"])

    if not achados:
        # ---- passada 2: o que veio ANTES no tempo -----------------------
        # ⚠️ Isto NAO e' ordem de serie. E' ordem de publicacao, e vale como
        # pista, nao como resposta.
        metodo = (metodo + " — sem resultado; caindo pra ") if metodo else ""
        metodo += "vizinhanca no tempo (PALPITE, nao ordem de serie)"
        busca = _get("search", {"part": "snippet", "channelId": canal_id,
                                "type": "video", "maxResults": 25,
                                "order": "date", "publishedBefore": publicado})
        for it in busca.get("items", [])[:quantos]:
            achados.append({"n": None, "id": it["id"]["videoId"],
                            "titulo": it["snippet"]["title"],
                            "quando": it["snippet"]["publishedAt"][:10]})

    return {"video": {"id": video_id, "titulo": titulo,
                      "canal": snip["channelTitle"], "marca": marca},
            "metodo": metodo, "candidatos": achados[:quantos]}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("video", help="id ou URL do YouTube do video que depende")
    p.add_argument("--quantos", type=int, default=6)
    a = p.parse_args()

    vid = a.video
    if "youtu" in vid:
        m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", vid)
        vid = m.group(1) if m else vid

    r = anteriores(vid, a.quantos)
    v = r["video"]
    print(f"video: {v['titulo'][:70]}")
    print(f"canal: {v['canal']}")
    print(f"marca de serie: {v['marca'] or 'nenhuma no titulo'}")
    print(f"metodo: {r['metodo']}")
    print()
    if not r["candidatos"]:
        print("  nenhum candidato — o canal nao tem video anterior visivel.")
        return
    # ⚠️ CERTEZA E PALPITE SAIEM MARCADOS DIFERENTE. Apresentar os dois com a
    # mesma cara seria pior que nao buscar.
    for c in r["candidatos"]:
        marca = f"[{c['n']}]" if c["n"] is not None else "[?]"
        print(f"  {marca} {c['quando']}  {c['titulo'][:62]}")
        print(f"      https://www.youtube.com/watch?v={c['id']}")
    print()
    print("  [n] = posicao confirmada pelo titulo    [?] = so' veio antes no tempo")


if __name__ == "__main__":
    main()
