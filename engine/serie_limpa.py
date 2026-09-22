# -*- coding: utf-8 -*-
"""O ponto SOLTO da serie de precos nao e' preco: e' outro anuncio.

## ⛔ O DEFEITO, medido em 21/09/2026

13 dos 147 produtos com serie de 3+ pontos tinham a MESMA assinatura: um
valor gritante, isolado, no meio de uma serie estavel.

    Escova de dentes ... 7,17 7,17 6,99 7,25 7,28 7,25 [40,30] 6,66
    Kit limpeza ........ 4,05 4,02 4,04 3,96 3,98 [16,16] 3,49
    Carregador USB C ... 6,37 6,37 6,11 6,32 6,35 6,17 6,20 [18,16] 6,43

⚠️ E era justamente ele que virava o `antes` RISCADO. A "queda de 84%" da
Escova nao era queda: era um 40,30 cercado de 7,00. O cartao prometia "voce
economiza R$ 33,64" num produto que sempre custou ~R$ 7 — o "a pagina passa a
mentir sozinha" que o projeto inteiro combate, por um caminho que nenhuma
guarda olhava.

⚠️ A guarda que existia (`SALTO_VARIANTE`) so' ve' o preco de HOJE subindo
acima do minimo — o caso do produto que esgotou. Aqui e' o contrario: hoje
esta' baixo e o ruido esta' no passado, virando desconto.

## ⭐ POR QUE ESTE MODULO EXISTE, E NAO UMA FUNCAO EM CADA LUGAR

TRES caminhos consolidam a mesma serie e nao podem divergir:

    publicar_bio._precos_por_dia   a pagina (queda, riscado, grafico)
    garimpo.historico              o cartaz do Telegram (`maior_visto`)
    vitrine.preco_antes_de         o post do canal

O `teste_vitrine_com_cartaz` cruza os tres sobre o catalogo inteiro e PEGOU a
divergencia quando a limpeza existia so' na pagina: o site dizia "sem queda" e
o canal continuava anunciando "de R$ 21,73". Uma regra, um arquivo.

## A REGRA: pico ISOLADO NO TEMPO

⭐ O discriminador e' temporal, e nao estatistico. Ruido e' um valor alto cujos
vizinhos de ANTES e de DEPOIS estao os dois bem abaixo. Queda de verdade nao
faz isso — ela desce em degraus, e cada ponto tem um vizinho perto.

⛔ DUAS REGRAS FORAM TESTADAS E REPROVADAS ANTES DESTA:

    por MEDIANA ..... com DOIS pontos de ruido a mediana sobe e eles se
                      protegem. Reprovou no Limpa vidro (27,54 com 19,73
                      por perto): o limiar subia para 28,44 e o ruido
                      passava por baixo da propria guarda.
    por AGRUPAMENTO . o maior grupo vira o "corpo" e o resto cai. Mas numa
                      queda real (27,5 26,9 20,1 12,0 11,8) o maior grupo
                      e' o de BAIXO, e a regra apaga a queda inteira.

⚠️ E a base e' o PERCENTIL 30, nao a mediana, pelo mesmo motivo: e' o preco
HABITUAL que interessa como referencia, nao a media entre o habitual e o
estranho.

## O que foi medido depois

    series com amplitude > 1,8x .... 13 -> 1
    Escova de dentes ............... queda 84% -> 8%
    Kit limpeza .................... queda 78% -> 14%
    Carregador USB C ............... queda 65% -> 0% (perdeu o riscado)
    Luz LED ........................ queda 62% -> 18%

⚠️ O que SOBROU fica dito: o "Filtro plastico" tem 6,26 ... 6,36 e depois
20,82 e 20,70 — as duas altas sao VIZINHAS uma da outra, entao nao sao pico
isolado. Pode ser variante e pode ser aumento real. A regra e' conservadora de
proposito: na duvida, nao apaga.

## ⭐ A EXCECAO MANUAL (22/09/2026)

O "Filtro plastico" ficou no ar 2 dias com queda de 70% depois desta regra
existir — o Bryan viu no celular (print) e perguntou. Tentei confirmar no
AliExpress pelo navegador e o bot-check bloqueou (redireciona pra pagina
generica, nao renderiza o produto). Sem forma automatica de saber se
R$ 20,82 foi um preco real algum dia, a decisao virou HUMANA: o Bryan pediu
pra forcar este produto agora, sem esperar mais um dia sanduichando os dois
caros (o que a regra automatica precisaria pra resolver sozinha).

`EXCECAO_MANUAL` e' isso: {id: (maior aprovado, motivo)}. Roda ANTES da
regra automatica e para um id que esta' nela, decide sozinha — documentada,
por id, reversivel removendo a linha. Nao muda `RUIDO_FATOR` nem
`RUIDO_VIZINHO`: a regra geral continua a mesma, testada, para todo o
resto do catalogo.
"""
from __future__ import annotations

RUIDO_FATOR = 1.8
RUIDO_VIZINHO = 0.25
RUIDO_MIN_PONTOS = 4

EXCECAO_MANUAL = {
    1005007345460326: (6.38,
        "Filtro plastico do funil: 20,82 e 20,70 sao a outra oferta do "
        "mesmo anuncio, nao o preco real. Decisao do Bryan, 22/09/2026, "
        "depois de EU NAO CONSEGUIR confirmar no AliExpress (bot-check "
        "bloqueou a checagem automatica) e a regra automatica recusar "
        "apagar por os dois dias caros serem VIZINHOS."),
    # ⛔ SEGUNDO CASO DO MESMO DIA (22/09/2026) — o proprio "Limpa vidro" que
    # o docstring acima ja citava como prova contra a mediana. Bruto:
    # 13-15/09 ~11,8-12,0; 16/09 27,54 (sozinho); GAP 17-19/09; 20-21/09
    # 19,73/19,61; hoje (instantaneo, 12:43 UTC) 11,89 de novo. E' o MESMO
    # padrao do Filtro plastico -- duas ofertas reais sob o mesmo id -- so'
    # que a leitura barata de hoje ainda nao virou linha na serie DIARIA
    # (so' existe no instantaneo horario), entao o "depois" que fecharia o
    # sanduiche pra regra automatica ainda nao existe onde ela olha.
    1005006994544782: (11.99,
        "Limpa vidro carro: 19,73/19,61/27,54 sao a oferta cara do mesmo "
        "anuncio (varia demais pra ser SO' aumento real -- de 19,6 a 27,5 "
        "em 5 dias). Decisao do Bryan, 22/09/2026."),
}


def sem_ponto_solto(dias: dict, pid=None) -> dict:
    """{dia: preco} sem os pontos que nao sao deste produto.

    ⭐ `pid` e' opcional (os tres chamadores de producao sempre passam; so'
    fica None nos testes que nao precisam da excecao). Ver EXCECAO_MANUAL.
    """
    if pid is not None:
        try:
            exc = EXCECAO_MANUAL.get(int(pid))
        except (TypeError, ValueError):
            exc = None
        if exc:
            maior, _motivo = exc
            limpo = {q: v for q, v in dias.items() if v <= maior * 1.001}
            if len(limpo) >= 2:
                return limpo
            # ⚠️ mesma trava da regra automatica: nunca devolve menos de
            # dois pontos, senao o produto some da pagina inteira.
    if len(dias) < RUIDO_MIN_PONTOS:
        return dias
    ordem = sorted(dias)                      # por DIA, nao por valor
    vals = [dias[q] for q in ordem]
    calmo = sorted(vals)
    base = calmo[max(0, int(len(calmo) * 0.30) - 1)]
    if base <= 0:
        return dias
    fora = set()
    for k, v in enumerate(vals):
        if v <= RUIDO_FATOR * base:
            continue                          # nem alto o bastante
        antes = vals[k - 1] if k > 0 else None
        depois = vals[k + 1] if k < len(vals) - 1 else None
        vizinhos = [x for x in (antes, depois) if x is not None]
        if vizinhos and all(x < v * (1 - RUIDO_VIZINHO) for x in vizinhos):
            fora.add(ordem[k])
    if not fora:
        return dias
    limpo = {q: v for q, v in dias.items() if q not in fora}
    # ⚠️ NUNCA devolve menos de dois pontos: sem serie o produto perde a trava
    # de 24 h e some da pagina inteira. Na duvida, fica o original.
    return limpo if len(limpo) >= 2 else dias
