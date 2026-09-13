# -*- coding: utf-8 -*-
"""O selo de seguir: desenha, sintetiza e FALHA ABERTA. Sem render pesado."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import seguir  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


print("1. o selo sai com o @ dentro")
p = seguir.desenhar_selo("@achadinho.make", 380, "#E0157F")
checar(Path(p).exists() and Path(p).stat().st_size > 1000, "PNG gerado")
from PIL import Image  # noqa: E402
im = Image.open(p)
checar(im.mode == "RGBA", "fundo transparente (RGBA)")
checar(im.size[0] == 380, "largura pedida respeitada")
# ⚠️ Selo alto demais tapa conteudo; a proporcao e' o que segura isso.
checar(0.2 < im.size[1] / im.size[0] < 0.32, "proporcao baixa (nao tapa)")

print("\n2. o @ entra mesmo sem a arroba")
p2 = seguir.desenhar_selo("achadinho.make", 380)
checar(Path(p2).exists(), "aceita sem @ e monta igual")

print("\n3. o som e' sintetizado, nao versionado")
w = seguir.fazer_som()
checar(Path(w).exists() and Path(w).stat().st_size > 10000, "WAV gerado")
checar(not list(Path("engine").glob("*.mp3")), "nao ha' audio no repo")

print("\n4. ⭐ FALHA ABERTA — video quebrado devolve o ORIGINAL, nao lixo")
# ⚠️ Selo e' enfeite. Perder o clipe por causa dele seria trocar um ganho
# pequeno por um estrago grande. (O contrario — falha fechada — e' a regra do
# link de afiliado, e e' outro caso.)
falso = Path(tempfile.mkdtemp()) / "nao_e_video.mp4"
falso.write_bytes(b"isto nao e um mp4")
r = seguir.aplicar(falso, "@x")
checar(r == falso, "devolve o caminho original quando o ffprobe falha")
checar(falso.read_bytes() == b"isto nao e um mp4", "e nao estraga o arquivo")

print("")
print("5. ⭐ NEGATIVO — o render TERMINA (o -loop 1 nao pode ser infinito)")
# ⚠️ MEDIDO EM 13/09/2026: sem `-t` na entrada da imagem, o ffmpeg escrevia
# pra sempre — 10s de video viraram 125 MB em tres horas, ainda crescendo. E
# o arquivo nao tinha indice final, entao nenhum player abria.
import subprocess, time  # noqa: E402
_d = Path(tempfile.mkdtemp())
_base = _d / "base.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                "-i", "color=c=black:size=240x426:duration=8:rate=12",
                "-f", "lavfi", "-i", "sine=frequency=200:duration=8",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", str(_base)],
               check=True, capture_output=True)
_t0 = time.time()
_saida = seguir.aplicar(_base, "@x", "#FFFFFF", destino=_d / "saida.mp4")
_gasto = time.time() - _t0
checar(_saida != _base, f"gerou o video ({_gasto:.1f}s)")
checar(_gasto < 120, "terminou em menos de 2 min (nao e' infinito)")
# ⚠️ E O ARQUIVO TEM DE ABRIR. Tamanho nao prova nada: o mp4 de 125 MB
# tambem "existia". Quem prova e' o ffprobe lendo a duracao.
_r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                     "format=duration", "-of", "csv=p=0", str(_saida)],
                    capture_output=True, text=True)
checar(_r.returncode == 0 and bool(_r.stdout.strip()),
       "o mp4 ABRE (tem indice final) — nao so' 'existe'")
if _r.stdout.strip():
    _dur = float(_r.stdout)
    checar(7.5 < _dur < 9.0, f"duracao bate com a entrada ({_dur:.1f}s)")
print("\n6. os numeros estao onde dao pra calibrar")
checar(seguir.SEGUIR_EM_S >= 5.0, "nao pula antes de 5s (a pessoa decide ate' la')")
checar(seguir.SOM_DB <= -20, "som bem abaixo da voz")
checar(seguir.LARGURA_FRAC < 0.5, "selo ocupa menos de metade da largura")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
