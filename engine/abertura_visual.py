# -*- coding: utf-8 -*-
"""Abertura visual: o primeiro 1,5 s mostra o ASSUNTO, nao o estudio.

## POR QUE EXISTE (26/09/2026, plano de virada item 2, aprovado pelo dono)

MEDIDO nos clipes do @modofuturo (quadros de 0 a 3,2 s de 17 clipes):
5 de 8 perdedores (91-137 views) abriam no MESMO estudio de podcast, alguem
ao microfone; 6 de 9 vencedores (551-637) abriam na maquina, no chip ou na
fabrica. A audiencia sai aos 0:01-0:02 (Studio, 08/09). Quem rola o feed ve
"mais um podcast" antes de ouvir qualquer coisa.

## O QUE FAZ

Quando o trecho ABRE num rosto (`abertura_mostra` = pessoa_falando/parado) e
a selecao apontou `momento_visual_s` (o segundo em que o assunto aparece mais
forte DENTRO do trecho), a IMAGEM dos primeiros `ABERTURA_VISUAL_S` segundos
do clipe e' trocada por esse momento. E' o "cold open" de documentario.

⚠️ SO' A IMAGEM. O audio do clipe fica intacto e com a mesma duracao, entao a
transcricao, a dublagem ancorada no tempo e a legenda nao mudam em nada. A voz
comeca no quadro 0 por cima da maquina — que e' exatamente o efeito.

FALHA ABERTA: qualquer erro devolve o clipe como estava.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import config

ABRE_SEM_ASSUNTO = {"pessoa_falando", "parado"}


def no_canal() -> bool:
    from .canais_registro import canonico
    return canonico(os.environ.get("CANAL_ESPERADO")) in config.CANAIS_ABERTURA_VISUAL


def instante(c: dict, ini: float, fim: float,
             dur: float = config.ABERTURA_VISUAL_S) -> float | None:
    """O segundo ABSOLUTO na fonte de onde tirar a abertura, ou None.

    Exposto pro teste. None quando: canal fora da lista, trecho ja' abre no
    assunto, sem `momento_visual_s`, ou o momento cai fora do trecho (ou tao
    perto do comeco que ja' seria a propria abertura).
    """
    from .canais_registro import canonico
    if canonico(os.environ.get("CANAL_ESPERADO")) not in config.CANAIS_ABERTURA_VISUAL:
        return None
    if str(c.get("abertura_mostra") or "").strip().lower() not in ABRE_SEM_ASSUNTO:
        return None
    try:
        t = float(c.get("momento_visual_s"))
    except (TypeError, ValueError):
        return None
    if t < ini + dur or t + dur > fim:
        return None
    return t


def aplicar(fonte: Path, bruto: Path, t: float,
            dur: float = config.ABERTURA_VISUAL_S) -> Path:
    """Troca a imagem de [0, dur) do `bruto` pela da `fonte` em [t, t+dur)."""
    saida = bruto.with_name(bruto.stem + "_abertura.mp4")
    filtro = (
        f"[1:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS[a0];"
        f"[a0][0:v]scale2ref[a][base];"
        f"[a]setsar=1[a1];"
        f"[base]trim=start={dur:.3f},setpts=PTS-STARTPTS,setsar=1[b];"
        f"[a1][b]concat=n=2:v=1:a=0[v]"
    )
    try:
        subprocess.run([
            "ffmpeg", "-v", "error", "-y",
            "-i", str(bruto),
            "-ss", f"{t:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", str(fonte),
            "-filter_complex", filtro,
            "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "copy", str(saida),
        ], check=True, capture_output=True, timeout=300)
        from . import midia
        if abs(midia.duracao(saida) - midia.duracao(bruto)) > 0.3:
            print("      [!] abertura visual: duracao mudou — mantido o original",
                  flush=True)
            return bruto
        print(f"      abertura visual: 1o {dur:.1f}s trocado pelo assunto "
              f"(fonte {t:.1f}s)", flush=True)
        return saida
    except Exception as e:
        print(f"      [!] abertura visual falhou ({type(e).__name__}) — "
              f"segue o original", flush=True)
        return bruto
