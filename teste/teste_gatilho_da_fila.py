# -*- coding: utf-8 -*-
"""A fila e' puxada pelo FIM DE UM CORTE, nao so' pelo relogio.

⚠️ MEDIDO em 01/09/2026. O `schedule` deste workflow pedia `*/30` e disparou
de fato as 00:41, 06:00 e 10:54 — intervalos de ~5 HORAS. O cron do Actions e'
best-effort; `*/30` e' pedido, nao garantia. Com teto de 2 em voo, a fila
ficava com vaga livre por horas.

⚠️ O NOME TEM DE BATER EXATAMENTE, acentos inclusive. `workflow_run` casa por
NOME do workflow; um acento fora do lugar nao da' erro em lugar nenhum — o
gatilho simplesmente nunca dispara, e a falha e' silenciosa. Foi por isso que
este teste existe, e nao por desconfianca do YAML.

⚠️ E O CRON CONTINUA. Ele deixou de ser o motor e virou REDE: se o evento se
perder, ou se a fila parar com tudo falhando por cota (nao ha' corte
terminando, logo nao ha' evento), o relogio ainda puxa.
"""
import io
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
falhas = []

fila = yaml.safe_load(io.open(RAIZ / ".github/workflows/cortar_fila.yml",
                              encoding="utf-8"))
corte = yaml.safe_load(io.open(RAIZ / ".github/workflows/cortar_de_bruto.yml",
                               encoding="utf-8"))
gat = fila[True]          # `on:` vira True no YAML

if "workflow_run" not in gat:
    falhas.append("a fila nao reage ao fim de um corte — so' ao relogio")
else:
    esperado = gat["workflow_run"]["workflows"]
    if corte["name"] not in esperado:
        falhas.append(f"nome nao bate: fila espera {esperado}, "
                      f"corte se chama {corte['name']!r}")
    if "completed" not in gat["workflow_run"].get("types", []):
        falhas.append("nao escuta o tipo 'completed'")

# ⚠️ o cron TEM de continuar: sem corte terminando, nao ha' evento nenhum
if "schedule" not in gat:
    falhas.append("o cron sumiu — sem ele, fila travada por cota nunca retoma")

# e o teto continua sendo 2
fonte = io.open(RAIZ / "cortar_fila.py", encoding="utf-8").read()
if 'os.environ.get("TETO") or d.get("teto_em_voo") or 2' not in fonte:
    falhas.append("o teto de 2 em voo saiu do lugar")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print("[ok] teste_gatilho_da_fila: puxada pelo fim do corte, cron como rede, "
      "teto de 2 intacto")
