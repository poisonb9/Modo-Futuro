# -*- coding: utf-8 -*-
"""Fotografa as views de todo post publicado, de hora em hora.

## POR QUE ISTO PRECISA EXISTIR

O Bryan impulsionou um post do @modofuturo em 01/09/2026 e levantou uma
duvida que corre solta por ai': "ouvi dizer que depois que faz isso o TikTok
para de entregar, pra fazer a gente ficar comprando".

⚠️ ISSO E' INVERIFICAVEL COM UMA FOTO. Views acumuladas nao dizem QUANDO
chegaram. Sem serie temporal nao da' pra distinguir "parou de entregar" de
"nunca entregou" nem de "entregou tudo no primeiro dia" — e a conclusao
viraria uma questao de fe' sobre onde gastar dinheiro.

Uma leitura por hora resolve: a DERIVADA das views mostra a curva de entrega.
Se a entrega cai a zero depois do impulsionamento, aparece. Se nao cai,
tambem.

⚠️ E PRECISA DE GRUPO DE CONTROLE. Por isso registra TODOS os canais e TODOS
os posts, nao so' o impulsionado. Se a entrega do @modofuturo cair enquanto
os outros seguem, e' sinal; se cair em todos, foi outra coisa.

## O ATRASO DA METRICA, MEDIDO

A `metrics` do Buffer atrasa, e o atraso encolhe com a idade do post
(comparacao print x API em 01/09):

    2,7h -> a API mostrava 49% do real     22,6h -> 99%
    7,6h -> 56%                            26,6h+ -> 100%

⚠️ Entao a curva das primeiras horas E' SUBESTIMADA, e comparar post novo com
post velho pelo valor absoluto engana. O que este arquivo guarda e' a leitura
CRUA com a hora — corrigir depois e' possivel; inventar dado que nao foi
gravado, nao.
"""
from __future__ import annotations

import io
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent / "desempenho.jsonl"
CRED = r"C:/Users/Administrator/Desktop/Tiktok/CREDENCIAIS.md"

CANAIS = {
    "modofuturo": ("6a6ca3c3aba3767824bf6234", "6a6cd9d54b2d03035f771631", "BUFFER_TOKEN"),
    "cozinha.internacional": ("6a90dddb9bb05f07b058e9bc", "6a90de80ccaf649a672ebe15", "BUFFER_TOKEN_COZINHA"),
    "semanestesia.pod": ("6a937e2ccae8f6fdedefa317", "6a938ce8065799be46508cc6", "BUFFER_TOKEN_SEMANESTESIA"),
    "atefalhar": ("6a94a9f9ca5d8883aa924198", "6a94aaf5065799be46581e1d", "BUFFER_TOKEN_ATEFALHAR"),
    "truque.importado": ("6a94c752e0b1602e8c5cf1ae", "6a94c8f3065799be465981f6", "BUFFER_TOKEN_TRUQUEIMPORTADO"),
}
Q = """query($i: PostsInput!){ posts(input:$i){ edges{ node{ id text sentAt
      metricsUpdatedAt metrics{ name value } } } } }"""


def _tokens() -> dict:
    t = {k: v for k in CANAIS if (v := os.environ.get(CANAIS[k][2], "").strip())}
    if len(t) == len(CANAIS) or not os.path.exists(CRED):
        return t
    for l in io.open(CRED, encoding="utf-8").read().splitlines():
        m = re.match(r"\|\s*@([\w.]+)\s*\|\s*`([^`]+)`\s*\|", l)
        if m and len(m.group(2)) > 30:
            t.setdefault(m.group(1), m.group(2))
    return t


def canal_vale_a_pena(canal: str, hora: int) -> bool:
    """Este canal precisa ser lido AGORA, ou pode esperar?

    ⚠️ O ORCAMENTO DA API E' REAL. Medido em 01/09/2026: cada canal e' uma
    conta Buffer separada, com 250 requisicoes/24h (nosso teto: 200). A foto
    de hora em hora sozinha consome 24 — 62% de todo o uso do canal.

    A regra: enquanto o canal tem post COM MENOS DE 72h, le' de hora em hora,
    porque e' ai' que a curva de entrega muda. Passado isso, as views ficam
    praticamente paradas e uma leitura a cada 6 horas ja' registra o mesmo.

    ⚠️ MAS NUNCA PARA DE LER. Se a regra fosse so' "pula canal velho", um
    canal que publicasse de novo ficaria invisivel pra sempre — o arquivo
    continuaria dizendo que o post mais novo tem 200 horas. Por isso o piso de
    6 em 6 horas, que sempre reencontra o canal.
    """
    if hora % 6 == 0:
        return True
    if not ARQUIVO.exists():
        return True
    mais_novo = None
    try:
        for linha in io.open(ARQUIVO, encoding="utf-8"):
            d = json.loads(linha)
            if d.get("canal") != canal or not d.get("publicado_em"):
                continue
            q = d["publicado_em"]
            if mais_novo is None or q > mais_novo:
                mais_novo = q
    except Exception:
        return True
    if mais_novo is None:
        return True
    idade = (datetime.now(timezone.utc)
             - datetime.fromisoformat(mais_novo.replace("Z", "+00:00"))
             ).total_seconds() / 3600
    return idade < 72


def main() -> None:
    tok = _tokens()
    hora = datetime.now(timezone.utc).hour
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    novas = 0
    with io.open(ARQUIVO, "a", encoding="utf-8", newline="\n") as f:
        for canal, (org, ch, _env) in CANAIS.items():
            t = tok.get(canal)
            if not t:
                print(f"  {canal}: sem token")
                continue
            if not canal_vale_a_pena(canal, hora):
                print(f"  {canal}: pulado (nada novo ha' 72h; le' de 6 em 6h)")
                continue
            try:
                req = urllib.request.Request(
                    "https://api.buffer.com/",
                    data=json.dumps({"query": Q, "variables": {"i": {
                        "organizationId": org,
                        "filter": {"status": ["sent"],
                                   "channelIds": [ch]}}}}).encode(),
                    headers={"Authorization": f"Bearer {t}",
                             "Content-Type": "application/json"})
                d = json.load(urllib.request.urlopen(req, timeout=60))
                ns = [e["node"] for e in d["data"]["posts"]["edges"]]
            except Exception as e:
                # ⚠️ Falha ABERTA por canal: um token recusado nao pode
                # impedir a foto dos outros quatro. Buraco num canal e' menos
                # grave que buraco em todos.
                print(f"  {canal}: Buffer recusou ({str(e)[:50]})")
                continue
            for n in ns:
                if not n.get("sentAt"):
                    continue
                m = {x["name"]: x["value"] for x in (n.get("metrics") or [])}
                f.write(json.dumps({
                    "lido_em": agora, "canal": canal, "post_id": n["id"],
                    "titulo": n["text"].splitlines()[0][:80],
                    "publicado_em": n["sentAt"],
                    "metricas_de": n.get("metricsUpdatedAt"),
                    "views": m.get("Views"), "reach": m.get("Reach"),
                    "curtidas": m.get("Reactions"),
                    "comentarios": m.get("Comments"),
                    "shares": m.get("Shares"),
                }, ensure_ascii=False) + "\n")
                novas += 1
            print(f"  {canal}: {len(ns)} post(s) fotografados")
    print(f"  +{novas} leituras em {ARQUIVO.name}")


if __name__ == "__main__":
    main()
