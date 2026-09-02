# -*- coding: utf-8 -*-
"""O veredito da sonda de cota tem de mandar a coisa CERTA.

⚠️ "Esperar ate' amanha" e' o conselho mais caro que este script pode dar:
joga fora meio dia de producao. A primeira versao dava esse conselho sempre
que aparecia UM 429, mesmo com tres chaves em 200 — e o 429 daquela medicao
tinha sido causado pela propria sonda, martelando duas vezes seguidas.

429 e' uma chave cansada. Nao e' o rodizio inteiro.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import sondar_cota as sc


def _foto(**placar):
    return {"placar": placar, "vivas": placar.get("viva", 0),
            "sondadas": sum(placar.values()), "no_rodizio": 15}


def teste_o_caso_que_estava_errado():
    """3 vivas + 1 em 429 -> tem de mandar CORTAR, nao esperar."""
    v = sc.veredito(_foto(viva=3, limite_nosso=1, sobrecarga_deles=1))
    assert "CORTAR" in v, v
    assert "reset" not in v.lower(), f"mandou esperar com 3 vivas: {v}"


def teste_positivo_limite_real_manda_esperar():
    """Sem nenhuma viva e com 429, ai' sim o reset e' a unica saida."""
    v = sc.veredito(_foto(limite_nosso=4, muda=1))
    assert "LIMITE NOSSO" in v and "reset" in v.lower(), v


def teste_negativo_sobrecarga_NAO_manda_esperar_o_reset():
    """⚠️ A distincao que custou meio dia de conclusao errada.

    503 e timeout sao do lado do Google. Mandar esperar o reset diario por
    causa deles jogaria fora horas de producao por um problema que costuma
    passar em minutos.
    """
    v = sc.veredito(_foto(sobrecarga_deles=3, muda=2))
    # ⚠️ Proibir a PALAVRA "reset" reprovava a mensagem certa, que diz
    # justamente "nao esperar o reset". O que nao pode e' ACONSELHAR a espera.
    assert "GOOGLE" in v, v
    assert "so' o reset" not in v.lower(), f"confundiu sobrecarga com cota: {v}"
    assert "nao esperar o reset" in v.lower(), v


def teste_negativo_uma_viva_avisa_que_nao_sustenta():
    """1 chave viva libera teto 1 na nuvem, mas um corte leva ~2h e faz
    dezenas de chamadas. Foi assim que o run de 142 min morreu."""
    v = sc.veredito(_foto(viva=1, muda=4))
    assert "TENTAR" in v.upper(), v
    assert "142" in v or "sustenta" in v, v


def teste_negativo_chave_invalida_nao_e_falta_de_cota():
    """403 nao melhora com o tempo — nao pode virar conselho de esperar."""
    v = sc.veredito(_foto(viva=3, invalida=1))
    assert "CORTAR" in v, v


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
