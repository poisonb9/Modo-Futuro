# -*- coding: utf-8 -*-
"""Elementos fixos sobrepostos a' fonte (marca d'agua): acha e borra.

    python -m engine.marca --video fonte.mp4 [--aplicar saida.mp4]

Detecta pelo que NAO se mexe: borda que aparece no mesmo pixel em quase todos
os quadros amostrados, enquanto o resto do video muda. Legenda queimada muda
a cada frase e nao passa. Falha aberta: sem certeza, nao mexe.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

AMOSTRAS = 30
LARG = 480                 # analise em baixa resolucao (rapido)
PERSISTE = 0.85            # borda presente em >= 85% dos quadros
AREA_MIN, AREA_MAX = 0.0004, 0.06   # fracao da tela
MARGEM = 0.35              # so' considera o que esta' nas bordas da tela


def _duracao(video: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def _quadros(video: Path) -> list[np.ndarray]:
    dur = _duracao(video)
    if dur <= 0:
        return []
    fps = AMOSTRAS / dur
    bruto = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vf",
         f"fps={fps:.5f},scale={LARG}:-2,format=gray", "-f", "rawvideo", "-"],
        capture_output=True).stdout
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0",
                        str(video)], capture_output=True, text=True)
    w, h = (int(v) for v in r.stdout.strip().split(",")[:2])
    alt = int(round(h * LARG / w / 2) * 2)
    tam = LARG * alt
    return [np.frombuffer(bruto[i:i + tam], np.uint8).reshape(alt, LARG)
            for i in range(0, len(bruto) - tam + 1, tam)]


def detectar(video: Path) -> list[dict]:
    """Caixas {x,y,w,h} em FRACAO da tela (0-1). Lista vazia = nada seguro."""
    from scipy import ndimage
    qs = _quadros(Path(video))
    if len(qs) < 10:
        return []
    bordas = [np.asarray(Image.fromarray(q).filter(ImageFilter.FIND_EDGES)) > 40
              for q in qs]
    freq = np.mean(bordas, axis=0)
    fixo = freq >= PERSISTE
    # conteudo que nao muda NADA (tela congelada/letterbox) nao conta
    var = np.std(np.stack(qs).astype(float), axis=0)
    fixo &= var < 25
    fixo = ndimage.binary_dilation(fixo, iterations=4)
    rot, n = ndimage.label(fixo)
    alt, larg = fixo.shape
    caixas = []
    for fatia in ndimage.find_objects(rot):
        y0, y1 = fatia[0].start, fatia[0].stop
        x0, x1 = fatia[1].start, fatia[1].stop
        area = (y1 - y0) * (x1 - x0) / (alt * larg)
        if not AREA_MIN <= area <= AREA_MAX:
            continue
        cx, cy = (x0 + x1) / 2 / larg, (y0 + y1) / 2 / alt
        if MARGEM < cx < 1 - MARGEM and MARGEM < cy < 1 - MARGEM:
            continue   # centro da tela: e' conteudo, nao marca
        caixas.append({"x": round(x0 / larg, 4), "y": round(y0 / alt, 4),
                       "w": round((x1 - x0) / larg, 4), "h": round((y1 - y0) / alt, 4)})
    return caixas


FAIXA_BAIXA = 0.25         # procura a legenda estrangeira no quarto de baixo
FAIXA_FREQ = 0.035         # linha com texto em >= 3,5% (medido: coreana 5-13%, fundo ~1%)


def faixa_legenda(video: Path) -> dict | None:
    """A faixa de LEGENDA QUEIMADA da fonte (texto que muda, mas sempre na
    mesma altura), em fracao da tela. None se nao houver com seguranca.

    ⭐ 25/09/2026: o "SABAE 🌹" nao e' logo fixo — e' a etiqueta de quem fala,
    junto da legenda coreana na base. Detector de "coisa parada" nao pega."""
    qs = _quadros(Path(video))
    if len(qs) < 10:
        return None
    bordas = np.mean([np.asarray(Image.fromarray(q).filter(ImageFilter.FIND_EDGES)) > 40
                      for q in qs], axis=0)
    alt = bordas.shape[0]
    ini = int(alt * (1 - FAIXA_BAIXA))
    por_linha = bordas[ini:].mean(axis=1)
    linhas = np.nonzero(por_linha >= FAIXA_FREQ)[0]
    if len(linhas) < 3:
        return None
    y0, y1 = (ini + linhas.min()) / alt, (ini + linhas.max() + 1) / alt
    if y1 - y0 > 0.2:
        return None            # alto demais pra ser legenda: e' conteudo
    m = 0.012
    return {"x": 0.0, "y": round(max(0, y0 - m), 4), "w": 1.0,
            "h": round(min(1, y1 + m) - max(0, y0 - m), 4)}


def filtro_faixa(f: dict, w: int, h: int) -> str:
    """Borra a faixa inteira (boxblur forte so' naquele retangulo)."""
    y, fh = int(f["y"] * h), max(8, int(f["h"] * h))
    return (f"split[a][b];[b]crop={w}:{fh}:0:{y},boxblur=18:2[z];"
            f"[a][z]overlay=0:{y}")


def filtro(caixas: list[dict], w: int, h: int) -> str:
    """Cadeia `delogo` do ffmpeg para as caixas, em pixels do video."""
    partes = []
    for c in caixas:
        x, y = max(1, int(c["x"] * w)), max(1, int(c["y"] * h))
        cw = min(int(c["w"] * w) + 4, w - x - 1)
        ch = min(int(c["h"] * h) + 4, h - y - 1)
        if cw > 4 and ch > 4:
            partes.append(f"delogo=x={x}:y={y}:w={cw}:h={ch}")
    return ",".join(partes)


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--video", type=Path, required=True)
    a.add_argument("--aplicar", type=Path)
    o = a.parse_args()
    cx = detectar(o.video)
    print(json.dumps(cx, ensure_ascii=False))
    if o.aplicar and cx:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0",
                            str(o.video)], capture_output=True, text=True)
        w, h = (int(v) for v in r.stdout.strip().split(",")[:2])
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(o.video), "-vf",
                        filtro(cx, w, h), "-c:a", "copy", str(o.aplicar)], check=True)
        print("->", o.aplicar)


if __name__ == "__main__":
    main()


def limpar_no_lugar(video: Path) -> dict | None:
    """Borra a faixa de legenda estrangeira do 9:16 pronto. Devolve a faixa
    borrada (pra registro) ou None. Falha ABERTA: erro = video intacto."""
    video = Path(video)
    try:
        f = faixa_legenda(video)
        if not f:
            return None
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0",
                            str(video)], capture_output=True, text=True)
        w, h = (int(v) for v in r.stdout.strip().split(",")[:2])
        novo = video.with_name(video.stem + "_m.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video),
                        "-filter_complex", filtro_faixa(f, w, h),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-c:a", "copy", "-movflags", "+faststart", str(novo)],
                       check=True, capture_output=True)
        video.unlink()
        novo.rename(video)
        return {k: float(v) for k, v in f.items()}
    except Exception as e:
        print(f"      [!] limpeza da base falhou ({type(e).__name__}) — video intacto")
        return None
