# -*- coding: utf-8 -*-
"""Video de OFERTA (9:16) de um produto do catalogo — canal Pago Menos.

    python -X utf8 ferramentas/video_oferta.py --id 1005012058103385 --saida oferta.mp4

⭐ 29/09/2026 (dono): "sempre confianca, sempre". Por isso o video so' afirma o
que a serie de precos prova:
  - o "antes" e' a MEDIANA dos ultimos dias da serie (`precos_vistos.jsonl`),
    nunca o "de" que a loja inventa — e a tela diz de onde saiu;
  - o "agora" e' o instantaneo (`precos_agora.json`), com a hora da conferencia;
  - sem queda real (>= QUEDA_MIN) nao ha' video: `ValueError`.
Fotos: as oficiais do anuncio. Nunca video de terceiro (direito autoral).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
FONTES = RAIZ / "engine" / "fontes"
W, H, FPS, DUR = 1080, 1920, 30, 20.0
QUEDA_MIN = 0.25
FUNDO, OURO, OURO2, CINZA, BRANCO = (14, 13, 18), (232, 190, 84), (198, 146, 40), (150, 148, 160), (250, 248, 244)
VOZ = "pt-BR-AntonioNeural"


def fonte(nome: str, t: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTES / nome), t)


def reais(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def dados(pid: str) -> dict:
    serie = []
    for l in open(RAIZ / "estado" / "precos_vistos.jsonl", encoding="utf-8"):
        x = json.loads(l)
        if str(x["id"]) == pid:
            serie.append((x["quando"], x["preco"]))
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))[pid]
    hoje = agora["quando"][:10]
    antes = [p for q, p in sorted(serie) if q < hoje][-30:]
    if len(antes) < 7:
        raise ValueError(f"serie curta demais ({len(antes)} dias) — sem prova de queda")
    ref = statistics.median(antes)
    queda = 1 - agora["preco"] / ref
    if queda < QUEDA_MIN:
        raise ValueError(f"queda de {queda:.0%} nao justifica video")
    nome = json.load(open(RAIZ / "estado" / "nomes_curtos.json", encoding="utf-8"))[pid]
    sp = datetime.fromisoformat(agora["quando"]).astimezone(timezone(timedelta(hours=-3)))
    return {"nome": nome, "agora": agora["preco"], "ref": ref, "dias": len(antes),
            "queda": queda, "hora": sp.strftime("%d/%m às %H:%M"), "imagens": agora["imagens"][:4]}


def baixar(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for tent in range(3):
        try:
            return Image.open(BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
        except OSError:
            if tent == 2:
                raise


def centro(d: ImageDraw.ImageDraw, y: int, txt: str, f, cor):
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, y), txt, font=f, fill=cor)
    return w


def pilula(d, x0, y0, x1, y1, cor):
    d.rounded_rectangle([x0, y0, x1, y1], (y1 - y0) // 2, fill=cor)


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def base_fundo() -> Image.Image:
    im = Image.new("RGB", (W, H), FUNDO)
    brilho = Image.new("L", (W, H), 0)
    ImageDraw.Draw(brilho).ellipse([-200, 300, W + 200, 1500], fill=38)
    brilho = brilho.filter(ImageFilter.GaussianBlur(160))
    return Image.composite(Image.new("RGB", (W, H), OURO2), im, brilho)


def cartao(foto: Image.Image, lado: int) -> Image.Image:
    c = Image.new("RGB", (lado, lado), (255, 255, 255))
    f = foto.copy()
    f.thumbnail((int(lado * 0.9), int(lado * 0.9)))
    c.paste(f, ((lado - f.width) // 2, (lado - f.height) // 2))
    return c


def quadro(t: float, d: dict, fundo: Image.Image, cartoes: list[Image.Image]) -> Image.Image:
    im = fundo.copy()
    dr = ImageDraw.Draw(im)
    # topo: marca + selo de confianca
    centro(dr, 110, "PAGO MENOS", fonte("Poppins-Bold.ttf", 44), OURO)
    fs = fonte("Poppins-Bold.ttf", 30)
    selo = f"preço conferido {d['hora']}"
    sw = dr.textlength(selo, font=fs) + 44          # + o visto desenhado
    x0 = (W - sw) / 2
    pilula(dr, x0 - 28, 180, x0 + sw + 28, 236, (36, 34, 44))
    dr.line([(x0 + 2, 210), (x0 + 12, 221), (x0 + 30, 196)], fill=(88, 200, 120), width=6, joint="curve")
    dr.text((x0 + 44, 186), selo, font=fs, fill=BRANCO)

    # foto: cartao branco arredondado, zoom lento, troca com fusao a cada 3 s
    lado = 820
    n = min(len(cartoes), 4)
    k = int(t // 3.2) % n
    frac = (t % 3.2) / 3.2
    z = 1.0 + 0.06 * frac
    a = cartoes[k].resize((int(lado * z),) * 2, Image.LANCZOS).crop(
        (int(lado * (z - 1) / 2),) * 2 + (int(lado * (z - 1) / 2) + lado,) * 2)
    if frac > 0.85 and n > 1:
        b = cartoes[(k + 1) % n].resize((lado, lado))
        a = Image.blend(a, b, (frac - 0.85) / 0.15)
    mask = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, lado - 1, lado - 1], 48, fill=255)
    y_foto = 300
    im.paste(a, ((W - lado) // 2, y_foto), mask)

    # gancho (0-3 s): faixa ouro por cima da foto
    if t < 3.2:
        e = ease(t / 0.4) * (1 - ease((t - 2.8) / 0.4))
        fg = fonte("Anton-Regular.ttf", 120)
        txt = "CAIU PELA METADE" if d["queda"] >= 0.5 else f"CAIU {round(d['queda'] * 100)}%"
        tw = dr.textlength(txt, font=fg)
        camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(camada)
        pilula(cd, (W - tw) / 2 - 50, 960, (W + tw) / 2 + 50, 1130, OURO + (int(255 * e),))
        cd.text(((W - tw) / 2, 968), txt, font=fg, fill=FUNDO + (int(255 * e),))
        im.paste(camada, (0, 0), camada)
        dr = ImageDraw.Draw(im)

    # nome
    centro(dr, 1150, d["nome"], fonte("Poppins-Bold.ttf", 46), BRANCO)

    # preco (a partir de 3,5 s)
    if t >= 3.5:
        e = ease((t - 3.5) / 0.6)
        y = int(1250 + 40 * (1 - e))
        fa = fonte("Poppins-Bold.ttf", 52)
        antes = f"antes {reais(d['ref'])}"
        aw = centro(dr, y, antes, fa, CINZA)
        dr.line([((W - aw) / 2, y + 36), ((W + aw) / 2, y + 36)], fill=CINZA, width=5)
        fp = fonte("Anton-Regular.ttf", 200)
        pw = centro(dr, y + 70, reais(d["agora"]), fp, OURO)
        fb = fonte("Poppins-Bold.ttf", 44)
        badge = f"-{round(d['queda'] * 100)}%"
        bw = dr.textlength(badge, font=fb)
        bx = (W + aw) / 2 + 40
        pilula(dr, bx - 22, y - 6, bx + bw + 22, y + 60, (200, 46, 60))
        dr.text((bx, y - 2), badge, font=fb, fill=BRANCO)
        nota = f"“antes” = preço mais comum nos últimos {d['dias']} dias"
        centro(dr, y + 330, nota, fonte("Poppins-Bold.ttf", 28), CINZA)

    # chamada final (a partir de 15 s)
    if t >= 15:
        e = ease((t - 15) / 0.5)
        fc = fonte("Poppins-Bold.ttf", 56)
        txt = "link na bio"
        tw = dr.textlength(txt, font=fc) + 60        # + a seta desenhada
        x0 = (W - tw) / 2
        y = int(1720 + 30 * (1 - e))
        pilula(dr, x0 - 50, y, x0 + tw + 50, y + 96, OURO)
        dr.text((x0, y + 12), txt, font=fc, fill=FUNDO)
        ax = x0 + tw - 22
        dr.polygon([(ax - 18, y + 38), (ax + 18, y + 38), (ax, y + 62)], fill=FUNDO)
    return im


def narracao(d: dict, destino: Path) -> None:
    import edge_tts
    from engine import numeros
    r, a = d["ref"], d["agora"]
    txt = (f"{d['nome']}. Nos últimos {d['dias']} dias ele custava, na maior parte do tempo, "
           f"{int(r)} reais. Hoje está {int(a)} reais e {round((a - int(a)) * 100)} centavos. "
           f"Eu conferi o preço agora há pouco. O link está na bio.")
    asyncio.run(edge_tts.Communicate(numeros.por_extenso(txt), voice=VOZ, rate="+4%").save(str(destino)))


def gerar(pid: str, saida: Path) -> dict:
    d = dados(pid)
    tmp = Path(tempfile.mkdtemp())
    cartoes = [cartao(baixar(u), 820) for u in d["imagens"]]
    voz = tmp / "voz.mp3"
    narracao(d, voz)
    fundo = base_fundo()
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(voz),
                          "-filter_complex", "[1:a]adelay=600|600,apad[a]", "-map", "0:v", "-map", "[a]",
                          "-t", str(DUR), "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                          "-movflags", "+faststart", str(saida)], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(quadro(i / FPS, d, fundo, cartoes).tobytes())
    p.stdin.close()
    p.wait()
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--saida", type=Path, required=True)
    a = ap.parse_args()
    print(gerar(a.id, a.saida))
