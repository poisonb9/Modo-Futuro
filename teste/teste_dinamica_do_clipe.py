# -*- coding: utf-8 -*-
"""A dinâmica da dublagem mede o CLIPE, não o vídeo-fonte inteiro.

POR QUE EXISTE

De 01/09 a 26/09/2026 o `main.py` chamava `voz_clonada.gerar_trilha(...,
fonte=fonte)` com o vídeo ORIGINAL inteiro. Os tempos dos segmentos são
relativos ao CLIPE (a transcrição é do próprio clipe), e `dinamica._pcm` lê
o arquivo nesses segundos sem deslocamento. Toda dublagem copiava a ênfase,
o volume e as pausas do COMEÇO do vídeo original — nada no log acusava.

  [1] positivo: com o clipe, a medida cai no trecho certo
  [2] negativo: com a fonte inteira + tempo do clipe, cai no trecho errado
      (prova que o teste enxerga o defeito)
  [3] o main.py passa `bruto` (o clipe), não `fonte`

Roda com: python teste/teste_dinamica_do_clipe.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import dinamica  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])
T = Path(tempfile.mkdtemp())
# "fonte": 20 s — 0-10 s baixinho, 10-20 s ALTO. O "clipe" é o trecho 10-20 s.
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=300:d=20",
                "-af", "volume='if(lt(t,10),0.02,0.8)':eval=frame", "-ar", "16000",
                str(T / "fonte.wav")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "10", "-t", "10", "-i",
                str(T / "fonte.wav"), str(T / "clipe.wav")], check=True)

bloco = [(1.0, 4.0)]   # tempo RELATIVO ao clipe
certo = dinamica.medir_blocos(T / "clipe.wav", bloco)[0]["db"]
errado = dinamica.medir_blocos(T / "fonte.wav", bloco)[0]["db"]
print(f"       clipe {certo:.1f} dB | fonte inteira {errado:.1f} dB")

alto = dinamica.medir_blocos(T / "fonte.wav", [(11.0, 14.0)])[0]["db"]
print("\n[1] com o clipe, mede o trecho alto")
checar(abs(certo - alto) < 1.5, f"clipe 1-4 s == fonte 11-14 s ({alto:.1f} dB)")
print("\n[2] NEGATIVO: com a fonte inteira, mede o trecho errado")
checar(errado < certo - 20, "a fonte inteira no mesmo tempo cai no trecho baixo")

print("\n[3] o main.py passa o CLIPE")
src = (RAIZ / "main.py").read_text(encoding="utf-8")
chamada = re.search(r"voz_clonada\.gerar_trilha\((.*?)\n\s*# a legenda", src, re.S)
checar(chamada is not None and re.search(r"fonte=bruto\)", chamada.group(1)) is not None,
       "gerar_trilha(..., fonte=bruto)")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
