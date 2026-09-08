# -*- coding: utf-8 -*-
"""O ciclo so' repoe fonte quando falta, e nunca foge do tema do canal.

⚠️ Ordem do Bryan em 08/09/2026: quando um canal comecar a ficar sem video
pra cortar, rodar radar em cima dos 2 que mais viralizaram na semana, baixar
5 fontes novas, e repetir por 1 mes. E, no mesmo dia: "nunca fuja do tema
principal do canal".

O QUE PRECISA SER PROVADO AQUI

O caso positivo (canal vazio dispara) e' trivial. O que quebra o canal e' o
contrario:

  - disparar com estoque cheio, e gastar cota e runner a toa;
  - deixar um titulo campeao de OUTRO assunto arrastar o radar pra fora do
    tema — e ai' o canal muda de assunto sozinho, que e' pior que ficar sem
    post;
  - baixar no escuro quando nao ha' metrica nenhuma.
"""
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import ciclo_semanal as cs
from engine import melhores


class RadarFalso:
    TEMA = ["glute", "gluteo", "treino", "workout", "disciplina"]


def teste_negativo_estoque_cheio_nao_dispara():
    """⚠️ O teste que evita queimar cota. Canal com fonte sobrando nao pede
    mais fonte."""
    cs.FILA = RAIZ / "fila_cortes.json"
    est = cs.estoque("semanestesia.pod")
    assert est["total"] > cs.PISO_FONTES, "dados de teste mudaram"
    linha = cs.rodar("semanestesia.pod", simular=True)
    assert linha["acao"] == "nada"


def teste_desistido_e_sem_fonte_NAO_contam_como_estoque():
    """Sao o oposto de estoque: item que ja' desistiu nao vira post nenhum."""
    import json
    tmp = pathlib.Path(tempfile.mkdtemp()) / "fila.json"
    tmp.write_text(json.dumps({"itens": [
        {"canal": "x", "estado": "desistido"},
        {"canal": "x", "estado": "sem_fonte"},
        {"canal": "x", "estado": "pronto"},
    ]}), encoding="utf-8")
    cs.FILA = tmp
    assert cs.estoque("x")["total"] == 1
    cs.FILA = RAIZ / "fila_cortes.json"


def teste_TEMA_trava_o_termo_que_foge_do_assunto():
    """⚠️ A trava editorial. Um campeao fora do tema nao arrasta o canal."""
    top = [{"titulo": "Os 3 melhores exercicios para crescer os gluteos"},
           {"titulo": "Como investir em criptomoeda e ficar rico"}]
    termos, _ = cs.termos_do_sucesso("atefalhar", top, RadarFalso())
    assert "gluteo" in termos or "glute" in termos
    assert not any("cripto" in t or "investir" in t for t in termos), \
        "termo fora do tema passou"


def teste_sem_termo_no_tema_NAO_inventa():
    """Zero termo e' resposta valida: usa as buscas fixas do radar.

    Inventar termo a partir de um campeao fora do tema seria trocar "sem
    viés" por "viés errado" — e o canal muda de assunto sozinho.
    """
    top = [{"titulo": "Como investir em criptomoeda"}]
    termos, por_que = cs.termos_do_sucesso("atefalhar", top, RadarFalso())
    assert termos == []
    assert "sem enviesar" in por_que


def teste_radar_sem_TEMA_nao_enviesa():
    class SemTema:
        pass
    termos, por_que = cs.termos_do_sucesso("x", [{"titulo": "qualquer"}], SemTema())
    assert termos == [] and "TEMA" in por_que


def teste_a_fonte_da_metrica_vem_junto():
    """⚠️ Ranking de curtida apresentado como view faz quem le' decidir
    achando que sabe."""
    top, fonte, aviso = melhores.melhores("modofuturo", 2)
    assert fonte in ("view_real", "curtida", "nenhuma")
    if fonte == "curtida":
        assert "CURTIDA" in aviso


def teste_nao_baixa_no_escuro():
    """Sem metrica nenhuma, o ciclo aborta em vez de escolher no acaso."""
    import json
    tmp = pathlib.Path(tempfile.mkdtemp()) / "fila.json"
    tmp.write_text(json.dumps({"itens": []}), encoding="utf-8")
    cs.FILA = tmp
    guardado = melhores.melhores
    melhores.melhores = lambda c, n=2: ([], "nenhuma", "sem dado")
    try:
        linha = cs.rodar("canal_sem_metrica", simular=True)
        assert "abortado" in linha["acao"]
    finally:
        melhores.melhores = guardado
        cs.FILA = RAIZ / "fila_cortes.json"


def teste_o_ciclo_nao_sobe_nem_dispara_corte():
    """A pasta do Drive decide o canal — foi ali que nasceram os 8 clipes de
    IA no @semanestesia. Subir continua sendo passo separado."""
    txt = (RAIZ / "ciclo_semanal.py").read_text(encoding="utf-8")
    assert "enviar_bruto_drive" not in txt
    assert "cortar_de_bruto" not in txt


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
