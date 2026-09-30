# -*- coding: utf-8 -*-
"""Teaser "INAUGURACAO AMANHA, 8H" — um por perfil de oferta.

30/09/2026 (dono: "gostei demais!!! comeca amanha, deixa tudo pronto hoje").
Dia 0 da semana de inauguracao: so' baloes e o convite, SEM produto e SEM
preco — nada a provar, nada inventado. A mesma festa do site e dos e-mails:
as letras-balao "INAUGURACAO" (paginas/baloes/letra_01..11), o balao do
perfil no centro, os lanca-confetes e a voz clonada do dono.

    python ferramentas/teaser_inauguracao.py --canal fatura.chora --saida x.mp4
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import video_oferta as vo  # noqa: E402

DUR = 12.0
ROTEIRO = [("Amanhã, às oito da manhã, a gente inaugura!", "+14%", 0.30),
           ("Todo dia um achado... com o preço conferido de verdade.", "+4%", 0.35),
           ("Segue o perfil pra não perder!", "+12%", 0.0)]


def quadro_teaser(t: float, marca: str, fundo: Image.Image) -> Image.Image:
    im = fundo.copy()
    dr = ImageDraw.Draw(im)
    topo = vo.SEG_TOPO
    vo.centro(dr, topo, marca, vo._caber(dr, marca, "Poppins-Bold.ttf", 40, vo.SEG_LARG), vo.OURO)
    # as 11 letras-balao sobem uma a uma e formam o arco "INAUGURACAO"
    n, larg = 11, vo.SEG_LARG + 20
    for i in range(n):
        chega = vo.ease((t - 0.15 * i) / 0.7)
        if chega <= 0:
            continue
        x = (vo.W - larg) / 2 + larg * (i + 0.5) / n
        y_fim = topo + 190 - 60 * math.sin(math.pi * (i + 0.5) / n) + 6 * math.sin(t * 2 + i)
        y = y_fim + (vo.SEG_BASE - y_fim) * (1 - chega)
        vo._colar(im, vo._balao(f"letra_{i + 1:02d}", 120), x, y, 4 * math.sin(t * 1.6 + i))
    # o balao do perfil, grande, no centro
    bal = vo.BALAO_DO_CANAL.get(marca, "inaug_lupa")
    e = vo.ease((t - 1.4) / 0.8)
    if e > 0:
        vo._colar(im, vo._balao(bal, 430), vo.W / 2, 820 + 40 * (1 - e) + 10 * math.sin(t * 1.8),
                  4 * math.sin(t * 1.2), e)
    vo._colar(im, vo._balao("inaug_estrela", 130), 95, 700 + 10 * math.sin(t * 1.7), 6 * math.sin(t * 1.3))
    vo._colar(im, vo._balao("inaug_laco", 100), 100, 960 + 8 * math.sin(t * 1.4 + 1), 5 * math.sin(t * 1.1))
    vo._colar(im, vo._balao("inaug_presente", 120), 96, 1180 + 8 * math.sin(t * 1.5 + 2), 4 * math.sin(t * 1.2))
    dr = ImageDraw.Draw(im)
    # o convite
    if t >= 2.6:
        e = vo.ease((t - 2.6) / 0.5)
        y = int(1090 + 30 * (1 - e))
        vo.pilula(dr, vo.W / 2 - 300, y, vo.W / 2 + 300, y + 150, vo.OURO)
        vo.centro(dr, y + 8, "AMANHÃ · 8H", vo.fonte("Anton-Regular.ttf", 110), vo.FUNDO)
    if t >= 4.2:
        f = vo.fonte("Poppins-Bold.ttf", 34)
        vo.centro(dr, 1270, "todo dia um achado com", f, vo.BRANCO)
        vo.centro(dr, 1316, "preço conferido de verdade", f, vo.BRANCO)
    vo._confete(im, t - 2.6, 26, vo.W / 2, 960)
    vo._confete(im, t - 7.5, 75, vo.W / 2, 960)
    return im


def gerar(canal: str, saida: Path) -> None:
    marca = vo.MARCAS[canal]
    tmp = Path(tempfile.mkdtemp())
    voz = tmp / "voz.mp3"
    vo.narracao({"partes": ROTEIRO, "ref": 0, "agora": 0, "nome": "", "dias": 0}, voz)
    fundo = vo.base_fundo()
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{vo.W}x{vo.H}", "-r", str(vo.FPS), "-i", "-", "-i", str(voz),
                          "-filter_complex", "[1:a]adelay=500|500,apad[a]", "-map", "0:v", "-map", "[a]",
                          "-t", str(DUR), "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                          "-movflags", "+faststart", str(saida)], stdin=subprocess.PIPE)
    for i in range(int(DUR * vo.FPS)):
        p.stdin.write(quadro_teaser(i / vo.FPS, marca, fundo).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    gerar(a.canal, Path(a.saida))
