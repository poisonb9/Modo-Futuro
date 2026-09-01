# -*- coding: utf-8 -*-
"""O volume do original fica na faixa util, e o ambiente manda.

O Bryan ouviu o corte do "Master Discipline" em 01/09/2026 e disse que a voz
original estava "um pouco alta". Baixou de 0.18 (~-15 dB) pra 0.12 (~-18,4).

⚠️ PISO DE 0.10. Abaixo disso o original vira ruido e o efeito de autoridade
se perde — que e' o unico motivo do voice over existir. Baixar sem limite
resolveria a reclamacao destruindo o recurso.

⚠️ E TETO: se alguem puser 1.0 por engano, o original briga de igual pra
igual com a dublagem e o corte fica inaudivel. Os dois lados sao guardados.
"""
import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

falhas = []
v = config.VOICE_OVER_VOL_ORIGINAL
if not (0.10 <= v <= 0.30):
    falhas.append(f"volume fora da faixa util: {v}")
if v >= 0.18:
    falhas.append(f"nao abaixou: {v} (o Bryan pediu mais baixo que 0.18)")

# o ambiente tem de mandar — pra ajustar por disparo, sem commit
os.environ["VOICE_OVER_VOL_ORIGINAL"] = "0.15"
importlib.reload(config)
if abs(config.VOICE_OVER_VOL_ORIGINAL - 0.15) > 1e-9:
    falhas.append("a variavel de ambiente nao sobrepoe o padrao")
del os.environ["VOICE_OVER_VOL_ORIGINAL"]
importlib.reload(config)
if abs(config.VOICE_OVER_VOL_ORIGINAL - 0.12) > 1e-9:
    falhas.append("sem a variavel, nao voltou pro padrao")

# a cadeia de audio precisa REALMENTE usar o valor
from engine import render  # noqa: E402
cadeia = render._cadeia_audio_vo()
if f"volume={config.VOICE_OVER_VOL_ORIGINAL}" not in cadeia:
    falhas.append(f"o filtro nao usa o valor configurado: {cadeia[:60]}")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_volume_voice_over: {config.VOICE_OVER_VOL_ORIGINAL} "
      "na faixa, ambiente manda, filtro usa")
