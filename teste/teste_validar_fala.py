# -*- coding: utf-8 -*-
"""Todo descarte do `_validar` diz o motivo.

POR QUE EXISTE

No run #194 (31/08/2026) o Gemini respondeu, o validador recusou TODOS os
momentos, e o log inteiro sobre isso foi UMA linha:

    nenhum momento aprovado na validação.

Nao dava pra saber se o problema era duracao, sobreposicao, campo faltando ou
gancho — e sem saber, a unica saida era redisparar no escuro e torcer.

`_validar` tem QUATRO caminhos de descarte e so' UM deles falava (o gancho
fraco). Os outros tres eram `continue` calado.

⚠️ Recusa silenciosa e' o defeito que mais custou tempo neste projeto. Ela nao
levanta excecao, nao reprova teste e nao aparece em log — some. Ja' apareceu
hoje na dedup (enxergava 13 de 101), no registro de rejeitados (inerte na
nuvem), no filtro de tema do radar de maquiagem (derrubava video bom) e no
detector de contagem do radar da cozinha (achava 0 de 42).

Roda com: python teste/teste_validar_fala.py
"""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import os  # noqa: E402
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

import config  # noqa: E402
from engine import selecao  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def validar_capturando(clipes, dur=800.0):
    buf = io.StringIO()
    with redirect_stdout(buf):
        bons = selecao._validar(clipes, dur)
    return bons, buf.getvalue()


print(__doc__.splitlines()[0])

# Um caso por caminho de descarte, mais um que passa.
CASOS = [
    {"titulo": "curto", "inicio_s": 10, "fim_s": 40,
     "nota": 90, "forca_gancho": 9},
    {"titulo": "sem fim_s", "inicio_s": 10, "nota": 90, "forca_gancho": 9},
    {"titulo": "gancho fraco", "inicio_s": 100, "fim_s": 200,
     "nota": 90, "forca_gancho": 1},
    {"titulo": "bom", "inicio_s": 300, "fim_s": 390,
     "nota": 95, "forca_gancho": 9},
    {"titulo": "sobrepoe o bom", "inicio_s": 320, "fim_s": 410,
     "nota": 80, "forca_gancho": 9},
]
bons, saida = validar_capturando(CASOS)

print("\n[1] o resultado continua correto")
checar([c["titulo"] for c in bons] == ["bom"],
       f"so' o clipe bom passa (passaram: {[c['titulo'] for c in bons]})")

print("\n[2] CADA descarte aparece no log, com o titulo")
for titulo, pista in [("gancho fraco", "gancho"),
                      ("curto", "curto demais"),
                      ("sem fim_s", "tempo ilegivel"),
                      ("sobrepoe o bom", "sobrepoe")]:
    linha = [l for l in saida.splitlines() if titulo in l]
    checar(bool(linha) and pista in linha[0],
           f'"{titulo}" -> motivo "{pista}"')

print("\n[3] o motivo vem com o NUMERO, nao so' o rotulo")
checar("< DUR_MIN" in saida, "o curto diz o limite que violou")
checar("30.8s" in saida or "30.9s" in saida, "e diz a duracao que tinha")
checar("KeyError" in saida, "o ilegivel diz qual excecao foi")

print("\n[4] quando NADA passa, o log diz de quantos era")
_, so_ruins = validar_capturando([CASOS[0], CASOS[2]])
checar("NENHUM passou" in so_ruins, "avisa que nenhum passou")
checar("2 momento" in so_ruins, "diz quantos o modelo devolveu")

print("\n[5] o caso NEGATIVO: lote bom nao ganha ruido")
limpos = [{"titulo": f"c{i}", "inicio_s": 100 * i, "fim_s": 100 * i + 90,
           "nota": 90, "forca_gancho": 8} for i in range(1, 5)]
bons2, saida2 = validar_capturando(limpos, 900.0)
checar(len(bons2) == 4, f"os 4 passam (passaram {len(bons2)})")
checar("[!]" not in saida2, "nenhuma linha de descarte num lote todo bom")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
