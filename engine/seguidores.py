# -*- coding: utf-8 -*-
"""Seguidor por video — a metrica que mede o objetivo, e que o motor nao ve.

⚠️ POR QUE ESTE MODULO EXISTE.

O `melhores.py` ranqueia por VIEW e entrega os 2 primeiros pro radar, que
escolhe a fonte dos proximos videos. Ou seja: a view decide o que a maquina
vai produzir na semana seguinte.

MEDIDO em 08-09/09/2026, 11 posts do @modofuturo lidos um a um na tela do
Studio (o campo "Novos seguidores" NAO vem em export nenhum):

    titulo                          views  seg  t.medio  completo
    As regras extremas / fabrica     2473   28   10,63s     6,9%
    Como 1 poeira / 1 milhao         1009    1   16,11s     9,1%
    O erro microscopico / 500.000     568    0   17,97s     8,6%
    A vantagem decisiva dos EUA       519    2   12,64s     1,5%
    O Segredo dos Chips / CFET        309    1    7,20s     1,8%
    (mais 6 posts, todos com ZERO)

Os dois primeiros foram publicados no MESMO DIA, no mesmo canal — mesma
cadencia, mesmo estado do algoritmo. O de baixo prendeu a audiencia por MAIS
tempo (16,11s contra 10,63s) e teve MAIS conclusao (9,1% contra 6,9%), e
converteu 28 VEZES MENOS. Nao ha' aqui como culpar idade nem volume.

⚠️ CONCLUSAO, E ELA E' DESCONFORTAVEL: nenhuma metrica que o motor coleta
previu seguidor. Nem view, nem retencao, nem conclusao, nem curtida — o
recordista de curtida do lote (4,24%) deu ZERO seguidor.

## O QUE ESTE MODULO FAZ, E O QUE ELE DELIBERADAMENTE NAO FAZ

FAZ: anota `seguidores` no ranking, quando o post e' conhecido, e AVISA
quando o primeiro por view nao e' o primeiro por seguidor.

NAO FAZ: nao reordena nada. Com 11 posts, 7 deles zerados e um outlier
carregando 28 dos 32 seguidores, ranquear por seguidor seria trocar um sinal
fraco por um mais fraco ainda. A decisao de reordenar espera o proximo
export, com n maior — ver §23.9 do PLAYBOOK_TIKTOK.md.

⚠️ E o aviso e' o ponto: um ranking de view apresentado como se fosse de
conversao e' pior que nao ter ranking, porque quem le' decide achando que
sabe. Mesma regra do cabecalho do `melhores.py`.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "estado" / "seguidores_por_video.jsonl"

# Mesmo piso do `melhores._juntar_repetidos`: abaixo disto um titulo curto
# vira prefixo de meio canal.
PISO_PREFIXO = 20


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def registros(canal: str | None = None) -> list[dict]:
    """Le o JSONL. Linha quebrada e' pulada, nao derruba a leitura."""
    if not ARQUIVO.exists():
        return []
    saida = []
    for linha in ARQUIVO.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            r = json.loads(linha)
        except Exception:
            continue
        if canal and r.get("canal") != canal:
            continue
        if r.get("titulo") and r.get("novos_seguidores") is not None:
            saida.append(r)
    return saida


def _casa(chave: str, k: str) -> bool:
    """Um titulo e' o outro quando um e' PREFIXO do outro.

    ⚠️ E' a MESMA regra do `melhores._juntar_repetidos`, e pelo mesmo motivo:
    o export do Studio cola a descricao no fim do titulo, entao o titulo da
    print e' prefixo do titulo do export. Sem isto, o mesmo post entra duas
    vezes com nomes diferentes.
    """
    if len(chave) < PISO_PREFIXO or len(k) < PISO_PREFIXO:
        return False
    return chave.startswith(k) or k.startswith(chave)


def de(canal: str, titulo: str):
    """Seguidores daquele post, ou None quando ele nao foi medido.

    ⚠️ None NAO e' zero. Zero e' "foi ao Studio e nao converteu ninguem";
    None e' "ninguem abriu esse post ainda". Confundir os dois transformaria
    todo post nao medido em fracasso medido.
    """
    chave = _norm(titulo)
    if not chave:
        return None
    for r in registros(canal):
        k = _norm(r["titulo"])
        if chave == k or _casa(chave, k):
            return int(r["novos_seguidores"])
    return None


def anotar(postos: list[dict], canal: str) -> tuple[list[dict], str]:
    """Poe `seguidores` em cada posto e devolve (postos, aviso).

    Nao reordena — ver o cabecalho. O aviso sai quando o campeao por view NAO
    e' o campeao por seguidor entre os que foram medidos.
    """
    saida = []
    for p in postos:
        q = dict(p)
        s = de(canal, q.get("titulo", ""))
        if s is not None:
            q["seguidores"] = s
        saida.append(q)

    medidos = [p for p in saida if "seguidores" in p]
    if len(medidos) < 2:
        return saida, ""
    topo_view = medidos[0]
    topo_seg = max(medidos, key=lambda p: p["seguidores"])
    if topo_seg is topo_view or topo_seg["seguidores"] <= topo_view["seguidores"]:
        return saida, ""
    return saida, (
        f"⚠️ ranking por VIEW; por SEGUIDOR o primeiro seria outro "
        f"({topo_seg['titulo'][:40]}, {topo_seg['seguidores']} seg contra "
        f"{topo_view['seguidores']}). View nao previu conversao nos 11 posts "
        f"medidos em 09/09 — ver engine/seguidores.py.")
