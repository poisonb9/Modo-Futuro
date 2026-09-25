# -*- coding: utf-8 -*-
"""Velocidade por canal no 9:16 pronto (video + voz, sem afinar)."""
from __future__ import annotations

import subprocess
from pathlib import Path

VELOCIDADE_POR_CANAL = {"truque.importado": 1.1}


def fator(canal: str) -> float:
    from . import canais_registro
    return VELOCIDADE_POR_CANAL.get(canais_registro.canonico(canal) or "", 1.0)


def aplicar_no_lugar(video: Path, canal: str) -> bool:
    f = fator(canal)
    if abs(f - 1.0) < 0.01:
        return False
    video = Path(video)
    novo = video.with_name(video.stem + "_r.mp4")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video),
                        "-filter_complex", f"[0:v]setpts=PTS/{f}[v];[0:a]atempo={f}[a]",
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset",
                        "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", str(novo)],
                       check=True, capture_output=True)
        video.unlink()
        novo.rename(video)
        return True
    except Exception as e:
        print(f"      [!] velocidade falhou ({type(e).__name__}) — video intacto")
        novo.unlink(missing_ok=True)
        return False
