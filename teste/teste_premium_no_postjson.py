# -*- coding: utf-8 -*-
"""Todo campo que a LEGENDA usa tem de estar na lista do post.json.

O post.json e' montado por uma copia POR NOMES em main.py. O que nao esta'
nessa lista nao chega ao arquivo — mesmo tendo sido gerado — e o
`publicar_tiktok` le' justamente o post.json pra escrever o .txt do Drive.

MEDIDO em 31/08/2026: `legenda_premium` ficou de fora da lista. O log dizia
"legenda premium: 1408 chars", o `post.txt` local saia completo, e o .txt que
chegava ao Drive tinha 0,3 KB, sem o bloco premium. Unificar as duas funcoes
de legenda (af01799) nao resolveu: o defeito nao era a montagem, era o dado
que nunca chegava.

⚠️ ESTE TESTE E' DA CLASSE, NAO DA INSTANCIA. Conferir so' `legenda_premium`
deixaria o proximo campo novo cair no mesmo buraco em silencio. Ele le' quais
campos a `legenda_post.montar` consome e exige TODOS na lista.
"""
import ast
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# ---- campos que a montagem da legenda consome ---------------------------
fonte_legenda = io.open(RAIZ / "engine" / "legenda_post.py", encoding="utf-8").read()
usados = set(re.findall(r'meta\.get\(["\'](\w+)["\']\)', fonte_legenda))
usados |= set(re.findall(r'for campo in \(([^)]*)\)', fonte_legenda)
             and re.findall(r'["\'](\w+)["\']',
                            re.findall(r'for campo in \(([^)]*)\)', fonte_legenda)[0]))

# ---- a lista branca do post.json ----------------------------------------
arv = ast.parse(io.open(RAIZ / "main.py", encoding="utf-8").read())
lista = None
for no in ast.walk(arv):
    if (isinstance(no, ast.DictComp) and isinstance(no.generators[0].iter, ast.Tuple)):
        itens = {e.value for e in no.generators[0].iter.elts
                 if isinstance(e, ast.Constant) and isinstance(e.value, str)}
        if "titulo" in itens:
            lista = itens
            break

if lista is None:
    print("  [x] nao achei a lista de campos do post.json em main.py")
    sys.exit(1)

falta = sorted(usados - lista)
if falta:
    print(f"  [x] a legenda usa {falta} e o post.json NAO carrega esses campos")
    print(f"      -> o .txt do Drive vai sair incompleto. Lista atual: {sorted(lista)}")
    sys.exit(1)

# ⚠️ CASO NEGATIVO: o teste tem de REPROVAR uma lista sem o premium. Sem
# isto, uma versao que sempre passa (por ler a lista errada, por exemplo)
# seria indistinguivel de uma que confere de verdade.
if not (usados - (lista - {"legenda_premium"})):
    print("  [x] o teste passaria mesmo sem legenda_premium — nao esta' medindo nada")
    sys.exit(1)

print(f"[ok] teste_premium_no_postjson: {sorted(usados)} todos no post.json")
