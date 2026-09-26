# -*- coding: utf-8 -*-
"""A cauda do conversor de timbre (voz D) e' aparada (RETOMADA §1.3).

POR QUE EXISTE

26/09/2026, dono: "as vezes eu ouvia um barulho estranho durante o video...
tipo suspense... ficava horrivel". As trilhas da previa mostraram: o edge-tts
termina a frase com ~0,8 s de silencio e o ChatterboxVC preenche esse
silencio com ruido de -45 a -50 dB que o YAMNet ouve como "Insect",
"Cricket", "Wild animals" — em 8 de 29 frases, sempre no fim da saida do VC,
nunca no mp3 do edge. O corte em fim-da-fala-do-edge + 0,12 s limpou as 7
frases do chips (medido).

  [1] mede onde a fala do edge acaba (tom 0-1 s + 0,8 s de silencio)
  [2] a saida do VC com ruido na cauda sai cortada em fim + 0,12 s, sem o
      ruido, e a fala antes do corte fica intacta
  [3] NEGATIVO: frase sem silencio no fim nao e' mexida
  [4] NEGATIVO: sem o edge (medida impossivel) nao e' mexida (falha aberta)
  [5] _falar_d chama o corte depois de gravar a saida do VC

Roda com: python teste/teste_cauda_vc.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import midia, voz_clonada as vc  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


T = Path(tempfile.mkdtemp())


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def rms(arq, a, b):
    r = subprocess.run(["ffmpeg", "-v", "info", "-ss", str(a), "-t", str(b - a), "-i", str(arq),
                        "-af", "astats=metadata=0", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"RMS level dB:\s*(-?[\d.]+|-inf)", r.stderr)
    return float(m[-1]) if m and m[-1] != "-inf" else -200.0


# edge: fala 0,0-1,0 s, silencio ate' 1,8 s
ff("-f", "lavfi", "-i", "sine=f=300:d=1.8", "-af",
   "volume='if(lt(t,1.0),0.5,0)':eval=frame", "-ar", "24000", str(T / "e.mp3"))
# "saida do VC": a mesma fala + ruido de ~-48 dB na cauda (o 'bicho')
ff("-f", "lavfi", "-i", "sine=f=300:d=1.8", "-f", "lavfi", "-i", "anoisesrc=d=1.8:a=0.006",
   "-filter_complex",
   "[0]volume='if(lt(t,1.0),0.5,0)':eval=frame[s];"
   "[1]volume='if(gte(t,1.05),1,0)':eval=frame[n];[s][n]amix=inputs=2:normalize=0",
   "-ar", "24000", str(T / "v.wav"))

print("[1] fim da fala do edge")
fim = vc._fim_da_fala(T / "e.mp3")
checar(fim is not None and abs(fim - 1.0) <= 0.1, f"fala acaba em ~1,0 s ({fim})")

print("\n[2] cauda do VC cortada")
antes = rms(T / "v.wav", 1.3, 1.75)
fala_antes = rms(T / "v.wav", 0.2, 0.9)
checar(vc._aparar_cauda_vc(T / "e.mp3", T / "v.wav"), "aparou")
d = midia.duracao(T / "v.wav")
checar(abs(d - (fim + vc.CAUDA_VC_S)) < 0.03, f"duracao = fim + {vc.CAUDA_VC_S} s ({d:.2f}s)")
fala = rms(T / "v.wav", 0.2, 0.9)
print(f"       cauda antes {antes:.1f} dB | fala depois {fala:.1f} dB")
checar(antes > -60, "havia ruido na cauda antes do corte")
checar(abs(fala - fala_antes) < 0.2, "a fala antes do corte fica intacta")
checar(not (T / "v_cauda.wav").exists(), "sem arquivo temporario sobrando")

print("\n[3] NEGATIVO: sem silencio no fim, nada muda")
ff("-f", "lavfi", "-i", "sine=f=300:d=1.2", "-ar", "24000", str(T / "e2.mp3"))
ff("-f", "lavfi", "-i", "sine=f=300:d=1.2", "-ar", "24000", str(T / "v2.wav"))
checar(not vc._aparar_cauda_vc(T / "e2.mp3", T / "v2.wav")
       and abs(midia.duracao(T / "v2.wav") - 1.2) < 0.02, "frase inteira preservada")

print("\n[4] NEGATIVO: sem o edge, falha aberta")
ff("-f", "lavfi", "-i", "sine=f=300:d=1.2", "-ar", "24000", str(T / "v3.wav"))
checar(not vc._aparar_cauda_vc(T / "nao_existe.mp3", T / "v3.wav")
       and abs(midia.duracao(T / "v3.wav") - 1.2) < 0.02, "sem medida, sem corte")

print("\n[5] ligado no caminho da voz D")
fonte = (RAIZ / "engine/voz_clonada.py").read_text(encoding="utf-8")
corpo = fonte[fonte.find("def _falar_d("):fonte.find("def _fim_da_fala(")]
checar(corpo.find("ta.save(str(destino)") < corpo.find("_aparar_cauda_vc(base, destino)"),
       "_falar_d apara depois de gravar a saida do VC")

print(f"\n{'FALHOU: ' + str(len(falhas)) if falhas else 'tudo verde'}")
sys.exit(1 if falhas else 0)
