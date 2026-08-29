# -*- coding: utf-8 -*-
"""Legenda premium: o que NAO coube no corte, escrito na descricao.

POR QUE EXISTE
Pedido do Bryan em 28/08/2026, depois de ver funcionar no canal de comida: la'
a descricao leva a receita inteira, e a pessoa le' com a mao na massa. Aqui o
equivalente nao e' receita — e' **contexto**.

Um corte de 90s sobre cadeia de semicondutores deixa de fora quase tudo: o
numero, a data, o porque aquilo importa. Quem se interessou fica sem para onde
ir. A descricao e' esse lugar — e e' texto indexavel, que a busca do TikTok le'.

O QUE ISTO NAO E'
Nao e' resumo do video. Resumir o que a pessoa acabou de assistir nao acrescenta
nada. E' o que ficou DE FORA, e o que faz o assunto valer mais do que pareceu.

LIMITE: 2200 caracteres na legenda do TikTok. O prompt pede ate' 1600 pra sobrar
espaco pro titulo e as hashtags.
"""
from __future__ import annotations

import re

PROMPT_PREMIUM = """Abaixo esta a fala de um corte de video curto, ja em
portugues. O canal fala de tecnologia, chips, industria e geopolitica.

Escreva a DESCRICAO do post. Formato EXATO, sem titulo de secao nenhum:

<UM icone que combine com o assunto> <A PRIMEIRA FRASE E' A MAIS IMPORTANTE DE
TODAS: e' a unica que aparece antes do "ver mais" do TikTok, junto com o titulo.
Comece pelo FATO MAIS FORTE que voce tem — um numero, um nome, uma
concentracao improvavel. Nunca comece com frase de aquecimento do tipo "a
industria de semicondutores e' complexa" ou "nos ultimos anos". Ex: "Uma cidade
de dez mil habitantes na Carolina do Norte abastece 80% do quartzo que o mundo
usa pra fazer chips.">

<mais 1 ou 2 frases de contexto, agora sim explicando o pano de fundo.>

<uma linha curta de transicao, terminada em dois pontos. Ex: "Para entender o
tamanho disso:" / "Tres pontos que explicam a briga:" / "O que sustenta esse
monopolio:">

→ <fato concreto, com numero ou data quando voce tiver certeza>

→ <outro>

→ <outro>

→ <outro>

→ <outro — QUATRO ou CINCO setas no total. Ha' folga de caracteres e o leitor
   que chegou ate' aqui quer mais, nao menos.>

<1 frase de fecho: o que isso decide, ou o que observar daqui pra frente.>

<UM icone> <uma PERGUNTA curta pro leitor, ou um gancho de curiosidade sobre o
que vem a seguir. Ex: "E se essa fabrica parar por uma semana?" / "O proximo
gargalo talvez nem seja o chip — e sim a energia pra alimenta-lo.">

REGRAS DE ACABAMENTO — o Bryan reprovou a versao anterior por parecer rascunho:
- NUNCA use titulo de secao em caixa alta ("O CONTEXTO", "POR QUE IMPORTA").
  Parece wireframe, nao produto acabado.
- NUNCA escreva que algo "nao coube no video" nem "ficou de fora". Isso sugere
  video incompleto. O texto e' aprofundamento, nao remendo.
- DOIS icones no total: um abrindo o contexto, outro abrindo a pergunta final.
  Nao use mais que isso — vira post de dica rapida e enfraquece a autoridade
  num canal de industria.
- A PERGUNTA FINAL nao pode ser retorica vazia ('o que voce acha?'). Tem que
  nascer do assunto e deixar o leitor pensando, ou apontar pra proxima
  pergunta do tema. Comentario e' dos sinais mais fortes do TikTok e hoje o
  canal nao pede nenhum.
- (regra antiga, mantida) icone so' nesses dois lugares. Mais que isso vira post de dica
  rapida e enfraquece a autoridade num canal de industria.
- Linha em branco entre cada seta, pra respirar.
- As DUAS PRIMEIRAS LINHAS sao as unicas que aparecem antes do "ver mais" do
  TikTok. Elas tem que ser conteudo, nunca enfeite.

REGRAS DURAS:
- SEJA ESPECIFICO. Fato sem numero, sem data e sem nome proprio nao acrescenta
  nada: "a China investe bilhoes" e' vago, "o CHIPS Act reservou mais de 50
  bilhoes de dolares" e' informacao. Nome de empresa, ano, cidade e cifra sao
  o que fazem a descricao valer a leitura.
- **MAS NAO INVENTE.** Se nao tiver certeza, escreva algo
  qualitativo. Um numero errado num canal de industria destroi a autoridade
  inteira, e quem entende percebe na hora. Prefira "poucas empresas no mundo" a
  um numero chutado.
- Nao repita o que o video ja' disse. A pessoa acabou de assistir.
- Nada de hype vazio ("isso vai mudar tudo", "o futuro chegou"). Fato e
  consequencia.
- Maximo 1600 caracteres.
- Portugues do Brasil, direto. Termo tecnico so' com explicacao de tres palavras.
- Sem despedida, sem hashtag, sem "siga para mais".
- QUANTIDADE: quatro ou cinco setas. Se voce nao tiver cinco fatos de que tem
  certeza, escreva quatro. Se nao tiver quatro, escreva tres. NUNCA complete a
  conta com fato vago ou inventado — melhor menos e verdadeiro.
- Cada seta tem que trazer informacao NOVA. Cinco setas dizendo a mesma coisa
  de cinco jeitos e' pior que tres bem escolhidas.

Fala do corte:
{texto}"""


def da_fala(segmentos: list[dict]) -> str:
    return " ".join(s["texto"].strip() for s in segmentos if s.get("texto"))


def gerar(segmentos: list[dict]) -> str:
    """Devolve a descricao premium, ou "" se nao der.

    Nunca levanta: descricao e' enfeite, e derrubar um clipe pronto por causa
    dela seria perder o render inteiro.
    """
    from . import traducao
    texto = da_fala(segmentos)
    if len(texto) < 150:
        return ""
    try:
        r = traducao._traduzir_texto(texto, prompt=PROMPT_PREMIUM)
    except Exception:
        return ""
    r = re.sub(r"^```.*?$|^```$", "", r, flags=re.M).strip()
    # Corte no PARAGRAFO, nunca no meio. Cortar em 1900 cru decepou a pergunta
    # final de uma legenda em 28/08/2026, e a pergunta e' justamente o que puxa
    # comentario. Se estourar, some o paragrafo do MEIO, nao o fim.
    TETO = 2000
    if len(r) <= TETO:
        return r
    partes = r.split("\n\n")
    while len(partes) > 3 and len("\n\n".join(partes)) > TETO:
        del partes[len(partes) // 2]
    return "\n\n".join(partes)[:TETO]
