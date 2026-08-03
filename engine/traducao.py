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


def _traduzir_texto(texto: str) -> str:
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
                    "contents": [{"parts": [{"text": PROMPT.format(texto=texto)}]}],
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
            raise
        except Exception as e:
            ultimo_erro = e
            time.sleep(1)
    raise RuntimeError(f"tradução falhou em todas as chaves: {ultimo_erro}")


def _redistribuir(palavras_traduzidas: list[str], inicio: float, fim: float) -> list[dict]:
    """Espalha as palavras traduzidas dentro da janela [inicio, fim],
    proporcional ao tamanho de cada palavra (palavra maior demora mais)."""
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


def traduzir_segmentos(palavras: list[dict], tamanho_janela_s: float = 4.0) -> list[dict]:
    """Recebe [{palavra, inicio, fim}] no idioma original e devolve trechos
    traduzidos em texto corrido: [{inicio, fim, texto}]. Usado pra dublagem
    (TTS fala o texto inteiro do trecho, não palavra por palavra)."""
    if not palavras:
        return []
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
        resultado.extend(_redistribuir(novas_palavras, seg["inicio"], seg["fim"]))
    return resultado


def traduzir_palavras(palavras: list[dict], tamanho_janela_s: float = 4.0) -> list[dict]:
    """Recebe [{palavra, inicio, fim}] no idioma original e devolve a mesma
    estrutura traduzida pra pt-BR, com timing reencaixado.

    Traduz em janelas de ~tamanho_janela_s (não a palavra isolada, nem o
    clipe inteiro de uma vez) pra manter contexto de frase sem estourar
    muito a sincronia do trecho.
    """
    if not palavras:
        return []
    segmentos = traduzir_segmentos(palavras, tamanho_janela_s)
    return segmentos_para_palavras(segmentos)
