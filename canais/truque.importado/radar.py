# -*- coding: utf-8 -*-
"""Radar de fontes para o @truque.importado — maquiagem de fora, em portugues.

DIFERENCA PROS OUTROS RADARES

Herda do @atefalhar a ideia de ponderar hype PELO custo de produzir, mas
inverte duas regras dele. As duas inversoes sao o motivo deste arquivo existir
em vez de um `--canal` no radar do Ate Falhar.

  IDIOMA PT NAO GANHA BONUS AQUI.  No Ate Falhar, fonte ja' em portugues vale
  60% a mais: pula traducao e dublagem (medido, 83 min contra 2h01). Aqui ela
  e' AMBIGUA. Se a fonte PT for de uma criadora brasileira, o canal deixa de
  ser "maquiagem de fora, em portugues" e vira agregador de conteudo nacional
  — some a razao de ele existir. Entao PT nao ganha nota; ele e' MARCADO, e a
  decisao de usar e' humana. Ver `PT_PRECISA_DE_OLHO`.

  FONTE MUDA E' VETO DURO, NAO PENALIDADE.  Este e' o nicho mais infestado de
  "no talking" da plataforma: tutorial de maquiagem com trilha e zero fala e'
  o formato dominante. O motor narra o que foi DITO — sem fala, nao ha' o que
  dublar, e o clipe sai mudo. O Cozinha ja' descartou fonte muda pelo mesmo
  motivo, e a guarda de clipe mudo recusaria os cortes no fim do run, depois
  de gastar o runner inteiro.

⚠️ NAO RODOU AINDA. Escrito em 31/08/2026, junto com o canal. As BUSCAS sao
hipotese, nao medicao — os outros radares foram calibrados vendo o que
voltava. Rode uma vez e ajuste os termos antes de confiar na ordem.

Roda com:  python canais/truque.importado/radar.py
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

    A primeira versao do radar do @atefalhar tinha as cinco chaves escritas
    dentro do arquivo. Este repositorio e' PUBLICO: commitar assim queima as
    cinco, e apagar depois nao resolve, porque o valor fica no historico.
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

# Buscas em ingles, coreano e espanhol — os tres mercados de maquiagem cujo
# material NAO chega traduzido ao Brasil. E' exatamente o "de fora" do nome.
#
# Todos os termos puxam para o formato FALADO ("explains", "tutorial",
# "how to", "artist"), porque o veto de fonte muda mata o resto de qualquer
# jeito e nao adianta gastar cota trazendo o que vai ser descartado.
BUSCAS = [
    "makeup artist explains technique",
    "professional makeup tutorial talking",
    "korean makeup tutorial english subtitles",
    "makeup artist reacts common mistake",
    "foundation technique explained artist",
    "eyeliner technique tutorial explained",
    "maquillaje tutorial explicado artista",
    "makeup transformation artist explains",
]

# ⚠️ Termos que denunciam material que o motor NAO consegue usar. Nao e'
# filtro de gosto: cada um destes ja' custou run em algum canal, ou custaria.
#
# Os quatro primeiros sao o formato dominante deste nicho — tutorial mudo com
# trilha. Sem fala nao ha' dublagem, e o clipe sai mudo.
VETO = [
    "no talking", "asmr", "silent", "music only",
    "compilation", "compilado", "satisfying", "tiktok compilation",
    "shorts", "#shorts",
    # sorteio/venda: o corte vira anuncio de terceiro
    "giveaway", "haul", "unboxing", "link in bio", "codigo de desconto",
]

# Fonte em portugues precisa de olho humano: e' dublagem/legendagem de
# material estrangeiro (serve) ou criadora brasileira (nao serve)? O radar nao
# sabe distinguir, entao ele MARCA e nao decide.
PT_PRECISA_DE_OLHO = ("fonte PT: conferir se e' material estrangeiro "
                      "dublado/legendado, e nao criadora brasileira")


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
            "videoDuration": "medium",   # 4 a 20 min: o que CABE no teto de 6h
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

    vph = views / horas
    eng = (likes / views * 100) if views else 0

    # So' DURACAO mexe na nota. Idioma nao — ver o cabecalho.
    if dur <= 20 * 60:
        custo = 1.0
    elif dur <= 45 * 60:
        custo = 0.7
    else:
        custo = 0.3           # so' com --recorte

    nota = (min(views / 1000, 100) * 0.5 + min(vph, 100) * 0.3
            + min(eng * 10, 100) * 0.2) * custo
    return {
        "id": v["id"], "titulo": v["snippet"]["title"],
        "canal": v["snippet"]["channelTitle"],
        "url": f"https://www.youtube.com/watch?v={v['id']}",
        "views": views, "views_h": round(vph, 1), "eng": round(eng, 2),
        "dur_min": round(dur / 60, 1), "idioma": idioma or "?",
        "pt": pt, "aviso": PT_PRECISA_DE_OLHO if pt else "",
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

    aval, vetados = [], 0
    for v in brutos:
        t = (v["snippet"]["title"] + " " + v["snippet"]["channelTitle"]).lower()
        if any(x in t for x in VETO):
            vetados += 1
            continue
        aval.append(avaliar(v))
    aval.sort(key=lambda x: -x["nota"])

    # Salva ANTES de imprimir. Em 30/08 um emoji no titulo derrubou a saida no
    # console do Windows (cp1252) e levou junto o resultado de uma rodada que
    # ja' tinha custado cota de YouTube.
    with open("radar_truque_importado.json", "w", encoding="utf-8") as f:
        json.dump(aval, f, ensure_ascii=False, indent=1)

    def seguro(t):
        return t.encode("ascii", "replace").decode("ascii")

    print(f"\n{len(aval)} candidato(s), {vetados} vetado(s) "
          f"(mudo, compilacao, venda)\n")
    print(f"{'#':<3} {'nota':>5} {'min':>6} {'idio':>5} {'views':>9} "
          f"{'v/h':>7} {'eng%':>5}  titulo")
    print("-" * 108)
    for i, v in enumerate(aval[:20], 1):
        cabe = "OK " if v["dur_min"] <= 45 else "REC"
        olho = " <PT?>" if v["pt"] else ""
        print(f"{i:<3} {v['nota']:>5} {v['dur_min']:>6} "
              f"{v['idioma'][:4]:>5} {v['views']:>9} "
              f"{v['views_h']:>7} {v['eng']:>5}  [{cabe}]{olho} "
              f"{seguro(v['titulo'])[:48]}")
    print(f"\n{len(aval)} salvos em radar_truque_importado.json")
    print("[OK ] cabe no teto de 6h    [REC] so' com --recorte")
    print("<PT?> fonte em portugues — CONFERIR se e' material estrangeiro")
    print("\n⚠️ A fonte tem de FALAR. O veto pega o titulo, nao o audio: se o")
    print("   video for mudo sem dizer no titulo, o clipe sai mudo e a guarda")
    print("   o recusa no fim do run, com o runner ja' gasto.")


if __name__ == "__main__":
    main()
