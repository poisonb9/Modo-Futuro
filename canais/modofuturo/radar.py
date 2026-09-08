# -*- coding: utf-8 -*-
"""Radar de fontes para o @modofuturo — o lado FISICO e EXTREMO dos chips.

⚠️ ESTE FOI O ULTIMO CANAL A GANHAR RADAR PROPRIO, e a falta dele apareceu
em 08/09/2026 do pior jeito: o `ciclo_semanal` encontrou o @modofuturo com
estoque de fonte ZERO — o unico canal precisando repor — e nao pode fazer
nada, porque nao havia `canais/modofuturo/radar.py`. Ele parou e disse "sem
radar", em vez de baixar as cegas. Este arquivo fecha esse buraco.

Ate' aqui o canal era servido pelo `descobrir.py` com os `TERMOS_HYPE` do
`config.py`. Aqueles termos continuam validos e sao a base das buscas daqui;
o que muda e' que agora existe uma lista TEMA declarada, que e' o que trava o
canal no assunto quando o ciclo semanal enviesa a busca pelos campeoes.

## O QUE VIRALIZA — MEDIDO, NAO ACHISMO

Do README do canal, e reconfirmado pela print do perfil de 08/09/2026:

    2473  As regras extremas para entrar na fabrica mais limpa do mundo
    1009  Como 1 poeira pode destruir 1 milhao de dolares em microchips
     728  A maquina de 400 milhoes de dolares
     585  O dia em que a Intel rejeitou Steve Jobs

O padrao e' o mesmo nas quatro: **corpo, escala e consequencia**. Sala limpa,
grao de poeira, maquina gigante, erro caro. Nao e' o assunto "chip" que
prende — e' o chip como coisa FISICA e extrema.

## E O QUE NAO VIRALIZA, TAMBEM MEDIDO

Analise e geopolitica: mediana 300 (Lex Fridman sobre TSMC) e um ZERO
("Semiconductor is the next OIL"). Por isso "chip war", "tensions" e "market"
ficaram fora dos `TERMOS_HYPE` **de proposito** — e continuam fora aqui.

⚠️ ISSO E' UMA ESCOLHA EDITORIAL COM CUSTO. Geopolitica de chip tem MUITA
fonte disponivel e boa viralidade no YouTube; abrir mao dela reduz o funil.
Fica escrito pra ninguem "consertar" isso de volta achando que foi descuido.

## A ARMADILHA QUE SO' ESTE CANAL TEM: SLIDESHOW

Em 30/08 o run #187 (Asianometry, "TSMC Old Fabs") escolheu 6 momentos com
gancho medio 8,8/10 e DESCARTOU OS 6 pela guarda de imagem travada: blocos de
33s a 82s de camera parada.

⚠️ Narracao sobre diagrama estatico passa por TODO filtro de texto e so' e'
pega no fim, depois do Gemini ja' ter analisado o video inteiro. Caro. O veto
abaixo tenta pegar na fonte o que da' pra pegar pelo titulo e pelo canal —
mas ele NAO resolve o caso geral, porque slideshow nao se anuncia.
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

# ⚠️ AS BUSCAS SAO AS DO `config.TERMOS_HYPE`, que ja' foram calibradas contra
# o desempenho real do canal, mais quatro que vem dos campeoes da print de
# 08/09 (sala limpa, poeira, macacao, erro caro). Nenhuma delas e' de
# analise ou geopolitica — ver o cabecalho.
BUSCAS = [
    "how computer chips are made",
    "inside semiconductor fab",
    "semiconductor cleanroom",
    "EUV lithography machine",
    "ASML machine",
    "silicon wafer manufacturing",
    "chip factory tour",
    "nanometer chip technology",
    "cleanroom protocol semiconductor",
    "chip fab contamination particle",
    "wafer defect cost",
    "inside chip factory documentary",
]

# Material que o motor nao consegue usar, ou que o canal ja' provou nao render.
VETO = [
    # slideshow e diagrama parado — a guarda de imagem descarta no fim, caro
    "explained animation", "animated explainer", "slideshow", "diagram",
    "presentation", "webinar", "lecture", "keynote", "conference talk",
    # analise e geopolitica: mediana 300 e um zero. Fora DE PROPOSITO.
    "chip war", "tensions", "market share", "stock", "investing",
    "geopolitic", "sanctions explained", "trade war", "economy",
    # nao e' fonte
    "shorts", "compilation", "reaction", "podcast highlights", "news update",
]

# ⚠️ FILTRO DE TEMA. E' esta lista que o `ciclo_semanal` usa pra decidir se um
# termo tirado de um titulo campeao pode enviesar a busca. Larga de proposito:
# no radar do @truque uma lista curta demais derrubou tres videos bons em
# silencio, e recusa silenciosa e' pior que ruido.
TEMA = [
    "chip", "chips", "semiconductor", "silicon", "wafer", "fab", "fabs",
    "foundry", "cleanroom", "clean room", "lithography", "euv", "asml",
    "tsmc", "nvidia", "intel", "samsung", "micron", "nanometer", "transistor",
    "microchip", "processor", "gpu", "datacenter", "data center",
    "factory", "fabrica", "manufacturing", "assembly", "machine", "maquina",
    "robot", "automation", "engineering", "precision", "contamination",
    "particle", "poeira", "dust", "yield", "defect", "erro", "extremo",
    "extreme", "regras", "rules", "protocol", "macacao", "suit",
]

# ⚠️ NUCLEO OBRIGATORIO, e ele existe por um FALSO POSITIVO MEDIDO.
#
# A primeira rodada deste radar, em 08/09/2026, devolveu entre os 20
# primeiros:
#
#     "How Pringles Are Made In Factory"      4.381.132 views
#     "How Coca-Cola Is Made In Factory"      3.988.083 views
#     "How Snickers Are Made In Factory"
#     "How KitKat Are Made In a Factory"
#
# Passaram porque `factory` e `manufacturing` estao no TEMA. Sao fabricas —
# nao sao fabricas de CHIP. A lista TEMA larga serve pra o ciclo semanal
# enviesar busca sem derrubar material bom em silencio; ela NAO serve
# sozinha pra decidir o que e' do canal.
#
# A regra: alem de casar com TEMA, o titulo (ou o canal) tem de trazer pelo
# menos um termo daqui.
#
# ⚠️ `dust`, `particle` e `purity` entram no NUCLEO de proposito, mesmo nao
# sendo palavras de semicondutor. Sao o assunto dos DOIS maiores sucessos do
# canal — "a poeira que destroi 1 milhao de dolares" (1009 views) e "as
# regras extremas da sala mais limpa" (2473). Sem eles, a regra derrubaria
# "The Most Expensive Dust in the World", que e' exatamente o material que
# este canal existe pra cortar. MEDIDO nos 45 candidatos da primeira rodada:
# com o nucleo assim, caem os 4 de comida e ficam os 40 restantes.
NUCLEO = [
    "chip", "semiconductor", "silicon", "wafer", "fab", "foundry",
    "lithograph", "euv", "asml", "tsmc", "nvidia", "intel", "micron",
    "samsung", "transistor", "microchip", "processor", "gpu", "cpu",
    "nanometer", "nanoparticle", " nm", "cleanroom", "clean room",
    "dust", "particle", "purity",
]

# Vizinhos que a busca traz e o canal nao cobre.
FORA_DO_TEMA = ["crypto", "bitcoin", "mining rig", "gaming setup",
                "unboxing", "phone review", "laptop review", "buy now"]

# Duracao: o corte precisa de arco autocontido, e o Gemini estoura o limite
# de frames acima de 90 min (cai pra modo so'-audio). `medium` ja' limita a
# 20 min, o que e' folga.
DUR_ALVO = (5.0, 20.0)


def _escrita_estranha(texto: str) -> bool:
    """Alfabeto nao-latino. O idioma declarado pela API MENTE (medido em
    30/08: video em hindi declarado `en`); o alfabeto nao."""
    letras = [c for c in texto if c.isalpha()]
    if not letras:
        return False
    fora = sum(1 for c in letras if ord(c) > 0x2E80 or 0x0370 <= ord(c) <= 0x1CFF)
    return fora / len(letras) > 0.15


def http(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def com_rodizio(monta_url):
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
            "videoDuration": "medium",
            # 30 dias no `config` porque documentario tecnico nao envelhece —
            # o video da ASML que deu 1826 nao tinha nada de recente. Aqui a
            # janela e' ainda mais larga, pelo mesmo motivo.
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
    vph = views / horas
    eng = (likes / views * 100) if views else 0

    # ⚠️ A nota do motor NAO preve views (medido em 24/08: nota 88 deu 1822
    # views, nota 98 deu 584). Esta nota tambem nao — ela ordena candidatos
    # por hype e forma, nao promete desempenho.
    forma = 1.0 if DUR_ALVO[0] <= minutos <= DUR_ALVO[1] else 0.6
    nota = (min(views / 1000, 100) * 0.5 + min(vph, 100) * 0.3
            + min(eng * 10, 100) * 0.2) * forma
    return {
        "id": v["id"], "titulo": v["snippet"]["title"],
        "canal": v["snippet"]["channelTitle"],
        "url": f"https://www.youtube.com/watch?v={v['id']}",
        "views": views, "views_h": round(vph, 1), "eng": round(eng, 2),
        "dur_min": round(minutos, 1), "pt": idioma.lower().startswith("pt"),
        "na_faixa": DUR_ALVO[0] <= minutos <= DUR_ALVO[1],
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
    corte = {"veto": 0, "tema": 0, "escrita": 0, "sem_nucleo": 0}
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
        # ⚠️ E o NUCLEO, que e' o que separa "fabrica" de "fabrica de chip".
        if not any(x in t for x in NUCLEO):
            corte["sem_nucleo"] += 1
            continue
        aval.append(avaliar(v))
    aval.sort(key=lambda x: -x["nota"])

    # Salva ANTES de imprimir: em 30/08 um emoji derrubou a saida no console
    # do Windows e levou junto o resultado de uma rodada ja' paga.
    with open("radar_modofuturo.json", "w", encoding="utf-8") as f:
        json.dump(aval, f, ensure_ascii=False, indent=1)

    def seguro(t):
        return t.encode("ascii", "replace").decode("ascii")

    print("")
    print(f"{len(aval)} candidato(s)   |   cortados: {corte['veto']} veto "
          f"(slideshow/geopolitica), {corte['tema']} fora do tema, "
          f"{corte['sem_nucleo']} sem termo de chip, "
          f"{corte['escrita']} alfabeto nao-latino")
    print("")
    print(f"{'#':<3} {'nota':>5} {'min':>6} {'views':>10} {'v/h':>7} "
          f"{'eng%':>5}  titulo")
    print("-" * 104)
    for i, v in enumerate(aval[:20], 1):
        print(f"{i:<3} {v['nota']:>5} {v['dur_min']:>6} {v['views']:>10} "
              f"{v['views_h']:>7} {v['eng']:>5}  {seguro(v['titulo'])[:46]}")
    print(f"\n{len(aval)} salvos em radar_modofuturo.json")
    print("")
    print("⚠️ SLIDESHOW NAO SE ANUNCIA. O veto pega o que da' pra pegar pelo")
    print("   titulo e pelo canal; camera parada so' e' vista pela guarda de")
    print("   imagem, depois do Gemini ja' ter analisado o video (run #187,")
    print("   6 momentos bons descartados). Antes de baixar, abra e veja se a")
    print("   camera se mexe.")
    print("⚠️ Analise e geopolitica ficam FORA de proposito: mediana 300 e um")
    print("   zero. Isso reduz o funil, e a troca e' editorial.")


if __name__ == "__main__":
    main()
