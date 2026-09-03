# -*- coding: utf-8 -*-
""""Espere ate' amanha" so' com a SERIE, nunca com uma foto.

⚠️ TRES ERROS MEUS NO MESMO DIA, todos com o mesmo formato: peguei UMA
medicao e dei veredito de dia inteiro.

    16:19  0/5 vivas        -> "cota seca"
    16:39  3/5 vivas            (20 min depois)

    00:03  0/5, cinco 429   -> "esgotada, SEM AMBIGUIDADE"
    00:23  4/5 vivas            (20 min depois)

    01:04  0/5, cinco 429   -> (o conserto ja' estava sendo escrito)
    01:24  3/5 vivas            (20 min depois)

⚠️ NEM O 429 PROVA DIA ESGOTADO: o Gemini devolve 429 pro limite por MINUTO e
pro limite por DIA. Como a sonda sorteia 5 de 15-27 chaves, cinco 429 podem
ser cinco chaves cansadas naquele instante.
"""
import json
import pathlib
import sys
import tempfile
from datetime import datetime, timedelta, timezone

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import sondar_cota as sc


def _serie(*vivas_por_idade_min):
    """Escreve um historico de mentira: (minutos_atras, vivas)."""
    tmp = pathlib.Path(tempfile.mkdtemp()) / "cota.jsonl"
    agora = datetime.now(timezone.utc)
    linhas = []
    for minutos, vivas in vivas_por_idade_min:
        q = (agora - timedelta(minutes=minutos)).isoformat(timespec="seconds")
        linhas.append(json.dumps({"quando": q, "vivas": vivas, "sondadas": 5,
                                  "placar": {"limite_nosso": 5} if not vivas
                                  else {"viva": vivas}}))
    tmp.write_text("\n".join(linhas), encoding="utf-8")
    return tmp


def _com(serie):
    antigo = sc.HISTORICO
    sc.HISTORICO = serie
    try:
        return sc.secou_de_verdade()
    finally:
        sc.HISTORICO = antigo


def teste_positivo_uma_hora_de_zero_e_seca_de_verdade():
    assert _com(_serie((55, 0), (35, 0), (15, 0), (2, 0))) is True


def teste_negativo_o_caso_das_00h03():
    """⚠️ O ERRO EXATO. Zero vivas agora, mas com vivas ha' pouco na serie."""
    assert _com(_serie((45, 4), (25, 2), (5, 0))) is False


def teste_negativo_uma_medicao_so_nao_prova():
    """Poucas medicoes na janela: o certo e' dizer que nao sabe, nao chutar
    pro lado caro."""
    assert _com(_serie((5, 0))) is False
    assert _com(_serie((20, 0), (5, 0))) is False


def teste_negativo_serie_velha_nao_conta():
    """Zero vivas de tres horas atras nao diz nada sobre agora."""
    assert _com(_serie((200, 0), (190, 0), (180, 0))) is False


def teste_negativo_sem_historico_nao_afirma_nada():
    tmp = pathlib.Path(tempfile.mkdtemp()) / "nao_existe.jsonl"
    assert _com(tmp) is False


def teste_o_veredito_usa_a_serie():
    """Com zero vivas e sem serie que sustente, o texto NAO pode mandar
    esperar o dia."""
    foto = {"vivas": 0, "sondadas": 5, "placar": {"limite_nosso": 5},
            "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    antigo = sc.HISTORICO
    sc.HISTORICO = _serie((45, 4), (25, 2))
    try:
        v = sc.veredito(foto)
    finally:
        sc.HISTORICO = antigo
    assert "por MINUTO" in v, v
    assert "agora sim e' o dia" not in v, f"mandou esperar sem base: {v}"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
