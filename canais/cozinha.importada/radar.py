# -*- coding: utf-8 -*-
"""Radar de fontes para o @cozinha.internacional — receita UNICA e FALADA.

⚠️ ESTE MOTOR NAO CORTA PRA COZINHA. Quem corta e' o `bryanaw2121-sketch/
pipeline`, que converte medidas (°F, xicara, polegada) — este aqui nao
converte nada disso, e em 03/09/2026 oito receitas sairam daqui com
Fahrenheit para publico brasileiro (ver `engine/escopo.py`). O radar so'
ACHA a fonte; o bruto vai pra pasta DOCES do Drive e o corte acontece la'.

## O CRITERIO QUE MANDA E' SEGUNDOS POR RECEITA

O corte tem de ser **uma receita inteira entre 65 e 210s**. Isso decide
tudo, e derruba material que qualquer radar de hype adoraria:

  - video de LISTA ("50 dicas", "5 jantares em 30 minutos", "5 habilidades")
    quebra o criterio: cada item dura segundos e o corte parte no meio. Foi
    por isso que o Gordon Ramsay de 39M views foi descartado em 06/09.
  - fonte MUDA nao serve. O run #12 provou: a "AMAZING Dessert Compilation"
    do Preppy Kitchen rendeu clipes com **4,3s de narracao em 91s de video**.
    Sem narracao nao ha' o que traduzir, dublar nem CONVERTER — e a conversao
    e' o produto deste canal.
  - os tres maiores canais de comida do radar foram descartados por serem
    silenciosos.

A guarda de clipe mudo (`engine/fala.py`, densidade < 0,5 palavra/s) pega o
mudo depois. Pegar na FONTE custa uma linha; pegar depois custa duas horas
de corte.

## O QUE JA' FOI APROVADO POR ESSE CRITERIO

Em 06/09/2026 entraram duas, escolhidas a mao pelo mesmo criterio:

    French Onion Soup | Basics with Babish   8,08M views   5,2 min
    Easy TIRAMISU Cake | No-Bake Dessert     4,22M views   5,4 min

⚠️ As duas tem **~5 minutos**. Nao e' coincidencia: 5 min e' onde mora a
receita unica falada. Abaixo de 4 costuma ser *satisfying* sem narracao;
acima de 10, ou e' lista, ou e' vlog com receita no meio. A nota abaixo
pondera por isso, e a faixa esta' escrita como numero, nao como intencao.

## FONTE EM PORTUGUES SAI

Mesma tese do @atefalhar: o valor e' trazer o que ninguem traduziu. A Ana
Maria Braga saiu da lista por ja' estar em portugues — sem nada a traduzir
E sem nada a converter, que e' o produto.

⚠️ O IDIOMA DA API MENTE (medido em 30/08 no radar do @atefalhar: video em
hindi declarado `en`). Por isso o filtro real e' o ALFABETO do titulo, e o
campo de idioma so' serve pra recusar PT quando ele se declara.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def _chaves() -> list[str]:
    """Le as chaves do AMBIENTE — nunca do codigo. Repositorio PUBLICO."""
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

# ⚠️ AS BUSCAS MIRAM A RECEITA, NAO O CANAL DE COMIDA. "how to make X" e
# "recipe" trazem receita unica; "best of", "compilation" e "tips" trazem
# lista, que e' exatamente o que este canal nao consegue cortar.
#
# Os nomes proprios sao os MEDIDOS: Babish rendeu a French Onion Soup ja'
# aprovada, e o README aponta Chef Jean-Pierre e Joshua Weissman como a
# aposta melhor por falarem sem parar.
BUSCAS = [
    "binging with babish basics recipe",
    "chef jean pierre recipe",
    "joshua weissman recipe how to make",
    "how to make classic french recipe step by step",
    "easy no bake dessert recipe tutorial",
    "authentic italian pasta recipe how to make",
    "homemade bread recipe step by step",
    "korean street food recipe how to make",
    "mexican tacos authentic recipe how to make",
    "classic dessert recipe explained",
]

# Material que o motor da cozinha NAO consegue usar. Nao e' gosto: cada um
# destes ja' custou run ou foi descartado a mao.
VETO = [
    # sem narracao — o run #12 e os tres canais silenciosos descartados
    "satisfying", "no talking", "asmr", "silent", "relaxing", "music",
    "cinematic", "aesthetic", "mukbang", "eating show",
    # lista: quebra o criterio de segundos por receita (o Gordon de 39M)
    "compilation", "compilado", "best of", "top 10", "top 5", "tips",
    "dicas", "hacks", "mistakes", "things you", "ways to", "recipes",
    "ideas", "menu", "meal prep", "week of", "everything you",
    # nao e' receita
    "shorts", "reaction", "review", "taste test", "vlog", "challenge",
    "ranking", "tier list", "restaurant tour", "kitchen tour",
]

# ⚠️ FILTRO DE TEMA POSITIVO, largo de proposito. No radar do
# @truque.importado uma lista curta demais derrubou tres videos bons em
# silencio — e recusa silenciosa e' pior que ruido, porque ninguem a percebe.
TEMA = [
    "recipe", "receita", "how to make", "how to cook", "cook", "cooking",
    "bake", "baking", "roast", "braise", "fry", "grill", "simmer",
    "dessert", "cake", "bread", "dough", "pasta", "soup", "sauce",
    "chicken", "beef", "pork", "fish", "rice", "egg", "cheese",
    "chocolate", "cookie", "pie", "tart", "custard", "curry", "stew",
    "babish", "jean-pierre", "jean pierre", "weissman", "kitchen", "chef",
]

# Vizinhos que a busca traz e o canal NAO cobre.
FORA_DO_TEMA = ["diet", "weight loss", "calories", "keto", "protein shake",
                "dog food", "cat food", "survival", "prison", "airline"]

# A faixa onde mora a receita unica falada, MEDIDA nas duas ja' aprovadas
# (5,2 e 5,4 min). Ver o cabecalho.
MIN_BOM = (4.0, 8.0)


def _escrita_estranha(texto: str) -> bool:
    """O titulo esta' em alfabeto que nao e' o latino?

    Herdado do radar do @atefalhar, onde foi MEDIDO: em 30/08 um video em
    hindi veio com `defaultAudioLanguage: en`. O campo mente; o alfabeto nao.
    Piso de 15% pra que um emoji ou um nome acentuado nao recuse titulo bom.
    """
    letras = [c for c in texto if c.isalpha()]
    if not letras:
        return False
    fora = sum(1 for c in letras if ord(c) > 0x2E80 or 0x0370 <= ord(c) <= 0x1CFF)
    return fora / len(letras) > 0.15


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
            # medium = 4 a 20 min. Receita unica falada vive na ponta de
            # baixo disso; `short` (<4 min) e' onde mora o satisfying mudo.
            "videoDuration": "medium",
            "publishedAfter": "2024-01-01T00:00:00Z",
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
    minutos = dur / 60
    pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
    horas = max(1.0, (datetime.now(timezone.utc) - pub).total_seconds() / 3600)
    idioma = (v["snippet"].get("defaultAudioLanguage")
              or v["snippet"].get("defaultLanguage") or "")
    pt = idioma.lower().startswith("pt")

    vph = views / horas
    eng = (likes / views * 100) if views else 0

    # ⚠️ O PESO DA DURACAO E' O CRITERIO DO CANAL, nao um detalhe de
    # ordenacao. Fora da faixa de 4 a 8 min a fonte quase sempre e' lista ou
    # vlog, e nenhuma das duas rende receita inteira em 65-210s.
    if MIN_BOM[0] <= minutos <= MIN_BOM[1]:
        forma = 1.0
    elif 3.0 <= minutos < MIN_BOM[0] or MIN_BOM[1] < minutos <= 12.0:
        forma = 0.6
    else:
        forma = 0.25

    nota = (min(views / 1000, 100) * 0.5 + min(vph, 100) * 0.3
            + min(eng * 10, 100) * 0.2) * forma
    return {
        "id": v["id"], "titulo": v["snippet"]["title"],
        "canal": v["snippet"]["channelTitle"],
        "url": f"https://www.youtube.com/watch?v={v['id']}",
        "views": views, "views_h": round(vph, 1), "eng": round(eng, 2),
        "dur_min": round(minutos, 1), "pt": pt,
        "na_faixa": MIN_BOM[0] <= minutos <= MIN_BOM[1],
        "nota": round(nota, 1),
    }


def main():
    vistos, brutos = set(), []
    for termo in BUSCAS:
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
    # Contar POR MOTIVO, nao um total. Filtro que come demais so' aparece se
    # cada corte tiver o seu numero.
    corte = {"veto": 0, "tema": 0, "escrita": 0, "portugues": 0}
    for v in brutos:
        titulo = v["snippet"]["title"]
        t = (titulo + " " + v["snippet"]["channelTitle"]).lower()
        if any(x in t for x in VETO):
            corte["veto"] += 1
            continue
        if _escrita_estranha(titulo):
            corte["escrita"] += 1
            continue
        if not any(x in t for x in TEMA) or any(x in t for x in FORA_DO_TEMA):
            corte["tema"] += 1
            continue
        item = avaliar(v)
        if item["pt"]:
            corte["portugues"] += 1
            continue
        aval.append(item)
    aval.sort(key=lambda x: -x["nota"])

    # ⚠️ SALVA ANTES DE IMPRIMIR. Em 30/08 um emoji no titulo derrubou a
    # saida no console do Windows (cp1252) e levou junto o resultado de uma
    # rodada que ja' tinha custado cota.
    with open("radar_cozinha.json", "w", encoding="utf-8") as f:
        json.dump(aval, f, ensure_ascii=False, indent=1)

    def seguro(t):
        return t.encode("ascii", "replace").decode("ascii")

    print("")
    print(f"{len(aval)} candidato(s)   |   cortados: "
          f"{corte['veto']} veto (mudo/lista), {corte['tema']} fora do tema, "
          f"{corte['escrita']} alfabeto nao-latino, "
          f"{corte['portugues']} em portugues")
    print("")
    print(f"{'#':<3} {'nota':>5} {'min':>6} {'views':>9} {'v/h':>7} "
          f"{'eng%':>5}  titulo")
    print("-" * 104)
    for i, v in enumerate(aval[:20], 1):
        marca = "FAIXA" if v["na_faixa"] else "  -  "
        print(f"{i:<3} {v['nota']:>5} {v['dur_min']:>6} {v['views']:>9} "
              f"{v['views_h']:>7} {v['eng']:>5}  [{marca}] "
              f"{seguro(v['titulo'])[:46]}")
    print(f"\n{len(aval)} salvos em radar_cozinha.json")
    print("[FAIXA] 4 a 8 min — onde mora a receita unica falada (as duas ja'")
    print("        aprovadas tem 5,2 e 5,4 min).")
    print("")
    print("⚠️ O radar NAO garante narracao continua: ele le' TITULO, e video")
    print("   mudo nem sempre se anuncia. Antes de baixar, ABRA e ouca 20s.")
    print("⚠️ O corte NAO acontece neste motor. Bruto vai pra pasta DOCES do")
    print("   Drive; quem corta e' o bryanaw2121-sketch/pipeline, que converte")
    print("   medidas. Ver engine/escopo.py.")


if __name__ == "__main__":
    main()
