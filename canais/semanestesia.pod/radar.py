# -*- coding: utf-8 -*-
"""Radar de fontes do @semanestesia.pod (30/09/2026).

Cortes de podcast estrangeiro FALADO: disciplina + neurociencia da forca de
vontade. Faixa 8-30 min (clipe de podcast; podcast inteiro estoura o teto de
6h do Actions — ver README). Saida: radar_semanestesia.json.
Uso: python canais/semanestesia.pod/radar.py
⚠️ O radar le' TITULO: antes de cortar, ouvir 20 s (tem de ser fala).
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

# Buscas: posicionamento aprovado em 27/09 (_privado/PLANO_SEMANESTESIA.md):
# "Mente forte, com ciencia" — disciplina + o cerebro por tras dela. Os temas
# que MEDIRAM melhor no canal: Goggins/disciplina e neurociencia da forca de
# vontade (Huberman, dopamina, desistencia).
BUSCAS = [
    "david goggins 40 percent rule",
    "david goggins mindset interview clip",
    "david goggins callous mind",
    "huberman willpower anterior mid cingulate cortex",
    "huberman dopamine motivation clip",
    "huberman protocol discipline morning",
    "anna lembke dopamine nation podcast clip",
    "dopamine detox science explained podcast",
    "why your brain quits neuroscience",
    "jocko willink discipline equals freedom clip",
    "james clear atomic habits podcast clip",
    "cal newport deep work focus podcast",
    "matthew walker sleep willpower podcast",
    "carol dweck growth mindset explained",
    "cold plunge dopamine huberman",
    "delayed gratification neuroscience podcast",
    "how to stop procrastinating neuroscience",
    "mental toughness navy seal podcast clip",
]

# sem fala, ou fora do nucleo (seducao/relacionamento/beleza/IA sairam em 27/09)
VETO = [
    "full episode", "compilation", "music", "asmr", "shorts", "reaction", "react",
    "tier list", "motivational speech", "edit", "sigma", "trailer", "live",
    "audiobook",
]

TEMA = [
    "goggins", "huberman", "dopamine", "discipline", "willpower", "habit",
    "jocko", "mindset", "mental", "brain", "neuroscien", "procrastinat",
    "focus", "sleep", "motivation", "cold", "navy seal", "lembke", "clear",
    "newport", "walker", "dweck", "gratification", "quit",
]

FORA_DO_TEMA = ["dating", "seduc", "attract", "relationship", "women", "girlfriend",
                "beauty", "skincare", " ai ", "chatgpt", "crypto", "stock", "trading"]

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
    # 06/10/2026: busca passa pelo engine/busca_yt (cache 24 h, trava de cota,
    # reserva yt-dlp). Antes a cota esgotada virava "0 candidatos" calado.
    if "/search?" in monta_url("X"):
        import importlib.util as _iu
        _p = __import__("pathlib").Path(__file__).resolve().parents[2] / "engine" / "busca_yt.py"
        _sp = _iu.spec_from_file_location("busca_yt", _p)
        _m = _iu.module_from_spec(_sp); _sp.loader.exec_module(_m)
        return _m.buscar(monta_url, CHAVES)
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
            "publishedAfter": "2023-01-01T00:00:00Z",
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
    with open("radar_semanestesia.json", "w", encoding="utf-8") as f:
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
    print(f"\n{len(aval)} salvos em radar_semanestesia.json")
    print("[FAIXA] 4 a 8 min — onde mora a receita unica falada (as duas ja'")
    print("        aprovadas tem 5,2 e 5,4 min).")
    print("")
    print("⚠️ O radar NAO garante narracao continua: ele le' TITULO, e video")
    print("   mudo nem sempre se anuncia. Antes de baixar, ABRA e ouca 20s.")


if __name__ == "__main__":
    main()
