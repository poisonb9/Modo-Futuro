# -*- coding: utf-8 -*-
"""O vigia do RAW nao pode cortar o que a fila curada ja' reivindicou.

Sao dois caminhos independentes ate' o MESMO cortador. Sem guarda, fonte
enfileirada a mao continua "nova" pro vigia e o video sai duas vezes — que e'
a causa medida dos dois colapsos de alcance (02/08 e 25/08/2026).

⚠️ O CASO POSITIVO SOZINHO NAO PROVA NADA. Uma guarda que bloqueia TUDO
passaria nele e desligaria o vigia — que e' pior que a duplicata, porque
duplicata da' pra ver e desfazer, e vigia mudo nao da'. Por isso os casos
negativos abaixo sao obrigatorios.
"""
import json
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import vigia_raw as V


def _com_fila(itens):
    """Roda `ids_na_fila_de_cortes` contra uma fila de mentira."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / "fila_cortes.json").write_text(
        json.dumps({"itens": itens}, ensure_ascii=False), encoding="utf-8")
    antigo = V.RAIZ
    V.RAIZ = tmp
    try:
        return V.ids_na_fila_de_cortes()
    finally:
        V.RAIZ = antigo


def teste_positivo_estado_vivo_bloqueia():
    for estado in ("pendente", "disparado", "pronto"):
        ids = _com_fila([{"estado": estado, "drive_file_id": "ABC"}])
        assert "ABC" in ids, f"{estado} tinha de bloquear o vigia"


def teste_negativo_estado_terminal_NAO_bloqueia():
    """⚠️ TEOREMATICO, nao intuitivo.

    `sem_fonte` e `desistido` sao itens que a fila LARGOU. Se bloqueassem, a
    fonte ficaria refem de uma fila que nao vai mais corta-la — ninguem
    cortaria, pra sempre. O bloqueio tem de valer so' enquanto alguem de fato
    pretende cortar.
    """
    for estado in ("sem_fonte", "desistido"):
        ids = _com_fila([{"estado": estado, "drive_file_id": "ABC"}])
        assert "ABC" not in ids, f"{estado} NAO podia bloquear — a fila largou"


def teste_negativo_fila_vazia_nao_bloqueia_nada():
    assert _com_fila([]) == set(), "fila vazia nao bloqueia ninguem"


def teste_negativo_fila_ilegivel_nao_desliga_o_vigia():
    """⚠️ O DEFEITO QUE ESTA GUARDA PODIA REPETIR.

    Em 30/08 o `corte_em_andamento()` devolveu "tem corte rodando" a cada erro
    e desligou o vigia por 375 passadas em silencio. Se a leitura da fila
    falhar, a guarda tem de ABRIR (nao bloquear ninguem), nao fechar.
    """
    tmp = pathlib.Path(tempfile.mkdtemp())   # sem fila_cortes.json nenhum
    antigo = V.RAIZ
    V.RAIZ = tmp
    try:
        assert V.ids_na_fila_de_cortes() == set(), \
            "fila ilegivel tem de ABRIR a guarda, nunca travar o vigia"
    finally:
        V.RAIZ = antigo


def teste_negativo_id_ausente_nao_vira_None_na_lista():
    """Item sem `drive_file_id` nao pode injetar None no conjunto: um video
    cujo id o Drive nao devolvesse casaria com esse None e seria pulado."""
    ids = _com_fila([{"estado": "pendente"}, {"estado": "pendente",
                                              "drive_file_id": "X"}])
    assert None not in ids and ids == {"X"}


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
