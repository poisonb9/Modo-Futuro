# -*- coding: utf-8 -*-
"""Diz QUAL post merece o dinheiro do impulsionamento — e por que.

Pedido do Bryan em 02/09/2026, depois de impulsionar um post por intuicao:
"pode deixar o seletor pronto".

## O QUE ELE DECIDE, E O QUE NAO DECIDE

Ele NAO cria campanha nem gasta nada. Devolve uma lista ordenada com o motivo
de cada posicao, pro Bryan confirmar no app. A automacao do gasto depende da
API de Anuncios do TikTok, que ficou pra quando ele separar orcamento.

## O CRITERIO: RITMO, NAO TOTAL

⚠️ ORDENAR POR VIEWS TOTAIS PREMIA O POST MAIS VELHO, sempre. Um post de tres
dias com 500 views nao esta' indo melhor que um de seis horas com 150 — esta'
ha' mais tempo no ar. O que separa os dois e' VIEWS POR HORA.

Amplificar o que ja' esta' pegando e' o que faz o dinheiro render: o algoritmo
ja' esta' entregando, e o pago soma em cima. Impulsionar um post parado e'
pagar pra descobrir de novo que ele nao pega.

## AS TRES EXCLUSOES

⚠️ POST COM MENOS DE 24h FICA DE FORA. A metrica do Buffer atrasa, e o atraso
encolhe com a idade — MEDIDO em 01/09 comparando print com API:

    2,7h -> a API mostrava 49% do real     22,6h -> 99%
    7,6h -> 56%                            26,6h+ -> 100%

Um post novo pareceria fraco por defeito da leitura, e o seletor o descartaria
justamente quando ele esta' subindo.

⚠️ POST COM MAIS DE 7 DIAS TAMBEM SAI. A entrega organica ja' terminou; o pago
nao reanima o que o algoritmo aposentou.

⚠️ E POST COM ZERO VIEWS SAI, por mais barato que pareca. Zero nao e' "ainda
nao pegou": nos MEDIMOS que os dois unicos posts com ritmo zero eram os dois
sem imagem de comida na abertura. Pagar pra distribuir um post que nao segura
ninguem e' comprar audiencia pra ela sair.
"""
from __future__ import annotations

import io
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CRED = r"C:/Users/Administrator/Desktop/Tiktok/CREDENCIAIS.md"
IDADE_MIN_H = 24        # abaixo disso a metrica do Buffer ainda esta' baixa
IDADE_MAX_H = 24 * 7    # acima disso a entrega organica ja' acabou

CANAIS = {
    "modofuturo": ("6a6ca3c3aba3767824bf6234", "6a6cd9d54b2d03035f771631", "BUFFER_TOKEN"),
    "cozinha.internacional": ("6a90dddb9bb05f07b058e9bc", "6a90de80ccaf649a672ebe15", "BUFFER_TOKEN_COZINHA"),
    "semanestesia.pod": ("6a937e2ccae8f6fdedefa317", "6a938ce8065799be46508cc6", "BUFFER_TOKEN_SEMANESTESIA"),
    "atefalhar": ("6a94a9f9ca5d8883aa924198", "6a94aaf5065799be46581e1d", "BUFFER_TOKEN_ATEFALHAR"),
    "truque.importado": ("6a94c752e0b1602e8c5cf1ae", "6a94c8f3065799be465981f6", "BUFFER_TOKEN_TRUQUEIMPORTADO"),
}
Q = """query($i: PostsInput!){ posts(input:$i){ edges{ node{ text sentAt
      metrics{ name value } } } } }"""


def _tokens() -> dict:
    t = {k: v for k in CANAIS if (v := os.environ.get(CANAIS[k][2], "").strip())}
    if len(t) == len(CANAIS) or not os.path.exists(CRED):
        return t
    for l in io.open(CRED, encoding="utf-8").read().splitlines():
        m = re.match(r"\|\s*@([\w.]+)\s*\|\s*`([^`]+)`\s*\|", l)
        if m and len(m.group(2)) > 30:
            t.setdefault(m.group(1), m.group(2))
    return t


def coletar() -> list[dict]:
    tok = _tokens()
    agora = datetime.now(timezone.utc)
    saida = []
    for canal, (org, ch, _e) in CANAIS.items():
        t = tok.get(canal)
        if not t:
            continue
        try:
            req = urllib.request.Request(
                "https://api.buffer.com/",
                data=json.dumps({"query": Q, "variables": {"i": {
                    "organizationId": org,
                    "filter": {"status": ["sent"], "channelIds": [ch]}}}}).encode(),
                headers={"Authorization": f"Bearer {t}",
                         "Content-Type": "application/json"})
            ns = [e["node"] for e in json.load(
                urllib.request.urlopen(req, timeout=60))["data"]["posts"]["edges"]]
        except Exception as e:
            print(f"  [!] {canal}: {str(e)[:50]}")
            continue
        for n in ns:
            if not n.get("sentAt"):
                continue
            m = {x["name"]: x["value"] for x in (n.get("metrics") or [])}
            v = m.get("Views")
            if v is None:
                continue
            idade = (agora - datetime.fromisoformat(
                n["sentAt"].replace("Z", "+00:00"))).total_seconds() / 3600
            saida.append({
                "canal": canal, "titulo": n["text"].splitlines()[0][:52],
                "views": int(v), "idade_h": idade,
                "por_hora": int(v) / max(idade, 0.1),
                "curtidas": int(m.get("Reactions") or 0),
                "shares": int(m.get("Shares") or 0),
            })
    return saida


def escolher(posts: list[dict]) -> tuple[list[dict], list[tuple[dict, str]]]:
    """(candidatos ordenados, descartados com o motivo)."""
    bons, fora = [], []
    for p in posts:
        if p["idade_h"] < IDADE_MIN_H:
            fora.append((p, f"novo demais ({p['idade_h']:.0f}h) — a metrica "
                            "do Buffer ainda esta' baixa"))
        elif p["idade_h"] > IDADE_MAX_H:
            fora.append((p, f"velho demais ({p['idade_h']/24:.0f}d) — a "
                            "entrega organica ja' acabou"))
        elif p["views"] == 0:
            fora.append((p, "zero views — pagar pra distribuir o que nao "
                            "segura ninguem"))
        else:
            bons.append(p)
    bons.sort(key=lambda x: -x["por_hora"])
    return bons, fora


def main() -> None:
    bons, fora = escolher(coletar())
    if not bons:
        print("Nenhum post elegivel agora.")
    else:
        print("IMPULSIONAR — ordenado por views/hora (ritmo, nao total)\n")
        for i, p in enumerate(bons[:8], 1):
            print(f"  {i}. {p['por_hora']:6.1f} views/h   {p['views']:>5} em "
                  f"{p['idade_h']:.0f}h   {p['canal']}")
            print(f"     {p['titulo']}")
    if fora:
        print(f"\nFora ({len(fora)}):")
        for p, motivo in fora[:8]:
            print(f"  {p['canal']:<22} {p['titulo'][:34]:<34} {motivo}")
    # ⚠️ O QUE ESTE SELETOR NAO ENXERGA, e precisa ser dito: RETENCAO. O
    # Buffer nao devolve "assistiram por 2s"; so' o painel de Promover do
    # TikTok mostra. E retencao e' o gargalo MEDIDO deste projeto. Entao esta
    # lista ordena por tracao, que e' a melhor proxy disponivel — nao pela
    # coisa certa.
    print("\n  ⚠️ ordenado por TRACAO (views/h). Retencao nao vem pela API do")
    print("     Buffer — so' aparece no painel do TikTok depois de promover.")


if __name__ == "__main__":
    main()
