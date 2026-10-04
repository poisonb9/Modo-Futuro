# -*- coding: utf-8 -*-
"""Anima o WALLPAPER semanal holografico (04/10/2026, prototipo aprovado para teste).

Efeitos (so' luz, os objetos nao se mexem): faixa holografica diagonal passando,
arco-iris respirando nas areas claras, faiscas piscando nos pontos mais claros e
zoom sutil. Loop de 5 s a 24 fps.

    python -X utf8 ferramentas/animar_wallpaper.py imagem.png saida_sem_extensao

Saida: <saida>.mp4 (wallpaper animado) e <saida>.gif (compartilhar).
⚠️ O GIF de 720px saiu com 22 MB no 1o teste: aqui ele sai com 360px, 3 s e 128
cores. Conferir o tamanho e baixar mais se passar de 5 MB.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


def quadros(src: Path, pasta: Path, largura: int = 720, n: int = 120) -> None:
    im0 = Image.open(src).convert("RGB")
    W = largura
    H = int(im0.height * W / im0.width) // 2 * 2
    base = np.asarray(im0.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    lum = base.mean(2)
    brilho = np.clip((lum - .62) / .38, 0, 1)
    yy, xx = np.mgrid[0:H, 0:W]
    rng = np.random.default_rng(3)
    cand = np.argwhere(lum > np.quantile(lum, .985))
    pts = cand[rng.choice(len(cand), min(70, len(cand)), replace=False)]
    fase = rng.random(len(pts))
    pos = (xx + yy * 0.6) / (W + H * 0.6)
    for f in range(n):
        t = f / n
        d = np.abs(((pos - t * 1.6 + 0.3) + 1) % 1 - 0.5)
        faixa = np.exp(-(d / 0.06) ** 2)
        hue = (pos * 2 + t) % 1
        arco = np.stack([np.clip(np.abs(((hue * 6 + k) % 6) - 3) - 1, 0, 1) for k in (0, 4, 2)], 2)
        img = base + (faixa * 0.35)[..., None] * arco + (brilho * 0.10 * np.sin(2 * np.pi * (t + pos)))[..., None] * arco
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        z = 1 + 0.015 * np.sin(2 * np.pi * t)
        cw, ch = int(W / z), int(H / z)
        im = im.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32)
        for (py, px), ph in zip(pts, fase):
            s = max(0, np.sin(2 * np.pi * (t * 2 + ph))) ** 8
            if s < .05:
                continue
            r = int(3 + 6 * s)
            y0, y1, x0, x1 = max(0, py - r * 3), min(H, py + r * 3), max(0, px - r * 3), min(W, px + r * 3)
            gy, gx = np.mgrid[y0:y1, x0:x1]
            cruz = (np.exp(-((gy - py) / 1.2) ** 2) * np.exp(-((gx - px) / (r * 1.6)) ** 2)
                    + np.exp(-((gx - px) / 1.2) ** 2) * np.exp(-((gy - py) / (r * 1.6)) ** 2))
            a[y0:y1, x0:x1] = np.clip(a[y0:y1, x0:x1] + 255 * s * cruz[..., None], 0, 255)
        Image.fromarray(a.astype(np.uint8)).save(pasta / f"{f:03d}.png")


def main() -> None:
    src, saida = Path(sys.argv[1]), Path(sys.argv[2])
    pasta = Path(tempfile.mkdtemp())
    quadros(src, pasta)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", str(pasta / "%03d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(saida.with_suffix(".mp4"))], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", str(pasta / "%03d.png"), "-t", "3",
                    "-vf", "fps=15,scale=360:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer",
                    str(saida.with_suffix(".gif"))], check=True)
    for p in pasta.glob("*.png"):
        p.unlink()
    pasta.rmdir()
    for ext in (".mp4", ".gif"):
        print(saida.with_suffix(ext), round(saida.with_suffix(ext).stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
