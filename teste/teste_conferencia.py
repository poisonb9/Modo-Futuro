# -*- coding: utf-8 -*-
"""Guarda da CONFERÊNCIA da dublagem (engine/conferencia.py + voz_clonada).

POR QUE EXISTE

Item 3 da dublagem (26/09/2026). O Chatterbox às vezes engole palavra ou erra
nome, e nada ouvia o resultado. Agora cada frase é transcrita e comparada; a
ruim é refeita uma vez e fica a melhor.

  [1] nota por palavras ignora acento, pontuação e maiúscula
  [2] "400" dito "quatrocentos" NÃO reprova (compara com a forma falada)
  [3] frase ruim é refeita e fica a melhor; frase boa não é refeita
  [4] teto de refações por clipe
  [5] NEGATIVO: sem transcrição (Groq fora) a frase segue, sem refazer
  [6] saída cedo zera o resumo (não herda a nota do clipe anterior)

Roda com: python teste/teste_conferencia.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import conferencia, voz_clonada  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])

print("\n[1] nota por palavras")
checar(conferencia.nota_texto("Olá, é a Wonhee!", "ola e a wonhee") == 1.0,
       "acento, vírgula e maiúscula não contam")
n = conferencia.nota_texto("ela aplica o corretivo em triângulo e espalha",
                           "ela aplica o corretivo")
checar(n < conferencia.LIMIAR, f"metade engolida reprova ({n:.2f})")

print("\n[2] número por extenso não reprova")
esperado = "Essa máquina custa 400 milhões de dólares."
ouvido = "essa máquina custa quatrocentos milhões de dólares"
melhor = max(conferencia.nota_texto(f, ouvido) for f in conferencia.formas_faladas(esperado))
checar(melhor >= 0.95, f"compara com a forma falada ({melhor:.2f})")

# --- gerar_trilha com voz e ouvido falsos ---------------------------------
def voz_falsa(texto, destino, amostra, idioma, enfase=None, motor=None):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=f=330:d={0.3 * len(texto.split()):.2f}", "-ar", "24000",
                    str(destino)], check=True)
    geradas.append(Path(destino).name)
    return destino


voz_clonada._falar = voz_falsa
amostra = Path(tempfile.mkdtemp()) / "a.wav"
amostra.write_bytes(b"x")
SEG = [{"inicio": 0.0, "fim": 8.0, "texto": "Frase um bem dita. Frase dois engolida. Frase tres ok."}]


def rodar(ouvidos):
    """`ouvidos`: por nome de arquivo, o que o Whisper 'ouviu' (None = falha)."""
    global geradas
    geradas = []
    conferencia.ouvir = lambda wav, idioma="pt": ouvidos.get(Path(wav).name, "")
    return voz_clonada.gerar_trilha(SEG, 12.0, Path(tempfile.mkdtemp()), amostra)


print("\n[3] a frase ruim é refeita e fica a melhor")
_, t = rodar({"voz_frase_000.wav": "frase um bem dita",
              "voz_frase_001.wav": "frase",                      # engoliu
              "voz_frase_001_b.wav": "frase dois engolida",      # refeita boa
              "voz_frase_002.wav": "frase tres ok"})
qc = voz_clonada.ULTIMO_QC
print(f"       geradas {geradas} | qc {qc}")
checar("voz_frase_001_b.wav" in geradas, "a frase 2 foi refeita")
checar(not any(g in geradas for g in ("voz_frase_000_b.wav", "voz_frase_002_b.wav")),
       "frases boas NÃO foram refeitas")
checar(qc.get("refeitas") == 1 and qc.get("min", 0) >= 0.99, "ficou a melhor versão")

print("\n[4] teto de refações por clipe")
ruim = {f"voz_frase_{i:03d}{s}.wav": "x" for i in range(3) for s in ("", "_b")}
teto = conferencia.MAX_REFEITAS_POR_CLIPE
conferencia.MAX_REFEITAS_POR_CLIPE = 1
rodar(ruim)
checar(voz_clonada.ULTIMO_QC.get("refeitas") == 1, "não passa do teto (1 neste teste)")
checar(voz_clonada.ULTIMO_QC.get("abaixo_do_limiar") == 3, "o resumo conta as que ficaram ruins")
conferencia.MAX_REFEITAS_POR_CLIPE = teto

print("\n[5] NEGATIVO: Groq fora -> segue sem refazer")
conferencia.ouvir = lambda wav, idioma="pt": None
geradas = []
voz_clonada.gerar_trilha(SEG, 12.0, Path(tempfile.mkdtemp()), amostra)
checar(not any(g.endswith("_b.wav") for g in geradas), "nenhuma refação")
checar(voz_clonada.ULTIMO_QC == {"conferidas": 0}, "resumo diz 0 conferidas")

print("\n[6] saída cedo zera o resumo")
voz_clonada.ULTIMO_QC = {"media": 0.5}
voz_clonada.gerar_trilha([], 12.0, Path(tempfile.mkdtemp()), amostra)
checar(voz_clonada.ULTIMO_QC == {}, "clipe sem fala não herda a nota anterior")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
