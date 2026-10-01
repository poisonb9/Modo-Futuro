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
import os
import statistics
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
FONTES = RAIZ / "engine" / "fontes"
W, H, FPS, DUR = 1080, 1920, 30, 20.0
# ⛔ 01/10/2026: UMA regra so'. Aqui era 0.25 fixo e o motor (engine/ofertas)
# ja' estava em 0.15 (dono, 30/09): a nuvem escolheu 9 ofertas e o video
# recusou 8 ("queda de 21% nao justifica video"). Agora le' de la'.
from engine.ofertas import QUEDA_MIN  # noqa: E402
FUNDO, OURO, OURO2, CINZA, BRANCO = (14, 13, 18), (232, 190, 84), (198, 146, 40), (150, 148, 160), (250, 248, 244)
VOZ = "pt-BR-AntonioNeural"


def fonte(nome: str, t: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTES / nome), t)


def reais(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def dados(pid: str, exigir_queda: bool = True) -> dict:
    serie = []
    for l in open(RAIZ / "estado" / "precos_vistos.jsonl", encoding="utf-8"):
        x = json.loads(l)
        if str(x["id"]) == pid:
            serie.append((x["quando"], x["preco"]))
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))[pid]
    hoje = agora["quando"][:10]
    antes = [p for q, p in sorted(serie) if q < hoje][-30:]
    if len(antes) < 7 and exigir_queda:
        raise ValueError(f"serie curta demais ({len(antes)} dias) — sem prova de queda")
    ref = statistics.median(antes) if antes else agora["preco"]
    queda = 1 - agora["preco"] / ref
    if queda < QUEDA_MIN and exigir_queda:
        raise ValueError(f"queda de {queda:.0%} nao justifica video")
    # ⛔ "provada" decide se o video pode dizer CAIU e mostrar o riscado. Sem
    # ela o video mostra so' o preco de hoje — nunca uma queda inventada.
    provada = len(antes) >= 7 and queda >= QUEDA_MIN
    nome = json.load(open(RAIZ / "estado" / "nomes_curtos.json", encoding="utf-8"))[pid]
    sp = datetime.fromisoformat(agora["quando"]).astimezone(timezone(timedelta(hours=-3)))
    return {"nome": nome, "agora": agora["preco"], "ref": ref, "dias": len(antes),
            "queda": queda, "hora": sp.strftime("%d/%m às %H:%M"), "imagens": agora["imagens"][:4],
            "nota": agora.get("nota"), "vendas": agora.get("vendas"),
            "marca": "PAGO MENOS", "numero": None, "provada": provada,
            "video": agora.get("video") or "", "gancho": ""}


# ⭐ 29/09/2026 (plano aprovado, ideias 5 e 10): a marca de cada canal no topo
# e a serie "ACHADO DO DIA #N" — numero por canal, contado no registro das
# ofertas feitas (nunca chutado: mesma regra do selo PARTE N).
MARCAS = {"fatura.chora": "PAGO MENOS", "achadinhos.instantaneos": "ACHADINHO TOTAL",
          "achadinhototal": "ACHEI PRA VOCÊ"}  # 30/09: = nome de exibicao do perfil (print do dono)


def proximo_numero(canal: str) -> int:
    from engine import ofertas
    return 1 + sum(1 for f in ofertas._feitas() if f.get("canal") == canal)


def vendas_curto(n: int) -> str:
    return f"{n / 1000:.1f}".replace(".0", "").replace(".", ",") + " mil" if n >= 1000 else str(n)


def legenda_post(d: dict) -> str:
    """A legenda do post no TikTok (30/09/2026).

    Mesma regra-mae do video ("sempre confianca, sempre"): so' afirma o que a
    nossa serie prova — o preco de hoje, a mediana dos nossos N dias e a loja.
    Estrutura do acervo (gancho -> prova -> oferta com chamada clara):
    afirma, nunca pergunta. Max 3 hashtags (legenda_post do motor, 28/09).
    """
    queda = round(float(d["queda"]) * 100)
    num = f" #{d['numero']}" if d.get("numero") else ""
    return (f"Achado do dia{num}: {d['nome']} caiu {queda}% 📉\n"
            f"Hoje {reais(d['agora'])} — o normal dele, nos nossos {d['dias']} dias "
            f"de acompanhamento, é {reais(d['ref'])}.\n"
            f"Loja nota {str(d['nota']).replace('.', ',')} · {vendas_curto(int(d['vendas']))} vendidos.\n"
            f"💬 Comenta QUERO aqui embaixo que eu te respondo!\n"
            f"🔗 Link na bio → Achado do dia{num}\n"
            f"#achadinhos #promoção #aliexpress")


def comentario_fixado(d: dict) -> str:
    """Ideia 6: o texto que o dono cola e fixa (o TikTok nao tem API pra isso)."""
    return (f"Preço conferido em {d['hora']}: {reais(d['agora'])}. "
            f"Se mudar, eu aviso no Telegram 🔔 (link da bio)")


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


def ordenar_fotos(urls: list[str]) -> list[str]:
    """⛔ 30/09 (print do dono): o video da faixa ABRIU com um aviso da loja
    ("Notice before purchase", texto 78% da foto). A foto com MENOS texto
    (OCR de estado/fotos_ocr.json) vai na frente — ela e' a capa — e foto que
    e' quase so' texto sai, se sobrar alguma limpa."""
    try:
        med = json.loads((RAIZ / "estado" / "fotos_ocr.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return urls
    txt = lambda u: (med.get(u) or {}).get("texto", 0.2)  # noqa: E731 — sem medida: no meio
    boas = [u for u in urls if txt(u) <= 0.35]
    return sorted(boas or urls, key=txt)


def cartao(foto: Image.Image, lado: int) -> Image.Image:
    c = Image.new("RGB", (lado, lado), (255, 255, 255))
    f = foto.copy().convert("RGB")
    # 01/10 (dono: "o produto ta' pequeno" na capa): foto de loja vem com muita
    # margem de fundo liso -> recorta ate' o produto quando os 4 cantos sao
    # do mesmo fundo (foto "de cena" fica como esta').
    cantos = [f.getpixel(p) for p in ((0, 0), (f.width - 1, 0), (0, f.height - 1), (f.width - 1, f.height - 1))]
    if max(max(abs(x - y) for x, y in zip(c_, cantos[0])) for c_ in cantos) < 18:
        dif = ImageChops.difference(f, Image.new("RGB", f.size, cantos[0])).convert("L").point(lambda v: 255 if v > 24 else 0)
        bb = dif.getbbox()
        if bb:
            pad = int(max(bb[2] - bb[0], bb[3] - bb[1]) * 0.04)
            f = f.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(f.width, bb[2] + pad), min(f.height, bb[3] + pad)))
    f.thumbnail((int(lado * 0.94), int(lado * 0.94)))
    c.paste(f, ((lado - f.width) // 2, (lado - f.height) // 2))
    return c


DEMO_S = 8.0   # ⭐ ideia 12: segundos do video OFICIAL do vendedor no cartao


# ⭐ 30/09/2026 21h — CAMADA DE INAUGURACAO (aprovada pelo dono: "gostei
# demais"). A mesma festa do site e dos e-mails dentro do anuncio:
#   0-1,4 s  o balao do canal sobe e pousa no canto da foto (gancho visual,
#            sem preco nos 2 primeiros segundos — acervo marketing-e-oferta)
#   3,5 s    o preco ESTOURA com os lanca-confetes do site (baloes/lanca)
#   prova    o "antes" vira a ETIQUETA dourada de inauguracao, riscada
#   15 s     o ENVELOPE-convite dos e-mails ao lado do "link na bio"
#   selo     "INAUGURACAO" ao lado do "preco conferido" ate' INAUGURACAO_ATE
# Tudo dentro da zona segura (SEG_*); enfeite so' na margem esquerda, que o
# TikTok nao cobre.
BALOES = RAIZ / "paginas" / "baloes"
# ⚠️ o NOME do arquivo engana: `canal_pago_menos` e' o CIFRAO e `canal_achadinhos_instantaneos`
# o CARRINHO. Aqui vale o AVATAR de cada perfil (prints do dono, 30/09).
BALAO_DO_CANAL = {"PAGO MENOS": "canal_achadinhos_instantaneos", "ACHADINHO TOTAL": "canal_pago_menos",
                  # 30/09: o perfil volta a se chamar Achadinhos Instantaneos (dono) — mesmo cifrao
                  "ACHADINHOS INSTANTÂNEOS": "canal_pago_menos",
                  "ACHEI PRA VOCÊ": "loja_lupa"}
# o que ENTRA no comeco (0-1,5 s). Achei Pra Voce: a lupa dourada de letra-balao.
BALAO_ENTRADA = {"PAGO MENOS": "canal_achadinhos_instantaneos", "ACHADINHO TOTAL": "canal_pago_menos",
                 "ACHADINHOS INSTANTÂNEOS": "canal_pago_menos",
                 "ACHEI PRA VOCÊ": "inaug_lupa"}
AVATAR_X, AVATAR_Y = 993, 797     # foto de perfil na coluna do TikTok (prints do dono, 1080x1920)   # 30/09: a lupa da LOJA (arte do dono), = avatar
INAUGURACAO_ATE = "2026-10-07"
_CACHE: dict = {}


def _balao(nome: str, altura: int, corte: tuple | None = None) -> Image.Image:
    chave = (nome, altura, corte)
    if chave not in _CACHE:
        im = Image.open(BALOES / f"{nome}.webp").convert("RGBA")
        if corte:
            im = im.crop(corte)
        im = im.crop(im.getbbox())
        _CACHE[chave] = im.resize((max(1, round(im.width * altura / im.height)), altura), Image.LANCZOS)
    return _CACHE[chave]


def _brilho(peca: Image.Image, fase: float) -> Image.Image:
    """⭐ 30/09 (premium, item 3): um REFLEXO de luz atravessa a peca dourada,
    como vitrine de joalheria. `fase` 0..1 = posicao da faixa; fora disso, nada."""
    if not (0 <= fase <= 1):
        return peca
    w, h = peca.size
    faixa = Image.new("L", (w, h), 0)
    x = -0.4 * w + fase * 1.8 * w
    ImageDraw.Draw(faixa).polygon([(x, 0), (x + w * 0.18, 0), (x + w * 0.18 - h * 0.6, h), (x - h * 0.6, h)], fill=120)
    faixa = ImageChops.multiply(faixa.filter(ImageFilter.GaussianBlur(max(2, w * 0.03))), peca.split()[3])
    luz = Image.new("RGBA", (w, h), (255, 250, 230, 0))
    luz.putalpha(faixa)
    return Image.alpha_composite(peca, luz)


def _colar(im: Image.Image, peca: Image.Image, cx: float, cy: float, ang: float = 0, alfa: float = 1,
           sombra: bool = True):
    if alfa <= 0:
        return
    if ang:
        peca = peca.rotate(ang, expand=True, resample=Image.BICUBIC)
    if alfa < 1:
        peca = peca.copy()
        peca.putalpha(peca.split()[3].point(lambda v: int(v * alfa)))
    x, y = int(cx - peca.width / 2), int(cy - peca.height / 2)
    # ⭐ 30/09 (premium, item 2): SOMBRA suave embaixo — o balao FLUTUA em vez
    # de parecer colado. So' nas pecas grandes (confete nao precisa).
    if sombra and peca.height >= 70:
        a = peca.split()[3].point(lambda v: int(v * 0.42))
        pad = 30
        sm = Image.new("L", (peca.width + 2 * pad, peca.height + 2 * pad), 0)
        sm.paste(a, (pad, pad))
        sm = sm.filter(ImageFilter.GaussianBlur(14))
        preto = Image.new("RGB", sm.size, (0, 0, 0))
        im.paste(preto, (x - pad + 10, y - pad + 22), sm)
    im.paste(peca, (x, y), peca)


def _confete(im: Image.Image, t: float, semente: int, cx: float, cy: float):
    """Os dois cones do site disparam dos lados do preco (t = s desde o disparo)."""
    import math
    import random
    if not (0 <= t <= 2.2):
        return
    pecas = sorted((BALOES / "lanca").glob("p*.webp"))
    rnd = random.Random(semente)
    for lado, x0 in ((-1, cx - 390), (1, cx + 360)):
        # ⭐ 30/09 (dono: "cada um mirando pra um canto aleatorio"): os dois
        # SIMETRICOS, boca pra dentro e pra cima (o da direita e' o espelho).
        cone = _balao("lanca/cone", 120)
        if lado > 0:
            from PIL import ImageOps
            cone = ImageOps.mirror(cone)
        _colar(im, cone, x0, cy + 60, 0, 1 - max(0, t - 1.6) / 0.6)
        for _ in range(26):
            f = pecas[rnd.randrange(len(pecas))]
            ang = math.radians(rnd.uniform(55, 88))
            v = rnd.uniform(900, 1500)
            spin = rnd.uniform(-400, 400)
            tam = rnd.randint(26, 44)
            x = x0 - lado * math.cos(ang) * v * t * 0.55
            y = cy - math.sin(ang) * v * t + 1300 * t * t
            if SEG_TOPO < y < SEG_BASE:
                _colar(im, _balao(f"lanca/{f.stem}", tam), x, y, spin * t, 1 - max(0, t - 1.5) / 0.7, sombra=False)


# ⭐ 30/09/2026 19:50 — ZONA SEGURA DO TIKTOK (print do dono no iPhone: topo
# embaixo da BUSCA, preco embaixo do @/legenda, "caiu pela metade" e o -56%
# embaixo dos botoes da direita). Medido nos prints (924x2000 -> 1080x1920):
#   busca/abas terminam em ~y 200  -> nada importante acima de SEG_TOPO
#   @ + legenda + "promover" comecam em ~y 1400 -> nada abaixo de SEG_BASE
#   coluna de icones comeca em ~x 935 (de y ~750 a ~1590) -> largura util
#   centrada de no maximo SEG_LARG (160..920).
SEG_TOPO, SEG_BASE, SEG_LARG = 262, 1380, 740
PRECO_T = 2.0
ROLA_S = 0.9       # o preco rola do "antes" ate' o de hoje


def _caber(dr, txt, nome, tam, larg, minimo=24):
    f = fonte(nome, tam)
    while dr.textlength(txt, font=f) > larg and f.size > minimo:
        f = fonte(nome, f.size - 2)
    return f


def quadro(t: float, d: dict, fundo: Image.Image, cartoes: list[Image.Image],
           demo: Image.Image | None = None) -> Image.Image:
    import math
    im = fundo.copy()
    dr = ImageDraw.Draw(im)
    festa = bool(d.get("festa"))
    # topo (logo abaixo da busca): marca + "achado do dia" numa linha so'
    marca = d.get("marca") or "PAGO MENOS"
    topo = f"{marca}  ·  ACHADO DO DIA #{d['numero']}" if d.get("numero") else marca
    centro(dr, SEG_TOPO, topo, _caber(dr, topo, "Poppins-Bold.ttf", 34, SEG_LARG), OURO)
    fs = fonte("Poppins-Bold.ttf", 26)
    selo = f"preço conferido {d['hora']}"
    sw = dr.textlength(selo, font=fs) + 40
    iw = dr.textlength("INAUGURAÇÃO", font=fs) + 60 if festa else 0
    x0 = (W - sw - iw) / 2 + iw
    y0 = SEG_TOPO + 56
    if festa:   # a pilula vermelha da festa, colada no selo de confianca
        pilula(dr, x0 - iw - 16, y0, x0 - 20, y0 + 48, (200, 46, 60))
        dr.text((x0 - iw + 6, y0 + 5), "INAUGURAÇÃO", font=fs, fill=BRANCO)
    pilula(dr, x0 - 24 + (12 if festa else 0), y0, x0 + sw + 24, y0 + 48, (36, 34, 44))
    dr.line([(x0 + 2, y0 + 26), (x0 + 11, y0 + 36), (x0 + 27, y0 + 14)], fill=(88, 200, 120), width=5, joint="curve")
    dr.text((x0 + 40, y0 + 5), selo, font=fs, fill=BRANCO)

    # foto: cartao menor, centrado, inteiro fora da coluna de icones
    # 01/10 (dono: "produto pequeno na capa"; acervo: miniatura com o assunto
    # GRANDE): nos 2 s antes do preco o cartao e' 540 e encolhe pra 440 quando
    # o preco entra — o quadro 0 (capa da grade) mostra o produto grande.
    lado = int(440 + 100 * (1 - ease((t - (PRECO_T - 0.5)) / 0.5)))
    n = min(len(cartoes), 4)
    k = int(t // 3.2) % n
    frac = (t % 3.2) / 3.2
    z = 1.0 + 0.06 * frac
    a = cartoes[k].resize((int(lado * z),) * 2, Image.LANCZOS).crop(
        (int(lado * (z - 1) / 2),) * 2 + (int(lado * (z - 1) / 2) + lado,) * 2)
    if frac > 0.85 and n > 1:
        b = cartoes[(k + 1) % n].resize((lado, lado))
        a = Image.blend(a, b, (frac - 0.85) / 0.15)
    if demo is not None:
        a = demo.resize((lado, lado)) if demo.size != (lado, lado) else demo
    y_foto = y0 + 76
    y_base_foto = y_foto + lado
    # ⛔ 30/09 (print do dono): o quadro 0 E' A CAPA DA GRADE. Ele estava vazio (so'
    # o balao subindo) e a grade mostrou um fundo preto. Produto inteiro desde t=0.
    entra = 1.0
    if entra > 0.02:
        ld = max(2, int(lado * (0.6 + 0.4 * entra)))
        mask = Image.new("L", (ld, ld), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, ld - 1, ld - 1], max(1, int(44 * ld / lado)),
                                               fill=int(255 * min(1.0, entra * 1.4)))
        im.paste(a.resize((ld, ld)), ((W - ld) // 2, y_foto + (lado - ld) // 2), mask)

    if festa:
        # ⭐ 30/09 18:30 (dono, ajuste fino): 3 papeis de balao —
        #  1. ENTRADA: a lupa (ou o balao do perfil) sobe grande, passa POR CIMA
        #     do produto "procurando" e vai pro lado esquerdo do cartao;
        #  2. PERFIL: a lupa da LOJA, com fita, flutua em cima da foto de perfil
        #     do TikTok (coluna da direita), a fita encostando na foto — e' la'
        #     que esta' o link;
        #  3. sem balao atras do laco; sacola some quando a MAO entra (15 s).
        esq, dir_ = (W - lado) / 2, (W + lado) / 2
        # 01/10 (dono): a LUPA entrando "procurando" e' o padrao de TODOS — o
        # balao do canal ja' esta' em cima da foto de perfil, repetir era redundante.
        ent = "inaug_lupa_cromada"   # 01/10 (dono): cromada, nao dourada
        # 01/10 (dono): a lupa vem DO ESPECTADOR — entra gigante, enchendo a
        # tela, encolhe ate' o produto puxando o olhar, procura e pousa no canto.
        sobe, some = ease(t / 0.7), ease((t - 1.05) / 0.5)
        procura = 60 * math.sin(max(0.0, t - 0.6) * 5) * (1 - some) if t > 0.6 else 0
        alt = int(2200 - (2200 - 470) * sobe - 270 * some)
        cx = W / 2 + procura + (esq - 55 - W / 2) * some
        cy = H / 2 + (y_foto + lado * 0.45 - H / 2) * sobe
        cy += ((y_foto + 175) - (y_foto + lado * 0.45)) * some + 6 * math.sin(t * 2)
        _colar(im, _balao(ent, alt), cx, cy, -6 * some + 3 * math.sin(t * 1.5) + 12 * (1 - sobe),
               ease(t / 0.15))
        # 2. em cima da foto de perfil (medida nos prints: centro ~(993, 797))
        per = BALAO_DO_CANAL.get(marca, "loja_lupa")
        # 01/10 (dono, prints do iPhone): o balao ficava LONGE da foto de perfil e
        # embolava no laco. No iPhone o 9:16 perde ~9% de cada lado e a foto de
        # perfil cai em x~914 do video (nao 993). Menor (200) e logo ACIMA da
        # foto, como quem aponta "siga aqui"; fora do laco do cartao.
        bp = _balao(per, 200)
        _colar(im, bp, 890 + 3 * math.sin(t * 1.3), AVATAR_Y - 70 - bp.height / 2 + 4 * math.sin(t * 1.7),
               2 * math.sin(t * 1.1), ease((t - 0.4) / 0.6))
        # 3. sacola ao lado do cartao (sai quando a mao chega) e laco = presente
        _colar(im, _balao("loja_sacola", 180, (0, 0, 970, 610)), esq - 50, y_foto + lado - 110 + 7 * math.sin(t * 1.4 + 1),
               6 + 4 * math.sin(t * 1.1 + 2), 1 - ease((t - PRECO_T - 0.4) / 0.4))
        # ⭐ 30/09 (arte do dono): logo depois do preco, o SELO "preco conferido"
        # toma o lugar da sacola — a prova no momento da decisao. Sai quando a mao entra.
        selo = ease((t - PRECO_T - ROLA_S - 0.6) / 0.5) * (1 - ease((t - 14.6) / 0.4))
        _colar(im, _balao("selo_preco_conferido", 215), esq - 45,
               y_foto + lado - 95 + 30 * (1 - selo) + 6 * math.sin(t * 1.5), -8 + 3 * math.sin(t * 1.2), selo)
        _colar(im, _balao("inaug_laco", 88, (0, 0, 360, 330)), dir_ - 4, y_foto + 36, 18)   # abaixo do selo do topo   # o cartao vira PRESENTE
        # 01/10 (arte do dono): no final, o COMENTE QUERO entra do lado do cartao
        cq = ease((t - 15.2) / 0.5)
        # 01/10 (dono, print com o circulo): pode ENTRAR sobre o fone, mas logo
        # VOA pro canto de cima a' direita e fica la' — abaixo da busca/abas do
        # TikTok (~y 200), a' direita do texto do topo, sem cobrir o produto.
        vai = ease((t - 16.1) / 0.6)
        alt_cq = int(round((300 - 150 * vai) / 10) * 10)
        x_cq = (dir_ - 70) + (865 - (dir_ - 70)) * vai
        y_cq = (y_foto + lado * 0.42 + 50 * (1 - cq)) + (175 - (y_foto + lado * 0.42) - 50 * (1 - cq)) * vai
        _colar(im, _balao("selo_comente_quero", alt_cq, (0, 0, 979, 1000)), x_cq, y_cq + 6 * math.sin(t * 2),
               6 + 3 * math.sin(t * 1.4), cq)

    # faixa ouro sobre a base da foto: gancho e, no fim, o convite
    faixa = None
    if t < 3.2:     # ja' no quadro 0 (capa): a faixa entra CHEIA, so' sai com fade
        e = 1 - ease((t - 2.8) / 0.4)
        if d.get("gancho"):
            faixa = d["gancho"]
        elif d.get("provada"):
            faixa = "CAIU PELA METADE" if d["queda"] >= 0.5 else f"CAIU {round(d['queda'] * 100)}%"
        else:
            faixa = "ACHADO DO DIA"
    elif t >= 15:
        e = ease((t - 15) / 0.5)
        faixa = "LINK NA BIO"
    if faixa:
        conv = festa and t >= 15
        yf = y_base_foto - 70
        if festa:
            # ⭐ 30/09 (dono: "balao faixa azul bem bonito", arte dele): o texto vai
            # no miolo liso da FAIXA AZUL (17%-83% da largura). No convite final a
            # MAO de balao aponta pro "link na bio" (troca o envelope, "feio").
            larg = 700 if conv else 760
            fx = _balao("loja_faixa_azul", 200, (0, 0, 1000, 262))   # so' pra proporcao
            alt = round(larg * fx.height / fx.width)
            banda = _balao("loja_faixa_azul", alt, (0, 0, 1000, 262)).copy()
            bd = ImageDraw.Draw(banda)
            fg = _caber(bd, faixa, "Anton-Regular.ttf", int(alt * 0.52), int(banda.width * 0.64), 40)
            tw = bd.textlength(faixa, font=fg)
            asc, desc = fg.getmetrics()
            ty = (alt - asc - desc) / 2 - alt * 0.03
            bd.text(((banda.width - tw) / 2 + 3, ty + 4), faixa, font=fg, fill=(10, 20, 70))
            bd.text(((banda.width - tw) / 2, ty), faixa, font=fg, fill=BRANCO)
            cx = W / 2 + (60 if conv else 0)
            _colar(im, banda, cx, yf + 66 + (40 * (1 - e) if conv else 0), 1.5 * math.sin(t * 1.6), e)
            if conv:
                # aponta pra cima-direita: pro balao em cima da foto de perfil (o link)
                _colar(im, _balao("loja_mao", 240, (0, 0, 419, 780)), cx - banda.width / 2 + 10,
                       yf - 10 + 70 * (1 - e) + 8 * math.sin(t * 3), -38 + 5 * math.sin(t * 3), e)
        else:
            fg = _caber(dr, faixa, "Anton-Regular.ttf", 96, SEG_LARG - 90, 50)
            tw = dr.textlength(faixa, font=fg)
            camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            cd = ImageDraw.Draw(camada)
            pilula(cd, (W - tw) / 2 - 45, yf, (W + tw) / 2 + 45, yf + 132, OURO + (int(255 * e),))
            cd.text(((W - tw) / 2, yf + 6), faixa, font=fg, fill=FUNDO + (int(255 * e),))
            im.paste(camada, (0, 0), camada)
        dr = ImageDraw.Draw(im)

    # nome + confianca da loja
    # ⭐ 30/09 (dono: "a descricao do produto esta' muito pequena"): 52 px, ate'
    # 2 linhas partidas no meio (acervo: "garantir que o texto seja legivel").
    y = y_base_foto + 92
    fn = fonte("Poppins-Bold.ttf", 52)
    linhas = [d["nome"]]
    if dr.textlength(d["nome"], font=fn) > SEG_LARG - 110:
        pal = d["nome"].split()
        k = min(range(1, len(pal)), key=lambda i: abs(dr.textlength(" ".join(pal[:i]), font=fn)
                                                      - dr.textlength(" ".join(pal[i:]), font=fn)))
        linhas = [" ".join(pal[:k]), " ".join(pal[k:])]
    MIOLO = SEG_LARG - 110          # 30/09 (dono): "letras encostando no anel dourado"
    fn = _caber(dr, max(linhas, key=lambda l: dr.textlength(l, font=fn)), "Poppins-Bold.ttf", 52, MIOLO, 34)
    # ⭐ 30/09 (arte do dono, premium item 7): a PLACA preta com friso dourado
    # atras do nome, e a parte que diz O QUE O PRODUTO FAZ (depois de "com"/"para")
    # em dourado. O nome continua texto limpo — informacao, nao enfeite.
    # 01/10 (dono: "o P de Tipo encosta, ta' muito colado"): respiro de verdade —
    # 30 px em cima e 40 embaixo (a perna do p/g/q desce abaixo da linha).
    alt_nome = len(linhas) * (fn.size + 10) + 70
    placa = _balao("placa_nome_produto", 100).resize((SEG_LARG + 60, alt_nome))
    im.paste(placa, (int((W - placa.width) / 2), int(y - 30)), placa)
    dr = ImageDraw.Draw(im)
    chave = ""
    for sep in (" com ", " para "):
        if sep in d["nome"]:
            chave = d["nome"].split(sep, 1)[1]
            chave = " ".join(chave.split()[:3])
            break
    douradas = set(chave.split())          # palavra a palavra: a chave pode quebrar de linha
    for li in linhas:
        xw = (W - dr.textlength(li, font=fn)) / 2
        for k, pal in enumerate(li.split()):
            pedaco = pal + (" " if k < len(li.split()) - 1 else "")
            dr.text((xw, y), pedaco, font=fn, fill=OURO if pal in douradas else BRANCO)
            xw += dr.textlength(pedaco, font=fn)
        y += fn.size + 10
    y += 30
    if d.get("nota") and d.get("vendas"):
        loja = f"loja nota {str(d['nota']).replace('.', ',')}  ·  {vendas_curto(d['vendas'])} vendidos"
        centro(dr, y + 2, loja, fonte("Poppins-Bold.ttf", 28), CINZA)
    y_preco = y + 58

    # preco (a partir de PRECO_T) — tudo termina acima de SEG_BASE. 30/09: era
    # 3,5 s e o terco de baixo ficava vazio; o acervo so' pede nada de desconto
    # nos 2 PRIMEIROS segundos.
    if t >= PRECO_T:
        e = ease((t - PRECO_T) / 0.6)
        y = int(min(y_preco, SEG_BASE - 250) + 20 * (1 - e))
        fa = fonte("Poppins-Bold.ttf", 40)
        fp = fonte("Anton-Regular.ttf", 128)
        preco = reais(d["agora"])
        # ⭐ 30/09 (dono: "ta' muito jogado, algo mais caprichado"): a PROVA vira
        # uma capsula propria — graficozinho dourado + frase clara — em linha
        # livre, abaixo da explosao. Mesmo fato, dito como garantia.
        # 01/10 (dono): a capsula cobria a explosao do preco, que e' PRIORIDADE ->
        # desenhada ANTES (fica por baixo) e um pouco mais abaixo.
        nota = (f"Medimos por {d['dias']} dias: o normal era {reais(d['ref'])}" if d.get("provada")
                else "sem desconto inventado: é o preço da loja agora")
        fcap = fonte("Poppins-Bold.ttf", 26)
        tw_n = dr.textlength(nota, font=fcap)
        cw, ch = tw_n + 90, 50
        cy_n = min(y + 256, SEG_BASE - ch + 18)
        cx0 = (W - cw) / 2
        dr.rounded_rectangle([cx0, cy_n, cx0 + cw, cy_n + ch], ch // 2, fill=(24, 22, 28), outline=OURO, width=2)
        for k, hbar in enumerate((12, 20, 28)):          # o grafico: tres barrinhas subindo
            bx_ = cx0 + 24 + k * 11
            dr.rounded_rectangle([bx_, cy_n + 38 - hbar, bx_ + 7, cy_n + 38], 2, fill=OURO)
        dr.text((cx0 + 70, cy_n + 10), nota, font=fcap, fill=BRANCO)
        if d.get("provada") and festa:
            # a ETIQUETA de inauguracao carrega o "antes", riscado, balancando
            tag = _balao("inaug_etiqueta", 160, (0, 90, 360, 318)).copy()
            pw = dr.textlength(preco, font=fp)
            gx = (W - (tag.width + 16 + pw)) / 2
            td = ImageDraw.Draw(tag)
            f1, f2 = fonte("Poppins-Bold.ttf", 26), fonte("Poppins-Bold.ttf", 38)
            antes = reais(d["ref"])
            w2, cxt = td.textlength(antes, font=f2), tag.width * 0.45
            td.text((cxt - td.textlength("antes", font=f1) / 2, tag.height * 0.16), "antes", font=f1, fill=FUNDO)
            td.text((cxt - w2 / 2, tag.height * 0.40), antes, font=f2, fill=FUNDO)
            ly = tag.height * 0.40 + 27
            td.line([(cxt - w2 / 2 - 4, ly), (cxt + w2 / 2 + 4, ly)], fill=(200, 46, 60), width=5)
            tag = _brilho(tag, ((t - PRECO_T) % 3.0 - 1.2) / 0.9)
            _colar(im, tag, gx + tag.width / 2, y + 108, -7 + 4 * math.sin((t - PRECO_T) * 2.2), e)
            dr = ImageDraw.Draw(im)
            px = gx + tag.width + 16
            # ⭐ 30/09 (arte do dono): a EXPLOSAO vermelha atras do preco — o heroi
            # ganha palco. Preco dourado com sombra escura pra ler no vermelho.
            asc, desc = fp.getmetrics()
            ex = _balao("loja_explosao", int((asc + desc) * 0.98))   # 01/10: era 1.1 e pisava na capsula
            larg_ex = int(pw + 120)
            ex = ex.resize((larg_ex, ex.height))
            # ⭐ 30/09 (premium, itens 4 e 6): o numero ROLA do "antes" ate' o de
            # hoje em ROLA_S — a queda que medimos, acontecendo na frente de quem
            # ve. SO' DEPOIS estouram a explosao, a pilula e o confete.
            rola = ease((t - PRECO_T) / ROLA_S)
            festa_p = ease((t - PRECO_T - ROLA_S) / 0.3)
            valor = d["ref"] + (d["agora"] - d["ref"]) * rola
            mostra = preco if rola >= 1 else reais(valor)
            ex = _brilho(ex, ((t - PRECO_T - ROLA_S) % 3.0) / 0.9)
            _colar(im, ex, px + pw / 2, y + 36 + (asc + desc) / 2 + 6, 2 * math.sin((t - PRECO_T) * 3), festa_p)
            dr = ImageDraw.Draw(im)
            dr.text((px + 5, y + 41), mostra, font=fp, fill=(60, 8, 12))
            dr.text((px, y + 36), mostra, font=fp, fill=OURO if rola >= 1 else BRANCO)
            fb = fonte("Poppins-Bold.ttf", 36)
            badge = f"-{round(d['queda'] * 100)}%"
            bw = dr.textlength(badge, font=fb)
            bx = px + pw - bw - 10
            # ⭐ 30/09 (arte do dono): a PILULA de balao vermelha carrega o -N%
            pil = _balao("pilula_desconto", 110).copy()
            pd = ImageDraw.Draw(pil)
            fb2 = _caber(pd, badge, "Anton-Regular.ttf", 64, int(pil.width * 0.55), 30)
            bx0, by0, bx1, by1 = pd.textbbox((0, 0), badge, font=fb2)
            px2 = pil.width * 0.45 - (bx0 + bx1) / 2          # centro do miolo liso
            py2 = pil.height * 0.60 - (by0 + by1) / 2         # (a pilula sobe pra direita)
            pd.text((px2 + 3, py2 + 3), badge, font=fb2, fill=(70, 5, 10))
            pd.text((px2, py2), badge, font=fb2, fill=BRANCO)
            _colar(im, pil, bx + bw / 2, y + 16, 0, festa_p)
            dr = ImageDraw.Draw(im)
            nota = f"“antes” = preço mais comum nos últimos {d['dias']} dias"
            _confete(im, t - PRECO_T - ROLA_S, int(str(d.get("id") or "7")[-6:]), W / 2, y + 100)
            dr = ImageDraw.Draw(im)
        elif d.get("provada"):
            antes = f"antes {reais(d['ref'])}"
            fb = fonte("Poppins-Bold.ttf", 36)
            badge = f"-{round(d['queda'] * 100)}%"
            aw, bw = dr.textlength(antes, font=fa), dr.textlength(badge, font=fb)
            x = (W - (aw + 36 + bw + 36)) / 2          # antes + selo, centrados JUNTOS
            dr.text((x, y), antes, font=fa, fill=CINZA)
            dr.line([(x, y + 28), (x + aw, y + 28)], fill=CINZA, width=4)
            bx = x + aw + 36
            pilula(dr, bx - 18, y - 2, bx + bw + 18, y + 50, (200, 46, 60))
            dr.text((bx, y + 1), badge, font=fb, fill=BRANCO)
            nota = f"“antes” = preço mais comum nos últimos {d['dias']} dias"
            centro(dr, y + 36, preco, fp, OURO)
        else:
            centro(dr, y, "preço de hoje", fa, CINZA)
            nota = "sem desconto inventado: é o preço da loja agora"
            centro(dr, y + 36, preco, fp, OURO)
    return im

def narracao(d: dict, destino: Path) -> None:
    import edge_tts
    from engine import numeros
    r, a = d["ref"], d["agora"]
    hoje = f"{int(a)} reais e {round((a - int(a)) * 100)} centavos"
    abre = (d["gancho"].capitalize() + ". ") if d.get("gancho") else ""
    # ⭐ 30/09/2026 (dono: "a dublagem esta' horrivel"): roteiro na ordem do
    # acervo (gancho -> prova -> oferta, FTA "How This Funnel Sold 100,000
    # Books", DEMONSTRADO), frase curta de conversa, e SO' o que a serie prova.
    # ⭐ ENTONACAO DE VENDA (dono, 30/09: "entonacao propria para vendas", +acervo).
    # Cada parte com o seu ritmo: acelerar na emocao, PAUSAR, desacelerar no
    # ponto importante (FTA Jeremy Miner, AFIRMADO); 135-185 palavras/min
    # (FTA sGakuNs9mT4); voz de IA um pouco acima de 1x soa mais natural
    # (roboverse987, DEMONSTRADO). (texto, velocidade edge-tts, pausa depois s)
    if d.get("provada"):
        queda = round(float(d["queda"]) * 100)
        partes = [(f"{abre}Olha isso! {d['nome']} caiu {queda} por cento.", "+14%", 0.25),
                  (f"Eu acompanho o preço dele há {d['dias']} dias. O normal é {int(r)} reais.", "+6%", 0.40),
                  (f"Hoje... tá {hoje}.", "-4%", 0.35),
                  ("Comenta QUERO aqui embaixo... o link tá na bio!", "+12%", 0.0)]
    else:
        partes = [(f"{abre}Olha isso! {d['nome']}.", "+14%", 0.25),
                  (f"Hoje... tá {hoje}.", "-4%", 0.35),
                  ("Comenta QUERO aqui embaixo... o link tá na bio!", "+12%", 0.0)]
    partes = d.get("partes") or partes        # roteiro pronto (teaser da inauguracao)
    txt = " ".join(p[0] for p in partes)
    # Mesma voz dos canais de corte: edge-tts -> ChatterboxVC com o timbre da
    # amostra (motor D do engine/voz_clonada), uma parte por vez. Sem amostra ou
    # sem o modelo, volta pra voz simples — video sem voz nao sai.
    amostra = Path(os.environ.get("AMOSTRA_VOZ_OFERTA") or "vozes/bryan_amostra.wav")
    if amostra.exists():
        from engine import voz_clonada
        pedacos, ok = [], True
        for k, (frase, vel, pausa) in enumerate(partes):
            wav = destino.with_name(f"parte{k}.wav")
            if not voz_clonada._falar_d(frase, wav, amostra, vel):
                ok = False
                break
            pedacos.append((wav, pausa))
        if ok:
            lista = destino.with_name("partes.txt")
            linhas = []
            for k, (wav, pausa) in enumerate(pedacos):
                linhas.append(f"file '{wav.as_posix()}'")
                if pausa:
                    sil = destino.with_name(f"sil{k}.wav")
                    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                                    "anullsrc=r=24000:cl=mono", "-t", str(pausa), str(sil)], check=True)
                    linhas.append(f"file '{sil.as_posix()}'")
            lista.write_text("\n".join(linhas), encoding="utf-8")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                            "-ar", "24000", "-ac", "1",
                            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", str(destino)], check=True)
            return
        print("  [!] voz clonada falhou — uso a voz simples", flush=True)
    asyncio.run(edge_tts.Communicate(numeros.por_extenso(txt), voice=VOZ, rate="+4%").save(str(destino)))


SONS = os.environ.get("SONS_OFERTA", "1") != "0"


def sons_filtro(ent: str, sai: str) -> str:
    """01/10/2026 (dono: "testar com 2 sons"; +acervo: efeito curto da' ritmo,
    mas pouco e baixo pra nao competir com a voz). SO' DOIS, sintetizados aqui
    (livres de direito, sem arquivo de terceiro):
      DING quando o preco para no valor de hoje (PRECO_T + ROLA_S)
      ESTOURO curto do confete, logo depois.
    SONS_OFERTA=0 desliga (pro teste com/sem)."""
    if not SONS:
        return f"[{ent}]anull[{sai}]"
    ms = int((PRECO_T + ROLA_S) * 1000)
    ding = ("aevalsrc='0.55*sin(2*PI*1568*t)*exp(-5*t)+0.35*sin(2*PI*2349*t)*exp(-7*t)"
            "+0.2*sin(2*PI*3136*t)*exp(-9*t)':s=44100:d=0.9,aformat=channel_layouts=stereo,"
            f"volume=0.45,adelay={ms}|{ms}[ding]")
    m2 = ms + 60
    estouro = (f"anoisesrc=d=0.35:c=pink:a=0.9:r=44100,highpass=f=1800,afade=t=out:st=0.02:d=0.33,"
               f"aformat=channel_layouts=stereo,volume=0.35,adelay={m2}|{m2}[est]")
    return f"{ding};{estouro};[{ent}][ding][est]amix=inputs=3:duration=first:normalize=0[{sai}]"


def _leitor_demo(url: str, tmp: Path):
    """Quadros 820x820 do video do vendedor (os DEMO_S primeiros segundos)."""
    if Path(url).exists():             # trecho ja' baixado (ex.: demo_youtube)
        arq = Path(url)
    else:
        arq = tmp / "demo.mp4"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        arq.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    lado = 820
    # a maioria dos videos de vendedor abre com 1-2 s de logo: pula quando da'
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True)
    try:
        dur = float(r.stdout.strip())
    except ValueError:
        dur = 0.0
    pulo = "3" if dur >= DEMO_S + 4 else "0"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", pulo, "-i", str(arq), "-t", str(DEMO_S), "-an",
                          "-vf", f"fps={FPS},scale={lado}:{lado}:force_original_aspect_ratio=increase,"
                                 f"crop={lado}:{lado}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    ultimo = None
    while True:
        b = p.stdout.read(lado * lado * 3)
        if len(b) < lado * lado * 3:
            break
        ultimo = Image.frombytes("RGB", (lado, lado), b)
        yield ultimo
    while True:               # video curto: segura o ultimo quadro
        yield ultimo


def gerar(pid: str, saida: Path, canal: str | None = None, numero: int | None = None,
          exigir_queda: bool = True, gancho: str = "", demo_arquivo: Path | None = None) -> dict:
    d = dados(pid, exigir_queda)
    d["gancho"] = gancho.upper()
    if demo_arquivo and Path(demo_arquivo).exists():
        d["video"] = str(demo_arquivo)
    elif not d.get("video"):
        # ⭐ item 16 (30/09/2026): trecho de demo que o PC tirou do YouTube,
        # conferido pelo Gemini contra a foto do anuncio (mesmo_produto >= 9),
        # e subiu pro Drive. Ver ferramentas/demo_local.py.
        demos = RAIZ / "estado" / "demos_drive.json"
        if demos.exists():
            reg = json.loads(demos.read_text(encoding="utf-8")).get(str(pid))
            if reg:
                d["video"] = reg["link"]
    if canal:
        d["marca"] = MARCAS.get(canal, d["marca"])
        d["numero"] = numero or proximo_numero(canal)
    # ⭐ semana de inauguracao: a festa entra sozinha e sai sozinha no dia 8
    from datetime import date as _date
    d.setdefault("festa", _date.today().isoformat() <= INAUGURACAO_ATE)
    d.setdefault("id", pid)
    tmp = Path(tempfile.mkdtemp())
    cartoes = [cartao(baixar(u), 820) for u in ordenar_fotos(d["imagens"])]
    voz = tmp / "voz.mp3"
    narracao(d, voz)
    fundo = base_fundo()
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(voz),
                          "-filter_complex", "[1:a]adelay=600|600,apad[v1];" + sons_filtro("v1", "a"),
                          "-map", "0:v", "-map", "[a]",
                          "-t", str(DUR), "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                          "-movflags", "+faststart", str(saida)], stdin=subprocess.PIPE)
    demo = None
    if d.get("video"):
        try:
            demo = _leitor_demo(d["video"], tmp)
            primeiro = next(demo)
            if primeiro is None:
                demo = None
        except Exception as e:  # noqa: BLE001 — sem demo, volta pra foto
            print(f"  [!] video do vendedor indisponivel ({type(e).__name__}); uso as fotos")
            demo = None
    for i in range(int(DUR * FPS)):
        t = i / FPS
        dq = next(demo) if (demo is not None and t < DEMO_S) else None
        p.stdin.write(quadro(t, d, fundo, cartoes, dq).tobytes())
    p.stdin.close()
    p.wait()
    d["comentario"] = comentario_fixado(d)
    d["legenda"] = legenda_post(d)
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--saida", type=Path, required=True)
    ap.add_argument("--canal")
    ap.add_argument("--sem-queda", action="store_true", help="mostra so' o preco de hoje")
    ap.add_argument("--gancho", default="")
    ap.add_argument("--demo", type=Path, help="trecho de demonstracao ja' baixado")
    a = ap.parse_args()
    print(gerar(a.id, a.saida, a.canal, exigir_queda=not a.sem_queda, gancho=a.gancho,
                demo_arquivo=a.demo))
