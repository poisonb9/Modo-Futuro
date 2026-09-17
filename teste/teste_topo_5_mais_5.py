# -*- coding: utf-8 -*-
"""Os 10 primeiros da vitrine: 5 ate' R$ 99,90 + 5 livres, intercalados. Sem rede.

## POR QUE EXISTE (Bryan, 17/09/2026)

"Temos que levar em consideracao os itens baratos mas sempre tentar ganhar em
cima — nao podemos postar so' porque e' barato e nao lucrar." Teste de 30 dias
medido por clique.

⭐ Casos teorematicos: (1) intercala, barato abre; (2) ⛔ barato que rende
< R$ 3 NAO entra na cota dos baratos (vai pra livre, e la' perde pela nota);
(3) nome repetido nao entra duas vezes; (4) quem esta' no piso (vitrine_fora)
nunca entra; (5) sem baratos suficientes, os livres completam os 10.
"""
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


def c(nome, preco, ganho, nota, fora=""):
    return {"nome": nome, "preco": f"R$ {preco:.2f}".replace(".", ","), "ganho": ganho,
            "vitrine_nota": nota, "vitrine_fora": fora, "id": nome}


pb._MEMO_HOJE.clear()
raiz = pb.RAIZ
pb.RAIZ = Path(__file__).parent / "_inexistente"      # sem serie: _preco_hoje_num le o texto do cartao
try:
    print("1. INTERCALA, BARATO ABRE")
    dados = [c(f"Caro {i}", 120 + i, 10, 90 - i) for i in range(8)] + [c(f"Barato {i}", 50 + i, 5, 70 - i) for i in range(8)]
    top = pb.marcar_topo(dados)
    nomes = [p["nome"].split()[0] for p in top]
    checar(len(top) == 10 and nomes == ["Barato", "Caro"] * 5, f"5+5 intercalados, barato primeiro: {nomes}")
    checar(top[0]["nome"] == "Barato 0" and top[1]["nome"] == "Caro 0", "dentro de cada cota, pela nota")

    print()
    print("2. ⛔ BARATO QUE NAO RENDE NAO OCUPA A COTA DOS BARATOS")
    dados = [c("Fone 67 mil vendas", 41, 2.86, 99)] + [c(f"Caro {i}", 120, 10, 80) for i in range(6)] + [c(f"Barato {i}", 60, 5, 60) for i in range(6)]
    top = pb.marcar_topo(dados)
    checar(top[0]["nome"] == "Barato 0", f"o fone (R$ 2,86) nao abre a pagina: {top[0]['nome']}")
    checar(top[1]["nome"] == "Fone 67 mil vendas", "mas concorre nos livres pela nota (99 > 80)")

    print()
    print("3. NOME REPETIDO NAO ENTRA DUAS VEZES")
    dados = [c("Balanca digital de cafe A", 52, 5, 80), c("Balanca digital de cafe B", 51, 4.6, 79)] + [c(f"Caro {i}", 120, 10, 70) for i in range(6)] + [c(f"Outro barato {i} x", 60, 5, 50) for i in range(6)]
    top = pb.marcar_topo(dados)
    checar(sum("Balanca" in p["nome"] for p in top) == 1, "so' uma balanca no topo")

    print()
    print("4. PISO NUNCA ENTRA; 5. LIVRES COMPLETAM")
    dados = [c("No piso", 60, 9, 99, fora="nota 80%")] + [c(f"Caro {i}", 120, 10, 80) for i in range(12)] + [c("Unico barato", 60, 5, 50)]
    top = pb.marcar_topo(dados)
    checar(all(p["nome"] != "No piso" for p in top), "quem esta' no piso fica fora")
    checar(len(top) == 10 and top[0]["nome"] == "Unico barato" and sum(p["nome"].startswith("Caro") for p in top) == 9,
           "1 barato + 9 livres = 10")
    checar(all(p.get("topo") == i for i, p in enumerate(top, 1)) and all("topo" not in p for p in dados if p not in top),
           "`topo` = posicao 1..10 so' nos escolhidos")
finally:
    pb.RAIZ = raiz
    pb._MEMO_HOJE.clear()

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
