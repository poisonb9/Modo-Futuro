# -*- coding: utf-8 -*-
"""Radar de fontes para o @atefalhar — disciplina, corpo e dor.

DIFERENCA PRO RADAR DOS OUTROS CANAIS

O radar da cozinha e o do Modo Futuro ordenam por HYPE puro: views, views/hora
e engajamento. Aqui entram duas colunas que eles nao tem, e que sao as que
decidem se o corte e' possivel:

  DURACAO  O GitHub Actions mata o job em 6 horas. Em 30/08/2026 dois runs do
           Sem Anestesia (mesma receita deste canal) morreram nesse teto, com
           fontes de 124 e 157 minutos. Fonte curta cabe; podcast inteiro nao.

  IDIOMA   Fonte ja' em portugues NAO e' traduzida nem dublada. Medido: 83 min
           contra 2h01 no mesmo passo, e zero cota de Gemini. Quando houver
           equivalente em PT, ela ganha.

Por isso a nota final aqui pondera hype PELO custo de produzir.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

def _chaves() -> list[str]:
    """Le as chaves do AMBIENTE — nunca do codigo.

    A primeira versao deste arquivo tinha as cinco chaves escritas aqui
    dentro. Este repositorio e' PUBLICO: commitar assim queima as cinco, e
    apagar depois nao resolve, porque o valor fica no historico. O unico
    conserto seria revogar todas no console do Google.

    Mesma convencao do `engine/keys.py`: `YOUTUBE_API_KEY` e depois
    `YOUTUBE_API_KEY_2`, `_3`, ... Os valores vivem no `.env` local e nos
    secrets do Actions, fora de qualquer repositorio.
    """
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    ks = []
    if v := os.getenv("YOUTUBE_API_KEY"):
        ks.append(v.strip())
    for i in range(2, 21):
        if v := os.getenv(f"YOUTUBE_API_KEY_{i}"):
            ks.append(v.strip())
    if not ks:
        sys.exit("Nenhuma YOUTUBE_API_KEY no ambiente. "
                 "Elas estao em Desktop/Tiktok/CREDENCIAIS.md, fora do repo.")
    return ks


CHAVES = _chaves()

# Buscas em ingles e em portugues, de proposito. A fonte PT sai muito mais
# barata, entao ela precisa estar no mesmo funil, nao numa rodada separada.
BUSCAS_EN = [
    "david goggins discipline podcast",
    "cameron hanes endurance podcast",
    "jocko willink discipline podcast",
    "andrew huberman exercise protocol",
    "bodybuilding mindset interview pain",
]
BUSCAS_PT = [
    "podcast disciplina treino portugues",
    "podcast musculacao mentalidade",
    "cortes podcast treino disciplina",
]

# Termos que denunciam material que o motor NAO consegue usar. Nao e' filtro
# de gosto: e' o que ja' custou run.
VETO = ["shorts", "compilation", "compilado", "satisfying", "music",
        "no talking", "asmr", "workout mix", "gym motivation music"]


def http(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def com_rodizio(monta_url):
    """Tenta cada chave: a cota de busca estoura rapido (429 medido em 30/08)."""
    ultimo = None
    for k in CHAVES:
        try:
            return http(monta_url(k))
        except Exception as e:
            ultimo = e
            continue
    raise RuntimeError(f"todas as {len(CHAVES)} chaves falharam: {ultimo}")


def buscar(termo, n=8):
    def url(k):
        q = urllib.parse.urlencode({
            "part": "snippet", "q": termo, "type": "video",
            "maxResults": n, "order": "viewCount",
            "videoDuration": "medium",   # 4 a 20 min: o que CABE no teto
            "publishedAfter": "2025-01-01T00:00:00Z",
            "key": k})
        return "https://www.googleapis.com/youtube/v3/search?" + q
    return com_rodizio(url).get("items", [])


def detalhes(ids):
    def url(k):
        q = urllib.parse.urlencode({
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(ids), "key": k})
        return "https://www.googleapis.com/youtube/v3/videos?" + q
    return com_rodizio(url).get("items", [])


def segundos(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def avaliar(v):
    st = v.get("statistics", {})
    views = int(st.get("viewCount", 0) or 0)
    likes = int(st.get("likeCount", 0) or 0)
    dur = segundos(v["contentDetails"]["duration"])
    pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
    horas = max(1.0, (datetime.now(timezone.utc) - pub).total_seconds() / 3600)
    idioma = (v["snippet"].get("defaultAudioLanguage")
              or v["snippet"].get("defaultLanguage") or "")
    pt = idioma.lower().startswith("pt")

    # Hype, na mesma moeda dos outros radares.
    vph = views / horas
    eng = (likes / views * 100) if views else 0

    # E o custo. Fonte curta cabe no teto; fonte PT pula traducao e dublagem.
    if dur <= 20 * 60:
        custo = 1.0
    elif dur <= 45 * 60:
        custo = 0.7
    elif dur <= 90 * 60:
        custo = 0.35
    else:
        custo = 0.15          # podcast inteiro: so' com recorte
    if pt:
        custo *= 1.6          # medido: 83 min contra 2h01, e zero cota Gemini

    nota = (min(views / 1000, 100) * 0.5 + min(vph, 100) * 0.3
            + min(eng * 10, 100) * 0.2) * custo
    return {
        "id": v["id"], "titulo": v["snippet"]["title"],
        "canal": v["snippet"]["channelTitle"],
        "url": f"https://www.youtube.com/watch?v={v['id']}",
        "views": views, "views_h": round(vph, 1), "eng": round(eng, 2),
        "dur_min": round(dur / 60, 1), "pt": pt, "nota": round(nota, 1),
    }


def main():
    vistos, brutos = set(), []
    for termo in BUSCAS_EN + BUSCAS_PT:
        try:
            itens = buscar(termo)
        except Exception as e:
            print(f"  [!] busca falhou ({termo[:35]}): {str(e)[:70]}")
            continue
        novos = [i["id"]["videoId"] for i in itens
                 if i["id"]["videoId"] not in vistos]
        vistos.update(novos)
        print(f"  {termo[:42]:<44} {len(novos)} novo(s)")
        for j in range(0, len(novos), 50):
            brutos += detalhes(novos[j:j + 50])

    aval = []
    for v in brutos:
        t = (v["snippet"]["title"] + " " + v["snippet"]["channelTitle"]).lower()
        if any(x in t for x in VETO):
            continue
        aval.append(avaliar(v))
    aval.sort(key=lambda x: -x["nota"])

    # Salva ANTES de imprimir. Em 30/08 um emoji no titulo derrubou a saida no
    # console do Windows (cp1252) e levou o resultado da rodada junto — a
    # rodada custou cota de YouTube e nao sobrou nada dela.
    with open("radar_atefalhar.json", "w", encoding="utf-8") as f:
        json.dump(aval, f, ensure_ascii=False, indent=1)

    def seguro(t):
        return t.encode("ascii", "replace").decode("ascii")

    print(f"\n{len(aval)} candidato(s) apos o veto\n")
    print(f"{'#':<3} {'nota':>5} {'min':>6} {'idio':>5} {'views':>9} "
          f"{'v/h':>7} {'eng%':>5}  titulo")
    print("-" * 108)
    for i, v in enumerate(aval[:20], 1):
        cabe = "OK " if v["dur_min"] <= 45 else "REC"
        print(f"{i:<3} {v['nota']:>5} {v['dur_min']:>6} "
              f"{('PT' if v['pt'] else 'en'):>5} {v['views']:>9} "
              f"{v['views_h']:>7} {v['eng']:>5}  [{cabe}] {seguro(v['titulo'])[:52]}")
    print(f"\n{len(aval)} salvos em radar_atefalhar.json")
    print("[OK ] cabe no teto de 6h    [REC] so' com --recorte")


if __name__ == "__main__":
    main()
