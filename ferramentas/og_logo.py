"""Card do WhatsApp so' com a LOGO, no padrao das grandes marcas (24/09/2026).

O dono comparou com Apple, Microsoft e Enjoei: logo sozinha, fundo branco,
a marca fala por si. Definitivo -- nunca precisa refazer. O fundo branco
segue a regra do site (so' fundo branco).
Uso: python -X utf8 ferramentas/og_logo.py -> paginas/og_logo.png
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
RAIZ = Path(__file__).resolve().parent.parent
W, H, LADO = 1200, 630, 330


def main() -> Path:
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    logo = Image.open(RAIZ / "paginas" / "logo_achadinho_mestre.png").convert("RGBA").resize((LADO, LADO), Image.LANCZOS)
    x, y = (W - LADO) // 2, (H - LADO) // 2 - 6
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((x + 20, y + 40, x + LADO - 20, y + LADO + 26), fill=(120, 90, 20, 70))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    im.alpha_composite(logo, (x, y))
    saida = RAIZ / "paginas" / "og_logo.png"
    im.convert("RGB").save(saida, optimize=True)
    return saida


if __name__ == "__main__":
    print(main())
