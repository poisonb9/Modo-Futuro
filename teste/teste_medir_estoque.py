# -*- coding: utf-8 -*-
"""O leitor de estoque nao pode inventar zero.

⚠️ CASO NEGATIVO OBRIGATORIO. O defeito que este script existe pra impedir foi
exatamente um ZERO que ninguem contou: em 04/09/2026 o "0 ainda nao agendado"
do repor_fila virou "a fabrica esta' seca", e o canal tinha 27 clipes prontos.
Se o parser devolvesse 0 quando nao acha a linha, ele reproduziria o mesmo
erro numa ferramenta feita pra evita-lo.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import medir_estoque as me

SAIDA_BOA = """canal confirmado: modofuturo
fila: 6/10 agendados, 0 reservada(s) -> 4 vaga(s) pra encher
161 clipe(s) no manifesto, 17 ainda não agendado(s)
"""

# Sem acento: o runner pode reencodar a saida do subprocesso.
SAIDA_SEM_ACENTO = "161 clipe(s) no manifesto, 17 ainda nao agendado(s)"

# O agendador para' ANTES de contar quando a fila esta' cheia — e' o caso que
# nao tem a linha de estoque nenhuma.
SAIDA_FILA_CHEIA = """canal confirmado: modofuturo
fila: 10/10 agendados, 0 reservada(s) -> 0 vaga(s) pra encher
nada a fazer: fila cheia.
"""


def teste_le_os_numeros():
    e = me.LINHA_ESTOQUE.search(SAIDA_BOA)
    assert e and (int(e.group(1)), int(e.group(2))) == (161, 17)
    f = me.LINHA_FILA.search(SAIDA_BOA)
    assert f and (int(f.group(1)), int(f.group(3))) == (6, 4)


def teste_le_sem_acento():
    e = me.LINHA_ESTOQUE.search(SAIDA_SEM_ACENTO)
    assert e and int(e.group(2)) == 17


def teste_fila_cheia_nao_vira_zero():
    """⚠️ O CASO NEGATIVO. Sem linha de estoque, o campo e' None, nunca 0."""
    assert me.LINHA_ESTOQUE.search(SAIDA_FILA_CHEIA) is None
    f = me.LINHA_FILA.search(SAIDA_FILA_CHEIA)
    assert f and int(f.group(1)) == 10


def teste_formatar_mostra_o_erro_em_vez_de_numero():
    txt = me.formatar([{"canal": "truque.importado",
                        "erro": "sem BUFFER_TOKEN_TRUQUEIMPORTADO"}])
    assert "sem BUFFER_TOKEN_TRUQUEIMPORTADO" in txt
    assert " 0 " not in txt


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
