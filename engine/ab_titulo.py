# -*- coding: utf-8 -*-
"""Teste A/B do TITULO NA TELA (25/09/2026, pedido do dono).

    A = o titulo como sai hoje (afirmacao: "A maquina de 400 milhoes")
    B = (25-27/09, ENCERRADO) o mesmo fato como PERGUNTA
    C = (desde 27/09) IDENTIFICACAO: nomeia a situacao de quem assiste
        ("Quando voce tem medo de errar a make")

⭐ POR QUE O C (27/09/2026, export do TikTok Studio de setembro): o unico
video que furou o teto de ~550 views em 4 canais (87.232, make) abre com
"Quando voce quer fazer uma maquiagem marcante mas tem medo do resultado";
7,1% de curtida/view contra 1-4% no resto. O acervo tem o mesmo achado
DEMONSTRADO (F01556: abrir nomeando a situacao de vida da pessoa). A pergunta
(B) ja' tinha medido mal (playbook: 0 de 4) e nao furou o teto.

So' o titulo NA TELA muda (os 2 s de abertura, que tambem sao a capa). A
legenda do post continua igual nos dois grupos: variar duas coisas juntas e'
o erro de 09/09, quando ninguem soube qual mexeu no numero.

O grupo sai do HASH do trecho (fonte + inicio), entao e' meio a meio, sem
escolha humana, e o mesmo trecho cai sempre no mesmo grupo. O grupo viaja no
post.json e no manifesto (`ab_titulo`) para a leitura de desempenho separar.

⚠️ B que falhou (modelo fora, resposta ruim) sai como A e e' marcado
`B_falhou`: entra na conta de NENHUM grupo. Misturar deixaria o B parecido
com o A e o teste diria "tanto faz" sem ter testado.
"""
from __future__ import annotations

import hashlib
import re
import os

LIGADO = os.environ.get("AB_TITULO", "1") != "0"
# ⭐ 26/09/2026: 70 -> 40, e vale pros DOIS grupos. O titulo do post (45-60
# letras) ia inteiro pra tela: 3 linhas, corpo encolhido ate' 55%, ilegivel
# nos 2 s. O acervo converge em <=40 letras / <=7 palavras (F132187,
# F136632, F134676). A e B passam pelo MESMO limite, entao o teste segue
# medindo so' afirmacao x pergunta. ⚠️ Posts de 25/09 (antes disto) sairam
# com titulo longo: o campo `titulo_tela_curto` separa na leitura.
MAX_CHARS = 40


# ⭐ 02/10/2026 (dono): grupo K = CAPA DE REVISTA. Engenharia reversa de 196
# capas da Capricho e revistas teen (_privado/capricho/ENGENHARIA_REVERSA.md):
# nome do idolo 87%, exclamacao 63%, numero 47%, gatilho (EXCLUSIVO,
# segredo, revela, descubra, mico) e angulo intimo. No Camarim o C nao serve
# (bastidor nao e' "situacao de quem assiste"): A x K. No Make: A x C x K.
GRUPOS_POR_CANAL = {"camarim.kpop": ("A", "K"), "truque.importado": ("A", "C", "K")}


def grupo(fonte: str, inicio_s, canal: str = "") -> str:
    h = hashlib.sha1(f"{fonte}|{round(float(inicio_s or 0), 1)}".encode()).hexdigest()
    gs = GRUPOS_POR_CANAL.get(canal, ("A", "C"))
    return gs[int(h[:8], 16) % len(gs)]


GATILHOS_CAPA = ("EXCLUSIVO", "SEGREDO", "REVELA", "DESCUBRA", "MICO", "SURPREENDE")


def _norm_fala(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in t if not unicodedata.combining(c)))


def como_capa(titulo: str, contexto: str = "", fala: str = "", canal: str = "") -> str | None:
    """O mesmo fato no formato de chamada de capa de revista teen.

    02/10/2026: estruturas medidas em 162 capas (_privado/capricho/): gatilho,
    "TEMA: promessa" (dois pontos, 174 chamadas), citacao em 1a pessoa entre
    aspas (22%) e, no Make, a OCASIAO da vida real (escola, festa, foto).
    Citacao so' passa se as palavras existem de verdade na `fala`.
    """
    from . import modelo_texto
    achou = re.search(r"\bd[oa]s? ((?:[A-Z0-9][\w&'-]*)(?: [A-Z0-9][\w&'-]*)*)", titulo)
    grupo_k = achou.group(1) if achou else ""
    make = canal == "truque.importado"
    r = modelo_texto.perguntar(
        "Reescreva o titulo abaixo de um video curto sobre idols de K-pop como CHAMADA "
        "DE CAPA de revista teen brasileira (estilo Capricho), em portugues correto do "
        "Brasil. Escolha UMA das estruturas, a que combinar melhor com o fato:\n"
        "- 'O SEGREDO de <idol> do <grupo> para <fato>!'\n"
        "- 'O MICO de <idol> do <grupo> <fato>!'\n"
        "- 'EXCLUSIVO: <idol> do <grupo> <fato>!'\n"
        "- '<idol> do <grupo> REVELA <fato>!'\n"
        "- 'DESCUBRA <fato> de <idol> do <grupo>!'\n"
        "- '<IDOL> do <grupo>: <promessa curta>!' (dois pontos)\n"
        "- '\"<frase curta que o idol DISSE na fala abaixo>\" — <idol> do <grupo>' "
        "(SO' se a fala tiver uma frase marcante; use as palavras exatas da fala)\n"
        "- '<numero> <coisas> de <idol> do <grupo>!' (so' se o video for lista)\n"
        + ("- 'Como fazer <o look/make> de <idol> do <grupo> PARA <escola/festa/foto/"
           "encontro>!' (so' se o video ensina a make; a ocasiao tem de combinar)\n"
           if make else "")
        + "Mantenha o NOME do idolo E o nome do GRUPO exatamente como no titulo; "
        "palavra-gatilho (se houver) em MAIUSCULAS; frase gramaticalmente correta. Nao "
        f"invente fato, nome ou numero. No maximo {MAX_CHARS + 8} caracteres, sem emoji, "
        "sem pergunta. Responda so' a chamada.\n\n"
        f"Titulo: {titulo}\nContexto: {contexto[:300]}\nFala do video: {fala[:900]}")
    # o _limpar tira aspas das pontas — aqui elas podem ser a CITACAO
    t = ((r or "").strip().splitlines() or [""])[0].strip()
    if not t or t.endswith("?") or len(t) > MAX_CHARS + 14 or len(t) < 10:
        return None
    if grupo_k and grupo_k.lower() not in t.lower():
        return None
    citacao = re.search(r"[\"“'‘](.{6,}?)[\"”'’]", t)
    if citacao:
        # ⛔ citacao inventada e' pior que nenhuma: tem de estar na fala
        if not fala or _norm_fala(citacao.group(1)) not in _norm_fala(fala):
            return None
        return t
    estrutura_ok = (any(g in t.upper() for g in GATILHOS_CAPA) or ":" in t
                    or (make and " PARA " in t.upper()))
    return t if estrutura_ok else None


# a identificacao precisa de um pouco mais de ar que a afirmacao
MAX_CHARS_C = 48


def como_identificacao(titulo: str, contexto: str = "") -> str | None:
    from . import modelo_texto
    r = modelo_texto.perguntar(
        "Escreva a frase de ABERTURA de um video curto, em portugues do Brasil, "
        "que NOMEIA a situacao de quem assiste, para a pessoa pensar 'sou eu'. "
        "Comece com 'Quando voce' ou 'Se voce'. Tem de ser verdade para o que o "
        "video mostra (o titulo e o contexto abaixo); nao invente fato, nome ou "
        f"numero. No maximo {MAX_CHARS_C} caracteres, sem aspas, sem emoji, sem "
        "ponto de interrogacao, sem explicacao. Responda so' a frase.\n\n"
        "Exemplo de outro video: 'Quando voce tem medo de errar a make'.\n\n"
        f"Titulo: {titulo}\nContexto: {contexto[:300]}")
    t = _limpar(r or "")
    ok = t.lower().startswith(("quando voc", "se voc"))
    if not ok or t.endswith("?") or len(t) > MAX_CHARS_C + 4 or len(t) < 14:
        return None
    return t


def _limpar(t: str) -> str:
    t = (t or "").strip().strip('"').strip("'").splitlines()[0].strip() if t else ""
    return t


def como_pergunta(titulo: str) -> str | None:
    from . import modelo_texto
    r = modelo_texto.perguntar(
        "Reescreva o titulo abaixo de um video curto como UMA pergunta curiosa em "
        "portugues do Brasil, que faca a pessoa querer ver a resposta no video. "
        "Mantenha o mesmo fato, os mesmos nomes e numeros; nao invente nada. "
        f"No maximo {MAX_CHARS} caracteres, termina com '?', sem aspas, sem emoji, "
        "sem explicacao. Responda so' a pergunta.\n\n"
        f"Titulo: {titulo}")
    p = _limpar(r or "")
    if not p or not p.endswith("?") or len(p) > MAX_CHARS + 5 or len(p) < 12:
        return None
    return p


def encurtar(titulo: str) -> str | None:
    """A MESMA afirmacao em <=40 letras, pra tela. None se nao der."""
    from . import modelo_texto
    r = modelo_texto.perguntar(
        "Encurte o titulo abaixo de um video curto para a tela de abertura, em "
        "portugues do Brasil. Mantenha o mesmo fato e a mesma forma (afirmacao "
        "continua afirmacao), os nomes e numeros principais; corte o resto e "
        "nao invente nada. Frase de impacto, sem artigo inicial se nao fizer "
        f"falta. No maximo {MAX_CHARS} caracteres e 7 palavras, sem aspas, sem "
        "emoji, sem explicacao. Responda so' o titulo.\n\n"
        f"Titulo: {titulo}")
    t = _limpar(r or "")
    if not t or len(t) > MAX_CHARS + 5 or len(t) < 8 or t.endswith("?"):
        return None
    return t


def aplicar(c: dict, fonte: str) -> str:
    """Decide o grupo, grava em `c` e devolve o titulo que vai NA TELA."""
    titulo = c.get("titulo", "")
    if not LIGADO or not titulo:
        return titulo
    g = grupo(fonte, c.get("inicio_s"), (os.environ.get("CANAL_ESPERADO") or "").strip().lower())
    c["ab_titulo"] = g
    c["titulo_tela"] = titulo
    if g == "C":
        p = como_identificacao(titulo, str(c.get("gancho") or c.get("descricao") or ""))
        if p:
            c["titulo_tela"] = p
        else:
            c["ab_titulo"] = "C_falhou"
    elif g == "K":
        p = como_capa(titulo, str(c.get("gancho") or c.get("descricao") or ""),
                      str(c.get("_fala") or ""), (os.environ.get("CANAL_ESPERADO") or "").strip().lower())
        if p:
            c["titulo_tela"] = p
        else:
            c["ab_titulo"] = "K_falhou"
    if (c["ab_titulo"] != "C" and len(c["titulo_tela"]) > MAX_CHARS + 5
            and not c["titulo_tela"].endswith("?")):
        curto = encurtar(c["titulo_tela"])
        if curto:
            c["titulo_tela"] = curto
    # False = foi longo pra tela (modelo fora): o card encolhe e quebra em 3
    c["titulo_tela_curto"] = len(c["titulo_tela"]) <= (
        MAX_CHARS_C + 4 if c["ab_titulo"] == "C" else MAX_CHARS + 5)
    print(f"      A/B do titulo: grupo {c['ab_titulo']} -> \"{c['titulo_tela'][:60]}\"")
    return c["titulo_tela"]
