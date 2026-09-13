# -*- coding: utf-8 -*-
"""O corte editorial tira o obvio e NAO tira o que rende."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import rende_video as rv  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


print("1. NEGATIVO — o que a pessoa ja' compra no automatico NAO rende")
# ⚠️ Sao nomes REAIS que o /highlights devolveu em 13/09/2026.
for nome in ("Papel Higiênico Supreme Folha Tripla 24 Rolos Neve",
             "Papel Higiênico Neve Toque Da Seda Folha Dupla 30 M",
             "Sabão Líquido Omo Lavagem Perfeita 900ml Refil",
             "Percarbonato De Sódio 100% Puro Tira Manchas Alvejante",
             "O Boticário Insensatez Deo Colônia 100ml"):
    ok, porque = rv.rende(nome)
    checar(not ok, f"{nome[:38]}… -> fora ({porque})")

print("\n2. ⭐ E O QUE RENDE TEM DE PASSAR — senao o filtro so' esvazia a lista")
for nome in ("Creatina 250g Suplemento Monohidratada em pó 100%",
             "Creme Multirreparador Pele Sensível Cicaplast Baume B5+",
             "Conjunto de pincéis de maquiagem profissional Kabuki",
             "Cortador de Melancia em Aço Inoxidável 2 em 1",
             "20 Peças de Organizadores de Cabos Adesivos",
             "Omegafor Plus 120 Cápsulas Ômega 3 Vitafor"):
    ok, porque = rv.rende(nome)
    checar(ok, f"{nome[:40]}… -> passa")

print("\n3. NEGATIVO — o filtro nao pode casar DENTRO de outra palavra")
# ⚠️ "neve" esta' em "neveira"; "veja" em "vejam". Filtro que casa demais
# reprova calado, e o produto so' some da lista sem ninguem notar.
for nome in ("Geladeira Neveira Portátil 12v para Carro",
             "Óculos de sol Vejam Style unissex"):
    ok, porque = rv.rende(nome)
    checar(ok, f"{nome[:36]}… -> passa (nao casou dentro da palavra)")

print("\n4. sem nome, nao rende")
checar(not rv.rende("")[0], "vazio -> fora")


print("")
print("5. ⭐ O CORTE POR IA CAI NA LISTA quando o modelo nao responde")
# ⚠️ FALHA ABERTA PARA A LISTA, nunca para o "sim". Modelo gratis nao e'
# contrato: MEDIDO em 13/09/2026, o llama-3.3-70b:free SAIU do plano gratis e
# passou a devolver 404. Deixar passar tudo seria trocar filtro grosseiro por
# filtro nenhum — e papel higienico voltaria pro canal de beleza.
import engine.rende_video as _rv  # noqa: E402
_orig = _rv._pedir
_rv._pedir = lambda *a, **k: None
prods = [{"nome": "Papel Higiênico Neve 30m"},
         {"nome": "Cortador de melancia 2 em 1"}]
fica, fora = _rv.peneirar_com_ia(prods)
checar(len(fica) == 1, "sem o modelo, a lista ainda corta o obvio")
checar(fica[0]["nome"].startswith("Cortador"), "e deixa passar o que rende")
_rv._pedir = _orig

print("")
print("6. NEGATIVO — resposta INCOMPLETA do modelo e' descartada")
# ⚠️ O modelo as vezes devolve 8 de 30 linhas. Aceitar isso deixaria 22
# produtos sem julgamento e ninguem notaria — a lista so' viria menor.
_rv._pedir = lambda titulos, tentativa=1: {0: (False, "so um julgado")}
muitos = [{"nome": f"Produto util numero {i}"} for i in range(10)]
fica2, _ = _rv.peneirar_com_ia(muitos)
checar(len(fica2) == 10,
       "1 julgamento de 10 -> descarta o modelo e mantem a lista")
_rv._pedir = _orig

print("")
print("7. a lista roda ANTES do modelo, e isso nao e' redundancia")
# ⚠️ Ela e' barata e deterministica: tira o lixo evidente sem gastar chamada.
fonte = Path("engine/rende_video.py").read_text(encoding="utf-8")
import re as _re  # noqa: E402
plano = _re.sub(r"[\s#]+", " ", fonte)
checar("A LISTA CONTINUA RODANDO ANTES" in plano, "esta' escrito no codigo")
checar("TENTATIVAS_MAX" in fonte, "ha' teto de chaves por rodada")
checar(_rv.TEMPO_S <= 30, "e timeout curto: o corte e' bonus, nao pode segurar")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
