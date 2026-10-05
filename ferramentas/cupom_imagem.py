# -*- coding: utf-8 -*-
"""Imagem de cupom pronta para post/stories/Telegram — uma por cupom ativo.

⭐ 05/10/2026 (dono): o botão "CUPOM10" do ChatGPT vira MODELO; o código real de
cada cupom (estado/cupons.json, atualizado de hora em hora) é escrito por cima,
no mesmo estilo (pílula creme, borda tracejada dourada, código marrom, "copiar").
Sem IA, sem custo.

    python -X utf8 ferramentas/cupom_imagem.py              # todos os cupons com código
    python -X utf8 ferramentas/cupom_imagem.py STREAMER10   # só um

Saída: midia/cupons_do_dia/<loja>_<codigo>.png (1080 px de largura, fundo transparente)
       + midia/cupons_do_dia/stories_<loja>_<codigo>.png (1080x1920, fundo preto/ouro).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "midia" / "cupons_do_dia"
FONTE_COD = "C:/Windows/Fonts/consolab.ttf"
FONTE_TXT = "C:/Windows/Fonts/seguibl.ttf"

CREME = (255, 246, 225, 255)
OURO = (201, 152, 61, 255)
MARROM = (110, 72, 18, 255)


def _fonte(caminho: str, tam: int):
    try:
        return ImageFont.truetype(caminho, tam)
    except OSError:
        return ImageFont.load_default()


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")[:40]


def pilula(codigo: str, largura: int = 1080) -> Image.Image:
    """O botão tracejado com o código e a etiqueta 'copiar'."""
    esc = 3  # desenha grande e reduz (borda lisa)
    W, H = largura * esc, int(largura * 0.19) * esc
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    m, r = 6 * esc, H // 2 - 6 * esc
    d.rounded_rectangle([m, m, W - m, H - m], radius=r, fill=CREME)
    # borda tracejada: segmentos ao longo do contorno
    passo, traco, larg = 34 * esc, 20 * esc, 7 * esc
    caixa = [m + larg, m + larg, W - m - larg, H - m - larg]
    rr = r - larg
    import math
    pontos = []
    x0, y0, x1, y1 = caixa
    reto = (x1 - x0) - 2 * rr
    perim = 2 * reto + 2 * math.pi * rr
    n = int(perim // passo)
    def ponto(t):
        if t < reto:
            return (x0 + rr + t, y0)
        t -= reto
        if t < math.pi * rr:
            a = -math.pi / 2 + t / rr
            return (x1 - rr + rr * math.cos(a), (y0 + y1) / 2 + rr * math.sin(a))
        t -= math.pi * rr
        if t < reto:
            return (x1 - rr - t, y1)
        t -= reto
        a = math.pi / 2 + t / rr
        return (x0 + rr + rr * math.cos(a), (y0 + y1) / 2 + rr * math.sin(a))
    for i in range(n):
        t0 = i * perim / n
        seg = [ponto(t0 + k * traco / 6) for k in range(7)]
        d.line(seg, fill=OURO, width=larg, joint="curve")
    # etiqueta "copiar"
    ft = _fonte(FONTE_TXT, int(H * 0.2))
    tw = d.textlength("copiar", font=ft)
    ex1 = W - m - int(H * 0.28)
    ex0 = ex1 - tw - int(H * 0.22)
    ey0, ey1 = int(H * 0.3), int(H * 0.7)
    d.rounded_rectangle([ex0, ey0, ex1, ey1], radius=int(H * 0.08), fill=(255, 255, 255, 255))
    d.text(((ex0 + ex1) / 2, (ey0 + ey1) / 2), "copiar", font=ft, fill=MARROM, anchor="mm")
    # codigo: maior que couber
    area = ex0 - (m + int(H * 0.45)) - int(H * 0.15)
    tam = int(H * 0.46)
    while tam > 10:
        fc = _fonte(FONTE_COD, tam)
        if d.textlength(codigo, font=fc) <= area:
            break
        tam -= 4
    d.text((m + int(H * 0.45) + area / 2, H / 2), codigo, font=fc, fill=MARROM, anchor="mm")
    return im.resize((W // esc, H // esc), Image.LANCZOS)


def stories(c: dict) -> Image.Image:
    """1080x1920: fundo preto com brilho dourado, loja, oferta, cupom e validade."""
    W, H = 1080, 1920
    im = Image.new("RGBA", (W, H), (15, 14, 19, 255))
    d = ImageDraw.Draw(im)
    for y in range(H):  # leve brilho dourado no topo
        a = max(0, 1 - y / 900)
        d.line([(0, y), (W, y)], fill=(int(15 + 30 * a), int(14 + 26 * a), int(19 + 6 * a), 255))
    ouro = (243, 215, 122, 255)
    for nome, xy, alt in (("bf_porcento_p", (40, 60), 200), ("bf_etiqueta_p", (W - 230, 90), 190)):
        try:
            b = Image.open(RAIZ / "paginas" / "baloes" / f"{nome}.webp").convert("RGBA")
            b = b.resize((round(b.width * alt / b.height), alt), Image.LANCZOS)
            im.alpha_composite(b, xy)
        except OSError:
            pass
    d.text((W / 2, 300), "CUPOM DE DESCONTO", font=_fonte(FONTE_TXT, 54), fill=ouro, anchor="mm")
    d.text((W / 2, 440), c["loja"][:28].upper(), font=_fonte(FONTE_TXT, 96), fill=(255, 255, 255, 255), anchor="mm")
    # titulo quebrado em linhas
    ft = _fonte(FONTE_TXT, 58)
    palavras, linhas, atual = c["titulo"].split(), [], ""
    for p in palavras:
        t = (atual + " " + p).strip()
        if d.textlength(t, font=ft) > W - 160:
            linhas.append(atual)
            atual = p
        else:
            atual = t
    linhas.append(atual)
    for i, l in enumerate(linhas[:4]):
        d.text((W / 2, 620 + i * 78), l, font=ft, fill=(230, 226, 214, 255), anchor="mm")
    p = pilula(c["codigo"], 940)
    im.alpha_composite(p, ((W - p.width) // 2, 1020))
    if c.get("fim"):
        f = dt.datetime.fromisoformat(c["fim"]).astimezone(dt.timezone(dt.timedelta(hours=-3)))
        d.text((W / 2, 1300), f"válido até {f:%d/%m}", font=_fonte(FONTE_TXT, 50), fill=ouro, anchor="mm")
    d.text((W / 2, 1720), "achadinhototal.com.br/cupons", font=_fonte(FONTE_TXT, 48), fill=(255, 255, 255, 255), anchor="mm")
    return im


def main() -> None:
    cupons = json.loads((RAIZ / "estado" / "cupons.json").read_text(encoding="utf-8"))
    agora = dt.datetime.now(dt.timezone.utc).isoformat()
    vivos = [c for c in cupons if c.get("codigo") and (not c.get("fim") or c["fim"] > agora)]
    if len(sys.argv) > 1:
        vivos = [c for c in vivos if c["codigo"].upper() == sys.argv[1].upper()]
    SAIDA.mkdir(parents=True, exist_ok=True)
    for c in vivos:
        base = f"{_slug(c['loja'])}_{_slug(c['codigo'])}"
        pilula(c["codigo"]).save(SAIDA / f"{base}.png", optimize=True)
        stories(c).convert("RGB").save(SAIDA / f"stories_{base}.png", optimize=True)
    print(f"{len(vivos)} cupom(ns) -> {SAIDA}")


if __name__ == "__main__":
    main()
