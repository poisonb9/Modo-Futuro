# -*- coding: utf-8 -*-
"""Canal nunca se adivinha, e as tabelas nao podem divergir.

⚠️ OS DOIS DEFEITOS QUE ESTE ARQUIVO GUARDA, os dois medidos em 04/09/2026:

 1. `agendar_buffer` tratava clipe SEM canal como `modofuturo`. Oito clipes de
    podcast do Goggins ficaram elegiveis pro canal de chips e QUATRO foram
    agendados. Publicacao no canal errado nao tem desfazer bonito.

 2. A tabela de canais estava copiada em cinco arquivos, e a cozinha acabou
    com dois nomes. O caminho do estrago: o vigia mandava
    `cozinha.internacional`, o workflow comparava com `cozinha.importada`, nao
    batia, caia no `else` e saia com o token do MODOFUTURO.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import canais_registro as cr


# ------------------------------------------------- o palpite acabou

def teste_apelido_resolve():
    assert cr.canonico("cozinha.internacional") == "cozinha.importada"
    assert cr.canonico("@modofuturo") == "modofuturo"
    assert cr.canonico("  ATEFALHAR ") == "atefalhar"


def teste_negativo_desconhecido_devolve_None_e_nao_chute():
    """⚠️ O CASO NEGATIVO, e ele e' o ponto do arquivo inteiro. Um resolvedor
    que sempre devolve algo passaria no teste de cima e reproduziria o
    defeito: canal desconhecido virando o canal padrao."""
    assert cr.canonico("canal que nao existe") is None
    assert cr.canonico("") is None
    assert cr.canonico(None) is None
    # e o apelido NAO vale como canal do motor
    assert "cozinha.internacional" not in cr.CANAIS


def teste_negativo_a_cozinha_nao_e_deste_motor():
    assert "cozinha.importada" not in cr.do_motor()
    assert cr.CANAIS["cozinha.importada"].motor is False


# ------------------------------------------------- o default morreu

FONTE_AGENDADOR = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")


def teste_o_default_modofuturo_saiu_do_agendador():
    """⚠️ Por GRAFIA de proposito: o defeito ERA uma linha literal, e o que
    tem de nunca mais voltar e' ela."""
    assert 'or "modofuturo"' not in FONTE_AGENDADOR, (
        "o default que mandou os Goggins pro canal de chips voltou")


def teste_o_agendador_resolve_canal_pelo_registro():
    assert "canais_registro.canonico" in FONTE_AGENDADOR


# ------------------------------------------------- as tabelas concordam

def _tabelas():
    """As tabelas que os scripts publicam, com o nome do arquivo junto."""
    import conferir_postados, escolher_impulsionar, painel_filas
    import registrar_desempenho, repor_fila
    return {
        "conferir_postados": conferir_postados.CANAIS,
        "escolher_impulsionar": escolher_impulsionar.CANAIS,
        "registrar_desempenho": registrar_desempenho.CANAIS,
        "painel_filas": {c[3]: (c[1], c[2]) for c in painel_filas.CANAIS},
        "repor_fila": {**repor_fila.LIBERADOS, **repor_fila.SO_RELATA},
    }


def teste_nenhuma_tabela_usa_nome_fora_do_registro():
    """⚠️ ESTE e' o teste que teria pego a cozinha com dois nomes."""
    for arquivo, tab in _tabelas().items():
        for nome in tab:
            assert cr.canonico(nome), (
                f"{arquivo} usa o canal '{nome}', que nao esta' no registro "
                f"nem como apelido")


def teste_os_ids_batem_com_o_registro():
    """Copia que diverge no ID publica no canal de outra pessoa."""
    for arquivo, tab in _tabelas().items():
        for nome, valor in tab.items():
            c = cr.CANAIS[cr.canonico(nome)]
            if isinstance(valor, dict):          # repor_fila
                org, canal_id = valor["org"], valor["canal"]
            else:                                 # (org, canal_id, env)
                org, canal_id = valor[0], valor[1]
            assert (org, canal_id) == (c.org, c.canal_id), (
                f"{arquivo}: {nome} tem ids diferentes do registro")


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
