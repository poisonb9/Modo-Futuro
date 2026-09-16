# -*- coding: utf-8 -*-
"""Os sinais de preco saem so' da serie, e cada um dispara no caso certo. Sem rede.

⛔ Casos negativos teorematicos: oscilacao < 2% nao e' sinal; subida que ja'
esta' a menos de 5% do maior NAO e' 'ultima chance'; sem leitura de hoje,
nada — sinal e' sobre o que aconteceu HOJE.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import sinais  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


H = "2026-09-16"
def sinal(dias, hoje=None):
    s = sinais.sinal_de(dias, hoje, H)
    return s["tipo"] if s else None

print("1. OS QUATRO SINAIS")
checar(sinal({"2026-09-12": 230.0, "2026-09-14": 191.0, "2026-09-15": 230.4}, 191.33) == "voltou_a_cair",
       "caiu hoje ate' o menor visto DEPOIS de ter subido => voltou_a_cair")
checar(sinal({"2026-09-14": 12.6, "2026-09-15": 12.6}, 11.97) == "novo_minimo",
       "caiu hoje abaixo de tudo, sem ter subido antes => novo_minimo")
checar(sinal({"2026-09-14": 48.79, "2026-09-15": 43.49}, 45.11) == "ultima_chance",
       "subiu hoje mas ainda >= 5% abaixo do maior => ultima_chance")
checar(sinal({"2026-09-14": 48.79, "2026-09-15": 43.49}, 48.0) == "subiu",
       "subiu e ja' esta' a menos de 5% do maior => subiu (sem post)")

print()
print("2. ⛔ NEGATIVOS")
checar(sinal({"2026-09-14": 10.0, "2026-09-15": 10.0}, 10.15) is None, "1,5% nao e' sinal (cambio)")
checar(sinal({"2026-09-14": 10.0, "2026-09-15": 9.0}, 9.5) == "ultima_chance", "exatamente 5% abaixo do maior ainda e' 'ultima chance' (limite inclusivo)")
checar(sinal({"2026-09-14": 10.0, "2026-09-15": 9.0}, 9.6) == "subiu", "a 4% do maior nao e' mais 'ultima chance': so' 'subiu'")
checar(sinal({"2026-09-14": 10.0, "2026-09-15": 9.0}, None) is None, "sem leitura de hoje => nada")
checar(sinal({}, 9.0) is None, "sem historico => nada")
checar(sinal({"2026-09-14": 10.0, "2026-09-15": 9.0}, 9.15) is None,
       "+1,7% sobre ontem: abaixo do piso de 2% => nada")

print()
print("3. A FRASE DIZ O FATO, com os dois precos")
f = sinais.frase({"tipo": "voltou_a_cair", "ontem": 230.4, "hoje": 191.33, "menor": 191.0, "maior": 230.4})
checar("230,40" in f and "191,33" in f and "voltou a cair" in f, f)
f = sinais.frase({"tipo": "ultima_chance", "ontem": 43.49, "hoje": 45.11, "menor": 43.49, "maior": 48.79})
checar("48,79" in f and "última chance" in f, f)

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
