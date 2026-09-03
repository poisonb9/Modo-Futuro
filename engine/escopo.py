# -*- coding: utf-8 -*-
"""Cada motor corta SO' para os canais que ele foi feito pra servir.

⚠️ POR QUE ISTO EXISTE, medido em 03/09/2026.

O Bryan viu um video do @cozinha.internacional falando "fahrenheit" na
dublagem E na legenda. Rastreado ate' a origem:

  1. videos de cozinha foram largados na pasta RAW deste motor;
  2. o vigia nao mandava canal, entao sairam rotulados `modofuturo`;
  3. ESTE motor nao converte medidas — °F, xicara e polegada passam intactos.
     Conversao de unidade e' o diferencial do motor da COZINHA, que vive em
     `bryanaw2121-sketch/pipeline` com `conversoes.converter`;
  4. resultado: receita em Fahrenheit para publico brasileiro, publicada.

Oito clipes sairam assim antes de alguem notar, e quem notou foi o dono
olhando o proprio canal — nenhuma guarda pegou, porque nenhuma existia. O
motor aceitou o trabalho de bom grado e entregou algo que ele nao sabe fazer.

⚠️ A REGRA: motor recusa o que nao e' dele. A excecao existe, mas tem de ser
PEDIDA — nunca e' o padrao. Ordem do Bryan: "faca que todos os motores recusem
cortar videos para o que nao foram propostos. Apenas se mandarmos em excecao".

COMO UM MOTOR NOVO USA ISTO

    from engine import escopo
    escopo.exigir_canal_do_motor(canal)   # levanta se nao for dele

E declara os seus em `CANAIS_DO_MOTOR` (ou na variavel de ambiente
`CANAIS_DO_MOTOR`, util quando o mesmo codigo serve dois repositorios).
"""
from __future__ import annotations

import os

# ⚠️ ESTE MOTOR (Modo-Futuro) NAO SERVE A COZINHA. Nao e' esquecimento: a
# cozinha precisa de conversao de medidas, e isso nao existe aqui.
CANAIS_DO_MOTOR = {
    "modofuturo",
    "semanestesia.pod",
    "atefalhar",
    "truque.importado",
}

# Variavel que autoriza a excecao, uma vez, para aquele disparo.
ENV_EXCECAO = "PERMITIR_FORA_DO_ESCOPO"


class ForaDoEscopo(RuntimeError):
    """O canal pedido nao e' deste motor."""


def canais_do_motor() -> set:
    """Os canais deste motor, com a variavel de ambiente vencendo o padrao."""
    bruto = (os.environ.get("CANAIS_DO_MOTOR") or "").strip()
    if bruto:
        return {c.strip().lower() for c in bruto.split(",") if c.strip()}
    return set(CANAIS_DO_MOTOR)


def excecao_autorizada() -> bool:
    """O disparo pediu explicitamente pra passar por cima?

    ⚠️ SO' VALORES EXPLICITOS CONTAM. String vazia, "false" e "0" sao NAO —
    e' o que chega quando o input do workflow nao foi preenchido, e tratar
    isso como sim transformaria a excecao em padrao pela porta dos fundos.
    """
    v = (os.environ.get(ENV_EXCECAO) or "").strip().lower()
    return v in ("1", "true", "sim", "yes")


def fora_do_escopo(canal: str | None) -> bool:
    """O canal pedido esta' fora do que este motor serve?

    ⚠️ CANAL VAZIO NAO E' FORA DO ESCOPO. Disparo manual e teste antigo nao
    mandam canal, e recusar por ausencia de dado quebraria todo uso legitimo
    que existe hoje. O que este modulo impede e' cortar pro canal ERRADO, nao
    cortar sem dizer o canal — esse outro problema tem guarda propria no
    vigia, que deduz o canal da pasta do RAW.
    """
    c = (canal or "").strip().lower().lstrip("@")
    if not c:
        return False
    return c not in canais_do_motor()


def exigir_canal_do_motor(canal: str | None) -> None:
    """Levanta `ForaDoEscopo` se o canal nao for deste motor.

    A mensagem diz o que fazer, nao so' o que houve: quem le' isso num log de
    Actions as 3 da manha precisa saber pra onde levar o video.
    """
    if not fora_do_escopo(canal) or excecao_autorizada():
        return
    c = (canal or "").strip().lower().lstrip("@")
    raise ForaDoEscopo(
        f"canal '{c}' NAO e' deste motor. Este corta: "
        f"{', '.join(sorted(canais_do_motor()))}.\n"
        f"  Motivo de existir a recusa: cada motor tem receita propria — a "
        f"cozinha converte medidas (°F, xicara, polegada) e este NAO. Em "
        f"03/09/2026 oito receitas sairam daqui com Fahrenheit para publico "
        f"brasileiro.\n"
        f"  Se o video e' de outro canal, corte no motor DELE.\n"
        f"  Se voce sabe o que esta' fazendo, dispare com "
        f"{ENV_EXCECAO}=true — e a responsabilidade e' sua.")
