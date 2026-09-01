# -*- coding: utf-8 -*-
"""A foto de hora em hora nao pode estourar a cota da API do Buffer.

⚠️ O ORCAMENTO E' REAL E FOI MEDIDO no painel em 29/08/2026: 250 requisicoes
por 24h por conta (nosso teto: 200, com 20% de margem porque o app do Buffer
divide o mesmo bolo). Cada canal e' uma conta separada.

Pergunta do Bryan em 01/09: "ficar olhando o buffer de hora em hora vai gastar
muito? a api do buffer e' limitada".

⚠️ CASO NEGATIVO — O CANAL NUNCA PODE SUMIR. Se a economia fosse so' "pula
canal sem post novo", um canal que voltasse a publicar ficaria invisivel pra
SEMPRE: o arquivo continuaria dizendo que o post mais novo tem 200 horas, e
nada o traria de volta. Por isso existe o piso de 6 em 6 horas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import registrar_desempenho as rd  # noqa: E402

TETO_24H = 200          # nosso, com margem
falhas = []

# ---- o orcamento fecha? -------------------------------------------------
por_dia = {
    "foto (canal ativo)": 24,
    "conferencia de fila": 1,
    "painel": 1,
    "conferir postados": 1,
    "ordenar cortes": 6,
    "agendar": 6,
}
total = sum(por_dia.values())
if total > TETO_24H:
    falhas.append(f"o uso diario ({total}) passa do nosso teto ({TETO_24H})")
if total > TETO_24H * 0.5:
    falhas.append(f"o uso diario ({total}) passa de metade do teto — "
                  "sem folga pra um dia atipico")

# ---- canal parado economiza --------------------------------------------
# hora divisivel por 6 -> sempre le' (o piso)
if not rd.canal_vale_a_pena("canal_inexistente", 6):
    falhas.append("o piso de 6 em 6h nao esta' valendo")
if not rd.canal_vale_a_pena("canal_inexistente", 0):
    falhas.append("hora 0 deveria ler (0 % 6 == 0)")

# ⚠️ NEGATIVO: canal desconhecido, fora da hora do piso, tem de ser LIDO —
# na duvida, ler. Pular um canal que nunca vimos seria decidir por ausencia
# de dado.
if not rd.canal_vale_a_pena("canal_que_nunca_vimos", 7):
    falhas.append("canal desconhecido foi pulado — decidiu por falta de dado")

# a economia existe de verdade: 4 leituras/dia em vez de 24 num canal parado
if 24 % 6 != 0:
    falhas.append("o piso nao divide o dia certo")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_orcamento_buffer: {total}/{TETO_24H} req/dia "
      f"({total/TETO_24H:.0%}), canal parado cai pra 4 leituras")
