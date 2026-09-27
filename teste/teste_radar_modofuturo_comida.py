# -*- coding: utf-8 -*-
"""Radar do @modofuturo: salgadinho nao e' chip (27/09/2026).

"Lay's Potato Chips", "Pringles" e "Jackfruit Chips" chegaram ao topo do radar
(notas 80-81): "chip" esta' no NUCLEO e casava com salgadinho. Os titulos
abaixo sao os REAIS daquela rodada.
"""
import importlib.util
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("radar", RAIZ / "canais" / "modofuturo" / "radar.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def passa(titulo, canal):
    t = (titulo + " " + canal).lower()
    return (not any(x in t for x in R.VETO) and any(x in t for x in R.TEMA)
            and not any(x in t for x in R.FORA_DO_TEMA) and any(x in t for x in R.NUCLEO))


falhas = 0
for tit, can in [("How Lay's Potato Chips Are Made In Factory | The Incredible Process", "Food Tech Today"),
                 ("Inside a Modern Pringles Factory, From Whole Potatoes to Stacked", "Sketchy Survival 710"),
                 ("Inside a Jackfruit Chips Factory - How They Make the Perfect Crunch", "The Mascot Vibrators")]:
    ok = not passa(tit, can); falhas += not ok
    print(("  ok    barrado: " if ok else "  FALHA passou: ") + tit[:50])
for tit, can in [("I shrunk down into an M5 chip", "Marques Brownlee"),
                 ("Inside Intel's $20 Billion Chip Factory in the US", "FRAME"),
                 ("There's a Class 100 semiconductor cleanroom inside this backyard shed.", "Dr.Semiconductor")]:
    ok = passa(tit, can); falhas += not ok
    print(("  ok    passa:   " if ok else "  FALHA barrado: ") + tit[:50])
print("\ntudo verde" if not falhas else f"\n{falhas} FALHA(S)")
sys.exit(1 if falhas else 0)
