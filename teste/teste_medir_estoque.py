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


def teste_fila_cheia_NAO_e_erro():
    """⚠️ "NAO PRECISOU" nao pode ser reportado como "NAO CONSEGUI".

    Medido em 09/09/2026: o Bryan perguntou se todos os canais estavam com
    cota e a ferramenta respondeu "[!] nao achei a linha de estoque na saida"
    para o @atefalhar e o @truque.importado. Parecia defeito nos dois. Era o
    MELHOR estado possivel: fila cheia, e o agendador retorna antes de contar
    o manifesto.

    E' o mesmo defeito que o wrapper do vigia ja' tinha registrado: as duas
    frases sao iguais pra quem le' rapido e significam coisas opostas — uma e'
    o sistema saudavel, a outra e' o sistema cego.
    """
    linha = {"canal": "atefalhar", "manifesto": None, "prontos": None,
             "agendados": 10, "limite": 10, "vagas": 0, "cheia": True,
             "erro": None}
    # ⚠️ olha a LINHA DO CANAL, nao o texto inteiro: o rodape explica o que
    # "fila CHEIA" quer dizer, e procurar no texto todo acharia a legenda.
    linha_do_canal = [l for l in me.formatar([linha]).splitlines()
                      if l.strip().startswith("atefalhar")][0]
    assert "fila CHEIA" in linha_do_canal, "estado saudavel aparece como estado"
    assert "[!]" not in linha_do_canal, "fila cheia nao sai marcada como erro"
    assert "10/10" in linha_do_canal, "e diz quantos, senao e' palavra sem numero"


def teste_NEGATIVO_saida_ilegivel_CONTINUA_sendo_erro():
    """⚠️ A metade que impede o conserto de virar cegueira.

    Se qualquer saida sem a linha de estoque passasse a ser "fila cheia", um
    agendador que estourasse no meio seria reportado como saudavel — e' o
    contrario do que este arquivo inteiro existe pra evitar.
    """
    linha = {"canal": "modofuturo", "manifesto": None, "prontos": None,
             "agendados": None, "limite": None, "vagas": None, "cheia": False,
             "erro": "nao achei a linha de estoque na saida"}
    linha_do_canal = [l for l in me.formatar([linha]).splitlines()
                      if l.strip().startswith("modofuturo")][0]
    assert "[!]" in linha_do_canal
    assert "fila CHEIA" not in linha_do_canal


def teste_a_marca_de_cheia_vem_da_saida_do_agendador():
    """A deteccao le' a frase que o agendador imprime, nao adivinha."""
    assert "fila cheia" in SAIDA_FILA_CHEIA
    assert "fila cheia" not in SAIDA_BOA


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
