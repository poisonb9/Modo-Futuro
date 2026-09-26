# -*- coding: utf-8 -*-
"""Guarda do Guia de voz (engine/guia_voz.py + .claude/skills/guia-de-voz).

POR QUE EXISTE

26/09/2026: o prompt de narração era UM para todos os canais. O Guia de voz
de cada canal entra no prompt (tom, glossário, proibido).

⛔ PRONÚNCIA: o dono decidiu NÃO alterar ("não pode mudar a pronúncia",
26/09). As tabelas ficam vazias e este teste FALHA se alguém preenchê-las
sem pedido dele. Única exceção pedida por ele: "Wonhee" -> "Uônwee" no make.

  [1] os 7 canais do registro têm guia com as 5 seções
  [2] o bloco do canal entra no prompt de narração E no literal; canal sem
      guia deixa o prompt como antes (NEGATIVO)
  [3] nenhuma pronúncia é trocada, em canal nenhum
  [4] a legenda não passa pelo caminho de fala (só voz e conferência chamam)

Roda com: python teste/teste_guia_voz.py
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

from engine import guia_voz, canais_registro, traducao  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])

print("\n[1] todo canal do registro tem guia completo")
for nome in canais_registro.CANAIS:
    s = guia_voz.secoes(nome)
    faltam = [x for x in ("tom", "voz", "pronúncia", "glossário", "proibido") if x not in s]
    checar(not faltam, f"{nome}: {'completa' if not faltam else 'falta ' + ', '.join(faltam)}")

print("\n[2] o bloco entra nos dois prompts, e só com canal conhecido")
os.environ["CANAL_ESPERADO"] = "truque.importado"
narr = traducao._montar(traducao.PROMPT_NARRACAO, "FALA_XYZ", None, 60)
lit = traducao._montar(traducao.PROMPT, "TEXTO")
checar("GUIA DE VOZ DO CANAL" in narr and "Amiga contando" in narr, "narração recebe o tom do make")
checar("GUIA DE VOZ DO CANAL" in lit, "literal (voice-over) também recebe")
checar(narr.index("GUIA DE VOZ") < narr.index("FALA_XYZ"), "o guia vem antes da fala original")
os.environ["CANAL_ESPERADO"] = "modofuturo"
checar("wafer" in traducao._montar(traducao.PROMPT_NARRACAO, "T", None, 60),
       "chips recebe o glossário de chips")
os.environ["CANAL_ESPERADO"] = "canal_que_nao_existe"
checar("GUIA DE VOZ" not in traducao._montar(traducao.PROMPT_NARRACAO, "T", None, 60),
       "NEGATIVO: canal desconhecido = prompt como antes")
os.environ.pop("CANAL_ESPERADO")
checar("GUIA DE VOZ" not in traducao._montar(traducao.PROMPT, "T"), "NEGATIVO: sem canal = como antes")

print("\n[3] pronúncia NÃO muda (decisão do dono, 26/09), exceto Wonhee no make")
# ⭐ única exceção, pedida pelo dono em 26/09: "Wonhee" falada "Uônwee"
EXCECOES = {"truque.importado": (("Wonhee", "Uônwee"),)}
for nome in canais_registro.CANAIS:
    esperado = EXCECOES.get(nome, ())
    checar(guia_voz.pronuncias(nome) == esperado,
           f"{nome}: tabela = {esperado or 'vazia'} ({guia_voz.pronuncias(nome)})")
frase = "A Risabae maquiou a Wonhee do ILLIT e o Felix do Stray Kids."
checar(guia_voz.para_fala(frase, "truque.importado") ==
       "A Risabae maquiou a Uônwee do ILLIT e o Felix do Stray Kids.",
       "make: só a Wonhee muda na fala; Risabae, ILLIT e Felix ficam")
checar(guia_voz.para_fala(frase, "modofuturo") == frase, "outro canal: nada muda")

print("\n[4] a legenda não passa pela pronúncia")
usos = [p.relative_to(RAIZ).as_posix() for p in (RAIZ / "engine").glob("*.py")
        # `guia_voz.para_fala`; o `conversoes.para_fala` (unidade da receita) e' outro
        if "guia_voz.para_fala(" in p.read_text(encoding="utf-8") and p.name != "guia_voz.py"]
# conferencia.py usa para comparar o que a voz OUVIU com o que ela RECEBEU
checar(sorted(usos) == ["engine/conferencia.py", "engine/dublagem.py", "engine/voz_clonada.py"],
       f"só os caminhos de VOZ (e a conferência dela) chamam para_fala ({usos})")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
