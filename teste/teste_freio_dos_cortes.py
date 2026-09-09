# -*- coding: utf-8 -*-
"""O freio pega nos TRES lugares que disparam corte — ou nao e' freio.

⚠️ Ordem do Bryan em 07/09/2026: "pausa os cortes por enquanto, eu preciso
dos tokens do Gemini para outro projeto".

O QUE ESTE ARQUIVO PROTEGE

Corte e' disparado de tres lugares que nao se conversam: o `vigia_raw` aqui
na maquina, o `cortar_fila` na nuvem pelo cron de 30 min, e o disparo manual.
Um freio que pega em dois dos tres nao economiza cota nenhuma — so' faz
parecer que economizou, ate' alguem olhar a fatura.

⚠️ E O CONTRARIO TAMBEM E' TESTADO: baixar e subir pro Drive tem de
CONTINUAR funcionando com o freio puxado. So' o corte gasta Gemini. Se a
pausa parasse tambem o estoque, sair dela levaria dias em vez de minutos.
"""
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import freio

VIGIA = (RAIZ / "vigia_raw.py").read_text(encoding="utf-8")
FILA = (RAIZ / "cortar_fila.py").read_text(encoding="utf-8")


# ⚠️ O TESTE NAO PODE ENCOSTAR NO FREIO DE VERDADE.
#
# MEDIDO em 07/09/2026, e o defeito era GRAVE: a primeira versao deste
# arquivo chamava `freio.ARQUIVO.unlink()` direto — e `freio.ARQUIVO` e' o
# PAUSA_CORTES da raiz do repositorio. Rodar a suite APAGAVA o freio de
# producao.
#
# Foi o que aconteceu: puxei o freio, rodei a suite logo depois, e a suite
# o soltou. O remoto continuou pausado (o commit ja' tinha ido), mas AQUI o
# vigia voltou a despachar — e cortou tres brutos do @atefalhar naquela
# noite, gastando exatamente a cota que a pausa existia pra poupar.
#
# Teste que escreve em estado de producao nao e' teste: e' um comando
# disfarcado, que roda toda vez que alguem confere a suite.
_TMP = pathlib.Path(tempfile.mkdtemp()) / "PAUSA_CORTES_teste"
freio.ARQUIVO = _TMP


def _limpo():
    if freio.ARQUIVO.exists():
        freio.ARQUIVO.unlink()


def teste_puxar_e_soltar():
    _limpo()
    assert not freio.puxado()
    freio.puxar("teste")
    assert freio.puxado()
    assert freio.soltar() is True
    assert not freio.puxado()
    assert freio.soltar() is False, "soltar duas vezes tem de ser inofensivo"


def teste_o_motivo_fica_escrito():
    """Freio sem explicacao vira misterio de uma semana."""
    _limpo()
    txt = freio.puxar("cota pro outro projeto", quem="Bryan")
    assert "cota pro outro projeto" in txt and "Bryan" in txt
    assert "cota pro outro projeto" in freio.motivo()
    _limpo()


def teste_motivo_util_mesmo_com_arquivo_vazio():
    """⚠️ Arquivo vazio nao pode virar linha em branco no log — isso faz o
    freio parecer defeito."""
    _limpo()
    freio.ARQUIVO.write_text("", encoding="utf-8")
    m = freio.motivo()
    assert m.strip(), "motivo vazio"
    assert "PAUSA_CORTES" in m
    _limpo()


def teste_o_vigia_respeita_o_freio():
    assert "freio.puxado()" in VIGIA, "o vigia nao consulta o freio"
    # E consulta ANTES de despachar, senao ja' gastou.
    assert VIGIA.index("freio.puxado()") < VIGIA.index('disparar(v["id"]')


def teste_o_consumidor_da_fila_respeita_o_freio():
    """⚠️ ESTE e' o que economiza de verdade. O vigia so' despacha bruto
    novo; quem consome os 29 itens ja' na fila, de 30 em 30 minutos, e' este.
    Um freio so' no vigia deixaria a nuvem cortando a noite toda."""
    assert "freio.puxado()" in FILA, "o cortar_fila nao consulta o freio"
    # Antes de ler a fila e antes de qualquer disparo.
    assert FILA.index("freio.puxado()") < FILA.index("pendentes = ")


def teste_NEGATIVO_baixar_e_subir_seguem_liberados():
    """O freio e' de CORTE, nao de estoque.

    Se ele parasse o download e o upload, sair da pausa levaria dias — teria
    de baixar tudo de novo. O ganho da pausa e' cota de Gemini, e nem baixar
    nem subir gastam uma gota dela.

    ⚠️ E A BUSCA E' PELO FREIO CERTO, nao pela palavra. Em 09/09/2026 a
    sentinela do YouTube ganhou um freio PROPRIO — o de bot-check, 24h, que
    NADA tem a ver com este, que e' pausa de corte por cota de Gemini. Sao
    dois mecanismos com o mesmo nome, e procurar a palavra solta acusava o
    download por consultar o freio errado. O que nao pode vazar pra ca' e' o
    `engine/freio.py`: `freio.puxado()`, `from engine import freio`.
    """
    baixar = (RAIZ / "baixar_em_intervalos.py").read_text(encoding="utf-8")
    subir = (RAIZ / "enviar_bruto_drive.py").read_text(encoding="utf-8")
    for nome, fonte in (("download", baixar), ("upload", subir)):
        assert "freio.puxado()" not in fonte, f"o freio de corte vazou pro {nome}"
        assert "from engine import freio" not in fonte, (
            f"o freio de corte vazou pro {nome}")
        assert "engine.freio" not in fonte, f"o freio de corte vazou pro {nome}"


def teste_o_arquivo_fica_na_raiz_e_gritando():
    """Freio escondido fica puxado por uma semana sem ninguem notar.

    ⚠️ Confere o CAMINHO PADRAO do modulo, nao o `freio.ARQUIVO` desta
    sessao — que este arquivo redirecionou pro temporario de proposito.
    """
    import importlib
    padrao = importlib.reload(importlib.import_module("engine.freio")).ARQUIVO
    assert padrao.parent == RAIZ
    assert padrao.name.isupper()
    # e devolve o desvio, senao os testes seguintes mexem no arquivo real
    freio.ARQUIVO = _TMP


def teste_a_suite_NAO_apaga_o_freio_de_producao():
    """⚠️ O teste que existe por causa do estrago de 07/09.

    Se `freio.ARQUIVO` apontar pra raiz durante a suite, rodar a suite
    APAGA a pausa — e foi assim que tres cortes sairam numa noite em que a
    cota devia estar sendo poupada.
    """
    assert freio.ARQUIVO != RAIZ / "PAUSA_CORTES"
    assert "PAUSA_CORTES" not in str(RAIZ / "x") or freio.ARQUIVO.parent != RAIZ


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
