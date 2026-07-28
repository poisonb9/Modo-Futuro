"""Face tracking: decide POR ONDE o quadro 9:16 passeia no vídeo 16:9.

Sem isso o crop vertical fica fixo no centro e corta a cabeça de quem está
falando de lado. Roda em CPU numa boa (MediaPipe é leve).
"""
import config

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


def trajetoria(clipe, largura: int, altura: int) -> list[tuple[float, float]]:
    """Devolve [(tempo, x_centro)] normalizado 0..1. Vazio = usa o centro."""
    try:
        import cv2, mediapipe as mp
        det = mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5)
    except (ImportError, AttributeError):
        print("   [!] face tracking indisponível (API do mediapipe mudou) — crop fixo no centro")
        return []

    cap = cv2.VideoCapture(str(clipe))
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    salto = max(1, int(round(fps / config.AMOSTRA_FPS)))

    tempos, xs = [], []
    idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % salto == 0:
                res = det.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if res.detections:
                    # com várias faces, segue a maior (quem está em primeiro plano)
                    d = max(res.detections,
                            key=lambda x: x.location_data.relative_bounding_box.width)
                    bb = d.location_data.relative_bounding_box
                    xs.append(min(1.0, max(0.0, bb.xmin + bb.width / 2)))
                    tempos.append(idx / fps)
            idx += 1
    finally:
        cap.release()
        det.close()

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

        # Cada x vale DA sua marca EM DIANTE, então o limite de cada if() é o
        # tempo do degrau SEGUINTE. Monta de trás pra frente.
        expr = f"{degraus[-1][1]}"
        for i in range(len(degraus) - 2, -1, -1):
            corte = degraus[i + 1][0]
            expr = f"if(lt(t,{corte:.2f}),{degraus[i][1]},{expr})"

    lv, av = config.VERTICAL
    return f"crop={alvo_l}:{altura}:'{expr}':0,scale={lv}:{av}"
