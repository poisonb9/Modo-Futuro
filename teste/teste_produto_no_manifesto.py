# -*- coding: utf-8 -*-
"""O produto de afiliado viaja no manifesto, e meio produto nao passa.

⚠️ POR QUE ESTE TESTE EXISTE.

Decisao da §2.2 do FASE2, tomada em 09/09/2026: o produto vira campo do
MANIFESTO, e nao registro proprio. O motivo esta' na propria §2.2 — a pagina
da bio e o grupo do WhatsApp tem de ler o preco do MESMO lugar que a legenda,
senao o video diz um preco e a pagina diz outro.

O QUE PRECISA SER PROVADO

  1. ⚠️ CASO NEGATIVO, e e' o principal: clipe SEM produto continua
     funcionando. Sao os cinco canais de hoje. Se a chegada do afiliado
     quebrasse o clipe comum, a fase 2 pararia a operacao inteira pra
     comecar — e ninguem veria antes de publicar.
  2. produto AUSENTE e' diferente de produto INVALIDO. Ausente = "nao e' de
     afiliado" e devolve None calado. Invalido LEVANTA — meio produto vira
     post com link quebrado, que e' pior que post sem link.
  3. link so' http(s). `javascript:` e `intent://` nao sao link torto, sao
     vetor de ataque numa pagina que a gente publica. Falha FECHADA.
  4. preco e' TEXTO com data. Numero envelhece calado: o clipe diria
     "R$ 39,90" pra sempre enquanto a loja ja' mudou.

Roda com: python teste/teste_produto_no_manifesto.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import produto as pr

falhas = 0


def checar(cond, recado):
    global falhas
    if cond:
        print(f"  ok  {recado}")
    else:
        print(f"  FALHOU  {recado}")
        falhas += 1


print("1. CASO NEGATIVO: clipe sem produto continua funcionando")
# ⚠️ Os cinco canais de hoje caem todos aqui. E' o teste que garante que a
# fase 2 nao para a operacao pra comecar.
checar(pr.normalizar(None) is None, "produto ausente -> None, sem levantar")
checar(pr.normalizar({}) is None, "produto vazio -> None, sem levantar")
item_comum = {"titulo": "As regras extremas", "canal": "modofuturo",
              "sha": "abc", "url": "https://exemplo/clipe.mp4"}
checar(pr.do_manifesto(item_comum) is None,
       "item de manifesto SEM o campo produto -> None (itens antigos)")
checar(pr.linha_da_lista(item_comum) is None,
       "clipe comum nao gera linha de lista")

print("\n2. produto completo entra normalizado")
p = pr.normalizar({"nome": "Base tailandesa", "link": "https://loja/x",
                   "preco": "R$ 39,90", "loja": "Shopee",
                   "categoria": "maquiagem"})
checar(p["nome"] == "Base tailandesa", "nome")
checar(p["link"] == "https://loja/x", "link")
checar(p["preco"] == "R$ 39,90", "preco preservado como TEXTO")
checar(p["preco_em"] != "", "preco_em preenchido: preco e' foto de um dia")
checar(p["categoria"] == "maquiagem", "categoria, pra pagina agrupar")

print("\n3. meio produto NAO passa (levanta, nao devolve pela metade)")
for ruim, oq in [({"nome": "so nome"}, "sem link"),
                 ({"link": "https://a"}, "sem nome"),
                 ({"nome": "x", "link": "   "}, "link em branco")]:
    try:
        pr.normalizar(ruim)
        checar(False, f"{oq}: deixou passar")
    except pr.ProdutoInvalido:
        checar(True, f"{oq}: recusou")

print("\n4. link so' http(s) — falha FECHADA, a pagina e' publica")
for esquema in ("javascript:alert(1)", "intent://x", "data:text/html,x",
                "file:///etc/passwd", "loja.com/sem-esquema"):
    try:
        pr.normalizar({"nome": "x", "link": esquema})
        checar(False, f"aceitou {esquema[:24]}")
    except pr.ProdutoInvalido:
        checar(True, f"recusou {esquema[:24]}")
# ⚠️ CASO NEGATIVO do item 4: o http normal TEM de passar. Uma guarda que
# recusa tudo "nunca deixa passar link ruim" e tambem nunca publica.
checar(pr.normalizar({"nome": "x", "link": "http://loja/y"})["link"]
       == "http://loja/y", "http simples PASSA (senao a guarda recusa tudo)")

print("\n5. preco sem preco nao inventa data")
sem = pr.normalizar({"nome": "x", "link": "https://a"})
checar(sem["preco"] == "" and sem["preco_em"] == "",
       "sem preco -> preco_em vazio, nao a data de hoje")

print("\n6. a linha que o grupo do WhatsApp le'")
linha = pr.linha_da_lista({"produto": p})
checar("Base tailandesa" in linha and "R$ 39,90" in linha
       and "https://loja/x" in linha, "nome, preco e link na linha")
checar(linha.count("\n") == 1, "link em linha propria (o WhatsApp lincaria errado)")

print(chr(10) + "7. o campo CHEGA no post.json — o cano inteiro, nao so' as pontas")
# ⚠️ O DEFEITO QUE ESTE BLOCO GUARDA, achado em 09/09/2026 depois que a §2.6
# (pagina da bio) foi escrita: `engine/produto.py` validava, o
# `publicar_release` poe no manifesto — e o `main.py` NAO copiava o campo pro
# post.json. O `meta` de la' e' uma copia POR NOMES: o que nao esta' na tupla
# nao existe daquele ponto em diante, sem erro nenhum.
#
# Ja' tinha acontecido com a `legenda_premium` (ate' 31/08: o log dizia "1408
# chars", o .txt do Drive saia com 0,3 KB). O produto era o campo seguinte a
# cair na mesma armadilha, e ninguem veria antes de publicar.
FONTE_MAIN = (RAIZ / "main.py").read_text(encoding="utf-8")
FONTE_REL = (RAIZ / "publicar_release.py").read_text(encoding="utf-8")
checar('"produto",' in FONTE_MAIN,
       "main.py copia `produto` pro post.json")
checar('m.get("produto")' in FONTE_REL,
       "publicar_release le' o produto do post.json")
# ⚠️ CASO NEGATIVO: a busca acima tem de ser capaz de ACUSAR. Se ela desse
# verdadeiro pra qualquer nome, o teste passaria com o cano rompido.
checar('"produto_que_nao_existe",' not in FONTE_MAIN,
       "NEGATIVO: a busca nao aprova nome que nao esta' na lista")
# e os dois campos que ja' custaram caro continuam la'
for campo in ("legenda_premium", "quarentena", "depende_de_anterior"):
    checar(f'"{campo}"' in FONTE_MAIN,
           f"`{campo}` continua na copia (ja' custou uma vez)")

if falhas:
    print(chr(10) + f"{falhas} FALHA(S)")
    sys.exit(1)
print(chr(10) + "tudo verde")
