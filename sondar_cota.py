# -*- coding: utf-8 -*-
"""Fotografa a saude das chaves do Gemini, e GUARDA a foto.

    python sondar_cota.py            # sonda uma amostra e grava
    python sondar_cota.py --todas    # sonda TODAS (use com parcimonia)
    python sondar_cota.py --historico  # so' mostra o que ja' foi medido

⚠️ POR QUE ISTO EXISTE, medido em 02/09/2026.

Um corte de 142 minutos morreu com "todas as chaves esgotadas" e eu conclui
que a cota do dia tinha acabado. Estava errado: a medicao seguinte mostrou
4 chaves em 200 e **zero 429**. O que havia era 503 e timeout — sobrecarga do
GOOGLE, nao limite nosso.

A diferenca decide o que fazer:

    429  limite NOSSO      -> so' o reset diario resolve (07:00 UTC)
    503  sobrecarga DELES  -> pode normalizar em minutos; esperar o reset
                             seria jogar meio dia fora
    Timeout                -> nao respondeu. NAO e' prova de nada.
    403  chave invalida    -> nao melhora com o tempo; regenerar a chave

Uma foto isolada nao distingue "ruim agora" de "ruim o dia todo". Por isso
este script GRAVA cada medicao em `estado/cota_gemini.jsonl`: a serie mostra
se esta' melhorando ou piorando, que e' o que decide disparar ou esperar.

⚠️ A ARMADILHA QUE ESTE SCRIPT EVITA. Bater em todas as chaves duas vezes
dentro do mesmo minuto estoura o limite POR MINUTO, e o 429 resultante e' lido
como cota diaria esgotada — a sonda causa o que mede. Medido em 01/09: uma
consulta direta as 14 chaves deu 10 em 200, e a sonda segundos depois deu
"1 ok, 8 sem cota", nas MESMAS chaves.

Defesas: amostra pequena, RODIZIO (cada passada usa chaves diferentes, entao
nenhuma e' martelada), pouca concorrencia, e recusa de sondar de novo antes
de INTERVALO_MIN_S.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / ".env", override=True)

HISTORICO = RAIZ / "estado" / "cota_gemini.jsonl"
AMOSTRA = 5
INTERVALO_MIN_S = 240      # 4 min entre sondagens, pra nao me atropelar
TIMEOUT_S = 30
MODELO = "gemini-3.6-flash"


def chaves() -> list[tuple[str, str]]:
    """Todas as chaves do rodizio — o mesmo intervalo que o motor le'."""
    nomes = ["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{i}" for i in range(2, 41)]
    return [(n, os.environ[n].strip())
            for n in nomes if (os.environ.get(n) or "").strip()]


def _classificar(par: tuple[str, str]) -> tuple[str, str]:
    nome, chave = par
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODELO}:generateContent?key={chave}",
        data=json.dumps({"contents": [{"parts": [{"text": "oi"}]}]}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return nome, "viva" if r.status == 200 else f"http{r.status}"
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return nome, "limite_nosso"          # 429 — so' o reset resolve
        if e.code == 503:
            return nome, "sobrecarga_deles"      # 503 — costuma passar
        if e.code == 403:
            return nome, "invalida"              # chave morta; regenerar
        return nome, f"http{e.code}"
    except Exception:
        # ⚠️ Silencio NAO e' "sem cota". Categoria propria, de proposito.
        return nome, "muda"


def _rodizio(todas: list, n: int) -> list:
    """Quais chaves sondar desta vez.

    ⚠️ RODIZIO, nao "as n primeiras". Chave fixa seria sempre a mesma a ser
    gasta, e a amostra deixaria de representar o conjunto. A janela anda com
    o numero de medicoes ja' feitas, entao ao longo do dia todas entram.
    """
    if len(todas) <= n:
        return todas
    ja = sum(1 for _ in HISTORICO.open(encoding="utf-8")) if HISTORICO.exists() else 0
    ini = (ja * n) % len(todas)
    dobra = todas + todas
    return dobra[ini:ini + n]


def ultima() -> dict | None:
    if not HISTORICO.exists():
        return None
    linhas = [l for l in HISTORICO.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(linhas[-1]) if linhas else None


def sondar(todas_as_chaves: bool = False) -> dict:
    ks = chaves()
    if not ks:
        raise SystemExit("nenhuma chave GEMINI_* no ambiente")
    alvo = ks if todas_as_chaves else _rodizio(ks, AMOSTRA)

    with ThreadPoolExecutor(max_workers=min(5, len(alvo))) as pool:
        res = list(pool.map(_classificar, alvo))

    placar = collections.Counter(v for _, v in res)
    foto = {
        "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sondadas": len(alvo),
        "no_rodizio": len(ks),
        "placar": dict(placar),
        "vivas": placar.get("viva", 0),
        "detalhe": {n: v for n, v in res},
    }
    HISTORICO.parent.mkdir(parents=True, exist_ok=True)
    with HISTORICO.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(foto, ensure_ascii=False) + "\n")
    return foto


def veredito(foto: dict) -> str:
    """O que a foto MANDA fazer — nao so' o que ela viu."""
    p = foto["placar"]
    # ⚠️ CHAVE VIVA MANDA MAIS QUE CHAVE EM 429, e a primeira versao disto
    # fazia o contrario: bastava UM 429 pra ela mandar esperar ate' o reset,
    # mesmo com tres chaves respondendo 200. Um 429 e' uma chave cansada, nao
    # o rodizio inteiro — e o 429 desta medicao fui EU que causei, sondando
    # duas vezes seguidas com --forcar.
    #
    # "Esperar ate' amanha" e' o conselho mais caro que este script pode dar.
    # Ele so' vale quando nao ha' NENHUMA viva e o 429 domina.
    if foto["vivas"] >= 3:
        return "DA' PRA CORTAR — varias chaves respondendo"
    if not foto["vivas"] and p.get("limite_nosso"):
        return ("LIMITE NOSSO (429) e nenhuma viva — so' o reset diario "
                "resolve, 07:00 UTC / 04:00 Sao Paulo")
    if foto["vivas"] >= 1:
        return ("DA' PRA TENTAR UM — mas 1 resposta boa nao sustenta um corte "
                "de ~2h; foi assim que o run de 142 min morreu")
    if p.get("sobrecarga_deles") or p.get("muda"):
        return ("GOOGLE ENGASGADO (503/mudo), NAO e' cota nossa — "
                "tentar de novo em 20-30 min, nao esperar o reset")
    return "sem leitura util"


def mostrar_historico(n: int = 12) -> None:
    if not HISTORICO.exists():
        print("ainda nao ha' historico"); return
    linhas = [json.loads(l) for l in HISTORICO.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"ultimas {min(n, len(linhas))} medicoes (de {len(linhas)}):\n")
    for f in linhas[-n:]:
        marcas = " ".join(f"{v}x{k}" for k, v in sorted(f["placar"].items()))
        print(f"  {f['quando'][11:16]} UTC  {f['vivas']}/{f['sondadas']} vivas   {marcas}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--todas", action="store_true",
                    help="sonda todas as chaves (use com parcimonia)")
    ap.add_argument("--historico", action="store_true", help="so' mostra o historico")
    ap.add_argument("--forcar", action="store_true",
                    help="ignora o intervalo minimo entre sondagens")
    a = ap.parse_args()

    if a.historico:
        mostrar_historico(); return

    u = ultima()
    if u and not a.forcar:
        idade = time.time() - datetime.fromisoformat(u["quando"]).timestamp()
        if idade < INTERVALO_MIN_S:
            print(f"ultima sondagem ha' {idade:.0f}s — esperando "
                  f"{INTERVALO_MIN_S}s pra nao estourar o limite por minuto.")
            print(f"  (a de {u['quando'][11:16]} UTC viu {u['vivas']}/{u['sondadas']} vivas)")
            print(f"  {veredito(u)}")
            return

    f = sondar(todas_as_chaves=a.todas)
    marcas = " · ".join(f"{v} {k}" for k, v in sorted(f["placar"].items()))
    print(f"[{f['quando'][11:16]} UTC] {f['vivas']}/{f['sondadas']} vivas "
          f"(de {f['no_rodizio']} no rodizio)   {marcas}")
    print(f"  {veredito(f)}")
    mortas = [n for n, v in f["detalhe"].items() if v == "invalida"]
    if mortas:
        print(f"  ⚠️ chave(s) INVALIDA(s), nao melhoram com o tempo: {', '.join(mortas)}")


if __name__ == "__main__":
    main()
