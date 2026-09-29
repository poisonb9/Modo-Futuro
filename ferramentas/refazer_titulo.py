# -*- coding: utf-8 -*-
"""Refaz o TITULO de um clipe ja' cortado a partir do que a FALA diz (nuvem).

    python -X utf8 ferramentas/refazer_titulo.py --titulo "<titulo antigo exato>"

⛔ 29/09/2026 (dono: "a refaça"): 6 clipes sairam com titulo de um trecho e
fala de outro (Coragem "caixas de chocolate" falava de Kansas). Em vez de
recortar (2 h por video), este arquivo:
  1. baixa o clipe da release e o Gemini OUVE o audio -> titulo novo
     (afirmando, estilo do canal), legenda curta e ate' 3 hashtags;
  2. cobre o card de titulo antigo (0..TITULO_SEGUNDOS) com a faixa de fundo
     do proprio video e desenha o novo com `render.imagem_titulo` (mesma
     fonte, mesmas caixas, mesmo destaque);
  3. sobe como clipe NOVO (nome `_TITULONOVO_`) e acrescenta ao manifesto
     com o titulo novo. O antigo segue em TITULOS_BLOQUEADOS; o novo ainda
     passa pela trava do agendador (que ouve e confere) antes de postar.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import keys, nome_produto as _np, render  # noqa: E402
import agendar_buffer as ab  # noqa: E402
import publicar_release as pr  # noqa: E402

TAG = "clipes-09-2026"
PEDIDO = (
    "Voce vai ouvir o audio de um video curto de TikTok (portugues), do canal \"{canal}\". "
    "O titulo antigo estava ERRADO (falava de outra coisa): \"{antigo}\".\n"
    "Escreva um titulo NOVO sobre o que a fala REALMENTE diz: afirmativo (nunca pergunta), "
    "curioso, ate' 60 caracteres, em portugues do Brasil, com o nome do personagem/pessoa "
    "principal, com a MESMA grafia do nome usada no titulo antigo. Escreva em CAIXA ALTA so' as 1-2 palavras de destaque.\n"
    "Responda SO' um JSON: {{\"titulo\": \"...\", \"legenda\": \"<2 frases sobre a fala>\", "
    "\"hashtags\": [\"#a\", \"#b\", \"#c\"]}}"
)


def gemini_ouve(audio: bytes, canal: str, antigo: str) -> dict:
    rot = keys.gemini()
    for _ in range(min(6, len(rot))):
        chave = rot.proxima()
        try:
            r = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{_np.MODELO_GEMINI}:generateContent?key={chave.strip()}",
                json={"contents": [{"parts": [
                    {"text": PEDIDO.format(canal=canal, antigo=antigo)},
                    {"inline_data": {"mime_type": "audio/mp3",
                                     "data": base64.b64encode(audio).decode()}}]}],
                      "generationConfig": {"temperature": 0.4}}, timeout=120)
            if r.status_code in (403, 429):
                rot.queimar(chave)
                continue
            r.raise_for_status()
            t = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(re.search(r"\{.*\}", t, re.S).group(0))
        except Exception as e:  # noqa: BLE001
            print(f"  [!] gemini: {type(e).__name__}")
    raise SystemExit("o Gemini nao respondeu")


# nomes que o ouvido do Gemini escreve errado -> grafia certa
GRAFIA = {"jiwou": "Jiwoo", "jiwu": "Jiwoo", "jiu": "Jiwoo"}


def corrige_grafia(t: str) -> str:
    for errado, certo in GRAFIA.items():
        t = re.sub(rf"{errado}",
                   lambda m, c=certo: c.upper() if m.group().isupper() else c, t, flags=re.I)
    return t


def sh(*a: str) -> None:
    subprocess.run(list(a), check=True)


def refazer(titulo_antigo: str, manif: dict) -> None:
    chave, clipe = next(((k, v) for k, v in manif.items()
                         if (v.get("titulo") or "").strip() == titulo_antigo.strip()), (None, None))
    if not clipe:
        print(f"  [!] titulo nao achado no manifesto: {titulo_antigo!r}")
        return
    tmp = Path(tempfile.mkdtemp())
    v, au = tmp / "v.mp4", tmp / "a.mp3"
    urllib.request.urlretrieve(clipe["url"], v)
    sh("ffmpeg", "-v", "error", "-y", "-i", str(v), "-vn", "-ac", "1", "-ar", "16000",
       "-b:a", "32k", str(au))
    novo = gemini_ouve(au.read_bytes(), clipe.get("canal") or "", clipe["titulo"])
    titulo = corrige_grafia(novo["titulo"].strip().strip('"'))
    novo["legenda"] = corrige_grafia(novo.get("legenda", ""))
    print(f"titulo novo: {titulo}")

    # card novo, com a mesma funcao do motor
    lv, av = 1080, 1920
    card = render.imagem_titulo(titulo, lv, av, tmp / "tit")
    topo = round(av * render.TITULO_TOPO_FRAC)
    fim = render.TITULO_SEGUNDOS + 0.15
    # faixa de fundo limpa: o mesmo retangulo num quadro logo DEPOIS do titulo
    faixa = tmp / "faixa.png"
    alt = 560
    sh("ffmpeg", "-v", "error", "-y", "-ss", f"{fim + 0.4:.2f}", "-i", str(v), "-frames:v", "1",
       "-vf", f"crop={lv}:{alt}:0:{max(0, topo - 40)},gblur=sigma=6", str(faixa))
    saida = tmp / clipe["url"].rsplit("/", 1)[1].replace("_short_9x16.mp4", "_TITULONOVO_short_9x16.mp4")
    filtro = (f"[0:v][1:v]overlay=0:{max(0, topo - 40)}:enable='lt(t,{fim:.2f})'[a];"
              f"[a][2:v]overlay=0:{topo}:enable='lt(t,{fim:.2f})'[v]")
    sh("ffmpeg", "-v", "error", "-y", "-i", str(v), "-loop", "1", "-t", f"{fim + 1:.2f}", "-i", str(faixa),
       "-loop", "1", "-t", f"{fim + 1:.2f}", "-i", str(card), "-filter_complex", filtro,
       "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
       "-c:a", "copy", "-movflags", "+faststart", str(saida))
    prev = tmp / (saida.stem + "_quadro.png")
    sh("ffmpeg", "-v", "error", "-y", "-ss", "0.8", "-i", str(saida), "-frames:v", "1",
       "-vf", "scale=540:-1", str(prev))
    sh("gh", "release", "upload", TAG, str(saida), str(prev), "--clobber")
    url = f"https://github.com/poisonb9/Modo-Futuro/releases/download/{TAG}/{saida.name}"
    tags = " ".join((novo.get("hashtags") or [])[:3])
    entrada = dict(clipe)
    entrada.update({"titulo": titulo, "url": url,
                    "legenda": f"{titulo}\n\n{novo.get('legenda', '').strip()}\n\n{tags}".strip(),
                    "refeito_de": clipe["titulo"], "publicado_em": None})
    pr._publicar_manifesto(ab._token_github(), TAG, {chave + "#titulonovo": entrada})
    print(f"ok -> {saida.name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--titulos", required=True, help="titulos ANTIGOS exatos, separados por ||")
    a = ap.parse_args()
    manif = ab.manifesto(ab._token_github(), None)
    for t in [x.strip() for x in a.titulos.split("||") if x.strip()]:
        print(f"\n=== {t}", flush=True)
        try:
            refazer(t, manif)
        except Exception as e:  # noqa: BLE001 — um clipe nao derruba os outros
            print(f"  [!] falhou: {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
