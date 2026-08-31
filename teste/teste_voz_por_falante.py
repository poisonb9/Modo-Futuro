# -*- coding: utf-8 -*-
"""Cada pessoa do clipe ganha a sua voz — e ninguem troca de voz a toa.

POR QUE EXISTE

Pedido do Bryan em 31/08/2026: "se for um video de homem e mulher podemos
alternar as vozes fazendo um dinamismo".

O que ele ouviu e gostou no run #184 eram DUAS PESSOAS REAIS — fonte em
portugues, audio original intacto. Nao era o motor. O motor tinha uma voz so'
por clipe.

A DIARIZACAO VEM DO GEMINI, nao de biblioteca nova: ele ja' VE o video na
selecao, entao devolve `falantes` — os intervalos de cada pessoa, com genero.
O prompt manda decidir pela IMAGEM e pela voz, nunca pelo texto.

⚠️ AGRUPA EM BLOCO, NAO POR FRASE. A sintese continua frase a frase (o
Chatterbox soa mal em texto longo), mas a VOZ so' muda quando a PESSOA muda.
O VOZ_MULTIPLA.md ja' avisava: "alternancia sem sentido editorial vira ruido".

⚠️ O CUSTO NAO DOBRA. O modelo do Chatterbox e' carregado UMA vez por execucao
(`_MODELO` global) e a amostra vai por chamada, em `audio_prompt_path`. Trocar
de voz nao recarrega nada — e' o mesmo numero de sinteses.

O CASO NEGATIVO, que e' o que protege os canais no ar

Sem `falantes`, tudo tem de sair exatamente como antes: UM bloco, a amostra do
disparo, nenhuma troca. Os quatro canais existentes dependem disso, e uma
troca de voz indevida nao levanta excecao — sai como clipe publicado com a voz
errada.

Roda com: python teste/teste_voz_por_falante.py
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

from engine import voz_clonada as v  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


SEG = [
    {"inicio": 0, "fim": 5, "texto": "Primeira fala dela."},
    {"inicio": 5, "fim": 10, "texto": "Segunda fala dela."},
    {"inicio": 10, "fim": 16, "texto": "Agora ele responde."},
    {"inicio": 16, "fim": 22, "texto": "E continua respondendo."},
    {"inicio": 22, "fim": 26, "texto": "Ela conclui."},
]
FAL = [
    {"inicio_s": 0, "fim_s": 10, "quem": "A", "genero": "feminino"},
    {"inicio_s": 10, "fim_s": 22, "quem": "B", "genero": "masculino"},
    {"inicio_s": 22, "fim_s": 26, "quem": "A", "genero": "feminino"},
]

print(__doc__.splitlines()[0])

# --- 1. o CASO NEGATIVO --------------------------------------------------
print("\n[1] sem `falantes`, nada muda")
b = v._blocos_por_falante(SEG, None)
checar(len(b) == 1, f"um bloco so' (foram {len(b)})")
checar(b[0][0] is None, "genero None — usa a amostra do disparo")
checar(len(b[0][1]) == len(SEG), "todos os segmentos no mesmo bloco")
checar(v._blocos_por_falante(SEG, [])[0][0] is None, "lista vazia idem")

# --- 2. o caso positivo --------------------------------------------------
print("\n[2] com `falantes`, um bloco por pessoa")
b = v._blocos_por_falante(SEG, FAL)
checar(len(b) == 3, f"tres blocos (foram {len(b)})")
checar([g for g, _ in b] == ["feminino", "masculino", "feminino"],
       "a ordem dos generos segue o tempo")
checar(len(b[0][1]) == 2, "as duas falas dela ficam JUNTAS num bloco")
checar(len(b[1][1]) == 2, "as duas dele tambem")

# --- 3. bloco, nao frase -------------------------------------------------
print("\n[3] a voz muda por PESSOA, nao por frase")
checar(len(b) < len(SEG),
       f"{len(b)} blocos para {len(SEG)} segmentos — agrupou de verdade")
umafala = [{"inicio": 0, "fim": 90, "texto": "Um monologo longo inteiro."}]
umso = [{"inicio_s": 0, "fim_s": 90, "quem": "A", "genero": "masculino"}]
checar(len(v._blocos_por_falante(umafala, umso)) == 1,
       "uma pessoa falando 90s e' UM bloco, nao varios")

# --- 4. o mapa genero -> amostra -----------------------------------------
print("\n[4] o genero escolhe a amostra, e falha ABERTA")
padrao = RAIZ / "vozes" / "bryan_amostra.wav"
os.environ.pop("AMOSTRA_VOZ_FEMININO", None)
checar(v._amostra_do_genero("feminino", padrao) == padrao,
       "sem a variavel de ambiente, cai no padrao")
checar(v._amostra_do_genero(None, padrao) == padrao, "genero None -> padrao")
checar(v._amostra_do_genero("indefinido", padrao) == padrao,
       "'indefinido' -> padrao (nao inventa voz)")
checar(v._amostra_do_genero("varios", padrao) == padrao,
       "'varios' -> padrao")
os.environ["AMOSTRA_VOZ_FEMININO"] = "nao_existe_no_disco.wav"
checar(v._amostra_do_genero("feminino", padrao) == padrao,
       "arquivo inexistente -> padrao, nao quebra o run")
os.environ.pop("AMOSTRA_VOZ_FEMININO", None)

# --- 5. as duas pontas existem no codigo ---------------------------------
print("\n[5] o fio esta' ligado, nao so' a peca")
sel = (RAIZ / "engine" / "selecao.py").read_text(encoding="utf-8")
mn = (RAIZ / "main.py").read_text(encoding="utf-8")
yml = (RAIZ / ".github" / "workflows" / "cortar_de_bruto.yml").read_text(
    encoding="utf-8")
checar('"falantes"' in sel, "a selecao PEDE os falantes ao Gemini")
checar("falantes=c.get(\"falantes\")" in mn, "o main PASSA os falantes")
checar('"falantes",' in mn, "e o campo sobrevive no post.json")
checar("AMOSTRA_VOZ_FEMININO" in yml and "AMOSTRA_VOZ_MASCULINO" in yml,
       "o workflow mapeia genero -> voz")
checar(yml.count("bruna_amostra.wav") >= 2 and yml.count("bryan_amostra.wav") >= 2,
       "o workflow garante as DUAS amostras em disco")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
