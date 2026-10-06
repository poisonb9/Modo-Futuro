# -*- coding: utf-8 -*-
"""Busca do YouTube COMPARTILHADA pelos radares — com cache, trava de cota e reserva.

06/10/2026: os 7 radares ficaram o dia inteiro com "0 candidatos" porque a cota
diaria de BUSCAS ("Search Queries per day") acabou nas 5 chaves (HTTP 429). O
radar engolia o erro, o estoque ficava em 0, o loop rodava o radar de novo a
cada 30 min e queimava a cota de novo. Sete canais ficaram sem fila e ninguem
foi avisado.

Regras daqui:
1. Mesma busca em menos de 24 h = cache (nao gasta cota).
2. 429/quota numa chave = chave marcada como esgotada ate' o reset (meia-noite
   do Pacifico ~ 07:00 UTC); nenhuma outra busca tenta essa chave antes disso.
3. Todas esgotadas = busca RESERVA pelo yt-dlp (sem cota). Os detalhes
   (videos.list) continuam na API — e' outra cota, custa 1 unidade.
4. Toda falha vira linha ALTA em estado/alertas_busca.log (o abastecer le).
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "estado" / "cache_buscas_yt.json"
COTA = RAIZ / "estado" / "cota_youtube.json"
ALERTAS = RAIZ / "estado" / "alertas_busca.log"
VALIDADE_S = 24 * 3600


def _ler(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _gravar(p: Path, d: dict) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)
    except Exception:  # noqa: BLE001
        pass


def alerta(msg: str) -> None:
    linha = f"{dt.datetime.now():%d/%m %H:%M} {msg}"
    print(f"  [!!] {msg}", flush=True)
    try:
        with ALERTAS.open("a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:  # noqa: BLE001
        pass


def _proximo_reset() -> float:
    agora = dt.datetime.now(dt.timezone.utc)
    r = agora.replace(hour=7, minute=5, second=0, microsecond=0)
    if r <= agora:
        r += dt.timedelta(days=1)
    return r.timestamp()


def _chave_id(k: str) -> str:
    return k[-6:]


def esgotadas() -> set[str]:
    d = _ler(COTA)
    agora = time.time()
    return {k for k, ate in d.items() if ate > agora}


def _marcar_esgotada(k: str) -> None:
    d = {k2: v for k2, v in _ler(COTA).items() if v > time.time()}
    d[_chave_id(k)] = _proximo_reset()
    _gravar(COTA, d)


def _reserva_ytdlp(termo: str, n: int) -> dict:
    """Busca sem cota (yt-dlp, flat). Devolve no formato da search API."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--flat-playlist", "-J",
             "--no-warnings", f"ytsearch{max(n * 2, 10)}:{termo}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120)
        d = json.loads(r.stdout or "{}")
    except Exception as e:  # noqa: BLE001
        alerta(f"busca reserva (yt-dlp) falhou para '{termo}': {e}")
        return {"items": []}
    itens = []
    for e in d.get("entries") or []:
        vid = e.get("id")
        if vid and len(vid) == 11:
            itens.append({"id": {"kind": "youtube#video", "videoId": vid},
                          "snippet": {"title": e.get("title") or ""}})
    return {"items": itens[: max(n * 2, 10)], "_reserva": True}


def buscar(monta_url, chaves: list[str]) -> dict:
    """Substitui o com_rodizio dos radares para URLs de /search."""
    url0 = monta_url("X")
    q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url0).query))
    q.pop("key", None)
    chave_cache = json.dumps(q, sort_keys=True)
    cache = _ler(CACHE)
    ent = cache.get(chave_cache)
    if ent and time.time() - ent.get("t", 0) < VALIDADE_S:
        return ent["d"]

    fora = esgotadas()
    ultimo = None
    for k in chaves:
        if _chave_id(k) in fora:
            continue
        try:
            with urllib.request.urlopen(monta_url(k), timeout=30) as r:
                d = json.load(r)
            break
        except urllib.error.HTTPError as e:
            corpo = e.read()[:400].decode("utf-8", "replace")
            ultimo = f"{e.code} {corpo[:120]}"
            if e.code in (403, 429) and "uota" in corpo:
                _marcar_esgotada(k)
            continue
        except Exception as e:  # noqa: BLE001
            ultimo = str(e)
            continue
    else:
        alerta(f"cota de BUSCA do YouTube esgotada nas {len(chaves)} chaves "
               f"({ultimo or 'todas marcadas'}) — usando busca reserva yt-dlp")
        d = _reserva_ytdlp(q.get("q", ""), int(q.get("maxResults") or 8))
        if not d["items"]:
            raise RuntimeError("busca da API e reserva falharam")
    cache = {k2: v for k2, v in _ler(CACHE).items()
             if time.time() - v.get("t", 0) < VALIDADE_S}
    cache[chave_cache] = {"t": time.time(), "d": d}
    _gravar(CACHE, cache)
    return d
