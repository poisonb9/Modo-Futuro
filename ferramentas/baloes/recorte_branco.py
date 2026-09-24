# Recorta balao de fundo BRANCO (presente, emoji 24/09): o fundo e' o branco
# LIGADO A BORDA (flood fill), nao todo branco -- o brilho do metal fica.
# Borda suave: alfa pela distancia do branco numa faixa de 3 px.
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
    a = Image.fromarray(alfa.astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))
    rgba = im.convert('RGBA'); rgba.putalpha(a)
    rgba = rgba.crop(rgba.getbbox())
    h = round(rgba.height * largura / rgba.width)
    rgba.resize((largura, h), Image.LANCZOS).save(dst, 'WEBP', quality=90, method=6)
    print(dst, (largura, h))
recorta(sys.argv[1], sys.argv[2], int(sys.argv[3]))
