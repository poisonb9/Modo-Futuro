# -*- coding: utf-8 -*-
"""Baloes de CTA do TikTok: curtidas, siga e compartilhe (25/09/2026).

    python -X utf8 ferramentas/baloes/cta_tiktok.py --previa [--video X.mp4] [--coracoes 6]
    python -X utf8 ferramentas/baloes/cta_tiktok.py --overlay saida.mov   (alfa, p/ o motor)

A CENA (desenho do Bryan):
  1. CURTIDAS — coracoes nascem do botao de curtir do TikTok e sobem ate' sumir
     no topo. Rajada: N coracoes (3/4/6/8), rapidos e se sobrepondo, com o
     intervalo CRESCENDO (a frequencia vai caindo). Fecha com o coracao TORTO
     (heart3) subindo devagar — o ultimo da sequencia.
  2. SIGA — os dois bonecos com o + branco surgem de forma premium (sobem do
     nada com escala em mola) e ficam ESTACIONADOS em cima do botao de seguir,
     balancando de leve; depois sobem e somem.
  3. COMPARTILHE — a seta surge igual e estaciona em cima do botao de
     compartilhar.

⚠️ POSICOES: a coluna de botoes do TikTok em 1080x1920 fica em x~1000; avatar
(seguir) ~y 880, curtir ~y 1060, compartilhar ~y 1520. Varia um pouco por
aparelho — por isso ficam em POS, num lugar so'. O balao estacionado fica
ACIMA/ao lado do botao, nunca por baixo do icone (o icone e' desenhado por
cima do video e embolaria).
"""
from __future__ import annotations

import argparse
import math
import random
import subprocess
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent / "cta"
JITTER = 22                      # px: raio de onde cada coracao pode nascer
BORDA_DIR = 1000                 # area segura: nada a direita disto
W, H, FPS = 1080, 1920, 30

POS = {
    # ⛔ MEDIDO no print do iPhone (25/09): o TikTok AMPLIA o 9x16 pra cobrir a
    # area acima da barra (924x1805 no iPhone -> x0,940) e corta ~45 px de cada
    # lado. A coluna de botoes cai em x~954 do video, NAO em 1000 (era o erro:
    # os coracoes nasciam a direita do botao).
    # ⭐ 2 e 3 (25/09): SERVIR EM TODOS. Os valores abaixo sao o MEIO entre o
    # iPhone (medido) e o Android 20:9 (estimado: coluna x~900, ~90 px abaixo).
    # E ha' FOLGA: coracao nasce numa area (JITTER), estacionado fica ~130 px ao
    # lado. AREA SEGURA: nada passa de x 1000 (o 20:9 corta ~80 px por lado).
    "curtir": (928, 1100),        # de onde os coracoes nascem
    # ⭐ 25/09 (Bryan): SIGA fica LA' EMBAIXO, pertinho do @perfil (canto
    # inferior esquerdo, onde a pessoa toca pra abrir o perfil e seguir)
    "siga": (250, 1585),          # acima do nome do perfil
    "comente": (795, 1250),       # a esquerda do botao de comentar
    "compartilhe": (795, 1590),   # a esquerda do botao de compartilhar
}


def _img(nome: str, largura: int) -> Image.Image:
    im = Image.open(AQUI / f"{nome}.webp").convert("RGBA")
    return im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)


def _mola(t: float) -> float:
    """0->1 com um passo alem e volta (entrada 'premium')."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 1 - math.exp(-6 * t) * math.cos(9 * t)


def _suave(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Coracao:
    def __init__(self, im, t0, dur, x0, y0, deriva, fase, amp):
        self.im, self.t0, self.dur = im, t0, dur
        self.x0, self.y0, self.deriva, self.fase, self.amp = x0, y0, deriva, fase, amp

    def quadro(self, t):
        u = (t - self.t0) / self.dur
        if u < 0 or u > 1:
            return None
        # nasce pequeno no botao, cresce rapido e sobe acelerando de leve
        esc = 0.15 + 0.85 * _suave(u / 0.2)
        y = self.y0 - (self.y0 + self.im.height) * (u ** 1.15)
        x = self.x0 - self.deriva * u + self.amp * math.sin(self.fase + u * 7)
        ang = 8 * math.sin(self.fase + u * 5)
        alfa = min(1.0, u / 0.08)
        return self.im, x, y, esc, ang, alfa


class Estacionado:
    """VEM DE BAIXO sutilmente, estaciona balancando, e VOLTA pra baixo."""

    def __init__(self, im, t0, fica, x, y):
        self.im, self.t0, self.fica, self.x, self.y = im, t0, fica, x, y

    def quadro(self, t):
        u = t - self.t0
        if u < 0:
            return None
        entra, sai = 0.9, 0.8
        if u > entra + self.fica + sai:
            return None
        esc = 0.85 + 0.15 * _mola(u / entra)
        dy = 420 * (1 - _mola(u / entra))                 # sobe de baixo, com mola leve
        bal = 10 * math.sin(u * 2.4)                       # balanco estacionado
        ang = 4 * math.sin(u * 1.7)
        alfa = min(1.0, u / 0.2)
        fim = u - entra - self.fica
        if fim > 0:                                        # desce e some por baixo
            k = _suave(fim / sai)
            dy += 520 * k
            alfa *= 1 - k
        return self.im, self.x, self.y + dy + bal, esc, ang, alfa


# ⭐ ORDEM (Bryan, 25/09): curtidas -> comente -> compartilhe -> SIGA por
# ultimo e mais tempo na tela (~2 s parado alem da entrada/saida).
def cena(coracoes: int = 6, t_curtir: float = 0.3, t_coment: float = 4.3,
         t_comp: float = 6.9, t_siga: float = 9.5, semente: int = 7) -> list:
    rnd = random.Random(semente)
    base = [_img("heart1", 150), _img("heart2", 150)]   # rajada
    elems = []
    t = t_curtir
    passo = 0.14
    bx, by = POS["curtir"]
    for i in range(coracoes):
        im = base[i % 2].resize((w := rnd.randint(105, 165),
                                 round(base[i % 2].height * w / base[i % 2].width)))
        # FOLGA: nasce num raio pequeno em volta do botao, nao num ponto
        elems.append(Coracao(im, t, rnd.uniform(1.5, 1.9),
                             bx + rnd.uniform(-JITTER, JITTER),
                             by + rnd.uniform(-JITTER, JITTER),
                             rnd.uniform(60, 240), rnd.uniform(0, 6.28),
                             rnd.uniform(12, 30)))
        t += passo
        passo *= 1.35                                      # frequencia caindo
    # ⭐ o ultimo e' o MAIS BONITO (heart2, fita em espiral): maior e devagar.
    # O torto (heart3) saiu por decisao do Bryan em 25/09.
    elems.append(Coracao(_img("heart2", 190), t + 0.25, 3.4, bx, by,
                         110, 1.0, 12))
    # comente: o balao CROMADO (o preto some em video escuro)
    elems.append(Estacionado(_img("cta_comente", 190), t_coment, 1.3,
                             *POS["comente"]))
    elems.append(Estacionado(_img("cta_compartilhe", 200), t_comp, 1.3,
                             *POS["compartilhe"]))
    elems.append(Estacionado(_img("cta_siga", 210), t_siga, 3.4, *POS["siga"]))
    return elems


BOTOES = [("avatar", 954, 878), ("curtir", 954, 1058), ("comentar", 954, 1223),
          ("salvar", 954, 1388), ("compartilhar", 954, 1559)]


def guias(im: Image.Image) -> Image.Image:
    """SO' NA PREVIA: circulos onde ficam os botoes do TikTok, pra conferir."""
    from PIL import ImageDraw
    im = im.copy()
    d = ImageDraw.Draw(im, "RGBA")
    for _, x, y in BOTOES:                            # iPhone 12 (medido): branco
        d.ellipse([x - 42, y - 42, x + 42, y + 42], outline=(255, 255, 255, 170), width=4)
    for _, x, y in BOTOES:                            # Android 20:9 (estimado): amarelo
        x2, y2 = x - 54, y + 90
        d.ellipse([x2 - 42, y2 - 42, x2 + 42, y2 + 42], outline=(255, 214, 0, 170), width=4)
    d.line([(BORDA_DIR, 0), (BORDA_DIR, H)], fill=(255, 80, 80, 90), width=2)
    # o @perfil (nome do canal), canto inferior esquerdo
    d.rounded_rectangle([60, 1640, 420, 1695], 12, outline=(255, 255, 255, 170), width=4)
    return im


def pintar(fundo: Image.Image, elems, t) -> Image.Image:
    tela = fundo.copy()
    for e in elems:
        q = e.quadro(t)
        if not q:
            continue
        im, x, y, esc, ang, alfa = q
        w = max(2, int(im.width * esc))
        h = max(2, int(im.height * esc))
        p = im.resize((w, h), Image.BILINEAR).rotate(ang, Image.BICUBIC, expand=True)
        if alfa < 1:
            a = p.getchannel("A").point(lambda v: int(v * alfa))
            p.putalpha(a)
        # (x, y) = centro do CORPO do balao (terco de cima da imagem)
        x = min(x, BORDA_DIR - p.width / 2)             # area segura (corte do 20:9)
        tela.alpha_composite(p, (int(x - p.width / 2), int(y - p.height * 0.28)))
    return tela


def render(saida: Path, fundo_video: Path | None, coracoes: int, alfa: bool) -> None:
    elems = cena(coracoes)
    dur = 14.8
    n = int(dur * FPS)
    if alfa:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "prores_ks",
               "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(saida)]
        fundo = lambda i: Image.new("RGBA", (W, H), (0, 0, 0, 0))
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
               "-pix_fmt", "yuv420p", "-crf", "20", str(saida)]
        quadros = None
        if fundo_video:
            bruto = subprocess.run(
                ["ffmpeg", "-loglevel", "error", "-ss", "30", "-i", str(fundo_video),
                 "-t", str(dur), "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                 f"crop={W}:{H},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                capture_output=True).stdout
            tam = W * H * 4
            quadros = [bruto[i:i + tam] for i in range(0, len(bruto) - tam + 1, tam)]
        liso = Image.new("RGBA", (W, H), (40, 38, 46, 255))

        def fundo(i):
            if quadros:
                return guias(Image.frombytes("RGBA", (W, H), quadros[min(i, len(quadros) - 1)]))
            return guias(liso)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(pintar(fundo(i), elems, i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    print(f"ok -> {saida}  ({dur}s, {coracoes} coracoes + o torto)")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--previa", metavar="MP4", nargs="?", const="saida/cta_previa.mp4")
    a.add_argument("--overlay", metavar="MOV")
    a.add_argument("--video", type=Path)
    a.add_argument("--coracoes", type=int, default=6)
    o = a.parse_args()
    if o.overlay:
        render(Path(o.overlay), None, o.coracoes, alfa=True)
    else:
        Path(o.previa or "saida/cta_previa.mp4").parent.mkdir(exist_ok=True)
        render(Path(o.previa or "saida/cta_previa.mp4"), o.video, o.coracoes, alfa=False)
