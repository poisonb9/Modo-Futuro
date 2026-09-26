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
    """O prompt como `_traduzir_texto` o monta, sem tocar na rede.
    Pelo `_montar` do motor: ele preenche TODOS os campos (inclusive o
    `{guia}` do Guia de voz, 26/09), e o teste nao envelhece a cada campo."""
    return t._montar(t.PROMPT_NARRACAO, "fala original aqui", None, dur)


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
print("\n[2] com duracao, o orcamento: 145 ppm na voz D (padrao), 113 na A")
# ⚠️ 113 e' MEDIDO na sintese da voz A (run #17: 135, 103 e 102 ppm
# reais, media 113). O 150 da primeira versao era ritmo de NARRADOR
# HUMANO, numero editorial — por isso pedia 32% de texto a mais do
# que cabia na janela.
# ⭐ 26/09: a voz D (producao) fala 150-164 ppm, MEDIDO; 145 fica logo
# abaixo. Com 113 ela terminava cedo e deixava pausas de segundos.
import os as _os
checar(t.PALAVRAS_POR_MINUTO_A == 113 and t.PALAVRAS_POR_MINUTO_D == 145, "113 (A) e 145 (D)")
checar(t.PALAVRAS_POR_MINUTO == (113 if (_os.environ.get("VOZ_MOTOR") or "D").upper() == "A"
                                 else 145), "o alvo segue o motor da voz")
t.PALAVRAS_POR_MINUTO = 113   # as contas abaixo sao do caso real da voz A
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
    # pelo `_montar`, como o motor faz: desde 26/09 o PROMPT comum tambem
    # tem `{guia}`, que o `_montar` preenche e um `.format(texto=)` nao
    comum = t._montar(t.PROMPT, "abc")
    checar("abc" in comum and "{" not in comum.replace("{{", ""),
           "PROMPT comum formata sem campo sobrando")
except KeyError as e:
    checar(False, f"PROMPT comum quebrou: {e}")

# ⭐ 26/09 (make: 154 de 206 palavras -> 24 s sem voz no fim do clipe)
print("\n[9] narracao CURTA: faixa no prompt e uma 2a tentativa")
t.PALAVRAS_POR_MINUTO = 145
orc = t.orcamento_de_palavras(85.0)
checar("entre 184 e 205 PALAVRAS" in orc, f"orcamento pede faixa ({orc[:60]})")
checar(t.escolher_narracao(154, 200, 205) == 2, "2a mais perto do alvo: fica a 2a")
checar(t.escolher_narracao(154, 150, 205) == 1, "2a ainda mais curta: fica a 1a")
checar(t.escolher_narracao(154, 260, 205) == 1, "NEGATIVO: 2a passa de 115%: fica a 1a")
chamadas = []
_real = t._traduzir_texto
t._traduzir_texto = lambda texto, prompt=None, genero=None, duracao_s=None: (
    chamadas.append(prompt) or " ".join(["palavra"] * 198))
curta = " ".join(["x"] * 154)
novo = t._completar_se_curta(curta, "orig", None, 85.0)
checar(len(chamadas) == 1 and "CURTA" in chamadas[0] and len(novo.split()) == 198,
       "curta (154/205): pede de novo e fica com a de 198")
chamadas.clear()
ok = " ".join(["x"] * 190)
checar(t._completar_se_curta(ok, "orig", None, 85.0) == ok and not chamadas,
       "NEGATIVO: no tamanho certo nao gasta 2a chamada")
t._traduzir_texto = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("sem cota"))
checar(t._completar_se_curta(curta, "orig", None, 85.0) == curta,
       "2a chamada falhou: segue a 1a (falha aberta)")
t._traduzir_texto = _real

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
