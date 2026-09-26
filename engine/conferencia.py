# -*- coding: utf-8 -*-
"""CONFERENCIA da dublagem: a voz falou o que devia?

## POR QUE EXISTE

Item 3 da dublagem (26/09/2026, dono: "vamos fazer isso!! Maravilha"). O
Chatterbox as vezes engole palavra, repete trecho ou erra nome — e nada no
motor ouvia o resultado. O Orca Dub chama isto de "verificacao de qualidade"
(acervo F128405).

Cada frase gerada e' transcrita (Whisper via Groq, o mesmo do corte, ~1 s) e
comparada com o texto que devia ser dito. Nota de 0 a 1 por palavras. Abaixo
de `LIMIAR`, `voz_clonada` refaz a frase (o modelo varia a cada geracao) e
fica com a melhor das tentativas.

⚠️ Compara com DUAS formas do esperado e fica com a melhor: a grafia
("400 milhoes", "Risabae") e a forma falada ("quatrocentos milhoes",
"Rissabe") — o Whisper escreve de um jeito ou de outro, e reprovar por isso
seria refazer frase boa.

FALHA ABERTA: Groq fora, sem chave, erro qualquer -> None, e a frase segue.
"""
from __future__ import annotations

import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

LIGADO = os.environ.get("QC_DUBLAGEM", "1") != "0"
LIMIAR = 0.75          # abaixo disto a frase e' refeita
TENTATIVAS = 2         # 1a geracao + 1 refacao
MAX_REFEITAS_POR_CLIPE = 4


def _palavras(texto: str) -> list[str]:
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", t)


def nota_texto(esperado: str, ouvido: str) -> float:
    """Semelhanca por PALAVRAS, 0 a 1, sem acento, pontuacao ou maiuscula."""
    a, b = _palavras(esperado), _palavras(ouvido)
    if not a:
        return 1.0
    if not b:
        return 0.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def formas_faladas(texto: str) -> list[str]:
    """A grafia e o que a voz de fato recebeu (numero por extenso + Biblia)."""
    from . import biblia, numeros
    falado = biblia.para_fala(numeros.por_extenso(texto))
    return [texto] if falado == texto else [texto, falado]


def ouvir(wav: Path, idioma: str = "pt") -> str | None:
    """Transcricao da frase gerada, ou None se nao der."""
    try:
        from . import transcricao
        ps = transcricao.palavras(Path(wav), idioma)
        return " ".join(p.get("palavra", "") for p in ps).strip()
    except Exception as e:
        print(f"        [qc] sem transcricao ({type(e).__name__}) — frase segue", flush=True)
        return None


def nota(wav: Path, texto: str, idioma: str = "pt") -> tuple[float, str] | None:
    """(nota, o que se ouviu) ou None (falha aberta)."""
    ouvido = ouvir(wav, idioma)
    if ouvido is None:
        return None
    return max(nota_texto(f, ouvido) for f in formas_faladas(texto)), ouvido


def resumo(notas: list[float | None], refeitas: int) -> dict:
    """O que vai pro post.json (`qc_dublagem`) pra cruzar com a retencao."""
    validas = [n for n in notas if n is not None]
    if not validas:
        return {"conferidas": 0}
    return {"conferidas": len(validas), "min": round(min(validas), 3),
            "media": round(sum(validas) / len(validas), 3), "refeitas": refeitas,
            "abaixo_do_limiar": sum(n < LIMIAR for n in validas)}
