# -*- coding: utf-8 -*-
"""A decupagem (tirar pausas mortas) vale também para clipe DUBLADO.

POR QUE EXISTE

Até 26/09/2026 `midia.cortar_silencios` era pulado com --dublar ("a trilha
dublada é gerada pra duração do recorte original"). Como quase todo clipe é
dublado, a decupagem estava desligada na prática. A transcrição e a dublagem
já rodam DEPOIS dela; o único elo com a duração antiga era o `fim - ini`
passado ao gerador de voz.

  [1] cortar_silencios encurta um vídeo com pausas longas e deixa as curtas
  [2] main.py: a decupagem não depende mais de --dublar
  [3] main.py: os DOIS geradores de voz recebem a duração ENXUTA
  [4] NEGATIVO: no modo procedimento (maquiagem) não decupa

Roda com: python teste/teste_decupagem_dublada.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import midia  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])

print("\n[1] cortar_silencios")
T = Path(tempfile.mkdtemp())
# 10 s: fala 0-2, pausa LONGA 2-4, fala 4-6, pausa curta 6-6,2, fala 6,2-10
vol = "if(between(t,2,4)+between(t,6,6.2),0,0.5)"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=10",
                "-f", "lavfi", "-i", "sine=f=300:d=10", "-filter:a", f"volume='{vol}':eval=frame",
                "-shortest", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
                str(T / "c.mp4")], check=True)
saida = midia.cortar_silencios(T / "c.mp4", T / "e.mp4")
d = midia.duracao(saida)
print(f"       10,0 s -> {d:.2f} s")
checar(saida != T / "c.mp4" and 7.8 < d < 8.6, "a pausa de 2 s sai (fica a folga), a de 0,2 s fica")

print("\n[2]-[4] o main.py")
src = (RAIZ / "main.py").read_text(encoding="utf-8")
bloco = re.search(r"if config\.CORTAR_SILENCIOS and ([^:]+):", src)
checar(bloco is not None and "dublar" not in bloco.group(1), "decupagem não depende de --dublar")
checar("_procedimento" in (bloco.group(1) if bloco else ""), "NEGATIVO: procedimento não decupa")
chamadas = re.findall(r"gerar_trilha\(\s*segmentos,\s*([^,]+),", src)
checar(len(chamadas) == 2 and all(c.strip() == "dur_final" for c in chamadas),
       f"os dois geradores de voz recebem dur_final ({chamadas})")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
