# -*- coding: utf-8 -*-
"""Que TRECHO de que FONTE ja' foi enfileirado — independente do texto.

⚠️ POR QUE ISTO EXISTE, e por que a guarda que ja' havia nao bastava.

O `agendar_buffer` ja' recusa repetir o mesmo trecho: "mesma fonte + mesmo
segundo = mesmo clipe, por mais que titulo, traducao e hash mudem". A regra
esta' certa. O problema e' COMO ela descobre o que ja' saiu:

    trechos_vistos = {(fonte, inicio) para os clipes do manifesto
                      cujo TEXTO a dedup reconheceu como publicado}

Ou seja: ela chega no trecho PELO TEXTO. E o caso que ela existe pra pegar e'
justamente aquele em que o texto MUDA:

    "Ramen de Carne com Legumes em Uma So Panela"        inicio 613,1s
    "Lamen de Carne Moida com Legumes em Uma Panela So"  inicio 613,1s

Se o primeiro foi publicado com um titulo e a dedup por texto nao o
reconhece, o par (fonte, 613.1) nunca entra no conjunto — e o segundo passa.
O Bryan viu esse par vivo no @cozinha.internacional em 08/09/2026.

⚠️ E TEM UM SEGUNDO BURACO, MAIOR: clipe sem `fonte_id` nunca entra. O campo
nasceu em 02/09/2026, e o manifesto da cozinha nao o tem — la' a guarda e'
letra morta, que e' exatamente onde o par sobreviveu.

## A CORRECAO: ANOTAR NA HORA DE ENFILEIRAR, NAO DEDUZIR DEPOIS

Quem enfileira SABE qual trecho esta' mandando. Anotar ali custa uma linha e
nao depende de reconhecer texto nenhum depois. O arquivo e' a memoria que
sobrevive ao runner — por isso vai pro git, como o `publicados.json` (que
ficou 10 dias fora e deixou passar a duplicata do ASML).

⚠️ ISTO NAO SUBSTITUI A DEDUP POR TEXTO. Sao redes diferentes: a de texto
pega o mesmo clipe re-renderizado de outra fonte; esta pega o mesmo trecho
com outro nome. Nenhuma das duas cobre a outra.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "estado" / "trechos_usados.json"

# Tolerancia do segundo. O `inicio_s` vem do Gemini e reaparece com fracao
# ligeiramente diferente entre dois cortes do mesmo bruto — 613.1 e 613.14
# sao o mesmo trecho. Uma casa decimal e' o que o proprio agendar_buffer ja'
# usava (`round(float(i), 1)`), mantido pra as duas guardas concordarem.
CASAS = 1


def _carregar() -> dict:
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def marca(fonte_id: str | None, inicio_s) -> str | None:
    """A chave de um trecho, ou None quando nao da' pra formar uma.

    ⚠️ AUSENCIA NAO VIRA CHAVE. Clipe sem `fonte_id` devolve None, e quem
    chama trata isso como "nao sei" — nunca como "trecho novo" nem como
    "trecho repetido". Inventar uma chave a partir do que falta juntaria
    clipes que nao tem nada a ver, e ai' a guarda passaria a RECUSAR material
    bom, que e' o jeito de fazer alguem desligar a guarda.
    """
    if not fonte_id or inicio_s is None:
        return None
    try:
        return f"{fonte_id}@{round(float(inicio_s), CASAS)}"
    except (TypeError, ValueError):
        return None


def ja_usado(fonte_id: str | None, inicio_s) -> bool:
    m = marca(fonte_id, inicio_s)
    return bool(m) and m in _carregar()


def anotar(fonte_id: str | None, inicio_s, titulo: str = "",
           canal: str = "") -> bool:
    """Registra que este trecho foi enfileirado. Devolve se anotou.

    ⚠️ NAO SOBRESCREVE. A primeira anotacao e' a que vale: ela guarda o
    titulo com que o trecho REALMENTE foi ao ar. Sobrescrever com o titulo da
    tentativa repetida apagaria a evidencia justamente no caso que interessa.
    """
    m = marca(fonte_id, inicio_s)
    if not m:
        return False
    d = _carregar()
    if m in d:
        return False
    d[m] = {"titulo": (titulo or "")[:90], "canal": canal,
            "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(json.dumps(d, ensure_ascii=False, indent=1,
                                  sort_keys=True), encoding="utf-8")
    return True


def marcas() -> set:
    """Todas as marcas conhecidas, pro agendador somar as duas redes."""
    return set(_carregar())
