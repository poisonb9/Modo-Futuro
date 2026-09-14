# -*- coding: utf-8 -*-
"""Um lembrete SO', na hora marcada, pelo Telegram — e depois se apaga.

    python lembrete_unico.py --texto "..." --tarefa NomeDaTarefa

## ⚠️ POR QUE ISTO EXISTE, E NAO "EU LEMBRO"

Eu NAO rodo entre os turnos do Bryan. "Te lembro a noite" so' funcionaria se
ele viesse falar comigo exatamente na hora certa — que e' o oposto de um
lembrete. Quem lembra tem de ser a maquina.

⭐ Mesmo raciocinio ja' escrito no `ciclo_semanal_agendado.ps1`.

## ⚠️ ELE NAO SE APAGA SOZINHO — E ISSO E' DE PROPOSITO

A primeira versao chamava `schtasks /Delete` na propria tarefa que estava
rodando. O Windows aceita o pedido e fica ESPERANDO a tarefa terminar; a
tarefa, por sua vez, esperava o delete. Ficou 'Running' travada (resultado
0x41301) ate' alguem parar na mao — medido em 14/09/2026, no primeiro teste.

⭐ Quem limpa e' o proprio Agendador: gatilho `ONCE` nao repete, e a tarefa
e' registrada com `DeleteExpiredTaskAfter`. Uma coisa so' faz a limpeza, e
nao e' a coisa que esta' sendo limpa.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))


def main() -> None:
    a = argparse.ArgumentParser(description="lembrete unico por Telegram")
    a.add_argument("--texto", required=True)
    a.add_argument("--tarefa", default="", help="tarefa do Agendador a apagar")
    o = a.parse_args()

    from engine import telegram

    # ⚠️ SE O TELEGRAM NAO FOR, NAO APAGA A TAREFA. Apagar depois de falhar
    # transformaria "lembrete que nao chegou" em "lembrete que nunca vai
    # chegar" — e ninguem ficaria sabendo de nenhum dos dois.
    if not telegram.enviar(o.texto):
        print("[!] Telegram nao enviou — a tarefa FICA, pra tentar de novo")
        raise SystemExit(1)
    print("lembrete enviado")

    # ⚠️ NAO APAGA A PROPRIA TAREFA AQUI. Ver o cabecalho: a tarefa ficava
    # travada esperando o delete de si mesma. O Agendador limpa sozinho.
    if o.tarefa:
        print(f"(a tarefa {o.tarefa} expira sozinha — gatilho ONCE)")


if __name__ == "__main__":
    main()
