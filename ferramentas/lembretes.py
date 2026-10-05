"""Lembretes no Telegram do dono: datas de promocao e pendencias abertas.

⭐ 05/10/2026 (dono): "como criar de forma que nunca esquecamos e sejamos
lembrados?" e "nunca oculte nenhum problema que ficar aberto".
- Datas: estado/calendario_promocoes.json, aviso 14, 7, 3 e 1 dia antes (e no dia).
- Pendencias: handoff/PENDENCIAS_ABERTAS.md, toda segunda-feira.

Uso:  python ferramentas/lembretes.py [--forcar-pendencias] [--simular]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import telegram  # noqa: E402

AVISAR_DIAS = {14, 7, 5, 3, 2, 1, 0}


def datas_proximas(hoje: dt.date) -> list[str]:
    cal = json.loads((RAIZ / "estado" / "calendario_promocoes.json").read_text(encoding="utf-8"))
    linhas = []
    for d in cal["datas"]:
        falta = (dt.date.fromisoformat(d["data"]) - hoje).days
        if falta in AVISAR_DIAS:
            quando = "HOJE" if falta == 0 else f"em {falta} dia(s)"
            linhas.append(f"📅 {d['nome']} — {quando} ({d['data'][8:]}/{d['data'][5:7]})"
                          + (f"\n   preparar: {d['preparar']}" if d.get("preparar") else ""))
    return linhas


def pendencias() -> list[str]:
    txt = (RAIZ / "handoff" / "PENDENCIAS_ABERTAS.md").read_text(encoding="utf-8")
    bloco = txt.split("## Abertas", 1)[1].split("## Resolvidas", 1)[0]
    return [re.sub(r"\*\*", "", l.strip()[6:]) for l in bloco.splitlines() if l.strip().startswith("- [ ]")]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--forcar-pendencias", action="store_true")
    p.add_argument("--simular", action="store_true")
    a = p.parse_args()
    hoje = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3)).date()
    partes = []
    d = datas_proximas(hoje)
    if d:
        partes.append("CALENDARIO DE PROMOCOES\n" + "\n".join(d))
    if hoje.weekday() == 0 or a.forcar_pendencias:
        pend = pendencias()
        partes.append(f"PENDENCIAS ABERTAS ({len(pend)})\n" + "\n".join("• " + x for x in pend))
    if not partes:
        print("nada a lembrar hoje")
        return
    msg = "\n\n".join(partes)
    print(msg)
    if not a.simular:
        print("telegram:", telegram.enviar(msg[:telegram.LIMITE_MSG]))


if __name__ == "__main__":
    main()
