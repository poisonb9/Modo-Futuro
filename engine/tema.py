# -*- coding: utf-8 -*-
"""Segunda opiniao sobre o canal: o TEMA do titulo contra a PASTA do Drive.

⚠️ POR QUE ISTO EXISTE, medido em 07/09/2026.

O Bryan viu oito clipes de INTELIGENCIA ARTIFICIAL no @semanestesia.pod —
Sam Altman, "99% de desemprego em 2027", "e' impossivel desligar uma IA".
Conteudo de @modofuturo, publicado no canal de comportamento. Rastreado ate'
a origem:

  1. o bruto `The AI Safety Expert... Dr. Roman Yampolskiy.mp4` foi parar na
     pasta `SEM ANESTESIA/` do Drive;
  2. `vigia_raw.canal_da_pasta` leu a pasta e devolveu `semanestesia.pod` —
     com confianca total, porque a pasta existe e esta' no mapa;
  3. o corte nasceu rotulado `semanestesia.pod`, e os 8 clipes entraram no
     manifesto com esse canal;
  4. `agendar_buffer.e_deste_canal()` conferiu o rotulo, bateu, e agendou.

**Nenhuma guarda falhou.** Todas obedeceram um rotulo que ja' era falso na
entrada. Ate' hoje o unico ponto de verdade sobre o canal era um arrastar de
arquivo no Drive, e ninguem no caminho tinha permissao de discordar dele.

⚠️ A REGRA: este modulo **so' barra e avisa**. Ele NUNCA redireciona sozinho.
Ordem do Bryan em 07/09/2026: "so' barrar+avisar, nunca redirecionar". Trocar
o canal na marra seria repetir o defeito na direcao oposta — um chute com
outro nome. Custo de barrar: um bruto parado ate' o dono olhar. Custo de
chutar: 8 posts no canal errado, e publicacao nao tem desfazer bonito.

## A REGRA DE DECISAO

    barra  <=>  outro canal pontua >= LIMIAR  E  pontua MAIS que a pasta

As duas condicoes juntas, e nao qualquer uma delas:

  - so' "outro canal pontua" barraria o Huberman ("Change Your Brain") toda
    vez que um termo de outro canal encostasse no titulo;
  - so' "pontua mais que a pasta" barraria titulo em coreano, que nao pontua
    em lugar nenhum — e ai' 12 dos 15 brutos do @truque.importado parariam.

Titulo que NAO pontua em canal nenhum PASSA. Ausencia de evidencia nao e'
evidencia de erro: o detector nao le' coreano, nao le' mojibake do log e nao
le' nome de arquivo do YTDown. Falha ABERTA de proposito — este modulo e'
uma segunda opiniao, nao um portao.

## O CASO NEGATIVO E' MEDIDO, NAO IMAGINADO

`teste/teste_tema_do_canal.py` roda os **32 brutos reais** que o vigia ja'
despachou com pasta de canal (extraidos de `estado/vigia_raw.log`), cada um
com a pasta em que ele realmente estava. Medido:

    1 barrado   — o Yampolskiy, o defeito que originou este modulo
    31 passam   — tudo o mais que ja' foi cortado e publicado sem reclamacao

E, como pressao extra de falso positivo, os **255 titulos** do manifesto:
5 acusados, e os cinco sao defeito DOCUMENTADO (4 dos 8 clipes de IA do
Yampolskiy, mais o clipe do biscoito Levain rotulado `modofuturo` — o
incidente do Fahrenheit de 03/09). Zero falso positivo.

⚠️ Detector que acusa 100% passa em qualquer caso positivo. O que prova
sensibilidade e' o 31, nao o 1.
"""
from __future__ import annotations

import re
import unicodedata

# Pontuacao minima do canal rival para valer uma recusa.
#
# Calibragem MEDIDA nos 32 brutos historicos: com 2 o "Stress Leaks Through
# Skin" do @semanestesia e' barrado por causa de `skin`, que e' termo de
# maquiagem — falso positivo. Com 3 o resultado e' 1 barrado e 31 passando,
# que e' exatamente o gabarito.
LIMIAR = 3

# ⚠️ OS TERMOS SAO OS MEDIDOS, NAO OS IMAGINADOS. Vem de `canais/*/README.md`
# (a tabela "o que viraliza") e de `config.TERMOS_HYPE` / `PODCAST_TERMOS_HYPE`.
# Peso 3 = termo que sozinho identifica o canal; 1 = pista fraca, que so' vale
# somada. Termo generico que aparece nos dois lados (`expert`, `truth`, `life`)
# fica FORA de proposito: ele nao separa nada e so' gera empate.
TERMOS: dict[str, dict[str, int]] = {
    "modofuturo": {
        # o nucleo fisico do canal — README: "chips, fabrica, maquina"
        "chip": 3, "chips": 3, "semiconductor": 3, "semicondutor": 3,
        "silicon": 3, "silicio": 3, "wafer": 3, "asml": 3, "euv": 3,
        "litografia": 3, "lithography": 3, "nanometer": 3, "nanometro": 3,
        "tsmc": 3, "nvidia": 3, "fab": 3, "fabs": 3, "cleanroom": 3,
        "quantum": 3, "quantico": 3, "gpu": 3, "datacenter": 3,
        "fabrica": 2, "factory": 2, "megafactory": 3, "terafab": 3,
        # o lado de IA que gerou o defeito de 07/09
        "openai": 3, "altman": 3, "agi": 3, "superintelligence": 3,
        "superinteligencia": 3, "ia": 3, "ai": 3,
        "inteligencia artificial": 3, "artificial intelligence": 3,
        "robot": 2, "robots": 2, "robo": 2, "robotica": 2, "robotics": 2,
        "intel": 2, "ibm": 2, "elon musk": 2, "tesla": 2,
    },
    "semanestesia.pod": {
        # README: "comportamento, mente e vida"; §5 do handoff de 07/09 mediu
        # responsabilidade pessoal e disciplina como o tema que mais engaja
        "brain": 3, "cerebro": 3, "neuroscientist": 3, "neurocientista": 3,
        "neuroscience": 3, "psychologist": 3, "psicologo": 3,
        "psychology": 3, "psicologia": 3, "therapist": 3, "terapeuta": 3,
        "mindset": 3, "mentalidade": 3, "dementia": 3, "demencia": 3,
        "anxiety": 3, "ansiedade": 3, "trauma": 3, "depression": 3,
        "depressao": 3, "loneliness": 3, "solidao": 3, "burnout": 3,
        "self esteem": 3, "autoestima": 3, "procrastination": 3,
        "procrastinacao": 3, "relationship": 2, "relacionamento": 2,
        "stress": 2, "estresse": 2, "habits": 2, "habitos": 2,
        "mind": 2, "mente": 2, "podcast": 1, "sleep": 2, "sono": 2,
    },
    "atefalhar": {
        # README: "disciplina, corpo e dor". Puxado pra MENTALIDADE em 06/09,
        # mas a mentalidade DELE e' a do esforco fisico — por isso os termos
        # de corpo continuam pesando.
        #
        # ⚠️ `goggins` e `navy seal` NAO entram aqui, por mais que pareca o
        # lugar deles. Em 04/09/2026 o Bryan reetiquetou os 8 clipes do
        # Goggins de `modofuturo` para `semanestesia.pod` — Goggins e' fonte
        # do canal de comportamento por decisao DELE. Com os dois termos aqui,
        # o detector acusava 4 clipes legitimos do @semanestesia.pod nos 255
        # do manifesto. Esses quatro foram os UNICOS falsos positivos que a
        # medicao encontrou, e a causa era esta.
        "workout": 3, "treino": 3, "glute": 3, "gluteo": 3, "gym": 3,
        "academia": 3, "muscle": 3, "musculo": 3, "hypertrophy": 3,
        "hipertrofia": 3, "marathon": 3, "maratona": 3, "ultramarathon": 3,
        "bodybuilding": 3, "crossfit": 3,
        "reps": 3, "deadlift": 3, "squat": 3, "cardio": 2, "running": 2,
        "corrida": 2, "discipline": 2, "disciplina": 2, "endurance": 2,
        "resistencia": 2, "pain": 1, "dor": 1,
    },
    "truque.importado": {
        # README: maquiagem coreana. RISABAE e' a fonte medida.
        "makeup": 3, "maquiagem": 3, "risabae": 3, "k-beauty": 3,
        "skincare": 3, "lipstick": 3, "batom": 3, "eyeliner": 3,
        "eyeshadow": 3, "delineador": 3, "foundation": 3, "base": 1,
        "glam": 3, "contour": 3, "blush": 3, "primer": 3, "corretivo": 3,
        "concealer": 3, "beauty": 2, "skin": 1, "pele": 1,
    },
    "cozinha.importada": {
        # README: receitas do mundo, com medida convertida. Este motor NAO
        # serve a cozinha (ver engine/escopo.py) — os termos existem aqui pra
        # o detector saber RECONHECER o tema quando ele cair na pasta errada.
        "recipe": 3, "receita": 3, "cook": 3, "cooking": 3, "cozinhar": 3,
        "bake": 3, "baking": 3, "assar": 3, "dessert": 3, "sobremesa": 3,
        "cookies": 3, "croissant": 3, "chocolate": 3, "tiramisu": 3,
        "chef": 3, "kitchen": 3, "cozinha": 3, "dough": 3, "massa": 2,
        "chicken": 2, "frango": 2, "butter": 2, "manteiga": 2,
        "dinner": 2, "jantar": 2, "sauce": 2, "molho": 2, "oven": 2,
        "forno": 2, "soup": 2, "sopa": 2,
    },
}


def _normalizar(texto: str) -> str:
    """Minusculas, sem acento, so' letras e digitos separados por espaco.

    ⚠️ O nome do bruto chega SUJO: sublinhado do YTDown, id do YouTube entre
    colchetes, hifen de separador, e as vezes mojibake do log. Trocar tudo
    que nao e' alfanumerico por espaco faz `AI-Safety_Expert[abc]` casar com
    `ai safety`, e deixa o mojibake virar espaco em vez de colar palavras.
    """
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " " + re.sub(r"[^a-z0-9]+", " ", t).strip() + " "


def pontuar(titulo: str) -> dict[str, int]:
    """Quanto o titulo pontua em cada canal."""
    t = _normalizar(titulo)
    notas = {}
    for canal, termos in TERMOS.items():
        # ⚠️ Casamento por PALAVRA INTEIRA. Sem isto `ia` casa dentro de
        # `social` e `via`, e `ai` dentro de `hair` e `train` — o titulo de
        # maquiagem viraria conteudo de chips na hora.
        #
        # ⚠️ E o PLURAL conta. Medido: "How To Make Proper CroissantS" pontuava
        # ZERO, porque a lista tem `croissant` no singular. Falha aberta nao
        # estraga nada, mas cega o detector de graca — e escrever cada termo
        # duas vezes na tabela e' pior que tratar aqui.
        notas[canal] = sum(p for termo, p in termos.items()
                           if f" {termo} " in t or f" {termo}s " in t)
    return notas


def conflito(titulo: str, canal_da_pasta: str | None) -> tuple[str, int, int] | None:
    """O tema contradiz a pasta? Devolve (canal_provavel, nota_dele, nota_da_pasta).

    None = pode disparar. Ver a REGRA DE DECISAO no topo do modulo.
    """
    pasta = (canal_da_pasta or "").strip().lower().lstrip("@")
    if not pasta:
        # Sem canal o vigia ja' recusa por conta propria, e com mensagem
        # melhor que a nossa. Nao ha' o que contradizer.
        return None
    notas = pontuar(titulo)
    nota_pasta = notas.get(pasta, 0)
    rival, nota_rival = max(
        ((c, n) for c, n in notas.items() if c != pasta),
        key=lambda x: x[1], default=("", 0))
    if nota_rival >= LIMIAR and nota_rival > nota_pasta:
        return rival, nota_rival, nota_pasta
    return None


def aviso(nome: str, canal_da_pasta: str, achado: tuple[str, int, int]) -> str:
    """A mensagem que vai pro log e pro Telegram.

    Diz o que FAZER, nao so' o que houve: quem le' isso precisa saber que o
    conserto e' mover o arquivo de pasta no Drive, e que o motor nao vai
    mover sozinho.
    """
    rival, nota_rival, nota_pasta = achado
    return (
        f"BRUTO NA PASTA ERRADA? nao disparei o corte.\n"
        f"  arquivo: {nome[:80]}\n"
        f"  pasta diz: {canal_da_pasta} (tema pontua {nota_pasta})\n"
        f"  tema diz:  {rival} (pontua {nota_rival})\n"
        f"  O que fazer: se a pasta esta' certa, ignore — eu tento de novo "
        f"na proxima passada e vou barrar de novo ate' o arquivo sair da "
        f"RAW. Se estiver errada, ARRASTE o arquivo pra pasta do {rival} no "
        f"Drive.\n"
        f"  Por que existo: em 04/09 o Yampolskiy caiu em SEM ANESTESIA e "
        f"rendeu 8 clipes de IA publicados no canal de comportamento.")
