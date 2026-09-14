# -*- coding: utf-8 -*-
"""O nome reescrito nao pode inventar nada — nem numero, nem produto.

⚠️ Nao toca na rede: a conferencia e' funcao pura, e e' ela que decide.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import nome_produto as np  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


ORIGINAL = ("Conjunto de Esponjas de Maquiagem de 7 Pecas, Adequado para "
            "Aplicacao de BB Cream Liqui")

print("1. o nome bom passa")
ok, _ = np.confere(ORIGINAL, "Kit com 7 esponjas de maquiagem")
checar(ok, "nome curto, fiel e sem enfeite")

print("")
print("2. NEGATIVO - numero que nao existe no original")
# ⚠️ ESTE E' O DEFEITO CARO: "18 pecas" quando sao 7 vira reclamacao de quem
# comprou, e a promessa saiu de nos, nao do vendedor.
ok, porque = np.confere(ORIGINAL, "Kit com 18 esponjas de maquiagem")
checar(not ok, "recusa quantidade inventada (" + porque + ")")

print("")
print("3. NEGATIVO - nome de outro produto")
# Sem esta conferencia, "Kit de beleza completo" passaria em todo o resto.
ok, porque = np.confere("Luvas de treino com suporte de punho",
                        "Kit de beleza completo")
checar(not ok, "recusa nome sem relacao (" + porque + ")")

print("")
print("4. NEGATIVO - vazio, curto demais, longo demais e cortado")
checar(not np.confere(ORIGINAL, "")[0], "vazio")
checar(not np.confere(ORIGINAL, "Kit")[0], "curto demais")
checar(not np.confere(ORIGINAL, "Kit com esponjas de maquiagem para "
                      "aplicacao de BB cream e corretivo liquido")[0],
       "longo demais")
checar(not np.confere(ORIGINAL, "Kit com esponjas de maquiagem,")[0],
       "termina cortado")

print("")
print("5. a reserva e o corte do titulo, e ele e' honesto")
# ⚠️ Sem modelo, sem cache e sem rede o produto AINDA tem nome: pior nome,
# zero mentira. E' a mesma regra do desconto, que e' ZERO sem historico nosso.
curto = np.cortar(ORIGINAL)
checar(curto == "Conjunto de Esponjas de Maquiagem de 7 Pecas",
       "corta na primeira virgula: " + curto)
checar(len(np.cortar("Luvas de Levantamento de Peso com Suporte para Punho "
                     "Respiraveis Antiderrapantes para Academia")) <= np.LIMITE,
       "titulo sem virgula tambem cabe")

print("")
print("6. NEGATIVO - sem cache, nome_de NAO estoura e NAO inventa")
np.CACHE = Path(__file__).resolve().parent / "_nao_existe_.json"
checar(np.nome_de({"id": 123, "nome": ORIGINAL}) == curto,
       "cai na reserva sozinho")

print("")
print("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde")
sys.exit(1 if falhas else 0)
