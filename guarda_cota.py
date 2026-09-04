# -*- coding: utf-8 -*-
"""Aborta o corte ANTES do download, quando o Gemini nao tem cota.

POR QUE ESTE ARQUIVO EXISTE, medido em 04/09/2026.

`engine/traducao.py` TEM caminho de reserva (Nemotron, com quarentena).
`engine/selecao.py` NAO tem: sem Gemini, ela levanta e mata o run.

O preco disso e' pago tarde. No run 33803772922 o motor baixou 0,11 GB,
traduziu o material inteiro (ja' caindo na reserva as 20:46:52) e so' as
20:48:42 morreu na selecao. Ou seja: **o run paga o download e a traducao e
so' entao descobre que nao tem como escolher.** Tres runs de 04/09 morreram
assim, e cada um roda de 40 a 100 minutos antes de morrer.

⚠️ ESTA GUARDA NAO MUDA O QUE SE PUBLICA. Foi de proposito: dar reserva a`
selecao mudaria QUAIS clipes vao ao ar, e isso e' decisao do Bryan — o
proprio `traducao.py` argumenta que o Nemotron e' reserva CARA, com
quarentena, e nao alternativa barata. Aqui a gente so' para de queimar
runner num run cujo desfecho ja' e' conhecido.

⚠️ E A MENSAGEM DE SAIDA NAO E' ENFEITE. Ela precisa conter uma das marcas
que o `cortar_fila.falhou_por_cota()` reconhece, senao a falha e' contada
como defeito DA FONTE e tres delas expulsam da fila um video perfeito — foi
o que aconteceu em 01/09 com "The Only 13 Minutes You Need To Master
Discipline".
"""
from __future__ import annotations

import sys

# A marca TEM de sobreviver a qualquer reescrita desta mensagem: e' o que o
# classificador procura no log pra nao punir a fonte.
MARCA = "todas as chaves esgotadas"


def main() -> int:
    import cortar_fila

    ok, motivo = cortar_fila.tem_cota()
    if ok:
        print(f"cota ok ({motivo}) — seguindo pro download.")
        return 0
    print(f"[x] ABORTANDO ANTES DO DOWNLOAD: {MARCA} ({motivo}).")
    print("    A selecao nao tem reserva; sem Gemini este run morreria depois "
          "de baixar e traduzir. Parar aqui economiza 40-100 min de runner.")
    print("    A cota diaria vira 07:00 UTC (04:00 em Sao Paulo).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
