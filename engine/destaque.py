"""Marca a palavra de maior impacto em cada grupo de legenda, via Gemini.

Padrão visto numa referência (Erica Bruno, TikTok, 02/08/2026): a legenda
fica branca por padrão e só UMA palavra por grupo ganha cor sólida — não é
a palavra sendo falada acendendo tipo karaokê, é uma escolha editorial de
qual palavra "pesa mais" na frase (verbo de ação, pronome direto, urgência).
Pedimos pro Gemini marcar essa palavra, numa chamada só por clipe (não uma
por grupo — o clipe inteiro tem ~20-30 grupos, uma chamada só é suficiente
e mais barato).
"""
import json
import re
import time

import requests

import config
from . import keys

PROMPT = """Você edita legendas de vídeos virais de TikTok em português do Brasil.

Primeiro, a fala COMPLETA do clipe, pra você entender o contexto e o que
realmente importa em cada parte (o que é revelação, o que é só conectivo):
"{contexto}"

Agora, a mesma fala quebrada em trechos curtos de legenda (cada um até 3
palavras), numerados na ordem em que aparecem no vídeo. Para CADA trecho,
escolha a palavra de MAIOR IMPACTO editorial pra destacar com cor — o tipo
de palavra que uma editora profissional destacaria pra prender atenção
(verbo de ação forte, pronome direto tipo "você", superlativo, palavra de
urgência ou revelação), julgando pelo peso da palavra DENTRO DA FRASE
COMPLETA acima, não isolada. Nem todo trecho precisa ter destaque: se
nenhuma palavra se destacar claramente, responda -1 pra esse trecho.

Responda SOMENTE um array JSON de inteiros, um por trecho, na mesma ordem,
com o ÍNDICE (começando em 0) da palavra escolhida dentro do trecho, ou -1.
Sem markdown, sem comentário, sem texto antes ou depois do array.

Trechos:
{trechos}"""


def _extrair_json(saida: str) -> str:
    saida = saida.strip()
    saida = re.sub(r"^```(json)?", "", saida).strip()
    saida = re.sub(r"```$", "", saida).strip()
    return saida


def marcar(grupos: list[list[dict]]) -> list[int | None]:
    """Devolve, por grupo, o índice (0-based) da palavra destacada, ou None."""
    if not grupos:
        return []

    trechos = "\n".join(
        f"{i}: " + " ".join(p["palavra"] for p in g)
        for i, g in enumerate(grupos)
    )
    contexto = " ".join(p["palavra"] for g in grupos for p in g)

    rot = keys.gemini()
    for _ in range(len(rot) * 2):
        chave = rot.proxima()
        try:
            r = requests.post(
                f"{config.GEMINI_URL}/models/{config.GEMINI_MODELO}:generateContent?key={chave}",
                json={
                    "contents": [{"parts": [{"text": PROMPT.format(contexto=contexto, trechos=trechos)}]}],
                    "generationConfig": {"temperature": 0.4},
                },
                timeout=60,
            )
            if r.status_code in (429, 403):
                rot.queimar(chave)
                continue
            r.raise_for_status()
            saida = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            arr = json.loads(_extrair_json(saida))
            if not isinstance(arr, list) or len(arr) != len(grupos):
                raise ValueError(f"esperava lista de {len(grupos)}, veio {arr!r}")
            return [
                (int(idx) if 0 <= int(idx) < len(g) else None)
                for idx, g in zip(arr, grupos)
            ]
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (429, 403):
                rot.queimar(chave)
                continue
            print(f"   [!] destaque: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"   [!] destaque: {e}")
            time.sleep(1)

    print("   [!] destaque de palavra falhou em todas as chaves — legenda sem cor")
    return [None] * len(grupos)


PROMPT_TITULO = """Você edita títulos de abertura de vídeos virais de TikTok, no
estilo de uma caixa de texto que aparece nos primeiros segundos — ex:
"VIRALIZOU / Faça isso / IMEDIATAMENTE", onde 1-2 trechos curtos (uma ou
poucas palavras) ficam em CAIXA ALTA pra dar impacto, e o resto do título
mantém a formatação normal. É esse ritmo alternado que dá o efeito.

Reescreva o título abaixo mudando SÓ A CAIXA (maiúscula/minúscula) de
palavras pra criar esse efeito. NÃO mude nenhuma palavra, não adicione nem
remova nada, não mude pontuação nem acento. Normalmente 1-2 trechos curtos
ficam em caixa alta — não exagere, a maior parte do título deve continuar
como está.

Responda SOMENTE o título reescrito, sem aspas, sem comentário, sem markdown.

Título original:
{texto}"""


def _mesmas_palavras(a: str, b: str) -> bool:
    norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
    return norm(a) == norm(b)


def marcar_titulo(texto: str) -> str:
    """Devolve o título com trechos em CAIXA ALTA pra dar ritmo editorial.

    Se o Gemini falhar ou mudar alguma palavra (alucinação), devolve o
    título original sem tocar — melhor sem o efeito do que com o título
    errado."""
    texto = (texto or "").strip()
    if not texto:
        return texto

    rot = keys.gemini()
    for _ in range(len(rot) * 2):
        chave = rot.proxima()
        try:
            r = requests.post(
                f"{config.GEMINI_URL}/models/{config.GEMINI_MODELO}:generateContent?key={chave}",
                json={
                    "contents": [{"parts": [{"text": PROMPT_TITULO.format(texto=texto)}]}],
                    "generationConfig": {"temperature": 0.4},
                },
                timeout=60,
            )
            if r.status_code in (429, 403):
                rot.queimar(chave)
                continue
            r.raise_for_status()
            saida = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            if _mesmas_palavras(saida, texto):
                return saida
            print("   [!] destaque de título: Gemini mudou palavra, ignorando")
            return texto
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (429, 403):
                rot.queimar(chave)
                continue
            print(f"   [!] destaque de título: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"   [!] destaque de título: {e}")
            time.sleep(1)

    print("   [!] destaque de título falhou em todas as chaves — título sem caixa alta")
    return texto
