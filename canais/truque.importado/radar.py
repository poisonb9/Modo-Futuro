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

CALIBRADO EM 31/08/2026, numa rodada de verdade. O que ela mostrou:

  43 resultados, 1 vetado. O veto de fonte muda quase nao mordeu — porque as
  buscas ja' puxam pro formato falado. Ele fica como rede de seguranca.

  "foundation technique explained artist" trouxe DESENHO. As tres palavras
  colidem com arte: "foundation", "technique" e "artist" descrevem retrato a
  lapis tao bem quanto base de maquiagem. Vieram "Foundations for Better
  Portrait Drawing" e "the right way to start learning how to draw". O termo
  foi trocado, e entrou um filtro de TEMA para o que escapar.

  "maquillaje tutorial explicado artista" devolveu ZERO. Foi trocado.

  13 dos 42 eram em hindi (31%) — noiva indiana, HD makeup. E' "de fora", mas
  e' outra estetica e outro publico. O radar MARCA e nao decide, igual ao PT.

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
# ⭐ 03/10/2026 (dono): o canal virou @achadinho.make = TECNICA de maquiagem
# de IDOL de K-pop. As buscas genericas antigas ("makeup artist explains...")
# trouxeram "FULL GLAM", "Bambi eyes" e "Paloma Mami" — 19 clipes sem idol
# foram ao manifesto e 10 ao Buffer, e o dono apagou. Toda busca agora nomeia
# o universo K-pop, e o filtro KPOP abaixo e' VETO DURO.
BUSCAS = [
    "RISABAE idol makeup",
    "이사배 아이돌 메이크업",
    "kpop idol makeup tutorial eng sub",
    "idol makeup artist reveals secret eng sub",
    "kpop idol makeup routine eng sub",
    "kpop stage makeup artist eng sub",
    "idol get ready with me makeup eng sub",
    "PONY syndrome idol makeup",
    # ⭐ 05/10/2026 (dono: radar do Make seco — 13 no radar, 1 inedito)
    "aespa makeup artist eng sub",
    "IVE makeup artist reveals eng sub",
    "newjeans makeup artist eng sub",
    "blackpink makeup artist secrets eng sub",
    "twice makeup artist eng sub",
    "le sserafim makeup eng sub",
    "babymonster makeup eng sub",
    "nmixx makeup eng sub",
    "stray kids makeup artist eng sub",
    "idol makeup transformation eng sub",
    "makeup artist reacts to idol makeup",
    "kpop idol bare face makeup routine",
    "아이돌 메이크업 비법",
    "아이돌 메이크업 아티스트",
    "이사배 메이크업 아이돌",
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

# ⚠️ FILTRO DE TEMA, medido. O titulo (ou o canal) tem de conter uma destas.
# Sem ele passaram 5 de 42: dois videos de DESENHO, um de cabelo, um de unha e
# uma entrevista de celebridade. Nenhum dos 5 era maquiagem — zero falso
# positivo na remocao, conferido um a um.
#
# "make up" separado, "mua" e "eyeshadow" estao aqui porque a primeira versao
# da lista derrubou tres videos de maquiagem de verdade por falta deles. Uma
# lista curta demais e' pior que nenhuma: ela recusa em silencio.
TEMA = [
    "makeup", "make up", "make-up", "mua", "maquill", "maquiagem",
    "beauty", "k-beauty", "cosmetic", "glam", "grwm", "bridal",
    "foundation", "concealer", "primer", "highlighter", "contour",
    "eyeliner", "eyeshadow", "lipstick", "blush", "skin",
]

# ⭐ 03/10/2026: TEM de ser do universo K-pop. Fonte com maquiagem mas sem
# idol/grupo/programa coreano NAO entra, por melhor que seja a tecnica.
KPOP = [
    "idol", "kpop", "k-pop", "아이돌", "risabae", "이사배", "pony", "포니",
    "stray kids", "skz", "felix", "hyunjin", "skz han", "nmixx", "jiwoo", "nmixx lily",
    "illit", "wonhee", "twice", "tzuyu", "nayeon", "nct", "babymonster",
    "ahyeon", "ive", "wonyoung", "yujin", "aespa", "karina", "winter",
    "le sserafim", "chaewon", "kazuha", "newjeans", "hanni", "blackpink",
    "jennie", "blackpink lisa", "rosé", "jisoo", "itzy", "yeji", "kiss of life",
    "seventeen", "treasure", "enhypen", "txt", "bts", "allday project",
    "noze", "스우파",
    # ⭐ 09/10/2026: revistas coreanas (W/ELLE/Dazed Korea) escrevem a idol em HANGUL
    "에스파", "아이브", "뉴진스", "르세라핌", "스트레이키즈", "스키즈", "엔믹스", "아일릿", "베이비몬스터", "블랙핑크", "트와이스", "있지", "세븐틴", "에이티즈", "엔하이픈", "투바투", "방탄", "레드벨벳", "아이들", "키스오브라이프", "미야오", "라이즈", "제로베이스원", "케플러", "원영", "카리나", "윈터", "해원", "지우", "원희", "아현", "하니",
]

# ⭐ Capas de revista teen (03/10/2026, 155 capas lidas pelo Gemini): nome do
# idolo 94%, segredo/bastidor 22-24%, numero 74%. Fonte cujo titulo ja' traz
# segredo/rotina/bastidor da idol rende titulo de capa melhor. BONUS, nao veto.
GANCHO_CAPA = ["secret", "reveal", "routine", "behind", "tip", "trick",
               "비법", "꿀팁", "루틴", "비밀"]

# Vizinhos que a busca traz e o canal NAO cobre. Cabelo e unha sao beleza, mas
# nao sao maquiagem; desenho e' colisao de vocabulario, nao vizinhanca.
FORA_DO_TEMA = ["hair colour", "hair color", "nail ", "nails",
                "how to draw", "drawing", "portrait draw"]

# Idiomas cujo material e' "de fora" mas de OUTRA estetica e outro publico.
# Na rodada de calibragem foram 13 de 42 (31%) — se nao for marcado, eles
# dominam o topo sozinhos. Marcar, nao vetar: e' decisao editorial do Bryan.
OUTRO_MERCADO = {"hi": "indiano", "ur": "indiano/paquistanes", "bn": "bengali"}

# Fonte em portugues precisa de olho humano: e' dublagem/legendagem de
# material estrangeiro (serve) ou criadora brasileira (nao serve)? O radar nao
# sabe distinguir, entao ele MARCA e nao decide.
PT_PRECISA_DE_OLHO = ("fonte PT: conferir se e' material estrangeiro "
                      "dublado/legendado, e nao criadora brasileira")


def tem_termo(texto: str, termos) -> bool:
    """Casa por PALAVRA inteira nos termos latinos.

    ⚠️ Substring simples nao serve: "ive" casa "live"/"five", "lisa" casa
    "Elisa", "rose" casa "rose gold". Termo em hangul nao tem fronteira de
    palavra confiavel, entao casa por substring.
    """
    t = texto.lower()
    for x in termos:
        if x.isascii():
            if re.search(r"(?<![a-z0-9])" + re.escape(x) + r"(?![a-z0-9])", t):
                return True
        elif x in t:
            return True
    return False


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


def buscar(termo, n=25):   # 05/10/2026: era 8 — radar seco (13 no radar)
    def url(k):
        q = urllib.parse.urlencode({
            "part": "snippet", "q": termo, "type": "video",
            "maxResults": n, "order": "viewCount",
            "videoDuration": "medium",   # 4 a 20 min: o que CABE no teto de 6h
            "publishedAfter": "2023-01-01T00:00:00Z",   # 05/10/2026: era 2025 — tecnica de idol nao envelhece em 1 ano
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

    # ⭐ 03/10/2026: fonte em coreano FALADO sem legenda gerou transcricao
    # inventada — 3 de 7 clipes do Hyunjin (Risabae) e 20 de 39 do Camarim
    # cairam na quarentena "narracao incoerente". Legenda EN/eng sub vale
    # mais; coreano sem legenda vale menos (nao veta: Risabae [Eng] e' ouro).
    texto = (v["snippet"]["title"] + " " + v["snippet"]["channelTitle"]).lower()
    com_legenda = (v["contentDetails"].get("caption") == "true"
                   or tem_termo(texto, ["eng sub", "eng", "english sub", "engsub"]))
    if com_legenda:
        legenda = 1.3
    elif idioma.lower().startswith("ko"):
        legenda = 0.5
    else:
        legenda = 1.0
    capa = 1.15 if tem_termo(texto, GANCHO_CAPA) else 1.0

    nota = (min(views / 1000, 100) * 0.5 + min(vph, 100) * 0.3
            + min(eng * 10, 100) * 0.2) * custo * legenda * capa
    return {
        "id": v["id"], "titulo": v["snippet"]["title"],
        "canal": v["snippet"]["channelTitle"],
        "url": f"https://www.youtube.com/watch?v={v['id']}",
        "views": views, "views_h": round(vph, 1), "eng": round(eng, 2),
        "dur_min": round(dur / 60, 1), "idioma": idioma or "?",
        "pt": pt, "aviso": PT_PRECISA_DE_OLHO if pt else "",
        "legenda": com_legenda,
        "nota": round(nota, 1),
    }


def _buscas_extras():
    """⭐ 08/10/2026: buscas tiradas dos posts campeoes do canal
    (engine/buscas_do_sucesso.py, renovadas pelo ciclo_semanal). Soma a BUSCAS;
    os filtros de TEMA/NUCLEO/VETO deste radar continuam valendo."""
    import json as _json
    import os as _os
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "buscas_extras.json")
    try:
        extras = _json.load(open(p, encoding="utf-8")).get("buscas", [])
    except Exception:
        return []
    return [b for b in extras if b not in BUSCAS]


def main():
    vistos, brutos = set(), []
    for termo in BUSCAS + _buscas_extras():
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

    # ⭐ 09/10/2026: catalogo dos canais-fonte campeoes, atras de OUTLIERS
    # (engine/minerar_canais.py). A busca por termo saturou (0 ineditos).
    import importlib.util as _iu
    _p = __import__("pathlib").Path(__file__).resolve().parents[2] / "engine" / "minerar_canais.py"
    _sp = _iu.spec_from_file_location("minerar_canais", _p)
    _mc = _iu.module_from_spec(_sp); _sp.loader.exec_module(_mc)
    try:
        for v in _mc.minerar('truque.importado', CHAVES):
            if v["id"] not in vistos:
                vistos.add(v["id"]); brutos.append(v)
    except Exception as e:
        print(f"  [!] mineracao de canais falhou: {str(e)[:80]}")

    aval, vetados = [], 0
    fora_tema = sem_kpop = 0
    for v in brutos:
        t = (v["snippet"]["title"] + " " + v["snippet"]["channelTitle"]).lower()
        if any(x in t for x in VETO):
            vetados += 1
            continue
        if not any(x in t for x in TEMA) or any(x in t for x in FORA_DO_TEMA):
            fora_tema += 1
            continue
        # ⛔ VETO DURO (03/10/2026): sem idol/grupo/programa K-pop nao entra.
        if not tem_termo(t, KPOP):
            sem_kpop += 1
            continue
        aval.append(_mc.bonus(avaliar(v), v))
    aval.sort(key=lambda x: -x["nota"])
    try:
        _mc.promover_do_radar('truque.importado', aval)   # ⭐ 09/10: sementes crescem sozinhas
    except Exception as e:
        print(f"  [!] promocao de sementes falhou: {str(e)[:80]}")

    # Salva ANTES de imprimir. Em 30/08 um emoji no titulo derrubou a saida no
    # console do Windows (cp1252) e levou junto o resultado de uma rodada que
    # ja' tinha custado cota de YouTube.
    with open("radar_truque_importado.json", "w", encoding="utf-8") as f:
        json.dump(aval, f, ensure_ascii=False, indent=1)

    def seguro(t):
        return t.encode("ascii", "replace").decode("ascii")

    print(f"\n{len(aval)} candidato(s), {vetados} vetado(s) "
          f"(mudo, compilacao, venda), {sem_kpop} sem K-pop\n")
    print(f"{'#':<3} {'nota':>5} {'min':>6} {'idio':>5} {'views':>9} "
          f"{'v/h':>7} {'eng%':>5}  titulo")
    print("-" * 108)
    for i, v in enumerate(aval[:20], 1):
        cabe = "OK " if v["dur_min"] <= 45 else "REC"
        olho = " <PT?>" if v["pt"] else ""
        merc = OUTRO_MERCADO.get(v["idioma"][:2].lower())
        if merc:
            olho += f" <{merc}>"
        print(f"{i:<3} {v['nota']:>5} {v['dur_min']:>6} "
              f"{v['idioma'][:4]:>5} {v['views']:>9} "
              f"{v['views_h']:>7} {v['eng']:>5}  [{cabe}]{olho} "
              f"{seguro(v['titulo'])[:48]}")
    print(f"\n{len(aval)} salvos em radar_truque_importado.json")
    print("[OK ] cabe no teto de 6h    [REC] so' com --recorte")
    print("<PT?> fonte em portugues — CONFERIR se e' material estrangeiro")
    print("<indiano> etc — 'de fora', mas outra estetica e outro publico;")
    print("             foram 31% da rodada de calibragem. Decisao sua.")
    print("\n⚠️ A fonte tem de FALAR. O veto pega o titulo, nao o audio: se o")
    print("   video for mudo sem dizer no titulo, o clipe sai mudo e a guarda")
    print("   o recusa no fim do run, com o runner ja' gasto.")


if __name__ == "__main__":
    main()
