"""Card do WhatsApp com a OFERTA DO DIA (og:image 1200x630), 24/09/2026.

Duas camadas (decisao com o dono, pelo acervo de marketing: criativo
estatico = foto do produto + oferta em texto grande; numero especifico):
  1. CENA fixa gerada por IA: Desktop/inauguracao/og_cena_oferta.png
     (buque da lupa a` esquerda, etiqueta-balao EM BRANCO e pedestal a` direita)
  2. ESTE script, a cada publicacao: produto da capa recortado no pedestal,
     queda e preco escritos NA etiqueta, com os numeros do momento.
Uso: python -X utf8 ferramentas/og_oferta.py [id]  -> paginas/og_oferta.png
"""
import io, sys, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_og import fonte, RAIZ

CENA = Path(r"C:/Users/Administrator/Desktop/inauguracao/og_cena_oferta.png")
ETIQ = (1000, 250, 1272, 480)        # area util da frente da etiqueta (px da cena 1728x910)
PEDESTAL = (1237, 700, 330, 215)     # centro x, base y (topo do pedestal), largura e altura maximas


def recorta(url):
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"}), timeout=30).read()
    im = Image.open(io.BytesIO(raw)).convert("RGB"); o = np.asarray(im).astype(float)
    dist = 255 - o.min(axis=2); rot, _ = ndimage.label(dist < 22)
    borda = set(np.unique(np.r_[rot[0], rot[-1], rot[:, 0], rot[:, -1]])) - {0}
    fundo = np.isin(rot, list(borda))
    # ⛔ foto de vendedor traz texto solto ("3500MB/s", logo): fica so' a
    # MAIOR peca -- o produto -- e o resto vira fundo
    pecas, n = ndimage.label(~fundo)
    if n > 1:
        tam = ndimage.sum(np.ones_like(pecas), pecas, range(1, n + 1))
        fundo = pecas != (int(np.argmax(tam)) + 1)
    a = Image.fromarray(np.where(fundo, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))
    r = im.convert("RGBA"); r.putalpha(a)
    return r.crop(r.getbbox())


def num(v):
    return float(str(v).replace("R$", "").replace(".", "").replace(",", ".").strip())


def reais(v):
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def main(p):
    cena = Image.open(CENA).convert("RGBA")
    # produto no pedestal, com sombra de contato
    prod = recorta(p["imagem"])
    cx, base, mw, mh = PEDESTAL
    s = min(mw / prod.width, mh / prod.height); prod = prod.resize((round(prod.width * s), round(prod.height * s)), Image.LANCZOS)
    px, py = cx - prod.width // 2, base - prod.height
    sh = Image.new("RGBA", cena.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - prod.width * .45, base - 10, cx + prod.width * .45, base + 12), fill=(70, 50, 10, 120))
    cena.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    cena.alpha_composite(prod, (px, py))
    # etiqueta: queda grande em vermelho, preco novo, preco antigo riscado
    d = ImageDraw.Draw(cena)
    x0, y0, x1, y1 = ETIQ; cxe = (x0 + x1) / 2
    vermelho, tinta, fraco = (176, 18, 24), (40, 26, 6), (72, 50, 14)

    def centro(txt, y, f, cor, risca=False):
        w = d.textlength(txt, font=f); x = cxe - w / 2
        d.text((x, y), txt, font=f, fill=cor)
        if risca:
            bb = d.textbbox((x, y), txt, font=f); m = (bb[1] + bb[3]) / 2
            d.line((bb[0] - 4, m, bb[2] + 4, m), fill=cor, width=4)
    centro("-" + str(round(p["queda"])) + "%", y0 + 6, fonte("ArchivoBlack.ttf", 84), vermelho)
    preco = num(p["preco"])
    centro("R$ " + f"{preco:.2f}".replace(".", ","), y0 + 118, fonte("ArchivoBlack.ttf", 50), tinta)
    if p.get("antes"):
        centro("era R$ " + f"{num(p['antes']):.2f}".replace(".", ","), y0 + 186, fonte("Poppins-Medium.ttf", 30), fraco, risca=True)
    W, H = 1200, 630
    s = W / cena.width; cena = cena.resize((W, round(cena.height * s)), Image.LANCZOS)
    y = (cena.height - H) // 2; out = cena.crop((0, y, W, y + H)).convert("RGB")
    saida = RAIZ / "paginas" / "og_oferta.png"; out.save(saida, optimize=True)
    return saida


if __name__ == "__main__":
    sys.path[:0] = [str(RAIZ), str(RAIZ / "paginas")]
    import publicar_bio as pb
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    dados = pb.produtos_todos()
    p = next((x for x in dados if (str(x.get("id")) == alvo if alvo else x.get("capa"))), None)
    print(p and p.get("antes"), main(p))
