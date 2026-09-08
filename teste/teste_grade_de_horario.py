# -*- coding: utf-8 -*-
"""A grade de horários: 3h entre posts, e o slot fraco fora da grade.

⚠️ MEDIDO em 08/09/2026, com VIEW REAL do TikTok (a do Buffer marca zero).
60 posts, e como cada hora da grade é um slot, a amostra é limpa:

    16:27   1,50x a mediana do canal   (n=11)   <- o melhor
    08:15   1,37x                      (n=14)
    19:30   1,27x                      (n=11)
    11:33   0,97x                      (n=12)   <- o único ABAIXO da mediana

Por faixa: tarde (12-17) 1,45x, manhã 1,22x, noite 1,23x. O 11:33 era o único
slot fora da faixa boa e o único que perdia. Virou 13:10.

## O QUE ESTE ARQUIVO PROTEGE

Duas coisas que já quebraram antes:

1. **A regra dos 3 horas.** Foi pedida pelo Bryan e a grade já esteve com
   2h36 entre dois slots sem ninguém notar. O sorteio de ±8 min em cada slot
   encurta o intervalo real em até 16 min — quem mexer na grade tem de contar
   isso, e é fácil esquecer.
2. **O 16:27 não se mexe.** É o melhor slot medido. Mudar o vencedor junto
   com o perdedor tornaria impossível saber qual mudança produziu o efeito no
   export do mês que vem.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import agendar_buffer as ab

MIN_HORAS = 3


def _minutos():
    return [h * 60 + m for h, m in ab.SLOTS_SP]


def teste_a_regra_dos_3_HORAS_vale_no_PIOR_caso():
    """⚠️ Com o sorteio, o intervalo real encolhe até 16 min. É esse que
    precisa passar dos 3h, não o nominal."""
    ms = _minutos()
    piores = [(b - a) - 2 * ab.VARIACAO_MIN for a, b in zip(ms, ms[1:])]
    assert min(piores) >= MIN_HORAS * 60, (
        f"o menor intervalo real e' {min(piores)} min, abaixo de "
        f"{MIN_HORAS}h. Aumente a folga da grade, nao reduza a variacao.")


def teste_os_slots_estao_em_ordem_e_sem_repetir():
    ms = _minutos()
    assert ms == sorted(ms), "grade fora de ordem"
    assert len(set(ms)) == len(ms), "slot repetido"


def teste_o_slot_VENCEDOR_de_16h_continua_na_grade():
    """⚠️ Ele é o melhor medido (1,50x). Se sair junto com uma mudança de
    outro slot, o efeito da mudança fica impossível de atribuir."""
    assert (16, 27) in ab.SLOTS_SP, "o melhor slot medido saiu da grade"


def teste_o_slot_PERDEDOR_de_11h33_saiu():
    """0,97x, o único abaixo da mediana do canal."""
    assert (11, 33) not in ab.SLOTS_SP


def teste_a_grade_tem_pelo_menos_um_slot_na_faixa_boa_da_tarde():
    """Tarde (12-17) mediu 1,45x contra 1,22x da manhã e 1,23x da noite."""
    assert any(12 <= h <= 17 for h, _ in ab.SLOTS_SP)


def teste_NEGATIVO_a_grade_nao_amontoa_tudo_na_tarde():
    """⚠️ O limite da regra. Se 'tarde é melhor' virasse 'só tarde', os 4
    posts sairiam em ~5 horas e o resto do dia ficaria vazio — e a medição
    NÃO diz isso: manhã (1,37x às 8h) e noite (1,27x) rendem bem. O que
    perdia era o meio da manhã, não a manhã.
    """
    horas = [h for h, _ in ab.SLOTS_SP]
    assert min(horas) < 12, "sumiu o slot da manha, que mede 1,37x"
    assert max(horas) >= 18, "sumiu o slot da noite, que mede 1,27x"


def teste_a_medicao_fica_junto_da_grade():
    txt = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")
    for n in ("1,50x", "0,97x", "n=11", "n=12"):
        assert n in txt, f"sumiu a medicao {n!r} de junto da grade"
    # e a contradição com a decisão de 26/08 fica registrada
    assert "13:07" in txt and "26/08" in txt


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
