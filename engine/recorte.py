"""Recorte do produto (remocao de fundo) rodando LOCAL, em ONNX.

⭐ POR QUE LOCAL, E NAO NO HUGGING FACE. O Space `not-lain/background-removal`
funciona e e' gratis, mas vive no ZeroGPU: a cota anonima acaba em poucas
chamadas (aconteceu em 15/09/2026, no meio de uma calibracao). Space publico
tambem cai sem aviso. Aqui nao ha cota, nao ha fila e nao ha conta.

⚠️ E O MODELO ACOMPANHA O PROJETO. Ordem do Bryan em 15/09/2026: se a operacao
mudar de maquina, isto tem de continuar funcionando. Por isso o peso mora em
`modelos/rmbg14_q8.onnx`, versionado junto com o codigo — 44,4 MB, abaixo do
teto de 100 MB por arquivo do GitHub. O RMBG-1.4 cheio (176 MB) NAO cabe, e o
`u2netp` (4,6 MB) cabe mas recorta pior; o quantizado int8 e' o meio-termo que
o repo aguenta.

⛔ NAO trocar por download sob demanda. Baixar no primeiro uso reintroduz
exatamente a dependencia de rede que este modulo existe para remover — e a
maquina nova pode nao ter internet no momento em que a suite roda.

⚠️ A MAQUINA NAO PROCESSA VIDEO, MAS PROCESSA ISTO. O motor pesado roda na
nuvem por decisao antiga; este modelo e' int8 e roda em CPU num piscar. Nao
confundir os dois casos.
"""
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / "modelos" / "rmbg14_q8.onnx"
LADO = 1024
_sessao = None


def _abrir():
    global _sessao
    if _sessao is None:
        import onnxruntime
        if not MODELO.exists():
            raise FileNotFoundError(
                f"peso ausente: {MODELO}. Ele e' versionado com o repo — "
                "se sumiu, foi filtro de .gitignore ou clone parcial (LFS).")
        so = onnxruntime.SessionOptions()
        so.intra_op_num_threads = 4          # nao tomar a maquina inteira
        _sessao = onnxruntime.InferenceSession(
            str(MODELO), so, providers=["CPUExecutionProvider"])
    return _sessao


def alfa(imagem) -> np.ndarray:
    """Devolve o canal alfa (uint8, mesmo tamanho da imagem): 255 = produto."""
    from PIL import Image
    im = Image.open(imagem).convert("RGB") if not isinstance(imagem, Image.Image) \
        else imagem.convert("RGB")
    larg, alt = im.size
    x = np.asarray(im.resize((LADO, LADO), Image.BILINEAR), dtype=np.float32) / 255.0
    x = (x - 0.5) / 1.0
    x = x.transpose(2, 0, 1)[None]
    s = _abrir()
    y = s.run(None, {s.get_inputs()[0].name: x})[0]
    y = np.squeeze(y)
    # ⚠️ A saida NAO e' 0..1: e' um mapa sem escala fixa. Sem este min-max o
    # recorte sai cinza e o limiar de 128 pega a imagem toda.
    y = (y - y.min()) / max(y.max() - y.min(), 1e-8)
    return np.asarray(Image.fromarray((y * 255).astype(np.uint8))
                      .resize((larg, alt), Image.BILINEAR))


def recortar(imagem):
    """Devolve a imagem RGBA com o fundo transparente."""
    from PIL import Image
    im = Image.open(imagem).convert("RGB") if not isinstance(imagem, Image.Image) \
        else imagem.convert("RGB")
    fora = im.convert("RGBA")
    fora.putalpha(Image.fromarray(alfa(im)))
    return fora
