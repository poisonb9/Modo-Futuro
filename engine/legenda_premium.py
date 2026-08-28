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

<UM icone que combine com o assunto> <2 a 3 frases de contexto: o pano de fundo
que da tamanho ao assunto. Escreva como texto corrido, nao como topico.>

<uma linha curta de transicao, terminada em dois pontos. Ex: "Para entender o
tamanho disso:" / "Tres pontos que explicam a briga:" / "O que sustenta esse
monopolio:">

→ <fato concreto, com numero ou data quando voce tiver certeza>

→ <outro>

→ <outro>

<1 ou 2 frases de fecho: o que isso decide, ou o que observar daqui pra frente.
Sem titulo, sem icone, so' a frase.>

REGRAS DE ACABAMENTO — o Bryan reprovou a versao anterior por parecer rascunho:
- NUNCA use titulo de secao em caixa alta ("O CONTEXTO", "POR QUE IMPORTA").
  Parece wireframe, nao produto acabado.
- NUNCA escreva que algo "nao coube no video" nem "ficou de fora". Isso sugere
  video incompleto. O texto e' aprofundamento, nao remendo.
- UM icone so', no comeco do primeiro paragrafo. Mais que isso vira post de dica
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
- Se a fala nao sustentar tres fatos honestos, escreva dois. Melhor menos e
  verdadeiro.

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
    return r[:1900]
