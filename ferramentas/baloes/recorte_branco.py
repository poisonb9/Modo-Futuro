# Recorta balao de fundo BRANCO (presente, apaixonado, setas -- 24/09): o
# fundo e' o branco LIGADO A BORDA (flood fill), nao todo branco -- o brilho
# do metal fica. ⛔ A FITA e' branca e o flood fill comia ela (fio saiu
# picotado no ar, print do Bryan): abaixo do corpo do balao, numa faixa
# estreita em volta do fio, o alfa vem da distancia do branco.
import sys, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
def recorta(src, dst, largura):
    im = Image.open(src).convert('RGB'); o = np.asarray(im).astype(float)
    dist = 255 - o.min(axis=2)
    claro = dist < 18
    rot, _ = ndimage.label(claro)
    borda = set(np.unique(np.r_[rot[0], rot[-1], rot[:, 0], rot[:, -1]])) - {0}
    fundo = np.isin(rot, list(borda))
    perto = ndimage.binary_dilation(fundo, iterations=3) & ~fundo
    alfa = np.where(fundo, 0, 255).astype(float)
    alfa[perto] = np.clip(dist[perto] * 6, 0, 255)
    # fio: linhas abaixo do corpo (corpo = linha com >15% da largura maxima)
    m = dist > 30; larg = m.sum(1); corpo = np.nonzero(larg > .15 * larg.max())[0]
    base = corpo.max() + 2
    abaixo = m[base:]
    if abaixo.any():
        cx = int(np.median(np.nonzero(abaixo)[1])); lb = int(.06 * o.shape[1])
        a0, a1 = max(0, cx - lb), cx + lb
        fio = np.clip((dist[base:, a0:a1] - 3) * 10, 0, 255)
        alfa[base:, a0:a1] = np.maximum(alfa[base:, a0:a1] * 0, fio)
        alfa[base:, :a0] = 0; alfa[base:, a1:] = 0
    a = Image.fromarray(alfa.astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))
    rgb = Image.fromarray(np.clip(o * .92, 0, 255).astype(np.uint8)) if False else im
    rgba = rgb.convert('RGBA'); rgba.putalpha(a)
    rgba = rgba.crop(rgba.getbbox())
    h = round(rgba.height * largura / rgba.width)
    rgba.resize((largura, h), Image.LANCZOS).save(dst, 'WEBP', quality=90, method=6)
    print(dst, (largura, h))
recorta(sys.argv[1], sys.argv[2], int(sys.argv[3]))
