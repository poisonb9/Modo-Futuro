# -*- coding: utf-8 -*-
"""Previa guarda as trilhas do meio (engine/diagnostico.py).

POR QUE EXISTE

26/09/2026, fim mudo (RETOMADA §1.1): a ultima frase some so' com a voz D
real, na nuvem, e o `trabalho/` morria com o runner. Na previa, cada etapa
da trilha vai para `<clipe>/diagnostico/` e sai no artifact.

  [1] NEGATIVO: sem PREVIA nada e' copiado (producao nao gasta disco)
  [2] com PREVIA=true: frases, ancoragem e as trilhas de cada etapa copiadas
  [3] o workflow passa PREVIA ao main.py e o artifact leva `diagnostico/`
  [4] main.py guarda DEPOIS do preencher_com_original (a ultima etapa)
  [5] voz_clonada grava ancoragem.json e zera NaN do conversor, avisando

Roda com: python teste/teste_diagnostico_previa.py
"""
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import diagnostico  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


with tempfile.TemporaryDirectory() as tmp:
    trab, clipe = Path(tmp) / "dub_01", Path(tmp) / "01_clipe"
    trab.mkdir(); clipe.mkdir()
    nomes = ["voz_frase_000.wav", "voz_frase_000_edge.mp3", "voz_frase_011_g.wav",
             "ancoragem.json", "voz_ancorada.wav", "trilha_dublada_clonada.wav",
             "trilha_com_fundo.wav", "trilha_com_fim.wav", "fundo_demucs.wav",
             "fundo_musica.json"]
    for n in nomes + ["lixo.tmp"]:
        (trab / n).write_bytes(b"x")

    os.environ.pop("PREVIA", None)
    checar(diagnostico.guardar(trab, clipe) == [] and not (clipe / "diagnostico").exists(),
           "[1] sem PREVIA nada e' copiado")

    os.environ["PREVIA"] = "true"
    feitos = diagnostico.guardar(trab, clipe)
    checar(sorted(feitos) == sorted(nomes), f"[2] copiou as {len(nomes)} trilhas ({len(feitos)})")
    checar(not (clipe / "diagnostico" / "lixo.tmp").exists(), "[2] so' as trilhas, nada mais")
    os.environ.pop("PREVIA", None)

wf = (RAIZ / ".github/workflows/cortar_de_bruto.yml").read_text(encoding="utf-8")
checar("PREVIA: ${{ inputs.previa }}" in wf, "[3] workflow passa PREVIA ao main.py")
checar("saida/**/diagnostico/**" in wf, "[3] artifact leva diagnostico/")

main = (RAIZ / "main.py").read_text(encoding="utf-8")
i_fim, i_diag = main.find("cauda.preencher_com_original("), main.find("diagnostico.guardar(")
checar(0 < i_fim < i_diag, "[4] main.py guarda depois do preencher_com_original")

vc = (RAIZ / "engine/voz_clonada.py").read_text(encoding="utf-8")
checar('"ancoragem.json"' in vc, "[5] voz_clonada grava ancoragem.json")
checar("nan_to_num" in vc and "NaN/inf" in vc, "[5] NaN do conversor zerado com aviso")

print(f"\n{'FALHOU: ' + str(len(falhas)) if falhas else 'tudo ok'}")
sys.exit(1 if falhas else 0)
