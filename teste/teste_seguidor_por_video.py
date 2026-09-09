# -*- coding: utf-8 -*-
"""O ranking do radar avisa quando a view nao e' quem converte.

⚠️ O QUE PRECISA SER PROVADO, E POR QUE.

O `melhores()` entrega os 2 primeiros por VIEW pro radar, e o radar escolhe a
fonte dos proximos videos — ou seja, a view decide o que a maquina produz na
semana seguinte. Em 09/09/2026 mediu-se, um a um na tela do Studio, o campo
"Novos seguidores" de 11 posts do @modofuturo: 7.775 views renderam 32
seguidores, e 28 deles vieram de UM post.

Os dois de 22/08 fecham o caso — mesmo dia, mesmo canal, mesma cadencia:

    As regras extremas / fabrica   2473 views  28 seg  10,63s  6,9% completo
    Como 1 poeira / 1 milhao       1009 views   1 seg  16,11s  9,1% completo

O de baixo prendeu MAIS a audiencia e converteu 28 VEZES MENOS.

OS CASOS NEGATIVOS

  aviso calado      ⚠️ o teste que da' sensibilidade ao resto. Um aviso que
                    dispara sempre nao avisa nada — vira ruido e quem le'
                    para de olhar. Quando o campeao de view TAMBEM e' o de
                    seguidor (que e' o caso real dos dois posts de 22/08), o
                    aviso tem de sair VAZIO.

  None nao e' zero  "ninguem abriu esse post no Studio" e' diferente de "foi
                    medido e nao converteu ninguem". Se `None` virasse zero,
                    todo post nao medido passaria a constar como fracasso
                    medido — e a media do canal desabaria por invencao.

  canal errado      o numero de um canal nao pode vazar pro ranking de outro.

  titulo curto      o export do Studio cola a descricao no fim do titulo (a
                    mesma armadilha que duplicou os "2 melhores" em 08/09),
                    entao a regra e' PREFIXO — mas com piso, senao um titulo
                    de 4 letras casa com meio canal.

Roda com: python teste/teste_seguidor_por_video.py
"""
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import seguidores

falhas = 0


def checar(cond, recado):
    global falhas
    if cond:
        print(f"  ok  {recado}")
    else:
        print(f"  FALHOU  {recado}")
        falhas += 1


def com_dados(linhas):
    """Aponta o modulo pra um JSONL temporario, pra nao depender do estado."""
    tmp = Path(tempfile.mkdtemp()) / "seg.jsonl"
    tmp.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n"
                           for x in linhas), encoding="utf-8")
    seguidores.ARQUIVO = tmp


def reg(titulo, seg, canal="modofuturo"):
    return {"canal": canal, "titulo": titulo, "novos_seguidores": seg,
            "views": 100}


ORIGINAL = seguidores.ARQUIVO

print("1. o aviso sai quando a view nao e' quem converte")
com_dados([reg("Post que alcanca mas nao converte ninguem", 0),
           reg("Post que alcanca menos e converte muito", 9)])
postos, aviso = seguidores.anotar(
    [{"titulo": "Post que alcanca mas nao converte ninguem", "views": 2000},
     {"titulo": "Post que alcanca menos e converte muito", "views": 500}],
    "modofuturo")
checar(postos[0].get("seguidores") == 0, "o primeiro por view vem anotado com 0")
checar(postos[1].get("seguidores") == 9, "o segundo vem anotado com 9")
checar("SEGUIDOR" in aviso, "avisa que por seguidor o primeiro seria outro")
checar(postos[0]["views"] == 2000, "NAO reordena — a ordem por view se mantem")

print("\n2. CASO NEGATIVO: o aviso fica calado quando os dois campeoes coincidem")
com_dados([reg("As regras extremas para entrar na fabrica", 28),
           reg("Como 1 poeira pode destruir 1 milhao", 1)])
_, aviso = seguidores.anotar(
    [{"titulo": "As regras extremas para entrar na fabrica", "views": 2473},
     {"titulo": "Como 1 poeira pode destruir 1 milhao", "views": 1009}],
    "modofuturo")
checar(aviso == "", f"aviso vazio no caso real de 22/08 (veio: {aviso!r})")

print("\n3. CASO NEGATIVO: nao medido nao vira zero")
com_dados([reg("Post medido de verdade no estudio", 0)])
checar(seguidores.de("modofuturo", "Post medido de verdade no estudio") == 0,
       "medido com zero devolve 0")
checar(seguidores.de("modofuturo", "Post que ninguem abriu no estudio") is None,
       "nao medido devolve None, e None nao e' zero")
checar(seguidores.de("atefalhar", "Post medido de verdade no estudio") is None,
       "o numero de um canal nao vaza pro outro")
postos, _ = seguidores.anotar(
    [{"titulo": "Post que ninguem abriu no estudio", "views": 800}], "modofuturo")
checar("seguidores" not in postos[0],
       "post nao medido sai do ranking SEM o campo, nao com zero")

print("\n4. titulo com descricao colada e' o mesmo post; titulo curto nao")
com_dados([reg("As regras extremas para entrar na fabrica", 28)])
checar(seguidores.de("modofuturo",
                     "As regras extremas para entrar na fabrica #cleanroom") == 28,
       "descricao colada no fim ainda casa o mesmo post")
checar(seguidores.de("modofuturo", "As regras") is None,
       "titulo curto nao casa por prefixo (piso de 20)")

print("\n5. o arquivo de verdade le' os 11 posts medidos")
seguidores.ARQUIVO = ORIGINAL
reais = seguidores.registros("modofuturo")
checar(len(reais) >= 11, f"{len(reais)} posts no estado (esperado 11+)")
checar(sum(r["novos_seguidores"] for r in reais) == 32,
       "somam os 32 seguidores medidos em 09/09")
checar(seguidores.de("modofuturo",
                     "As regras extremas para entrar na fabrica mais limpa do mundo") == 28,
       "o post de 22/08 devolve os 28 seguidores")

if falhas:
    print(chr(10) + f"{falhas} FALHA(S)")
    sys.exit(1)
print(chr(10) + "tudo verde")
