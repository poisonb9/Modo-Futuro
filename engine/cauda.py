# -*- coding: utf-8 -*-
"""A cauda muda no fim do clipe — quando a narracao acaba e o video segue.

## O DEFEITO, E DE ONDE ELE VEM

`dublagem.gerar_trilha` e `voz_clonada.gerar_trilha` montam a trilha sobre uma
base de SILENCIO do tamanho do clipe inteiro (`anullsrc ... d=duracao_total`) e
posicionam cada frase no tempo dela. Isso e' o certo pra sincronia — e tem uma
consequencia: se a ultima frase acaba aos 48s num clipe de 62s, os 14s finais
sao silencio de verdade, nao "audio baixo".

⚠️ **NAO E' O MESMO CASO DO `montagem.py`.** La' o audio SOBRA e a imagem
acaba antes, e a ultima cena estica pra caber a fala. Aqui e' o inverso: a
imagem sobra e a fala acabou. Os dois vivem no mesmo motor e se confundem
facil na leitura.

E so' acontece com DUBLAGEM. Sem ela o audio que toca ate' o fim e' o
original, que nao e' mudo — por isso quem chama passa o `tem_dublagem`.

## POR QUE APARAR, E NAO PREENCHER

A audiencia sai entre 0:01 e 0:02 (18 posts, 08-09/09/2026). Quem chega ao fim
e' justamente quem ficou, e o que ele recebe hoje sao segundos sem voz. Aparar
e' a unica opcao que nao inventa conteudo: preencher com musica ou com o audio
original de volta seria uma decisao de estilo que ninguem mediu.

## ⚠️ O PISO DE DINHEIRO MANDA MAIS QUE A CAUDA

`config.DUR_MIN` (65s) e' REGRA DE DINHEIRO, nao estetica. Se aparar deixaria o
clipe abaixo dele, NAO se apara — o mesmo desfecho que a decupagem de silencios
ja' escolhe no `main.py`. Um clipe com cauda muda vale mais que um clipe
desmonetizado.

## ⚠️ O QUE ESTE MODULO NAO FAZ

Ele nao mede nada sozinho e nao chama ffmpeg. Devolve UM numero — ate' onde o
video deve ir — e quem renderiza aplica como teto de duracao. Assim o mesmo
calculo serve ao 9:16 e ao 16:9 sem os dois poderem divergir.
"""
from __future__ import annotations

# Quanto de silencio no fim e' tolerado antes de valer a pena aparar.
#
# ⚠️ NAO E' ZERO DE PROPOSITO. Fim exato na ultima silaba corta a respiracao e
# a cauda de reverb do TTS, e o corte fica audivel. Abaixo deste valor a sobra
# le' como fechamento, nao como falha.
CAUDA_MAX_S = 1.5

# O que fica DEPOIS da ultima palavra quando a gente apara. Segura o decaimento
# do audio e deixa a ultima legenda respirar na tela antes de o video acabar.
CAUDA_MARGEM_S = 0.6


def fim_da_fala(palavras: list[dict] | None) -> float:
    """Onde a ultima palavra acaba, em segundos relativos ao clipe.

    Recebe a lista `[{palavra, inicio, fim}]` — a MESMA que vira legenda. E'
    de proposito: no caminho da voz clonada o `main.py` substitui essa lista
    pelo timing REAL do audio dublado, e ler dela e' o unico jeito de a conta
    valer para os dois caminhos de TTS.

    ⚠️ Falha ABERTA: sem palavra nenhuma devolve 0,0, e quem chama entende
    isso como "nao sei aparar". Clipe sem fala ja' e' barrado antes, pelo
    `engine/fala.py`.
    """
    if not palavras:
        return 0.0
    fins = [float(p.get("fim") or 0.0) for p in palavras]
    return max(fins) if fins else 0.0


def duracao_util(duracao_total: float, palavras: list[dict] | None,
                 tem_dublagem: bool, dur_min: float) -> float | None:
    """Ate' onde o video deve ir, ou None quando nao ha' o que aparar.

    None quer dizer "deixa como esta'" — e' o que quem chama espera pra manter
    o comportamento antigo intacto. Devolve numero SO' nos casos em que aparar
    e' seguro:

        sem dublagem            None  (o audio original toca ate' o fim)
        sem palavra             None  (nao da' pra saber onde a fala acabou)
        cauda <= CAUDA_MAX_S    None  (a sobra le' como fechamento)
        cortaria abaixo do piso None  (DUR_MIN e' regra de dinheiro)
    """
    if not tem_dublagem:
        return None
    if not duracao_total or duracao_total <= 0:
        return None
    fim = fim_da_fala(palavras)
    if fim <= 0:
        return None
    if duracao_total - fim <= CAUDA_MAX_S:
        return None
    util = fim + CAUDA_MARGEM_S
    if util >= duracao_total:
        return None
    if util < dur_min:
        return None
    return round(util, 3)
