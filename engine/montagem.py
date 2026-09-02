# -*- coding: utf-8 -*-
"""Monta video vertical a partir de FOTOS de produto — a peca que faltava.

## POR QUE ELE EXISTE

O motor inteiro CORTA video que ja' existe: recorta um trecho de podcast, de
treino, de receita. Produto de marketplace quase nunca tem video — tem FOTO,
e as vezes um clipe curto do vendedor.

Sem isto, o pipeline de afiliado nao sai do lugar: haveria dado de produto,
narracao, legenda e publicacao prontos, e nada pra mostrar na tela.

⚠️ E' A UNICA PECA QUE NAO DEPENDE DA CREDENCIAL. O radar de produto espera a
aprovacao do AliExpress (em analise em 02/09/2026); a montagem so' precisa de
imagem, que vem de qualquer lugar. Por isso foi construida primeiro.

## O QUE ELE REAPROVEITA, E O QUE E' NOVO

    reaproveita   voz_clonada (narracao), legendas, midia.roda com timeout,
                  a fonte e o desenho de caixa do render, o encoder
    novo          transformar UMA FOTO em cena de video com movimento

## ⚠️ FOTO PARADA NAO E' VIDEO

Uma imagem estatica por 8 segundos e' o formato que o TikTok e o YouTube
tratam como slideshow, e slideshow entrega mal. Cada cena aqui ganha
movimento continuo (zoom lento com deriva), o que faz o quadro nunca repetir.

O mesmo raciocinio do `_ken_burns` do render, e pelo mesmo motivo declarado
la': "e' edicao de verdade em cima do material — importa pra nao cair em
'conteudo reaproveitado sem transformacao'". Aqui pesa ainda mais, porque a
foto e' literalmente do vendedor.

## ⚠️ A DURACAO DE CADA CENA SEGUE A NARRACAO, NUNCA O CONTRARIO

Fixar a cena em N segundos e esticar a fala deixa a locucao corrida ou com
buraco — o mesmo defeito que ja' custou caro na dublagem (ver o teto de 1,6x
no voz_clonada). Aqui a fala manda: a cena dura o que a frase dela durou.
"""
from __future__ import annotations

import math
from pathlib import Path

from . import midia

# 1080x1920. Nao vem do config de proposito: este modulo tem de rodar em
# teste sem carregar a configuracao inteira do motor.
LARGURA, ALTURA = 1080, 1920

# Quanto a cena aproxima do inicio ao fim. 8% e' perceptivel sem parecer
# que a camera esta' correndo — acima de ~15% a foto perde nitidez nas
# bordas, porque nao ha' pixel novo pra revelar.
ZOOM_TOTAL = 0.08

# Piso e teto por cena.
#
# ⚠️ O PISO EXISTE PORQUE FRASE CURTA VIRA CORTE SECO. "Custa vinte reais"
# dura 1,4s; sem piso, o produto apareceria e sumiria antes de a pessoa ler o
# preco.
#
# ⚠️ E O TETO PORQUE FOTO PARADA CANSA. Passando de ~9s numa unica imagem, a
# retencao cai — e retencao e' o gargalo MEDIDO deste projeto.
CENA_MIN_S = 2.5
CENA_MAX_S = 9.0


def _cena(imagem: Path, segundos: float, destino: Path,
          fps: int = 30) -> Path:
    """Uma foto vira uma cena com movimento.

    ⚠️ O `zoompan` conta em FRAMES DE SAIDA (`on`), nao em segundos, e uma
    imagem estatica tem UM frame de entrada: sem `-loop 1` e `-t`, ele produz
    um unico quadro e a cena sai com 1/30 de segundo. Foi o erro obvio de
    escrever, e o motivo de a duracao entrar em dois lugares.

    A deriva lateral (`x` variando com `on`) existe porque zoom puro no centro
    parece defeito de compressao; deslocar junto le' como movimento de camera.
    """
    total = max(1, int(round(segundos * fps)))
    z = f"1+{ZOOM_TOTAL:.4f}*on/{total}"
    # deriva de meio ciclo: sai do centro e volta, sem quina no fim
    dx = f"(iw-iw/zoom)/2+(iw-iw/zoom)*0.06*sin(PI*on/{total})"
    filtro = (
        # cobre o quadro inteiro e corta o excesso — foto de produto costuma
        # ser quadrada, e barra preta em video vertical derruba retencao
        f"scale={LARGURA * 2}:{ALTURA * 2}:force_original_aspect_ratio=increase,"
        f"crop={LARGURA * 2}:{ALTURA * 2},"
        f"zoompan=z='{z}':d={total}:x='{dx}':y='(ih-ih/zoom)/2'"
        f":s={LARGURA}x{ALTURA}:fps={fps},"
        f"setsar=1"
    )
    midia.roda(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(imagem),
                "-t", f"{segundos:.3f}", "-vf", filtro,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-an", str(destino)])
    return destino


def duracao_da_cena(segundos_da_fala: float) -> float:
    """Quanto a cena dura, dado o tempo da frase que a acompanha.

    A fala manda; o piso e o teto so' evitam os dois extremos ruins.
    """
    if not segundos_da_fala or segundos_da_fala <= 0:
        return CENA_MIN_S
    return max(CENA_MIN_S, min(CENA_MAX_S, float(segundos_da_fala)))


def _placa(texto: str, destino: Path) -> Path | None:
    """Caixa branca com o texto — o preco e o nome do produto sobre a foto.

    ⚠️ Falha ABERTA: sem Pillow ou sem a fonte, devolve None e a cena sai SEM
    a placa. Video sem preco na tela e' pior; video que nao renderiza e' muito
    pior.
    """
    if not texto:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    fonte_arq = Path(__file__).resolve().parent / "fontes" / "Poppins-Bold.ttf"
    if not fonte_arq.exists():
        return None
    corpo = 64
    fonte = ImageFont.truetype(str(fonte_arq), corpo)
    img = Image.new("RGBA", (LARGURA, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    caixa = d.textbbox((0, 0), texto, font=fonte)
    lt, at = caixa[2] - caixa[0], caixa[3] - caixa[1]
    px, py = 34, 20
    x0 = (LARGURA - lt) // 2 - px
    d.rounded_rectangle([x0, 0, x0 + lt + px * 2, at + py * 2], radius=18,
                        fill=(255, 255, 255, 240))
    d.text((x0 + px - caixa[0], py - caixa[1]), texto, font=fonte,
           fill=(15, 15, 16, 255))
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino)
    return destino


def montar(cenas: list[dict], destino: Path, trabalho: Path,
           audio: Path | None = None) -> Path:
    """Junta as cenas num video vertical, com o audio da narracao por cima.

    Cada cena: {"imagem": Path, "segundos": float, "placa": str}

    ⚠️ CENA SEM IMAGEM NAO DERRUBA A MONTAGEM. Produto sem foto acontece —
    link quebrado, imagem removida pelo vendedor. A cena e' PULADA e as outras
    seguem. Um video com dois produtos e' melhor que nenhum video.
    """
    trabalho.mkdir(parents=True, exist_ok=True)
    partes: list[Path] = []
    for i, c in enumerate(cenas):
        img = c.get("imagem")
        if not img or not Path(img).exists():
            print(f"   [!] cena {i + 1} sem imagem — pulada", flush=True)
            continue
        seg = duracao_da_cena(c.get("segundos"))
        bruta = trabalho / f"cena_{i:02d}.mp4"
        try:
            _cena(Path(img), seg, bruta)
        except Exception as e:
            print(f"   [!] cena {i + 1} falhou ({str(e)[:60]}) — pulada",
                  flush=True)
            continue
        placa = _placa(str(c.get("placa") or ""), trabalho / f"placa_{i:02d}.png")
        if placa:
            comp = trabalho / f"cena_{i:02d}_p.mp4"
            # a placa entra DEPOIS do zoompan: antes, ela seria ampliada e
            # cortada junto com a foto (mesma nota do render.vertical)
            midia.roda(["ffmpeg", "-y", "-v", "error", "-i", str(bruta),
                        "-i", str(placa), "-filter_complex",
                        f"[0:v][1:v]overlay=0:{int(ALTURA * 0.16)}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-an", str(comp)])
            bruta = comp
        partes.append(bruta)

    if not partes:
        raise RuntimeError("nenhuma cena com imagem — nada a montar")

    lista = trabalho / "cenas.txt"
    lista.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in partes) + "\n",
        encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
           "-i", str(lista)]
    if audio and Path(audio).exists():
        # ⚠️ `-shortest` E' TETO, nao ajuste: se a narracao for mais longa que
        # as cenas, o video termina junto com a imagem e a fala e' cortada. E'
        # por isso que `duracao_da_cena` segue a fala — a ordem certa e' a
        # cena obedecer ao audio, nao o audio ser truncado pela cena.
        cmd += ["-i", str(audio), "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", str(destino)]
    midia.roda(cmd)
    return destino
