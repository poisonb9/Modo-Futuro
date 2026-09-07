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

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import freio

VIGIA = (RAIZ / "vigia_raw.py").read_text(encoding="utf-8")
FILA = (RAIZ / "cortar_fila.py").read_text(encoding="utf-8")


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
    """
    baixar = (RAIZ / "baixar_em_intervalos.py").read_text(encoding="utf-8")
    subir = (RAIZ / "enviar_bruto_drive.py").read_text(encoding="utf-8")
    assert "freio" not in baixar, "o freio vazou pro download"
    assert "freio" not in subir, "o freio vazou pro upload"


def teste_o_arquivo_fica_na_raiz_e_gritando():
    """Freio escondido fica puxado por uma semana sem ninguem notar."""
    assert freio.ARQUIVO.parent == RAIZ
    assert freio.ARQUIVO.name.isupper()


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
