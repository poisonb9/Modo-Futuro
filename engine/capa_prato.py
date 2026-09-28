# -*- coding: utf-8 -*-
"""A FOTO DO PRATO de um corte de receita (28/09/2026, documento da receita).

A capa comum sai do 1o segundo (render.capa) — em receita isso e' salsinha,
mao ou a apresentadora. E tirar do video PUBLICADO nao serve: ele tem baloes,
aviao e legenda por cima. Aqui a foto vem do BRUTO (limpo): amostra quadros
da 2a metade do trecho (onde o CRITERIO_RECEITA poe o resultado), descarta os
que tem ROSTO (MediaPipe, o mesmo modelo do enquadrar) e fica com o mais
nitido e colorido. Recorte 4:3 no centro. Falha aberta: None.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / "modelos" / "blaze_face_short_range.tflite"
AMOSTRAS = 12


def escolher(video: Path, ini: float = 0.0, fim: float | None = None) -> bytes | None:
    try:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
        if fim is None:
            fim = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                 str(video)], capture_output=True, text=True).stdout)
        det = None
        if MODELO.exists():
            det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
                base_options=BaseOptions(model_asset_path=str(MODELO)),
                min_detection_confidence=0.55))
        d = Path(tempfile.mkdtemp())
        a = ini + (fim - ini) * 0.35
        b = max(a + 0.5, ini + (fim - ini) * 0.85)
        melhor, nota_m = None, -1.0
        for k in range(AMOSTRAS):
            t = a + (b - a) * k / (AMOSTRAS - 1)
            j = d / f"q{k}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video),
                            "-frames:v", "1", "-vf",
                            "crop='min(iw,ih*4/3)':'min(ih,iw*3/4)',scale=960:-2",
                            "-q:v", "3", str(j)], check=True)
            img = cv2.imread(str(j))
            if img is None:
                continue
            if det is not None:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                if det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)).detections:
                    continue
            cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            nit = cv2.Laplacian(cinza, cv2.CV_64F).var()
            sat = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 1].mean()
            nota = nit ** 0.5 * (0.5 + sat / 255)
            if nota > nota_m:
                melhor, nota_m = j, nota
        dados = melhor.read_bytes() if melhor else None
        shutil.rmtree(d, ignore_errors=True)
        return dados
    except Exception as e:  # noqa: BLE001
        print(f"      [!] foto do prato falhou ({type(e).__name__}: {str(e)[:80]})")
        return None
