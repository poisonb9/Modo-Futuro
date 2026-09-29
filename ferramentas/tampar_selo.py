# -*- coding: utf-8 -*-
"""TAMPA o selo "NOME · PARTE N" errado de um clipe JA' CORTADO com o certo.

    python -X utf8 ferramentas/tampar_selo.py --video in.mp4 --antigo "CORAGEM · PARTE 10" \
        --novo "CORAGEM · PARTE 2" --saida out.mp4

⛔ 29/09/2026: os cortes do Geracao 2000 sairam com PARTE errada (o contador
somava tiktok+reels e seguia a nota — ver main.py `_ordem_no_video`). Para nao
recortar tudo (2 h por video), a pilula nova vai POR CIMA da antiga:
  - nunca menor que a antiga (+ margem), mesma posicao e mesmo centro;
  - entra 0,3 s ANTES e sai 0,3 s DEPOIS da antiga, opaca durante toda a
    janela dela — a antiga nao aparece nem no fade.
Dono decide olhando o resultado; se nao ficar bom, recorta.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import selo  # noqa: E402

MARGEM = 6   # px de sobra em cada lado (borda antisserrilhada da antiga)


def _pilula_larga(texto: str, largura_video: int, w: int) -> Image.Image:
    """A mesma pilula do engine/selo.py, mas com largura fixa `w` (texto centrado)."""
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype(str(selo.FONTE), max(24, largura_video // 26))
    tw = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(texto, font=f)
    alt = int(f.size * 1.9)
    im = Image.new("RGBA", (w, alt), (0, 0, 0, 0))
    grad = Image.new("RGBA", (w, alt))
    gd = ImageDraw.Draw(grad)
    for x in range(w):
        k = x / max(w - 1, 1)
        gd.line([(x, 0), (x, alt)], fill=tuple(int(selo.OURO_A[i] + (selo.OURO_B[i] - selo.OURO_A[i]) * k) for i in range(3)) + (255,))
    mask = Image.new("L", (w, alt), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, alt - 1], alt // 2, fill=255)
    im.paste(grad, (0, 0), mask)
    ImageDraw.Draw(im).text(((w - tw) / 2, (alt - f.size * 1.25) / 2), texto, font=f, fill=selo.TINTA)
    return im


def pilula_que_cobre(antigo: str, novo: str, w: int) -> tuple[Image.Image, int]:
    """(imagem, deslocamento x) — a nova com largura >= a antiga + margem."""
    a = selo.imagem(antigo, w)
    n = selo.imagem(novo, w)
    alvo_w = max(a.width, n.width) + 2 * MARGEM   # mesma fonte = mesma altura
    if n.width < alvo_w:
        n = _pilula_larga(novo, w, alvo_w)
    # a antiga comeca em x0; centro alinhado pelo lado esquerdo menos a margem
    return n, -MARGEM


def tampar(video: Path, antigo: str, novo: str, saida: Path) -> None:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0",
                        str(video)], capture_output=True, text=True, check=True)
    w, h = (int(v) for v in r.stdout.strip().split(",")[:2])
    im, dx = pilula_que_cobre(antigo, novo, w)
    png = Path(tempfile.mkdtemp()) / "tampa.png"
    im.save(png)
    x, y = int(w * 0.06) + dx, int(h * selo.TOPO_FRAC)
    ini, fim = selo.INI_S - 0.2, selo.FIM_S + 0.3
    filtro = (f"[1:v]format=rgba,fade=t=in:st={ini}:d=0.2:alpha=1,"
              f"fade=t=out:st={fim - 0.3}:d=0.3:alpha=1[s];"
              f"[0:v][s]overlay={x}:{y}:enable='between(t,{ini},{fim})'[v]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-loop", "1",
                    "-t", str(fim + 0.5), "-i", str(png), "-filter_complex", filtro,
                    "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset",
                    "veryfast", "-crf", "18", "-c:a", "copy", "-movflags",
                    "+faststart", str(saida)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=Path, required=True)
    ap.add_argument("--antigo", required=True)
    ap.add_argument("--novo", required=True)
    ap.add_argument("--saida", type=Path, required=True)
    a = ap.parse_args()
    tampar(a.video, a.antigo, a.novo, a.saida)
    print(f"ok -> {a.saida}")


if __name__ == "__main__":
    main()
