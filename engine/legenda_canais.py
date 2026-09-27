# -*- coding: utf-8 -*-
"""A legenda do post COM A CARA DE CADA CANAL.

⭐ 27/09/2026 (dono: "as legendas da achadinho make estao muito pesadas, la'
e' um canal fofo, esta' com legenda no estilo Modo Futuro — devemos avaliar
todos os canais; acho que so' o cozinha esta' alinhado"). O formato de
`legenda_premium.PROMPT_PREMIUM` (fato com numero, setas, tom de relatorio de
industria) nasceu pro Modo Futuro e era usado em TODO canal. A cozinha
escapava porque la' a legenda e' a receita (`receita_texto`).

Cada canal aqui segue o `## Tom` do seu guia de voz
(.claude/skills/guia-de-voz/canais/<canal>.md). Canal sem entrada volta ao
formato do Modo Futuro (com o contexto certo), como antes.
"""
from __future__ import annotations

_COMUM = """
REGRAS PARA TODOS:
- Portugues do Brasil, natural, como gente fala. Nada de titulo de secao em
  caixa alta, nada de "nao coube no video", sem hashtag, sem "siga para mais".
- NAO INVENTE: so' o que a fala sustenta. Na duvida, deixe de fora.
- NUNCA cite marca/produto patrocinado que aparece na fala (ex.: "AG1",
  cupom, "link na descricao"): e' o anuncio do podcast original.
- As DUAS primeiras linhas aparecem antes do "ver mais": sao conteudo.

Fala do corte:
{texto}"""

PROMPTS: dict[str, str] = {
    # ---- make: fofo, amiga contando pra amiga -------------------------
    "truque.importado": """Abaixo esta a fala de um corte curto de um canal FOFO
de maquiagem coreana e idols de K-pop. O tom e' de AMIGA contando pra outra
amiga o que viu: leve, curiosa, animada, sem virar propaganda e sem aula.

Escreva a LEGENDA do post neste formato:

<1 emoji fofo> <UMA frase curta com o momento mais fofo, engracado ou o
resultado da make. Ex: "O delineado de gatinho que deixou a Wonhee com cara
de boneca 🐱">

<1 frase curta dizendo quem e' (a idol, o grupo, a maquiadora), se a fala
disser.>

<SO' se a fala mostrar produtos ou passos:> O que ela usou ✨
• <produto pelo que ele E', sem marca: "um corretivo clarinho">
• <outro>
• <outro — no maximo 4>

<1 pergunta leve e divertida pra puxar comentario, com 1 emoji. Ex: "Voce
teria coragem de usar esse glitter no dia a dia? 👀">

PROIBIDO NESTE CANAL: numero de industria, economia, pais, PIB, tecnologia,
"sistema de treinamento", tom de reportagem. Nada de seta "→". No maximo 450
caracteres e 4 emojis no total.""",

    # ---- Sem Anestesia: disciplina + cerebro, sobrio ---------------------
    "semanestesia.pod": """Abaixo esta a fala de um corte curto de um canal sobre
disciplina e o cerebro por tras dela (Goggins, Huberman, dopamina, habito,
sono). O tom e' SOBRIO e direto: a fala do convidado e' o valor, sem exagerar
nem suavizar.

Escreva a LEGENDA do post neste formato:

<1 emoji discreto> <UMA frase forte com a ideia central da fala, atribuida a
quem falou. Ex: "Goggins nao esperou motivacao: ele reescrevia a mesma pagina
ate' decorar.">

<2 frases curtas explicando o porque, no que a fala sustenta.>

Pra levar pro seu dia:
• <1 acao pratica e concreta que sai da fala>
• <outra — 2 ou 3 no total>

<1 pergunta direta, pessoal, sem ser retorica vazia. Ex: "O que voce faz nos
dias em que a vontade nao aparece?">

PROIBIDO: conselho medico como verdade absoluta ("isso cura"), dado que o
convidado nao citou, hype ("vai mudar sua vida"), tecnologia/industria. No
maximo 600 caracteres e 2 emojis.""",

    # ---- Ate' Falhar: treino, pratico ------------------------------------
    "atefalhar": """Abaixo esta a fala de um corte curto de um canal de treino e
disciplina fisica. O tom e' firme e direto, frases curtas, sempre a licao
pratica.

Escreva a LEGENDA do post neste formato:

<1 emoji> <UMA frase com o ponto principal do treino ou da licao.>

Como fazer:
• <passo ou dica concreta da fala>
• <outro — 2 a 4 no total>

<SO' se a fala disser:> Erro comum: <o erro, em uma frase>

<1 pergunta curta pra puxar comentario.>

PROIBIDO: promessa de resultado em X dias que a fala nao faz, tecnologia/
industria. No maximo 500 caracteres e 2 emojis.""",
}


def prompt_do_canal(canal: str | None) -> str | None:
    """O prompt proprio do canal, ou None (usa o formato do Modo Futuro)."""
    base = PROMPTS.get(canal or "")
    return (base + "\n" + _COMUM) if base else None
