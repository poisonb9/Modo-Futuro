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
print("3b. KILL DE 30 DIAS SEM CLIQUE — so' com cliques MEDIDOS")
base = {"loja": ALI, "nome": "x", "preco": "R$ 20,00", "dias": 31, "cliques_30": 0}
checar(rv.piso(dict(base, cliques_medidos=True)) == "30 dias na vitrine sem clique", "31 dias, 0 cliques, medido = fora")
checar(rv.piso(dict(base, cliques_medidos=False)) == "", "⛔ sem medicao = NADA muda")
checar(rv.piso(dict(base, cliques_medidos=True, dias=29)) == "", "29 dias ainda nao")
checar(rv.piso(dict(base, cliques_medidos=True, cliques_30=1)) == "", "1 clique salva")

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
# v2: faixa ESCALONADA (ENP + Jungle Scout): 150 / 500 / 1.500 / fora
checar(rv.rende({"loja": ALI, "ganho": 10.0, "preco": "R$ 191,33"}, ref) == 0.85, "150-500 = x0,85")
checar(abs(rv.rende({"loja": ALI, "ganho": 10.0, "preco": "R$ 999,00"}, ref) - 0.7) < 1e-9, "500-1.500 = x0,7")
checar(rv.rende({"loja": ALI, "ganho": 10.0, "preco": "R$ 1.501,00"}, ref) == 0.0, "> 1.500 = 0 (e piso)")
checar("acima de" in rv.piso({"loja": ALI, "nome": "x", "preco": "R$ 1.501,00"}), "> 1.500 e' piso nomeado")
# v2: recorrencia +15% (LTV) — consumivel, desgaste, colecionavel
checar(abs(rv.rende({"loja": ALI, "ganho": 5.0, "preco": "R$ 50,00", "nome": "Exypna Energy Drink"}, ref) - 0.575) < 1e-9,
       "energetico = recorrente: 0,5 x 1,15")
checar(rv.rende({"loja": ALI, "ganho": 10.0, "preco": "R$ 50,00", "nome": "Whey 900g"}, ref) == 1.0, "teto 1,0 mesmo recorrente")
checar(not rv.recorrente({"nome": "Cafeteira eletrica"}), "⛔ 'cafeteira' NAO e' 'cafe' (borda de palavra)")
# v2: exclusoes
for nome, motivo in (("Gift Card Netshoes 150", "Gift Card"), ("Recarga de celular Vivo R$ 30", "Recarga de celular"), ("Livro de receitas", "Livro")):
    checar(rv.piso({"loja": "Kabum", "nome": nome, "preco": "R$ 50,00"}).startswith("excluido: " + motivo), f"{nome!r} excluido")
for nome in ("Cinto tonificador com recarga USB", "Capa para laptop 13 a 16", "Capa dura Kindle"):
    checar(rv.piso({"loja": "Kabum", "nome": nome, "preco": "R$ 50,00"}) == "", f"⛔ {nome!r} E' produto, fica")

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
# v2 (17/09): sem reputacao no instantaneo, 0,8 vendedores + 0,2 frete
checar(abs(rv.confianca({"loja": ML, "vendedores": [13, 0, "16/09"]}) - 0.8) < 1e-9, ">= 5 vendedores, sem reputacao = 0,8")
checar(abs(rv.confianca({"loja": ML, "vendedores": [13, 0, "16/09"], "frete_gratis": True}) - 1.0) < 1e-9, "+ frete gratis = 1,0")
checar(abs(rv.confianca({"loja": ML, "vendedores": [3, 0, "16/09"]}) - 0.4) < 1e-9, "2-4 vendedores = 0,4")
# com reputacao medida: 0,5 termometro + 0,3 vendedores + 0,2 frete
checar(abs(rv.confianca({"loja": ML, "vendedores": [13, 0, "16/09"], "frete_gratis": True,
                         "reputacao": {"nivel": 5}}) - 1.0) < 1e-9, "5_green + 13 vendedores + frete = 1,0")
checar(abs(rv.confianca({"loja": ML, "vendedores": [13, 0, "16/09"], "reputacao": {"nivel": 3}}) - 0.3) < 1e-9,
       "termometro 3 zera a parte dele: sobra 0,3 dos vendedores")
checar(abs(rv.confianca({"loja": ML, "vendedores": [40, 0, "16/09"], "frete_gratis": True}) - 0.8) < 1e-9,
       "⛔ curva B: > 30 vendedores = commodity, x0,8")
checar(abs(rv.momento({"queda": 0.0, "vendedores": [13, 2, "16/09"]}) - 0.28) < 1e-9, "+2 vendedores = momento 0,4 x 0,7")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
