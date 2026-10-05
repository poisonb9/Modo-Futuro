# -*- coding: utf-8 -*-
"""Radar de fontes do canal de NOSTALGIA ANOS 2000 (ex-@atefalhar, 28/09/2026).

Acha documentarios/ensaios FALADOS (em ingles) sobre os desenhos do inicio dos
anos 2000 — bastidores, "o que aconteceu com", curiosidades, criadores. O motor
dubla na voz do Bryan e narra a HISTORIA (nunca reposta episodio).
Saida: radar_nostalgia.json. Uso: python canais/atefalhar/radar_nostalgia.py
⚠️ O radar le' TITULO: antes de baixar, abrir e ouvir 20 s (tem de ser fala).
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

# Buscas: documentario/ensaio FALADO sobre cada desenho da lista do dono.
BUSCAS = [
    "courage the cowardly dog behind the scenes history",
    "ed edd n eddy history explained documentary",
    "rocket power what happened to the show",
    "rocket power history nickelodeon",
    "cartoon network 2000s history documentary",
    "nickelodeon 2000s shows history",
    "powerpuff girls history behind the scenes",
    "dexter's laboratory history creator",
    "hey arnold history what happened",
    "fairly oddparents history explained",
    "codename kids next door history",
    "cow and chicken history cartoon",
    "johnny bravo history cartoon network",
    "spongebob early seasons behind the scenes",
    "cartoon facts you didn't know 2000s",
    # ⭐ 05/10/2026 (dono: radar seco — 0 ineditos; precisa de algo extremamente viral)
    "things only 2000s kids remember",
    "2000s kids nostalgia you forgot",
    "pokemon anime history behind the scenes",
    "digimon history what happened",
    "dragon ball z history behind the scenes",
    "yu-gi-oh anime history censorship",
    "ben 10 history what happened",
    "jimmy neutron history",
    "kim possible history behind the scenes",
    "avatar the last airbender behind the scenes",
    "scooby doo history explained",
    "disney channel 2000s history",
    "jetix fox kids history",
    "cartoons that were cancelled too soon",
    "tamagotchi history 2000s",
    # ⭐ 05/10/2026 (dono: "menos dark e mais curiosidades")
    "cartoon fun facts you didn't know",
    "spongebob fun facts behind the scenes",
    "pokemon fun facts you didn't know",
    "disney channel fun facts 2000s",
    "cartoon network easter eggs you missed",
    "nickelodeon secrets fun facts",
    "how cartoons were made 2000s behind the scenes",
    "voice actors behind famous cartoons",
    "2000s kids toys fun facts",
    "dragon ball fun facts",
    "ben 10 fun facts",
    "scooby doo fun facts",
    "tom and jerry fun facts behind the scenes",
    "looney tunes fun facts",
    "the simpsons fun facts you didn't know",
    "shrek fun facts behind the scenes",
]

# sem fala ou sem historia: nao da' pra dublar nem narrar
VETO = [
    # 05/10/2026 (dono): menos dark — curiosidade, nao terror
    "dark", "creepy", "disturbing", "scary", "horror", "theory", "theories", "banned",
    "full episode", "episodio completo", "compilation", "compilado", "best moments",
    "funniest moments", "all intros", "intro", "theme song", "opening", "song",
    "music", "asmr", "no commentary", "shorts", "reaction", "react", "tier list",
    "ranking", "speedpaint", "drawing", "how to draw", "fan animation", "ai cover",
    "toy review", "unboxing", "live action", "trailer", "clip", "scene",
]

TEMA = [
    "fun facts", "easter egg", "did you know", "voice actor", "how it was made",
    "courage", "ed edd", "rocket power", "cartoon network", "nickelodeon", "nick",
    "powerpuff", "dexter", "hey arnold", "rugrats", "fairly odd", "invader zim",
    "kids next door", "cow and chicken", "johnny bravo", "spongebob", "cartoon",
    "history", "behind the scenes", "explained", "what happened", "documentary",
    "creator", "cancelled", "facts", "theory", "2000s",
    # ⭐ 05/10/2026 (temas novos das buscas novas)
    "pokemon",
    "digimon",
    "dragon ball",
    "yu-gi-oh",
    "ben 10",
    "teen titans",
    "jimmy neutron",
    "kim possible",
    "avatar",
    "scooby",
    "power rangers",
    "disney channel",
    "jetix",
    "fox kids",
    "tamagotchi",
    "2000s kids",
    "lost media",
    "banned",
    "childhood",
    "nostalgia",
    "cast",
]

FORA_DO_TEMA = ["movie review", "remake", "reboot trailer", "roblox", "fortnite",
                "minecraft", "gameplay"]

# documentario/ensaio falado: 8 a 30 min rende varios cortes de historia
MIN_BOM = (8.0, 30.0)


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

    # Faixa 8-30 min: documentario/ensaio falado (rende varios cortes de
    # historia). Curto demais costuma ser compilado; longo demais, live.
    if MIN_BOM[0] <= minutos <= MIN_BOM[1]:
        forma = 1.0
    elif 5.0 <= minutos < MIN_BOM[0] or MIN_BOM[1] < minutos <= 45.0:
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
    with open("radar_nostalgia.json", "w", encoding="utf-8") as f:
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
    print(f"\n{len(aval)} salvos em radar_nostalgia.json")
    print("[FAIXA] 4 a 8 min — onde mora a receita unica falada (as duas ja'")
    print("        aprovadas tem 5,2 e 5,4 min).")
    print("")
    print("⚠️ O radar NAO garante narracao continua: ele le' TITULO, e video")
    print("   mudo nem sempre se anuncia. Antes de baixar, ABRA e ouca 20s.")


if __name__ == "__main__":
    main()
