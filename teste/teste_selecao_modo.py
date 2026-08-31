# -*- coding: utf-8 -*-
"""Teste do criterio de corte por canal (`SELECAO_MODO`).

POR QUE EXISTE

Em 31/08/2026 o Bryan olhou a receita do canal de maquiagem e disse que corte
comecando no meio de uma maquiagem, ou parando antes de ela terminar, ou com
passo faltando, e' **inadmissivel**.

O motor fazia exatamente isso, e nao por acaso: o unico criterio de corte que
existia e' RETORICO, e ele MANDA terminar abrupto —

    "Termine logo apos o pico (frase mais forte), de forma ABRUPTA"

Num canal de fala isso e' tensao e segura a retencao. Num canal de
procedimento e' um video quebrado.

O QUE ESTE TESTE PROTEGE

O `selecao.py` e' compartilhado pelos CINCO canais. Quatro deles ja' estao no
ar e dependem do texto antigo. Uma mudanca de prompt nao quebra teste, nao
levanta excecao e nao aparece em log: ela sai como corte pior, semanas depois.

Por isso o caso NEGATIVO aqui e' o principal: **sem `SELECAO_MODO`, o prompt
tem de ficar byte a byte identico ao de antes.** O caso positivo (o modo novo
funciona) sozinho nao provaria nada — um criterio que substituisse o prompt
inteiro em todo disparo tambem passaria nele.

Roda com: python teste/teste_selecao_modo.py
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def monta(modo):
    """O texto do prompt como `escolher()` o montaria, sem tocar na rede."""
    if modo is None:
        os.environ.pop("SELECAO_MODO", None)
    else:
        os.environ["SELECAO_MODO"] = modo
    import importlib
    from engine import selecao
    importlib.reload(selecao)
    import config
    return selecao.PROMPT.format(tipo="vídeo", n=5,
                                 criterio=selecao._criterio(),
                                 dmin=config.DUR_MIN, dmax=config.DUR_MAX)


print(__doc__.splitlines()[0])

# --- 1. o caso NEGATIVO, que e' o que protege os 4 canais no ar ----------
print("\n[1] sem SELECAO_MODO, o prompt nao pode ter mudado")
padrao = monta(None)
checar("ESTRUTURA GPC (Gancho-Progresso-Clímax)" in padrao,
       "o criterio retorico continua no prompt")
checar("de forma abrupta" in padrao,
       "a instrucao de terminar abrupto continua (os canais de fala usam)")
checar("Corte em pausa natural da fala" in padrao,
       "o corte em pausa de fala continua")
checar("UNIDADE COMPLETA DE PROCEDIMENTO" not in padrao,
       "o criterio de maquiagem NAO vaza pro disparo padrao")
checar("{criterio}" not in padrao, "nenhum placeholder sobrou por preencher")

# A PROVA FORTE: comparar com o texto que estava no git ANTES da mudanca.
# As checagens acima confirmam que os pedacos certos estao la'; so' esta
# confirma que NADA mudou — nem um espaco, nem uma linha em branco. Foi
# exatamente uma linha em branco a mais que ela pegou na primeira tentativa.
import subprocess
try:
    antes = subprocess.run(["git", "show", "HEAD:engine/selecao.py"],
                           cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8", check=True).stdout
except Exception as e:
    print(f"  aviso  git indisponivel, prova byte a byte pulada ({str(e)[:40]})")
else:
    import config
    i = antes.index('PROMPT = """')
    j = antes.index('"""', i + 12) + 3
    ns = {}
    exec(compile(antes[i:j], "antes", "exec"), ns)
    if "{criterio}" in ns["PROMPT"]:
        print("  aviso  HEAD ja' tem o criterio por canal; prova nao se aplica")
    else:
        velho = ns["PROMPT"].format(tipo="vídeo", n=5,
                                    dmin=config.DUR_MIN, dmax=config.DUR_MAX)
        checar(velho == padrao,
               "prompt padrao IDENTICO byte a byte ao do git HEAD")

# valor desconhecido cai no antigo, nao derruba o run
esquisito = monta("modo-que-nao-existe")
checar(esquisito == padrao,
       "valor desconhecido cai no criterio antigo (falha ABERTA)")
checar(monta("") == padrao, "string vazia tambem cai no antigo")

# --- 2. o caso positivo ---------------------------------------------------
print("\n[2] com SELECAO_MODO=procedimento, o criterio troca")
proc = monta("procedimento")
checar("UNIDADE COMPLETA DE PROCEDIMENTO" in proc, "o criterio novo entra")
checar("ESTRUTURA GPC" not in proc, "o criterio retorico SAI (nao se somam)")
checar("de forma abrupta" not in proc.split("INADMISSIVEL")[0],
       "a instrucao de terminar abrupto nao sobrevive antes do bloco de veto")

print("\n[3] o criterio novo proibe, nominalmente, o que o Bryan listou")
for frase, oque in [
        ("comecar com a maquiagem ja pela metade", "comecar no meio"),
        ("terminar antes de a etapa fechar", "nao terminar"),
        ("faltar um passo no meio", "faltar parte"),
        ("DESCARTE o video", "descartar em vez de entregar quebrado")]:
    checar(frase in proc, f"proibe: {oque}")

print("\n[4] maiusculas/minusculas e espacos nao driblam a guarda")
checar(monta("PROCEDIMENTO") == proc, "PROCEDIMENTO em caixa alta funciona")
checar(monta("  procedimento  ") == proc, "com espacos em volta funciona")

os.environ.pop("SELECAO_MODO", None)
print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
