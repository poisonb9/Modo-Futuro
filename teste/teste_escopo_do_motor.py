# -*- coding: utf-8 -*-
"""Motor recusa cortar pro que nao e' dele — so' passa com excecao PEDIDA.

⚠️ MEDIDO em 03/09/2026. O Bryan viu um video do @cozinha.internacional
falando "fahrenheit" na dublagem e na legenda. Rastreado: oito receitas foram
cortadas por ESTE motor, que nao converte medidas — conversao de unidade e' o
diferencial do motor da cozinha, noutro repositorio.

Nenhuma guarda pegou porque nenhuma existia: o motor aceitou o trabalho e
entregou algo que nao sabe fazer. Quem notou foi o dono, olhando o canal.

Ordem do Bryan: "faca que todos os motores recusem cortar videos para o que
nao foram propostos. Apenas se mandarmos em excecao".
"""
import os
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import escopo

MAIN = (RAIZ / "main.py").read_text(encoding="utf-8")
VIGIA = (RAIZ / "vigia_raw.py").read_text(encoding="utf-8")


def _limpo():
    os.environ.pop(escopo.ENV_EXCECAO, None)
    os.environ.pop("CANAIS_DO_MOTOR", None)


def teste_positivo_recusa_canal_de_outro_motor():
    _limpo()
    assert escopo.fora_do_escopo("cozinha.internacional")
    try:
        escopo.exigir_canal_do_motor("cozinha.internacional")
        raise AssertionError("devia ter recusado")
    except escopo.ForaDoEscopo as e:
        # a mensagem tem de DIZER O QUE FAZER, nao so' que houve erro
        assert "motor DELE" in str(e), str(e)
        assert escopo.ENV_EXCECAO in str(e), str(e)


def teste_negativo_os_canais_deste_motor_PASSAM():
    """⚠️ TEOREMATICO. Uma guarda que recusasse tudo passaria no positivo e
    pararia a fabrica inteira."""
    _limpo()
    for c in ("modofuturo", "semanestesia.pod", "atefalhar", "truque.importado"):
        escopo.exigir_canal_do_motor(c)          # nao pode levantar
        assert not escopo.fora_do_escopo(c)


def teste_negativo_canal_vazio_NAO_e_fora_do_escopo():
    """Disparo manual e uso antigo nao mandam canal. Recusar por ausencia de
    dado quebraria tudo que funciona hoje — e esse outro problema ja' tem
    guarda propria no vigia, que deduz o canal da pasta."""
    _limpo()
    assert not escopo.fora_do_escopo("")
    assert not escopo.fora_do_escopo(None)
    escopo.exigir_canal_do_motor(None)


def teste_arroba_e_caixa_nao_enganam():
    _limpo()
    assert not escopo.fora_do_escopo("@ModoFuturo")
    assert escopo.fora_do_escopo("@Cozinha.Internacional")


def teste_excecao_precisa_ser_PEDIDA():
    _limpo()
    os.environ[escopo.ENV_EXCECAO] = "true"
    escopo.exigir_canal_do_motor("cozinha.internacional")   # passa
    _limpo()


def teste_negativo_valor_vazio_NAO_autoriza():
    """⚠️ O input do workflow chega vazio quando ninguem preencheu. Se isso
    contasse como sim, a excecao viraria o padrao pela porta dos fundos."""
    for v in ("", "false", "0", "nao", "  "):
        os.environ[escopo.ENV_EXCECAO] = v
        assert not escopo.excecao_autorizada(), f"{v!r} nao podia autorizar"
    _limpo()


def teste_a_guarda_esta_LIGADA_no_main():
    """Modulo certo e nao chamado seria pior que nao existir: daria a
    impressao de protecao."""
    assert "escopo.exigir_canal_do_motor" in MAIN, "main.py nao chama a guarda"
    i_guarda = MAIN.index("escopo.exigir_canal_do_motor")
    i_ffmpeg = MAIN.index('for b in ("ffmpeg", "ffprobe")')
    assert i_guarda < i_ffmpeg, "a guarda roda DEPOIS do trabalho comecar"


def teste_a_guarda_esta_LIGADA_no_vigia():
    """Recusar no main custa um run de setup; recusar no vigia custa uma
    linha de log."""
    assert "escopo.fora_do_escopo" in VIGIA, "o vigia nao filtra por escopo"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
