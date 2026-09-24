"""Refaz as fitas do buque na cena do card do WhatsApp (24/09/2026).

A IA desenhou fitas onduladas e cachos em bloco; balao de gas puxa a fita
TENSA. Aqui: apaga as fitas velhas (inpaint so' no fundo claro, nunca no
balao) e desenha 5 fitas retas, finas, com 2-3 voltas de cacho sob o no.
Uso: python -X utf8 ferramentas/fitas_buque.py ENTRADA SAIDA
"""
import math, sys
import numpy as np, cv2
from PIL import Image, ImageDraw

NOS = [(237, 494), (310, 646), (487, 633), (677, 643), (745, 519)]   # estrela, etiqueta, lupa, sacola, emoji
CAIXA = (487, 734)
VELHAS = [((225, 492), (252, 532)), ((303, 643), (331, 679)), ((478, 636), (502, 679)),
          ((649, 641), (679, 675)), ((731, 517), (756, 552))]
LINHAS = [((325, 673), (447, 750)), ((343, 627), (453, 743)), ((489, 677), (489, 733)),
          ((657, 673), (527, 747)), ((633, 623), (520, 743))]


def main(ent, sai):
    im = cv2.imread(ent)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    fundo = (hsv[:, :, 1] < 60) & (hsv[:, :, 2] > 120)          # parede/chao claro, nao balao
    m = np.zeros(im.shape[:2], np.uint8)
    for a, b in VELHAS:
        cv2.rectangle(m, a, b, 255, -1)
    for a, b in LINHAS:
        cv2.line(m, a, b, 255, 9)
    m = (m > 0) & fundo
    m = cv2.dilate(m.astype(np.uint8) * 255, np.ones((3, 3), np.uint8))
    limpo = cv2.inpaint(im, m, 6, cv2.INPAINT_TELEA)
    base = Image.fromarray(cv2.cvtColor(limpo, cv2.COLOR_BGR2RGB)).convert("RGBA")
    K = 4
    cam = Image.new("RGBA", (base.width * K, base.height * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(cam)
    for i, (x, y) in enumerate(NOS):
        fx = CAIXA[0] + (i - 2) * 3; fy = CAIXA[1]
        # cacho: 3 voltas em 16 px logo abaixo do no, na direcao da fita
        dx, dy = fx - x, fy - y; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = -uy, ux
        pts = []
        for k in range(0, 161):
            t = k / 160 * 20
            amp = 4.2 * (1 - t / 22)
            s = math.sin(t / 20 * 3 * 2 * math.pi) * amp
            pts.append((x + ux * t + nx * s, y + uy * t + ny * s))
        pts += [(fx, fy)]
        P = [(px * K, py * K) for px, py in pts]
        d.line([(a + 3 * K * .3, b + 2 * K * .3) for a, b in P], fill=(120, 110, 100, 55), width=int(3.4 * K))  # sombra
        d.line(P, fill=(168, 168, 176, 255), width=int(3.0 * K))
        d.line([(a - .5 * K, b) for a, b in P], fill=(246, 246, 250, 255), width=int(1.4 * K))  # brilho
    cam = cam.resize(base.size, Image.LANCZOS)
    # fita so' aparece no fundo (passa por TRAS dos baloes)
    a = np.asarray(cam).copy(); a[..., 3] = (a[..., 3] * fundo).astype(np.uint8)
    base.alpha_composite(Image.fromarray(a))
    base.convert("RGB").save(sai)
    print(sai)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
