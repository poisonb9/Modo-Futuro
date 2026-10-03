# -*- coding: utf-8 -*-
"""Capa nitida: o quadro 0 do 9:16 passa a ser o mais nitido dos 2 s do titulo.

    python -m engine.capa_nitida --video c.mp4

## POR QUE EXISTE

A capa do TikTok (grade do perfil) e' o PRIMEIRO QUADRO do video — a API do
Buffer so' deixa escolher o quadro, nao mandar imagem (render.py). E o primeiro
quadro do corte e' o que calhar: borrado de movimento, olho fechado, meio de
transicao. O acervo manda cuidar desse quadro (F132220, F100190).

Decisao do dono em 26/09/2026 (opcao "a"): procurar o melhor quadro SO' dentro
dos 2 s do titulo — ali a imagem e' limpa (a legenda so' entra depois do
titulo e os baloes aos 3 s), entao a capa continua sendo titulo + imagem.

Um quadro (1/fps, ~33 ms) nao se percebe assistindo, mas vira a capa. O audio
atrasa o mesmo quadro, pra nao dessincronizar. So' mexe se o melhor quadro for
CLARAMENTE mais nitido que o atual (`GANHO_MIN`); senao nao reprocessa nada.
Falha aberta.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

LIGADO = os.environ.get("CAPA_NITIDA", "1") != "0"
GANHO_MIN = 1.15
PASSO_S = 0.15

# ⭐ CAPA SEM TEXTO QUEIMADO DA FONTE (27/09/2026, dono aprovou: "a grade mistura
# o nosso titulo com texto grande do video original" — "Futuro Tem Preço",
# "Está Fora do Jogo?" atras das nossas caixas brancas).
#
# ⚠️ A nitidez (variancia das bordas) PREFERE esses quadros: letra grande e'
# borda pura. Por isso a capa nitida escolhia justamente o quadro sujo.
#
# MEDIDO (EasyOCR, so' deteccao, 4 quadros nos 2 s do titulo, % da area com
# letras FORA da faixa do nosso titulo): limpos 2-8%; sujos com picos de 22%,
# 37%, 43% e 48% — e o texto da fonte APARECE E SOME dentro dos 2 s, entao
# quase sempre ha' quadro limpo pra escolher. Corte: LIMITE_TEXTO.
# O OCR roda NA NUVEM (passo "OCR da capa" do cortar_de_bruto.yml); sem ele
# instalado, a capa volta ao criterio so' de nitidez (falha aberta).
LIMITE_TEXTO = 12.0          # % da area fora do titulo
FAIXA_TITULO = 0.36          # o nosso titulo ocupa o topo ate' 36% da altura
_LEITOR = None


def texto_fora_do_titulo(img) -> float | None:
    """% da area (abaixo da faixa do titulo) coberta por letras, ou None se
    o OCR nao estiver instalado. Exposto pro teste."""
    global _LEITOR
    try:
        import numpy as np
        if _LEITOR is None:
            import easyocr
            _LEITOR = easyocr.Reader(["en"], gpu=False, recognizer=False,
                                     verbose=False)
        a = np.array(img.convert("RGB"))
        h, w = a.shape[:2]
        caixas, _ = _LEITOR.detect(a, min_size=15)
        area = 0.0
        for x0, x1, y0, y1 in caixas[0]:
            if (y0 + y1) / 2 < FAIXA_TITULO * h:
                continue
            area += max(0, x1 - x0) * max(0, y1 - y0)
        return area / (w * h * (1 - FAIXA_TITULO)) * 100
    except Exception:
        return None


def escolher(amostras: list[tuple[float, float, float | None]]
             ) -> tuple[float, float, bool]:
    """(instante, nota, trocar?) a partir de [(t, nitidez, texto%)]. Exposto
    pro teste: quadros com texto > LIMITE_TEXTO nao podem ser capa; se o
    quadro 0 tem texto e existe um limpo, troca mesmo sem ganho de nitidez."""
    t0, n0, x0 = amostras[0]
    limpos = [a for a in amostras if a[2] is None or a[2] <= LIMITE_TEXTO]
    if not limpos:
        return t0, n0, False
    t, n, _ = max(limpos, key=lambda a: a[1])
    sujo0 = x0 is not None and x0 > LIMITE_TEXTO
    if sujo0 and t > 0.05:
        return t, n, True
    return t, n, t >= 0.05 and n >= n0 * GANHO_MIN


def nota_quadro(img) -> float:
    """Nitidez (variancia das bordas) com penalidade de exposicao ruim."""
    from PIL import ImageFilter, ImageStat
    g = img.convert("L")
    nit = ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0]
    media = ImageStat.Stat(g).mean[0]
    if media < 35 or media > 220:
        nit *= 0.5
    return nit


# ⭐ 02/10/2026 (dono): CAPA COM OLHAR NA CAMERA E SORRISO. Engenharia reversa
# de 162 capas de revista teen (_privado/capricho/): 161 olham para a lente,
# 69% sorriem, 51% em close. O acervo confirma (contato visual direto prende
# no feed). Rosto FRONTAL (detector de frente) ~ olhando para a camera; olhos
# abertos e sorriso somam. Bonus multiplica a nitidez; sem OpenCV = 1.0.
BONUS_FRONTAL = 0.6
BONUS_OLHOS = 0.3
BONUS_SORRISO = 0.3
# 03/10/2026 (dono): capa com UM rosto so' — 114 de 155 capas teen eram solo.
# Rosto vizinho com >= 60% do tamanho do maior conta como "segundo rosto".
BONUS_SOLO = 0.2
_HAAR = {}


def _cascata(nome: str):
    import cv2
    if nome not in _HAAR:
        # 03/10: o opencv da nuvem (e o do PC) vem SEM os XML; eles moram no repo
        base = os.environ.get("HAAR_DIR") or str(Path(__file__).with_name("haar"))
        _HAAR[nome] = cv2.CascadeClassifier(os.path.join(base, nome))
    return _HAAR[nome]


def bonus_rosto(img) -> float:
    """1.0 sem rosto; ate' ~2.4 com rosto grande, de frente, olhos e sorriso."""
    try:
        import cv2
        import numpy as np
        g = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
        h, w = g.shape
        caras = _cascata("haarcascade_frontalface_default.xml").detectMultiScale(
            g, 1.1, 5, minSize=(w // 8, w // 8))
        if len(caras) == 0:
            return 1.0
        x, y, cw, ch = max(caras, key=lambda r: r[2] * r[3])
        b = 1.0 + BONUS_FRONTAL * min(1.0, (cw / w) / 0.35)      # maior = melhor ate' 35% da largura
        if sum(1 for r in caras if r[2] * r[3] >= 0.6 * cw * ch) == 1:
            b += BONUS_SOLO
        rosto = g[y:y + ch, x:x + cw]
        olhos = _cascata("haarcascade_eye.xml").detectMultiScale(rosto[: ch // 2], 1.1, 6)
        if len(olhos) >= 2:
            b += BONUS_OLHOS
        sorr = _cascata("haarcascade_smile.xml").detectMultiScale(rosto[ch // 2:], 1.7, 22)
        if len(sorr) >= 1:
            b += BONUS_SORRISO
        return b
    except Exception:
        return 1.0


def amostrar(video: Path, ate_s: float) -> list[tuple[float, float, float | None]]:
    """[(instante, nitidez, % de texto fora do titulo)] nos `ate_s` iniciais."""
    from PIL import Image
    pasta = Path(tempfile.mkdtemp(prefix="capa_"))
    t, out = 0.0, []
    while t < ate_s - 0.05:
        f = pasta / f"q_{int(t * 1000):05d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video),
                        "-frames:v", "1", "-vf", "scale=540:-2", str(f)],
                       check=True, capture_output=True, timeout=60)
        if f.exists():
            im = Image.open(f)
            out.append((t, nota_quadro(im.resize((360, round(im.height * 360 / im.width)))) * bonus_rosto(im),
                        texto_fora_do_titulo(im)))
        t += PASSO_S
    if not out:
        raise RuntimeError("nenhum quadro lido")
    return out


def aplicar_no_lugar(video: Path) -> bool:
    if not LIGADO:
        return False
    from . import midia
    from .render import TITULO_SEGUNDOS
    video = Path(video)
    novo = video.with_name(video.stem + "_capa.mp4")
    try:
        amostras = amostrar(video, TITULO_SEGUNDOS)
        t, nota, trocar = escolher(amostras)
        nota0, texto0 = amostras[0][1], amostras[0][2]
        sujos = sum(1 for a in amostras if a[2] is not None and a[2] > LIMITE_TEXTO)
        print(f"      capa: OCR {'ok' if texto0 is not None else 'AUSENTE (so nitidez)'}"
              f"; {sujos}/{len(amostras)} quadro(s) com texto da fonte"
              + (f"; quadro 0 tem {texto0:.0f}% de letras" if texto0 else ""))
        if not trocar:
            return False
        fps = midia.fps(video)
        q = 1.0 / fps
        ms = max(1, round(q * 1000))
        filtro = (f"[0:v]split[a][b];[b]trim=start={t:.3f}:duration={q:.5f},"
                  f"setpts=PTS-STARTPTS[c];[c][a]concat=n=2:v=1:a=0[v];"
                  f"[0:a]adelay={ms}:all=1[au]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                        "-filter_complex", filtro, "-map", "[v]", "-map", "[au]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", str(novo)],
                       check=True, capture_output=True, timeout=900)
        if not novo.exists() or novo.stat().st_size < 1000:
            raise RuntimeError("saida vazia")
        print(f"      capa: quadro de {t:.2f}s ({nota / max(nota0, 1e-9):.2f}x mais nitido "
              "que o 1o) virou o quadro 0")
    except Exception as e:
        print(f"      [!] capa nitida nao aplicada ({type(e).__name__})")
        novo.unlink(missing_ok=True)
        return False
    video.unlink(missing_ok=True)
    novo.rename(video)
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    print(aplicar_no_lugar(Path(ap.parse_args().video)))
