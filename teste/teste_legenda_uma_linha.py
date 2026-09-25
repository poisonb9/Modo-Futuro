# -*- coding: utf-8 -*-
"""Guarda do ajustador de linhas da capa (`ajustarLinhasCapaJa`).

Nasceu do print do Bryan em 22/09/2026: a legenda da capa
("rastreando ha 8 dias · a R$ 0,03 do menor preco") quebrava no meio da
frase, em "· a" / "R$ 0,03 do menor preco".

MEDIDO no ar: a frase pede 302 px a 12,5 px, e a largura util da legenda
e' ~83,35% da tela. Entao em toda tela abaixo de ~390 px ela NAO cabia --
e o ajustador de entao so' sabia CRESCER (12,5 -> 13), nunca encolher.

Este teste nao abre navegador: ele reimplementa a MESMA aritmetica do
`ajustarLinhasCapaJa` extraido do todos.html, e confere que:

  positivo  a 360/375 px as duas linhas cabem numa linha so'
  negativo  a 320 px NENHUMA cabe, e as duas voltam a quebrar
  negativo  a decisao e' COLETIVA: a 340 px, onde uma cabia e a outra nao,
            as duas quebram juntas (nunca 11,3 inteira ao lado de 12,5
            quebrada)

⚠ O teste tambem confere que as CONSTANTES do teste batem com as do
  arquivo. Sem isso ele viraria um teste do proprio teste: alguem mudaria
  o piso no todos.html e a aritmetica daqui continuaria verde sozinha.
"""
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGINA = os.path.join(RAIZ, "paginas", "todos.html")

falhas = []


def ok(cond, msg):
    print(("  ok   " if cond else "  FALHOU  ") + msg)
    if not cond:
        falhas.append(msg)


# --------------------------------------------------------------------------
# 1. AS CONSTANTES SAO LIDAS DO ARQUIVO, nao decoradas aqui.
# --------------------------------------------------------------------------
print("1. AS CONSTANTES VEM DO todos.html")

with io.open(PAGINA, encoding="utf-8") as f:
    fonte = f.read()

m = re.search(
    r"var CAPA_LINHA_MIN\s*=\s*([\d.]+),\s*CAPA_LINHA_MAX\s*=\s*([\d.]+),"
    r"\s*CAPA_LINHA_PISO\s*=\s*([\d.]+)",
    fonte,
)
ok(m is not None, "as tres constantes existem e sao declaradas juntas")
if m is None:
    print("\n⛔ sem as constantes o resto nao tem o que medir")
    sys.exit(1)

MIN, MAX, PISO = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
# ⭐ 25/09/2026 — O QUE ESTA' NO AR VALE (decisao do dono): a linha da capa
# ficou FIXA em 11 px (MIN = MAX = PISO = 11). O ajustador que crescia de
# 12,5 a 13 px saiu; as verificacoes dele (secoes 2-5 antigas, commit
# f918d6d) descreviam um comportamento que nao existe mais.
ok(MIN == 11.0, "CAPA_LINHA_MIN = 11 (fixo)")
ok(MAX == 11.0, "CAPA_LINHA_MAX = 11 (fixo: nao cresce)")
ok(PISO == 11.0, "CAPA_LINHA_PISO = 11 (o piso do Impeccable, typeset.md)")
ok(MIN == MAX == PISO, "os tres iguais: o tamanho nao depende da tela")

print("\n2. NEGATIVO — nenhum tamanho abaixo do piso de leitura")
ok(min(MIN, MAX) >= 11.0, "nada abaixo de 11 px (legibilidade no celular)")

# --------------------------------------------------------------------------
# 6. O SSR nao pode morrer aqui (o erro 4.4 do handoff de 22/09).
# --------------------------------------------------------------------------
print("\n6. O SSR CONTINUA PROTEGIDO")
ok(
    re.search(r"try \{ ajustarLinhasCapaJa\(pl\); \} catch \(e\)", fonte) is not None,
    "a chamada segue dentro de try/catch (o jsdom nao mede texto)",
)
ok(
    re.search(r"if \(!document\.createRange\) \{ return null; \}", fonte) is not None
    and re.search(r"if \(!medidos\.length\) \{ return; \}", fonte) is not None,
    "sem medida a linha devolve `null` e o ajuste sai sem tocar em nada",
)

# --------------------------------------------------------------------------
print("")
if falhas:
    print("⛔ %d FALHA(S):" % len(falhas))
    for f in falhas:
        print("   - " + f)
    sys.exit(1)
print("tudo verde")
