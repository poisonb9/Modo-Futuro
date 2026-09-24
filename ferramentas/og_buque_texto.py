"""Card do WhatsApp: buque da lupa (foto) + o texto do card antigo (24/09/2026).

A foto ocupa a esquerda e se dissolve no creme onde mora o texto. Pelo
acervo (miniatura no celular): so' o que le' de longe -- marca, slogan,
uma linha curta e o dominio. Uso: python -X utf8 ferramentas/og_buque_texto.py
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_og import fonte, luz, RAIZ

FOTO = Path(r"C:/Users/Administrator/Desktop/inauguracao/og_buque_lupa.png")
W, H = 1200, 630


def main() -> Path:
    im = luz(W, H, False).convert("RGBA")
    f = Image.open(FOTO).convert("RGBA")
    s = 0.52
    f = f.resize((round(f.width * s), round(f.height * s)), Image.LANCZOS)
    fw, fh = f.size
    # bordas dissolvidas nos 4 lados: a parede da foto vira o creme do card
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    borda = np.minimum.reduce([xx, fw - 1 - xx, yy * 1.6, (fh - 1 - yy) * 3])
    a = np.clip(borda / 110, 0, 1) ** 1.3 * 255
    f.putalpha(Image.fromarray(a.astype(np.uint8)))
    im.alpha_composite(f, (-150 + 18, (H - fh) // 2 + 10))
    d = ImageDraw.Draw(im)
    tinta, fraco, ouro = (22, 21, 28), (111, 107, 125), (192, 136, 20)
    x = 630
    d.text((x, 150), "ACHADINHO TOTAL", font=fonte("Poppins-Medium.ttf", 26), fill=fraco)
    f1 = fonte("ArchivoBlack.ttf", 54)
    d.text((x, 196), "Eu procuro.", font=f1, fill=tinta)
    d.text((x, 264), "Você ", font=f1, fill=tinta)
    d.text((x + d.textlength("Você ", font=f1), 264), "paga menos.", font=f1, fill=ouro)
    d.text((x, 384), "Preço conferido de hora em hora.", font=fonte("Poppins-Medium.ttf", 29), fill=tinta)
    d.text((x, 470), "achadinhototal.com.br", font=fonte("Poppins-Medium.ttf", 29), fill=ouro)
    saida = RAIZ / "paginas" / "og_buque_texto.png"
    im.convert("RGB").save(saida, optimize=True)
    return saida


if __name__ == "__main__":
    print(main())
