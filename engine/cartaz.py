# -*- coding: utf-8 -*-
"""O cartaz do produto: uma imagem 9x16 montada por nos, a partir da foto da loja.

    python -m engine.cartaz --ensaio        monta um exemplo e salva em saida/

## POR QUE EXISTE

Medido em 14/09/2026 e repetido em 15/09: o gargalo do achadinho nao e' achar o
produto, e' TER IMAGEM DELE. A foto da loja e' quadrada, vem com marca d'agua de
vendedor, texto chines e proporcao errada pro TikTok e pro Telegram. O
Achadinho Make recomenda um serum do qual nao temos uma unica imagem nossa.

Isto nao gera imagem nova — GERAR e' o caminho que reprovou nove provedores em
15/09 (ver o handoff daquele dia). Aqui a foto do anuncio e' a mesma; o que se
monta em volta dela e' nosso. Por isso nao ha' guarda de fidelidade neste
modulo: nao existe o modo de falha que ela vigia. O produto nao pode virar outro
produto porque ninguem o redesenhou.

## ⛔ O SELO DE QUEDA NAO ACEITA UM NUMERO PRONTO

Em 15/09/2026 dez produtos anunciaram desconto que nao existia: o registro em
disco guardava uma queda calculada por historico sujo, e a pagina lia o campo.
O conserto la' foi RECALCULAR da serie consolidada em vez de ler.

Aqui a mesma familia de defeito seria pior, porque um cartaz e' uma imagem: ela
viaja pro Telegram, pro post, pro print de alguem, e nao se recalcula depois de
salva. Entao este modulo NAO recebe `queda`. Ele recebe os dois precos e deriva
o selo deles:

    preco=89.90, antes=129.90   ->  selo "-31%", preco cortado visivel
    preco=89.90, antes=89.90    ->  sem selo, sem preco cortado
    preco=89.90, antes=None     ->  sem selo, sem preco cortado

⭐ Um numero, uma fonte. O selo nao tem como discordar dos dois precos impressos
na MESMA imagem, logo abaixo dele, porque saiu deles. Quem quiser aplicar a
regra do motor (`desconto_honesto`, minimo de serie, dia consolidado) aplica
ANTES, decidindo qual `antes` passar — ou nenhum.

## ⚠️ A FONTE VIAJA NO REPO, E ISSO NAO E' DETALHE

O rascunho desta montagem pedia `segoeuib.ttf` ao sistema, com
`ImageFont.load_default()` de reserva. Na nuvem, que e' Linux, a Segoe nao
existe: a reserva entra sozinha, o cartaz sai com fonte bitmap minuscula e
NADA levanta erro. Falha silenciosa, so' visivel na imagem publicada.

Por isso aqui a fonte e' a `Poppins-Bold.ttf` que ja' mora em `engine/fontes/`
(a mesma do card de titulo, `engine/render.py`) e a ausencia dela e' ERRO, nao
reserva. Mesma regra do peso do recorte: se a operacao mudar de maquina, tem de
continuar funcionando.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
FONTE = Path(__file__).resolve().parent / "fontes" / "Poppins-Bold.ttf"

TAMANHO = (1080, 1920)          # 9x16, o formato do TikTok e do Telegram
FUNDO_A = (0x17, 0x16, 0x1D)    # o mesmo par escuro da pagina
FUNDO_B = (0x2A, 0x24, 0x3B)
CLARO = (0xF2, 0xEF, 0xF4)
OURO = (0xFF, 0xD9, 0x8A)       # preco: a mesma cor de destaque do catalogo
CINZA = (0xA7, 0xA0, 0xB2)      # preco antigo, cortado
VERDE = (0x16, 0xA3, 0x4A)      # selo de queda

# ⚠️ Abaixo disto o selo nao vai ao ar. Nao e' estetica: 1% de queda com o selo
# verde no canto grita "promocao" do tamanho que grita 40%, e a imagem nao tem
# como se explicar depois. Mesmo piso do `>= 5%` que a pagina usa pra contar
# produto "em queda".
QUEDA_MINIMA = 5.0


def _fonte(tam: int) -> ImageFont.FreeTypeFont:
    if not FONTE.exists():
        raise FileNotFoundError(
            f"fonte ausente: {FONTE}. Ela e' versionada com o repo — se sumiu, "
            "foi filtro de .gitignore ou clone parcial. ⛔ Nao trocar por fonte "
            "do sistema: na nuvem ela nao existe e o cartaz sai com a fonte de "
            "reserva, minusculo, sem levantar erro.")
    return ImageFont.truetype(str(FONTE), tam)


def _gradiente(w: int, h: int) -> Image.Image:
    coluna = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(coluna)
    for y in range(h):
        t = y / max(h - 1, 1)
        d.point((0, y), tuple(int(FUNDO_A[i] + (FUNDO_B[i] - FUNDO_A[i]) * t)
                              for i in range(3)))
    return coluna.resize((w, h), Image.BILINEAR)


def _cantos(im: Image.Image, raio: int) -> Image.Image:
    mascara = Image.new("L", im.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        [0, 0, im.size[0] - 1, im.size[1] - 1], raio, fill=255)
    im = im.convert("RGBA")
    im.putalpha(mascara)
    return im


def _quebrar(d: ImageDraw.ImageDraw, texto: str, f, largura: float,
             linhas_max: int) -> list[str]:
    """Quebra o nome em linhas, e CORTA o que nao couber.

    ⚠️ O corte com reticencias e' obrigatorio, nao enfeite. Titulo de AliExpress
    passa de 100 caracteres com frequencia ("Organizador de maquiagem giratorio
    360 graus com 7 compartimentos a prova de poeira..."). Sem corte a ultima
    linha sai por fora do cartaz — foi um dos nove defeitos vistos no iPhone em
    15/09, `nowrap` sem `overflow: hidden`, o mesmo erro em outro meio.
    """
    linhas: list[str] = []
    atual = ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if d.textlength(teste, font=f) <= largura:
            atual = teste
            continue
        if atual:
            linhas.append(atual)
        atual = palavra
        if len(linhas) == linhas_max:
            break
    if atual and len(linhas) < linhas_max:
        linhas.append(atual)
    if not linhas:
        return []
    sobrou = len(" ".join(linhas).split()) < len(texto.split())
    if sobrou:
        ultima = linhas[-1]
        while ultima and d.textlength(ultima + "...", font=f) > largura:
            ultima = ultima[:-1].rstrip()
        linhas[-1] = ultima + "..."
    return linhas


def _reais(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def queda_do_par(preco: float, antes: float | None) -> float:
    """Quanto o par de precos diz que caiu. Sem par, ZERO.

    ⛔ Falha FECHADA, do lado que nao mente: `antes` ausente, zerado, menor ou
    igual ao preco de hoje devolve 0.0, e 0.0 apaga o selo E o preco cortado.
    Nao existe caminho neste modulo que desenhe desconto sem os dois numeros
    que o sustentam.
    """
    if not antes or not preco or antes <= preco:
        return 0.0
    return (antes - preco) / antes * 100


def montar(foto: Image.Image, nome: str, preco: float,
           antes: float | None = None, *, tamanho=TAMANHO) -> Image.Image:
    """Monta o cartaz. `foto` e' a imagem da loja, ja' baixada."""
    largura, altura = tamanho
    tela = _gradiente(largura, altura)

    # ⭐ O BRILHO COBRE A PECA INTEIRA, e isso e' correcao de 15/09/2026, vinda
    # de ver o post no Telegram de verdade. A primeira versao punha a elipse so'
    # atras do produto ([0.05, 0.14, 0.95, 0.62]), entao o topo e o rodape
    # saiam CHAPADOS — medido nos cantos do JPEG, 13 de 255 em cima e 23
    # embaixo, contra 90 de media da peca. Na tela do celular isso le' como
    # "faltou alguma coisa ali".
    #
    # ⚠️ A INTENSIDADE E' ESCOLHA DO BRYAN, entre tres medidas (cantos em 38,
    # 47 e 59). Ficou a do meio. Nao subir mais: o nome do produto e o preco
    # antigo riscado sao claros sobre fundo escuro, e na variante forte o
    # riscado — que e' cinza de proposito — comeca a competir com o fundo.
    halo = Image.new("RGB", (largura, altura), (0, 0, 0))
    ImageDraw.Draw(halo).ellipse(
        [-largura * 0.30, -altura * 0.12, largura * 1.30, altura * 1.12],
        fill=(70, 60, 95))
    tela.paste(Image.blend(tela, halo.filter(ImageFilter.GaussianBlur(200)), 0.55))

    # o produto, quadrado e no centro
    lado = int(largura * 0.82)
    p = foto.convert("RGB")
    c = min(p.size)
    p = p.crop(((p.width - c) // 2, (p.height - c) // 2,
                (p.width + c) // 2, (p.height + c) // 2))
    p = p.resize((lado, lado), Image.LANCZOS)
    # ⚠️ Realce de tela, nao de conteudo: nitidez, cor e contraste em dose baixa
    # compensam o JPEG de catalogo. Nao mexem no que o produto E' — quem mexe
    # nisso e' modelo de imagem, e esse caminho esta' fechado desde 15/09.
    p = ImageEnhance.Sharpness(p).enhance(1.35)
    p = ImageEnhance.Color(p).enhance(1.08)
    p = ImageEnhance.Contrast(p).enhance(1.06)
    p = _cantos(p, 44)

    x, y = (largura - lado) // 2, int(altura * 0.17)
    sombra = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle(
        [x + 10, y + 26, x + lado + 10, y + lado + 26], 44, fill=(0, 0, 0, 150))
    tela.paste(Image.alpha_composite(
        tela.convert("RGBA"), sombra.filter(ImageFilter.GaussianBlur(28))).convert("RGB"))
    tela.paste(p, (x, y), p)

    d = ImageDraw.Draw(tela)
    queda = queda_do_par(preco, antes)
    mostra_queda = queda >= QUEDA_MINIMA

    if mostra_queda:
        f = _fonte(46)
        t = f"-{queda:.0f}%"
        tw = d.textlength(t, font=f)
        d.rounded_rectangle([x + 22, y + 22, x + 22 + tw + 56, y + 22 + 78],
                            26, fill=VERDE)
        d.text((x + 22 + 28, y + 22 + 14), t, font=f, fill=(255, 255, 255))

    fn = _fonte(62)
    yy = y + lado + 70
    for linha in _quebrar(d, nome, fn, largura * 0.84, 2):
        d.text(((largura - d.textlength(linha, font=fn)) / 2, yy), linha,
               font=fn, fill=CLARO)
        yy += 78

    yy += 26
    if mostra_queda:
        fa = _fonte(50)
        texto_antes = _reais(antes)
        la = d.textlength(texto_antes, font=fa)
        d.text(((largura - la) / 2, yy), texto_antes, font=fa, fill=CINZA)
        d.line([(largura - la) / 2 - 8, yy + 34, (largura + la) / 2 + 8, yy + 34],
               fill=CINZA, width=4)
        yy += 66

    fp = _fonte(126)
    texto_preco = _reais(preco)
    d.text(((largura - d.textlength(texto_preco, font=fp)) / 2, yy),
           texto_preco, font=fp, fill=OURO)
    return tela


# ⭐ O CARTAZ CLARO (24/09/2026) — a marca virou "so' fundo branco" e o canal
# destoava: roxo-escuro, 9x16 (um paredao no feed do Telegram), nome cru do
# AliExpress cortado no meio. Aqui: branco, 4x5 (o formato que o feed mostra
# inteiro sem rolar), nome curto e a logo no topo — o post se reconhece como
# Achadinho Total antes de ser lido.
#
# ⚠️ O OURO SOBRE BRANCO E' O ESCURO (#A8740F), nao o do tema escuro: o #FFD98A
# some no branco. Mesmo par da pagina clara (--ouro).
TAMANHO_CLARO = (1080, 1350)
BRANCO = (0xFF, 0xFF, 0xFF)
TINTA = (0x16, 0x15, 0x1C)
OURO_ESCURO = (0xA8, 0x74, 0x0F)
CINZA_CLARO = (0x8A, 0x86, 0x94)
BORDA = (0xEC, 0xE9, 0xF1)
LOGO = RAIZ / "paginas" / "logo_achadinho_mestre.png"


def montar_claro(foto: Image.Image, nome: str, preco: float,
                 antes: float | None = None, *, rodape: str = "") -> Image.Image:
    """O cartaz do canal no padrao da marca: branco, 4x5, logo no topo."""
    largura, altura = TAMANHO_CLARO
    tela = Image.new("RGB", TAMANHO_CLARO, BRANCO)
    d = ImageDraw.Draw(tela)

    # topo: logo + nome da marca, discretos
    fm = _fonte(40)
    marca = "Achadinho Total"
    lado_logo = 72
    wm = d.textlength(marca, font=fm)
    x0 = (largura - (lado_logo + 18 + wm)) / 2
    if LOGO.exists():
        lg = Image.open(LOGO).convert("RGBA").resize((lado_logo, lado_logo), Image.LANCZOS)
        tela.paste(lg, (int(x0), 44), lg)
    d.text((x0 + lado_logo + 18, 44 + (lado_logo - 48) / 2), marca, font=fm, fill=TINTA)

    # a foto: quadrada, borda fina e sombra leve — a foto de loja quase sempre
    # tem fundo branco, e sem borda ela se dissolve na pagina
    lado = 800
    p = foto.convert("RGB")
    c = min(p.size)
    p = p.crop(((p.width - c) // 2, (p.height - c) // 2,
                (p.width + c) // 2, (p.height + c) // 2))
    p = p.resize((lado, lado), Image.LANCZOS)
    p = ImageEnhance.Sharpness(p).enhance(1.25)
    x, y = (largura - lado) // 2, 150
    sombra = Image.new("RGBA", TAMANHO_CLARO, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle(
        [x, y + 14, x + lado, y + lado + 14], 40, fill=(40, 30, 60, 46))
    tela = Image.alpha_composite(tela.convert("RGBA"),
                                 sombra.filter(ImageFilter.GaussianBlur(24))).convert("RGB")
    tela.paste(_cantos(p, 40), (x, y), _cantos(p, 40))
    d = ImageDraw.Draw(tela)
    d.rounded_rectangle([x, y, x + lado, y + lado], 40, outline=BORDA, width=3)

    queda = queda_do_par(preco, antes)
    mostra_queda = queda >= QUEDA_MINIMA
    if mostra_queda:
        f = _fonte(44)
        t = f"-{queda:.0f}%"
        tw = d.textlength(t, font=f)
        d.rounded_rectangle([x + 24, y + 24, x + 24 + tw + 52, y + 24 + 74],
                            24, fill=VERDE)
        d.text((x + 24 + 26, y + 24 + 12), t, font=f, fill=(255, 255, 255))

    fn = _fonte(50)
    yy = y + lado + 34
    for linha in _quebrar(d, nome, fn, largura * 0.86, 2):
        d.text(((largura - d.textlength(linha, font=fn)) / 2, yy), linha,
               font=fn, fill=TINTA)
        yy += 64

    # preco (e o "de", riscado, AO LADO — em cima dele roubava altura do 4x5)
    fp = _fonte(104)
    tp = _reais(preco)
    wp = d.textlength(tp, font=fp)
    yy += 4
    if mostra_queda:
        fa = _fonte(44)
        ta = _reais(antes)
        wa = d.textlength(ta, font=fa)
        xt = (largura - (wa + 28 + wp)) / 2
        ya = yy + 50
        d.text((xt, ya), ta, font=fa, fill=CINZA_CLARO)
        d.line([xt - 6, ya + 30, xt + wa + 6, ya + 30], fill=CINZA_CLARO, width=4)
        d.text((xt + wa + 28, yy), tp, font=fp, fill=OURO_ESCURO)
    else:
        d.text(((largura - wp) / 2, yy), tp, font=fp, fill=OURO_ESCURO)

    if rodape:
        fr = _fonte(30)
        d.text(((largura - d.textlength(rodape, font=fr)) / 2, altura - 62),
               rodape, font=fr, fill=CINZA_CLARO)
    return tela


def _ensaio() -> None:
    import io
    import urllib.request

    saida = RAIZ / "saida"
    saida.mkdir(exist_ok=True)
    url = ("https://ae01.alicdn.com/kf/S0f0ca2a0c3a94e0aa2d6a3ad2e1b4c3dQ.jpg")
    try:
        bruto = urllib.request.urlopen(url, timeout=20).read()
        foto = Image.open(io.BytesIO(bruto))
    except Exception as e:                                  # pragma: no cover
        print(f"sem rede pra foto de exemplo ({e}); usando quadrado chapado")
        foto = Image.new("RGB", (800, 800), (0x3A, 0x36, 0x44))
    img = montar(foto, "Organizador de maquiagem giratório 360°", 89.90, 129.90)
    destino = saida / "cartaz_ensaio.jpg"
    img.save(destino, quality=92)
    img.resize((540, 960), Image.LANCZOS).save(saida / "cartaz_previa.jpg", quality=90)
    print(f"ok -> {destino}  {img.size}")


if __name__ == "__main__":                                  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ensaio", action="store_true", help="monta um exemplo")
    a = ap.parse_args()
    if a.ensaio:
        _ensaio()
    else:
        ap.print_help()
