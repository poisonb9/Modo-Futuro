# -*- coding: utf-8 -*-
"""engine/calendario.py: a data certa no canal certo, e NADA fora da janela."""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import calendario as c  # noqa: E402

D = datetime.date
casos = [
    # positivos
    (("camarim.kpop", "BANG CHAN do Stray Kids usa roupas", D(2026, 10, 3)), "aniversario de Bang Chan e' HOJE"),
    (("atefalhar", "", D(2026, 10, 8)), "Dia das Criancas em 4 dia(s)"),
    (("truque.importado", "", D(2026, 7, 25)), "volta as aulas em 3 dia(s)"),
    (("modofuturo", "", D(2026, 12, 20)), "Natal em 5 dia(s)"),
    # negativos: fora da janela, canal fora da lista, nome dentro de palavra
    (("atefalhar", "", D(2026, 9, 1)), ""),
    (("modofuturo", "", D(2026, 10, 10)), ""),
    (("camarim.kpop", "Hand cream chance", D(2026, 9, 14)), ""),
    (("semanestesia.pod", "Felix fala de disciplina", D(2026, 9, 15)), ""),
]
falhas = 0
for (canal, titulo, hoje), esperado in casos:
    r = c.ocasiao(canal, titulo, hoje)
    if r != esperado:
        falhas += 1
        print("FALHOU", canal, titulo, hoje, "->", repr(r), "esperado", repr(esperado))
assert c.dica("atefalhar", "", D(2026, 9, 1)) == ""
print("tudo verde" if not falhas else f"{falhas} falha(s)")
sys.exit(1 if falhas else 0)
