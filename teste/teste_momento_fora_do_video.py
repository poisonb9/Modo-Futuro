# -*- coding: utf-8 -*-
"""Momento que comeca depois do fim do video tem motivo PROPRIO.

MEDIDO no run 33622773012 (02/09/2026): fonte de 17,0 min, o modelo devolveu
momentos comecando em ~1409s e ~1204s. O `min(dur_total, fim_s)` prendia o fim
em 1020s, a subtracao dava NEGATIVA, e o descarte saia como
"curto demais: -389.7s < DUR_MIN 65s".

⚠️ Duracao negativa nao existe. A rejeicao estava certa; o ROTULO mandava
procurar defeito no tamanho do clipe, que estava intacto.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import config
from engine import selecao


def _clipe(ini, fim, titulo="t", nota=9, gancho=10):
    return {"titulo": titulo, "nota": nota, "forca_gancho": gancho,
            "inicio_s": ini, "fim_s": fim}


def _motivos(clipes, dur_total):
    """Roda o validador e devolve os motivos de recusa que ele imprimiu."""
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        selecao._validar([dict(c) for c in clipes], dur_total)
    return buf.getvalue()


def teste_positivo_momento_fora_do_video():
    saida = _motivos([_clipe(1409.0, 1500.0)], dur_total=1020.0)
    assert "fora do video" in saida, saida
    assert "curto demais" not in saida, "o rotulo antigo voltou: " + saida


def teste_negativo_clipe_normal_passa():
    """⚠️ TEOREMATICO. Um clipe de 90s no meio de um video de 1020s nao pode
    ser recusado — se fosse, a guarda estaria recusando TUDO e o teste
    positivo sozinho nao perceberia."""
    bons = selecao._validar([_clipe(100.0, 190.0)], dur_total=1020.0)
    assert len(bons) == 1, f"clipe valido foi recusado: {bons}"


def teste_negativo_curto_demais_continua_curto_demais():
    """A causa antiga tem de continuar sendo detectada com o nome dela.
    Um clipe de 10s dentro do video e' curto — nao e' 'fora do video'."""
    saida = _motivos([_clipe(100.0, 110.0)], dur_total=1020.0)
    assert "curto demais" in saida, saida
    assert "fora do video" not in saida, saida


def teste_negativo_termina_exatamente_no_fim_nao_e_fora():
    """Clipe que vai ate' o ultimo segundo do video e' VALIDO. Se a guarda
    usasse `fim_s > dur_total` em vez de `inicio_s >= dur_total`, este caso
    seria recusado por engano."""
    bons = selecao._validar([_clipe(900.0, 1020.0)], dur_total=1020.0)
    assert len(bons) == 1, f"clipe que termina no fim foi recusado: {bons}"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
