# -*- coding: utf-8 -*-
"""Muda o horario de UM post agendado (clipe do motor) no Buffer.

02/10/2026 (dono: "o primeiro pode sair agora, nos proximos 5 minutos").
Acha o post `scheduled` pelo horario atual (UTC, AAAA-MM-DDTHH:MM), acha o
video dele no manifesto das releases (o editPost exige texto E video de novo)
e remarca. `--em-min N` = daqui a N..N+3 min, segundo aleatorio.

    python ferramentas/mover_agendado.py --canal camarim.kpop --de 2026-10-02T19:34 --em-min 5 [--simular]
"""
import argparse, datetime, os, random, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import agendar_buffer as ab  # noqa: E402
from engine import canais_registro as cr  # noqa: E402

M = """mutation($input: EditPostInput!) { editPost(input: $input) { __typename
  ... on PostActionSuccess { post { id dueAt } } ... on InvalidInputError { message }
  ... on UnexpectedError { message } ... on RestProxyError { message } } }"""

p = argparse.ArgumentParser()
p.add_argument("--canal", required=True)
p.add_argument("--de", required=True)
p.add_argument("--em-min", type=int, default=5)
p.add_argument("--simular", action="store_true")
a = p.parse_args()
c = cr.CANAIS[cr.canonico(a.canal)]
tok = (os.environ.get(c.env) or "").strip()
os.environ["CANAL_ESPERADO"] = c.nome_buffer
_, _cid, posts = ab.contexto_buffer(tok, fresco=True)
alvo = next((x for x in posts if x.get("status") == "scheduled" and (x.get("dueAt") or "")[:16] == a.de), None)
if not alvo:
    sys.exit(f"nenhum agendado em {a.de}")
texto = alvo.get("text") or ""
print("post:", texto[:70])
man = ab.manifesto(os.environ["GH_TOKEN"])
ini = texto.strip()[:60]
clipe = next((v for v in man.values()
              if cr.canonico(v.get("canal")) == c.nome_buffer
              and ini and ((v.get("legenda") or "").strip().startswith(ini[:40])
                           or ini.startswith((v.get("titulo") or "#").strip()[:40]))), None)
if not clipe:
    sys.exit("[!] nao achei o video desse post no manifesto")
quando = datetime.datetime.utcnow() + datetime.timedelta(minutes=a.em_min + random.randint(0, 3),
                                                          seconds=random.randint(1, 58))
due = quando.strftime("%Y-%m-%dT%H:%M:%S.000Z")
print("video:", clipe["url"][-70:], "->", due)
if a.simular:
    sys.exit(0)
titulo = (clipe.get("titulo") or texto.split("#")[0]).strip()[:90]
d = ab.consultar(tok, M, {"input": {"id": alvo["id"], "dueAt": due, "text": texto,
                                    "mode": "customScheduled", "schedulingType": "automatic",
                                    "assets": [{"video": {"url": clipe["url"]}}],
                                    "metadata": {"tiktok": {"isAiGenerated": True, "title": titulo}}}})["editPost"]
print(d)
sys.exit(0 if d["__typename"] == "PostActionSuccess" else 1)
