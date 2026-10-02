# -*- coding: utf-8 -*-
"""Apaga posts AGENDADOS de um canal no Buffer, escolhidos pelo horario (UTC).

02/10/2026 (dono): dois cortes do @camarim.kpop rodaram juntos e os dois
agendaram os MESMOS clipes (duplicata) e posts a 3 min um do outro. So' apaga
post `scheduled` cujo dueAt bate EXATO com um dos pedidos. Nada e' criado.

    python ferramentas/apagar_agendados.py --canal camarim.kpop --horarios "2026-10-02T22:45||..." [--simular]
"""
import argparse, os, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import agendar_buffer as ab  # noqa: E402
from engine import canais_registro as cr  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--canal", required=True)
p.add_argument("--horarios", required=True, help="AAAA-MM-DDTHH:MM em UTC, separados por ||")
p.add_argument("--simular", action="store_true")
a = p.parse_args()
alvos = {h.strip() for h in a.horarios.split("||") if h.strip()}
c = cr.CANAIS[cr.canonico(a.canal)]
tok = (os.environ.get(c.env) or "").strip()
if not tok:
    sys.exit(f"secret {c.env} nao chegou")
os.environ["CANAL_ESPERADO"] = c.nome_buffer
_, _cid, posts = ab.contexto_buffer(tok, fresco=True)
falhou = False
for x in posts:
    due = (x.get("dueAt") or "")[:16]
    if x.get("status") != "scheduled" or due not in alvos:
        continue
    alvos.discard(due)
    print(f"  {due} {(x.get('text') or '')[:60]!r}")
    if a.simular:
        print("    SIMULADO -> apagar"); continue
    d = ab.consultar(tok, 'mutation { deletePost(input: {id: "%s"}) { __typename } }' % x["id"])["deletePost"]
    ok = "Success" in d["__typename"]
    falhou |= not ok
    print(f"    {'APAGADO' if ok else '[!] FALHOU'} -> {d}")
for h in alvos:
    print(f"  [!] {h}: nenhum agendado nesse horario")
sys.exit(1 if falhou else 0)
