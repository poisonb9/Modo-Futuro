"""Cartao do WhatsApp da INAUGURACAO (og:image 1200x630), 24/09/2026.

Cena: foto gerada pelo dono (parede clara, luz de janela, baloes da serie)
em Desktop/inauguracao/og_cena_parede.png. Por cima, nitido e nosso: o varal
de letras-balao "INAUGURACAO" do topo do site, o slogan e o dominio.
Uso:  python -X utf8 ferramentas/og_inauguracao.py  -> paginas/og_inauguracao.png
"""
import math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_og import fonte, RAIZ

CENA = Path(r"C:/Users/Administrator/Desktop/inauguracao/og_cena_parede.png")
W, H = 1200, 630


def main() -> Path:
    cena = Image.open(CENA).convert("RGBA")
    s = max(W / cena.width, H / cena.height)
    cena = cena.resize((round(cena.width * s), round(cena.height * s)), Image.LANCZOS)
    x0, y0 = (cena.width - W) // 2, (cena.height - H) // 2
    im = cena.crop((x0, y0, x0 + W, y0 + H))
    # varal: 11 letras em arco suave, como no topo do site
    n, larg, passo = 11, 50, 58
    xi = (W - passo * (n - 1)) / 2
    fio = ImageDraw.Draw(im)
    pts = [(xi + passo * i, 58 + 26 * math.sin(math.pi * i / (n - 1))) for i in range(n)]
    fio.line([(xi - 40, 40)] + pts + [(xi + passo * (n - 1) + 40, 40)], fill=(150, 130, 90), width=2)
    for i, (x, y) in enumerate(pts):
        L = Image.open(RAIZ / "paginas" / "baloes" / ("letra_%02d.webp" % (i + 1))).convert("RGBA")
        L = L.resize((larg, round(L.height * larg / L.width)), Image.LANCZOS)
        L = L.rotate((i - 5) * -2.2, resample=Image.BICUBIC, expand=True)
        sh = Image.new("RGBA", L.size, (70, 50, 10, 0)); sh.putalpha(L.getchannel("A").point(lambda v: v * 60 // 255))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (round(x - L.width / 2 + 4), round(y + 8)))
        im.alpha_composite(L, (round(x - L.width / 2), round(y)))
    # ⭐ 24/09, pelo acervo (miniatura no celular: 2-3 elementos, reduzir a
    # 25% e conferir; o TITULO do chat complementa, nao repete): sem texto
    # digitado -- varal, logo e baloes. O slogan vem no titulo do WhatsApp.
    lado = 250
    logo = Image.open(RAIZ / "paginas" / "logo_achadinho_mestre.png").convert("RGBA").resize((lado, lado), Image.LANCZOS)
    lx, ly = (W - lado) // 2, 205
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((lx + 18, ly + 30, lx + lado + 18, ly + lado + 30), fill=(90, 65, 20, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    im.alpha_composite(logo, (lx, ly))
    saida = RAIZ / "paginas" / "og_inauguracao.png"
    im.convert("RGB").save(saida, optimize=True)
    return saida


if __name__ == "__main__":
    print(main())
