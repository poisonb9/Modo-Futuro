# -*- coding: utf-8 -*-
"""A escolha da foto do cartao. Sem rede: as notas sao injetadas.

O que protege (18/09/2026):
1. extra mais limpa que a principal por mais de MARGEM -> troca;
2. ⛔ caso negativo: extra melhor por MENOS que a margem -> fica a principal
   (sem isto, ruido trocaria a foto a cada publicacao);
3. ⛔ falha ABERTA: sem nota da principal, fica a principal — cartao sem
   foto e' quebrado, foto pior e' so' feia;
4. sem extras, nem chama modelo.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import foto_limpa  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


M = foto_limpa.MARGEM
print("1. extra mais limpa por mais que a margem -> troca")
c = {"p.jpg": 0.05, "a.jpg": 0.05 + M + 0.01, "b.jpg": 0.02}
checar(foto_limpa.escolher("p.jpg", ["a.jpg", "b.jpg"], c) == "a.jpg", "escolhe a extra 'a'")

print("2. ⛔ extra melhor por MENOS que a margem -> fica a principal")
c = {"p.jpg": 0.05, "a.jpg": 0.05 + M - 0.001}
checar(foto_limpa.escolher("p.jpg", ["a.jpg"], c) == "p.jpg", "ruido nao troca a foto")

print("3. ⛔ falha aberta: principal sem nota -> principal")
chamadas = []
_nota = foto_limpa.nota
foto_limpa.nota = lambda u, cache=None: (chamadas.append(u), None)[1]
try:
    checar(foto_limpa.escolher("p.jpg", ["a.jpg"]) == "p.jpg", "sem nota fica a principal")
    checar(chamadas == ["p.jpg"], f"e nem mede as extras (chamou {chamadas})")
finally:
    foto_limpa.nota = _nota

print("4. sem extras nao mede nada")
chamadas = []
foto_limpa.nota = lambda u, cache=None: (chamadas.append(u), 0.5)[1]
try:
    checar(foto_limpa.escolher("p.jpg", []) == "p.jpg" and chamadas == [], "zero chamadas")
finally:
    foto_limpa.nota = _nota

print("5. o modulo explica por que o vetor da dedupe nao serve")
_fonte = Path(RAIZ / "engine" / "foto_limpa.py").read_text(encoding="utf-8")
checar("RECORTA" in _fonte, "o recorte e' o motivo, e esta' escrito")

print()
print("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde")
sys.exit(1 if falhas else 0)
