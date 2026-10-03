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
- NAO INVENTE: so' o que a fala sustenta. Na duvida, deixe de fora. ONDE e
  COM QUEM (programa, live, entrevista, bate-papo com fas) so' se a fala
  disser — em 03/10 saiu "em um bate-papo com fas" sem a fala dizer.
- Pergunta-teste sem "A)" "B)": escreva as opcoes na frase ("time X ou time Y?").
- NUNCA cite marca/produto patrocinado que aparece na fala (ex.: "AG1",
  cupom, "link na descricao"): e' o anuncio do podcast original.
- As DUAS primeiras linhas aparecem antes do "ver mais": sao conteudo.

ESCOLA DE REVISTA (03/10/2026, dono: "reformular todas as legendas com base nas
revistas"; 155 capas teen lidas, _privado/capricho/ENGENHARIA_REVERSA.md):
- A 1a LINHA e' CHAMADA DE CAPA: o NOME em destaque (94% das capas) + um
  NUMERO real da fala (74%) ou um gatilho (segredo, revela, descubra,
  especial, infalivel, adeus...). Exclamacao combina (80%). Nao copie o
  titulo da tela palavra por palavra: complete-o.
- Se a fala tiver uma frase marcante, use-a ENTRE ASPAS com as palavras
  exatas, atribuida a quem disse (22% das capas). Nunca invente citacao.
- Fale com VOCE e com a vida real (escola, festa, rotina, trabalho), quando
  a fala permitir: capa teen vende o beneficio pra leitora.
- Nome, programa, data e evento concretos ajudam o TikTok a entender o post.
- SOE GENTE (skill humanizar): varie o jeito de abrir entre posts; nada de
  lista de tres em toda frase, nada de "nao e' X, e' Y", travessao so' se
  precisar, sem "alem disso"/"vale ressaltar"/"em resumo".
- A PERGUNTA FINAL e' um TESTE de revista (03/10/2026, dono: em todos os
  canais): a pessoa responde sobre ELA MESMA, com escolha clara (A ou B,
  "qual e' voce", "voce faria?"). Nunca "o que voce acha?".

Fala do corte:
{texto}"""

PROMPTS: dict[str, str] = {
    # ---- camarim: bastidor, reacao, humor (02/10/2026) -----------------
    "camarim.kpop": """Abaixo esta a fala de um corte curto de um canal de
BASTIDORES de idols de K-pop: reacoes, humor, fofura e personalidade. O tom e'
de fa contando pra outra fa o que viu: leve, animado, sem propaganda.

Escreva a LEGENDA do post neste formato:

<1 emoji> <CHAMADA DE CAPA com o NOME da idol e o GRUPO e o momento mais fofo
ou engracado. Ex: "O ataque de riso da Wonhee do ILLIT que ninguem segurou 😂",
"HAN do Stray Kids REVELA: 2 semanas sendo ignorado no grupo!">

<1 frase curta de contexto (programa, com quem estava), se a fala disser.>

<1 pergunta no formato TESTE de revista teen (02/10/2026: 38% das capas da
Capricho traziam teste), que a pessoa responde nos comentarios sobre ELA
mesma, com 1 emoji. Ex: "Qual integrante do Stray Kids e' voce? Comenta 👇",
"Voce seria a BFF de quem? 👀", "Doce ou salgado: qual time e' o seu? 🍪">

Fala do corte:
{texto}""",
    # ---- make: fofo, amiga contando pra amiga -------------------------
    "truque.importado": """Abaixo esta a fala de um corte curto de um canal FOFO
de maquiagem coreana e idols de K-pop. O tom e' de AMIGA contando pra outra
amiga o que viu: leve, curiosa, animada, sem virar propaganda e sem aula.

Escreva a LEGENDA do post neste formato:

<1 emoji fofo> <CHAMADA DE CAPA com o NOME da idol e o resultado ou o segredo
da make. Ex: "O delineado de gatinho que deixou a Wonhee com cara de boneca 🐱",
"3 passos da make dumpling do Hyunjin pra voce copiar!">

<1 frase curta dizendo quem e' (a idol, o grupo, a maquiadora), se a fala
disser.>

<SO' se a fala mostrar produtos ou passos:> O que ela usou ✨
• <produto pelo que ele E', sem marca: "um corretivo clarinho">
• <outro>
• <outro — no maximo 4>

<1 pergunta-TESTE leve, sobre a propria pessoa, com 1 emoji. Ex: "Voce
usaria esse glitter na escola ou so' na festa? 👀", "Time delineado ou time
cilios? Comenta 👇">

PROIBIDO NESTE CANAL: numero de industria, economia, pais, PIB, tecnologia,
"sistema de treinamento", tom de reportagem. Nada de seta "→". No maximo 450
caracteres e 4 emojis no total.""",

    # ---- Sem Anestesia: disciplina + cerebro, sobrio ---------------------
    "semanestesia.pod": """Abaixo esta a fala de um corte curto de um canal sobre
disciplina e o cerebro por tras dela (Goggins, Huberman, dopamina, habito,
sono). O tom e' SOBRIO e direto: a fala do convidado e' o valor, sem exagerar
nem suavizar.

Escreva a LEGENDA do post neste formato:

<1 emoji discreto> <CHAMADA DE CAPA sobria: o NOME de quem falou + a ideia
central, com numero se a fala tiver. Ex: "Goggins nao esperou motivacao: ele
reescrevia a mesma pagina ate' decorar.", "O protocolo de 2 minutos do Huberman
pra dopamina nao despencar">

<2 frases curtas explicando o porque, no que a fala sustenta.>

Pra levar pro seu dia:
• <1 acao pratica e concreta que sai da fala>
• <outra — 2 ou 3 no total>

<1 pergunta-TESTE direta e pessoal, com escolha clara. Ex: "Voce treina
cedo ou a noite?", "Voce aguentaria 1 semana da rotina do Goggins? Sim ou
nao">

PROIBIDO: conselho medico como verdade absoluta ("isso cura"), dado que o
convidado nao citou, hype ("vai mudar sua vida"), tecnologia/industria. No
maximo 600 caracteres e 2 emojis.""",

    # ---- Geracao 2000 (ex-Ate' Falhar, 28/09): nostalgia de desenho -------
    "atefalhar": """Abaixo esta a fala de um corte curto de um canal sobre os
desenhos animados dos anos 2000 (Coragem, Padrinhos Magicos, Tres Espias, Du
Dudu e Edu...). O tom e' de conversa entre amigos que cresceram vendo isso:
nostalgico, curioso, com a revelacao no centro. Use os nomes da dublagem
brasileira.

Escreva a LEGENDA do post neste formato:

<1 emoji> <CHAMADA DE CAPA com o NOME do desenho ou personagem e a revelacao.
Ex: "O SEGREDO do Coragem que voce nao viu quando crianca!", "Adeus, Cosmo e
Wanda: o que mudou nos Padrinhos Magicos">

<2 frases curtas: o detalhe que prova e por que ninguem percebeu quando
crianca.>

<1 pergunta-TESTE nostalgica sobre a propria pessoa. Ex: "Voce assistia
antes da escola ou depois do almoco?", "Qual Padrinho Magico seria o seu:
Cosmo ou Wanda?">

PROIBIDO: inventar fato que a fala nao diz, spoiler sem aviso, treino/
tecnologia/industria. No maximo 500 caracteres e 2 emojis.""",
}


def prompt_do_canal(canal: str | None) -> str | None:
    """O prompt proprio do canal, ou None (usa o formato do Modo Futuro)."""
    base = PROMPTS.get(canal or "")
    if not base:
        return None
    from . import calendario   # 03/10/2026: data do momento (volta as aulas...)
    return base + calendario.dica(canal or "") + "\n" + _COMUM
