# -*- coding: utf-8 -*-
"""A fila tem de distinguir COTA, FONTE APAGADA e defeito de verdade.

⚠️ CADA UMA PEDE UMA REACAO DIFERENTE, e confundi-las custou fonte boa hoje:

    cota           -> devolve pra fila SEM contar tentativa (passa sozinho)
    fonte apagada  -> terminal; tentar de novo da' 404 pra sempre
    defeito        -> conta tentativa, desiste na terceira

MEDIDO em 01/09/2026:

  - o "Stop Being F cking Weak" falhou 3x por cota NA SELECAO. O detector so'
    conhecia a mensagem da TRADUCAO, nenhuma foi reconhecida, e o cron
    DESISTIU de uma fonte perfeita.
  - o run #235 morreu com 404 do Drive: o bruto tinha sido apagado depois do
    corte anterior. Devolver pra fila faria 404 pra sempre, dois runs por
    rodada.

⚠️ O DEFEITO DE FUNDO SE REPETIU HOJE TRES VEZES: detector que casa com UMA
frase enxerga UMA classe. Aconteceu no pyflakes (so' "undefined name"), no
teste do 503 (media a prosa) e aqui.
"""
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
fonte = io.open(RAIZ / "cortar_fila.py", encoding="utf-8").read()
falhas = []

# as DUAS mensagens de cota, dos dois passos do motor
for marca in ("SEM COTA", "todas as chaves esgotadas"):
    if marca not in fonte:
        falhas.append(f"o detector de cota nao conhece {marca!r}")

# fonte apagada e' terminal, e nao se confunde com cota
if "sem_fonte" not in fonte:
    falhas.append("nao ha' estado terminal pra bruto apagado")
if "HttpError 404" not in fonte:
    falhas.append("nao reconhece o 404 do Drive")

i404 = fonte.find("def fonte_sumiu")
icota = fonte.find("def falhou_por_cota")
if i404 < 0 or icota < 0:
    falhas.append("um dos dois classificadores sumiu")
else:
    # ⚠️ NEGATIVO: o 404 tem de ser checado ANTES da cota. Um run que morre
    # por fonte apagada nao pode voltar pra fila so' porque o log tambem
    # menciona cota em alguma linha de rotacao de chave.
    iuso404 = fonte.find("fonte_sumiu(item[")
    iusocota = fonte.find("falhou_por_cota(item[")
    if iuso404 < 0 or iusocota < 0:
        falhas.append("um dos classificadores nao e' usado")
    elif iuso404 > iusocota:
        falhas.append("a cota e' checada ANTES do 404 — fonte apagada "
                      "voltaria pra fila e bateria em 404 pra sempre")

# ⚠️ NEGATIVO: cota nao pode contar tentativa
if "nao conta como tentativa" not in fonte:
    falhas.append("cota voltou a contar tentativa — desistiria de fonte boa")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print("[ok] teste_classificar_falha: cota (2 mensagens), fonte apagada "
      "terminal e checada primeiro")
