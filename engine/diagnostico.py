# -*- coding: utf-8 -*-
"""Na PREVIA, guarda cada etapa da trilha dublada ao lado do clipe.

POR QUE EXISTE (26/09/2026)

O fim mudo (a ultima frase some, RETOMADA §1.1) nao se reproduz localmente:
com voz falsa todas as etapas mantem a frase. So' a voz D real (edge +
ChatterboxVC, que nao cabe na maquina local) mostra o defeito, e a nuvem
apagava o `trabalho/` no fim do run. Sem as trilhas do meio, cada hipotese
virava um corte inteiro no escuro.

Com `PREVIA=true` (o workflow passa o input `previa`), copia para
`<pasta do clipe>/diagnostico/`:
  voz_frase_*.wav (+ _edge.mp3, _b, _g)   cada frase como saiu do motor
  ancoragem.json                          frases, inicios, duracoes, escala
  voz_ancorada.wav                        as frases somadas no tempo (amix)
  trilha_dublada_clonada.wav              + apad ou atempo
  trilha_com_fundo.wav                    + fundo do original (Demucs)
  trilha_com_fim.wav                      + som original depois da fala
  fundo_demucs.wav, fundo_musica.json     o fundo antes de tirar a musica
e o artifact `previa-clipes` leva a pasta junto. A ordem acima e' a ordem do
motor: a primeira trilha em que a ultima frase nao esta' e' a etapa culpada.

Fora da previa nao faz nada (nao gasta disco nem tempo em producao).
Falha ABERTA: erro aqui nunca derruba o corte.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

PASTA = "diagnostico"
_PADROES = ("voz_frase_*", "ancoragem.json", "voz_ancorada.wav",
            "voz_concatenada.wav", "trilha_dublada_clonada.wav",
            "trilha_com_fundo.wav", "trilha_com_fim.wav",
            "fundo_demucs.wav", "fundo_musica.json")


def ligado() -> bool:
    return os.environ.get("PREVIA", "").strip().lower() in ("true", "1")


def guardar(trabalho: Path, pasta_clipe: Path) -> list[str]:
    """Copia as trilhas de `trabalho` para `pasta_clipe/diagnostico`.
    Devolve os nomes copiados ([] fora da previa ou se nada existir)."""
    if not ligado():
        return []
    try:
        trabalho, destino = Path(trabalho), Path(pasta_clipe) / PASTA
        achados = sorted({p for pad in _PADROES for p in trabalho.glob(pad)
                          if p.is_file()})
        if not achados:
            return []
        destino.mkdir(parents=True, exist_ok=True)
        for p in achados:
            shutil.copy2(p, destino / p.name)
        print(f"      [diag] {len(achados)} trilha(s) do meio guardadas em "
              f"{PASTA}/ (previa)", flush=True)
        return [p.name for p in achados]
    except Exception as e:
        print(f"      [!] diagnostico nao guardado ({type(e).__name__})", flush=True)
        return []
