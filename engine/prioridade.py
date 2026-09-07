# -*- coding: utf-8 -*-
"""A cozinha corta primeiro: este motor CEDE a vez quando ha' bruto dela.

Ordem do Bryan em 07/09/2026: "quando chegar video da cozinha ele e' o
primeiro a disparar".

## O QUE OS DOIS MOTORES DISPUTAM NAO E' RUNNER, E' COTA DE GEMINI

Medido em 07/09/2026, na mesma hora:

    14:40  bryanaw2121-sketch/pipeline  Cortar do Drive   failure
    14:41  poisonb9/Modo-Futuro         Cortar de bruto   failure
    14:51  poisonb9/Modo-Futuro         Cortar de bruto   failure

A mensagem do Modo-Futuro foi literal: "ABORTANDO ANTES DO DOWNLOAD: todas
as chaves esgotadas". A cota diaria vira 07:00 UTC, e nesse dia ela durou
**8 horas**. Enquanto ela esta' seca, corte nenhum acontece em lugar nenhum
— e a cozinha, que estava com 0 posts agendados, era a unica que nao tinha
folga pra esperar (os outros quatro tinham de +44h a +55h).

⚠️ **A PREMISSA DO POOL COMPARTILHADO NAO ESTA' PROVADA.** O que eu tenho:

  - os dois repositorios declaram **27 chaves GEMINI** cada um (contadas nos
    secrets do Modo-Futuro e nas referencias do workflow da cozinha);
  - os dois esgotaram na MESMA janela de minutos.

O que falta pra provar: comparar os VALORES, e o token nao le' os secrets do
repo da cozinha (403). Entao ceder a vez pode ser inutil — se os pools forem
distintos, a cota da cozinha nao melhora por este motor parar.

⚠️ Por isso o custo de ceder tem de ser BAIXO, e e' por isso que existe teto.
Se a premissa cair, o prejuizo maximo e' algumas horas de corte adiado num
motor com 44h de folga. Sem teto, o prejuizo seria os quatro canais secando.

## O TETO NAO E' ZELO, E' UM DEFEITO QUE JA' EXISTE

Bruto da cozinha **fica na RAW deste motor pra sempre**. Medido: a French
Onion Soup e o Tiramisu foram enviados em 06/09 e continuavam sendo
recusados a cada passada em 07/09 15:01 — este motor nunca os marca como
vistos, porque nunca os despacha.

Ceder "enquanto houver bruto da cozinha na RAW" seria, na pratica, ceder
PARA SEMPRE, e os quatro canais deste motor secariam em ~44h. Por isso:

    cede  <=>  ha' bruto da cozinha na RAW
               E faz menos de TETO_HORAS que ele apareceu
               E a cozinha nao teve corte com SUCCESS desde que ele apareceu

As tres juntas. A terceira desliga a cessao assim que a cozinha consegue o
que precisava; a segunda desliga mesmo que ela nunca consiga.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_COZINHA = "bryanaw2121-sketch/pipeline"

# ⚠️ TETO. Um corte da cozinha leva de 40 a 100 min (medido nos runs). Seis
# horas cobrem varios, e sao 13% das 44h de folga do canal mais apertado
# deste motor. Numero escolhido pra que a cessao NUNCA seja o motivo de um
# canal secar — se um dia for, o teto e' que esta' errado, nao a folga.
TETO_HORAS = 6

RAIZ = Path(__file__).resolve().parent.parent
VISTOS = RAIZ / "estado" / "cozinha_esperando.json"


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _carregar() -> dict:
    try:
        return json.loads(VISTOS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _gravar(d: dict) -> None:
    VISTOS.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                      encoding="utf-8")


def marcar(brutos: list[tuple[str, str | None]]) -> dict:
    """Registra desde quando cada bruto da cozinha esta' esperando.

    Recebe (id, chegada), onde `chegada` e' o `modifiedTime` do Drive.

    ⚠️ O RELOGIO E' O DA CHEGADA NO DRIVE, nao o da primeira vez que eu vi.
    O Bryan pediu "quando CHEGAR video da cozinha ele e' o primeiro a
    disparar" — chegada, nao descoberta.

    Isso foi medido num ensaio em 07/09: a French Onion Soup e o Tiramisu
    estavam parados na RAW desde 06/09, travados por COTA e nao por vez. Com
    o relogio na descoberta, eles zeravam o prazo no instante em que a guarda
    nasceu e faziam o motor ceder 6h por brutos de ontem — cedendo a vez pra
    quem nao estava esperando a vez.

    ⚠️ E o carimbo NAO SE RENOVA: `setdefault` so' escreve na primeira vez.
    Se cada passada reescrevesse, o teto nunca venceria e a cessao voltaria a
    ser eterna, que e' exatamente o que o teto existe pra impedir.
    """
    d = _carregar()
    agora = _agora().isoformat()
    ids = [i for i, _ in brutos]
    for i, chegada in brutos:
        d.setdefault(i, chegada or agora)
    # Bruto que saiu da RAW nao espera mais nada.
    for i in list(d):
        if i not in ids:
            del d[i]
    _gravar(d)
    return d


def _cozinha_ja_cortou(desde: datetime) -> bool | None:
    """A cozinha teve corte com SUCCESS depois de `desde`?

    None = nao deu pra saber (sem token, ou a API nao respondeu). Quem chama
    trata None como "nao sei", e nao como "nao cortou" — ver `ceder`.
    """
    tok = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if not tok:
        try:
            tok = (RAIZ / "github_token.txt").read_text(encoding="utf-8").strip()
        except Exception:
            return None
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO_COZINHA}/actions/runs?per_page=20",
        headers={"Authorization": f"Bearer {tok}",
                 "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            runs = json.load(r).get("workflow_runs", [])
    except Exception:
        return None
    for x in runs:
        if x.get("conclusion") != "success":
            continue
        # ⚠️ So' corte conta. "Conferir postados" tambem da' success e nao
        # gasta uma gota de Gemini — trata-lo como corte desligaria a cessao
        # sem a cozinha ter cortado nada.
        if "cortar" not in (x.get("name") or "").lower():
            continue
        quando = datetime.fromisoformat(
            x["created_at"].replace("Z", "+00:00"))
        if quando > desde:
            return True
    return False


def ceder(brutos_cozinha: list[tuple[str, str | None]]) -> tuple[bool, str]:
    """Este motor deve segurar os disparos desta passada?

    Devolve (cede, motivo). O motivo vai pro log SEMPRE, inclusive quando a
    resposta e' nao — cessao silenciosa e' indistinguivel de defeito.
    """
    # ⚠️ MARCA ANTES DE SAIR, inclusive com a lista vazia. Sem isto o estado
    # nunca era limpo: o bruto saia da RAW e o registro dele ficava, com um
    # carimbo velho que faria o teto vencer na proxima vez sem motivo.
    espera = marcar(brutos_cozinha)
    if not espera:
        return False, ""

    def _quando(v: str) -> datetime:
        # O Drive devolve "...Z"; o nosso proprio carimbo ja' vem com fuso.
        d = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

    mais_antigo = min(_quando(v) for v in espera.values())
    horas = (_agora() - mais_antigo).total_seconds() / 3600
    if horas > TETO_HORAS:
        return False, (
            f"bruto da cozinha esperando ha' {horas:.1f}h — passou do teto de "
            f"{TETO_HORAS}h, este motor volta a cortar. ⚠️ Se a cozinha ainda "
            f"nao cortou, o problema NAO e' fila: e' cota ou defeito la'.")

    ja = _cozinha_ja_cortou(mais_antigo)
    if ja is True:
        return False, ("a cozinha ja' cortou desde que o bruto chegou — "
                       "nao ha' mais o que ceder.")
    # ⚠️ None (nao deu pra saber) CEDE, dentro do teto. Errar cedendo custa
    # uma passada de 10 min num motor com 44h de folga; errar nao-cedendo
    # custa a vez do canal que esta' em ZERO. E o teto limita o estrago dos
    # dois lados.
    duvida = " (nao consegui ler os runs da cozinha; cedo por duvida)" if ja is None else ""
    return True, (
        f"CEDENDO A VEZ: {len(espera)} bruto(s) da cozinha esperando ha' "
        f"{horas:.1f}h de {TETO_HORAS}h{duvida}. Ordem do Bryan em 07/09: "
        f"video da cozinha dispara primeiro. Volto a cortar na proxima "
        f"passada em que ela tiver cortado, ou quando o teto vencer.")
