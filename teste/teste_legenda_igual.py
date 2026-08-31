# -*- coding: utf-8 -*-
"""A legenda do .txt do Drive e a do post tem de ser A MESMA.

POR QUE EXISTE

O motor tinha DUAS funcoes de legenda que discordavam:

    main._legenda                  titulo + descricao + premium + hashtags
    publicar_tiktok.legenda_do_clipe   titulo + hashtags

A segunda e' quem escreve o `.txt` que vai pro Drive ao lado do clipe. O mesmo
clipe saia com legenda COMPLETA no post e legenda POBRE no arquivo.

MEDIDO em 31/08/2026, nos arquivos do Drive:

    @truque.importado (31-08 v2)   0,1 KB   x4
    cozinha                        5,4 a 12,1 KB

O Bryan viu e reportou: "os videos de maquiagem estao sem legenda premium".

⚠️ E ELA ERA GERADA. O log do run #196 registrou "legenda premium: 1646
chars" nos quatro clipes — o texto existia no post.json e se perdia na hora de
escrever o arquivo. Nao era falta de conteudo, era duas fontes de verdade.

⚠️ Por que ninguem percebeu: o clipe FICAVA certo no Buffer, que usa a outra
funcao. So' quem abrisse o .txt no Drive veria — e o Drive so' passou a ser o
caminho de revisao hoje, quando o Bryan decidiu postar as estreias na mao.

O CASO NEGATIVO: um clipe SEM premium tem de dar o mesmo resultado nas duas.
Se so' a versao com premium batesse, a divergencia voltaria pelo caminho de
baixo sem ninguem ver.

Roda com: python teste/teste_legenda_igual.py
"""
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import os  # noqa: E402
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

import main as m  # noqa: E402
import publicar_tiktok as pt  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def comparar(meta: dict, rotulo: str) -> None:
    d = Path(tempfile.mkdtemp()) / "clipe"
    d.mkdir()
    (d / "post.json").write_text(json.dumps(meta, ensure_ascii=False),
                                 encoding="utf-8")
    do_txt = pt.legenda_do_clipe(d)
    do_post = m._legenda(meta)
    checar(do_txt == do_post, f"{rotulo}: .txt do Drive == post do Buffer")
    if do_txt != do_post:
        print(f"          txt  ({len(do_txt)}): {do_txt[:110]!r}")
        print(f"          post ({len(do_post)}): {do_post[:110]!r}")
    return do_txt


print(__doc__.splitlines()[0])

COMPLETO = {
    "titulo": "Como fazer base e contorno em creme perfeito",
    "descricao": "A tecnica que evita marcar a pele.",
    "legenda_premium": ("O que nao coube no corte: a base em creme pede pele "
                        "hidratada, e o contorno frio puxa o rosto. " * 6),
    "tags": ["maquiagem", "tutorialdemaquiagem", "contornoemcreme",
             "baseperfeita", "maquiagempele"],
}

print("\n[1] clipe completo: as duas funcoes concordam")
txt = comparar(COMPLETO, "completo")
checar("O que nao coube no corte" in txt, "a legenda premium ESTA' no .txt")
checar(COMPLETO["descricao"] in txt, "a descricao esta' no .txt")
checar("#maquiagem" in txt, "as hashtags estao no .txt")

print("\n[2] o tamanho deixou de ser 0,1 KB")
checar(len(txt) > 400,
       f"o .txt tem {len(txt)} chars (os da maquiagem tinham ~140)")

print("\n[3] o CASO NEGATIVO: sem premium, ainda concordam")
sem_premium = dict(COMPLETO)
sem_premium.pop("legenda_premium")
comparar(sem_premium, "sem premium")

print("\n[4] e sem descricao tambem")
so_titulo = {"titulo": "Titulo sozinho", "tags": ["a", "b"]}
t = comparar(so_titulo, "so' titulo e tags")
checar("Titulo sozinho" in t and "#a" in t, "o minimo ainda sai certo")

print("\n[5] hashtag continua sem acento nem espaco")
com_acento = {"titulo": "T", "tags": ["maquiagem básica", "pele"]}
t = comparar(com_acento, "acento na tag")
checar("#maquiagembasica" in t, "acento e espaco somem da hashtag")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
