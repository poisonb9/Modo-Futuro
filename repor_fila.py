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

⚠️ CANAIS EM ESTREIA FICAM DE FORA — mas HOJE NAO HA' NENHUM. Quem manda
nisso e' `engine/estreia.py`, cujo `ESTREIA_ATE` esta' VAZIO desde 01/09/2026:
o Bryan liberou @truque.importado, @atefalhar e @semanestesia.pod, e
reconfirmou em 02/09 ("liberado, pode postar assim que encher").

O motivo da trava continua valendo pro PROXIMO canal novo: uma estreia
automatica ja' flopou, e o Bryan posta os primeiros na mao por 2 dias. Canal
novo entra no `ESTREIA_ATE` com data e destrava sozinho.

⚠️ Este paragrafo dizia "so' o @modofuturo e a cozinha entram aqui" ate'
02/09/2026 — e estava MENTINDO havia um dia, porque o `LIBERADOS` abaixo ja'
tinha os quatro canais com `repoe: True`. Comentario que contradiz o codigo
custa mais caro que comentario nenhum: manda a proxima sessao procurar uma
trava que nao existe. Ver LIBERADOS.

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

from engine import canais_registro as _cr

RAIZ = Path(__file__).resolve().parent
API = "https://api.buffer.com/"

# ⚠️ So' entra aqui canal que o Bryan JA' LIBEROU pro automatico. Acrescentar
# um canal em estreia faz o primeiro video sair sozinho — exatamente o que ele
# pediu pra nao acontecer.
# ⚠️ Vem do registro desde 04/09/2026. Esta tabela estava copiada em CINCO
# arquivos, e foi a copia que deixou a cozinha com dois nomes. Canal novo se
# acrescenta em engine/canais_registro.py, e SO' la'.
#
# ⚠️ O QUE NAO VEM DO REGISTRO E' O `repoe`, de proposito: quem repoe sozinho
# e' decisao editorial do Bryan, nao propriedade do canal. Acrescentar canal
# ao registro NAO o autoriza a postar sozinho — foi ele que pediu pra nenhum
# canal em estreia sair no automatico.
def _do(nome: str, **extra) -> dict:
    c = _cr.CANAIS[nome]
    return {"env": c.env, "org": c.org, "canal": c.canal_id, **extra}


LIBERADOS = {n: _do(n, repoe=True) for n in _cr.do_motor()}

# Conferidos e relatados, mas NAO repostos por este repositorio.
SO_RELATA = {n: _do(n, nota="motor no repo pipeline")
             for n, c in _cr.CANAIS.items() if not c.motor}

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
