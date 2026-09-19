"""Gera a imagem de compartilhamento (og:image, 1200x630) do Achadinho Total.

Bryan, 19/09/2026: "quando mandei o link pra minha namorada, olha como ficou
feio" — o iMessage recortava o icone quadrado e escrevia so' a descricao.
Esta imagem e' o CARTAO DE VISITA no chat: luz dourada, a lupa, o slogan e
o dominio, no formato que iMessage/WhatsApp/Telegram mostram inteiro.

Uso:  python -X utf8 ferramentas/gerar_og.py   -> paginas/og_achadinho.png
Fontes: baixa Archivo Black e Poppins do repo google/fonts se nao existirem.
"""
from __future__ import annotations
import os, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
FONTES = Path(os.environ.get("TEMP", "/tmp")) / "fontes"
URLS = {
    "ArchivoBlack.ttf": "https://github.com/google/fonts/raw/main/ofl/archivoblack/ArchivoBlack-Regular.ttf",
    "Poppins-Medium.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Medium.ttf",
}


def fonte(nome: str, tam: int) -> ImageFont.FreeTypeFont:
    FONTES.mkdir(parents=True, exist_ok=True)
    f = FONTES / nome
    if not f.exists() or f.stat().st_size < 1000:
        urllib.request.urlretrieve(URLS[nome], f)
    return ImageFont.truetype(str(f), tam)


def luz(w: int, h: int, escuro: bool) -> Image.Image:
    """Fundo com as duas luzes douradas (a mesma .luz do site), desfocadas."""
    base = (23, 19, 13) if escuro else (250, 249, 252)
    im = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(im)
    ouro, creme = (242, 201, 76), (255, 236, 190)
    d.ellipse((-200, -260, 620, 420), fill=ouro)
    d.ellipse((760, 120, 1500, 700), fill=creme)
    im = im.filter(ImageFilter.GaussianBlur(160))
    return Image.blend(Image.new("RGB", (w, h), base), im, 0.75 if escuro else 0.55)


def gerar(escuro: bool = False) -> Path:
    W, H = 1200, 630
    im = luz(W, H, escuro).convert("RGBA")
    logo = Image.open(RAIZ / "paginas" / "logo_achadinho_mestre.png").convert("RGBA")
    logo = logo.resize((330, 330), Image.LANCZOS)
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).ellipse((100, 210, 430, 540), fill=(120, 80, 0, 110))
    sombra = sombra.filter(ImageFilter.GaussianBlur(40))
    im.alpha_composite(sombra)
    im.alpha_composite(logo, (100, 150))
    d = ImageDraw.Draw(im)
    tinta = (244, 242, 249) if escuro else (22, 21, 28)
    fraco = (165, 161, 180) if escuro else (111, 107, 125)
    ouro = (240, 182, 46) if escuro else (200, 144, 26)
    x = 480
    d.text((x, 150), "ACHADINHO TOTAL", font=fonte("Poppins-Medium.ttf", 26), fill=fraco, spacing=4)
    f1 = fonte("ArchivoBlack.ttf", 66)
    d.text((x, 196), "Eu garimpo.", font=f1, fill=tinta)
    d.text((x, 276), "Você ", font=f1, fill=tinta)
    dx = d.textlength("Você ", font=f1)
    d.text((x + dx, 276), "paga menos.", font=f1, fill=ouro)
    f2 = fonte("Poppins-Medium.ttf", 30)
    d.text((x, 392), "Preço conferido de hora em hora.", font=f2, fill=tinta)
    d.text((x, 434), "Queda medida contra o que eu vi, não contra a loja.", font=fonte("Poppins-Medium.ttf", 23), fill=fraco)
    d.text((x, 530), "achadinhototal.com.br", font=fonte("Poppins-Medium.ttf", 28), fill=ouro)
    saida = RAIZ / "paginas" / ("og_achadinho_escuro.png" if escuro else "og_achadinho.png")
    im.convert("RGB").save(saida, optimize=True)
    return saida


if __name__ == "__main__":
    for e in (False, True):
        p = gerar(e)
        print(p, p.stat().st_size // 1024, "KB")
