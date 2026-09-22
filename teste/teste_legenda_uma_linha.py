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
ok(MIN == 12.5, "CAPA_LINHA_MIN = 12,5 (o degrau PREFERIDO, nao o piso)")
ok(MAX == 13.0, "CAPA_LINHA_MAX = 13 (2 px abaixo do papel de apoio)")
ok(PISO == 11.0, "CAPA_LINHA_PISO = 11 (o piso do Impeccable, typeset.md)")

# a decisao coletiva tem de estar no arquivo, e nao linha a linha
ok(
    "cabemTodas" in fonte
    and re.search(r"var cabemTodas = Math\.min\.apply\(null, medidos\) >= CAPA_LINHA_PISO",
                  fonte) is not None,
    "a decisao 'cabe numa linha' e' COLETIVA (cabemTodas, sobre o MENOR alvo)",
)
ok(
    re.search(r"l\.style\.whiteSpace = cabemTodas \? \"nowrap\" : \"\";", fonte) is not None,
    "e e' cabemTodas -- nao um 'cabe' por linha -- que decide o nowrap",
)


# --------------------------------------------------------------------------
# 2. A MESMA ARITMETICA DO ARQUIVO, em Python.
# --------------------------------------------------------------------------
def alvos_de(tela):
    """Os alvos das duas linhas nessa largura de tela.

    ⚠ CADA LINHA TEM SUA PROPRIA LARGURA UTIL, e isso nao e' detalhe: a
      legenda mede contra `.escala` (o pai) e a linha da loja contra ela
      mesma. Escrevi este teste com UMA largura so' para as duas, e ele
      reprovou -- com um valor unico a linha mais CURTA ganha o alvo MAIOR,
      que e' o inverso do que o navegador mostrou. As duas larguras abaixo
      sao derivadas das medidas reais a 375 px (alvos 12,45 e 12,05).
    """
    return [
        # Math.floor(MIN * disp / natural * 20) / 20
        int(MIN * (disp375 * tela / 375.0) / natural * 20) / 20.0
        for natural, disp375 in ((LEGENDA, UTIL_LEGENDA_375),
                                 (LOJA, UTIL_LOJA_375))
    ]


def ajustar(tela):
    """Devolve [(tamanho_px, uma_linha), ...] para cada linha."""
    alvos = alvos_de(tela)
    juntas = max(alvos) - min(alvos) <= 1
    comum = min(alvos)
    cabem_todas = min(alvos) >= PISO
    saida = []
    for a in alvos:
        ideal = a if juntas else comum
        tam = min(MAX, ideal) if cabem_todas else MIN
        saida.append((tam, cabem_todas))
    return saida


# MEDIDO no ar a 375 px, na capa do dia:
#   a frase da legenda ocupa 302 px a 12,5 px, e tem 300,8 px de largura util
#   a frase da loja    ocupa 298 px a 12,5 px, e tem 287,3 px de largura util
# (as duas uteis vem dos alvos que o navegador devolveu: 12,45 e 12,05.)
# A largura util cresce proporcional a' tela.
LEGENDA, LOJA = 302.0, 298.0
UTIL_LEGENDA_375, UTIL_LOJA_375 = 300.8, 287.3


# --------------------------------------------------------------------------
print("\n2. POSITIVO — nas telas comuns, TUDO numa linha so'")
for tela in (360, 375, 390, 412, 430):
    r = ajustar(tela)
    ok(
        all(uma for _, uma in r),
        "a %d px as duas linhas cabem inteiras (%s)"
        % (tela, ", ".join("%.2f px" % t for t, _ in r)),
    )

print("\n   e nenhuma delas fura o piso nem o teto")
for tela in (360, 375, 390, 430):
    r = ajustar(tela)
    ok(
        all(PISO <= t <= MAX for t, _ in r),
        "a %d px os tamanhos ficam entre 11 e 13 px (%s)"
        % (tela, ", ".join("%.2f px" % t for t, _ in r)),
    )

# --------------------------------------------------------------------------
print("\n3. ⛔ NEGATIVO — a 320 px NAO cabe, e o piso manda")
r = ajustar(320)
ok(
    not any(uma for _, uma in r),
    "a 320 px nenhuma linha e' forcada a uma linha so'",
)
ok(
    all(t == MIN for t, _ in r),
    "e as duas voltam ao degrau preferido de 12,5 px, livres para quebrar",
)

# --------------------------------------------------------------------------
print("\n4. ⛔ NEGATIVO — a decisao e' COLETIVA (o defeito de 340 px)")
r = ajustar(340)
# a 340 px a legenda daria 11,3 e a loja 10,9 -- uma cabe, a outra nao
alvos340 = alvos_de(340)
ok(
    alvos340[0] >= PISO and alvos340[1] < PISO,
    "a 340 px e' mesmo o caso misto (legenda %.2f >= 11, loja %.2f < 11)"
    % tuple(alvos340),
)
ok(
    len(set(t for t, _ in r)) == 1,
    "e mesmo assim as duas saem com o MESMO tamanho (%s)"
    % ", ".join("%.2f px" % t for t, _ in r),
)
ok(
    not any(uma for _, uma in r),
    "as duas quebram JUNTAS -- nunca 11,3 inteira ao lado de 12,5 quebrada",
)

# --------------------------------------------------------------------------
print("\n5. ⛔ NEGATIVO — este teste e' SENSIVEL (senao nao guarda nada)")
# com o piso antigo (12,5 como minimo absoluto), a 375 px a legenda
# NAO caberia -- que e' exatamente o defeito que o Bryan fotografou.
alvo375 = alvos_de(375)[0]
ok(
    alvo375 < MIN,
    "a 375 px o tamanho necessario (%.2f px) e' MENOR que 12,5 -- por isso "
    "o ajustador antigo, que so' crescia, deixava quebrar" % alvo375,
)
ok(
    alvo375 >= PISO,
    "e ele so' e' alcancavel porque o piso caiu para 11 px",
)

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
