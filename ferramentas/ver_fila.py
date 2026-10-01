# -*- coding: utf-8 -*-
"""SO' LE a fila do Buffer de UM canal: agendados, enviados, com erro e rascunhos.

01/10/2026 (dono: "olha a fila, vamos investigar o problema desse canal" — o
@semanestesia.pod parou de publicar). Nada e' criado, movido ou apagado.

    python ferramentas/ver_fila.py --canal semanestesia.pod
"""
import argparse, datetime, os, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import agendar_buffer as ab  # noqa: E402
from engine import canais_registro as cr  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--canal", required=True)
a = p.parse_args()
c = cr.CANAIS[cr.canonico(a.canal)]
tok = (os.environ.get(c.env) or "").strip()
if not tok:
    sys.exit(f"secret {c.env} nao chegou")
org = ab.consultar(tok, "query { account { organizations { id } } }")["account"]["organizations"][0]["id"]
chs = ab.consultar(tok, """query($i: ChannelsInput!) { channels(input: $i) { id service name isDisconnected isLocked } }""",
                   {"i": {"organizationId": org}})["channels"]
print("canais na conta:", chs)
tk = [x for x in chs if x["service"] == "tiktok"]
for st in (["error"], ["scheduled"], ["sent"], ["draft"]):
    try:
        d = ab.consultar(tok, """query($i: PostsInput!) { posts(input: $i, first: 30) {
            edges { node { id status dueAt sentAt error { message } text } } } }""",
            {"i": {"organizationId": org, "filter": {"status": st, "channelIds": [tk[0]["id"]]}}})
    except Exception as e:  # noqa: BLE001
        print(st, "falhou:", str(e)[:300]); continue
    nos = [e["node"] for e in d["posts"]["edges"]]
    print(f"\n== {st[0]}: {len(nos)}")
    for n in sorted(nos, key=lambda n: n.get("dueAt") or "")[-15:]:
        print(f"  {n.get('dueAt')} sent={n.get('sentAt')} err={(n.get('error') or {}).get('message')} | {(n.get('text') or '')[:60]!r}")
