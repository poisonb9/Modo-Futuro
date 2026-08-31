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
    """Alguma chave do Gemini responde 200? So' o 200 libera o disparo.

    ⚠️ UMA CHAVE SO' NAO DECIDE NADA. A primeira versao disto sondava a
    `GEMINI_API_KEY` e liberava em qualquer coisa que nao fosse 429. Em
    31/08/2026 essa chave respondeu 503 — sobrecarga, nao cota — a sonda
    liberou, e os DOIS runs morreram na selecao com as 20 chaves esgotadas.
    A leitura estava certa e a conclusao errada: 503 numa chave nao diz nada
    sobre as outras dezenove.

    ⚠️ E 429 CONTINUA SENDO DIFERENTE DE 503. Nao voltei a juntar os dois: a
    mensagem final distingue "sem cota" (espere o reset) de "sobrecarregado"
    (tente de novo daqui a pouco), porque sao esperas de tamanhos diferentes.
    O que mudou e' que agora o SILENCIO tambem barra — sem um 200 na mao,
    nao gasto runner.
    """
    chaves = [v for v in (os.environ.get(n) for n in
                          ("GEMINI_API_KEY", "GEMINI_API_KEY_2",
                           "GEMINI_API_KEY_3", "GEMINI_API_KEY_4",
                           "GEMINI_API_KEY_5")) if (v or "").strip()]
    if not chaves:
        return True, "nenhuma chave pra sondar — seguindo sem sonda"

    placar = {"sem cota": 0, "sobrecarregado": 0, "mudo": 0}
    for chave in chaves:
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3.6-flash:generateContent?key={chave.strip()}",
            data=json.dumps({"contents": [{"parts": [{"text": "oi"}]}]}).encode(),
            headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=20)
            return True, f"chave respondeu 200 ({len(chaves)} sondadas)"
        except urllib.error.HTTPError as e:
            placar["sem cota" if e.code == 429 else "sobrecarregado"] += 1
        except Exception:
            placar["mudo"] += 1

    resumo = ", ".join(f"{v} {k}" for k, v in placar.items() if v)
    return False, f"nenhuma das {len(chaves)} chaves respondeu 200 ({resumo})"


def devolver_os_que_falharam(d: dict) -> list[str]:
    """Item cujo run falhou volta pra `pendente`. Sem isto a fila DRENA.

    ⚠️ ERA UM DEFEITO REAL, nao precaucao: o item era marcado `disparado` e
    ficava assim pra sempre. Um run que morre por cota levava a fonte junto,
    e ao fim da noite a fila estaria vazia com zero corte feito — o cron
    tocando alegremente pra ninguem.

    ⚠️ TEM TETO DE TENTATIVAS. Sem ele, uma fonte defeituosa (bruto corrompido,
    id que sumiu do Drive) voltaria pra fila pra sempre, queimando dois runs a
    cada meia hora, e a fila nunca andaria.
    """
    voltaram = []
    for item in d["itens"]:
        if item.get("estado") != "disparado" or not item.get("run_id"):
            continue
        try:
            r = _gh(f"actions/runs/{item['run_id']}")
        except Exception:
            continue
        if r.get("status") != "completed":
            continue
        if r.get("conclusion") == "success":
            item["estado"] = "pronto"
            continue
        item["tentativas"] = int(item.get("tentativas") or 0) + 1
        if item["tentativas"] >= 3:
            item["estado"] = "desistido"
            voltaram.append(f"  DESISTI de {item['nome'][:40]} (3 tentativas)")
        else:
            item["estado"] = "pendente"
            item.pop("run_id", None)
            voltaram.append(f"  volta pra fila: {item['nome'][:40]}"
                            f" (tentativa {item['tentativas']})")
    return voltaram


def run_recem_criado() -> int | None:
    """O id do run que acabamos de disparar.

    A API de dispatch nao devolve o id. Como o workflow tem `concurrency` e
    esta e' a unica coisa que dispara corte automaticamente, o run mais novo
    e' o nosso. Se nao aparecer a tempo, devolve None e o item fica sem id —
    o que so' custa nao poder devolve-lo pra fila depois.
    """
    import time
    for _ in range(10):
        time.sleep(3)
        d = _gh(f"actions/workflows/{WF}/runs?per_page=1")
        runs = d.get("workflow_runs") or []
        if runs:
            return runs[0]["id"]
    return None


def main() -> None:
    d = json.loads(FILA.read_text(encoding="utf-8"))
    teto = int(os.environ.get("TETO") or d.get("teto_em_voo") or 2)

    # ⚠️ ANTES DE QUALQUER COISA: recolher os que falharam. Se isto rodasse
    # depois do disparo, um item que falhou continuaria fora da conta e a
    # fila andaria pra frente sem ele.
    devolvidos = devolver_os_que_falharam(d)
    for linha in devolvidos:
        print(linha)
    if devolvidos:
        FILA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + chr(10),
                        encoding="utf-8")

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
        rid = run_recem_criado()
        if rid:
            item["run_id"] = rid
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
