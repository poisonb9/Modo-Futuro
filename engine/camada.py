# -*- coding: utf-8 -*-
"""Camada animada sobre o 9:16.

    python -m engine.camada --previa saida/x.mp4 [--video fundo.mp4]
    python -m engine.camada --video c.mp4 --canal <canal>
"""
from __future__ import annotations

import argparse
import math
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ATIVOS = Path(__file__).resolve().parent / "camada"
W, H, FPS = 1080, 1920, 30
DUR = 16.0
FOLGA = 22
BORDA = 1000
FIM_ANTES_S = 0.6

POS = {"a": (928, 1100), "e1": (795, 1250), "e2": (795, 1590), "e3": (250, 1585)}

CANAIS: set[str] = set()


def _img(nome: str, largura: int) -> Image.Image:
    im = Image.open(ATIVOS / f"{nome}.webp").convert("RGBA")
    return im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)


def _mola(t: float) -> float:
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 1 - math.exp(-6 * t) * math.cos(9 * t)


def _suave(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class _Sobe:
    def __init__(self, im, t0, dur, x0, y0, deriva, fase, amp):
        self.im, self.t0, self.dur = im, t0, dur
        self.x0, self.y0, self.deriva, self.fase, self.amp = x0, y0, deriva, fase, amp

    def quadro(self, t):
        u = (t - self.t0) / self.dur
        if u < 0 or u > 1:
            return None
        esc = 0.15 + 0.85 * _suave(u / 0.2)
        y = self.y0 - (self.y0 + self.im.height) * (u ** 1.15)
        x = self.x0 - self.deriva * u + self.amp * math.sin(self.fase + u * 7)
        return self.im, x, y, esc, 8 * math.sin(self.fase + u * 5), min(1.0, u / 0.08)


class _Para:
    def __init__(self, im, t0, fica, x, y):
        self.im, self.t0, self.fica, self.x, self.y = im, t0, fica, x, y

    def quadro(self, t):
        u = t - self.t0
        entra, sai = 0.9, 0.8
        if u < 0 or u > entra + self.fica + sai:
            return None
        esc = 0.85 + 0.15 * _mola(u / entra)
        dy = 420 * (1 - _mola(u / entra))
        alfa = min(1.0, u / 0.2)
        fim = u - entra - self.fica
        if fim > 0:
            k = _suave(fim / sai)
            dy += 520 * k
            alfa *= 1 - k
        return (self.im, self.x, self.y + dy + 10 * math.sin(u * 2.4), esc,
                4 * math.sin(u * 1.7), alfa)


class _Cruza:
    ENTRA, SAI = 1.4, 1.4

    def __init__(self, t0, fica=3.4, y=360):
        self.t0, self.fica, self.y = t0, fica, y
        self.dur = self.ENTRA + fica + self.SAI
        self.av = _img("v1", 330)
        self.fx = _img("v2", 600)
        self.cd = Image.open(ATIVOS / "v3.webp").convert("RGBA")

    def _onda(self, t):
        f = self.fx
        out = Image.new("RGBA", (f.width, f.height + 40), (0, 0, 0, 0))
        w = f.width // 120 + 1
        for x0 in range(0, f.width, w):
            fat = f.crop((x0, 0, min(x0 + w, f.width), f.height))
            dy = 20 + 14 * (x0 / f.width) * math.sin(t * 7 - x0 / 55)
            out.alpha_composite(fat, (x0, int(dy)))
        return out

    def pintar(self, tela, t):
        tt = t - self.t0
        if tt < 0 or tt > self.dur:
            return
        vao = 90
        total = self.av.width + vao + self.fx.width
        meio = (W - total) / 2
        if tt < self.ENTRA:
            k = 1 - (1 - tt / self.ENTRA) ** 3
            x = W + 40 + (meio - W - 40) * k
        elif tt < self.ENTRA + self.fica:
            x = meio - 25 * ((tt - self.ENTRA) / self.fica)
        else:
            k = ((tt - self.ENTRA - self.fica) / self.SAI) ** 2
            x = meio - 25 - (meio - 25 + total + 60) * k
        y = self.y + 12 * math.sin(t * 2.2)
        av = self.av.rotate(3 * math.sin(t * 1.8), Image.BICUBIC, expand=True)
        fx = self._onda(t)
        xa, ya = int(x), int(y - av.height / 2)
        xf, yf = int(x + self.av.width + vao), int(y - fx.height / 2 + 30)
        x1, y1 = xa + self.av.width - 40, int(y + 10)
        x2, y2 = xf + 14, yf + fx.height // 2
        comp = max(10, int(math.hypot(x2 - x1, y2 - y1)))
        c = self.cd.resize((comp, max(8, round(self.cd.height * comp / self.cd.width * 3.2))))
        c = c.rotate(-math.degrees(math.atan2(y2 - y1, x2 - x1)), Image.BICUBIC, expand=True)
        tela.alpha_composite(c, (int((x1 + x2) / 2 - c.width / 2),
                                 int((y1 + y2) / 2 - c.height / 2)))
        if xf < W:
            tela.alpha_composite(fx, (xf, yf))
        if -av.width < xa < W:
            tela.alpha_composite(av, (xa, ya))


def cena(n: int = 6, semente: int = 7) -> list:
    rnd = random.Random(semente)
    base = [_img("c1", 150), _img("c2", 150)]
    els: list = []
    t, passo = 0.3, 0.14
    bx, by = POS["a"]
    for i in range(n):
        b = base[i % 2]
        w = rnd.randint(105, 165)
        els.append(_Sobe(b.resize((w, round(b.height * w / b.width))), t,
                         rnd.uniform(1.5, 1.9), bx + rnd.uniform(-FOLGA, FOLGA),
                         by + rnd.uniform(-FOLGA, FOLGA), rnd.uniform(60, 240),
                         rnd.uniform(0, 6.28), rnd.uniform(12, 30)))
        t += passo
        passo *= 1.35
    els.append(_Sobe(_img("c2", 190), t + 0.25, 3.4, bx, by, 110, 1.0, 12))
    els.append(_Para(_img("e1", 190), 4.3, 1.3, *POS["e1"]))
    els.append(_Para(_img("e2", 200), 6.9, 1.3, *POS["e2"]))
    els.append(_Para(_img("e3", 210), 9.5, 3.4, *POS["e3"]))
    els.append(_Cruza(9.5, fica=3.4))
    return els


def pintar(fundo: Image.Image, els, t) -> Image.Image:
    tela = fundo.copy()
    for e in els:
        if isinstance(e, _Cruza):
            e.pintar(tela, t)
            continue
        q = e.quadro(t)
        if not q:
            continue
        im, x, y, esc, ang, alfa = q
        p = im.resize((max(2, int(im.width * esc)), max(2, int(im.height * esc))),
                      Image.BILINEAR).rotate(ang, Image.BICUBIC, expand=True)
        if alfa < 1:
            p.putalpha(p.getchannel("A").point(lambda v: int(v * alfa)))
        x = min(x, BORDA - p.width / 2)
        tela.alpha_composite(p, (int(x - p.width / 2), int(y - p.height * 0.28)))
    return tela


def _guias(im: Image.Image) -> Image.Image:
    from PIL import ImageDraw
    im = im.copy()
    d = ImageDraw.Draw(im, "RGBA")
    for y in (878, 1058, 1223, 1388, 1559):
        d.ellipse([912, y - 42, 996, y + 42], outline=(255, 255, 255, 170), width=4)
        d.ellipse([858, y + 48, 942, y + 132], outline=(255, 214, 0, 170), width=4)
    d.line([(BORDA, 0), (BORDA, H)], fill=(255, 80, 80, 90), width=2)
    d.rounded_rectangle([60, 1640, 420, 1695], 12, outline=(255, 255, 255, 170), width=4)
    return im


def gerar(saida: Path, fundo_video: Path | None = None, previa: bool = False,
          n: int = 6) -> Path:
    """`previa`: mp4 com fundo e guias. Senao: .mov com alfa (ProRes 4444)."""
    els = cena(n)
    quadros = int(DUR * FPS)
    if previa:
        enc = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20"]
    else:
        enc = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *enc, str(saida)]
    vazio = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    liso = Image.new("RGBA", (W, H), (40, 38, 46, 255))
    fundo = None
    if previa and fundo_video:
        bruto = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-ss", "30", "-i", str(fundo_video),
             "-t", str(DUR), "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
            capture_output=True).stdout
        tam = W * H * 4
        fundo = [bruto[i:i + tam] for i in range(0, len(bruto) - tam + 1, tam)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(quadros):
        if not previa:
            base = vazio
        elif fundo:
            base = _guias(Image.frombytes("RGBA", (W, H), fundo[min(i, len(fundo) - 1)]))
        else:
            base = _guias(liso)
        p.stdin.write(pintar(base, els, i / FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg falhou ao gerar a camada")
    return saida


_CACHE: dict[str, Path] = {}


def _mov() -> Path:
    if "mov" not in _CACHE or not _CACHE["mov"].exists():
        _CACHE["mov"] = gerar(Path(tempfile.mkdtemp()) / "camada.mov")
    return _CACHE["mov"]


def ligado(canal: str) -> bool:
    from . import canais_registro
    nome = canais_registro.canonico(canal)
    return bool(nome) and nome in CANAIS


def aplicar(video: Path, destino: Path) -> Path | None:
    """Sobrepoe a camada terminando perto do fim do video. None se nao deu."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    dur = float(r.stdout.strip())
    ini = max(0.0, dur - DUR - FIM_ANTES_S)
    filtro = (f"[1:v]setpts=PTS-STARTPTS+{ini:.3f}/TB[c];"
              f"[0:v][c]overlay=0:0:eof_action=pass:format=auto[v]")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(_mov()),
         "-filter_complex", filtro, "-map", "[v]", "-map", "0:a?",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-c:a", "copy", "-movflags", "+faststart", str(destino)],
        check=True, capture_output=True)
    return destino


def aplicar_no_lugar(video: Path, canal: str) -> bool:
    """Troca o arquivo so' se o novo existir e abrir. Falha aberta."""
    video = Path(video)
    if not ligado(canal):
        return False
    novo = video.with_name(video.stem + "_c.mp4")
    try:
        aplicar(video, novo)
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(novo)], capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            raise RuntimeError("saida nao abre")
    except Exception as e:
        print(f"      [!] camada falhou ({type(e).__name__}) — video sem ela")
        novo.unlink(missing_ok=True)
        return False
    video.unlink(missing_ok=True)
    novo.rename(video)
    return True


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--previa", metavar="MP4")
    a.add_argument("--video", type=Path)
    a.add_argument("--canal")
    a.add_argument("--n", type=int, default=6)
    o = a.parse_args()
    if o.previa:
        Path(o.previa).parent.mkdir(parents=True, exist_ok=True)
        print(gerar(Path(o.previa), o.video, previa=True, n=o.n))
    elif o.video:
        CANAIS.add(o.canal or "")
        destino = o.video.with_name(o.video.stem + "_c.mp4")
        print(aplicar(o.video, destino))


if __name__ == "__main__":
    main()
