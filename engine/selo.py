# -*- coding: utf-8 -*-
"""Selo de continuidade no 9:16: "NOME · PARTE N" quando o tema se repete.

    python -m engine.selo --video c.mp4 --nome Wonhee --parte 2
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
FONTE = Path(__file__).resolve().parent / "fontes" / "Poppins-Bold.ttf"
INI_S, FIM_S = 2.2, 5.0
# 0.085 -> 0.13 em 28/09 (dono, print do Microsoft Parte 8): a barra de
# pesquisa do TikTok (~5-10% da altura) cobria a pilula. 0.13 = 250 px de
# 1920, logo abaixo dela. Nao colide com o titulo (0.16): ele sai aos 2,0 s
# e a pilula so' entra aos 2,2 s (INI_S).
TOPO_FRAC = 0.13
OURO_A, OURO_B = (0xF2, 0xC9, 0x4C), (0xC8, 0x90, 0x1A)
TINTA = (0x16, 0x15, 0x1C)


def parte_do_tema(canal: str, nome: str, usados: dict | None = None) -> int:
    """Quantos clipes do canal ja' falaram deste nome, +1.

    ⛔ 27/09/2026 (dono, prints: "ta' ficando tudo PARTE 3"). Contava pelo
    `desempenho.jsonl`, que NAO e' atualizado a cada corte: todos os clipes de
    um mesmo corte (e dos cortes seguintes) recebiam o MESMO numero. Agora
    conta pelo `registro_clipes.json` (commitado depois de cada corte) e soma
    dentro do proprio corte via `usados` (o 1o e' N, o 2o N+1...).
    """
    if not nome:
        return 1
    chave = nome.lower().replace(" ", "")
    n = 0
    arq = RAIZ / "registro_clipes.json"
    try:
        reg = json.loads(arq.read_text(encoding="utf-8")).get("clipes") or {}
    except (OSError, ValueError):
        reg = {}
    for v in reg.values():
        # so' o MESMO canal: "coragem" num titulo motivacional do Sem
        # Anestesia nao e' parte da serie do Coragem no Geracao 2000
        if canal and v.get("canal") and v.get("canal") != canal:
            continue
        if chave in str(v.get("titulo") or "").lower().replace(" ", ""):
            n += 1
    if usados is not None:
        n = max(n, usados.get(chave, 0))
        usados[chave] = n + 1
    return n + 1


def nome_da_tag(tag: str, titulo: str = "") -> str:
    """Nome curto do tema pra pilula a partir da 1a tag.

    ⛔ 28/09 (previa do Coragem): a tag vem GRUDADA ("coragemocaocovarde") e a
    pilula saiu "CORAGEMOCAOCOVARDE · PARTE 2". Tag longa sem espaco: usa a
    palavra do TITULO que comeca a tag ("Coragem"). Sem casar, a tag como veio.
    """
    import unicodedata

    def _n(s):
        s = unicodedata.normalize("NFKD", s.lower())
        return "".join(c for c in s if c.isalnum())

    tag = str(tag or "").strip()
    if len(tag) <= 12 or " " in tag:
        return tag.title()
    t = _n(tag)
    for w in sorted(str(titulo or "").split(), key=len, reverse=True):
        wn = _n(w)
        if len(wn) >= 3 and t.startswith(wn):
            return w.strip(",.!?:;").title()
    return tag.title()


def imagem(texto: str, largura: int) -> Image.Image:
    f = ImageFont.truetype(str(FONTE), max(24, largura // 26))
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = d0.textlength(texto, font=f)
    alt = int(f.size * 1.9)
    w = int(tw + alt * 1.1)
    im = Image.new("RGBA", (w, alt), (0, 0, 0, 0))
    grad = Image.new("RGBA", (w, alt))
    gd = ImageDraw.Draw(grad)
    for x in range(w):
        k = x / max(w - 1, 1)
        gd.line([(x, 0), (x, alt)], fill=tuple(int(OURO_A[i] + (OURO_B[i] - OURO_A[i]) * k) for i in range(3)) + (255,))
    mask = Image.new("L", (w, alt), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, alt - 1], alt // 2, fill=255)
    im.paste(grad, (0, 0), mask)
    ImageDraw.Draw(im).text(((w - tw) / 2, (alt - f.size * 1.25) / 2), texto, font=f, fill=TINTA)
    return im


# ⭐ 28/09/2026 (dono, Achadinho Chef): na cozinha o selo do topo e' a PROVA
# do diferencial, nao serie ("FRANGO · PARTE 3" numa receita nao diz nada).
TEXTO_COZINHA = "MEDIDAS EM GRAMA E °C"
CANAIS_SELO_MEDIDAS = {"cozinha.importada"}


def aplicar_no_lugar(video: Path, nome: str, parte: int) -> bool:
    """Sobrepoe o selo "NOME · PARTE N" entre INI_S e FIM_S. Falha aberta."""
    if parte < 2 or not nome:
        return False
    return aplicar_texto_no_lugar(video, f"{nome.upper()} · PARTE {parte}")


def aplicar_texto_no_lugar(video: Path, texto: str) -> bool:
    """Sobrepoe uma pilula com `texto` entre INI_S e FIM_S. Falha aberta."""
    video = Path(video)
    if not texto:
        return False
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0",
                            str(video)], capture_output=True, text=True)
        w, h = (int(v) for v in r.stdout.strip().split(",")[:2])
        png = Path(tempfile.mkdtemp()) / "selo.png"
        imagem(texto, w).save(png)
        novo = video.with_name(video.stem + "_s.mp4")
        x, y = int(w * 0.06), int(h * TOPO_FRAC)
        filtro = (f"[1:v]format=rgba,fade=t=in:st={INI_S}:d=0.3:alpha=1,"
                  f"fade=t=out:st={FIM_S - 0.3}:d=0.3:alpha=1[s];"
                  f"[0:v][s]overlay={x}:{y}:enable='between(t,{INI_S},{FIM_S})'[v]")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-loop", "1",
                        "-t", str(FIM_S + 0.5), "-i", str(png), "-filter_complex", filtro,
                        "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset",
                        "veryfast", "-crf", "18", "-c:a", "copy", "-movflags",
                        "+faststart", str(novo)], check=True, capture_output=True)
        video.unlink()
        novo.rename(video)
        return True
    except Exception as e:
        print(f"      [!] selo falhou ({type(e).__name__}) — video sem ele")
        return False


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--video", type=Path, required=True)
    a.add_argument("--nome", required=True)
    a.add_argument("--parte", type=int, required=True)
    o = a.parse_args()
    print(aplicar_no_lugar(o.video, o.nome, o.parte))


if __name__ == "__main__":
    main()
