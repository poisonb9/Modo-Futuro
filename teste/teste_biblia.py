# -*- coding: utf-8 -*-
"""Guarda da Bíblia da dublagem (engine/biblia.py + .claude/skills/biblia-da-dublagem).

POR QUE EXISTE

26/09/2026: o prompt de narração era UM para todos os canais, e nome de idol
saía lido letra a letra pela voz. A Bíblia de cada canal entra no prompt (tom,
glossário, proibido) e na FALA (pronúncia) — nunca na legenda.

  [1] os 7 canais do registro têm bíblia com as 5 seções
  [2] o bloco do canal entra no prompt de narração E no literal; canal sem
      bíblia deixa o prompt como antes (NEGATIVO)
  [3] pronúncia: troca palavra inteira, sem ligar pra maiúscula; o "(a
      conferir)" não vai pra voz; palavra DENTRO de outra não é trocada
  [4] a legenda não passa pela pronúncia (só `_falar` e `dublagem` chamam)

Roda com: python teste/teste_biblia.py
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

from engine import biblia, canais_registro, traducao  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])

print("\n[1] todo canal do registro tem bíblia completa")
for nome in canais_registro.CANAIS:
    s = biblia.secoes(nome)
    faltam = [x for x in ("tom", "voz", "pronúncia", "glossário", "proibido") if x not in s]
    checar(not faltam, f"{nome}: {'completa' if not faltam else 'falta ' + ', '.join(faltam)}")

print("\n[2] o bloco entra nos dois prompts, e só com canal conhecido")
os.environ["CANAL_ESPERADO"] = "truque.importado"
narr = traducao._montar(traducao.PROMPT_NARRACAO, "FALA_XYZ", None, 60)
lit = traducao._montar(traducao.PROMPT, "TEXTO")
checar("BÍBLIA DO CANAL" in narr and "Amiga contando" in narr, "narração recebe o tom do make")
checar("BÍBLIA DO CANAL" in lit, "literal (voice-over) também recebe")
checar(narr.index("BÍBLIA") < narr.index("FALA_XYZ"), "a bíblia vem antes da fala original")
os.environ["CANAL_ESPERADO"] = "modofuturo"
checar("wafer" in traducao._montar(traducao.PROMPT_NARRACAO, "T", None, 60),
       "chips recebe o glossário de chips")
os.environ["CANAL_ESPERADO"] = "canal_que_nao_existe"
checar("BÍBLIA" not in traducao._montar(traducao.PROMPT_NARRACAO, "T", None, 60),
       "NEGATIVO: canal desconhecido = prompt como antes")
os.environ.pop("CANAL_ESPERADO")
checar("BÍBLIA" not in traducao._montar(traducao.PROMPT, "T"), "NEGATIVO: sem canal = como antes")

print("\n[3] pronúncia só na fala")
f = biblia.para_fala("A risabae maquiou a Wonhee do ILLIT.", "truque.importado")
print(f"       {f}")
checar("Rissabé" in f and "Ílit" in f, "troca sem ligar pra maiúscula")
checar("conferir" not in f and "Uônri" in f, "'(a conferir)' não vai pra voz")
checar(biblia.para_fala("Felixandro", "truque.importado") == "Felixandro",
       "NEGATIVO: palavra dentro de outra não é trocada")
checar(biblia.para_fala("Stray Kids", "truque.importado") == "Strêi Quids",
       "nome de duas palavras troca inteiro")
checar(biblia.para_fala("Risabae", "canal_que_nao_existe") == "Risabae",
       "NEGATIVO: canal sem bíblia não mexe no texto")

print("\n[4] a legenda não passa pela pronúncia")
usos = [p.relative_to(RAIZ).as_posix() for p in (RAIZ / "engine").glob("*.py")
        if "para_fala(" in p.read_text(encoding="utf-8") and p.name != "biblia.py"]
# conferencia.py usa para comparar o que a voz OUVIU com o que ela RECEBEU
checar(sorted(usos) == ["engine/conferencia.py", "engine/dublagem.py", "engine/voz_clonada.py"],
       f"só os caminhos de VOZ (e a conferência dela) chamam para_fala ({usos})")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
