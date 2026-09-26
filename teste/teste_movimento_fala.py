# -*- coding: utf-8 -*-
"""O enquadramento corta JUNTO da fala (engine/render.py::_zoom_por_frase).

POR QUE EXISTE

26/09/2026 (análise "o que falta pra ficar premium", aprovada): o zoom era um
ciclo cego de 3 s. Agora o nível alterna 100% <-> 108% no início de cada frase
(jump cut em câmera única) e empurra 1%/s (teto 3%) dentro da frase.

  [1] cortes saem em pausa > 0,25 s e depois de ./!/?, nunca < 1,5 s entre si
  [2] a expressão do ffmpeg dá o zoom certo em cada quadro (avaliada aqui)
  [3] o ffmpeg ACEITA a expressão num render real de 6 s
  [4] NEGATIVO: sem fala medida, volta o ciclo antigo (vertical escolhe)

Roda com: python teste/teste_movimento_fala.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import render  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])

print("\n[1] onde corta")
ps = [{"palavra": "Essa", "inicio": 0.0, "fim": 0.3},
      {"palavra": "sala.", "inicio": 0.3, "fim": 0.7},
      {"palavra": "Custa", "inicio": 0.75, "fim": 1.0},      # após "." mas < 1,5 s do início? (1o corte)
      {"palavra": "caro", "inicio": 1.0, "fim": 1.4},
      {"palavra": "demais", "inicio": 2.0, "fim": 2.4},      # pausa 0,6 s, mas 1,25 s do corte anterior
      {"palavra": "E", "inicio": 3.0, "fim": 3.2},           # pausa 0,6 s
      {"palavra": "aqui", "inicio": 3.2, "fim": 3.5},
      {"palavra": "dentro", "inicio": 3.52, "fim": 3.9}]     # sem pausa
c = render.cortes_da_fala(ps)
print(f"       cortes {c}")
checar(c == [0.75, 3.0], "corta depois de '.' e na pausa, respeitando 1,5 s")
checar(render.cortes_da_fala([]) == [], "sem palavras, sem cortes")

print("\n[2] zoom em cada quadro")
render.midia.fps = lambda _b: 30.0
filtro = render._zoom_por_frase(Path("x.mp4"), 1080, 1920, [1.0, 3.0])
z = re.search(r"z='([^']+)'", filtro).group(1)
py = (z.replace("gte(", "_gte(").replace("mod(", "_mod(").replace("min(", "min("))


def zoom(on):
    return eval(py, {"_gte": lambda a, b: 1 if a >= b else 0,
                     "_mod": lambda a, b: a % b, "min": min, "on": on})


antes, logo, depois, fim, outro = zoom(0), zoom(30), zoom(30 + 60), zoom(89), zoom(90)
print(f"       0s {antes:.3f} | 1s {logo:.3f} | 3s-1q {fim:.3f} | 3s {outro:.3f}")
checar(abs(antes - 1.0) < 1e-9, "começa em 100%")
checar(abs(logo - 1.08) < 1e-9, "no 1o corte salta pra 108%")
checar(abs(fim - (1.08 + 0.0197)) < 0.002, "dentro da frase empurra ~1%/s")
checar(abs(outro - 1.0) < 1e-9, "no 2o corte volta pra 100% (sem herdar o empurrão)")
checar(zoom(30 + 30 * 10) <= 1.08 + 0.03 + 1e-9, "empurrão com teto de 3%")

print("\n[3] o ffmpeg aceita num render real")
T = Path(tempfile.mkdtemp())
src = T / "s.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                "testsrc2=s=1080x1920:r=30:d=6", str(src)], check=True)
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf",
                    filtro.lstrip(","), "-frames:v", "150", str(T / "o.mp4")],
                   capture_output=True, text=True)
checar(r.returncode == 0 and (T / "o.mp4").exists(), f"render ok {r.stderr[-120:]}")

print("\n[4] NEGATIVO: sem cortes volta o ciclo")
checar("cos(" in render._ken_burns(Path("x.mp4"), 1080, 1920), "ciclo antigo continua existindo")
src_v = (RAIZ / "engine" / "render.py").read_text(encoding="utf-8")
checar("if cortes" in src_v and "else _ken_burns(" in src_v, "vertical cai no ciclo sem cortes")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
