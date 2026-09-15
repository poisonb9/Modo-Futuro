"""Guarda: o tratamento manteve O MESMO produto, ou virou outro?

⚠️ POR QUE EXISTE. Ordem do Bryan em 15/09/2026: *"nao pode ir pra internet o
video de um produto que nao e' o de acordo"*. E' a mesma regra que matou o
video do YouTube (83% do catalogo e' generico e nao da' pra verificar) — a
diferenca e' que aqui da' pra MEDIR, porque temos a foto do anuncio como
verdade de referencia.

## O que ela responde, e o que ela NAO responde

    virou OUTRO produto            -> REPROVA   (e' para isto que ela existe)
    mesmo produto, luz nova        -> passa     (o relume premium e' desejado)
    mesmo produto, redesenhado pior-> PASSA  ⚠️ ela NAO pega isso

⛔ O ultimo caso nao e' descuido, e' limite medido: o inpainting do Cloudflare,
que refez o produto com menos detalhe, tira 0,9786 — acima de qualquer limiar
util. Degradacao de QUALIDADE e' outro problema (nitidez/resolucao) e pede
outra guarda. Nao esticar esta para cobrir aquilo.

## Como se chegou aqui — quatro tentativas que FALHARAM

Metricas classicas foram testadas e todas INVERTERAM a ordem, aprovando o
inpainting infiel e reprovando o relume fiel:

    Canny IoU (imagem inteira)   relume 0,054  inpaint 0,555
    Canny IoU (so' o produto)    relume 0,186  inpaint 0,469
    Canny + CLAHE                relume 0,242  inpaint 0,518
    ORB (pontos que casam)       relume 0,013  inpaint 0,226
    histograma de gradiente      relume 0,920  inpaint 0,958

⭐ A razao e' semantica, nao de ajuste: o inpainting partiu da mesma imagem e
manteve pose e luz, entao PARECE mais; o relume recolocou o produto numa cena
nova e PARECE menos, preservando a identidade. "E' o mesmo objeto?" nao e' uma
pergunta sobre pixels — por isso o julgamento e' de um modelo de visao.

## Calibracao — e o caso negativo teve de ser trocado

⚠️ O primeiro negativo escolhido (o inpainting) NAO era teorematico: ele nao
virou outro produto, virou o mesmo produto malfeito. Com ele nenhuma metrica
podia passar. O negativo correto e' um produto DIFERENTE do catalogo:

    mesmo produto      min 0,9593   (identica, Ken Burns, relume, LTX, inpaint)
    outro produto      max 0,5861   (espelho, termometro, carregador, kit ABS)
    margem                   0,37

LIMIAR = 0,85 fica no meio do vazio, longe dos dois lados.

⚠️ Esta guarda precisa de REDE (embedding na NVIDIA). O recorte
(`engine/recorte.py`) e' local de proposito; este nao da' pra ser, porque
julgamento de identidade exige modelo grande. Sem rede, o clipe nao sai — e
esse e' o lado seguro do erro.
"""
import os
import base64
from io import BytesIO
from pathlib import Path

import numpy as np

MODELO = "nvidia/llama-nemotron-embed-vl-1b-v2"
URL = "https://integrate.api.nvidia.com/v1/embeddings"
LIMIAR = 0.85
LADO = 448


def _vetor(imagem) -> np.ndarray:
    """Embedding do PRODUTO (recortado), nao da cena.

    ⚠️ O recorte importa: com a imagem inteira o fundo entra na conta e o
    relume cai de 0,9689 para 0,9377 sem ter mudado o produto."""
    import requests
    from PIL import Image
    from engine import recorte

    im = Image.open(imagem).convert("RGB") if not isinstance(imagem, Image.Image) \
        else imagem.convert("RGB")
    a = recorte.alfa(im)
    ys, xs = np.where(a > 128)
    if len(ys) > 50:
        im = im.crop((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
    im.thumbnail((LADO, LADO))
    bo = BytesIO()
    im.save(bo, "JPEG", quality=88)
    url = "data:image/jpeg;base64," + base64.b64encode(bo.getvalue()).decode()

    chave = os.getenv("NVIDIA_API_KEY")
    if not chave:
        raise RuntimeError("falta NVIDIA_API_KEY no .env")
    r = requests.post(URL, headers={"Authorization": f"Bearer {chave}"}, timeout=180,
                      json={"model": MODELO, "input": [url], "encoding_format": "float",
                            # ⚠️ imagem e' "passage". Com "query" a API responde
                            # 400 "does not support image input as query".
                            "input_type": "passage", "truncate": "NONE"})
    r.raise_for_status()
    return np.array(r.json()["data"][0]["embedding"], dtype=np.float32)


def comparar(antes, depois) -> dict:
    a, b = _vetor(antes), _vetor(depois)
    s = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
    return {"semelhanca": round(s, 4), "aprovado": s >= LIMIAR,
            "motivo": "" if s >= LIMIAR else "o produto mostrado nao e' o do anuncio"}


def do_video(original, video, quadros: int = 4) -> dict:
    """O PIOR quadro manda: basta um quadro com outro produto para o clipe
    nao poder ir ao ar."""
    import subprocess
    import tempfile

    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(video)],
        capture_output=True, text=True).stdout.strip() or 2)
    todos = []
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(quadros):
            t = dur * (i + 0.5) / quadros
            q = Path(tmp) / f"q{i}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t),
                            "-i", str(video), "-frames:v", "1", str(q)], check=False)
            if not q.exists():
                continue
            r = comparar(original, q)
            r["t"] = round(t, 2)
            todos.append(r)
    if not todos:
        return {"aprovado": False, "pior": None, "quadros": [],
                "motivo": "nenhum quadro pode ser lido"}
    pior = min(todos, key=lambda r: r["semelhanca"])
    return {"aprovado": all(r["aprovado"] for r in todos),
            "pior": pior, "quadros": todos}
