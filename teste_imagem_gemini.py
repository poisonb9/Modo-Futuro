"""Piloto: geração de imagem via Gemini (gemini-2.5-flash-image, "nano banana"),
usando a mesma infra de chaves (engine/keys.py) já usada no resto do motor.
Descartável -- só pra avaliar se o estilo cinematografico/sci-fi realista
funciona pra substituir video de arquivo por imagem gerada.
"""
import base64
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from engine import keys

MODELO = "gemini-2.5-flash-image"
URL = "https://generativelanguage.googleapis.com/v1beta"

PROMPTS = [
    "Cinematic hyper-realistic sci-fi scene: a massive humanoid AI robot "
    "standing in a dark server room lit by blue and red data lights, "
    "dramatic volumetric lighting, shallow depth of field, 8k, film still, "
    "vertical 9:16 composition",

    "Cinematic hyper-realistic scene: a glowing neural network made of "
    "light strands wrapped around a human brain silhouette, dark "
    "background, dramatic rim lighting, sci-fi documentary trailer look, "
    "vertical 9:16 composition",

    "Cinematic hyper-realistic scene: a futuristic city skyline at night "
    "with holographic AI data streams flowing between skyscrapers, "
    "dramatic blue and orange lighting, film grain, vertical 9:16 "
    "composition",
]


def gerar(prompt: str, destino: Path):
    rot = keys.gemini()
    for _ in range(len(rot) * 2):
        chave = rot.proxima()
        r = requests.post(
            f"{URL}/models/{MODELO}:generateContent?key={chave}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["IMAGE"]},
            },
            timeout=120,
        )
        if r.status_code in (429, 403):
            rot.queimar(chave)
            continue
        if not r.ok:
            print(f"   [!] {r.status_code}: {r.text[:500]}")
            r.raise_for_status()
        data = r.json()
        partes = data["candidates"][0]["content"]["parts"]
        for p in partes:
            if "inlineData" in p:
                img_b64 = p["inlineData"]["data"]
                destino.write_bytes(base64.b64decode(img_b64))
                print(f"   ok: {destino}")
                return
        print("   [!] resposta sem imagem:", json.dumps(data)[:500])
        return
    print("   [!] falhou em todas as chaves")


if __name__ == "__main__":
    saida = Path(__file__).parent / "teste_imagens_ia"
    saida.mkdir(exist_ok=True)
    for i, p in enumerate(PROMPTS, 1):
        print(f"[{i}/{len(PROMPTS)}] gerando...")
        gerar(p, saida / f"teste_{i}.png")
