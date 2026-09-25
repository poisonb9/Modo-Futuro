# -*- coding: utf-8 -*-
"""Ajuste de cor por canal no 9:16 pronto. Canal fora da tabela = intacto."""
from __future__ import annotations

import subprocess
from pathlib import Path

COR_POR_CANAL = {
    "truque.importado": "colorbalance=rm=0.04:gm=-0.01:bm=0.03,eq=saturation=1.06:brightness=0.02",
    "semanestesia.pod": "colorbalance=rm=0.05:gm=0.01:bm=-0.04:rh=0.03:bh=-0.03,eq=contrast=1.06:saturation=0.95",
}


def aplicar_no_lugar(video: Path, canal: str) -> bool:
    from . import canais_registro
    filtro = COR_POR_CANAL.get(canais_registro.canonico(canal) or "")
    if not filtro:
        return False
    video = Path(video)
    novo = video.with_name(video.stem + "_cor.mp4")
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", filtro,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-c:a", "copy", "-movflags", "+faststart", str(novo)],
                       check=True, capture_output=True)
        video.unlink()
        novo.rename(video)
        return True
    except Exception as e:
        print(f"      [!] cor falhou ({type(e).__name__}) — video intacto")
        novo.unlink(missing_ok=True)
        return False
