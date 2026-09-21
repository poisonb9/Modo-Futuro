# -*- coding: utf-8 -*-
"""`/todos` do SITE MAE redireciona para a raiz -- e o das bios NAO.

## ⛔ POR QUE ESTE TESTE EXISTE

MEDIDO no ar em 21/09/2026:

    achadinhototal.com.br/motor.js        200  application/javascript  226 KB
    achadinhototal.com.br/todos/motor.js  200  text/html               114 KB

No site mae a raiz E' o catalogo e os externos ficam na raiz: a pasta
`todos/` nunca e' criada. Quem abria `/todos/` recebia a pagina raiz (o
Pages devolve a raiz para caminho inexistente) e o `src="motor.js"`
RELATIVO virava `/todos/motor.js`, que devolve HTML. O navegador recusa por
MIME e a pagina fica SEM JS NENHUM -- sem lupa, sem filtro, sem link.

⚠ O sintoma engana: tudo responde 200, e `/todos` SEM barra funcionava
(o relativo resolve para `/motor.js`). Por isso a conferencia do publicador
passava verde ha' dias.

⭐ E O CASO NEGATIVO E' METADE DO TESTE: nas BIOS `/todos/` e' pagina de
verdade, com o motor ao lado. Redirecionar la' apagaria o catalogo dos 5
canais. O `_redirects` tem de ser escrito SO' no site mae.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
import publicar_bio as pb  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


print("1. A REGRA EXISTE, e manda /todos para a raiz")
regras = [l.strip() for l in pb.REDIRECTS.splitlines() if l.strip()]
checar(any(l.startswith("/todos/*") and l.endswith("301") for l in regras),
       "/todos/* -> / com 301 (a forma COM barra, que era a quebrada)")
checar(any(l.split()[0] == "/todos" and l.endswith("301") for l in regras),
       "/todos -> / com 301 (a forma sem barra, para nao sobrar dois enderecos)")
checar(any(l.startswith("https://www.") for l in regras),
       "a regra do www de 17/09 continua ali (nao foi sobrescrita)")

print()
print("2. ⛔ NEGATIVO: o _redirects e' SO' do site mae")
FONTE = (RAIZ / "paginas" / "publicar_bio.py").read_text(encoding="utf-8")
escritas = re.findall(r'\(\s*(\w+)\s*/\s*"_redirects"\s*\)\.write_text', FONTE)
checar(escritas == ["casa"],
       f"_redirects escrito uma vez, e em `casa`: {escritas}")
checar('(pasta / "_redirects")' not in FONTE,
       "a pasta das BIOS nao recebe _redirects (la' /todos/ e' pagina real)")

print()
print("3. ⛔ NEGATIVO: a pasta das bios continua montando /todos com o motor")
checar('(pasta / "todos").mkdir()' in FONTE,
       "as bios seguem criando a pasta todos/")
checar('(pasta / "todos" / nome).write_text' in FONTE,
       "e os externos (motor.js incluso) seguem indo para dentro dela")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
