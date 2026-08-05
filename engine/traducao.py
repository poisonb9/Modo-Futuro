"""Tradução de legenda pra pt-BR — sem dublagem, só o texto que fica queimado.

Groq devolve timestamp por palavra NO IDIOMA ORIGINAL. Traduzir palavra por
palavra quebraria a ordem (inglês e português não têm a mesma estrutura de
frase), então a abordagem é: traduzir o trecho inteiro de uma vez com o
Gemini, e redistribuir as palavras traduzidas dentro da MESMA janela de tempo
do trecho original, proporcional ao tamanho de cada palavra. Não é
sincronismo labial nem por palavra exata — é karaokê aproximado, suficiente
pra legenda (não estamos dublando áudio).
"""
import re
import time

import requests

import config
from . import keys

PROMPT = """Traduza a fala abaixo para português do Brasil, natural e coloquial
(é legenda de vídeo curto, não documento formal). Mantenha o mesmo número
aproximado de frases. Responda SOMENTE com o texto traduzido, sem aspas,
sem comentário, sem markdown.

Fala original:
{texto}"""

# Usado só quando --dublar: a fala original costuma ter mais de uma pessoa
# (entrevistador perguntando, entrevistado respondendo) e cacoetes de fala
# ("ok ok", repetição, gagueira). Traduzir isso literalmente faz a voz
# clonada (uma pessoa só) "interpretar" os dois lados do diálogo, o que
# soa estranho. Aqui a IA reescreve como um NARRADOR CONTANDO A HISTÓRIA
# do que está acontecendo com base no que os personagens disseram — não
# é dublagem das falas deles, é o narrador relatando os fatos.
PROMPT_NARRACAO = """A fala abaixo é a transcrição de um vídeo e pode ter mais de
uma pessoa falando (por exemplo: entrevistador perguntando, entrevistado
respondendo), além de cacoetes de fala como "ok ok", repetições e gagueira.

Reescreva isso em português do Brasil como se VOCÊ fosse um narrador contando
a história do que está acontecendo, com base no que os personagens disseram
— não é dublar/interpretar as falas deles, é você relatando os fatos e o que
foi dito (ex: em vez de reproduzir a pergunta e a resposta como diálogo,
narre o que aconteceu: "ela explicou que..." / "ele mostrou como..."). Um só
narrador falando o tempo todo, nunca trocando de personagem. Mantenha o
MESMO ASSUNTO e as MESMAS informações e fatos (não invente nada, não resuma
demais), só remova a troca de interlocutor e os cacoetes de fala, deixando o
texto linear e natural de se ouvir em voz alta. Responda SOMENTE com o texto
reescrito, sem aspas, sem comentário, sem markdown.

Fala original:
{texto}"""


def _traduzir_texto(texto: str, prompt: str = PROMPT) -> str:
    if not texto.strip():
        return texto

    rot = keys.gemini()
    ultimo_erro = None
    for _ in range(len(rot) * 2):
        chave = rot.proxima()
        try:
            r = requests.post(
                f"{config.GEMINI_URL}/models/{config.GEMINI_MODELO}:generateContent?key={chave}",
                json={
                    "contents": [{"parts": [{"text": prompt.format(texto=texto)}]}],
                    "generationConfig": {"temperature": 0.3},
                },
                timeout=60,
            )
            if r.status_code in (429, 403):
                rot.queimar(chave)
                continue
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except requests.HTTPError as e:
            ultimo_erro = e
            if e.response is not None and e.response.status_code in (429, 403):
                rot.queimar(chave)
                continue
            # 503 é sobrecarga TRANSITÓRIA do servidor (mesmo padrão do
            # nemotron.py), não chave sem cota — tentar de novo resolve,
            # crashar o run inteiro por isso jogaria fora um clipe já
            # transcrito (medido: run 30860861087, clipe nota 96 perdido).
            if e.response is not None and e.response.status_code == 503:
                time.sleep(2)
                continue
            raise
        except Exception as e:
            ultimo_erro = e
            time.sleep(1)
    raise RuntimeError(f"tradução falhou em todas as chaves: {ultimo_erro}")


def redistribuir_palavras(palavras_traduzidas: list[str], inicio: float, fim: float) -> list[dict]:
    """Espalha as palavras traduzidas dentro da janela [inicio, fim],
    proporcional ao tamanho de cada palavra (palavra maior demora mais).
    Pública porque `voz_clonada` reaproveita pra alinhar a legenda ao
    timing REAL do áudio dublado (não ao timing do vídeo original)."""
    if not palavras_traduzidas:
        return []
    pesos = [max(1, len(p)) for p in palavras_traduzidas]
    total = sum(pesos)
    dur = max(0.4, fim - inicio)

    saida, t = [], inicio
    for p, peso in zip(palavras_traduzidas, pesos):
        d = dur * (peso / total)
        saida.append({"palavra": p, "inicio": round(t, 3), "fim": round(t + d, 3)})
        t += d
    return saida


def _agrupar(palavras: list[dict], tamanho_janela_s: float) -> list[list[dict]]:
    grupos, atual = [], []
    inicio_grupo = palavras[0]["inicio"]
    for p in palavras:
        atual.append(p)
        if p["fim"] - inicio_grupo >= tamanho_janela_s:
            grupos.append(atual)
            atual = []
            inicio_grupo = p["fim"]
    if atual:
        grupos.append(atual)
    return grupos


def _distribuir_texto_em_janelas(texto: str, grupos: list[list[dict]]) -> list[dict]:
    """Divide um texto reescrito (já não bate mais 1:1 com as janelas
    originais, porque a reescrita muda o número de palavras) nas mesmas
    janelas de tempo dos grupos, proporcional à duração de cada uma —
    igual espírito do _redistribuir, mas em nível de texto corrido em vez
    de palavra por palavra."""
    texto = texto.strip()
    inicio_total = grupos[0][0]["inicio"]
    fim_total = grupos[-1][-1]["fim"]
    duracao_total = max(0.1, fim_total - inicio_total)
    n = len(texto)

    resultado, pos, acumulado = [], 0, 0.0
    for i, grupo in enumerate(grupos):
        acumulado += grupo[-1]["fim"] - grupo[0]["inicio"]
        if i == len(grupos) - 1:
            corte = n
        else:
            corte = round(n * (acumulado / duracao_total))
            while corte < n and not texto[corte].isspace():
                corte += 1
        resultado.append({
            "inicio": grupo[0]["inicio"],
            "fim": grupo[-1]["fim"],
            "texto": texto[pos:corte].strip(),
        })
        pos = corte
    return resultado


def traduzir_segmentos(palavras: list[dict], tamanho_janela_s: float = 4.0,
                        narrar: bool = False) -> list[dict]:
    """Recebe [{palavra, inicio, fim}] no idioma original e devolve trechos
    traduzidos em texto corrido: [{inicio, fim, texto}]. Usado pra dublagem
    (TTS fala o texto inteiro do trecho, não palavra por palavra).

    narrar=True (usado com --dublar): em vez de traduzir cada janela de
    ~4s isoladamente (o que preserva vaivém de diálogo e cacoetes de fala
    da transcrição original), reescreve o trecho INTEIRO de uma vez como
    narração de um narrador só, depois distribui esse texto nas mesmas
    janelas de tempo. Ver PROMPT_NARRACAO."""
    if not palavras:
        return []

    if narrar:
        texto_completo = " ".join(p["palavra"] for p in palavras)
        texto_narrado = _traduzir_texto(texto_completo, prompt=PROMPT_NARRACAO)
        grupos = _agrupar(palavras, tamanho_janela_s)
        return _distribuir_texto_em_janelas(texto_narrado, grupos)

    resultado = []
    for grupo in _agrupar(palavras, tamanho_janela_s):
        texto_original = " ".join(p["palavra"] for p in grupo)
        traduzido = _traduzir_texto(texto_original)
        resultado.append({
            "inicio": grupo[0]["inicio"],
            "fim": grupo[-1]["fim"],
            "texto": traduzido,
        })
    return resultado


def segmentos_para_palavras(segmentos: list[dict]) -> list[dict]:
    """Converte [{inicio, fim, texto}] em [{palavra, inicio, fim}] pra
    legenda karaokê, redistribuindo o texto de cada segmento na sua janela."""
    resultado = []
    for seg in segmentos:
        novas_palavras = re.findall(r"\S+", seg["texto"])
        resultado.extend(redistribuir_palavras(novas_palavras, seg["inicio"], seg["fim"]))
    return resultado


def traduzir_palavras(palavras: list[dict], tamanho_janela_s: float = 4.0,
                       narrar: bool = False) -> list[dict]:
    """Recebe [{palavra, inicio, fim}] no idioma original e devolve a mesma
    estrutura traduzida pra pt-BR, com timing reencaixado.

    Traduz em janelas de ~tamanho_janela_s (não a palavra isolada, nem o
    clipe inteiro de uma vez) pra manter contexto de frase sem estourar
    muito a sincronia do trecho.
    """
    if not palavras:
        return []
    segmentos = traduzir_segmentos(palavras, tamanho_janela_s, narrar=narrar)
    return segmentos_para_palavras(segmentos)
