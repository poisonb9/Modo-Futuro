# -*- coding: utf-8 -*-
"""Le uma pasta de imagens de referencia com o Gemini e grava so' DADOS (JSON).

    python ferramentas/ler_referencias.py <pasta> <saida.json>

Retoma: o que ja' esta' na saida sem erro nao e' lido de novo. ~4 s entre
imagens (cota). O roteiro da leitura vem de REF_ROTEIRO (secret); sem ele, um
roteiro generico de capa/layout editorial.
"""
import base64, io, json, os, sys, time
from pathlib import Path

import requests
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import keys  # noqa: E402

ROTEIRO = os.environ.get("REF_ROTEIRO") or """Analise esta imagem de capa/layout editorial. Responda SO' JSON:
{"e_capa": true/false, "titulo_publicacao": "", "epoca": "", "quem": "", "nome_em_destaque": "",
"chamada_principal": "", "chamadas_secundarias": [], "brinde": "", "formulas": [], "palavras_gatilho": [],
"cores": "", "logo": "", "pose_olhar": "", "hierarquia": ""}
Use "" quando ilegivel. Nao invente texto."""
# ⭐ 02/10/2026 (dono): modelos FORA da cadeia dos cortes (3.8/3.7/3.6/3.5-flash),
# pra nao disputar cota com eles. Gemma 4 le capa muito bem (medido).
# ⛔ 03/10/2026 (dono): flash-lite e' fraco demais — fora. So' Gemma 4 (o 26B de reserva).
MODELOS = ("gemma-4-31b-it", "gemma-4-26b-a4b-it")


def ler(f: Path, rot) -> dict:
    im = Image.open(f).convert("RGB")
    im.thumbnail((1100, 1100))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    corpo = {"contents": [{"parts": [{"inline_data": {"mime_type": "image/jpeg",
                                                      "data": base64.b64encode(b.getvalue()).decode()}},
                                     {"text": ROTEIRO}]}],
             "generationConfig": {"temperature": 0}}
    for _ in range(min(12, len(rot))):
        k = rot.proxima().strip()
        for modelo in MODELOS:
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                                  headers={"x-goog-api-key": k}, json=corpo, timeout=120)
            except requests.RequestException:
                continue
            if r.status_code == 200:
                try:
                    t = r.json()["candidates"][0]["content"]["parts"][-1]["text"]
                    d = json.loads(t[t.index("{"):t.rindex("}") + 1])   # Gemma nao tem modo JSON
                    d["arquivo"] = f.name
                    return d
                except (KeyError, ValueError, IndexError):
                    continue
            if r.status_code in (403, 429):
                rot.queimar(k)
                break
    return {"arquivo": f.name, "erro": "sem resposta"}


def main() -> None:
    pasta, saida = Path(sys.argv[1]), Path(sys.argv[2])
    fs = sorted(p for p in pasta.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    velho = {x["arquivo"]: x for x in (json.loads(saida.read_text(encoding="utf-8")) if saida.exists() else [])
             if not x.get("erro")}
    falta = [f for f in fs if f.name not in velho]
    print(f"ja' lidas {len(velho)}, faltam {len(falta)}", flush=True)
    rot = keys.gemini()
    novos = []
    for i, f in enumerate(falta, 1):
        novos.append(ler(f, rot))
        if i % 10 == 0:
            print(i, flush=True)
            saida.write_text(json.dumps(list(velho.values()) + novos, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(4)
    res = list(velho.values()) + novos
    saida.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(res)} lidas; {sum(1 for x in res if x.get('erro'))} com erro", flush=True)


if __name__ == "__main__":
    main()
