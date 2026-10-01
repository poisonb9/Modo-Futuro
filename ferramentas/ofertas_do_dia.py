# -*- coding: utf-8 -*-
"""Gera os videos de oferta do dia (Pago Menos + achadinhos.instantaneos).

    python -X utf8 ferramentas/ofertas_do_dia.py --pasta saida/      gera e sobe na release
    python -X utf8 ferramentas/ofertas_do_dia.py --pasta saida/ --ensaio   so' diz o que faria

Roda na NUVEM (workflow `ofertas.yml`).
⭐ 30/09/2026: com `--agendar` (so' junto de `--registrar`) cada video entra
na fila do Buffer DO SEU CANAL — token pelo `env` do canais_registro
(PAGOMENOS, ACHADINHOSINSTANTANEOS, ACHADINHOTOTAL), guarda CANAL_ESPERADO
(aborta se o token abrir outra conta) e grade do agendar_buffer (4/dia,
intervalo minimo 3 h). Sem `--agendar` nada vai ao Buffer.

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


REPO = "poisonb9/Modo-Futuro"


def conferir_buffer(canais: list[str]) -> None:
    """So' LE: o secret de cada canal chegou e abre o canal certo no Buffer?
    Roda no ensaio, pra o dia de ligar nao ter surpresa. Nada e' agendado."""
    import os
    import agendar_buffer as ab
    from engine import canais_registro as cr
    for canal in canais:
        c = cr.CANAIS[canal]
        token = (os.environ.get(c.env) or "").strip()
        if not token:
            print(f"  buffer {canal}: secret {c.env} AUSENTE")
            continue
        os.environ["CANAL_ESPERADO"] = canal
        try:
            _, cid, posts = ab.contexto_buffer(token, fresco=True)
            fila = sum(1 for x in posts if x.get("status") != "sent")
            print(f"  buffer {canal}: OK (canal {cid}, {fila} na fila)")
        except SystemExit as e:
            print(f"  buffer {canal}: ERRO {str(e)[:120]}")
        except Exception as e:  # noqa: BLE001
            print(f"  buffer {canal}: ERRO {type(e).__name__}: {str(e)[:120]}")


def _espalhar(h, usados: set) -> "datetime":
    """Desloca o horario do slot em -20..+20 min e segundo aleatorio, sem
    repetir o MINUTO de outro post ja' marcado nesta rodada (qualquer canal)."""
    import random
    from datetime import timedelta
    for _ in range(200):
        q = h + timedelta(minutes=random.randint(-20, 20), seconds=random.randint(1, 58))
        if not any(abs((q - u).total_seconds()) < 180 for u in usados):
            usados.add(q)
            return q
    return h


def agendar(por_canal: dict[str, list[dict]]) -> None:
    """Cada video na fila do Buffer do SEU canal. Um canal que falha nao
    derruba os outros — mas a falha aparece (exit 1 no fim)."""
    import os
    import agendar_buffer as ab
    from engine import canais_registro as cr
    falhou = []
    usados: set = set()        # horarios ja' marcados (todos os canais)
    for canal, posts in por_canal.items():
        c = cr.CANAIS[canal]
        token = (os.environ.get(c.env) or "").strip()
        if not token:
            print(f"  [!] {canal}: secret {c.env} nao chegou ao ambiente — nada agendado")
            falhou.append(canal)
            continue
        os.environ["CANAL_ESPERADO"] = canal          # guarda de canal errado
        try:
            _, canal_id, conhecidos = ab.contexto_buffer(token, fresco=True)
            agendados = [x for x in conhecidos if x.get("status") != "sent"]
            horas = ab.proximos_horarios(agendados, len(posts), conhecidos)
            # ⭐ 30/09/2026 (dono): "minutos aleatorios, sem bater nenhum canal
            # postando junto no mesmo minuto e segundo" — pra nao parecer bot.
            horas = [_espalhar(h, usados) for h in horas]
            for post, h in zip(posts, horas):
                quando = ab.enfileirar(token, canal_id, post, simular=False, quando_sp=h)
                print(f"  📅 {canal}: {post['titulo'][:60]} -> {quando}")
        except SystemExit as e:
            print(f"  [!] {canal}: {e}")
            falhou.append(canal)
        except Exception as e:  # noqa: BLE001
            print(f"  [!] {canal}: {type(e).__name__}: {str(e)[:160]}")
            falhou.append(canal)
    if falhou:
        sys.exit(f"agendamento falhou em: {', '.join(falhou)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", type=Path, required=True)
    ap.add_argument("--ensaio", action="store_true")
    # ⚠️ SEM --registrar os videos sao PREVIA: sobem na release, mas nao entram
    # em ofertas_feitas nem na pagina da bio. Registrar = o video VAI AO AR
    # (senao a bio diria "do video de hoje" de um video que ninguem viu).
    ap.add_argument("--registrar", action="store_true")
    ap.add_argument("--agendar", action="store_true",
                    help="poe cada video na fila do Buffer do canal (exige --registrar)")
    # 01/10/2026 (dono: "publica 1 para analisarmos"): so' estes ids (virgula)
    ap.add_argument("--so", default="")
    a = ap.parse_args()
    if a.agendar and not a.registrar:
        sys.exit("--agendar exige --registrar: post no ar sem registro quebra a pagina da bio")
    para_agendar: dict[str, list[dict]] = {}
    a.pasta.mkdir(parents=True, exist_ok=True)
    hoje = date.today()
    tag = f"ofertas-{hoje:%Y-%m}"
    escolha = ofertas.do_dia(hoje)
    if a.so:
        so = {x.strip() for x in a.so.split(",") if x.strip()}
        escolha = {c: [o for o in v if str(o["id"]) in so] for c, v in escolha.items()}
        escolha = {c: v for c, v in escolha.items() if v}
    # ⭐ o link de afiliado (com o nosso tracking) vem do garimpo, gravado em
    # produtos_publicados.jsonl — o que esta' no git. O `site_no_ar/links.json`
    # e' so' backup do ar e fica velho no repositorio.
    links: dict[str, str] = {}
    for l in (RAIZ / "estado" / "produtos_publicados.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            x = json.loads(l)
        except ValueError:
            continue
        if x.get("id") and str(x.get("link", "")).startswith("https://s.click.aliexpress.com/"):
            links[str(x["id"])] = x["link"]
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))
    total = sum(len(v) for v in escolha.values())
    print(f"{hoje}: {total} oferta(s) passaram em todas as guardas")
    if a.ensaio or not total:
        for c, os_ in escolha.items():
            for o in os_:
                print(f"  {c}: -{o['queda']:.0%} {o['nome']} R$ {o['agora']:.2f}")
        if a.ensaio:
            conferir_buffer(list(escolha))
        return
    subprocess.run(["gh", "release", "view", tag], capture_output=True) .returncode == 0 or \
        subprocess.run(["gh", "release", "create", tag, "--title", tag, "--notes",
                        "videos de oferta (Pago Menos / instantaneos)"], check=True)
    comentarios = []
    for canal, os_ in escolha.items():
        n = video_oferta.proximo_numero(canal)
        for o in os_:
            if o["id"] not in links:
                print(f"  [!] {o['id']} sem link de afiliado — pulado")
                continue
            arq = a.pasta / f"{hoje}_{canal.replace('.', '-')}_{o['id']}.mp4"
            try:
                d = video_oferta.gerar(o["id"], arq, canal, n)
            except Exception as e:  # noqa: BLE001 — um produto nao derruba o dia
                print(f"  [!] {o['id']}: {type(e).__name__}: {str(e)[:120]}")
                continue
            subprocess.run(["gh", "release", "upload", tag, str(arq), "--clobber"], check=True)
            o["comentario"] = d["comentario"]
            o["numero"] = d["numero"]
            n += 1
            comentarios.append(f"{arq.name}\n  comentario fixado: {d['comentario']}")
            print(f"  ok {canal} #{d['numero']}: {o['nome']} -> {arq.name}")
            if not a.registrar:
                continue
            para_agendar.setdefault(canal, []).append({
                "url": f"https://github.com/{REPO}/releases/download/{tag}/{arq.name}",
                "legenda": d["legenda"], "titulo": f"Achado do dia #{d['numero']}: {o['nome']}"[:90]})
            ofertas.registrar(canal, o, hoje)
            with open(RAIZ / "estado" / "produtos_publicados.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": o["id"], "nome": o["nome"], "canal": canal, "onde": "video_oferta",
                    "preco": video_oferta.reais(o["agora"]), "link": links[o["id"]],
                    "imagem": (agora[o["id"]].get("imagens") or [""])[0],
                    "vendas": o["vendas"], "fonte": "aliexpress",
                    "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }, ensure_ascii=False) + "\n")


    if a.agendar:
        agendar(para_agendar)

    if comentarios:
        txt = a.pasta / f"{hoje}_comentarios_fixados.txt"
        txt.write_text("\n\n".join(comentarios) + "\n", encoding="utf-8")
        subprocess.run(["gh", "release", "upload", tag, str(txt), "--clobber"], check=True)


if __name__ == "__main__":
    main()
