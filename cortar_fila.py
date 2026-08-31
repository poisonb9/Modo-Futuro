# -*- coding: utf-8 -*-
"""Consome a fila de cortes, no maximo 2 por vez.

Pedido do Bryan em 31/08/2026: "vamos de 2 em 2 ate' cortar tudo".

POR QUE ISTO EXISTE COMO MAQUINA, E NAO COMO EU DISPARANDO

Eu nao rodo entre os turnos do Bryan. Um plano do tipo "vou disparando ao
longo da noite" so' funciona se ele ficar me cutucando — e ele pediu
justamente pra nao precisar. Entao quem conta os runs e dispara e' o cron.

⚠️ O TETO DE 2 E' O REPARO DE UM ERRO MEDIDO. Em 31/08/2026 disparei 10 runs
em paralelo. NOVE morreram: as 40 chaves do Gemini secaram no meio do
caminho. As fontes ficaram intactas, mas o runner foi embora. Dois de cada
vez cabe na cota; dez nao cabe.

⚠️ SONDA A COTA ANTES DE DISPARAR. Sem isto, uma noite inteira de cron vira
uma noite inteira de runs mortos com a mesma falha, um a cada 30 minutos. Se
nao ha' cota, este script NAO dispara e diz por que.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FILA = RAIZ / "fila_cortes.json"
REPO = os.environ.get("GITHUB_REPOSITORY") or "poisonb9/Modo-Futuro"
WF = "cortar_de_bruto.yml"
PASTA_DRIVE = "1aM22tjWvoWLTv9v1PrICUzk0_763xcUK"   # "a postar" da conta reserva


def _gh(caminho: str, dados: dict | None = None):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{caminho}",
        data=json.dumps(dados).encode() if dados is not None else None,
        headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        corpo = r.read()
        return json.loads(corpo) if corpo else {}


def em_voo() -> int:
    """Runs de corte ainda vivos. E' o numero que o teto limita."""
    n = 0
    for st in ("queued", "in_progress"):
        d = _gh(f"actions/workflows/{WF}/runs?status={st}&per_page=50")
        n += len(d.get("workflow_runs", []))
    return n


def tem_cota() -> tuple[bool, str]:
    """Uma chave do Gemini responde? Sonda barata antes de gastar runner.

    ⚠️ 503 NAO E' COTA — e' sobrecarga passageira do servidor. Tratar os dois
    como a mesma coisa faria o cron desistir a noite toda por um soluco de
    30 segundos. Na medicao de 31/08 as duas coisas apareceram juntas: 6
    chaves em 429 e 4 em 503.
    """
    chave = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not chave:
        return True, "sem chave pra sondar — seguindo sem sonda"
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.6-flash:generateContent?key={chave}",
        data=json.dumps({"contents": [{"parts": [{"text": "oi"}]}]}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20)
        return True, "cota ok"
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return False, "chave sondada esta SEM COTA — nao vou queimar runner"
        return True, f"sonda deu HTTP {e.code} (nao e' cota) — seguindo"
    except Exception as e:
        return True, f"sonda falhou ({str(e)[:40]}) — seguindo"


def main() -> None:
    d = json.loads(FILA.read_text(encoding="utf-8"))
    teto = int(os.environ.get("TETO") or d.get("teto_em_voo") or 2)
    pendentes = [i for i in d["itens"] if i["estado"] == "pendente"]

    if not pendentes:
        print("fila vazia — nada pendente")
        Path("relato_cortes.txt").write_text(
            "Fila de cortes VAZIA — tudo que estava pendente ja' foi disparado.",
            encoding="utf-8")
        return

    voando = em_voo()
    vagas = max(0, teto - voando)
    print(f"em voo: {voando} | teto: {teto} | vagas: {vagas} | pendentes: {len(pendentes)}")
    if not vagas:
        print("sem vaga — o cron tenta de novo na proxima passada")
        return

    ok, motivo = tem_cota()
    print(f"sonda de cota: {motivo}")
    if not ok:
        Path("relato_cortes.txt").write_text(
            f"Nao disparei: {motivo}. Restam {len(pendentes)} na fila.",
            encoding="utf-8")
        return

    linhas = []
    for item in pendentes[:vagas]:
        entradas = {
            "drive_file_id": item["drive_file_id"],
            "pasta_drive": PASTA_DRIVE,
            "canal": item["canal"],
            "qtd": item["qtd"],
            "idioma": "en",
            "conta": "reserva",
            "dublar": "true",
            "fala_literal": "true",
            "voice_over": "true",
            "voz_clonada": "true",
            "amostra_voz": item["amostra_voz"],
            "selecao_modo": item["selecao_modo"],
        }
        _gh(f"actions/workflows/{WF}/dispatches",
            {"ref": "main", "inputs": entradas})
        item["estado"] = "disparado"
        item["quando"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        linhas.append(f"  {item['canal']:<18} {item['nome'][:46]}")
        print(f"disparado: {item['canal']} — {item['nome'][:50]}")

    FILA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    restam = sum(1 for i in d["itens"] if i["estado"] == "pendente")
    Path("relato_cortes.txt").write_text(
        f"Disparei {len(linhas)} corte(s):\n" + "\n".join(linhas)
        + f"\n\nRestam {restam} na fila.", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
