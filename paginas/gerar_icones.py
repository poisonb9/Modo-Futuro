# -*- coding: utf-8 -*-
"""Deriva os dois icones do site a partir da logo mestre.

    python paginas/gerar_icones.py

Le' `logo_achadinho_mestre.png` (a lupa dourada ja' RECORTADA, com alfa de
verdade) e escreve os dois arquivos que o `publicar_bio._por_icone` copia pra
dentro de todo deploy.

## POR QUE EXISTE UM MESTRE, E POR QUE ELE E' GRANDE

Ate' 16/09/2026 os dois icones eram os UNICOS arquivos de logo do repo, ambos
em 180x180 — e nao havia de onde regerar. Pior: medido no dia, a lupa ocupava
**13,1%** da moldura de 180 px. Isso da' uma logo efetiva de ~73 pixels, e e'
essa a causa da baixa qualidade que o Bryan viu na tela, mais do que a origem.

⭐ O mestre e' a fonte unica. Qualquer tamanho novo (192 do Android, 512 do
manifest, avatar de canal) sai daqui por reducao, que e' barata e nitida.
Aumentar 180 px nao e' — e era o unico caminho que existia antes.

## ⛔ O FUNDO XADREZ NAO ERA TRANSPARENCIA

Os dois arquivos que o Bryan mandou chegaram em modo **RGB, sem canal alfa**:
o xadrez cinza estava PINTADO nos pixels. E nao dava pra tirar por cor — o
xadrez e' cinza e o aro da lupa e' CROMADO, cinza tambem; chave de cor comeria
metade do desenho.

O recorte saiu pela CONECTIVIDADE (fundo e' o que se alcanca a partir da borda
andando so' por pixel com cara de xadrez; o aro esta' cercado de dourado, entao
nao se chega nele sem atravessar cor). Medido na saida: raio entre 562 e 573 px
nas oito direcoes (2% de desvio — e' um circulo, nao um vazamento), 78,3% da
caixa opaco contra os 78,5% teoricos de um disco inscrito.

⚠️ E foi o arquivo PNG que serviu, nao o JPG. No JPG o recorte VAZOU: as
sombras escuras do cromado batem com o tom escuro do xadrez (1 contra 141), o
fundo se emendou com o objeto e a "logo" saiu com 91,2% da tela — a imagem
inteira. Com o PNG (tons 154 e 209) deu 64,1%, que e' o disco.
"""
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
MESTRE = AQUI / "logo_achadinho_mestre.png"

# ⚠️ A MESMA COR DE FUNDO DO ICONE ANTIGO (#17161D), medida nele antes de
# trocar. Icone de tela de inicio que muda de cor parece app trocado.
FUNDO_APP = (23, 22, 29)

# ⚠️ MARGENS DIFERENTES DE PROPOSITO.
#
#   favicon      quase sem margem: ele aparece num quadradinho de 16 px na aba,
#                e margem la' e' pixel jogado fora.
#   apple-touch  margem de folga: o iOS recorta o icone com cantos
#                arredondados POR CIMA do que a gente manda. Sem folga, o
#                arredondamento come o aro cromado.
MARGEM_FAVICON = 0.02
MARGEM_APP = 0.08


def _quadro(mestre: Image.Image, lado: int, margem: float,
            fundo: tuple[int, int, int] | None) -> Image.Image:
    """A logo reduzida e centralizada num quadrado de `lado`."""
    dentro = max(1, int(round(lado * (1 - 2 * margem))))
    # ⚠️ LANCZOS na reducao. O padrao do `resize` antigo do Pillow era
    # bilinear, e metal escovado com listra fina serrilha feio nele.
    peca = mestre.resize((dentro, dentro), Image.LANCZOS)
    if fundo is None:
        quadro = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    else:
        quadro = Image.new("RGBA", (lado, lado), fundo + (255,))
    canto = (lado - dentro) // 2
    quadro.paste(peca, (canto, canto), peca)
    return quadro


def main() -> None:
    if not MESTRE.exists():
        raise SystemExit(f"nao achei {MESTRE}")
    mestre = Image.open(MESTRE).convert("RGBA")
    if mestre.size[0] != mestre.size[1]:
        raise SystemExit(f"o mestre tem de ser quadrado: {mestre.size}")
    # ⛔ O MESTRE TEM DE TER ALFA DE VERDADE. Um PNG pode estar em modo RGBA e
    # ter o canal inteiro em 255 — que e' opaco, ou seja, xadrez pintado. Foi
    # exatamente isso que chegou, e sem esta guarda o recorte nao se prova.
    a, b = mestre.getchannel("A").getextrema()
    if a != 0 or b != 255:
        raise SystemExit(
            f"o mestre nao tem recorte: alfa vai de {a} a {b}, e tem de ir de "
            f"0 a 255. PNG opaco com xadrez pintado passa por 'transparente'.")

    # ⛔ FAVICON: fundo TRANSPARENTE. A aba do navegador tem fundo proprio
    # (claro ou escuro) e um quadrado escuro fixo vira mancha nela.
    fav = _quadro(mestre, 512, MARGEM_FAVICON, None)
    fav.save(AQUI / "icone_achadinho_favicon.png", optimize=True)

    # ⛔ APPLE-TOUCH: fundo OPACO, obrigatoriamente. O iOS NAO respeita alfa
    # aqui — ele compoe o icone sobre PRETO. Um PNG transparente viraria uma
    # lupa dourada flutuando num quadrado preto.
    app = _quadro(mestre, 180, MARGEM_APP, FUNDO_APP).convert("RGB")
    app.save(AQUI / "icone_achadinho_180.png", optimize=True)

    for nome in ("icone_achadinho_favicon.png", "icone_achadinho_180.png"):
        im = Image.open(AQUI / nome)
        ocupa = ""
        if "A" in im.mode:
            import numpy as np
            ocupa = "  logo em %.1f%% da moldura" % (
                100 * (np.asarray(im.getchannel("A")) > 128).mean())
        print(f"  {nome}  {im.size}  {im.mode}{ocupa}")


if __name__ == "__main__":
    main()
