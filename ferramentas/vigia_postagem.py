# -*- coding: utf-8 -*-
"""Vigia de postagem: avisa no Telegram quando um canal nao vai bater os 4 do dia.

04/10/2026 (dono: "tem como criarmos um alerta toda vez que um canal ficar sem
publicar algum dos 4 videos do dia?" — o @achadinho.make ficou 1 dia parado
com a fila vazia e ninguem viu). SO' LE o Buffer; nada e' criado ou movido.

Para cada canal com token:
  hoje   = enviados hoje (Sao Paulo) + agendados para o resto de hoje
  amanha = agendados nas proximas 24 h
  erro   = posts com status "error"
Alerta se hoje < META, se amanha == 0 (fila vazia) ou se houver erro.

    python -X utf8 ferramentas/vigia_postagem.py            # le e avisa
    python -X utf8 ferramentas/vigia_postagem.py --so-ler   # so' imprime
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import agendar_buffer as ab  # noqa: E402
from engine import canais_registro as cr  # noqa: E402

META = 4
SP = timezone(timedelta(hours=-3))
CONSULTA = """query($i: PostsInput!) { posts(input: $i, first: 60) {
    edges { node { status dueAt sentAt } } } }"""


def _quando(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def medir(canal: str) -> dict | None:
    c = cr.CANAIS[canal]
    tok = (os.environ.get(c.env) or "").strip()
    if not tok:
        return None
    org = ab.consultar(tok, "query { account { organizations { id } } }")[
        "account"]["organizations"][0]["id"]
    chs = ab.consultar(tok, """query($i: ChannelsInput!) { channels(input: $i) {
        id service isDisconnected } }""", {"i": {"organizationId": org}})["channels"]
    tk = [x for x in chs if x["service"] == c.servico]
    if not tk:
        return {"canal": canal, "falha": "canal nao encontrado no Buffer"}
    if tk[0].get("isDisconnected"):
        return {"canal": canal, "falha": "canal DESCONECTADO no Buffer"}
    agora = datetime.now(timezone.utc)
    ini_hoje = datetime.now(SP).replace(hour=0, minute=0, second=0, microsecond=0)
    fim_hoje = ini_hoje + timedelta(days=1)
    n = {"enviados_hoje": 0, "agendados_hoje": 0, "proximas_24h": 0, "erros": 0}
    for st in ("sent", "scheduled", "error"):
        d = ab.consultar(tok, CONSULTA, {"i": {"organizationId": org, "filter": {
            "status": [st], "channelIds": [tk[0]["id"]]}}})
        for e in d["posts"]["edges"]:
            x = e["node"]
            if st == "error":
                n["erros"] += 1
                continue
            q = _quando(x.get("sentAt") if st == "sent" else x.get("dueAt"))
            if not q:
                continue
            if st == "sent" and ini_hoje <= q.astimezone(SP) < fim_hoje:
                n["enviados_hoje"] += 1
            if st == "scheduled":
                if q.astimezone(SP) < fim_hoje:
                    n["agendados_hoje"] += 1
                if agora <= q <= agora + timedelta(hours=24):
                    n["proximas_24h"] += 1
    return {"canal": canal, "arroba": c.arroba, **n}


def problemas(m: dict) -> list[str]:
    if m.get("falha"):
        return [m["falha"]]
    out = []
    hoje = m["enviados_hoje"] + m["agendados_hoje"]
    if hoje < META:
        out.append(f"hoje {hoje}/{META} ({m['enviados_hoje']} saiu, {m['agendados_hoje']} na fila)")
    if m["proximas_24h"] == 0:
        out.append("fila VAZIA nas proximas 24 h")
    if m["erros"]:
        out.append(f"{m['erros']} post(s) com ERRO no Buffer")
    return out


def avisar(texto: str) -> None:
    import requests
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        print("  (sem TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID — aviso so' no log)")
        return
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": chat, "text": texto}, timeout=30)
    print(f"  telegram: {r.status_code}")


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--so-ler", action="store_true")
    o = a.parse_args()
    linhas = []
    for canal in cr.CANAIS:
        try:
            m = medir(canal)
        except Exception as e:  # noqa: BLE001 — um canal nao derruba a vigia
            m = {"canal": canal, "falha": f"nao li o Buffer ({type(e).__name__})"}
        if m is None:
            print(f"{canal:26} (sem token neste ambiente)")
            continue
        p = problemas(m)
        print(f"{canal:26} {'OK' if not p else ' | '.join(p)}  {m}")
        if p:
            linhas.append(f"• {m.get('arroba') or canal}: " + "; ".join(p))
    if linhas and not o.so_ler:
        hora = datetime.now(SP).strftime("%d/%m %H:%M")
        avisar(f"⚠️ Vigia de postagem ({hora})\n" + "\n".join(linhas))
    if not linhas:
        print("todos os canais com a meta do dia")


if __name__ == "__main__":
    main()
