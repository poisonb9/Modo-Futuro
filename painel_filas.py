# -*- coding: utf-8 -*-
"""O panorama das filas dos 5 canais, numa tabela so'.

O Bryan pediu isto em 01/09/2026 e gostou do formato: um canal por linha,
quantos posts, ate' quando, e quantas horas de folga.

## A META DAS 50 HORAS — AINDA NAO E' REGRA

Na mesma conversa ele disse: "vamos tentar manter todos os canais com mais de
50h de cortes, MAS depois que estiver tudo 100% validado e estivermos
gostando dos videos".

⚠️ ENTAO O PAINEL SO' MOSTRA A DISTANCIA ATE' A META. Ele nao enfileira nada
por conta disso, e o `repor_fila` continua com o piso de 5 posts. Encher cinco
canais ate' 50h agora significaria despejar dezenas de clipes que o Bryan
ainda nao aprovou — e o que ele quer validar e' justamente a qualidade.

Quando ele disser que gostou, e' trocar META_HORAS por piso de verdade no
repor_fila. Ate' la', o numero serve pra ele enxergar o quanto falta.

⚠️ E A FOLGA NAO E' QUALIDADE. Um canal com 50h de fila pode estar cheio de
clipe ruim. A tabela mede sobrevida, nao acerto — por isso a coluna de meta
diz "falta", nunca "ok".
"""
from __future__ import annotations

import datetime
import io
import json
import os
import re
import urllib.request

API = "https://api.buffer.com/"
META_HORAS = 50          # alvo do Bryan, ainda NAO aplicado automaticamente

CANAIS = [
    ("@modofuturo",            "6a6ca3c3aba3767824bf6234", "6a6cd9d54b2d03035f771631", "modofuturo"),
    ("@truque.importado",      "6a94c752e0b1602e8c5cf1ae", "6a94c8f3065799be465981f6", "truque.importado"),
    ("@cozinha.internacional", "6a90dddb9bb05f07b058e9bc", "6a90de80ccaf649a672ebe15", "cozinha.internacional"),
    ("@semanestesia.pod",      "6a937e2ccae8f6fdedefa317", "6a938ce8065799be46508cc6", "semanestesia.pod"),
    ("@atefalhar",             "6a94a9f9ca5d8883aa924198", "6a94aaf5065799be46581e1d", "atefalhar"),
]
Q = "query($i: PostsInput!){ posts(input:$i){ edges{ node{ dueAt } } } }"

# O token de cada canal: variavel de ambiente na nuvem, CREDENCIAIS.md no
# disco do Bryan. ⚠️ O arquivo NAO vive em repositorio nenhum, de proposito.
ENV = {"modofuturo": "BUFFER_TOKEN",
       "cozinha.internacional": "BUFFER_TOKEN_COZINHA",
       "semanestesia.pod": "BUFFER_TOKEN_SEMANESTESIA",
       "atefalhar": "BUFFER_TOKEN_ATEFALHAR",
       "truque.importado": "BUFFER_TOKEN_TRUQUEIMPORTADO"}
CRED = r"C:/Users/Administrator/Desktop/Tiktok/CREDENCIAIS.md"


def _tokens() -> dict:
    t = {k: v for k in ENV if (v := os.environ.get(ENV[k], "").strip())}
    if len(t) == len(ENV) or not os.path.exists(CRED):
        return t
    for l in io.open(CRED, encoding="utf-8").read().splitlines():
        m = re.match(r"\|\s*@([\w.]+)\s*\|\s*`([^`]+)`\s*\|", l)
        if m and len(m.group(2)) > 30:
            t.setdefault(m.group(1), m.group(2))
    return t


def fila(token: str, org: str, canal: str) -> list[str]:
    req = urllib.request.Request(
        API, data=json.dumps({"query": Q, "variables": {"i": {
            "organizationId": org,
            "filter": {"status": ["scheduled"], "channelIds": [canal]}}}}).encode(),
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if not d.get("data"):
        raise RuntimeError(json.dumps(d.get("errors"))[:120])
    return sorted(e["node"]["dueAt"] for e in d["data"]["posts"]["edges"])


def montar() -> str:
    tok = _tokens()
    agora = datetime.datetime.now(datetime.timezone.utc)
    linhas, total, faltando = [], 0, []
    for nome, org, ch, chave in CANAIS:
        t = tok.get(chave)
        if not t:
            linhas.append(f"  {nome:<24}  ?   sem token")
            continue
        try:
            ds = fila(t, org, ch)
        except Exception as e:
            linhas.append(f"  {nome:<24}  ?   Buffer recusou ({str(e)[:34]})")
            continue
        total += len(ds)
        if not ds:
            linhas.append(f"  {nome:<24} {len(ds):>2}   VAZIA")
            faltando.append((nome, 0.0))
            continue
        fim = datetime.datetime.fromisoformat(ds[-1].replace("Z", "+00:00"))
        h = (fim - agora).total_seconds() / 3600
        sp = fim - datetime.timedelta(hours=3)
        linhas.append(f"  {nome:<24} {len(ds):>2}   ate' {sp:%d/%m %H:%M}  "
                      f"(+{h:.0f}h)")
        if h < META_HORAS:
            faltando.append((nome, h))
    saida = ["Filas dos canais (horario de Sao Paulo)", ""] + linhas
    saida.append("")
    saida.append(f"  TOTAL agendado: {total} posts")
    if faltando:
        # ⚠️ Informativo. A meta so' vira piso quando o Bryan validar os
        # videos — ver o cabecalho.
        saida.append("")
        saida.append(f"  meta de {META_HORAS}h (ainda nao aplicada): "
                     + ", ".join(f"{n.lstrip('@')} faltam {META_HORAS - h:.0f}h"
                                 for n, h in faltando))
    return "\n".join(saida)


if __name__ == "__main__":
    print(montar())
