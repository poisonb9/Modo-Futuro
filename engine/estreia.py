# -*- coding: utf-8 -*-
"""Quais canais estao em ESTREIA — e por isso nao podem ser agendados.

O Bryan posta os primeiros videos de um canal novo na mao, porque uma estreia
automatica ja' flopou. Em 31/08/2026 ele fixou o prazo: "sao 2 dias de
estreia".

⚠️ ESTE MODULO EXISTE PORQUE EU CONSERTEI A INSTANCIA TRES VEZES NO MESMO
DIA. Em 31/08 os runs #191, #196, #202 e #216 enfileiraram sozinhos em canal
de estreia, e a cada vez eu apaguei o post e segui. Apagar depois nao e'
conserto: o run seguinte repoe. A recusa tem de estar na ORIGEM, no momento
de decidir o que entra na fila.

⚠️ E TEM PRAZO, nao e' interruptor eterno. Sem data, o canal ficaria travado
pra sempre e alguem teria de lembrar de destravar — que e' outra forma de
depender da memoria de uma pessoa. Passados os 2 dias, o canal volta sozinho.
"""
from __future__ import annotations

import datetime

# canal -> ultimo dia (inclusive) em que ele ainda esta' em estreia.
# O @atefalhar e o @truque.importado estrearam em 31/08/2026; o
# @semanestesia.pod tambem. Dois dias = 31/08 e 01/09.
ESTREIA_ATE: dict = {
    # ⚠️ VAZIO desde 01/09/2026: o Bryan liberou os tres canais novos. O
    # @atefalhar foi o ultimo, quando ele pediu "preencha todas as filas" — e
    # o prazo de 2 dias que ele mesmo fixou vencia nesse mesmo dia.
    #
    # A tabela FICA, e o mecanismo tambem: canal novo entra aqui com data, e
    # destrava sozinho. Apagar o modulo por estar vazio hoje obrigaria a
    # reconstrui-lo no proximo canal.
}


def em_estreia(canal: str, hoje: datetime.date | None = None) -> bool:
    """O canal ainda esta' no periodo em que o Bryan posta na mao?"""
    limite = ESTREIA_ATE.get((canal or "").strip().lower().lstrip("@"))
    if limite is None:
        return False
    return (hoje or datetime.date.today()) <= limite


def motivo(canal: str) -> str:
    limite = ESTREIA_ATE.get((canal or "").strip().lower().lstrip("@"))
    return (f"canal em ESTREIA ate' {limite:%d/%m} — o Bryan posta na mao"
            if limite else "")
