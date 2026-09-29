# -*- coding: utf-8 -*-
"""Gera os videos de oferta do dia (Pago Menos + achadinhos.instantaneos).

    python -X utf8 ferramentas/ofertas_do_dia.py --pasta saida/      gera e sobe na release
    python -X utf8 ferramentas/ofertas_do_dia.py --pasta saida/ --ensaio   so' diz o que faria

Roda na NUVEM (workflow `ofertas.yml`). ⛔ NAO AGENDA NADA: os dois canais
ainda nao tem Buffer (canais_registro, motor=False) e o dono ve' a previa
antes de ligar. Quando ligar, o agendamento entra aqui — 4 por canal por dia.

Cada video gerado:
  - sobe na release `ofertas-AAAA-MM` (nome = canal + id + dia);
  - entra em `estado/ofertas_feitas.jsonl` (nao repete por 21 dias);
  - entra em `estado/produtos_publicados.jsonl` com o canal, para a pagina
    da bio mostrar o MESMO produto no topo ("🎬 do video de hoje").
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "ferramentas"))
from engine import ofertas  # noqa: E402
import video_oferta  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", type=Path, required=True)
    ap.add_argument("--ensaio", action="store_true")
    a = ap.parse_args()
    a.pasta.mkdir(parents=True, exist_ok=True)
    hoje = date.today()
    tag = f"ofertas-{hoje:%Y-%m}"
    escolha = ofertas.do_dia(hoje)
    links = json.load(open(RAIZ / "site_no_ar" / "links.json", encoding="utf-8"))
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))
    total = sum(len(v) for v in escolha.values())
    print(f"{hoje}: {total} oferta(s) passaram em todas as guardas")
    if a.ensaio or not total:
        for c, os_ in escolha.items():
            for o in os_:
                print(f"  {c}: -{o['queda']:.0%} {o['nome']} R$ {o['agora']:.2f}")
        return
    subprocess.run(["gh", "release", "view", tag], capture_output=True) .returncode == 0 or \
        subprocess.run(["gh", "release", "create", tag, "--title", tag, "--notes",
                        "videos de oferta (Pago Menos / instantaneos)"], check=True)
    for canal, os_ in escolha.items():
        for o in os_:
            if o["id"] not in links:
                print(f"  [!] {o['id']} sem link de afiliado — pulado")
                continue
            arq = a.pasta / f"{hoje}_{canal.replace('.', '-')}_{o['id']}.mp4"
            try:
                video_oferta.gerar(o["id"], arq)
            except Exception as e:  # noqa: BLE001 — um produto nao derruba o dia
                print(f"  [!] {o['id']}: {type(e).__name__}: {str(e)[:120]}")
                continue
            subprocess.run(["gh", "release", "upload", tag, str(arq), "--clobber"], check=True)
            ofertas.registrar(canal, o, hoje)
            with open(RAIZ / "estado" / "produtos_publicados.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": o["id"], "nome": o["nome"], "canal": canal, "onde": "video_oferta",
                    "preco": video_oferta.reais(o["agora"]), "link": links[o["id"]],
                    "imagem": (agora[o["id"]].get("imagens") or [""])[0],
                    "vendas": o["vendas"], "fonte": "aliexpress",
                    "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }, ensure_ascii=False) + "\n")
            print(f"  ok {canal}: {o['nome']} -> {arq.name}")


if __name__ == "__main__":
    main()
