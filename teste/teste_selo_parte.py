"""Selo "NOME · PARTE N" (27/09/2026: tudo saia PARTE 3).

Dentro do mesmo corte o numero tem de SUBIR, e nome novo comeca em 1.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import selo  # noqa: E402

erros = 0
def checar(ok, msg):
    global erros
    erros += not ok
    print("  ok  " if ok else "  ERRO", msg)

u = {}
a, b, c = (selo.parte_do_tema("truque.importado", "Wonhee", u) for _ in range(3))
checar(b == a + 1 and c == a + 2, f"mesmo corte sobe: {a}, {b}, {c}")
checar(selo.parte_do_tema("truque.importado", "NomeQueNuncaApareceu", {}) == 1, "nome novo = 1")
checar(selo.parte_do_tema("truque.importado", "", {}) == 1, "sem nome = 1")
print("\ntudo verde" if not erros else f"\n{erros} ERRO(S)")
sys.exit(1 if erros else 0)
