# -*- coding: utf-8 -*-
"""Semana de inauguracao — o que roda NA NUVEM (workflow inauguracao.yml).

30/09/2026 (dono: "monta tudo usando a nuvem no github").
  --teaser "canal@@AAAA-MM-DD HH:MM:SS||..."   gera o teaser de cada canal (voz
        clonada), sobe na release e AGENDA no Buffer do canal na hora dada (SP).
  --refazer "canal:N@@AAAA-MM-DD HH:MM:SS||..." refaz so' o VISUAL (camada de
        festa) do Achado do dia #N ja' agendado — mesmo audio, mesmos dados de
        preco do dia — sobe como _festa.mp4 e troca o video do post (editPost).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "ferramentas"))
import agendar_buffer as ab  # noqa: E402
from engine import canais_registro as cr  # noqa: E402

REPO = "poisonb9/Modo-Futuro"
TAG_TEASER = "inauguracao-2026-09"
LEGENDA_TEASER = ("🎈 Inauguração amanhã às 8h!\n"
                  "Todo dia um achado com o preço conferido de verdade — sem desconto inventado.\n"
                  "Segue o perfil pra não perder 🔔\n"
                  "#achadinhos #promoção #inauguração")


def _gh(*args: str) -> None:
    subprocess.run(["gh", *args], check=True)


def teasers(itens: str) -> bool:
    import teaser_inauguracao as ti
    subprocess.run(["gh", "release", "view", TAG_TEASER], capture_output=True).returncode == 0 or \
        _gh("release", "create", TAG_TEASER, "--title", TAG_TEASER, "--notes", "teasers da inauguracao")
    ok = True
    for it in [i.strip() for i in itens.split("||") if i.strip()]:
        canal, quando = [x.strip() for x in it.split("@@")]
        arq = Path(f"teaser_{canal.replace('.', '-')}.mp4")
        ti.gerar(canal, arq)
        _gh("release", "upload", TAG_TEASER, str(arq), "--clobber")
        tok = (os.environ.get(cr.CANAIS[canal].env) or "").strip()
        os.environ["CANAL_ESPERADO"] = canal
        _, cid, _ = ab.contexto_buffer(tok, fresco=True)
        q = datetime.datetime.strptime(quando, "%Y-%m-%d %H:%M:%S")
        try:
            r = ab.enfileirar(tok, cid, {"url": f"https://github.com/{REPO}/releases/download/{TAG_TEASER}/{arq.name}",
                                         "legenda": LEGENDA_TEASER, "titulo": "Inauguração amanhã às 8h!"},
                              simular=False, quando_sp=q)
            print(f"  📅 teaser {canal} -> {r}")
        except Exception as e:  # noqa: BLE001
            print(f"  [!] teaser {canal}: {e}")
            ok = False
    return ok


def refazer(itens: str) -> bool:
    import video_oferta as vo
    # os dados de preco EXATOS do run 36743009796 (a legenda publicada usa estes)
    base = Path("_dia"); (base / "estado").mkdir(parents=True, exist_ok=True)
    for f in ("precos_vistos.jsonl", "precos_agora.json", "nomes_curtos.json"):
        (base / "estado" / f).write_bytes(subprocess.run(["git", "show", f"062bbab:estado/{f}"],
                                                         capture_output=True, check=True).stdout)
    raiz_real, vo.RAIZ = vo.RAIZ, base
    feitas = [json.loads(l) for l in open(RAIZ / "estado" / "ofertas_feitas.jsonl", encoding="utf-8") if l.strip()]
    novos = []
    for it in [i.strip() for i in itens.split("||") if i.strip()]:
        alvo, quando = [x.strip() for x in it.split("@@")]
        canal, n = alvo.split(":")
        f = next(x for x in reversed(feitas) if x["canal"] == canal and x.get("numero") == int(n))
        nome = f"{f['dia']}_{canal.replace('.', '-')}_{f['id']}"
        orig = Path(nome + "_orig.mp4")
        urllib.request.urlretrieve(f"https://github.com/{REPO}/releases/download/ofertas-{f['dia'][:7]}/{nome}.mp4", orig)
        vo.RAIZ = base
        d = vo.dados(f["id"])
        vo.RAIZ = raiz_real
        assert abs(d["agora"] - f["agora"]) < 0.005 and d["hora"] in f["comentario"], (d["agora"], d["hora"])
        d.update(gancho="", marca=vo.MARCAS[canal], numero=int(n), id=f["id"], festa=True)
        cart = [vo.cartao(vo.baixar(u), 820) for u in d["imagens"]]
        fundo = vo.base_fundo()
        saida = Path(nome + "_festa.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{vo.W}x{vo.H}", "-r", str(vo.FPS), "-i", "-", "-i", str(orig),
                              "-map", "0:v", "-map", "1:a", "-t", str(vo.DUR), "-c:v", "libx264",
                              "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy",
                              "-movflags", "+faststart", str(saida)], stdin=subprocess.PIPE)
        for i in range(int(vo.DUR * vo.FPS)):
            p.stdin.write(vo.quadro(i / vo.FPS, d, fundo, cart).tobytes())
        p.stdin.close()
        p.wait()
        _gh("release", "upload", f"ofertas-{f['dia'][:7]}", str(saida), "--clobber")
        print(f"  ok visual de festa: {saida.name}")
        novos.append(f"{canal}:{n}@@{quando}@@_festa")
    r = subprocess.run([sys.executable, "-X", "utf8", str(RAIZ / "ferramentas" / "mover_ofertas.py"),
                        "--itens", "||".join(novos)])
    return r.returncode == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--teaser", default="")
    ap.add_argument("--refazer", default="")
    a = ap.parse_args()
    ok = True
    if a.refazer:
        ok &= refazer(a.refazer)
    if a.teaser:
        ok &= teasers(a.teaser)
    sys.exit(0 if ok else 1)
