# -*- coding: utf-8 -*-
"""`engine/serie_limpa.py` nunca apaga MICROVARIACAO real -- so' anuncio
duplicado. Sem rede.

## ⛔ POR QUE ESTE TESTE EXISTE

`engine/serie_limpa.py` tinha uma historia inteira de abordagens tentadas e
reprovadas escrita SO' no docstring -- media, agrupamento -- cada uma com o
exemplo adversarial que a derrubou. Historia em comentario nao impede
ninguem de tropecar de novo: em 22/09/2026 eu mesmo cheguei a considerar
generalizar "ponto isolado" pra "sequencia isolada" (pra pegar plato de
2+ dias caros) e só não apliquei porque testei a mao contra o exemplo do
docstring e vi que quase apagava uma queda real. Esse teste e' a mao que
eu tive que fazer, permanente: qualquer regra nova tem de passar por aqui
ANTES de ir pro arquivo.

⭐ Pedido do Bryan (22/09/2026): "eu quero o grafico acompanhando isso,
descendo degrau por degrau, e eventualmente se tivesse subido era pra
acompanhar, quero microvariacoes". Os casos 1 e 2 sao a prova disso nos
dois sentidos -- queda real e subida real, espelhadas.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import serie_limpa as sl  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


print("1. QUEDA REAL, DEGRAU POR DEGRAU — nenhum ponto some")
# ⚠️ O exemplo do proprio docstring: "numa queda real (27,5 26,9 20,1 12,0
# 11,8) o maior grupo e' o de BAIXO e a regra AGRUPAMENTO apaga a queda
# inteira". Cada ponto tem de sobreviver, na ordem, sem arredondar sequencia
# nenhuma pra fora.
dias = {"2026-09-13": 27.5, "2026-09-14": 26.9, "2026-09-15": 20.1,
        "2026-09-16": 12.0, "2026-09-17": 11.8}
limpo = sl.sem_ponto_solto(dias)
checar(limpo == dias, "os 5 degraus da queda sobrevivem intactos, na ordem")

print()
print("2. SUBIDA REAL, DEGRAU POR DEGRAU — o espelho do caso 1")
# ⭐ Pedido explicito do Bryan: "eventualmente se tivesse subido era pra
# acompanhar". A mesma serie, de tras pra frente, tem de sobreviver do
# mesmo jeito -- a regra nao pode enxergar direcao, so' ISOLAMENTO.
dias_subida = {"2026-09-13": 11.8, "2026-09-14": 12.0, "2026-09-15": 20.1,
               "2026-09-16": 26.9, "2026-09-17": 27.5}
limpo = sl.sem_ponto_solto(dias_subida)
checar(limpo == dias_subida, "os 5 degraus da subida sobrevivem intactos, na ordem")

print()
print("3. MICROVARIACAO — ruido de cambio/arredondamento nunca e' 'anuncio'")
# ⚠️ Preco balancando ±1-2% dia a dia (cambio, centavo de arredondamento) e'
# a imensa maioria do catalogo. Se ISSO comecasse a sumir da serie, o
# grafico inteiro viraria uma linha reta -- o oposto do que foi pedido.
dias_micro = {"2026-09-13": 24.90, "2026-09-14": 24.75, "2026-09-15": 25.10,
              "2026-09-16": 24.80, "2026-09-17": 24.95, "2026-09-18": 25.05}
limpo = sl.sem_ponto_solto(dias_micro)
checar(limpo == dias_micro, "seis leituras dentro de 1,4% nao perdem ponto nenhum")

print()
print("4. ⛔ NEGATIVO — pico ISOLADO de verdade ainda e' pego (nao regrediu)")
# ⚠️ SENSIBILIDADE: os casos 1-3 provam que a regra NAO apaga demais. Este
# prova que ela continua apagando o que DEVE — sem ele, os casos de cima
# passariam so' porque a regra parou de fazer qualquer coisa.
dias_ruido = {"2026-09-12": 7.17, "2026-09-13": 7.25, "2026-09-14": 40.30,
              "2026-09-15": 7.28, "2026-09-16": 6.66}
limpo = sl.sem_ponto_solto(dias_ruido)
checar("2026-09-14" not in limpo, "o 40,30 isolado (Escova de dentes, caso real) ainda some")
checar(len(limpo) == 4, "e os quatro pontos vizinhos ficam")

print()
print("5. ⛔ NEGATIVO — sequencia de 2+ dias caros NAO e' apagada sozinha")
# ⚠️ Este e' o caso que eu CHEGUEI A CONSIDERAR automatizar em 22/09 e nao
# apliquei: dois (ou mais) dias caros seguidos, mesmo cercados de baixo dos
# dois lados. Fica registrado como comportamento ATUAL, de proposito
# conservador -- se um dia isto mudar, tem de ser decisao explicita, nao
# efeito colateral de outra mexida.
dias_plato = {"2026-09-13": 8.69, "2026-09-14": 7.91, "2026-09-15": 18.19,
              "2026-09-16": 18.27, "2026-09-17": 8.04, "2026-09-19": 8.44,
              "2026-09-20": 8.6, "2026-09-21": 9.4}
limpo = sl.sem_ponto_solto(dias_plato)
checar(limpo == dias_plato,
       "o plato de 2 dias (15 e 16/09) continua no dado -- conservador, nao regra")

print()
print("6. AS DUAS EXCECOES MANUAIS (22/09/2026, decisao do Bryan)")
# ⭐ Confere que EXCECAO_MANUAL funciona e que ela e' POR ID -- um id
# qualquer com o MESMO desenho nao e' afetado (ja' coberto no
# teste_grafico_serie.py, seccao 4c; aqui e' so' a leitura direta do dict).
checar(1005007345460326 in sl.EXCECAO_MANUAL, "Filtro plastico do funil esta' na excecao")
checar(1005006994544782 in sl.EXCECAO_MANUAL, "Limpa vidro esta' na excecao")
maior_fp, _ = sl.EXCECAO_MANUAL[1005007345460326]
checar(abs(maior_fp - 6.38) < 0.01, "o maior aprovado do Filtro plastico e' 6,38")
maior_lv, _ = sl.EXCECAO_MANUAL[1005006994544782]
checar(abs(maior_lv - 11.99) < 0.01, "o maior aprovado do Limpa vidro e' 11,99")

print()
print("7. ⭐ OFERTA DUPLA CONFIRMADA — resolve SOZINHO, sem excecao manual")
# ⚠️ O terceiro caso do mesmo dia (22/09/2026, "Bolsa grande para cabos e
# fones") nao ganhou excecao manual -- a regra geral por evidencia
# resolveu sozinha. A prova e' TEMPORAL num sentido diferente do vizinho
# no tempo: e' o MESMO instante tendo duas leituras.
dias_bolsa = {"2026-09-12": 31.99, "2026-09-14": 31.21, "2026-09-15": 31.69,
              "2026-09-16": 31.79, "2026-09-17": 49.71}
maiores_bolsa = {"2026-09-12": 31.99, "2026-09-14": 48.97, "2026-09-15": 49.66,
                  "2026-09-16": 49.88, "2026-09-17": 49.71}
limpo = sl.sem_ponto_solto(dias_bolsa, None, maiores_bolsa)
checar("2026-09-17" not in limpo,
       "o 49,71 sai mesmo sem excecao manual -- 3 dias provam a oferta dupla")
checar(len(limpo) == 4, "os quatro dias baratos ficam")

print()
print("8. ⛔ NEGATIVO — UM SO' dia com leitura dupla nao confirma nada")
# ⚠️ SENSIBILIDADE: exigir >= 2 dias (DIAS_MIN_CONFIRMA) e' o que separa
# "oferta dupla confirmada" do caso que o dedup-por-dia original (15/09)
# ja' resolve sozinho -- um UNICO dia com leitura dupla nao e' prova de
# nada alem do que ja' era tratado antes desta regra existir.
dias_um_dia = {"2026-09-12": 13.36, "2026-09-13": 13.36, "2026-09-14": 12.56}
maiores_um_dia = {"2026-09-12": 13.36, "2026-09-13": 13.36, "2026-09-14": 25.08}
confirmado = sl.maior_confiavel_oferta_dupla(dias_um_dia, maiores_um_dia)
checar(confirmado is None, "um dia so' com leitura dupla nao confirma oferta dupla")

print()
print("9. ⛔ NEGATIVO — queda/subida real, mesmo com `maiores_do_dia`, sobrevive")
# ⚠️ A prova positiva e' PASSIVA: se o id nunca teve leitura dupla no mesmo
# dia, `maiores_do_dia` e' identico a `dias` (uma leitura por dia, minimo
# igual ao maximo) -- e a funcao tem de continuar deixando o degrau a
# degrau intacto, exatamente como nos casos 1 e 2, mesmo com o parametro
# novo preenchido.
dias_queda = {"2026-09-13": 27.5, "2026-09-14": 26.9, "2026-09-15": 20.1,
              "2026-09-16": 12.0, "2026-09-17": 11.8}
limpo = sl.sem_ponto_solto(dias_queda, None, dict(dias_queda))
checar(limpo == dias_queda,
       "queda real com maiores_do_dia preenchido (=dias) continua intacta")

print()
if falhas:
    print(f"[x] {len(falhas)} falha(s)")
    for f in falhas:
        print("   -", f)
    raise SystemExit(1)
print("tudo verde")
