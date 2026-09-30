# -*- coding: utf-8 -*-
"""Muda o horario dos posts de oferta ja' agendados no Buffer (editPost).

30/09/2026 19:12 UTC — pedido do dono: "publica agora daqui 5 minutos" o #1
de cada canal, e encadear os outros. So' mexe em post `scheduled` cujo texto
comeca com "Achado do dia #N" — nada e' criado, nada e' apagado.

    python ferramentas/mover_ofertas.py --itens "fatura.chora:1@@2026-09-30 16:20||..."
    (hora de SAO PAULO; --simular so' lista)
"""
import argparse, datetime, os, re, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import agendar_buffer as ab  # noqa: E402
from engine import canais_registro as cr  # noqa: E402

import json  # noqa: E402
FEITAS = [json.loads(l) for l in (RAIZ / "estado" / "ofertas_feitas.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

M = """mutation($input: EditPostInput!) { editPost(input: $input) { __typename
  ... on PostActionSuccess { post { id dueAt } } ... on InvalidInputError { message }
  ... on UnexpectedError { message } ... on RestProxyError { message } } }"""


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--itens", required=True)
    p.add_argument("--simular", action="store_true")
    a = p.parse_args()
    pedidos: dict[str, dict[int, str]] = {}
    for it in [i.strip() for i in a.itens.split("||") if i.strip()]:
        alvo, quando = it.split("@@")
        canal, n = alvo.split(":")
        pedidos.setdefault(canal.strip(), {})[int(n)] = quando.strip()
    falhou = False
    for canal, nums in pedidos.items():
        c = cr.CANAIS[canal]
        tok = (os.environ.get(c.env) or "").strip()
        os.environ["CANAL_ESPERADO"] = canal
        _, cid, posts = ab.contexto_buffer(tok, fresco=True)
        for x in posts:
            m = re.match(r"\s*Achado do dia #(\d+)", x.get("text") or "")
            print(f"  {canal}: {x.get('status')} {x.get('dueAt')} {(x.get('text') or '')[:50]!r}")
            if not m or int(m.group(1)) not in nums or x.get("status") != "scheduled":
                continue
            q = datetime.datetime.strptime(nums.pop(int(m.group(1))), "%Y-%m-%d %H:%M")
            due = (q + datetime.timedelta(hours=ab.FUSO_SP_H)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            if a.simular:
                print(f"    SIMULADO -> {due}")
                continue
            # ⚠️ o editPost EXIGE texto e video de novo (InvalidInputError sem eles)
            n = int(m.group(1))
            f = next(f for f in reversed(FEITAS) if f["canal"] == canal and f.get("numero") == n)
            url = (f"https://github.com/poisonb9/Modo-Futuro/releases/download/ofertas-{f['dia'][:7]}/"
                   f"{f['dia']}_{canal.replace('.', '-')}_{f['id']}.mp4")
            titulo = (x.get("text") or "").splitlines()[0][:90]
            d = ab.consultar(tok, M, {"input": {"id": x["id"], "dueAt": due, "text": x.get("text"),
                                                "mode": "customScheduled", "schedulingType": "automatic",
                                                "assets": [{"video": {"url": url}}],
                                                "metadata": {"tiktok": {"isAiGenerated": True, "title": titulo}}}})["editPost"]
            ok = d["__typename"] == "PostActionSuccess"
            falhou |= not ok
            print(f"    {'movido' if ok else '[!] FALHOU'} #{m.group(1)} -> {d.get('post', {}).get('dueAt') if ok else d}")
        for n in nums:
            print(f"  [!] {canal} #{n}: nao achei agendado")
            falhou = True
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()
