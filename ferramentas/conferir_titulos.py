# -*- coding: utf-8 -*-
"""Confere se a FALA de cada video agendado trata do que o TITULO promete.

    python -X utf8 ferramentas/conferir_titulos.py                 todos os canais
    python -X utf8 ferramentas/conferir_titulos.py --canal atefalhar

⛔ 29/09/2026 (dono, com print): "esses videos do Coragem estao falando de outras
coisas enquanto a capa fala de chocolate e a legenda tambem". Medido: o clipe
"As caixas inteiras de chocolate que Coragem devora" (inicio 799 s de "Courage
the Cowardly Dog REAL Monster") fala de Kansas, Nowhere e monstros — nenhuma
palavra de chocolate. O titulo nasceu de um trecho e o corte saiu de outro.

Roda na NUVEM (Buffer + Gemini nos Secrets). Para cada post agendado: baixa o
video QUE ESTA' NO POST, tira o audio, e pergunta ao Gemini (que ouve audio)
se a fala trata do assunto do titulo. SO' RELATA — quem decide apagar ou
trocar e' o dono.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import trocar_legendas_agendadas as tl  # noqa: E402
from engine import canais_registro, keys, nome_produto as _np  # noqa: E402

PERGUNTA = (
    "Voce vai ouvir o audio de um video curto (portugues). O TITULO publicado e': "
    "\"{titulo}\".\n"
    "Responda SO' um JSON: {{\"bate\": true|false, \"fala_de\": \"<assunto real da fala em ate 12 palavras>\"}}.\n"
    "bate = true so' se a fala trata do assunto CENTRAL do titulo (nao basta citar o personagem)."
)


# 06/10/2026: o juiz tentava so' 4 chaves e desistia em qualquer erro que nao
# fosse cota (503 = Gemini sobrecarregado) -> "sem veredito" -> clipe pulado ->
# fila vazia em 4 canais. Agora percorre TODAS as chaves, espera no 5xx e cai
# para o modelo reserva. ⛔ Flash-LITE proibido (regra do dono).
MODELOS_JUIZ = [_np.MODELO_GEMINI, "gemini-3.5-flash"]


def julgar(audio: bytes, titulo: str) -> dict | None:
    import time as _t
    rot = keys.gemini()
    for modelo in MODELOS_JUIZ:
        for _ in range(max(1, len(rot))):
            chave = rot.proxima()
            if not chave:
                break
            try:
                r = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{modelo}:generateContent?key={chave.strip()}",
                    json={"contents": [{"parts": [
                        {"text": PERGUNTA.format(titulo=titulo)},
                        {"inline_data": {"mime_type": "audio/mp3",
                                         "data": base64.b64encode(audio).decode()}}]}],
                          "generationConfig": {"temperature": 0}}, timeout=120)
                if r.status_code in (403, 429):
                    rot.queimar(chave)
                    continue
                if r.status_code >= 500:
                    print(f"    [!] gemini {modelo}: {r.status_code} (sobrecarga) — espero e tento outra")
                    _t.sleep(4)
                    continue
                if r.status_code != 200:
                    print(f"    [!] gemini {modelo}: {r.status_code} {r.text[:160]}")
                    break
                t = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                m = re.search(r"\{.*\}", t, re.S)
                return json.loads(m.group(0)) if m else None
            except Exception as e:  # noqa: BLE001
                print(f"    [!] gemini {modelo}: {type(e).__name__} {str(e)[:120]}")
        rot._queimadas.clear()   # cota e' por modelo: chaves de volta para o reserva
    return None


def audio_do_video(url: str) -> bytes:
    tmp = Path(tempfile.mkdtemp())
    v, a = tmp / "v.mp4", tmp / "a.mp3"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    v.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-vn", "-ac", "1",
                    "-ar", "16000", "-b:a", "32k", str(a)], check=True)
    return a.read_bytes()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal")
    a = ap.parse_args()
    nomes = [canais_registro.canonico(a.canal)] if a.canal else [
        n for n, c in canais_registro.CANAIS.items() if c.motor and c.env and os.environ.get(c.env)]
    ruins = 0
    for nome in nomes:
        c = canais_registro.CANAIS[nome]
        token = (os.environ.get(c.env) or "").strip()
        if not token:
            print(f"\n{nome}: sem token — pulado")
            continue
        posts = sorted(tl.agendados(token, c.org, c.canal_id), key=lambda p: p["dueAt"])
        print(f"\n== {nome}: {len(posts)} agendado(s)")
        for p in posts:
            titulo = (p.get("text") or "").split("\n")[0].strip()
            url = tl.video_do_post(token, p["id"])
            if not url:
                print(f"  ?  {p['dueAt'][:16]}  {titulo[:60]}  (video nao lido)")
                continue
            try:
                j = julgar(audio_do_video(url), titulo)
            except Exception as e:  # noqa: BLE001
                print(f"  ?  {p['dueAt'][:16]}  {titulo[:60]}  ({type(e).__name__})")
                continue
            if not j:
                print(f"  ?  {p['dueAt'][:16]}  {titulo[:60]}  (sem veredito)")
                continue
            ok = bool(j.get("bate"))
            ruins += 0 if ok else 1
            print(f"  {'ok ' if ok else 'XX '} {p['dueAt'][:16]}  id {p['id']}  {titulo[:60]}"
                  + ("" if ok else f"\n        a fala e' sobre: {j.get('fala_de')}"))
    print(f"\n{ruins} post(s) com titulo que NAO bate com a fala")


if __name__ == "__main__":
    main()
