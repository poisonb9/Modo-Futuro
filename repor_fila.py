# -*- coding: utf-8 -*-
"""Confere a fila de cada canal e repoe a que estiver abaixo do piso.

Pedido do Bryan em 31/08/2026: "eu quero eles em uma fila; assim que esses 10
estiverem faltando 5, eu quero que voce preencha a fila de novo. Nao precisa
ficar olhando toda hora — olha uma vez por dia e cheque a fila e reponha ela,
caso tenha videos bons confirmados para rodar".

⚠️ "VIDEOS BONS CONFIRMADOS" E' O QUE ESTA' NO MANIFESTO. Este script NAO
corta video: ele agenda o que ja' foi cortado e publicado numa release. Se nao
houver clipe elegivel, ele AVISA e para. Disparar corte custa runner e e'
decisao do Bryan.

⚠️ CANAIS EM ESTREIA FICAM DE FORA. O Bryan quer postar os DOIS primeiros
videos de @truque.importado, @atefalhar e @semanestesia.pod na mao — ja' teve
estreia automatica que flopou. Enquanto ele nao liberar, so' o @modofuturo e a
cozinha entram aqui. Ver LIBERADOS.

⚠️ A COZINHA NAO E' DESTE REPOSITORIO. O motor dela vive em
bryanaw2121-sketch/pipeline, com manifesto proprio. Este script confere a fila
dela e RELATA, mas quem repoe e' o workflow de la'.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
API = "https://api.buffer.com/"

# ⚠️ So' entra aqui canal que o Bryan JA' LIBEROU pro automatico. Acrescentar
# um canal em estreia faz o primeiro video sair sozinho — exatamente o que ele
# pediu pra nao acontecer.
LIBERADOS = {
    "atefalhar": {
        "env": "BUFFER_TOKEN_ATEFALHAR",
        "org": "6a94a9f9ca5d8883aa924198",
        "canal": "6a94aaf5065799be46581e1d",
        "repoe": True,
    },
    "truque.importado": {
        "env": "BUFFER_TOKEN_TRUQUEIMPORTADO",
        "org": "6a94c752e0b1602e8c5cf1ae",
        "canal": "6a94c8f3065799be465981f6",
        "repoe": True,
    },
    "semanestesia.pod": {
        "env": "BUFFER_TOKEN_SEMANESTESIA",
        "org": "6a937e2ccae8f6fdedefa317",
        "canal": "6a938ce8065799be46508cc6",
        "repoe": True,
    },
    "modofuturo": {
        "env": "BUFFER_TOKEN",
        "org": "6a6ca3c3aba3767824bf6234",
        "canal": "6a6cd9d54b2d03035f771631",
        "repoe": True,
    },
}

# Conferidos e relatados, mas NAO repostos por este repositorio.
SO_RELATA = {
    "cozinha.importada": {
        "env": "BUFFER_TOKEN_COZINHA",
        "org": "6a90dddb9bb05f07b058e9bc",
        "canal": "6a90de80ccaf649a672ebe15",
        "nota": "motor no repo pipeline",
    },
}

Q = ("query($i: PostsInput!){ posts(input:$i){ edges{ node{ dueAt } } } }")


def fila(token: str, org: str, canal: str) -> list[str] | None:
    """Datas dos posts agendados, ou None se o token nao responder."""
    if not token:
        return None
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": Q, "variables": {"i": {
            "organizationId": org,
            "filter": {"status": ["scheduled"], "channelIds": [canal]}}}}).encode(),
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=60))
    except Exception as e:
        print(f"    [!] Buffer nao respondeu: {str(e)[:70]}")
        return None
    if "errors" in d:
        print(f"    [!] Buffer recusou: {json.dumps(d['errors'])[:110]}")
        return None
    return sorted(e["node"]["dueAt"] for e in d["data"]["posts"]["edges"]
                  if e["node"].get("dueAt"))


def horizonte(datas: list[str]) -> str:
    if not datas:
        return "fila VAZIA"
    import datetime
    fim = datetime.datetime.fromisoformat(datas[-1].replace("Z", "+00:00"))
    h = (fim - datetime.datetime.now(datetime.timezone.utc)).total_seconds() / 3600
    return f"ate' {datas[-1][:16]} ({h:+.0f}h)"


def main() -> None:
    piso = int(os.environ.get("PISO") or 5)
    pedidos = [c.strip() for c in (os.environ.get("CANAIS") or "").split(",")
               if c.strip()]
    linhas = [f"Fila dos canais (piso {piso})", ""]
    repostos = []

    todos = {**LIBERADOS, **SO_RELATA}
    for nome, cfg in todos.items():
        if pedidos and nome not in pedidos:
            continue
        token = (os.environ.get(cfg["env"]) or "").strip()
        datas = fila(token, cfg["org"], cfg["canal"])
        if datas is None:
            linhas.append(f"  {nome}: sem leitura (token ausente ou recusado)")
            continue
        nota = cfg.get("nota", "")
        linha = f"  {nome}: {len(datas)} na fila, {horizonte(datas)}"
        if nota:
            linha += f"  [{nota}]"
        print(linha)
        linhas.append(linha)

        if not cfg.get("repoe"):
            continue
        if len(datas) >= piso:
            continue

        # ⚠️ CANAL_ESPERADO e' a guarda: o agendar_buffer aborta se o token
        # abrir um canal diferente deste nome.
        print(f"    abaixo do piso — repondo {nome}")
        env = dict(os.environ, CANAL_ESPERADO=nome, BUFFER_TOKEN=token)
        r = subprocess.run([sys.executable, "-X", "utf8", "agendar_buffer.py"],
                           cwd=RAIZ, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        saida = (r.stdout or "") + (r.stderr or "")
        print(saida[-1200:])
        ult = [l for l in saida.splitlines() if "enfileirado" in l]
        linhas.append(f"    -> {ult[-1].strip() if ult else 'sem clipe elegivel'}")
        repostos.append(nome)

    if not repostos:
        linhas.append("")
        linhas.append("Nada reposto. Se algum canal esta' baixo e sem clipe "
                      "elegivel, ele precisa de CORTE novo — este script nao "
                      "dispara corte.")

    Path("relato_fila.txt").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()
