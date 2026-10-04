# -*- coding: utf-8 -*-
"""Pacote de figurinhas de WhatsApp a partir dos BALOES (04/10/2026).

Cada balao (PNG/WEBP com fundo transparente) vira:
  - <nome>.webp          figurinha PARADA, 512x512, <= 100 KB
  - <nome>_anim.webp     figurinha ANIMADA (balao flutuando), 512x512, <= 500 KB
  - <nome>.gif           a mesma animacao em GIF (Stories / GIPHY)
e o pacote ganha bandeja.png (96x96, <= 50 KB), o icone do pacote.

    python -X utf8 ferramentas/figurinhas_whatsapp.py pasta_fonte pasta_saida [icone_nome]

Limpeza: o recorte do GPT deixa uma franja avermelhada no contorno. Aqui a
borda semi-transparente recebe a cor do pixel opaco mais proximo e o alfa e'
afinado 1 px — some a franja sem comer o balao.
Animacao: sobe e desce 14 px com leve balanco (+-4 graus) pivotando na cordinha,
loop fechado de 2 s a 15 fps. Regras do WhatsApp conferidas no fim (tamanho).
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

LADO, MARGEM = 512, 16
QUADROS, MS = 20, 100  # 2 s a 10 fps (30 quadros passava de 500 KB)


def limpar(im: Image.Image) -> Image.Image:
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    opaco = (al > 250).astype(np.uint8)
    # cor da borda = cor do pixel opaco mais proximo (tira a franja)
    _, rotulos = cv2.distanceTransformWithLabels(1 - opaco, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(opaco)
    if len(ys):
        idx = np.zeros(rotulos.max() + 1, np.int64)
        lab_op = rotulos[ys, xs]
        idx[lab_op] = np.arange(len(ys))
        borda = (al > 0) & (al <= 250)
        viz = idx[rotulos[borda]]
        rgb[borda] = rgb[ys[viz], xs[viz]]
    al = cv2.erode(al, np.ones((3, 3), np.uint8))
    al[al < 12] = 0
    out = np.dstack([rgb, al]).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(out, "RGBA")
    return im.crop(im.getbbox())


def encaixar(im: Image.Image, folga: float = 1.0) -> Image.Image:
    """Centraliza no quadrado 512 com margem (folga<1 deixa espaco para o balanco)."""
    m = (LADO - 2 * MARGEM) * folga
    k = min(m / im.width, m / im.height)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    tela = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    tela.alpha_composite(im, ((LADO - im.width) // 2, (LADO - im.height) // 2))
    return tela


def quadros(base: Image.Image) -> list[Image.Image]:
    """Balao flutuando: pivo na ponta de baixo (cordinha), sobe/desce e balanca."""
    out = []
    bb = base.getbbox()
    pivo = ((bb[0] + bb[2]) / 2, bb[3])
    for i in range(QUADROS):
        t = i / QUADROS
        ang = 4 * np.sin(2 * np.pi * t)
        dy = -14 * np.sin(2 * np.pi * t + np.pi / 2) / 2 - 7 * np.sin(4 * np.pi * t) / 2
        im = base.rotate(ang, resample=Image.BICUBIC, center=pivo)
        tela = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
        tela.alpha_composite(im, (0, int(round(dy))))
        out.append(tela)
    return out


def salvar_webp_anim(fr: list[Image.Image], destino: Path, limite: int = 500_000) -> int:
    for q in (80, 65, 50, 40, 30, 20):
        fr[0].save(destino, "WEBP", save_all=True, append_images=fr[1:], duration=MS, loop=0,
                   quality=q, alpha_quality=60, method=1, lossless=False)
        if destino.stat().st_size <= limite:
            return q
    return q


def salvar_webp(im: Image.Image, destino: Path, limite: int = 100_000) -> int:
    for q in (95, 90, 85, 80, 70, 60, 50):
        im.save(destino, "WEBP", quality=q, method=3)
        if destino.stat().st_size <= limite:
            return q
    return q


def main() -> None:
    fonte, saida = Path(sys.argv[1]), Path(sys.argv[2])
    icone = sys.argv[3] if len(sys.argv) > 3 else None
    saida.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(p for p in fonte.iterdir() if p.suffix.lower() in (".png", ".webp"))
    for p in arquivos:
        limpo = limpar(Image.open(p))
        parado = encaixar(limpo)
        q1 = salvar_webp(parado, saida / f"{p.stem}.webp")
        fr = quadros(encaixar(limpo, folga=0.9))
        q2 = salvar_webp_anim(fr, saida / f"{p.stem}_anim.webp")
        fr[0].save(saida / f"{p.stem}.gif", save_all=True, append_images=fr[1:], duration=MS, loop=0,
                   disposal=2, transparency=0, optimize=True)
        print(f"{p.stem}: parada {(saida / f'{p.stem}.webp').stat().st_size // 1024} KB (q{q1}), "
              f"animada {(saida / f'{p.stem}_anim.webp').stat().st_size // 1024} KB (q{q2})")
    alvo = next((p for p in arquivos if p.stem == icone), arquivos[0])
    b = limpar(Image.open(alvo))
    b.thumbnail((88, 88), Image.LANCZOS)
    tela = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    tela.alpha_composite(b, ((96 - b.width) // 2, (96 - b.height) // 2))
    tela.save(saida / "bandeja.png", optimize=True)
    print("bandeja.png", (saida / "bandeja.png").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
