# -*- coding: utf-8 -*-
"""`_subiu`, o espelho de `_antes`: quando hoje E' o pico da serie, mostra o
MENOR ja' visto -- pra virar "voce perde R$ X" no cartao (Bryan, 23/09/2026,
print: "R$ 55,49 sem riscado" num produto que so' subiu).

⛔ Casos negativos teorematicos: hoje sendo o maior mas dentro do piso de 2%
nao e' subida; hoje NAO sendo o maior (queda real, `_antes` cobre) nunca
soma com `_subiu` -- os dois sao mutuamente exclusivos por construcao.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
sys.argv = ["x"]
import publicar_bio as pb  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


def d(preco):
    return {"id": "p1", "preco": f"R$ {preco:.2f}".replace(".", ",")}


print("1. O CASO POSITIVO — hoje e' o pico, sobe do menor visto")
serie = {"p1": ("2026-09-14", 5, 55.49, "2026-09-22")}
por_dia = {"p1": {"2026-09-14": 40.0, "2026-09-16": 45.0, "2026-09-22": 55.49}}
checar(pb._subiu(serie, por_dia, d(55.49)) == "R$ 40,00",
       "hoje = maior da serie, sobe > 2% do menor => devolve o MENOR")

print()
print("2. ⛔ NEGATIVOS")
checar(pb._subiu(serie, {"p1": {"2026-09-14": 55.0, "2026-09-22": 55.49}}, d(55.49)) == "",
       "sobe menos de 2% do menor (cambio/arredondamento) => nada")
serie_caiu = {"p1": ("2026-09-14", 3, 70.0, "2026-09-22")}
checar(pb._subiu(serie_caiu, por_dia, d(55.49)) == "",
       "hoje NAO e' o maior da serie (e' queda real, `_antes` cobre) => nada")
checar(pb._subiu({"p1": ("", 0, 0.0, "")}, por_dia, d(55.49)) == "",
       "sem serie (maior=0) => nada")
checar(pb._subiu(serie, {}, d(55.49)) == "",
       "sem por_dia (produto novo, sem historico) => nada")
checar(pb._subiu(serie, por_dia, {"id": "p1", "preco": ""}) == "",
       "sem preco de hoje => nada")

print()
print("3. MUTUAMENTE EXCLUSIVO COM `_antes`, no MESMO ponto")
# ⭐ o mesmo par (serie, d) nunca preenche os dois ao mesmo tempo
checar(bool(pb._antes(serie, d(55.49))) != True, "hoje = maior => `_antes` fica vazio (pre-condicao do teste)")
checar(pb._subiu(serie, por_dia, d(55.49)) != "" and pb._antes(serie, d(55.49)) == "",
       "quando `_subiu` preenche, `_antes` esta' vazio no MESMO par")
checar(pb._antes(serie_caiu, d(55.49)) != "" and pb._subiu(serie_caiu, por_dia, d(55.49)) == "",
       "e o inverso: quando `_antes` preenche (queda real), `_subiu` fica vazio")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
