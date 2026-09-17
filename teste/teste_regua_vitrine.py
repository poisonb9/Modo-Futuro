# -*- coding: utf-8 -*-
"""A Nota de Vitrine (35/30/20/15) faz o que o doc diz — e so' isso. Sem rede.

## POR QUE EXISTE (17/09/2026)

`CRITERIOS_DA_VITRINE.md`: uma regua so' para a ordem, o fogo e o ML. Os casos
sao TEOREMATICOS: cada um segue da definicao, nao de intuicao sobre o dado.

1. os pesos somam 100 e um cartao perfeito da' 100;
2. ⛔ NEGATIVO: externa (Awin) tem Confianca 0 por construcao — sem review no
   feed, sem decreto; e nao entra no piso (fica na vitrine com nota menor);
3. piso e' "fora da vitrine" (nota 0, motivo nomeado), nunca "fora do dado";
4. Rende e' por LOJA (o Kabum a 2% nao e' medido pela regua do Ali), e a faixa
   de impulso rebaixa acima de R$ 150;
5. quem subiu (ja_esteve) nao tem Momento de queda;
6. ML: vendedores >= 5 = confianca cheia; 2-4 = metade; crescimento = momento.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import regua_vitrine as rv  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


ALI = "AliExpress"
ML = "Mercado Livre"

print("1. PESOS SOMAM 100; CARTAO PERFEITO = 100")
checar(sum(rv.PESOS.values()) == 100, f"pesos {rv.PESOS}")
perfeito = {"loja": ALI, "ganho": 10.0, "preco": "R$ 99,00", "nota": 98.0, "vendas": 5000,
            "queda": 20.0, "vendeu": [800, "14/09"], "imagem": "x", "views_acima_da_mediana": 1}
ref = rv.referencias([perfeito, {"loja": ALI, "ganho": 5.0}])
total, eixos, motivo = rv.nota(perfeito, ref)
checar(total == 100.0 and not motivo, f"perfeito = {total} ({eixos})")

print()
print("2. ⛔ NEGATIVO: externa tem Confianca 0 por construcao, e NAO cai no piso")
nike = {"loja": "Nike", "ganho": 8.0, "preco": "R$ 149,90", "queda": 0.0, "imagem": "x"}
ref = rv.referencias([nike])
total, eixos, motivo = rv.nota(nike, ref)
checar(eixos["confianca"] == 0.0, "confianca 0 (sem review no feed)")
checar(motivo == "" and total == 35 + 7.5, f"na vitrine com Rende cheio + Mostravel meio = {total}")

import json, tempfile
from datetime import date, timedelta
rep_real = rv.REPUTACAO
rv.REPUTACAO = Path(tempfile.mkdtemp()) / "rep.json"
rv.REPUTACAO.write_text(json.dumps({"Nike": {"nota": 8.4, "em": date.today().isoformat()},
                                    "Kabum": {"nota": 7.2, "em": date.today().isoformat()},
                                    "Clovis Calçados": {"nota": 8.9, "em": (date.today() - timedelta(days=61)).isoformat()}}), encoding="utf-8")
checar(rv.confianca({"loja": "Nike"}) == 1.0 and rv.confianca({"loja": "Kabum"}) == 0.7,
       "reputacao lida a mao (Reclame Aqui) vira Confianca: 8,4 = cheia, 7,2 = 0,7")
checar(rv.confianca({"loja": "Clovis Calçados"}) == 0.0, "numero com 61 dias NAO vale (validade 60)")
rv.REPUTACAO = rep_real

print()
print("3. PISO: fora da vitrine com motivo, nota 0")
ruim = dict(perfeito, nota=87.0)
total, eixos, motivo = rv.nota(ruim, rv.referencias([ruim]))
checar(total == 0.0 and motivo.startswith("nota 87%"), f"Ali 87% => 0, motivo {motivo!r}")
ml1 = {"loja": ML, "ganho": 2.0, "preco": "R$ 20,00", "vendedores": [1, 0, "16/09"], "imagem": "x"}
total, eixos, motivo = rv.nota(ml1, rv.referencias([ml1]))
checar(total == 0.0 and "vendedor" in motivo, f"ML com 1 vendedor => 0, motivo {motivo!r}")
sem_nota = {"loja": ALI, "ganho": 2.0, "preco": "R$ 20,00", "imagem": "x"}
total, eixos, motivo = rv.nota(sem_nota, rv.referencias([sem_nota]))
checar(motivo == "", "Ali SEM nota nao e' piso (falta de dado nao e' nota baixa)")

print()
print("4. RENDE POR LOJA + FAIXA DE IMPULSO")
dados = [{"loja": ALI, "ganho": 10.0, "preco": "R$ 50,00"},
         {"loja": ALI, "ganho": 1.0, "preco": "R$ 10,00"},
         {"loja": "Kabum", "ganho": 2.0, "preco": "R$ 100,00"},
         {"loja": "Kabum", "ganho": 0.5, "preco": "R$ 20,00"}]
ref = rv.referencias(dados)
checar(rv.rende(dados[0], ref) == 1.0 and rv.rende(dados[2], ref) == 1.0,
       "o melhor de CADA loja tem Rende 1 (Kabum a R$ 2 nao e' medido pelo Ali a R$ 10)")
checar(rv.rende(dados[1], ref) == 0.1 and rv.rende(dados[3], ref) == 0.25, "os outros, proporcionais")
caro = {"loja": ALI, "ganho": 10.0, "preco": "R$ 191,33"}
checar(rv.rende(caro, ref) == rv.IMPULSO_ACIMA, f"acima de R$ 150 rebaixa para {rv.IMPULSO_ACIMA}")

print()
print("5. QUEM SUBIU NAO TEM MOMENTO DE QUEDA")
subiu = {"queda": 20.0, "ja_esteve": {"preco": "R$ 30,00", "em": "14/09"}}
checar(rv.momento(subiu) == 0.0, "ja_esteve zera a parte de queda")
caiu = {"queda": 20.0}
checar(rv.momento(caiu) == 0.6, "queda >= 15 sem crescimento = 0,6")
caiu_vendendo = {"queda": 20.0, "vendeu": [792, "14/09"]}
checar(rv.momento(caiu_vendendo) == 1.0, "queda + volume subindo = 1 (o sinal mais forte)")

print()
print("6. ML: vendedores como confianca e crescimento como momento")
checar(rv.confianca({"loja": ML, "vendedores": [13, 0, "16/09"]}) == 1.0, ">= 5 vendedores = cheia")
checar(rv.confianca({"loja": ML, "vendedores": [3, 0, "16/09"]}) == 0.5, "2-4 = metade")
checar(abs(rv.momento({"queda": 0.0, "vendedores": [13, 2, "16/09"]}) - 0.28) < 1e-9, "+2 vendedores = momento 0,4 x 0,7")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
