# -*- coding: utf-8 -*-
"""Videos do VENDEDOR na pagina do produto no AliExpress (alem do da API).

    python -X utf8 ferramentas/videos_aliexpress.py --max 5         teste
    python -X utf8 ferramentas/videos_aliexpress.py --max 60        rodada

⭐ 29/09/2026 (dono: "tudo automatico, eu nao posso ficar baixando na mao").
A API de afiliados devolve UM `product_video_url` (17 de 182 produtos). A
pagina do anuncio costuma ter mais: o vendedor sobe o video no proprio
anuncio. E' material do vendedor, na plataforma de que somos afiliados.

Regras:
  - roda na NUVEM, devagar (PAUSA_S entre paginas) e so' nos produtos que
    ainda nao tem video;
  - ⛔ se a pagina vier com desafio de robo (captcha/slider/"punish"), PARA a
    rodada inteira e nao tenta contornar;
  - guarda em `estado/videos_produto.json` {id: {"videos": [...], "quando"}};
    o `video_oferta` usa o primeiro quando o instantaneo nao tiver video.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "estado" / "videos_produto.json"
PAUSA_S = 8
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
DESAFIO = re.compile(r"punish|captcha|slide to verify|x5sec|baxia", re.I)
VIDEO = re.compile(r"https?:\\?/\\?/[a-z0-9.-]*(?:alicdn|aliexpress-media)[a-z0-9./\\_-]*?\.mp4", re.I)


def ler() -> dict:
    return json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else {}


def videos_da_pagina(pid: str) -> tuple[list[str], str]:
    """(videos, estado) — estado: ok | desafio | erro"""
    try:
        r = requests.get(f"https://pt.aliexpress.com/item/{pid}.html",
                         headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"},
                         timeout=30)
    except requests.RequestException as e:
        return [], f"erro {type(e).__name__}"
    if DESAFIO.search(r.text[:20000]) and "videoUid" not in r.text:
        return [], "desafio"
    achados = []
    for m in VIDEO.findall(r.text):
        u = m.replace("\\/", "/").replace("\\u002F", "/")
        if u not in achados:
            achados.append(u)
    return achados[:3], "ok"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=5)
    a = ap.parse_args()
    agora = json.loads((RAIZ / "estado" / "precos_agora.json").read_text(encoding="utf-8"))
    feito = ler()
    alvo = [pid for pid, v in agora.items()
            if pid.isdigit() and len(pid) > 12 and not v.get("video") and pid not in feito][:a.max]
    print(f"{len(alvo)} produto(s) sem video para olhar")
    com = 0
    for i, pid in enumerate(alvo):
        vids, estado = videos_da_pagina(pid)
        if estado == "desafio":
            print(f"⛔ desafio de robo na pagina ({pid}) — PARO a rodada, sem contornar")
            break
        feito[pid] = {"videos": vids, "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "estado": estado}
        com += bool(vids)
        print(f"  {pid}: {len(vids)} video(s) [{estado}]")
        if i < len(alvo) - 1:
            time.sleep(PAUSA_S)
    SAIDA.write_text(json.dumps(feito, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{com} de {len(alvo)} com video na pagina")


if __name__ == "__main__":
    main()
