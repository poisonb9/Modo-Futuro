# -*- coding: utf-8 -*-
"""O prompt manda MOSTRAR a coisa, e nao ensinar a fazer.

⚠️ MEDIDO em 08/09/2026, na autopsia dos 75 melhores posts das 5 contas, com
view REAL do TikTok Studio (nao a do Buffer, que marca zero).

    titulo que ENSINA   1,07x a mediana do canal   (n=31)
    titulo que MOSTRA   1,48x                      (n=44)   +37%

E o engajamento foi junto: 3,53% de curtida por view contra 2,62%. Duas
medidas independentes apontando pro mesmo lado — e' isso que separa "padrao"
de "coincidencia de distribuicao".

Repetiu em QUATRO dos cinco canais, com assuntos sem relacao entre si.

## POR QUE ESTE TESTE EXISTE

A calibragem inteira e' UMA LINHA de prompt. Linha de prompt e' a coisa mais
facil de alguem reescrever "melhorando o texto" — e o efeito so' apareceria
um mes depois, no export, sem ninguem ligar uma coisa na outra.

⚠️ Este teste NAO prova que a regra funciona. Ele prova que a regra continua
escrita. A prova de que funciona e' o export do mes que vem.
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SELECAO = (RAIZ / "engine" / "selecao.py").read_text(encoding="utf-8")


def _bloco_do_titulo() -> str:
    i = SELECAO.index('"titulo": "<pt-BR')
    return SELECAO[max(0, i - 2600):i + 500]


def teste_o_prompt_manda_MOSTRAR():
    bloco = _bloco_do_titulo()
    assert "MOSTRE a coisa" in bloco or "MOSTRE" in bloco


def teste_o_prompt_desaconselha_o_titulo_AULA():
    """As tres aberturas que a medicao reprovou tem de estar citadas."""
    bloco = _bloco_do_titulo()
    for termo in ("Como", "Por que", "O segredo"):
        assert termo in bloco, f"o prompt nao menciona {termo!r}"


def teste_a_medicao_fica_junto_da_regra():
    """⚠️ Regra sem o numero que a gerou vira gosto pessoal — e a proxima
    pessoa a reescreve sem custo, porque nao ha' nada a contradizer."""
    bloco = _bloco_do_titulo()
    assert "1,48x" in bloco and "1,07x" in bloco, "sumiu a medicao de views"
    assert "3,53%" in bloco and "2,62%" in bloco, "sumiu a medicao de engajamento"


def teste_a_ressalva_de_amostra_fica_junto():
    """75 posts nao e' muito. Guardar a ressalva evita que a proxima sessao
    trate a magnitude como se fosse precisa."""
    bloco = _bloco_do_titulo()
    assert "75 posts" in bloco
    assert "RESSALVA" in bloco or "nao e' precisa" in bloco


def teste_NEGATIVO_a_regra_nao_proibe_a_palavra_como():
    """⚠️ O caso que impede a regra de virar burrice.

    "Como 1 poeira pode destruir 1 milhao de dolares" foi o SEGUNDO maior
    post de toda a operacao (1009 views). Se a regra virasse "proibido
    comecar com Como", ela mataria o proprio material que a originou.
    """
    bloco = _bloco_do_titulo()
    assert "NAO E' PROIBIDO" in bloco or "nao e' a palavra" in bloco
    assert "poeira" in bloco, "sumiu o contraexemplo que limita a regra"


def teste_o_numero_no_titulo_esta_pedido():
    bloco = _bloco_do_titulo()
    assert "+27%" in bloco and "numero" in bloco.lower()
    # e pedido SEM inventar
    assert "nao invente" in bloco.lower()


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
