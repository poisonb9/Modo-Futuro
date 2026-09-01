# -*- coding: utf-8 -*-
"""A origem descoberta por nome de arquivo nunca se passa por certeza.

⚠️ O BURACO QUE ISTO TAPA: quando o bruto vem do Drive, e nao de um download
nosso, o manifesto saia com `url_origem: ""`. Em 01/09/2026 o Bryan pediu os
episodios anteriores de um corte que comecava no "dia 3" — o clipe existia, o
canal existia, e nao havia como saber QUE video do YouTube era.

⚠️ CASO NEGATIVO 1: nome generico nao pode virar origem. `fonte.mp4` buscado
no YouTube devolve qualquer coisa, e essa qualquer coisa entraria no
manifesto como a origem do clipe.

⚠️ CASO NEGATIVO 2: semelhanca baixa nao pode virar origem. Plantar um link
errado e' pior que deixar vazio — ninguem confere origem depois, e a busca de
episodios iria pro canal errado com cara de acerto.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import origem  # noqa: E402

falhas = []

# limpeza de nome — o que chega do Drive
CASOS = [
    ("First Day At Gym _ Full Workout Plan.mp4", "First Day At Gym Full Workout Plan"),
    ("YTDown.com_YouTube_AMAZING-Dessert.mp4", "AMAZING-Dessert"),
    ("Bambi eyes tutorial (1).mp4", "Bambi eyes tutorial"),
]
for bruto, esperado in CASOS:
    if origem.limpar(bruto) != esperado:
        falhas.append(f"limpar({bruto!r}) = {origem.limpar(bruto)!r}, "
                      f"esperava {esperado!r}")

# NEGATIVO 1 — nome generico devolve vazio SEM nem consultar a rede
for g in ("fonte.mp4", "video.mp4", "bruto.mp4", "output.mp4"):
    if origem.descobrir(g) != {}:
        falhas.append(f"{g} virou origem — buscaria 'fonte' no YouTube")

# NEGATIVO 2 — sem chave de API, devolve vazio em vez de estourar
import os  # noqa: E402
guardadas = {k: os.environ.pop(k) for k in list(os.environ)
             if k.startswith("YOUTUBE_API_KEY")}
try:
    if origem.descobrir("Um titulo qualquer de video") != {}:
        falhas.append("sem chave deveria devolver vazio")
finally:
    os.environ.update(guardadas)

# o limiar existe e nao e' frouxo
fonte = (Path(__file__).resolve().parent.parent / "engine/origem.py").read_text(
    encoding="utf-8")
if "nota_melhor < 0.5" not in fonte:
    falhas.append("o limiar de semelhanca sumiu — qualquer resultado viraria origem")
if "confianca" not in fonte:
    falhas.append("a marca de confianca sumiu — palpite viraria certeza")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print("[ok] teste_origem: nome limpo, generico recusado, sem chave nao estoura")
