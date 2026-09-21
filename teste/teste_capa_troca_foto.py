# -*- coding: utf-8 -*-
"""Foto ruim TROCA por uma extra boa, e so' desqualifica se nao houver troca.

## ⛔ POR QUE ESTE TESTE EXISTE

Ordem do Bryan em 21/09/2026: "temos que ter uma extra boa pra nao perder
vendas". Ate' entao foto ruim MATAVA o produto na regua da capa.

MEDIDO no catalogo daquele dia: dos 7 produtos que passavam em TODO o resto
da regua, 5 eram barrados SO' pela foto -- 71%. Depois de julgar as 23 extras
desses 5, dois voltaram (nota 10 e nota 9) e um deles GANHOU a capa, com
numeros melhores em todos os eixos que o anterior.

## ⚠️ O CASO NEGATIVO E' O QUE FAZ ESTE TESTE VALER

Um "trocador" que troque SEMPRE passa em qualquer teste de troca. Entao aqui
se prova tambem que ele NAO troca quando nao deve:

1. troca pela extra boa, e escolhe a de MAIOR nota entre as boas;
2. NEGATIVO: extras todas ruins -> nao troca, e o produto continua fora;
3. NEGATIVO: extra SEM JULGAMENTO nao serve de troca -- apesar de
   `serve_de_capa` falhar ABERTO. Trocar o que sabemos ruim pelo que nao
   sabemos nada e' piorar a aposta com cara de conserto;
4. NEGATIVO: extra com TEXTO QUEIMADO nao serve, mesmo com nota alta e sem
   colagem -- `melhor_foto` e `serve_de_capa` tem de ter UMA definicao de
   "serve", senao a troca devolve foto que a regua recusa em seguida;
5. foto principal boa nao e' trocada por nada.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
sys.argv = ["x"]
from engine import foto_julga as fj  # noqa: E402

FALHAS = 0


def checar(ok, msg):
    global FALHAS
    print(("  ok   " if ok else "  [x]  ") + msg)
    if not ok:
        FALHAS += 1


import inspect  # noqa: E402

PISO = 9


def julg(nota, colagem=False, texto=False):
    return {"nota": nota, "colagem": colagem, "texto_queimado": texto}


CACHE = {
    "ruim.jpg": julg(4, colagem=True),
    "boa9.jpg": julg(9),
    "boa10.jpg": julg(10),
    "ruim2.jpg": julg(5, texto=True),
    "texto.jpg": julg(10, texto=True),
}
fj._cache = lambda: CACHE
fj.julgado = lambda u: CACHE.get(u, {})

print("1. TROCA PELA EXTRA BOA, E PEGA A DE MAIOR NOTA")
esc = fj.melhor_foto("ruim.jpg", ["boa9.jpg", "boa10.jpg"], PISO)
checar(esc == "boa10.jpg", "escolheu a nota 10 entre a 9 e a 10 (" + esc + ")")

print()
print("2. NEGATIVO: EXTRAS TODAS RUINS -> NAO TROCA")
esc = fj.melhor_foto("ruim.jpg", ["ruim2.jpg"], PISO)
checar(esc == "ruim.jpg", "ficou na principal (" + esc + ")")
checar(not fj.serve_de_capa("ruim.jpg", PISO),
       "e a principal continua reprovada -- o produto sai da capa")

print()
print("3. NEGATIVO: EXTRA SEM JULGAMENTO NAO SERVE DE TROCA")
checar(fj.serve_de_capa("nunca_vista.jpg", PISO),
       "serve_de_capa falha ABERTO para foto sem julgamento (de proposito)")
esc = fj.melhor_foto("ruim.jpg", ["nunca_vista.jpg"], PISO)
checar(esc == "ruim.jpg",
       "mas melhor_foto NAO troca por ela (" + esc + ")")

print()
print("4. NEGATIVO: TEXTO QUEIMADO NAO SERVE, MESMO COM NOTA 10")
checar(not fj.serve_de_capa("texto.jpg", PISO),
       "serve_de_capa recusa nota 10 com texto queimado")
esc = fj.melhor_foto("ruim.jpg", ["texto.jpg"], PISO)
checar(esc == "ruim.jpg",
       "e melhor_foto recusa a MESMA foto -- uma so definicao de serve ("
       + esc + ")")

print()
print("5. PRINCIPAL BOA NAO E' TROCADA")
esc = fj.melhor_foto("boa9.jpg", ["boa10.jpg"], PISO)
checar(esc in ("boa9.jpg", "boa10.jpg"), "continua numa foto que serve")
checar(fj.serve_de_capa(esc, PISO), "e a escolhida passa na regua da capa")

print()
print("6. A REGUA DA CAPA CHAMA A TROCA (e nao so' a funcao existe)")
import publicar_bio as pb  # noqa: E402
fonte_capa = inspect.getsource(pb.marcar_capa)
checar("melhor_foto(" in fonte_capa, "marcar_capa chama melhor_foto")
checar("imagens" in fonte_capa, "e passa as EXTRAS do instantaneo")
i_serve = fonte_capa.find("serve_de_capa")
i_troca = fonte_capa.find("melhor_foto")
checar(0 < i_serve < i_troca,
       "a troca vem DEPOIS da reprovacao, nao no lugar dela")

print()
print("tudo verde" if not FALHAS else str(FALHAS) + " FALHA(S)")
sys.exit(1 if FALHAS else 0)
