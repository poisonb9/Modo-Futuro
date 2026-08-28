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

Escreva a DESCRICAO do post. Formato EXATO:

O CONTEXTO
<2 a 3 frases: o pano de fundo que o corte nao teve tempo de explicar. Onde
isso se encaixa numa historia maior.>

3 COISAS QUE NAO COUBERAM NO VIDEO
- <fato concreto, de preferencia com numero ou data>
- <outro>
- <outro>

POR QUE ISSO IMPORTA
<1 a 2 frases: o que muda na vida de quem esta assistindo, ou o que observar
daqui pra frente.>

REGRAS DURAS:
- **NAO INVENTE FATO, NUMERO NEM DATA.** Se voce nao tem certeza de um dado,
  escreva algo qualitativo em vez de numerico. Um numero errado num canal que
  fala de industria e tecnologia destroi a autoridade inteira, e o leitor que
  entende do assunto percebe na hora. Prefira "poucas empresas no mundo" a um
  numero chutado.
- Nao repita o que o video ja' disse. A pessoa acabou de assistir. Isto e' o que
  ficou DE FORA.
- Nada de hype vazio ("isso vai mudar tudo", "o futuro chegou"). Fato e
  consequencia.
- Maximo 1600 caracteres.
- Portugues do Brasil, direto, sem jargao desnecessario. Se usar termo tecnico,
  explique em tres palavras.
- Sem introducao, sem despedida, sem hashtag.
- Se a fala for curta ou vaga demais pra sustentar tres fatos honestos, escreva
  menos itens. Melhor duas linhas verdadeiras que tres com uma inventada.

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
