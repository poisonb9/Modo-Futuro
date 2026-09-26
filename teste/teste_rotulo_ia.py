# -*- coding: utf-8 -*-
"""Todo post agendado sai com o rótulo "feito com IA" do TikTok.

POR QUE EXISTE

26/09/2026, revisão de riscos (+acervo) pedida pelo dono: a voz é clonada e
o TikTok pede rótulo em áudio realista gerado por IA. O rótulo JÁ existia
(`agendar_buffer.py`, `metadata.tiktok.isAiGenerated`), mas nenhum teste o
guardava: uma edição no payload o tiraria em silêncio, e nada acusaria.

  [1] o payload do createPost leva isAiGenerated = True
  [2] só existe UM createPost no repositório — um segundo caminho de
      publicação nasceria sem o rótulo
  [3] os workflows que publicam chamam o agendar_buffer (não outro script)

Roda com: python teste/teste_rotulo_ia.py
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])

print("\n[1] rótulo no payload")
ab = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")
checar(re.search(r'"metadata":\s*\{\s*"tiktok":\s*\{\s*"isAiGenerated":\s*True', ab) is not None,
       "createPost manda metadata.tiktok.isAiGenerated = True")

print("\n[2] um só caminho de publicação")
ignorar = ("node_modules", "teste", ".git", "site_no_ar", "_privado")
com_create = [p.relative_to(RAIZ).as_posix() for p in RAIZ.rglob("*.py")
              if not any(x in p.parts for x in ignorar)
              and "createPost(" in p.read_text(encoding="utf-8", errors="ignore")]
checar(com_create == ["agendar_buffer.py"], f"createPost só no agendar_buffer ({com_create})")

print("\n[3] workflows publicam pelo agendar_buffer")
wf = RAIZ / ".github" / "workflows"
for nome in ("cortar.yml", "cortar_de_bruto.yml"):
    checar("agendar_buffer.py" in (wf / nome).read_text(encoding="utf-8"),
           f"{nome} enfileira pelo agendar_buffer")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
