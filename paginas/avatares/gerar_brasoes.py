# -*- coding: utf-8 -*-
"""Todos os brasoes com MASCARA CIRCULAR e fundo transparente.

⚠️ O DEFEITO QUE ISTO CONSERTA: os brasoes vem num quadrado PRETO. Na primeira
versao eu cortei 4% das bordas e confiei no `border-radius` do avatar pra
esconder o resto — nao escondeu. Sobrava um arco preto embaixo de cada um,
porque o aro de cromo nao encosta na borda por igual: no rodape do desenho ha'
mais preto que no topo.

O `modofuturo` nao tinha o defeito porque foi o UNICO que recebeu mascara de
alfa, e recebeu por outro motivo (a foto tinha um cenario pra descartar). Ou
seja: eu ja' tinha a solucao na mao e apliquei em um so'.

⚠️ E AQUI O CIRCULO E' MEDIDO, nao chutado: acha o que NAO e' preto, pega a
caixa, e o circulo sai do centro dessa caixa. Cada arquivo tem sua margem, e
um numero fixo erraria em alguns.
"""
import base64, io
from pathlib import Path
from PIL import Image, ImageDraw

UP = Path(r"C:\Users\Administrator\.claude\uploads\fbe65d66-b0f1-424c-811a-39e428ecddb1")
REPO = Path(r"C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine")
DEST = REPO / "paginas" / "avatares"

MAPA = {
    "b7c47489-image.png": "achadinho.make",
    "73eb13c5-image.png": "semanestesia.pod",
    "ebe6a397-image.png": "atefalhar",
    "1630f790-image.png": "fatura.chora",
    "757f8d97-image.png": "achadinhos.instantaneos",
    "ffa6438c-image.png": "cozinha.internacional",   # chapeu de chef
}

def circulo_medido(im, limiar=26):
    """Caixa do que nao e' preto -> circulo inscrito nela."""
    cinza = im.convert("L").point(lambda v: 255 if v > limiar else 0)
    caixa = cinza.getbbox()
    if not caixa:
        raise RuntimeError("imagem toda preta")
    e, t, d, b = caixa
    cx, cy = (e + d) / 2, (t + b) / 2
    # o menor dos dois lados manda: o brasao e' redondo, entao o lado maior
    # so' pode estar pegando reflexo ou brilho que vazou pro fundo
    r = min(d - e, b - t) / 2
    return cx, cy, r

uris = {}
for arq, canal in MAPA.items():
    im = Image.open(UP / arq).convert("RGB")
    cx, cy, r = circulo_medido(im)
    # 1% pra dentro: o anti-serrilhado da borda do brasao guarda pixels
    # escuros do fundo, e eles reapareceriam como um fio na volta do circulo
    r *= 0.99
    quadro = im.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))
    quadro = quadro.resize((640, 640), Image.LANCZOS)

    mascara = Image.new("L", (640, 640), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, 639, 639), fill=255)
    recorte = Image.new("RGBA", (640, 640), (0, 0, 0, 0))
    recorte.paste(quadro, (0, 0), mascara)

    recorte.resize((320, 320), Image.LANCZOS).save(DEST / f"{canal}.png", optimize=True)

    buf = io.BytesIO()
    recorte.resize((160, 160), Image.LANCZOS).save(buf, format="WEBP", quality=86, method=6)
    uris[canal] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    print(f"{canal:26} circulo em ({cx:.0f},{cy:.0f}) r={r:.0f}   webp {len(uris[canal])//1024} KB")

# o modofuturo ja' foi recortado da foto e continua como esta'
buf = io.BytesIO()
Image.open(DEST / "modofuturo.png").convert("RGBA").resize((160, 160), Image.LANCZOS)\
     .save(buf, format="WEBP", quality=86, method=6)
uris["modofuturo"] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

(DEST / "_data_uris.txt").write_text(
    "\n".join(f"{c}\t{u}" for c, u in uris.items()) + "\n", encoding="utf-8")
print("\ntotal:", sum(len(u) for u in uris.values()) // 1024, "KB em", len(uris), "brasoes")

# mosaico pra conferir a olho, sobre fundo claro (onde o preto apareceria)
tira = Image.new("RGB", (7 * 120, 120), (247, 246, 248))
for i, c in enumerate(uris):
    b = Image.open(DEST / f"{c}.png").convert("RGBA").resize((112, 112), Image.LANCZOS)
    tira.paste(b, (i * 120 + 4, 4), b)
tira.save(r"C:\Users\ADMINI~1\AppData\Local\Temp\brasoes_conferir.png")
