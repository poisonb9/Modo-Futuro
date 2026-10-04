# -*- coding: utf-8 -*-
"""Wallpaper holografico no MODO PSICODELICO (04/10/2026).

Receita tirada das referencias (ver _privado/wallpaper/analise_gemini/RELATORIO_OBJETOS.md):
- icones GIRAM em 3D (eixo Y), um de cada vez, em fases diferentes;
- um evento-surpresa por ciclo (o coracao bate);
- a personagem fica PARADA; so' a cor desce pelas mechas e pelo vestido;
- moldura e barra da janela: so' ciclo de matiz;
- globo de cristal: facetas trocam de cor girando (sem objeto dentro);
- luzes do camarim e estrelas piscam. Loop FECHADO (tudo periodico no ciclo).

    python -X utf8 ferramentas/animar_wallpaper_psico.py imagem.png objetos.json saida_sem_extensao

Saida: <saida>.mp4 (tamanho real) e <saida>.gif (<5 MB, para compartilhar).
O objetos.json diz onde esta' cada coisa na imagem (caixas em pixels).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np


def _recorte(img, box):
    """Mascara suave do objeto (GrabCut dentro da caixa)."""
    x0, y0, x1, y1 = box
    m = np.zeros(img.shape[:2], np.uint8)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, m, (x0, y0, x1 - x0, y1 - y0), bg, fg, 5, cv2.GC_INIT_WITH_RECT)
    obj = np.where((m == 1) | (m == 3), 1.0, 0.0).astype(np.float32)
    return cv2.GaussianBlur(obj, (3, 3), 0)


def _matiz(rgb, graus, peso):
    """Gira o matiz por pixel (graus pode ser mapa), misturado por peso."""
    hsv = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    hsv[..., 0] = (hsv[..., 0] + np.asarray(graus) * 256 / 360) % 256
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB_FULL).astype(np.float32)
    p = peso[..., None]
    return np.asarray(rgb, np.float32) * (1 - p) + out * p


def _ease(u):
    return 0.5 - 0.5 * np.cos(np.pi * np.clip(u, 0, 1))


def preparar(img, cfg):
    H, W = img.shape[:2]
    giros = [(g, _recorte(img, g["box"])) for g in cfg["giros"]]
    batidas = [(g, _recorte(img, g["box"])) for g in cfg["batidas"]]
    todos = np.zeros((H, W), np.float32)
    a = cfg["asas"]
    ax0, ay0, ax1, ay1 = a["box"]
    asas_full = _recorte(img, a["box"])
    for obj in [o for _, o in giros + batidas] + [asas_full]:
        todos = np.maximum(todos, cv2.dilate(obj, np.ones((7, 7))))
    limpa = cv2.inpaint(img, (todos > 0.1).astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA).astype(np.float32)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    h, s, v = (hsv[..., i].astype(np.float32) for i in range(3))
    # mulher: SO' a silhueta (GrabCut na caixa), menos a pele (poligonos do json), pesada
    # pela saturacao: cabelo e vestido iridescentes mudam, meia branca e pele nao.
    sil = _recorte(img, cfg["mulher"]["box"])
    pele = np.zeros((H, W), np.uint8)
    for poli in cfg["mulher"].get("pele", []):
        cv2.fillPoly(pele, [np.int32(poli)], 1)
    pele = cv2.GaussianBlur(pele.astype(np.float32), (0, 0), 6)
    mulher = sil * (1 - pele) * np.clip((s - 25) / 60, 0, 1) * np.clip((v - 90) / 80, 0, 1)
    mulher = cv2.GaussianBlur(mulher, (0, 0), 2)
    # moldura e barra da janela
    b = cfg["moldura_px"]
    mold = np.zeros((H, W), np.float32)
    mold[:b] = 1; mold[-b:] = 1; mold[:, :b] = 1; mold[:, -b:] = 1
    bx0, by0, bx1, by1 = cfg["barra"]
    mold[by0:by1, bx0:bx1] = np.maximum(mold[by0:by1, bx0:bx1], 0.7)
    perim = (np.arctan2(yy - H / 2, xx - W / 2) / (2 * np.pi)) % 1
    # globo
    cx, cy = cfg["globo"]["centro"]
    r = cfg["globo"]["raio"]
    dist = np.hypot(xx - cx, yy - cy)
    globo = np.clip((r - dist) / 6, 0, 1).astype(np.float32)
    ang = np.arctan2(yy - cy, xx - cx)
    # luzes que piscam (so' o que ja' e' claro)
    luz = np.zeros((H, W), np.float32)
    for L in cfg["luzes"]:
        if "centro" in L:
            lx, ly = L["centro"]
            luz = np.maximum(luz, np.clip((L["raio"] - np.hypot(xx - lx, yy - ly)) / 10, 0, 1))
        else:
            lx0, ly0, lx1, ly1 = L["box"]
            luz[ly0:ly1, lx0:lx1] = 1
    luz *= np.clip((v - 200) / 55, 0, 1)
    asas = asas_full[ay0:ay1, ax0:ax1]
    return dict(giros=giros, batidas=batidas, todos=todos, limpa=limpa, mulher=mulher, mold=mold,
                perim=perim, globo=globo, ang=ang, dist=dist, luz=luz, yy=yy, xx=xx, asas=asas)


def _colar(fundo, img, obj, box, sx, sy=1.0, brilho=0.0):
    """Cola o objeto escalado a partir do centro da propria caixa (sx<0 = espelhado)."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    H, W = fundo.shape[:2]
    pad = int(max(x1 - x0, y1 - y0) * max(0, abs(sy) - 1)) + 4
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    gx, gy = np.meshgrid(np.arange(X0, X1, dtype=np.float32), np.arange(Y0, Y1, dtype=np.float32))
    mx = (cx + (gx - cx) / sx).astype(np.float32)
    my = (cy + (gy - cy) / sy).astype(np.float32)
    rgb = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT).astype(np.float32)
    al = cv2.remap(obj, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None]
    rgb = np.clip(rgb * (1 + brilho), 0, 255)
    fundo[Y0:Y1, X0:X1] = fundo[Y0:Y1, X0:X1] * (1 - al) + rgb * al


def quadro(img, cfg, P, t):
    """Um quadro; t em [0,1) do ciclo."""
    T = cfg["loop_s"]
    seg = t * T
    yy, xx = P["yy"], P["xx"]
    # 1) personagem: onda de matiz DESCENDO (2 ciclos por loop) + faixa clara descendo
    onda = np.sin(2 * np.pi * (2 * t - yy / 420))
    f = _matiz(img, 45 * onda, P["mulher"] * 0.9)
    faixa = np.exp(-((((yy / 380 - 2 * t) % 1) - 0.5) / 0.07) ** 2)
    f += (P["mulher"] * faixa * 38)[..., None]
    # 2) moldura e barra: matiz correndo em volta (1 volta por loop)
    f = _matiz(f, 360 * ((P["perim"] * 3 - t) % 1), P["mold"] * 0.85)
    # 3) globo: facetas trocam de cor girando + reflexo dando a volta
    g = 360 * ((P["ang"] / (2 * np.pi) * 2 + P["dist"] / 120 - t * 2) % 1)
    f = _matiz(f, g, P["globo"] * 0.75)
    esp = np.exp(-((((P["ang"] - 2 * np.pi * t + np.pi) % (2 * np.pi)) - np.pi) / 0.35) ** 2) * P["globo"]
    f += (esp * 45)[..., None]
    # 4) luzes do camarim e estrelas do frontao piscam
    pisca = 0.5 + 0.5 * np.sin(2 * np.pi * (4 * t + xx / 90 + yy / 70))
    f += (P["luz"] * pisca * 60)[..., None]
    f = np.clip(f, 0, 255)
    # 5) objetos: fundo limpo no lugar deles, e recoloca girando
    tm = P["todos"][..., None]
    f = f * (1 - tm) + P["limpa"] * tm
    for g_, obj in P["giros"]:
        u = ((seg - g_["ini"]) % T) / g_["dur"]
        th = 2 * np.pi * _ease(u) if u <= 1 else 0.0
        sx = np.cos(th)
        sx = np.sign(sx or 1) * max(abs(sx), 0.04)
        _colar(f, img, obj, g_["box"], sx, 1.0, brilho=0.35 * abs(np.sin(th)))
    for g_, obj in P["batidas"]:
        k = 1.0 + sum(0.22 * np.exp(-((seg - tb) / 0.07) ** 2) for tb in g_["tempos"])
        _colar(f, img, obj, g_["box"], k, k, brilho=(k - 1) * 1.2)
    # 6) asas da borboleta batem (escala X a partir do corpo)
    a = cfg["asas"]
    x0, y0, x1, y1 = a["box"]
    bat = 0.89 + 0.11 * np.cos(2 * np.pi * seg / a["periodo"])
    cx = a["centro_x"] - x0
    gx = np.arange(x1 - x0, dtype=np.float32)
    mapx = np.tile(cx + (gx - cx) / bat, (y1 - y0, 1)).astype(np.float32)
    mapy = np.tile(np.arange(y1 - y0, dtype=np.float32)[:, None], (1, x1 - x0))
    src = img[y0:y1, x0:x1].astype(np.float32)
    am = cv2.remap(P["asas"], mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None]
    warped = cv2.remap(src, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    reg = f[y0:y1, x0:x1]  # ja' tem o fundo limpo onde a borboleta estava
    f[y0:y1, x0:x1] = reg * (1 - am) + warped * am
    return np.clip(f, 0, 255).astype(np.uint8)


def main() -> None:
    src, cfgp, saida = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    cfg = json.loads(cfgp.read_text(encoding="utf-8"))
    img = cv2.cvtColor(cv2.imread(str(src)), cv2.COLOR_BGR2RGB)
    img = img[: img.shape[0] // 2 * 2, : img.shape[1] // 2 * 2].copy()
    P = preparar(img, cfg)
    n = int(cfg["loop_s"] * cfg["fps"])
    pasta = Path(tempfile.mkdtemp())
    for i in range(n):
        cv2.imwrite(str(pasta / f"{i:03d}.png"), cv2.cvtColor(quadro(img, cfg, P, i / n), cv2.COLOR_RGB2BGR))
    fps = str(cfg["fps"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", fps, "-i", str(pasta / "%03d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(saida.with_suffix(".mp4"))], check=True)
    gif = saida.with_suffix(".gif")
    for larg, cores, gfps in ((360, 128, 12), (320, 96, 12), (300, 64, 10), (270, 48, 8)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", fps, "-i", str(pasta / "%03d.png"),
                        "-vf", f"fps={gfps},scale={larg}:-2:flags=lanczos,split[a][b];"
                               f"[a]palettegen=max_colors={cores}:stats_mode=diff[p];"
                               f"[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                        str(gif)], check=True)
        if gif.stat().st_size < 5e6:
            break
    for p in pasta.glob("*.png"):
        p.unlink()
    pasta.rmdir()
    for p in (saida.with_suffix(".mp4"), gif):
        print(p, round(p.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
