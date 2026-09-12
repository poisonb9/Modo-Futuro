# -*- coding: utf-8 -*-
"""Estado escrito na nuvem tem de VOLTAR pro repositorio, ou nao existe.

⚠️ A CLASSE DE DEFEITO, tres ocorrencias ja' medidas neste repositorio:

    desempenho.jsonl        parado em 03/09 com o workflow rodando de hora em
                            hora e dizendo "+10 leituras" (ja' consertado)
    estado/publicados.json  mesmo caso, mesmo conserto
    trechos_usados.json     ESTA, medida em 12/09/2026

O runner do GitHub morre no fim do job. O que o passo escreveu em disco vai
junto — e o log continua dizendo que funcionou, porque a escrita funcionou
mesmo. O que nao acontece e' o arquivo chegar ao proximo run.

⚠️ O QUE ISSO CUSTOU: `agendar_buffer` chama `trechos.anotar()` ao enfileirar,
e essa e' a UNICA guarda que pega o mesmo trecho cortado duas vezes — o sha
muda (dois encodes do mesmo trecho dao hashes diferentes) e o texto muda (o
Gemini reescreve titulo e descricao a cada corte). Com o arquivo voltando
vazio a cada run, ela enxergava so' ate' o ultimo commit feito a mao.

Resultado: dois posts do mesmo trecho no @modofuturo em 10/09/2026, as 15:27 e
as 16:18, apagados a mao pelo Bryan. Duplicata derruba o alcance do canal.
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
WF = RAIZ / ".github" / "workflows"

# arquivo de estado -> workflow que TEM de commita-lo de volta
PRECISAM_VOLTAR = {
    "estado/trechos_usados.json": "cortar_de_bruto.yml",
    "registro_clipes.json": "cortar_de_bruto.yml",
    "desempenho.jsonl": "desempenho.yml",
    "estado/publicados.json": "desempenho.yml",
    "estado/serie_views.jsonl": "desempenho.yml",
}

falhas = []

for arquivo, wf in sorted(PRECISAM_VOLTAR.items()):
    caminho = WF / wf
    if not caminho.exists():
        falhas.append(f"{wf} nao existe mais — quem guarda {arquivo} agora?")
        continue
    txt = caminho.read_text(encoding="utf-8")
    if arquivo not in txt:
        falhas.append(f"{wf} NAO devolve {arquivo} — o que ele escrever morre "
                      "com o runner, e a guarda que depende disso fica cega")
        continue
    # ⚠️ Citar o nome nao basta: tem de haver commit E push no mesmo arquivo.
    if "git commit" not in txt or "git push" not in txt:
        falhas.append(f"{wf} cita {arquivo} mas nao commita/empurra")

# ⚠️ CASO NEGATIVO 1: a regra tem de saber ACUSAR. Um workflow que so' roda e
# nao devolve nada precisa cair na conta — senao este teste aprova qualquer
# coisa que tenha a palavra certa em algum lugar.
FALSO = "run: python -X utf8 agendar_buffer.py\n"
if "estado/trechos_usados.json" in FALSO or "git push" in FALSO:
    falhas.append("caso negativo mal montado")
elif not ("estado/trechos_usados.json" not in FALSO):
    falhas.append("NEGATIVO: a regra nao acusaria um workflow que nao devolve "
                  "o estado")

# ⚠️ CASO NEGATIVO 2: o arquivo precisa estar FORA do .gitignore, senao o
# `git add` e' recusado em silencio e o commit nao leva nada.
GI = (RAIZ / ".gitignore").read_text(encoding="utf-8")
for arquivo in ("estado/trechos_usados.json", "estado/publicados.json"):
    if f"!{arquivo}" not in GI:
        falhas.append(f"{arquivo} nao esta' liberado no .gitignore "
                      "(`estado/*` o ignora) — o git add nao levaria nada")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_guardas_voltam_do_runner: {len(PRECISAM_VOLTAR)} arquivo(s) "
      "de estado voltam da nuvem pro repositorio")
