# -*- coding: utf-8 -*-
"""Este motor cede a vez pra cozinha — mas nunca a ponto de secar sozinho.

⚠️ Ordem do Bryan em 07/09/2026: "quando chegar video da cozinha ele e' o
primeiro a disparar". Os dois motores disputam a COTA DO GEMINI: em 07/09 os
dois esgotaram na mesma janela e a cota do dia durou 8 horas.

⚠️ O TESTE QUE MAIS IMPORTA AQUI E' O DO TETO.

Ceder e' facil de escrever e facil de acertar. O que quebra o projeto e' a
cessao que nao termina: bruto da cozinha **fica na RAW deste motor pra
sempre** (ele nunca o despacha, entao nunca o marca como visto). A French
Onion Soup e o Tiramisu entraram em 06/09 e continuavam sendo recusados em
07/09 15:01. Sem teto, "cede enquanto houver bruto da cozinha" seria "cede
pra sempre", e os quatro canais deste motor secariam em ~44h.

Nenhum teste aqui vai a' rede: `_cozinha_ja_cortou` e' trocado a mao.
"""
import json
import pathlib
import sys
import tempfile
from datetime import datetime, timedelta, timezone

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import prioridade

IDS = ["bruto-da-cozinha-1"]

# (id, chegada) — chegada None quer dizer "o Drive nao disse", e ai' vale a
# hora da passada. Ver prioridade.marcar.
NOVOS = [(IDS[0], None)]


def _chegou_ha(horas):
    """Um bruto que o DRIVE diz ter chegado ha' N horas."""
    q = (datetime.now(timezone.utc) - timedelta(hours=horas))
    return [(IDS[0], q.isoformat().replace("+00:00", "Z"))]


def _isolar():
    """Estado num arquivo temporario: teste nao escreve no estado real."""
    tmp = pathlib.Path(tempfile.mkdtemp()) / "cozinha_esperando.json"
    prioridade.VISTOS = tmp
    return tmp


def _envelhecer(tmp, horas):
    """Faz o bruto ter chegado ha' N horas, sem esperar N horas."""
    quando = (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat()
    tmp.write_text(json.dumps({i: quando for i in IDS}), encoding="utf-8")


def teste_positivo_cede_quando_ha_bruto_da_cozinha_esperando():
    _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: False
    cede, motivo = prioridade.ceder(NOVOS)
    assert cede is True
    assert "CEDENDO A VEZ" in motivo


def teste_negativo_sem_bruto_da_cozinha_nao_cede():
    _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: False
    cede, motivo = prioridade.ceder([])
    assert cede is False
    assert motivo == ""


def teste_TETO_o_motor_volta_a_cortar_e_nao_seca():
    """⚠️ O teste que sustenta o resto. Sem ele, a cessao e' eterna.

    O canal mais apertado deste motor tinha +44h de folga; o teto de 6h e'
    13% disso. Se um dia a cessao for o motivo de um canal secar, o errado e'
    o teto, nao a folga.
    """
    tmp = _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: False   # ela NUNCA cortou
    _envelhecer(tmp, prioridade.TETO_HORAS + 0.5)
    cede, motivo = prioridade.ceder(NOVOS)
    assert cede is False, "passou do teto e ainda cedeu — o motor secaria"
    assert "teto" in motivo
    # E o motivo tem de dizer onde procurar, nao so' que desistiu.
    assert "cota" in motivo


def teste_dentro_do_teto_ainda_cede():
    """A borda do teto pelo lado de dentro — senao o teste acima passaria
    com um `ceder` que devolve False sempre."""
    tmp = _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: False
    _envelhecer(tmp, prioridade.TETO_HORAS - 0.5)
    cede, _ = prioridade.ceder(NOVOS)
    assert cede is True


def teste_para_de_ceder_quando_a_cozinha_ja_cortou():
    tmp = _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: True
    _envelhecer(tmp, 1)
    cede, motivo = prioridade.ceder(NOVOS)
    assert cede is False
    assert "ja' cortou" in motivo


def teste_duvida_cede_mas_o_motivo_diz_que_e_duvida():
    """Nao conseguir ler os runs da cozinha CEDE, dentro do teto — mas o log
    tem de deixar claro que foi por duvida, e nao por medicao."""
    _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: None
    cede, motivo = prioridade.ceder(NOVOS)
    assert cede is True
    assert "duvida" in motivo


def teste_o_relogio_nao_se_renova_a_cada_passada():
    """⚠️ Se cada passada reiniciasse o prazo, o teto nunca venceria — e a
    cessao voltaria a ser eterna pela porta dos fundos."""
    tmp = _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: False
    _envelhecer(tmp, 3)
    antes = json.loads(tmp.read_text(encoding="utf-8"))[IDS[0]]
    prioridade.ceder(NOVOS)
    prioridade.ceder(NOVOS)
    depois = json.loads(tmp.read_text(encoding="utf-8"))[IDS[0]]
    assert antes == depois, "o prazo foi renovado; o teto nunca venceria"


def teste_bruto_que_saiu_da_raw_para_de_contar():
    tmp = _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: False
    prioridade.ceder(NOVOS)
    prioridade.ceder([])
    assert json.loads(tmp.read_text(encoding="utf-8")) == {}


def teste_bruto_VELHO_do_drive_nao_faz_o_motor_ceder():
    """⚠️ MEDIDO num ensaio real em 07/09, e foi o ensaio que achou.

    A French Onion Soup e o Tiramisu estavam na RAW desde 06/09, travados por
    COTA e nao por vez. Com o relogio na DESCOBERTA, eles zeravam o prazo no
    instante em que a guarda nasceu, e o motor cederia 6h por brutos de
    ontem — cedendo a vez pra quem nao estava esperando a vez.

    O Bryan pediu "quando CHEGAR video da cozinha". Chegada, nao descoberta.
    """
    _isolar()
    prioridade._cozinha_ja_cortou = lambda desde: False
    cede, motivo = prioridade.ceder(_chegou_ha(prioridade.TETO_HORAS + 2))
    assert cede is False, "cedeu por um bruto que chegou ontem"
    assert "teto" in motivo


def teste_a_guarda_esta_LIGADA_no_vigia():
    vigia = (RAIZ / "vigia_raw.py").read_text(encoding="utf-8")
    assert "prioridade.ceder" in vigia
    # E tem de ceder ANTES de despachar, nao depois.
    i_cede = vigia.index("prioridade.ceder")
    i_disparo = vigia.index("disparar(v[\"id\"]")
    assert i_cede < i_disparo, "cede depois de ja' ter disparado"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
