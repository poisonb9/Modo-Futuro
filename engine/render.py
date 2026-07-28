"""Corte e render final. Aqui a GTX 1650 trabalha (NVENC)."""
from pathlib import Path

import config
from . import midia, enquadrar

_NVENC = None


def _encoder() -> list[str]:
    """Detecta NVENC uma vez. No Nitro 5 usa a 1650; sem NVIDIA usa a CPU."""
    global _NVENC
    if _NVENC is None:
        _NVENC = midia.tem_nvenc()
        print(f"   encoder: {'NVENC (GPU)' if _NVENC else 'libx264 (CPU)'}")
    if _NVENC:
        return ["-c:v", config.NVENC, "-preset", "p5", "-rc", "vbr",
                "-cq", "23", "-b:v", "0"]
    return ["-c:v", config.CPU_ENC, "-preset", "medium", "-crf", "20"]


def _escapar(p: Path) -> str:
    """ffmpeg trata ':' e '\\' como sintaxe dentro de filtro. No Windows o
    caminho C:\\... quebra o filtro subtitles= se não for escapado."""
    return str(p).replace("\\", "/").replace(":", r"\:")


def cortar(fonte: Path, inicio: float, fim: float, destino: Path) -> Path:
    """Corta sem reencodar o trecho (rápido). -ss antes do -i = seek veloz;
    o -ss depois garante precisão no frame."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    midia.roda([
        "ffmpeg", "-y",
        "-ss", f"{max(0, inicio - 5):.3f}", "-i", str(fonte),
        "-ss", f"{min(5, inicio):.3f}", "-t", f"{fim - inicio:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-avoid_negative_ts", "make_zero",
        str(destino),
    ])
    return destino


# Normalização de volume, alvo do TikTok (~-14 LUFS). Cada podcast-fonte
# chega num volume diferente; sem isso um clipe sai abafado no feed e o
# seguinte sai estourado. É filtro nativo do ffmpeg — aritmética de ganho,
# nada de modelo — e entra na mesma passada que já roda pro vídeo.
# TP=-1.5 deixa margem de pico pra recodificação do TikTok não clipar.
AUDIO_LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11"


def _render(bruto: Path, filtro_video: str, ass: Path | None,
            destino: Path, audio_dublado: Path | None = None) -> Path:
    cadeia = filtro_video
    if ass is not None:
        cadeia += f",subtitles='{_escapar(ass)}'"

    if audio_dublado is not None:
        # troca a trilha original pela dublada — vídeo vem do bruto (input 0),
        # áudio vem do arquivo dublado (input 1)
        midia.roda([
            "ffmpeg", "-y", "-i", str(bruto), "-i", str(audio_dublado),
            "-vf", cadeia, *_encoder(),
            "-map", "0:v:0", "-map", "1:a:0",
            "-af", AUDIO_LOUDNORM,
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(destino),
        ])
        return destino

    midia.roda([
        "ffmpeg", "-y", "-i", str(bruto),
        "-vf", cadeia, *_encoder(),
        "-af", AUDIO_LOUDNORM,
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(destino),
    ])
    return destino


_KB_ZOOM_TOTAL = 0.06   # 1.00 -> 1.06 ao longo do clipe inteiro — sutil, não "efeito TikTok"


def _ken_burns(bruto: Path, largura: int, altura: int) -> str:
    """Zoom lento e contínuo (Ken Burns). Além de disfarçar trecho parado,
    é edição de verdade em cima do material — importa pra não cair em
    'conteúdo reaproveitado sem transformação' quando o corte é de vídeo
    de terceiros.

    Usa o fps NATIVO da fonte (nunca força 30) — forçar conversão de frame
    rate no zoompan foi o que causou legenda dessincronizando do áudio.
    """
    dur = max(0.5, midia.duracao(bruto))
    fps = midia.fps(bruto)
    frames = dur * fps
    incremento = _KB_ZOOM_TOTAL / frames
    return (f",zoompan=z='min(zoom+{incremento:.8f},{1 + _KB_ZOOM_TOTAL})':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={largura}x{altura}:fps={fps:.3f}")


def vertical(bruto: Path, ass: Path | None, destino: Path,
             audio_dublado: Path | None = None) -> Path:
    """9:16 para Shorts, com o quadro seguindo o rosto."""
    l, a = midia.dimensoes(bruto)
    caminho = enquadrar.trajetoria(bruto, l, a)
    lv, av = config.VERTICAL
    filtro = enquadrar.filtro_vertical(l, a, caminho) + _ken_burns(bruto, lv, av)
    return _render(bruto, filtro, ass, destino, audio_dublado)


def horizontal(bruto: Path, ass: Path | None, destino: Path,
               audio_dublado: Path | None = None) -> Path:
    """16:9 tela cheia — o corte de 1 minuto que você queria também."""
    lh, ah = config.HORIZONTAL
    filtro = (f"scale={lh}:{ah}:force_original_aspect_ratio=decrease,"
              f"pad={lh}:{ah}:(ow-iw)/2:(oh-ih)/2:black") + _ken_burns(bruto, lh, ah)
    return _render(bruto, filtro, ass, destino, audio_dublado)


def capa(bruto: Path, destino: Path, em: float = 1.0) -> Path:
    """Thumbnail: pega um frame já com o crop vertical aplicado."""
    l, a = midia.dimensoes(bruto)
    filtro = enquadrar.filtro_vertical(l, a, [])
    midia.roda(["ffmpeg", "-y", "-ss", f"{em:.2f}", "-i", str(bruto),
                "-vf", filtro, "-frames:v", "1", "-q:v", "2", str(destino)])
    return destino
