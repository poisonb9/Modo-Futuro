"""Gera .ass com efeito karaokê (palavra acende conforme é falada) e
destaque de palavra por grupo (ver engine/destaque.py).
"""
import itertools
import os
from pathlib import Path

from . import destaque as _destaque

MAX_LINHA = 3          # palavras por tela — Shorts pede pouco texto e grande
BASE = "&H00FFFFFF"      # branco

# Paleta do destaque de palavra — girada por grupo, na ordem abaixo.
# Valores em BGR (formato de override do ASS, "&HBBGGRR&"), sem rosa: pedido
# do Bryan em 02/08/2026 foi mapear a referência (rosa/vermelho/azul) para
# azul/verde/vermelho, mantendo vermelho como vermelho.
_AZUL = "&HFF9900&"       # RGB(0,153,255)
_VERDE = "&H76E600&"      # RGB(0,230,118)
_VERMELHO = "&H303BFF&"   # RGB(255,59,48)
PALETA = (_AZUL, _VERDE, _VERMELHO)

# Cor por SENTIDO da palavra, não por rotação (pedido do Bryan em 26/08/2026).
# Quem decide qual é qual é o Gemini, em engine/destaque.py — aqui só traduz o
# nome pra cor do ASS.
POR_NOME = {"vermelho": _VERMELHO, "azul": _AZUL, "verde": _VERDE}
_RESET = "&HFFFFFF&"      # branco, pra voltar depois da palavra destacada

# Estilo 1 = o que o canal já usava até 02/08/2026 (Inter Black, corpo fixo).
# Estilo 2 = pedido do Bryan em 02/08/2026: réplica da referência (Erica
# Bruno) — mesma fonte do card de título (Poppins Bold, engine/render.py),
# mesmo esquema de cor do destaque (idêntico ao estilo 1, já bate com a
# referência), e a dinâmica de tamanho variável entre grupos (a "linha de
# cima" às vezes maior que a de baixo). Não dá pra saber ao certo QUAL grupo
# ela aumenta — a regra escolhida aqui é: o grupo que tem palavra destacada
# (mais "peso" na frase) cresce, o resto fica no tamanho normal. Reaproveita
# o mesmo destaque.marcar() já chamado, sem gasto extra de API.
FONTE_ESTILO_2 = "Poppins Bold"
_ESTILO_2_CRESCE = 1.22   # corpo do grupo COM destaque
_ESTILO_2_NORMAL = 0.90   # corpo do grupo SEM destaque
# Bryan (02/08/2026, olhando o teste): "não tá igual", "tem um sombreado
# também", "sombreado meio esfumaçado" — o \shad do ASS é sombra DURA
# (silhueta sólida deslocada), a referência tem sombra com borda suave. \be
# (blur edges) desfoca contorno E sombra juntos — é o jeito do ASS chegar
# perto de "esfumaçado" sem precisar pré-renderizar em PIL feito o título.
#
# BUG achado depois de 3 rodadas de teste sem sombra visível nenhuma: o byte
# de alfa do ASS é INVERTIDO do que parece óbvio — 00 é OPACO, FF é
# TRANSPARENTE. BackColour estava em &H80000000 (~50% transparente, quase
# some) achando que era "bem visível". Confirmado isolado num fundo cinza
# antes de mexer no vídeo de verdade: com &H00000000 (opaco) a sombra
# esfumaçada aparece de vez.
#
# 2ª correção no mesmo dia: o \shad do ASS desloca a sombra pra
# baixo-direita (silhueta duplicada, não um halo). Bryan queria o efeito
# ENVOLVENDO a letra inteira, não puxado pra um lado. Solução: SHADOW=0 (sem
# deslocamento) e o halo vem do próprio CONTORNO borrado por \be.
#
# 3ª correção: comparando com a referência lado a lado, ela não é borrada
# por igual — a borda BEM colada na letra é nítida, só a parte mais externa
# desfoca (gradiente nítido→difuso). Um \be só não faz isso: ele borra tudo
# junto por igual. Precisa de DUAS camadas desenhadas na mesma posição:
# uma sombra preta grossa e borrada por trás (Layer 0), e o texto de
# verdade por cima, com contorno fino e SEM blur (Layer 1) — a parte da
# sombra que fica embaixo do texto nítido não aparece, só a franja borrada
# que sobra pra fora do contorno fino.
_ESTILO_2_BLUR = 4.5
_PRETO = "&H00000000"   # opaco — ver bug do alfa acima

# ⭐ Estilo 3 = PREMIUM (25/09/2026, aprovado pelo Bryan na comparação lado a
# lado sobre o bruto da sala limpa: fundo ocupado, amarelo e quase branco).
# A autópsia do estilo 2 achou cinco defeitos, cada constante abaixo é a
# resposta a um deles:
#   1. letra pequena no celular (3,8% da altura)     -> _PREMIUM_CORPO 5,8%
#   2. grupo fixo de 3 corta a frase ("…PORQUE UMA") -> _agrupar_premium, por
#      SENTIDO: nunca termina em palavra fraca, quebra na pausa da fala
#   3. vermelho/azul/verde sem critério              -> UMA cor só, a do canal
#   4. some em fundo claro                           -> sombra difusa larga
#   5. karaokê desligado (cor base == cor de acento) -> a palavra FALADA acende
# Não chama o Gemini (destaque.marcar): quem acende é o tempo da fala.
FONTE_PREMIUM = "Poppins Bold"
_PREMIUM_CORPO = 0.058
_PREMIUM_ACENTO = "&H00D2FF&"     # âmbar RGB(255,210,0), em BGR
_PREMIUM_MAX_PAL = 3
_PREMIUM_MAX_CAR = 16
_PREMIUM_PAUSA = 0.25             # silêncio que fecha o grupo
_PREMIUM_ANTECIPA = 0.06          # o texto chega 60 ms antes da voz
# largura média de uma letra MAIÚSCULA da Poppins Bold / corpo. Medido: 0,33
# na comparação de 25/09; 0,36 deixa folga pro acento crescer 8%.
_PREMIUM_LETRA = 0.36
PALAVRA_FRACA = {"a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das",
                 "e", "que", "por", "porque", "para", "pra", "com", "em", "no", "na",
                 "nos", "nas", "sem", "se", "só", "é", "ao", "à", "mas", "ou",
                 "the", "of", "to", "and", "in", "on", "for", "with", "is"}


def _t(seg: float) -> str:
    seg = max(0.0, seg)
    h, resto = divmod(seg, 3600)
    m, s = divmod(resto, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def escrever(palavras: list[dict], destino: Path, largura: int, altura: int,
             estilo: int = 1, oculto_ate: float = 0.0,
             estreito: tuple | list | None = None) -> Path | None:
    """Cria o arquivo .ass. Devolve None se não houver o que legendar.

    `estilo`: 1 = padrão do canal (Inter Black, corpo fixo). 2 = réplica da
    referência (Poppins Bold, corpo variável — ver FONTE_ESTILO_2 acima).
    3 = premium (ver FONTE_PREMIUM acima)."""
    # ⭐ CAPA LIMPA (25/09/2026): o TikTok usa o 1o quadro como capa, e nele a
    # 1a palavra da legenda saia queimada no meio ("ELA EXPLICOU QUE") — cara
    # de corte automatico na grade inteira. Enquanto o titulo esta' na tela
    # (`oculto_ate`), nao ha' legenda; a fala segue normal.
    if oculto_ate > 0:
        palavras = [dict(p, inicio=max(p["inicio"], oculto_ate))
                    for p in palavras if p["fim"] > oculto_ate]
    if not palavras:
        return None
    if estilo == 3:
        return _escrever_premium(palavras, destino, largura, altura, estreito)

    # fonte proporcional à altura: mesma leitura em 9:16 e 16:9. Menor que
    # antes e com margem lateral generosa — texto fica num bloco central,
    # nunca encosta na borda mesmo em frase mais longa.
    corpo = max(22, int(altura * 0.038))
    fontname = FONTE_ESTILO_2 if estilo == 2 else "Inter Black"
    # LEGENDA_MARGEM_V_FRAC: override pontual pra vídeo específico com algo
    # cobrindo a legenda na posição normal (ex: caixa branca de UI na fonte).
    #
    # Padrão subiu de 0.18 para 0.30 em 28/07/2026: a 18% da base a legenda
    # cai justamente na faixa que a UI do TikTok ocupa — nome do perfil,
    # curtir, comentar, compartilhar. O corpus recomenda o texto
    # ligeiramente acima do centro (PLAYBOOK §5). Legenda escondida atrás
    # de botão não é lida, e legenda é uma das 3 camadas de edição que
    # sustentam o RPM.
    frac_v = float(os.environ.get("LEGENDA_MARGEM_V_FRAC", "0.30"))
    margem_v = int(altura * frac_v)   # sobe o texto: no Shorts a UI cobre a base
    margem_lat = int(largura * 0.12)
    # Estilo 1: contorno único, sem sombra à parte (como sempre foi).
    # Estilo 2: contorno FINO e nítido na camada de cima (Style K) — a
    # sombra borrada vem de uma camada separada atrás (Style S), mais grossa
    # de propósito pra sobrar franja borrada pra fora do contorno nítido.
    contorno = max(2, corpo // (24 if estilo == 2 else 14))
    contorno_sombra = max(3, corpo // 6)
    sombra = 0 if estilo == 2 else 2
    cor_sombra = "&H80000000"   # só usado no estilo 1

    estilo_s = ""
    if estilo == 2:
        estilo_s = (f"\nStyle: S,{fontname},{corpo},{_PRETO},{_PRETO},{_PRETO},"
                    f"{_PRETO},-1,0,0,0,100,100,0,0,1,{contorno_sombra},0,2,"
                    f"{margem_lat},{margem_lat},{margem_v},1")

    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {largura}
PlayResY: {altura}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: K,{fontname},{corpo},{BASE},{BASE},&H00000000,{cor_sombra},-1,0,0,0,100,100,0,0,1,{contorno},{sombra},2,{margem_lat},{margem_lat},{margem_v},1{estilo_s}

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

    grupos = [palavras[i:i + MAX_LINHA] for i in range(0, len(palavras), MAX_LINHA)]
    destaques = _destaque.marcar(grupos)

    linhas = []
    for grupo, (idx_destaque, nome_cor) in zip(grupos, destaques):
        ini, fim = grupo[0]["inicio"], grupo[-1]["fim"]
        if fim <= ini:
            fim = ini + 0.4
        cor = POR_NOME.get(nome_cor or "", _VERDE) if idx_destaque is not None else None

        # Estilo 2: o grupo inteiro cresce ou encolhe conforme tem ou não
        # destaque — é a dinâmica de "linha de cima às vezes maior" da
        # referência. \fs é override de tamanho por trecho de texto do ASS;
        # vai uma vez no início da linha, vale pro resto dela.
        fs_override = ""
        if estilo == 2:
            fator = _ESTILO_2_CRESCE if idx_destaque is not None else _ESTILO_2_NORMAL
            fs_override = f"\\fs{round(corpo * fator)}"

        # \k usa centésimos de segundo
        partes = [f"{{{fs_override}}}"] if fs_override else []
        for j, p in enumerate(grupo):
            dur = max(1, int((p["fim"] - p["inicio"]) * 100))
            palavra = p["palavra"].upper()
            if j == idx_destaque:
                partes.append(f"{{\\k{dur}\\c{cor}}}{palavra} {{\\c{_RESET}}}")
            else:
                partes.append(f"{{\\k{dur}}}{palavra} ")
        texto = "".join(partes).strip()
        # ⭐ 25/09: enquanto o balao de COMENTARIO esta' na tela (lado direito),
        # a legenda ganha margem direita e quebra a' esquerda dele.
        # `estreito`: uma janela (ini, fim, fracao) ou lista de (ini, fim,
        # fracao, lado); lado "esq" abre espaco a' esquerda (balao ali).
        ml, mr = _margens(estreito, ini, fim, largura)
        linhas.append(f"Dialogue: 1,{_t(ini)},{_t(fim)},K,,{ml},{mr},0,,{texto}")

        if estilo == 2:
            # Camada de sombra, MESMO texto (sem cor — só a silhueta borrada
            # importa), Layer 0 = desenhada ATRÁS da camada nítida acima.
            palavras_planas = " ".join(p["palavra"].upper() for p in grupo)
            texto_sombra = f"{{{fs_override}\\be{_ESTILO_2_BLUR}}}{palavras_planas}"
            linhas.append(f"Dialogue: 0,{_t(ini)},{_t(fim)},S,,{ml},{mr},0,,{texto_sombra}")

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    return destino


def _margens(estreito, ini: float, fim: float, largura: int) -> tuple[int, int]:
    """(margem esq, margem dir) extra enquanto um balão cruza a legenda."""
    ml = mr = 0
    for jan in ([estreito] if isinstance(estreito, tuple) else estreito or []):
        if ini < jan[1] and fim > jan[0]:
            lado = jan[3] if len(jan) > 3 else "dir"
            if lado in ("esq", "ambos"):
                ml = max(ml, int(largura * jan[2]))
            if lado in ("dir", "ambos"):
                mr = max(mr, int(largura * jan[2]))
    return ml, mr


def _agrupar_premium(palavras: list[dict]) -> list[list[dict]]:
    """Grupos por SENTIDO: fecha na pausa da fala ou quando enche (3 palavras
    ou 16 letras) — mas nunca termina em palavra fraca ("…PORQUE UMA").

    Quando enche com palavra fraca no fim, ela RECUA pro começo do próximo
    grupo ("MILHÕES" / "PORQUE UMA POEIRA"). A 1a versão deixava a fraca
    segurar o grupo aberto: saía "MILHÕES PORQUE UMA POEIRA", 25 letras, que
    não cabe numa linha e quebrava com "MILHÕES" sozinho em cima."""
    def fraca(p):
        return p["palavra"].lower().strip(".,!?;:") in PALAVRA_FRACA

    grupos, g = [], []
    for i, p in enumerate(palavras):
        g.append(p)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        if prox is None:
            grupos.append(g)
            break
        texto = " ".join(x["palavra"] for x in g)
        if prox["inicio"] - p["fim"] > _PREMIUM_PAUSA:
            grupos.append(g)
            g = []
        elif (len(g) >= _PREMIUM_MAX_PAL
              or len(texto) + 1 + len(prox["palavra"]) > _PREMIUM_MAX_CAR):
            k = len(g)
            while k > 1 and fraca(g[k - 1]):
                k -= 1
            # só fracas ("PORQUE UMA"): segue aberto até a palavra de peso —
            # "PORQUE" sozinho na tela não diz nada. Se passar da largura,
            # a quebra/encolhimento em _escrever_premium resolve.
            if k == 1 and fraca(g[0]):
                continue
            grupos.append(g[:k])
            g = g[k:]
    return grupos


def _ponto_de_quebra(tokens: list[str], cabe: int) -> int | None:
    """Índice depois do qual entra \\N, ou None se a linha cabe inteira.
    A quebra é decidida AQUI, igual pra sombra e pro texto: deixar o libass
    quebrar sozinho faria as duas camadas discordarem quando a palavra ativa
    cresce 8%."""
    if len(" ".join(tokens)) <= cabe or len(tokens) < 2:
        return None
    meio = len(" ".join(tokens)) / 2
    melhor, dist = None, 1e9
    for k in range(len(tokens) - 1):
        # palavra fraca nunca fica pendurada no fim da 1a linha ("A" /
        # "EXTRAORDINÁRIA"): sem quebra boa, quem resolve é o corpo menor
        if tokens[k].lower() in PALAVRA_FRACA:
            continue
        d = abs(len(" ".join(tokens[:k + 1])) - meio)
        if d < dist:
            melhor, dist = k, d
    return melhor


def _escrever_premium(palavras: list[dict], destino: Path, largura: int,
                      altura: int, estreito) -> Path:
    corpo = max(22, int(altura * _PREMIUM_CORPO))
    frac_v = float(os.environ.get("LEGENDA_MARGEM_V_FRAC", "0.30"))
    margem_v = int(altura * frac_v)
    margem_lat = int(largura * 0.08)
    contorno = max(4, corpo // 14)
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {largura}
PlayResY: {altura}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: P,{FONTE_PREMIUM},{corpo},{BASE},{BASE},{_PRETO},{_PRETO},-1,0,0,0,100,100,1,0,1,{contorno},0,2,{margem_lat},{margem_lat},{margem_v},1
Style: S,{FONTE_PREMIUM},{corpo},{_PRETO},{_PRETO},{_PRETO},{_PRETO},-1,0,0,0,100,100,1,0,1,{corpo // 5},0,2,{margem_lat},{margem_lat},{margem_v},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    grupos = _agrupar_premium(palavras)
    inis = [max(0.0, g[0]["inicio"] - _PREMIUM_ANTECIPA) for g in grupos]
    linhas = []
    for n, g in enumerate(grupos):
        ini = inis[n]
        fim = g[-1]["fim"]
        if fim <= ini:
            fim = ini + 0.4
        # ⚠️ o grupo SAI quando o próximo ENTRA. Com os 60 ms de antecipação
        # os dois se sobrepunham, e o libass trata sobreposição na mesma
        # camada como colisão: empurra o grupo novo pra CIMA e ele fica lá
        # a vida toda — uma caixa escura fantasma acima da frase (visto no
        # quadro amarelo da comparação de 25/09).
        if n + 1 < len(grupos):
            fim = min(fim, inis[n + 1])
        if fim - ini < 0.05:
            continue
        ml, mr = _margens(estreito, ini, fim, largura)
        # ⚠️ no ASS a margem do EVENTO (se não for 0) SUBSTITUI a do estilo,
        # não soma — contar as duas subestimava o espaço em ~170 px
        util = largura - (ml or margem_lat) - (mr or margem_lat)
        cabe = int(util / (corpo * _PREMIUM_LETRA))
        tokens = [p["palavra"].upper() for p in g]
        q = _ponto_de_quebra(tokens, cabe)
        # linha única que não cabe e não tem quebra boa: encolhe SÓ esse grupo
        maior = max(len(" ".join(tokens[:q + 1])), len(" ".join(tokens[q + 1:]))) \
            if q is not None else len(" ".join(tokens))
        fs = f"\\fs{int(corpo * cabe / maior)}" if maior > cabe else ""

        def juntar(partes):
            return "".join(t + ("" if j == len(partes) - 1 else "\\N" if j == q else " ")
                           for j, t in enumerate(partes))

        # sombra difusa atrás (camada 0): contraste em QUALQUER fundo
        linhas.append(f"Dialogue: 0,{_t(ini)},{_t(fim)},S,,{ml},{mr},0,,"
                      f"{{{fs}\\be8\\alpha&H70&\\fad(60,0)}}{juntar(tokens)}")
        # texto (camada 1): um evento por palavra falada, ela acende em âmbar
        # e cresce 8%; o grupo entra com "pop" de 92% -> 100% em 110 ms
        for k in range(len(g)):
            a0 = ini if k == 0 else max(ini, g[k]["inicio"])
            a1 = fim if k + 1 == len(g) else min(fim, g[k + 1]["inicio"])
            if a1 - a0 < 0.01:
                continue
            partes = [f"{{\\c{_PREMIUM_ACENTO}\\fscx108\\fscy108}}{t}"
                      f"{{\\c{_RESET}\\fscx100\\fscy100}}" if j == k else t
                      for j, t in enumerate(tokens)]
            pop = "\\fscx92\\fscy92\\t(0,110,\\fscx100\\fscy100)" if k == 0 else ""
            abre = f"{{{fs}{pop}}}" if fs or pop else ""
            linhas.append(f"Dialogue: 1,{_t(a0)},{_t(a1)},P,,{ml},{mr},0,,{abre}{juntar(partes)}")

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    return destino


def faixa_ocupada(altura: int, linhas: int = 2) -> tuple[int, int]:
    """(topo, base) em pixels da faixa que a legenda ocupa. FONTE UNICA.

    ⚠️ ISTO EXISTE PORQUE EU COPIEI O NUMERO EM VEZ DE DERIVAR DELE. Em
    13/09/2026 a cascata de CTA foi posicionada em 0,60 da altura — dentro da
    legenda, que ocupa de ~0,605 a 0,70. O Bryan viu na tela: "está em cima da
    legenda". Eu ja' tinha consertado a MESMA colisao horas antes, no selo
    anterior, movendo um numero — consertei a instancia e nao a classe.

    ⭐ A REGRA QUE SOBROU: quem desenha por cima do video PERGUNTA aqui onde a
    legenda esta'. Ninguem mais escreve 0,30 nem 0,70 em lugar nenhum.

    ⚠️ `linhas=2` e' orcamento, nao medida: a legenda quebra em uma ou duas
    linhas conforme a frase, e reservar duas e' o lado seguro. Reservar uma
    deixaria a colisao voltar em frase longa — e voltaria CALADA, porque nada
    no render reclama de sobreposicao.

    ⭐ 25/09/2026: mede pelo estilo 3 (premium, 5,8%), o MAIOR dos três.
    Quem ainda roda estilo 1 ou 2 reserva um pouco a mais — lado seguro.
    """
    corpo = max(22, int(altura * _PREMIUM_CORPO))
    frac_v = float(os.environ.get("LEGENDA_MARGEM_V_FRAC", "0.30"))
    base = altura - int(altura * frac_v)
    # entrelinha do ASS fica perto de 1,25 do corpo
    topo = base - int(corpo * 1.25 * max(1, linhas))
    return topo, base
