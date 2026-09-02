# -*- coding: utf-8 -*-
"""Resposta ruim do MODELO nao pode gastar a tentativa da FONTE.

O teto de 3 tentativas existe pra fonte quebrada (bruto corrompido, id que
sumiu do Drive) — essas nao melhoram tentando de novo. Resposta imprestavel do
Gemini melhora: e' amostragem. Contar as duas no mesmo contador expulsa fonte
boa, que e' o defeito que a cota ja' tinha causado em 01/09/2026.

⚠️ Este teste NAO chama a API. Ele confere o CODIGO — que as duas contagens
existem, sao separadas, e que o perdao ao modelo e' finito.
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

FONTE = (RAIZ / "cortar_fila.py").read_text(encoding="utf-8")

import cortar_fila as cf


def teste_positivo_detector_reconhece_as_duas_marcas():
    """As duas linhas que o pipeline imprime quando nada passa."""
    corpo = FONTE[FONTE.index("def falhou_por_selecao_vazia"):]
    corpo = corpo[:corpo.index("\ndef ", 1)]
    assert "nenhum momento aprovado" in corpo, "falta a marca do main.py"
    assert "e NENHUM passou" in corpo, "falta a marca do validador"


def teste_negativo_uma_marca_so_nao_basta():
    """⚠️ TEOREMATICO, e a razao de este teste existir.

    Detector de UMA frase ja' me pegou tres vezes neste pipeline. A linha do
    `main.py` pode mudar de texto sem que a do validador mude. Se um dia
    sobrar so' uma marca, este teste reprova antes de a fonte boa ser expulsa.
    """
    corpo = FONTE[FONTE.index("def falhou_por_selecao_vazia"):]
    corpo = corpo[:corpo.index("\ndef ", 1)]
    marcas = re.findall(r'"([^"]{8,})"', corpo.split("MARCAS = ")[1])
    assert len(marcas) >= 2, f"detector com uma marca so': {marcas}"


def teste_contadores_sao_separados():
    """`tentativas` e `tentativas_modelo` nao podem ser o mesmo campo."""
    assert "tentativas_modelo" in FONTE
    bloco = FONTE[FONTE.index("if falhou_por_selecao_vazia(item"):]
    bloco = bloco[:bloco.index("item[\"tentativas\"] =")]
    assert 'item["tentativas"] =' not in bloco, \
        "o ramo do modelo esta' mexendo no contador da FONTE"


def teste_negativo_o_perdao_ao_modelo_e_FINITO():
    """⚠️ O caso negativo mais importante.

    Se `falhou_por_selecao_vazia` sempre devolvesse True e nao houvesse teto,
    a fonte giraria pra sempre queimando runner a cada rodada. O perdao tem de
    acabar — maior que o das falhas comuns, mas finito.
    """
    assert isinstance(cf.TETO_TENTATIVAS_MODELO, int)
    assert cf.TETO_TENTATIVAS_MODELO > 3, "tem de ser mais generoso que o teto comum"
    assert cf.TETO_TENTATIVAS_MODELO <= 10, "perdao praticamente infinito queima runner"
    # e o teto tem de DESISTIR de verdade quando estourar, nao so' avisar
    ramo = FONTE[FONTE.index("if n >= TETO_TENTATIVAS_MODELO:"):][:300]
    assert 'item["estado"] = "desistido"' in ramo, \
        "estourar o teto do modelo nao esta' tirando o item da fila"


def teste_negativo_cota_continua_com_prioridade():
    """Cota tem de ser checada ANTES da selecao vazia: um run que morreu por
    cota nem chegou a pedir momento ao modelo, e nao pode gastar nem uma
    tentativa, nem a do modelo."""
    i_cota = FONTE.index("cota = falhou_por_cota(item")
    i_modelo = FONTE.index("if falhou_por_selecao_vazia(item")
    assert i_cota < i_modelo, "a cota tem de ser avaliada primeiro"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
