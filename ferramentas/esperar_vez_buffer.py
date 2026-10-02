# -*- coding: utf-8 -*-
"""Espera a vez de agendar: so' um corte por vez no passo "Enfileirar no Buffer".

02/10/2026: dois cortes do @camarim.kpop agendaram ao mesmo tempo e puseram o
MESMO clipe duas vezes, a 3 min um do outro. Reler o Buffer antes de cada post
resolveria, mas gasta cota do Buffer (dono: nao). Isto pergunta ao GITHUB (de
graca) se outro run deste workflow esta' agendando agora; se estiver, espera.
Falha ABERTA: sem resposta do GitHub ou passado o teto, segue.
"""
import json, os, sys, time, urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "")
RUN = os.environ.get("GITHUB_RUN_ID", "")
TOK = os.environ.get("GH_TOKEN", "")
PASSO = "Enfileirar no Buffer"
TETO_S = 45 * 60


def api(caminho):
    r = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{caminho}",
                               headers={"Authorization": f"Bearer {TOK}",
                                        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.load(x)


def outro_agendando() -> str | None:
    runs = api("actions/workflows/cortar_de_bruto.yml/runs?status=in_progress&per_page=30")["workflow_runs"]
    for r in runs:
        if str(r["id"]) == RUN:
            continue
        for j in api(f"actions/runs/{r['id']}/jobs")["jobs"]:
            for s in j.get("steps") or []:
                if s["name"] == PASSO and s["status"] == "in_progress":
                    return str(r["id"])
    return None


inicio = time.time()
while time.time() - inicio < TETO_S:
    try:
        o = outro_agendando()
    except Exception as e:  # noqa: BLE001
        print(f"[!] GitHub nao respondeu ({type(e).__name__}) — sigo (falha aberta)")
        sys.exit(0)
    if not o:
        print("vez livre — pode agendar")
        sys.exit(0)
    print(f"run {o} esta' agendando agora — espero 30 s")
    time.sleep(30)
print("[!] teto de espera — sigo")
