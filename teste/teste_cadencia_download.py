# -*- coding: utf-8 -*-
"""Dois downloads nunca coincidem, e sempre ha' intervalo entre eles.

⚠️ Ordem do Bryan em 08/09/2026: "os downloads nunca podem coincidir de
nenhum canal. Sempre respeitando intervalos para que a gente nunca perca esse
privilegio que acabamos de conseguir. Crie uma guarda infalivel pra isso."

O privilegio: esta maquina baixa do YouTube sem espera e sem CAPTCHA; o
runner do GitHub nao (IP de datacenter). Se este IP for degradado, o projeto
perde o unico caminho que funciona, e nao ha' plano B.

O QUE ESTE ARQUIVO PROVA

O caso positivo (espera quando acabou de baixar) e' facil. O que sustenta a
guarda sao os casos em que ela poderia falhar ABERTA — deixar passar:

  - estado corrompido lido como "nunca baixei";
  - relogio pra tras fazendo o intervalo parecer cumprido;
  - trava presa liberada sem conferir se o dono morreu;
  - e, o mais importante, a trava morando no LACO em vez do download, o que
    a faria valer dentro de uma rodada e nao entre canais.
"""
import json
import os
import pathlib
import sys
import tempfile
from datetime import datetime, timedelta, timezone

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import cadencia

TMP = pathlib.Path(tempfile.mkdtemp())
cadencia.ESTADO = TMP / "cadencia.json"
cadencia.TRAVA = TMP / "cadencia.lock"


def _limpo():
    for p in (cadencia.ESTADO, cadencia.TRAVA):
        if p.exists():
            p.unlink()


def _carimbar(segundos_atras: float):
    q = datetime.now(timezone.utc) - timedelta(seconds=segundos_atras)
    cadencia.ESTADO.write_text(json.dumps({"ultimo": q.isoformat()}),
                               encoding="utf-8")


def teste_positivo_espera_logo_apos_um_download():
    _limpo()
    _carimbar(0)
    assert cadencia.espera_devida() > 0


def teste_negativo_depois_do_intervalo_pode_baixar():
    """Senao a guarda travaria tudo pra sempre — e alguem a desligaria."""
    _limpo()
    _carimbar(cadencia.INTERVALO_S * 2)
    assert cadencia.espera_devida() == 0


def teste_estado_corrompido_ESPERA(  ):
    """⚠️ Falha FECHADA. Ler lixo como 'nunca baixei' e' o que produz duas
    rodadas coladas logo depois de um estado corrompido."""
    _limpo()
    cadencia.ESTADO.write_text("{lixo nao json", encoding="utf-8")
    assert cadencia.espera_devida() > 0


def teste_relogio_para_tras_ESPERA():
    """Carimbo no futuro nao pode virar 'ja' passou tempo demais'."""
    _limpo()
    _carimbar(-3600)          # uma hora no futuro
    assert cadencia.espera_devida() > 0


def teste_maquina_limpa_pode_baixar():
    """Sem estado nenhum e sem arquivo, a primeira vez nao espera."""
    _limpo()
    assert cadencia.espera_devida() == 0


def teste_trava_de_processo_VIVO_nao_e_tomada():
    """⚠️ O teste que impede o download simultaneo.

    Uma trava com PID vivo tem de ser respeitada. Tomar a trava de um
    processo vivo produz exatamente o que a guarda existe pra impedir.
    """
    _limpo()
    cadencia.TRAVA.write_text(f"{os.getpid()} outro_canal", encoding="utf-8")
    cadencia.ESPERA_MAX_TRAVA_S = 1        # nao trava a suite
    cadencia.SONDA_S = 0.1
    try:
        with cadencia.vez(canal="teste"):
            assert False, "tomou a trava de um processo VIVO"
    except TimeoutError as e:
        assert "dois ao mesmo tempo" in str(e)
    finally:
        cadencia.ESPERA_MAX_TRAVA_S = 2400
        cadencia.SONDA_S = 5


def teste_trava_de_processo_MORTO_e_assumida():
    """Senao um crash travaria os downloads pra sempre."""
    _limpo()
    _carimbar(cadencia.INTERVALO_S * 2)
    # PID que nao existe: alto e improvavel nesta maquina
    cadencia.TRAVA.write_text("999999 fantasma", encoding="utf-8")
    with cadencia.vez(canal="teste"):
        pass
    assert not cadencia.TRAVA.exists(), "a trava ficou pra tras"


def teste_o_carimbo_e_gravado_ao_terminar():
    _limpo()
    _carimbar(cadencia.INTERVALO_S * 2)
    with cadencia.vez(canal="modofuturo"):
        pass
    d = json.loads(cadencia.ESTADO.read_text(encoding="utf-8"))
    assert d["por"] == "modofuturo"
    assert cadencia.espera_devida() > 0, "nao carimbou o fim"


def teste_a_guarda_esta_NO_DOWNLOAD_e_nao_no_laco():
    """⚠️ O teste estrutural que sustenta todos os outros.

    Se a trava morasse no laco de `main()`, ela valeria dentro de UMA rodada
    e nao entre canais — e o `ciclo_semanal --todos` a contornaria sem
    ninguem perceber. Ela tem de estar na funcao por onde todo download
    passa.
    """
    txt = (RAIZ / "baixar_em_intervalos.py").read_text(encoding="utf-8")
    i_def = txt.index("def baixar(")
    i_priv = txt.index("def _baixar_agora(")
    i_vez = txt.index("cadencia.vez(")
    assert i_def < i_vez < i_priv, "a cadencia nao envolve o download"
    # e o laco nao pode ter voltado a dormir por conta propria
    assert "time.sleep(pausa)" not in txt


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
