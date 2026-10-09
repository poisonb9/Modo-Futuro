# -*- coding: utf-8 -*-
"""Minera o CATALOGO dos canais-fonte campeoes, atras de OUTLIERS.

09/10/2026 (dono: "ampliar radar ... consulte as views do canal ... +acervo,
organiza nosso radar de maneira excepcional").

POR QUE: o radar so' fazia BUSCA POR TERMO e saturou. Em 09/10 13:58:
truque 49 no radar / 0 ineditos, modofuturo 82 / 0, atefalhar 161 / 0. A
busca do YouTube devolve sempre os mesmos ~25 do topo, e cada busca custa
100 unidades de cota.

O acervo (maestros) e' unanime no metodo: abrir os canais do nicho, ordenar
por views e pegar os OUTLIERS -- "procure videos outliers (com visualizacoes
muito acima da media) e reproduza ... dentro do seu nicho"; "adicione canais
do nicho, use 'similar channels' ... ordene por outlier".

COMO:
  1. Sementes = `canais/<canal>/fontes_campeas.json`: os canais do YouTube
     que JA' deram fonte aprovada (abastecer_loop.json -> feitos), mais os
     vizinhos escolhidos a mao a partir dos campeoes de views no TikTok.
  2. Lista de envios de cada canal (playlistItems: 1 unidade por 50 videos,
     contra 100 da busca), ate' `paginas` x 50 videos.
  3. OUTLIER = views / mediana de views do proprio canal. Um video de 2 mi
     num canal que faz 2 mi de media nao e' sinal; 600 mil num canal de 60
     mil e'.
  4. Devolve os itens no MESMO formato do `videos.list` que o radar ja' usa,
     com `_outlier` e `_via` anexados. TEMA/KPOP/NUCLEO/VETO de cada radar
     continuam decidindo -- isto so' traz material novo para eles julgarem.

Cache de 24 h em `estado/mineracao_cache.json` (o radar roda varias vezes ao
dia; o catalogo de um canal nao muda nesse intervalo).
"""
from __future__ import annotations

import json
import statistics
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "estado" / "mineracao_cache.json"
CACHE_H = 24
API = "https://www.googleapis.com/youtube/v3/"
# Short e live de 3 h nao viram corte; o radar ainda aplica a sua faixa.
DUR_MIN_S, DUR_MAX_S = 4 * 60, 60 * 60


def _get(caminho: str, params: dict, chaves: list[str]) -> dict:
    ultimo = None
    for k in chaves:
        url = API + caminho + "?" + urllib.parse.urlencode({**params, "key": k})
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # cota/chave ruim: proxima chave
            ultimo = e
    raise RuntimeError(f"todas as {len(chaves)} chaves falharam: {ultimo}")


def _segundos(iso: str) -> int:
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def _ler_cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def resolver_sementes(arquivo: Path, chaves: list[str]) -> list[dict]:
    """Le fontes_campeas.json; nome sem `id` e' resolvido UMA vez (busca de
    canal, 100 unidades) e o id fica gravado no proprio arquivo."""
    d = json.loads(arquivo.read_text(encoding="utf-8"))
    mudou = False
    for s in d["canais"]:
        if s.get("id"):
            continue
        try:
            r = _get("search", {"part": "snippet", "q": s["nome"],
                                "type": "channel", "maxResults": 1}, chaves)
            it = r.get("items", [])
            # ⚠️ CONFERE O NOME. Em 09/10 "Intel" resolveu para "Intel Edits"
            # (Minecraft) e "The Cartoon Cruise" para um canal nepales: a busca
            # devolve o mais popular PARECIDO, nao o certo.
            achado = it[0]["snippet"]["channelTitle"] if it else ""
            if it and _mesmo_nome(s["nome"], achado):
                s["id"] = it[0]["snippet"]["channelId"]
                s["achado_como"] = achado
                mudou = True
            else:
                s["recusado"] = achado or "nada"
                mudou = True
                print(f"  [!] semente '{s['nome']}' resolveu para '{achado}' — recusada")
        except Exception as e:
            print(f"  [!] semente sem id ({s['nome']}): {str(e)[:60]}")
    if mudou:
        arquivo.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    return [s for s in d["canais"] if s.get("id") and not s.get("desligado")]


def _mesmo_nome(a: str, b: str) -> bool:
    import re
    n = lambda x: re.sub(r"[^a-z0-9]", "", x.casefold())
    return bool(n(a)) and n(a) == n(b)


def _catalogo(cid: str, paginas: int, chaves: list[str]) -> list[dict]:
    up = _get("channels", {"part": "contentDetails", "id": cid}, chaves)
    it = up.get("items", [])
    if not it:
        return []
    pl = it[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    for _ in range(paginas):
        p = {"part": "contentDetails", "playlistId": pl, "maxResults": 50}
        if token:
            p["pageToken"] = token
        r = _get("playlistItems", p, chaves)
        ids += [x["contentDetails"]["videoId"] for x in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    vids = []
    for j in range(0, len(ids), 50):
        r = _get("videos", {"part": "snippet,statistics,contentDetails",
                            "id": ",".join(ids[j:j + 50])}, chaves)
        vids += r.get("items", [])
    return vids


def minerar(canal: str, chaves: list[str], paginas: int = 4,
            outlier_min: float = 1.5) -> list[dict]:
    """Videos dos canais-semente de `canal` com views >= outlier_min x a
    mediana do proprio canal. Formato = item do videos.list + _outlier/_via."""
    arq = RAIZ / "canais" / canal / "fontes_campeas.json"
    if not arq.exists():
        return []
    sementes = resolver_sementes(arq, chaves)
    cache = _ler_cache()
    agora = time.time()
    saida, mudou = [], False
    for s in sementes:
        c = cache.get(s["id"])
        if not c or agora - c.get("t", 0) > CACHE_H * 3600:
            try:
                vids = _catalogo(s["id"], paginas, chaves)
            except Exception as e:
                print(f"  [!] mineracao falhou ({s.get('nome')}): {str(e)[:60]}")
                continue
            c = {"t": agora, "vids": vids}
            cache[s["id"]] = c
            mudou = True
        vids = [v for v in c["vids"]
                if DUR_MIN_S <= _segundos(v["contentDetails"]["duration"]) <= DUR_MAX_S]
        views = [int(v.get("statistics", {}).get("viewCount", 0) or 0) for v in vids]
        if len(views) < 3:
            continue
        med = max(statistics.median(views), 1)
        exigir = [t.casefold() for t in s.get("exigir_no_titulo", [])]
        # Formato que o motor NAO usa (palco = so' musica, sem fala p/ dublar)
        excluir = [t.casefold() for t in s.get("excluir_no_titulo", [])]
        n = 0
        for v, vw in zip(vids, views):
            # Canal que NAO e' so' do nicho (Vogue, PONY): o termo do nicho tem
            # de estar no TITULO -- no radar o nome do canal ("PONY Syndrome")
            # casava sozinho com o filtro KPOP.
            if exigir and not any(t in v["snippet"]["title"].casefold() for t in exigir):
                continue
            if excluir and any(t in v["snippet"]["title"].casefold() for t in excluir):
                continue
            o = vw / med
            if o >= outlier_min:
                v = dict(v, _outlier=round(o, 2), _via=f"canal:{s.get('nome')}")
                saida.append(v)
                n += 1
        print(f"  [canal] {s.get('nome', s['id'])[:34]:<36} {len(vids):>3} videos, "
              f"{n} outlier(s) >= {outlier_min}x (mediana {int(med):,})")
    if mudou:
        CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return saida


# ---------------------------------------------------------------- renovacao
#
# ⛔ A CAUSA RAIZ do radar seco de 09/10: as fontes eram uma lista FIXA de
# buscas escrita a mao, e nada a fazia crescer. O vigia so' AVISAVA
# "radar ESGOTADO" e o canal ficava dias sem estoque esperando alguem
# escrever buscas novas. Agora as sementes crescem sozinhas, por dois
# caminhos, ambos com o canal JA' filtrado pelo tema do radar:
#   1. canal de fonte APROVADA pelo Gemini (abastecer_loop) vira semente;
#   2. canal que aparece com >= 2 itens no radar filtrado vira semente.
# Semente que der 0 outlier aproveitavel em 3 rodadas NAO e' apagada (o
# dono decide); so' fica marcada.

MIN_ITENS_PROMOVER = 3      # 09/10: com 2, entraram WSJ, CNBC, "Ben 10" oficial
MIN_VIEWS_PROMOVER = 200_000
MAX_PROMOVER_RODADA = 3


def _promover(canal: str, novos: dict[str, tuple[str, str]]) -> list[str]:
    arq = RAIZ / "canais" / canal / "fontes_campeas.json"
    if not arq.exists() or not novos:
        return []
    d = json.loads(arq.read_text(encoding="utf-8"))
    ja = {s.get("id") for s in d["canais"]} | {s.get("recusado_id") for s in d["canais"]}
    nunca = {n.casefold() for n in d.get("nao_promover", [])}
    add = []
    for cid, (nome, origem) in novos.items():
        if cid and cid not in ja and nome.casefold() not in nunca:
            d["canais"].append({"nome": nome, "id": cid, "origem": origem})
            add.append(nome)
    if add:
        arq.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return add


def promover_aprovado(canal: str, item: dict) -> list[str]:
    """Chamado pelo abastecer_loop quando o Gemini APROVA uma fonte."""
    from datetime import date
    return _promover(canal, {item.get("canal_id", ""): (
        item.get("canal", "?"), f"auto: fonte aprovada {date.today():%d/%m}")})


def promover_do_radar(canal: str, aval: list[dict]) -> list[str]:
    """Chamado pelo radar com a lista JA' filtrada por tema."""
    from collections import Counter
    from datetime import date
    cont = Counter(i.get("canal_id") for i in aval if i.get("canal_id") and not i.get("via")
                   and i.get("views", 0) >= MIN_VIEWS_PROMOVER)
    nomes = {i.get("canal_id"): i.get("canal", "?") for i in aval}
    novos = {c: (nomes[c], f"auto: {n} itens no radar {date.today():%d/%m}")
             for c, n in cont.most_common(MAX_PROMOVER_RODADA) if n >= MIN_ITENS_PROMOVER}
    add = _promover(canal, novos)
    if add:
        print(f"  [+] {len(add)} canal(is) promovido(s) a semente: {', '.join(add)[:150]}")
    return add


def bonus(item_avaliado: dict, bruto: dict) -> dict:
    """Aplica o peso do outlier na nota do radar (raiz: 4x vale 2x, 9x vale
    3x -- teto 3x para um outlier nao atropelar o resto)."""
    item_avaliado["canal_id"] = bruto.get("snippet", {}).get("channelId", "")
    o = bruto.get("_outlier")
    if o:
        item_avaliado["outlier"] = o
        item_avaliado["via"] = bruto.get("_via", "")
        item_avaliado["nota"] = round(item_avaliado["nota"] * min(o ** 0.5, 3.0), 1)
    return item_avaliado
