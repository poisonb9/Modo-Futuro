# -*- coding: utf-8 -*-
"""TESTE: trecho de demonstracao do produto tirado do YouTube (so' na nuvem).

    python -X utf8 ferramentas/demo_youtube.py --id <produto> --saida demo.mp4

⭐ 29/09/2026 — DECISAO DO DONO, com o risco explicado (direito autoral e
originalidade, playbook §6): "canais oficiais e canais estrangeiros, vamos
evitar canais brasileiros; se tomarmos flag a gente para. Eu quero testar."

Regras que este arquivo garante:
  1. So' entra aqui produto SEM video oficial do vendedor (esse vem primeiro).
  2. Toda conversa com o YouTube passa pela SENTINELA (uma porta, intervalo,
     freio no bot-check) — `python -m engine.sentinela_youtube -- yt-dlp ...`.
  3. Ordem: canal OFICIAL (nome da marca no canal) > canal ESTRANGEIRO.
     Canal/titulo em portugues fica de fora.
  4. Baixa SO' um trecho curto (TRECHO_S), pulando a introducao — nunca o
     video inteiro.
  5. ⛔ TRAVA: qualquer sinal ruim (bot-check, 429, copyright) grava
     `estado/demo_youtube_parado.json` e NADA mais roda ate' o dono soltar.
     O mesmo arquivo e' o botao de parar se o TikTok der flag.
  6. Cada trecho usado fica anotado em `estado/demo_youtube_fontes.jsonl`
     (de onde veio) — pra responder rapido se alguem reclamar.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
TRAVA = RAIZ / "estado" / "demo_youtube_parado.json"
FONTES = RAIZ / "estado" / "demo_youtube_fontes.jsonl"
ULTIMO = RAIZ / "estado" / "youtube_ultima_chamada.json"
# ⭐ 29/09/2026 (dono: "o YouTube e' extremamente sensivel... bom intervalo entre
# downloads"). Cada maquina do GitHub nasce sem memoria, entao a sentinela
# sozinha nao espaca UMA RODADA da outra. A hora da ultima chamada mora no
# repositorio e nenhuma rodada fala com o YouTube antes deste intervalo.
INTERVALO_ENTRE_RODADAS_MIN = 30
TRECHO_S = 8
DUR_MIN, DUR_MAX = 20, 900

# titulo/canal com cara de portugues -> fora (decisao do dono: sem canal BR)
PT = re.compile(r"[ãõç]|\b(de|do|da|que|com|para|muito|vale a pena|comprei|testei|"
                r"resenha|análise|analise|unboxing brasil|mercado livre|shopee)\b", re.I)
RUIM = re.compile(r"sign in to confirm|not a bot|http error 429|too many requests|"
                  r"copyright|blocked it on copyright|video unavailable", re.I)


def parado() -> str:
    if TRAVA.exists():
        return json.loads(TRAVA.read_text(encoding="utf-8")).get("motivo", "parado")
    return ""


def travar(motivo: str) -> None:
    TRAVA.write_text(json.dumps({"motivo": motivo[:300],
                                 "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"⛔ TRAVADO: {motivo[:200]}")


def cedo_demais() -> float:
    """Minutos que ainda faltam para poder falar com o YouTube (0 = pode)."""
    if not ULTIMO.exists():
        return 0.0
    try:
        t = datetime.fromisoformat(json.loads(ULTIMO.read_text(encoding="utf-8"))["quando"])
    except (ValueError, KeyError):
        return 0.0
    passou = (datetime.now(timezone.utc) - t).total_seconds() / 60
    return max(0.0, INTERVALO_ENTRE_RODADAS_MIN - passou)


def _yt(args: list[str]) -> str:
    ULTIMO.write_text(json.dumps({"quando": datetime.now(timezone.utc).isoformat(timespec="seconds")}),
                      encoding="utf-8")
    r = subprocess.run([sys.executable, "-X", "utf8", "-m", "engine.sentinela_youtube", "--",
                        "yt-dlp", *args], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=3600)
    saida = (r.stdout or "") + (r.stderr or "")
    if RUIM.search(saida):
        travar(RUIM.search(saida).group(0))
        raise SystemExit(2)
    return r.stdout or ""


def busca_em_ingles(nome_loja: str) -> str:
    from engine import modelo_texto
    q = modelo_texto.perguntar(
        "Write ONLY an English YouTube search query (3 to 6 words) to find a video "
        "demonstrating this product in use. Keep a real brand name if there is one. "
        f"Product: {nome_loja}") or ""
    q = q.strip().strip('"').splitlines()[0] if q.strip() else ""
    return q or nome_loja


def _marca(nome_loja: str) -> str:
    """Primeira palavra com cara de marca (Maiuscula, nao generica)."""
    for w in re.findall(r"[A-Z][A-Za-z0-9]{2,}", nome_loja):
        if w.lower() not in {"para", "com", "kit", "usb", "led", "rgb", "novo", "nova"}:
            return w.lower()
    return ""


def escolher(itens: list[dict], marca: str) -> dict | None:
    bons = []
    for v in itens:
        dur = v.get("duration") or 0
        tit, canal = v.get("title") or "", v.get("channel") or v.get("uploader") or ""
        if not (DUR_MIN <= dur <= DUR_MAX):
            continue
        if PT.search(tit) or PT.search(canal):
            continue
        oficial = bool(marca) and marca in canal.lower().replace(" ", "")
        bons.append((0 if oficial else 1, v))
    bons.sort(key=lambda x: x[0])
    return bons[0][1] if bons else None


def achar(pid: str, saida: Path) -> dict | None:
    motivo = parado()
    if motivo:
        print(f"demo do YouTube PARADA ({motivo}) — nada a fazer")
        return None
    falta = cedo_demais()
    if falta:
        print(f"ultima chamada ao YouTube foi ha' pouco — faltam {falta:.0f} min; nao chamo")
        return None
    nomes = {}
    for l in (RAIZ / "estado" / "produtos_publicados.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            x = json.loads(l)
        except ValueError:
            continue
        if str(x.get("id")) == pid:
            nomes[pid] = x.get("nome") or ""
    nome_loja = nomes.get(pid) or json.load(open(RAIZ / "estado" / "nomes_curtos.json",
                                                   encoding="utf-8")).get(pid, "")
    q = busca_em_ingles(nome_loja)
    print(f"busca: {q!r}")
    linhas = _yt([f"ytsearch8:{q}", "--dump-json", "--flat-playlist", "--no-warnings"])
    itens = []
    for l in linhas.splitlines():
        try:
            itens.append(json.loads(l))
        except ValueError:
            pass
    v = escolher(itens, _marca(nome_loja))
    if not v:
        print("nenhum video estrangeiro/oficial serviu")
        return None
    dur = float(v["duration"])
    ini = max(3.0, dur * 0.2)              # pula a introducao
    ini = min(ini, max(0.0, dur - TRECHO_S - 1))
    url = f"https://www.youtube.com/watch?v={v['id']}"
    print(f"escolhido: {v.get('title')!r} — canal {v.get('channel')!r} — trecho {ini:.0f}s")
    _yt(["-f", "bv*[height<=1080][ext=mp4]/bv*[height<=1080]/b", "-q",
         "--download-sections", f"*{ini:.0f}-{ini + TRECHO_S:.0f}", "--force-keyframes-at-cuts",
         "-o", str(saida), url])
    if not saida.exists():
        return None
    reg = {"id": pid, "url": url, "canal": v.get("channel"), "titulo": v.get("title"),
           "ini": round(ini), "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with open(FONTES, "a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    return reg


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--saida", type=Path, required=True)
    a = ap.parse_args()
    print(achar(a.id, a.saida))
