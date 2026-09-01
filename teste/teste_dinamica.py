# -*- coding: utf-8 -*-
"""A dinamica medida tem de SEPARAR trecho intenso de trecho calmo.

Pedido do Bryan em 01/09/2026: aplicar a dinamica do audio original na
dublagem, pra ela deixar de soar monotona.

⚠️ O TESTE USA AUDIO DE VERDADE, gerado com ffmpeg — nao numeros inventados.
Um teste que alimentasse dicionarios prontos provaria a aritmetica e nao
provaria que a MEDICAO funciona, que e' a parte que pode estar errada.

⚠️ E O CASO NEGATIVO E' O QUE IMPORTA: audio UNIFORME nao pode virar
dinamica. Se blocos iguais saissem com enfases diferentes, estariamos
injetando variacao aleatoria e chamando de entonacao — pior que a monotonia,
porque some com a intencao do original.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import dinamica  # noqa: E402

tmp = Path(tempfile.mkdtemp())
falhas = []


def gerar(caminho: Path, partes: list[str]) -> None:
    """Concatena trechos descritos por filtros do ffmpeg."""
    filtros = ";".join(f"{p}[a{i}]" for i, p in enumerate(partes))
    entradas = "".join(f"[a{i}]" for i in range(len(partes)))
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-filter_complex",
         f"{filtros};{entradas}concat=n={len(partes)}:v=0:a=1[out]",
         "-map", "[out]", str(caminho)], check=True, capture_output=True)


# ---- POSITIVO: calmo, depois intenso ------------------------------------
# 0-2s tom fraco e constante; 2-4s tom forte e MODULADO (volume oscilando)
forte = ("sine=frequency=200:duration=2,volume=0.9,"
         "tremolo=f=6:d=0.8")
fraco = "sine=frequency=200:duration=2,volume=0.05"
a = tmp / "a.wav"
gerar(a, [fraco, forte])

med = dinamica.medir_blocos(a, [(0.0, 2.0), (2.0, 4.0)])
if len(med) != 2:
    falhas.append("nao mediu os dois blocos")
elif med[1]["db"] <= med[0]["db"]:
    falhas.append(f"nao viu o bloco forte: {med[0]['db']:.1f} vs {med[1]['db']:.1f} dB")
elif med[1]["variacao_db"] <= med[0]["variacao_db"]:
    falhas.append("nao viu a MODULACAO do bloco forte")

enf = dinamica.enfase_por_bloco(med)
if enf and not (enf[0] < enf[1]):
    falhas.append(f"enfase nao acompanhou a intensidade: {enf}")
if enf and not all(dinamica.ENFASE_MIN <= e <= dinamica.ENFASE_MAX for e in enf):
    falhas.append(f"enfase saiu da faixa segura: {enf}")

gan = dinamica.ganho_por_bloco(med)
if gan and not (gan[0] < 1.0 < gan[1]):
    falhas.append(f"ganho nao ficou centrado em 1.0: {gan}")

# ---- NEGATIVO: audio UNIFORME nao pode virar dinamica -------------------
b = tmp / "b.wav"
gerar(b, [fraco, fraco])
med2 = dinamica.medir_blocos(b, [(0.0, 2.0), (2.0, 4.0)])
enf2 = dinamica.enfase_por_bloco(med2)
if enf2 and abs(enf2[0] - enf2[1]) > 0.05:
    falhas.append(f"audio uniforme gerou enfases diferentes: {enf2}")
gan2 = dinamica.ganho_por_bloco(med2)
if gan2 and any(abs(g - 1.0) > 0.05 for g in gan2):
    falhas.append(f"audio uniforme mexeu no volume: {gan2}")

# ---- pausas -------------------------------------------------------------
p = dinamica.pausas_originais([(0.0, 2.0), (3.5, 5.0), (5.0, 6.0)])
if p != [0.0, 1.5, 0.0]:
    falhas.append(f"pausas erradas: {p}")
# blocos sobrepostos nao podem gerar pausa negativa
if dinamica.pausas_originais([(0.0, 2.0), (1.8, 3.0)])[1] != 0.0:
    falhas.append("sobreposicao virou pausa negativa")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_dinamica: intenso x calmo separados (enfase "
      f"{enf[0]:.2f} -> {enf[1]:.2f}), uniforme nao inventa variacao")
