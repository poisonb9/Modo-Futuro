# -*- coding: utf-8 -*-
"""A chamada pro link da bio: na legenda e no fim do clipe.

⚠️ POR QUE ELA EXISTE, medido em 12/09/2026: NENHUM video da operacao mandava
alguem pro link. A legenda era titulo + descricao + premium + hashtags, e nada
mais. A contra-capa ficou pronta, os convites dos grupos estao vivos, o livro
01 estreia no @semanestesia.pod — e o primeiro degrau do funil nao existia.

⚠️ E ELA RESOLVE UMA TENSAO QUE NOS MESMOS CRIAMOS NO MESMO DIA. O aparo da
cauda muda faz o clipe terminar 0,6s depois da ultima palavra, e isso tirou a
tela onde um card de fim caberia. A saida nao foi desfazer o aparo: foi
devolver os segundos SO' QUANDO ELES TEM O QUE CARREGAR. O defeito era rodar
sem voz E SEM NADA — cauda com chamada nao e' o mesmo defeito.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import chamada, legenda_post  # noqa: E402

falhas = []


def checar(cond, recado):
    print(("  ok  " if cond else "  [x] ") + recado)
    if not cond:
        falhas.append(recado)


print("1. cada canal com destino tem a sua chamada")
checar("livro" in chamada.do_canal("semanestesia.pod").lower(),
       "o Sem Anestesia chama pro LIVRO, que e' o produto que estreia la'")
checar("bio" in chamada.do_canal("truque.importado").lower(),
       "o Achadinho Make chama pros achadinhos")
# aceita apelido e arroba, como o resto do motor
checar(chamada.do_canal("@achadinho.make") == chamada.do_canal("truque.importado"),
       "resolve pelo registro: arroba e apelido dao a mesma chamada")

print("\n2. NEGATIVO — canal desconhecido nao ganha chamada nenhuma")
# ⚠️ Esta e' a metade que importa. Uma chamada generica no canal errado e'
# pior que chamada nenhuma: publico de tecnologia convidado pra grupo de
# promocao nao volta. O resolvedor devolve None pra desconhecido, e aqui isso
# tem de virar string vazia, nunca um texto padrao.
for ruim in ("canal que nao existe", "", None, "modofuturo_2"):
    checar(chamada.do_canal(ruim) == "", f"{ruim!r} -> sem chamada")

print("\n3. NEGATIVO — canal conhecido SEM destino tambem fica sem chamada")
# O @modofuturo e o @atefalhar nao tem grupo nem produto hoje. Convidar pra
# uma pagina que nao entrega gasta a unica frase que a pessoa leria ate' o fim.
for sem in ("modofuturo", "atefalhar"):
    checar(chamada.do_canal(sem) == "",
           f"{sem} nao tem destino -> nao chama")

print("\n4. a chamada MOSTRA, nao pergunta")
# ⭐ Playbook §23.9: titulo-PERGUNTA converteu 0 de 4; o que AFIRMA, 7 de 14.
# Nao ha' razao pra uma chamada obedecer logica diferente da de um titulo.
for canal, texto in chamada.CHAMADA.items():
    checar("?" not in texto, f"{canal}: sem pergunta")
    checar(texto.strip().endswith("."), f"{canal}: frase fechada")

print("\n5. na legenda, ANTES das hashtags")
meta = {"titulo": "Um titulo", "descricao": "Uma descricao.",
        "chamada": "O livro esta no link da bio.", "tags": ["um", "dois"]}
txt = legenda_post.montar(meta)
checar(txt.index("link da bio") < txt.index("#um"),
       "a chamada vem antes da primeira hashtag")
# ⚠️ hashtag e' rodape: ninguem le' o que vem depois dela. A chamada tem de
# ser a ultima COISA LIDA, nao a ultima linha do arquivo.
checar(txt.index("Uma descricao") < txt.index("link da bio"),
       "e depois do texto, nao no meio dele")

print("\n6. NEGATIVO — sem chamada, a legenda fica como era")
sem_chamada = legenda_post.montar(
    {"titulo": "Um titulo", "descricao": "Uma descricao.", "tags": ["um"]})
checar("\n\n\n" not in sem_chamada, "campo vazio nao deixa buraco na legenda")
checar(sem_chamada.endswith("#um"), "termina na hashtag, como antes")

print("\n7. esta' LIGADA no motor")
FONTE = (RAIZ / "main.py").read_text(encoding="utf-8")
checar("chamada=texto_chamada" in FONTE, "o render recebe a chamada")
checar('"chamada",' in FONTE, "e o campo viaja no post.json (copia por nomes)")
checar("dur_max + render.CHAMADA_SEGUNDOS" in FONTE,
       "a cauda e' devolvida pra caber o card")
checar("min(dur_final_antes" in FONTE,
       "e NUNCA alem do que o bruto tem — esticar o -t nao estica o video")

RENDER = (RAIZ / "engine" / "render.py").read_text(encoding="utf-8")
checar("img_chamada" in RENDER, "o render desenha o card")
checar("gte(t," in RENDER, "e ele aparece no FIM, nao no comeco")

if falhas:
    print(f"\n{len(falhas)} FALHA(S)")
    sys.exit(1)
print("\ntudo verde")
