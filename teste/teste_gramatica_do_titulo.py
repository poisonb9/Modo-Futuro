# -*- coding: utf-8 -*-
"""O acento do titulo — e, mais importante, o que NAO se mexe.

⚠️ O CASO, 09/09/2026, @semanestesia.pod, ao vivo na tarja E na legenda:

    "Por que contratar amigos e um ERRO e usar inimigos FUNCIONA"

O primeiro "e" e' o verbo. Ordem do Bryan: "nao vamos deletar, mas nao
podemos ter esse tipo de erro de gramatica".

⚠️ E O ACENTO NAO SE PERDEU NO MOTOR. Conferido antes de escrever uma linha:
as duas funcoes que normalizam pra ASCII sao de HASHTAG e de CHAVE de
registro, e nenhuma toca o titulo. O modelo gerou assim.

O QUE ESTE ARQUIVO PROTEGE, e a metade que importa e' a segunda:

  1. o que NAO EXISTE sem acento e' corrigido ("nao", "voce", "tambem")
  2. ⚠️ o que TEM segunda leitura NAO E' TOCADO. "amigos e um inimigo" e'
     portugues correto — um corretor afoito publicaria "amigos É um inimigo"
     e teria trocado um erro por outro, com a diferenca de que este ninguem
     reportou. Um corretor que muda tudo passa no teste de cima e destroi
     frase certa.
  3. a CAIXA e' preservada: o motor usa CAIXA ALTA pra enfase na tarja, e
     devolver "não" onde estava "NAO" estragaria o desenho.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import gramatica as g  # noqa: E402

falhas = []


def checar(cond, recado):
    if cond:
        print("  ok ", recado)
    else:
        print("  [x]", recado)
        falhas.append(recado)


print("1. o caso que foi ao ar")
t = "Por que contratar amigos e um ERRO e usar inimigos FUNCIONA"
checar(g.corrigir(t) ==
       "Por que contratar amigos é um ERRO e usar inimigos FUNCIONA",
       "o verbo ganha acento e o resto da frase fica intacto")
# ⚠️ o segundo "e" da frase E' conjuncao ("... e usar inimigos") e nao pode
# virar verbo. E' a mesma frase provando as duas coisas.
checar("e usar inimigos" in g.corrigir(t),
       "a conjuncao do meio da frase continua sem acento")

print("\n2. palavra que nao existe sem acento")
checar(g.corrigir("NAO faca isso") == "NÃO faca isso", "NAO -> NÃO em caixa alta")
checar(g.corrigir("voce nao viu") == "você não viu", "minusculas preservadas")
checar(g.corrigir("Voce viu") == "Você viu", "Inicial maiuscula preservada")

print("\n3. NEGATIVO — o que tem segunda leitura fica como esta'")
for frase in ("Ele falou de amigos e um inimigo",
              "Trouxe o cachorro e uma bola",
              "Comprou tres livros e um caderno"):
    saida = g.corrigir(frase)
    checar(" é um" not in saida and " é uma" not in saida,
           f'nao inventou verbo em "{frase[:34]}..."')

print("\n4. NEGATIVO — palavra legitima sem acento nao vira outra")
# "faca" (utensilio) e "esta" (este/esta) existem sem acento. Um corretor que
# os "consertasse" trocaria o sentido da frase.
for palavra in ("faca", "esta", "e", "para", "so", "sobre", "pode"):
    checar(g.corrigir(palavra) == palavra,
           f'"{palavra}" nao foi mexida (existe sem acento)')

print("\n5. o que ele NAO conserta, ele AVISA")
avisos = g.suspeitas("Ele falou de amigos e um inimigo")
checar(len(avisos) == 1, "caso duvidoso vira aviso, nao silencio")
checar(g.suspeitas("Isso e um ERRO") == [],
       "NEGATIVO: o que ele JA' consertou nao vira aviso tambem")
checar(g.suspeitas("Frase sem nada disso") == [],
       "NEGATIVO: frase limpa nao gera aviso")

print("\n6. esta' LIGADO no motor")
FONTE = (RAIZ / "main.py").read_text(encoding="utf-8")
checar("gramatica.corrigir(" in FONTE, "o main.py corrige antes de renderizar")
checar("gramatica.suspeitas(" in FONTE, "e imprime o aviso do caso duvidoso")
# ⚠️ tem de vir ANTES do suavizar: o suavizar troca letra por digito
# (morte -> m0rte) e a busca por palavra nao acharia mais o que corrigir.
checar(FONTE.index("gramatica.corrigir(") < FONTE.index("suavizar.palavras("),
       "corrige ANTES do suavizar, senao a palavra ja' mudou de forma")

if falhas:
    print(f"\n{len(falhas)} FALHA(S)")
    sys.exit(1)
print("\ntudo verde")
