# -*- coding: utf-8 -*-
"""Mesmo trecho, outro titulo: a duplicata que a dedup por texto nao ve.

⚠️ MEDIDO. O par que sobreviveu no @cozinha.internacional ate' 08/09/2026:

    "Ramen de Carne com Legumes em Uma So Panela"        inicio 613,1s
    "Lamen de Carne Moida com Legumes em Uma Panela So"  inicio 613,1s

Mesmo bruto, mesmo trecho, cortado em dois dias. O Gemini escolheu o MESMO
momento (era o melhor) e traduziu diferente. Nenhuma guarda pegou:

  - o hash muda, porque o render e' novo;
  - a dedup por texto compara PREFIXO, e "ramen" e "lamen" diferem na
    PRIMEIRA letra;
  - e a guarda de trecho que ja' existia chegava no par PELO texto, entao
    herdava a mesma cegueira.

Este arquivo prova a rede que nao depende de texto nenhum.
"""
import json
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import trechos

# ⚠️ Nunca no arquivo de producao — foi assim que a suite apagou o freio em
# 07/09. Teste que escreve em estado real e' um comando disfarcado.
trechos.ARQUIVO = pathlib.Path(tempfile.mkdtemp()) / "trechos_usados.json"

FONTE = "1abcDEFghi_fonte_do_ramen"
INICIO = 613.1


def _limpo():
    if trechos.ARQUIVO.exists():
        trechos.ARQUIVO.unlink()


def teste_positivo_mesmo_trecho_com_outro_titulo_e_pego():
    _limpo()
    assert trechos.anotar(FONTE, INICIO,
                          titulo="Ramen de Carne com Legumes em Uma So Panela")
    # O segundo corte: outro titulo, outra traducao, mesmo segundo.
    assert trechos.ja_usado(FONTE, 613.1)
    assert trechos.ja_usado(FONTE, 613.14), "a fracao mudou e ele escapou"


def teste_negativo_outro_trecho_da_MESMA_fonte_passa():
    """⚠️ ESTE e' o teste que impede a guarda de virar um bloqueio de fonte.

    Um bruto rende varios clipes de propósito. Se a marca fosse so' o
    `fonte_id`, o segundo clipe de todo video seria recusado — e a guarda
    seria desligada por atrapalhar, que e' o pior desfecho possivel.
    """
    _limpo()
    trechos.anotar(FONTE, 613.1, titulo="Ramen")
    assert not trechos.ja_usado(FONTE, 90.0)
    assert not trechos.ja_usado(FONTE, 1210.5)


def teste_negativo_outra_fonte_no_mesmo_segundo_passa():
    """Dois videos diferentes podem ter um bom trecho no mesmo minuto."""
    _limpo()
    trechos.anotar(FONTE, 613.1, titulo="Ramen")
    assert not trechos.ja_usado("outra_fonte_qualquer", 613.1)


def teste_negativo_clipe_SEM_fonte_id_nao_e_recusado():
    """⚠️ Ausencia de dado nao pode virar recusa.

    O campo `fonte_id` nasceu em 02/09/2026 e o manifesto da cozinha nao o
    tem. Recusar por ausencia travaria tudo que foi cortado antes — e
    inventar uma chave a partir do que falta juntaria clipes sem relacao,
    fazendo a guarda recusar material bom.
    """
    _limpo()
    assert trechos.marca(None, 613.1) is None
    assert trechos.marca(FONTE, None) is None
    assert not trechos.ja_usado(None, 613.1)
    assert not trechos.ja_usado(FONTE, None)
    assert trechos.anotar(None, 613.1) is False


def teste_a_primeira_anotacao_e_a_que_vale():
    """O titulo guardado tem de ser o que REALMENTE foi ao ar.

    Sobrescrever com o titulo da tentativa repetida apagaria a evidencia
    justamente no caso que interessa.
    """
    _limpo()
    trechos.anotar(FONTE, INICIO, titulo="Ramen de Carne")
    assert trechos.anotar(FONTE, INICIO, titulo="Lamen de Carne Moida") is False
    d = json.loads(trechos.ARQUIVO.read_text(encoding="utf-8"))
    assert "Ramen" in d[trechos.marca(FONTE, INICIO)]["titulo"]


def teste_o_agendador_usa_o_registro_duravel():
    """A guarda so' serve se estiver somada ao conjunto que o agendador usa."""
    ab = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")
    assert "trechos.marcas()" in ab, "o agendador nao le' o registro duravel"
    assert "trechos.anotar(" in ab, "o agendador nao anota o que enfileira"
    # E anota SO' quando enfileira de verdade.
    i = ab.index("trechos.anotar(")
    assert "not a.simular" in ab[i - 200:i]


def teste_o_registro_sobrevive_ao_runner():
    """Sem estar no git, o arquivo morre com o runner — foi o que aconteceu
    com o `publicados.json`, que ficou 10 dias fora e deixou passar a
    duplicata do ASML em 08/09."""
    gi = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert "!estado/trechos_usados.json" in gi


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
