# -*- coding: utf-8 -*-
"""Foto de produto vira cena COM MOVIMENTO, e cena sem foto nao derruba tudo.

⚠️ O TESTE PRECISA DE IMAGEM COM TEXTURA, e isso nao e' detalhe. A primeira
versao usou imagens de COR SOLIDA e mediu 0% de mudanca entre os quadros — o
que parecia provar que o zoom nao funcionava. Nao provava nada: cor solida
ampliada continua identica. O detector nao conseguia distinguir movimento de
imobilidade, entao o resultado nao era informacao.

Com `testsrc2` (padrao com detalhe), a mesma cena acusa 10 a 13% dos pixels
mudando, e a diferenca CRESCE com o intervalo — que e' a assinatura de um
zoom progressivo, nao de um corte.

⚠️ POR QUE O MOVIMENTO IMPORTA: foto parada por 8 segundos e' o formato que
TikTok e YouTube tratam como slideshow, e slideshow entrega mal. Alem disso e'
edicao de verdade sobre material de terceiro — o mesmo argumento que ja' esta'
escrito no `_ken_burns` do render.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import midia, montagem  # noqa: E402

tmp = Path(tempfile.mkdtemp())
falhas = []


def quadro(video: Path, em: float, destino: Path) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(em),
                    "-i", str(video), "-frames:v", "1", str(destino)],
                   check=True, capture_output=True)
    return destino


# ⚠️ TEXTURA, nao cor solida — ver o cabecalho.
tex = tmp / "tex.png"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                "-i", "testsrc2=s=900x900", "-frames:v", "1", str(tex)],
               check=True, capture_output=True)

# ---- 1. a cena tem a duracao pedida e o formato vertical ---------------
cena = montagem._cena(tex, 5.0, tmp / "cena.mp4")
d = midia.duracao(cena)
if abs(d - 5.0) > 0.25:
    falhas.append(f"duracao errada: pedi 5,0s e veio {d:.2f}s")
if midia.dimensoes(cena) != (montagem.LARGURA, montagem.ALTURA):
    falhas.append(f"nao saiu vertical: {midia.dimensoes(cena)}")

# ---- 2. POSITIVO: o quadro MUDA ao longo da cena -----------------------
try:
    from PIL import Image
    a = list(Image.open(quadro(cena, 0.1, tmp / "a.png")).convert("L").getdata())
    b = list(Image.open(quadro(cena, 4.5, tmp / "b.png")).convert("L").getdata())
    dif = sum(1 for x, y in zip(a, b) if abs(x - y) > 3) / len(a)
    if dif < 0.02:
        falhas.append(f"a cena esta' PARADA: so' {dif:.1%} dos pixels mudaram")
except ImportError:
    print("  [aviso] sem Pillow — nao da' pra medir o movimento")

# ---- 3. duracao segue a fala, com piso e teto --------------------------
if montagem.duracao_da_cena(4.2) != 4.2:
    falhas.append("fala de 4,2s deveria dar cena de 4,2s")
if montagem.duracao_da_cena(1.1) != montagem.CENA_MIN_S:
    falhas.append("fala curta nao respeitou o PISO — viraria corte seco")
if montagem.duracao_da_cena(14.0) != montagem.CENA_MAX_S:
    falhas.append("fala longa nao respeitou o TETO — foto parada cansa")
if montagem.duracao_da_cena(0) != montagem.CENA_MIN_S:
    falhas.append("sem medida de fala deveria cair no piso, nao estourar")

# ---- 4. NEGATIVO: cena sem imagem e' PULADA, nao derruba a montagem ----
saida = montagem.montar(
    [{"imagem": tex, "segundos": 3.0, "placa": "R$ 24,90"},
     {"imagem": tmp / "nao_existe.png", "segundos": 3.0, "placa": "some"},
     {"imagem": tex, "segundos": 3.0, "placa": ""}],
    tmp / "final.mp4", tmp / "trab")
dur = midia.duracao(saida)
if abs(dur - 6.0) > 0.4:
    falhas.append(f"esperava 6s (2 cenas de 3s, 1 pulada), veio {dur:.2f}s")

# ---- 5. NEGATIVO: NENHUMA imagem tem de FALHAR, nao gerar video vazio --
try:
    montagem.montar([{"imagem": tmp / "x.png", "segundos": 3.0}],
                    tmp / "vazio.mp4", tmp / "t2")
    falhas.append("montou video sem cena nenhuma — deveria falhar")
except RuntimeError:
    pass

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_montagem: cena vertical de 5s com {dif:.0%} de movimento, "
      "piso/teto valendo, cena sem foto pulada")
