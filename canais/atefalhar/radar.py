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

RECALIBRADO EM 31/08/2026 — e uma das duas regras acima FOI REVOGADA.

  FONTE EM PORTUGUES SAI, POR ORDEM DO BRYAN.  A rodada de 30/08 devolveu 6
  fontes PT, e as quatro melhores notas da lista eram todas PT (Os Socios, Fe
  Alves, Forte Como Um Leao). Ele olhou e disse: nao quero em portugues.

  ⚠️ Isso ABRE MAO de um ganho medido: fonte PT pula traducao e dublagem —
  83 min contra 255 no mesmo passo, e zero cota de Gemini. A troca e'
  deliberada e e' editorial: o canal promete "podcasts de fora", e fonte
  brasileira contradiz a promessa. Fica registrado que o custo subiu de
  proposito, para ninguem "consertar" isso de volta sem saber.

  O IDIOMA DA API MENTE.  Na rodada de 30/08 o item #6 era "Book Tuber Hindi"
  — video inteiro em hindi, com `defaultAudioLanguage` dizendo `en`. Passou
  batido. O idioma declarado nao serve como filtro; o que serve e' o ALFABETO
  do titulo. Ver `_escrita_estranha`.

  E FALTAVA FILTRO DE TEMA.  Entre os 38 vieram exercicio para gordura
  visceral e entrevista sobre politica — hype alto, tema fora. Entra uma
  lista de TEMA positiva, igual a' que o radar do @truque.importado ganhou.
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

# ⚠️ SO' EM INGLES desde 31/08/2026. As tres buscas em portugues foram
# removidas por ordem do Bryan — ver o cabecalho. Entraram quatro termos EN
# no lugar, pra repor o volume que elas traziam.
BUSCAS = [
    "david goggins discipline podcast",
    "cameron hanes endurance podcast",
    "jocko willink discipline podcast",
    "andrew huberman exercise protocol",
    "bodybuilding mindset interview pain",
    "hard work mental toughness podcast clip",
    "athlete pain tolerance interview",
    "navy seal discipline routine interview",
    "training through pain podcast",
]

# Termos que denunciam material que o motor NAO consegue usar. Nao e' filtro
# de gosto: e' o que ja' custou run.
VETO = ["shorts", "compilation", "compilado", "satisfying", "music",
        "no talking", "asmr", "workout mix", "gym motivation music"]

# ⚠️ FILTRO DE TEMA. O titulo (ou o canal) tem de conter uma destas. Sem ele,
# a rodada de 30/08 trouxe "exercicio para queimar gordura visceral" e uma
# entrevista sobre politica: hype alto, tema fora do canal.
#
# A lista e' LARGA de proposito. No radar do @truque.importado uma lista curta
# demais derrubou tres videos bons em silencio — recusa silenciosa e' pior que
# ruido, porque ninguem a percebe.
TEMA = [
    "disciplin", "discipline", "mental", "toughness", "tough", "mindset",
    "grit", "willpower", "habit", "routine", "consistency",
    "pain", "suffer", "endurance", "endure", "limit", "quit", "weak",
    "train", "workout", "gym", "lift", "run", "athlete", "bodybuilding",
    "goggins", "jocko", "hanes", "huberman", "navy seal", "marine",
]

# Vizinhos que a busca traz e o canal NAO cobre: dieta/nutricao e politica sao
# outro assunto, ainda que apareçam nos mesmos podcasts.
FORA_DO_TEMA = ["visceral fat", "burning fat", "diet plan", "what to eat",
                "supplement", "politic", "election", "hegseth"]


def _escrita_estranha(texto: str) -> bool:
    """O titulo esta' em alfabeto que nao e' o latino?

    POR QUE ISTO EXISTE, e por que nao basta olhar o idioma

    Na rodada de 30/08 o item #6 era "Book Tuber Hindi": video inteiro em
    hindi, e a API do YouTube declarou `defaultAudioLanguage: en`. O campo
    MENTE, entao filtrar por ele nao pega nada.

    O que nao mente e' o ALFABETO. Devanagari, arabe, cirilico, CJK e hangul
    fora da faixa latina denunciam a fonte independentemente do que o
    metadado diz.

    Piso de 15%: titulo em ingles com um emoji ou um nome proprio acentuado
    nao pode ser recusado por isso.
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
    # ⚠️ O bonus de 1.6x para fonte PT foi REMOVIDO em 31/08/2026: fonte em
    # portugues nao entra mais neste canal. Ver o cabecalho — a troca e'
    # editorial e custa tempo de corte, de proposito.

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
    # Contar POR MOTIVO, nao um total. Um filtro que come demais so' aparece
    # se cada corte tiver o seu numero.
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

    # Salva ANTES de imprimir. Em 30/08 um emoji no titulo derrubou a saida no
    # console do Windows (cp1252) e levou o resultado da rodada junto — a
    # rodada custou cota de YouTube e nao sobrou nada dela.
    with open("radar_atefalhar.json", "w", encoding="utf-8") as f:
        json.dump(aval, f, ensure_ascii=False, indent=1)

    def seguro(t):
        return t.encode("ascii", "replace").decode("ascii")

    print("")
    print(f"{len(aval)} candidato(s)   |   cortados: "
          f"{corte['veto']} veto, {corte['tema']} fora do tema, "
          f"{corte['escrita']} alfabeto nao-latino, "
          f"{corte['portugues']} em portugues")
    print("")
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
    print("")
    print("⚠️ Fonte em portugues NAO entra neste canal (ordem de 31/08).")
    print("   Isso custa tempo de corte de proposito: PT pularia traducao e")
    print("   dublagem, 83 min contra 255. A troca e' editorial.")
    print("⚠️ A busca usa videoDuration=medium, que ja' limita a 20 min. Se")
    print("   'nenhum passa de 45 min', isso e' tautologia, nao seguranca.")


if __name__ == "__main__":
    main()
