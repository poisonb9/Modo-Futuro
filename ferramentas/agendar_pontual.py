# -*- coding: utf-8 -*-
"""Agenda clipes ESPECIFICOS em horarios ESPECIFICOS (hora de Sao Paulo).

Uso (na nuvem, pelo agendar_pontual.yml):
    python -X utf8 ferramentas/agendar_pontual.py \
        --itens "Titulo exato@@2026-09-29 22:50||Outro titulo@@2026-09-30 08:15"

Criado em 29/09/2026 para os Coragem com titulo refeito (PARTE 3,4,5), que
precisam sair NESSA ordem — a fila automatica ordena por fonte e nao garante.
Mesmas travas do agendador: canal conferido (CANAL_ESPERADO), nada repetido
na fila, e o Gemini OUVE o clipe antes (nao bate ou sem veredito -> nao posta).
"""
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import agendar_buffer as ab  # noqa: E402
from ferramentas import conferir_titulos as ct  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--itens", required=True, help='"titulo@@AAAA-MM-DD HH:MM" separados por ||')
    p.add_argument("--simular", action="store_true")
    a = p.parse_args()
    tb, tg = ab._token_buffer(), ab._token_github()
    _, canal, conhecidos = ab.contexto_buffer(tb, fresco=True)
    na_fila = {ab._chave_texto(x.get("text") or ""): x for x in conhecidos}
    manif = ab.manifesto(tg, None)
    for item in [i.strip() for i in a.itens.split("||") if i.strip()]:
        titulo, quando = [x.strip() for x in item.split("@@")]
        clipe = next((v for v in manif.values() if (v.get("titulo") or "").strip() == titulo), None)
        if not clipe:
            print(f"  [!] nao achei no manifesto: {titulo}")
            continue
        if ab._chave_texto(clipe.get("legenda") or titulo) in na_fila:
            x = na_fila[ab._chave_texto(clipe.get("legenda") or titulo)]
            print(f"  = ja' esta' no Buffer ({x.get('status')} {x.get('dueAt')}): {titulo}")
            continue
        j = ct.julgar(ct.audio_do_video(clipe["url"]), titulo)
        if not j or not j.get("bate"):
            print(f"  ⛔ {titulo}: fala NAO bate ({(j or {}).get('fala_de', 'sem veredito')}) — pulado")
            continue
        q = datetime.datetime.strptime(quando, "%Y-%m-%d %H:%M")
        print(f"  ok {titulo} -> {ab.enfileirar(tb, canal, clipe, a.simular, quando_sp=q)}")


if __name__ == "__main__":
    main()
