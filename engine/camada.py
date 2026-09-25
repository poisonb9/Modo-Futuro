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
FOLGA = 22
REVELA_ANTES_S = 2.8
FICA_E = 2.0          # comente e compartilhe parados (dono: "mais tempo", 25/09)
BORDA = 1000
INICIO_S = 3.0          # respiro depois do titulo (dono, 25/09)
DUR_A = 9.6
DUR_B = 6.2
B_FRAC = 0.40
B_MIN_S = 16.0
B_FIM_S = 3.0

# Uma camada por plataforma: cada balao ao lado do SEU botao, e os botoes
# do Reels ficam ~250 px mais altos que os do TikTok (medido em 25/09).
# "esc" reduz comente/compartilhe/siga; "e2" e' a peca do compartilhe.
PLAT = {
    "tiktok": {"pos": {"a": (928, 1100), "e1": (795, 1250), "e2": (795, 1590),
                       "e3": (250, 1555)},
               "e2": ("e2", 200), "esc": 0.8},
    "reels": {"pos": {"a": (886, 848), "e1": (760, 992), "e2": (760, 1327),
                      "e3": (250, 1345)},
              "e2": ("e2r", 230), "esc": 0.8},
}
POS = PLAT["tiktok"]["pos"]
SUFIXO = {"tiktok": "", "reels": "_reels"}
ENTRA, SAI = 0.9, 0.8
MARGEM_COLUNA = 0.20
FICA = {"e1": FICA_E, "e2": FICA_E, "e3": 3.4}
LARG = {"e1": 190, "e3": 210}


def arquivo(plat: str) -> str:
    return f"short_9x16{SUFIXO[plat]}.mp4"


VAO = 0.25          # respiro entre um balao sair e o proximo entrar


def _coracoes(n: int = 6, semente: int = 7, plat: str = "tiktok") -> list:
    rnd = random.Random(semente)
    base = [_img("c1", 150), _img("c2", 150)]
    bx, by = PLAT[plat]["pos"]["a"]
    els: list = []
    t, passo = 0.0, 0.12
    for i in range(n):
        b = base[i % 2]
        w = rnd.randint(105, 165)
        els.append(_Sobe(b.resize((w, round(b.height * w / b.width))), t,
                         rnd.uniform(1.5, 1.9), bx + rnd.uniform(-FOLGA, FOLGA),
                         by + rnd.uniform(-FOLGA, FOLGA), rnd.uniform(60, 240),
                         rnd.uniform(0, 6.28), rnd.uniform(12, 30)))
        t += passo
        passo *= 1.3
    els.append(_Sobe(_img("c2", 190), t + 0.15, 3.0, bx, by, 110, 1.0, 12))
    return els


def tempos(n: int = 6) -> dict[str, float]:
    """Inicio de cada balao parado. ⛔ NUNCA DOIS BALOES NA TELA (dono,
    25/09): cada um so' entra quando o anterior saiu — coracoes (a rajada
    conta como um), depois comente, compartilhe e siga."""
    fim = max(e.t0 + e.dur for e in _coracoes(n))
    out = {}
    for e in ("e1", "e2", "e3"):
        out[e] = fim + VAO
        fim = out[e] + ENTRA + FICA[e] + SAI
    return out


def dur_a(plat: str = "tiktok", n: int = 6) -> float:
    t = tempos(n)
    return t["e3"] + ENTRA + FICA["e3"] + SAI

CANAIS: set[str] = {"truque.importado"}


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

    def __init__(self, t0, fica=3.4, y=370):     # abaixo de "Para voce"/"Reels" (25/09)
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


def cena(n: int = 6, semente: int = 7, parte: str = "a",
         plat: str = "tiktok") -> list:
    if parte == "b":
        return [_Cruza(0.0, fica=3.4)]
    els = _coracoes(n, semente, plat)
    t = tempos(n)
    pos = PLAT[plat]["pos"]
    for e, im in _parados(plat):
        els.append(_Para(im, t[e], FICA[e], *pos[e]))
    return els


def _parados(plat: str) -> list:
    cfg = PLAT[plat]
    e2, l2 = cfg["e2"]
    return [("e1", _img("e1", round(LARG["e1"] * cfg["esc"]))),
            ("e2", _img(e2, round(l2 * cfg["esc"]))),
            ("e3", _img("e3", round(LARG["e3"] * cfg["esc"])))]


def janelas(plat: str = "tiktok") -> list[tuple[float, float, float, str]]:
    """[(inicio, fim, fracao, lado)] no tempo do video final: enquanto um
    balao parado cruza a faixa da legenda, ela abre espaco do lado dele."""
    from .legendas import faixa_ocupada
    topo, base = faixa_ocupada(H)
    topo -= 40                                   # linha que cresce no estilo 2
    # a coluna de botoes (e os numeros) fica na altura da legenda nos dois
    # apps: frase longa nunca passa de x ~865 (medido nos prints, 25/09).
    # Margem IGUAL dos dois lados: so' a' direita, a legenda ficava sempre
    # fora do centro e parecia "nao voltar" depois do balao (dono, 25/09).
    out = [(0.0, 1e9, MARGEM_COLUNA, "ambos")]
    for e, im in _parados(plat):
        x, y = PLAT[plat]["pos"][e]
        a = im.getchannel("A").point(lambda v: 255 if v > 40 else 0)
        # so' o corpo do balao conta; a fita fina pode cruzar o texto
        corpo = a.crop((0, 0, im.width, int(im.height * 0.62))).getbbox()
        if not corpo:
            continue
        y0 = y - im.height * 0.28 + corpo[1]
        y1 = y - im.height * 0.28 + corpo[3]
        if y1 < topo or y0 > base:
            continue
        ini = INICIO_S + tempos()[e]
        out.append((ini, ini + ENTRA + FICA[e] + SAI, 0.40,
                    "esq" if x < W / 2 else "dir"))
    return out


def janela_comente() -> tuple[float, float, float]:
    """(inicio, fim, fracao da largura) em que o balao de comentario ocupa o
    lado direito, no tempo do video final."""
    ini = INICIO_S + 1.8
    return (ini, ini + 0.9 + FICA_E + 0.8, 0.40)


def plano(dur_video: float, plat: str = "tiktok") -> list[tuple[str, float]]:
    """[(parte, inicio_s)] que cabem neste video."""
    p = [("a", INICIO_S)] if dur_video >= INICIO_S + dur_a(plat) * 0.6 else []
    # o aviao tambem e' balao: so' depois de a parte A inteira sair
    ib = max(B_FRAC * dur_video, B_MIN_S, INICIO_S + dur_a(plat) + VAO)
    if ib + DUR_B <= dur_video - B_FIM_S:
        p.append(("b", ib))
    return p


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


def gerar(saida: Path, parte: str = "a", n: int = 6, plat: str = "tiktok") -> Path:
    """.mov com alfa (ProRes 4444) de uma parte."""
    els = cena(n, parte=parte, plat=plat)
    quadros = int((dur_a(plat) if parte == "a" else DUR_B) * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "prores_ks",
           "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(saida)]
    vazio = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(quadros):
        p.stdin.write(pintar(vazio, els, i / FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg falhou ao gerar a camada")
    return saida


def previa(saida: Path, fundo_video: Path | None = None, dur: float = 30.0,
           n: int = 6, plat: str = "tiktok") -> Path:
    """mp4 simulando um video de `dur` s, com as partes nos seus momentos."""
    partes = [(cena(n, parte=k, plat=plat), ini, dur_a(plat) if k == "a" else DUR_B)
              for k, ini in plano(dur, plat)]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
           "-pix_fmt", "yuv420p", "-crf", "22", str(saida)]
    liso = Image.new("RGBA", (W, H), (40, 38, 46, 255))
    src = None
    if fundo_video:
        src = subprocess.Popen(
            ["ffmpeg", "-loglevel", "error", "-ss", "30", "-i", str(fundo_video), "-t",
             str(dur), "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
            stdout=subprocess.PIPE)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    tam = W * H * 4
    for i in range(int(dur * FPS)):
        t = i / FPS
        raw = src.stdout.read(tam) if src else b""
        base = _guias(Image.frombytes("RGBA", (W, H), raw) if len(raw) == tam else liso)
        for els, ini, d in partes:
            if ini <= t < ini + d:
                base = pintar(base, els, t - ini)
        p.stdin.write(base.tobytes())
    p.stdin.close()
    p.wait()
    return saida


_CACHE: dict[str, Path] = {}


def _mov(parte: str, plat: str = "tiktok") -> Path:
    chave = f"{plat}_{parte}"
    if chave not in _CACHE or not _CACHE[chave].exists():
        _CACHE[chave] = gerar(Path(tempfile.mkdtemp()) / f"{chave}.mov", parte,
                              plat=plat)
    return _CACHE[chave]


def ligado(canal: str) -> bool:
    from . import canais_registro
    nome = canais_registro.canonico(canal)
    return bool(nome) and nome in CANAIS


def aplicar(video: Path, destino: Path, plat: str = "tiktok") -> Path | None:
    """Sobrepoe as partes que cabem (ver `plano`). None se nada cabe."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    pl = plano(float(r.stdout.strip()), plat)
    if not pl:
        return None
    entradas, filtros, ant = [], [], "0:v"
    for i, (k, ini) in enumerate(pl, start=1):
        entradas += ["-i", str(_mov(k, plat))]
        filtros.append(f"[{i}:v]setpts=PTS-STARTPTS+{ini:.3f}/TB[c{i}];"
                       f"[{ant}][c{i}]overlay=0:0:eof_action=pass:format=auto[v{i}]")
        ant = f"v{i}"
    # sons: estalo em cada coracao (parte A) + sino na revelacao (fim)
    dur = float(r.stdout.strip())
    momentos = []
    for k, ini in pl:
        if k == "a":
            pass   # estalo nos coracoes: REPROVADO pelo dono (25/09)
    if dur > REVELA_ANTES_S + 4:
        momentos.append(("s2", dur - REVELA_ANTES_S, 1.0))
    n = 1 + len(pl)
    audio, rotulos = [], []
    for j, (som, t, vol) in enumerate(momentos):
        entradas += ["-i", str(ATIVOS / f"{som}.wav")]
        ms = int(t * 1000)
        audio.append(f"[{n + j}:a]adelay={ms}|{ms},volume={vol}[x{j}]")
        rotulos.append(f"[x{j}]")
    tem_audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True).stdout.strip() != ""
    if momentos and tem_audio:
        filtros += audio
        filtros.append(f"[0:a]{''.join(rotulos)}amix=inputs={len(rotulos) + 1}:"
                       f"normalize=0:duration=first[aa]")
        mapa_a, cod_a = ["-map", "[aa]"], ["-c:a", "aac", "-b:a", "192k"]
    else:
        mapa_a, cod_a = ["-map", "0:a?"], ["-c:a", "copy"]
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video), *entradas,
         "-filter_complex", ";".join(filtros), "-map", f"[{ant}]", *mapa_a,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         *cod_a, "-movflags", "+faststart", str(destino)],
        check=True, capture_output=True)
    return destino


def _abre(arq: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True)
    return r.returncode == 0 and bool(r.stdout.strip())


def aplicar_no_lugar(video: Path, canal: str, plat: str = "tiktok") -> bool:
    """Troca o arquivo so' se o novo existir e abrir. Falha aberta."""
    video = Path(video)
    if not ligado(canal):
        return False
    novo = video.with_name(video.stem + "_c.mp4")
    try:
        if aplicar(video, novo, plat) is None:
            return False
        if not _abre(novo):
            raise RuntimeError("saida nao abre")
    except Exception as e:
        print(f"      [!] camada {plat} falhou ({type(e).__name__}) — video sem ela")
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
    a.add_argument("--dur", type=float, default=30.0)
    a.add_argument("--plat", default="tiktok", choices=sorted(PLAT))
    o = a.parse_args()
    if o.previa:
        Path(o.previa).parent.mkdir(parents=True, exist_ok=True)
        print(previa(Path(o.previa), o.video, o.dur, o.n, o.plat))
    elif o.video:
        CANAIS.add(o.canal or "")
        destino = o.video.with_name(o.video.stem + (SUFIXO[o.plat] or "_c") + ".mp4")
        print(aplicar(o.video, destino, o.plat))


if __name__ == "__main__":
    main()
