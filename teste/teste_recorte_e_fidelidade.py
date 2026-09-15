"""Guardas do recorte local (ONNX) e da guarda de fidelidade do produto.

⚠️ Roda OFFLINE. O embedding da NVIDIA e' substituido por duble — o que se
prova aqui e' a DECISAO da guarda, nao o provedor.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from engine import fidelidade, recorte  # noqa: E402

falhas = []


def checar(cond, oque):
    print(("  ok   " if cond else "  FALHA ") + oque)
    if not cond:
        falhas.append(oque)


print("1. O PESO DO RECORTE VIAJA COM O PROJETO")
# ⚠️ Ordem do Bryan em 15/09/2026: se a operacao mudar de maquina, o recorte
# tem de continuar funcionando. `modelos/` esta' no .gitignore como material
# pesado; o peso so' entra por causa da excecao `!modelos/rmbg14_q8.onnx`.
# Se alguem desfizer isso, a maquina nova clona sem o peso e a quebra so'
# aparece quando o recorte for usado. Esta guarda falha antes.
checar(recorte.MODELO.exists(), f"o peso existe em {recorte.MODELO.name}")
_r = subprocess.run(["git", "ls-files", "--error-unmatch", "modelos/rmbg14_q8.onnx"],
                    cwd=RAIZ, capture_output=True, text=True)
checar(_r.returncode == 0,
       "o peso esta' VERSIONADO (senao a maquina nova clona sem ele)")
_mb = recorte.MODELO.stat().st_size / 1e6
# ⛔ Acima de 100 MB o GitHub recusa o push. O RMBG-1.4 cheio tem 176 MB — foi
# por isso que ficou o quantizado, e nao por economia de disco.
checar(_mb < 95, f"o peso cabe no push do GitHub ({_mb:.1f} MB < 95)")

print("\n2. O RECORTE DEVOLVE MASCARA UTIL")
_im = Image.new("RGB", (320, 240), (240, 240, 240))
for _x in range(110, 210):
    for _y in range(70, 170):
        _im.putpixel((_x, _y), (30, 30, 30))
_a = recorte.alfa(_im)
checar(_a.shape == (240, 320), "a mascara sai no tamanho da imagem, nao 1024")
# ⚠️ A saida crua do RMBG NAO e' 0..1: e' um mapa sem escala fixa. Sem o
# min-max a mascara sai espremida no meio da faixa e o limiar de 128 pega a
# imagem inteira — o recorte "funciona" e nao recorta nada.
checar(_a.max() == 255 and _a.min() == 0,
       f"a mascara usa a faixa toda (min={_a.min()} max={_a.max()})")
checar(recorte.recortar(_im).mode == "RGBA", "recortar() devolve RGBA")

print("\n3. A GUARDA APROVA O MESMO PRODUTO E REPROVA OUTRO")


class _Duble:
    def __init__(self, mapa):
        self.mapa = mapa
        self.velho = fidelidade._vetor

    def __enter__(self):
        fidelidade._vetor = lambda p: np.array(self.mapa[str(p)], dtype=np.float32)

    def __exit__(self, *a):
        fidelidade._vetor = self.velho


with _Duble({"a": [1, 0, 0, 0], "b": [0.97, 0.24, 0, 0]}):
    _r1 = fidelidade.comparar("a", "b")
checar(_r1["aprovado"], "mesmo produto (luz nova) passa")

# ⚠️ O CASO NEGATIVO E' O QUE PROVA A GUARDA. Sem ele, um detector que aprova
# tudo passaria em todos os outros testes deste arquivo.
with _Duble({"a": [1, 0, 0, 0], "b": [0.55, 0.83, 0, 0]}):
    _r2 = fidelidade.comparar("a", "b")
checar(not _r2["aprovado"], "produto DIFERENTE reprova")
checar(_r2["motivo"] == "o produto mostrado nao e' o do anuncio",
       "e o motivo sai em portugues, para aparecer no relato")

print("\n4. O LIMIAR FICA NO VAZIO ENTRE AS DUAS NUVENS")
# Medido em 15/09/2026: 5 pares do mesmo produto (identica, Ken Burns, relume
# Nano Banana, LTX, inpainting) contra 10 pares de produtos diferentes
# (espelho, termometro, carregador, kit ABS).
_MESMO_MIN, _OUTRO_MAX = 0.9593, 0.5861
checar(_OUTRO_MAX < fidelidade.LIMIAR < _MESMO_MIN,
       f"limiar {fidelidade.LIMIAR} entre {_OUTRO_MAX} e {_MESMO_MIN}")
# ⭐ E a margem e' o que da' sossego: limiar encostado numa das nuvens vira
# sorteio no primeiro produto fora da amostra.
checar(min(fidelidade.LIMIAR - _OUTRO_MAX, _MESMO_MIN - fidelidade.LIMIAR) > 0.08,
       "com folga dos dois lados, nao encostado numa nuvem")

print("\n5. NO VIDEO, O PIOR QUADRO MANDA")
# ⛔ Basta UM quadro com outro produto para o clipe nao poder ir ao ar. Media
# esconderia exatamente o quadro que nao pode existir.
_seq = iter([[1, 0, 0, 0], [0.99, 0.1, 0, 0], [0.4, 0.9, 0, 0], [0.98, 0.15, 0, 0]])
_ref = np.array([1, 0, 0, 0], dtype=np.float32)
_velho_vetor, _velho_run, _velho_exists = fidelidade._vetor, subprocess.run, Path.exists
fidelidade._vetor = (lambda p: _ref if str(p).endswith("ref.png")
                     else np.array(next(_seq), dtype=np.float32))
subprocess.run = lambda *a, **k: type("R", (), {"stdout": "4.0", "returncode": 0})()
Path.exists = lambda self: True
try:
    _rv = fidelidade.do_video("ref.png", "video.mp4", quadros=4)
finally:
    fidelidade._vetor, subprocess.run, Path.exists = _velho_vetor, _velho_run, _velho_exists
checar(not _rv["aprovado"], "um quadro com outro produto reprova o clipe inteiro")
checar(_rv["pior"]["semelhanca"] < fidelidade.LIMIAR, "e o relato aponta o pior quadro")

print("\n6. O MODULO DIZ O QUE A GUARDA NAO PEGA")
# ⚠️ O inpainting do Cloudflare refez o produto com menos detalhe e tira
# 0,9786 — passa. Isso e' limite MEDIDO, nao descuido, e tem de continuar
# escrito para ninguem confiar na guarda para a coisa errada.
_fonte = Path("engine/fidelidade.py").read_text(encoding="utf-8")
checar("nao pega" in _fonte.lower() or "NAO pega" in _fonte,
       "o modulo declara o caso que ela NAO cobre")
checar("0,9786" in _fonte or "0.9786" in _fonte,
       "e traz o numero medido desse caso")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
