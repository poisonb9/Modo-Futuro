"""Face tracking: decide POR ONDE o quadro 9:16 passeia no vídeo 16:9.

Sem isso o crop vertical fica fixo no centro e corta a cabeça de quem está
falando de lado. Roda em CPU numa boa (MediaPipe é leve).
"""
import config

try:
    import numpy as np
except ImportError:      # so' o caminho com deteccao usa
    np = None

MAX_DEGRAUS = 60   # teto de mudanças de enquadramento por clipe


def _suavizar(pontos: list[float], alfa: float) -> list[float]:
    """Média exponencial nos dois sentidos: tira o tremor sem atrasar o
    movimento (só um sentido faria o quadro correr atrás do rosto)."""
    if not pontos:
        return []
    ida = [pontos[0]]
    for p in pontos[1:]:
        ida.append(alfa * ida[-1] + (1 - alfa) * p)
    volta = [ida[-1]]
    for p in reversed(ida[:-1]):
        volta.append(alfa * volta[-1] + (1 - alfa) * p)
    return list(reversed(volta))


MODELO_URL = ("https://storage.googleapis.com/mediapipe-models/face_detector/"
              "blaze_face_short_range/float16/1/blaze_face_short_range.tflite")
MODELO = config.RAIZ / "modelos" / "blaze_face_short_range.tflite"


def _garantir_modelo():
    """O MediaPipe Tasks não embute o modelo: precisa do .tflite em disco.
    São ~230 KB, então baixar na primeira vez sai barato e o arquivo fica
    em cache — no runner do Actions isso acontece uma vez por execução."""
    if MODELO.exists() and MODELO.stat().st_size > 0:
        return True
    try:
        import urllib.request
        MODELO.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MODELO_URL, MODELO)
        return MODELO.stat().st_size > 0
    except Exception as e:
        print(f"   [!] não consegui baixar o modelo de rosto ({e})")
        return False


def trajetoria(clipe, largura: int, altura: int) -> list[tuple[float, float]]:
    """Devolve [(tempo, x_centro)] normalizado 0..1. Vazio = usa o centro."""
    # mp.solutions saiu no MediaPipe 1.0 — o caminho atual é o Tasks API.
    # Diferenças que importam aqui: o modelo vem de arquivo, e a bounding box
    # volta em PIXELS (a antiga vinha normalizada 0..1).
    try:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
    except ImportError as e:
        print(f"   [!] face tracking indisponível ({e}) — crop fixo no centro")
        return []

    if not _garantir_modelo():
        print("   [!] face tracking sem modelo — crop fixo no centro")
        return []

    try:
        det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(MODELO)),
            running_mode=vision.RunningMode.VIDEO,
            min_detection_confidence=0.5,
        ))
    except Exception as e:
        print(f"   [!] face tracking indisponível ({e}) — crop fixo no centro")
        return []

    cap = cv2.VideoCapture(str(clipe))
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    salto = max(1, int(round(fps / config.AMOSTRA_FPS)))

    tempos, xs = [], []
    idx, amostras, achou_1x, achou_2x = 0, 0, 0, 0
    ultimo_x = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % salto == 0:
                amostras += 1
                largura_frame = frame.shape[1] or 1
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ts = int(idx / fps * 1000)
                res = det.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
                deslocamento, escala = 0, 1.0
                if res.detections:
                    achou_1x += 1
                else:
                    # SEGUNDA PASSADA EM TILES. O modelo e' o
                    # `blaze_face_short_range`: feito pra rosto PROXIMO. Em
                    # plano aberto de entrevista o rosto ocupa poucos pixels e
                    # ele nao ve' — e sem deteccao o crop cai pro centro fixo e
                    # corta a pessoa fora do quadro. Foi o que o Bryan viu em
                    # 30/08: um clipe abrindo numa sala vazia com o convidado
                    # cortado na borda.
                    #
                    # ⚠️ AMPLIAR O FRAME NAO RESOLVE. Testei 2x, 3x e 4x e a
                    # deteccao nao melhorou em nada: o BlazeFace redimensiona a
                    # entrada pra um tamanho fixo, entao escalar o frame
                    # inteiro e' inocuo. O que muda a proporcao do rosto e'
                    # RECORTAR.
                    #
                    # MEDIDO com um rosto real colado em altura conhecida:
                    #     frame inteiro -> so' detecta a partir de 300 px
                    #     3 tiles       -> detecta ja' com 140 px
                    # Mais que o dobro de sensibilidade, pelo custo de algumas
                    # deteccoes extras SO' quando a primeira passada falhou.
                    lt = int(largura_frame / 1.8)          # tile largo, com folga
                    for i in range(5):                     # 5 janelas sobrepostas
                        x0 = int(i * (largura_frame - lt) / 4)
                        tile = np.ascontiguousarray(rgb[:, x0:x0 + lt])
                        r2 = det.detect_for_video(
                            mp.Image(image_format=mp.ImageFormat.SRGB, data=tile),
                            ts + 1 + i)
                        if r2.detections:
                            res, deslocamento = r2, x0
                            achou_2x += 1
                            break

                if res.detections:
                    # CONTINUIDADE, nao "a maior". Seguir a maior face troca de
                    # pessoa toda vez que alguem se inclina pra frente — o
                    # quadro pula entre entrevistador e convidado sem que
                    # ninguem tenha comecado a falar.
                    #
                    # Aqui a face escolhida e' a mais PROXIMA da anterior, com
                    # o tamanho entrando so' como desempate. Trocar de pessoa
                    # passa a exigir que a nova esteja bem maior, nao so' um
                    # pouco.
                    def _centro(d):
                        # `deslocamento` devolve a coordenada do TILE pro frame
                        # inteiro. Sem isso um rosto achado no tile da direita
                        # seria lido como se estivesse na esquerda.
                        bb = d.bounding_box
                        x = bb.origin_x + bb.width / 2 + deslocamento
                        return x / largura_frame

                    if ultimo_x is None:
                        d = max(res.detections, key=lambda x: x.bounding_box.width)
                    else:
                        maior = max(x.bounding_box.width for x in res.detections)
                        d = min(res.detections,
                                key=lambda x: (abs(_centro(x) - ultimo_x)
                                               - 0.35 * x.bounding_box.width / maior))
                    centro = min(1.0, max(0.0, _centro(d)))
                    ultimo_x = centro
                    xs.append(centro)
                    tempos.append(idx / fps)
            idx += 1
    finally:
        cap.release()
        det.close()

    cobertura = (achou_1x + achou_2x) / amostras if amostras else 0.0
    print(f"      enquadramento: rosto em {cobertura*100:.0f}% das amostras "
          f"({achou_1x} direto, {achou_2x} so' na 2a passada ampliada)")
    if cobertura < 0.30:
        # Nao e' erro: pode ser B-roll legitimo. Mas e' o caso em que o
        # enquadramento vale pouco, e sem dizer isso o defeito so' aparece
        # depois de publicado.
        print("      [!] pouco rosto no clipe — o crop vai ficar quase fixo")

    if len(xs) < 3:
        return []
    return list(zip(tempos, _suavizar(xs, config.SUAVIZACAO)))


def filtro_vertical(largura: int, altura: int,
                    caminho: list[tuple[float, float]]) -> str:
    """Monta o filtro ffmpeg do crop 9:16 seguindo o rosto."""
    alvo_l = int(altura * 9 / 16)          # largura da janela vertical
    if alvo_l >= largura:
        # fonte já é estreita: só escala e preenche as bordas
        lv, av = config.VERTICAL
        return (f"scale={lv}:-2,pad={lv}:{av}:(ow-iw)/2:(oh-ih)/2:black")

    max_x = largura - alvo_l
    if not caminho:
        expr = f"{max_x // 2}"
    else:
        # Converte a trajetória em degraus (tempo -> x em pixels), descartando
        # variações pequenas: encurta muito a expressão e ainda tira tremor.
        # Sobe o limiar até caber num número seguro de degraus: expressão
        # muito longa deixa o parser do ffmpeg lento e frágil.
        pixels = [(t, int(min(max_x, max(0, xn * largura - alvo_l / 2))))
                  for t, xn in caminho]
        limiar = max(8, alvo_l // 60)
        while True:
            degraus: list[tuple[float, int]] = []
            for t, x in pixels:
                if not degraus or abs(x - degraus[-1][1]) >= limiar:
                    degraus.append((t, x))
            if len(degraus) <= MAX_DEGRAUS or limiar > alvo_l:
                break
            limiar = int(limiar * 1.5) + 1

        # INTERPOLA entre os degraus em vez de saltar de um pro outro.
        #
        # Antes isto era uma função degrau — if(lt(t,corte), x1, x2) — e o
        # recorte ficava imóvel e PULAVA no instante do corte, no mínimo
        # `limiar` pixels de um frame pro outro. Era o "microtravadas" que o
        # usuário viu nos clipes de 28/07: o _suavizar() acima produzia uma
        # curva suave e a quantização a destruía logo em seguida.
        #
        # Agora cada trecho vira uma rampa linear entre (t_i, x_i) e
        # (t_i+1, x_i+1), então o movimento é contínuo. A expressão fica mais
        # longa, mas o teto de MAX_DEGRAUS continua segurando o tamanho.
        if len(degraus) == 1:
            expr = f"{degraus[0][1]}"
        else:
            # Depois do último degrau o valor congela — não há pra onde ir.
            expr = f"{degraus[-1][1]}"
            for i in range(len(degraus) - 2, -1, -1):
                t0, x0 = degraus[i]
                t1, x1 = degraus[i + 1]
                dt = max(1e-3, t1 - t0)          # nunca divide por zero
                rampa = f"({x0}+({x1 - x0})*(t-{t0:.2f})/{dt:.3f})"
                expr = f"if(lt(t,{t1:.2f}),{rampa},{expr})"

    lv, av = config.VERTICAL
    return f"crop={alvo_l}:{altura}:'{expr}':0,scale={lv}:{av}"
