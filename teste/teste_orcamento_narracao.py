# -*- coding: utf-8 -*-
"""A narracao cabe no tempo do clipe — sem perder informacao.

POR QUE EXISTE, medido em 31/08/2026

Os logs dos runs de hoje mostram o motor avisando sobre si mesmo:

    ritmo alto: 277 palavras/min   (x2)
    ritmo alto: 275 palavras/min
    ritmo alto: 269 palavras/min
    ritmo alto: 256 palavras/min
    narracao 173,9s pro clipe de 118,3s (acelerando 1,47x)

O codigo diz que acima de 200 ppm a compreensao cai, e TODAS as medicoes
ficaram entre 256 e 277. O aviso disparava sempre e ninguem podia agir: o
texto ja' vinha longo do modelo, e so' restava ao `atempo` esmagar o audio.

⚠️ Nenhum motor de TTS soa natural depois de ser acelerado 47%. Trocar de
modelo de voz nao resolveria isto — o defeito e' o TEXTO, nao a sintese.

O prompt ja' tinha uma secao TAMANHO, mas ela era RELATIVA ("parecido com o
original") e sem numero. Traduzir ingles -> portugues estica o texto por
natureza, entao "parecido com o original" ainda estoura.

⚠️ O RISCO DE ENCURTAR, e o que o prompt faz contra ele: encurtar pode virar
PERDER INFORMACAO. O texto manda cortar redundancia (repeticao, conectivo
longo, adjetivo decorativo) e proibe cortar numero, nome, marca, unidade,
passo de procedimento e conclusao. E manda ENTREGAR ASSIM MESMO se nao couber
sem perder fato — texto um pouco longo e' melhor que texto incompleto.

O CASO NEGATIVO, que e' o que protege os videos

Sem duracao, o prompt tem de ficar EXATAMENTE como era. Os quatro canais no
ar dependem disso, e uma mudanca de prompt nao levanta excecao nem reprova
teste — ela sai como narracao pior, dias depois.

Roda com: python teste/teste_orcamento_narracao.py
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

from engine import traducao as t  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def montar(dur):
    """O prompt como `_traduzir_texto` o monta, sem tocar na rede."""
    return t.PROMPT_NARRACAO.format(
        texto="fala original aqui",
        dica_genero=t.dica_de_genero(None),
        orcamento=t.orcamento_de_palavras(dur))


print(__doc__.splitlines()[0])

# --- 1. o caso NEGATIVO ---------------------------------------------------
print("\n[1] sem duracao, o prompt nao ganha orcamento nenhum")
for dur in (None, 0, -5, 3):
    checar(t.orcamento_de_palavras(dur) == "",
           f"duracao {dur} -> sem orcamento")
sem = montar(None)
checar("PALAVRAS (sao" not in sem, "nenhum numero de palavras vaza pro prompt")
checar("MESMO TEMPO que a fala" in sem, "a secao TAMANHO continua no prompt")

# --- 2. o caso positivo: a conta ------------------------------------------
print("\n[2] com duracao, o orcamento e' 113 ppm")
# ⚠️ 113 e' MEDIDO na sintese (run #17: 135, 103 e 102 ppm
# reais, media 113). O 150 da primeira versao era ritmo de NARRADOR
# HUMANO, numero editorial — por isso pedia 32% de texto a mais do
# que cabia na janela.
checar(t.PALAVRAS_POR_MINUTO == 113, "o alvo e' 113, o ritmo MEDIDO da sintese")
for dur, esperado in ((60, 113), (90, 169), (110, 207), (118.3, 222)):
    txt = t.orcamento_de_palavras(dur)
    checar(f"{esperado} PALAVRAS" in txt,
           f"{dur}s -> {esperado} palavras")

print("\n[3] o caso REAL que motivou isto")
# clipe de 118,3s cuja narracao durou 173,9s (1,47x de aceleracao)
orc = t.orcamento_de_palavras(118.3)
checar("222" in orc, "o clipe de 118,3s ganha orcamento de 222 palavras")
# 173,9s de fala a 150 ppm sao ~435 palavras; 222 e' quase metade
checar(222 < 435, "o orcamento e' menor que o texto que estourou")

# --- 4. encurtar NAO pode virar perder informacao -------------------------
print("\n[4] o prompt protege o conteudo ao mandar encurtar")
com = montar(110)
for frase, oque in [
        ("REDUNDÂNCIA, nunca FATO", "diz o que cortar e o que nao"),
        ("NUNCA corte", "lista explicita do que e' proibido cortar"),
        ("número", "numero esta' protegido"),
        ("nome", "nome esta' protegido"),
        ("passo de um procedimento", "passo de procedimento protegido"),
        ("ENTREGUE ASSIM MESMO", "prefere estourar a perder informacao")]:
    checar(frase in com, oque)

# --- 5. o outro prompt (traducao comum) nao quebra ------------------------
print("\n[5] o PROMPT comum, que nao tem esses campos, continua formatando")
try:
    comum = t.PROMPT.format(texto="abc")
    checar("abc" in comum, "PROMPT comum formata so' com {texto}")
except KeyError as e:
    checar(False, f"PROMPT comum quebrou: {e}")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
