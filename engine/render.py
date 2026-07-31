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


# ------------------------------------------------------------ título na tela
#
# Pedido do Bryan em 30/07/2026, depois do diagnóstico do canal.
#
# Por que existe: o clipe tinha legenda karaokê e MAIS NADA no primeiro meio
# segundo — a legenda aparece palavra a palavra conforme a fala, então quem
# rola o feed não tem o que ler pra decidir parar. Sete fontes independentes
# do corpus `destravar-tiktok` apontam o título em texto na abertura como a
# alavanca nº 1 pra fazer o dedo parar: o cérebro lê mais rápido do que ouve,
# e a decisão de assistir acontece antes do gancho falado terminar.
#
# É título de TÓPICO, não legenda: diz do que o vídeo trata em uma linha.

TITULO_SEGUNDOS = 3.5      # tempo na tela; o gancho falado cobre o resto
TITULO_LINHA_MAX = 21      # caracteres por linha (Anton é condensada, cabe mais)
TITULO_MAX_LINHAS = 3      # acima disso vira parágrafo e ninguém lê

# A fonte VIAJA COM O REPOSITÓRIO. Arial e DejaVu são tipos de interface: dão
# exatamente a "cara de gerado automaticamente" que o Bryan reclamou em
# 30/07. Anton é display condensada — é o tipo que os canais de corte usam em
# gancho, e é o que separa "vídeo feito" de "vídeo cuspido por script".
#
# Depender da fonte da máquina também é frágil: o corte roda no ubuntu do
# GitHub Actions, e cada runner tem um conjunto diferente. Com a fonte no
# repo, o resultado é idêntico aqui e na nuvem. Anton é OFL, pode redistribuir.
FONTES_DIR = Path(__file__).resolve().parent / "fontes"

_FONTES = [
    # Inter Black — escolhida pelo Bryan em 31/07. É a MESMA que a legenda
    # karaokê pede (legendas.py, Style: K), então o vídeo inteiro fica com
    # uma tipografia só; e é a alternativa aberta desenhada para se parecer
    # com a San Francisco da Apple, que ele pediu mas é licenciada e não
    # pode ser redistribuída.
    str(FONTES_DIR / "Inter-Black.ttf"),
    str(FONTES_DIR / "Anton-Regular.ttf"),
    # Reservas, se alguém rodar sem a pasta fontes/
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",       # ubuntu
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",                                # windows
]


def _fonte_titulo() -> str | None:
    for f in _FONTES:
        if Path(f).exists():
            return f
    return None


def _quebrar(texto: str, largura: int = TITULO_LINHA_MAX) -> str:
    linhas, atual = [], ""
    for palavra in (texto or "").split():
        if len(atual) + len(palavra) + 1 <= largura:
            atual = f"{atual} {palavra}".strip()
        else:
            linhas.append(atual)
            atual = palavra
        if len(linhas) == TITULO_MAX_LINHAS:
            break
    if atual and len(linhas) < TITULO_MAX_LINHAS:
        linhas.append(atual)
    return "\n".join(linhas)


def filtro_titulo(texto: str, largura: int, altura: int, pasta_tmp: Path) -> str:
    """Filtro drawtext com o título nos primeiros segundos, ou '' se não der.

    O texto vai por ARQUIVO (`textfile`), não inline: título real tem aspas,
    dois-pontos, vírgula e acento, e todos são metacaracteres do drawtext —
    escapar na mão é a receita para um render que quebra num título e passa
    em outro.
    """
    texto = (texto or "").strip()
    fonte = _fonte_titulo()
    if not texto or not fonte:
        return ""
    pasta_tmp.mkdir(parents=True, exist_ok=True)

    linhas = _quebrar(texto).split("\n")
    corpo = round(altura * 0.036)
    # Entrelinha generosa. A 1,22 as linhas encostavam umas nas outras — com
    # acento maiúsculo (JÁ, É) o acento da linha de baixo quase tocava a
    # perna da de cima, e era parte do que dava cara de automático.
    passo = round(corpo * 1.42)
    topo = round(altura * 0.075)                 # abaixo da barra de status
    filtros = []
    for i, linha in enumerate(linhas):
        # Um drawtext POR LINHA. Com textfile de várias linhas o bloco todo é
        # centrado, mas cada linha fica alinhada à ESQUERDA dentro dele — é o
        # degrau torto do primeiro teste. Uma chamada por linha deixa usar
        # x=(w-text_w)/2 em cada uma, que é centralização de verdade.
        #
        # newline="\n" é OBRIGATÓRIO: no Windows o modo texto do Python
        # converte \n em \r\n e o drawtext trata o \r como conteúdo (foi o vão
        # gigante entre linhas no primeiro teste). No ubuntu da nuvem o
        # defeito não apareceria, o que o tornaria ainda mais difícil de achar.
        arq = pasta_tmp / f"titulo_{i}.txt"
        arq.write_text(linha, encoding="utf-8", newline="\n")
        filtros.append(
            f",drawtext=fontfile='{_escapar(Path(fonte))}'"
            f":textfile='{_escapar(arq)}'"
            # expansion=none: sem isso o drawtext trata % e {} como variável a
            # expandir. Título real do canal tem porcentagem ("50% DOS EMPREGOS
            # SERÃO ELIMINADOS PELA IA") e o ffmpeg reclama "Stray %" e come o
            # texto. Achado em 31/07 testando a legenda de um clipe publicado.
            f":expansion=none"
            f":fontcolor=white:fontsize={corpo}"
            # Sem caixa. Contorno preto grosso + sombra deslocada dão leitura
            # sobre qualquer fundo sem tapar a imagem. A caixa preta atrás
            # tinha cara de legenda automática, não de gancho.
            f":borderw={max(2, round(corpo * 0.10))}:bordercolor=black"
            f":shadowcolor=black@0.55"
            f":shadowx={max(1, round(corpo * 0.045))}"
            f":shadowy={max(1, round(corpo * 0.06))}"
            f":x=(w-text_w)/2:y={topo + i * passo}"
            f":enable='lt(t,{TITULO_SEGUNDOS})'"
        )
    return "".join(filtros)


def _render(bruto: Path, filtro_video: str, ass: Path | None,
            destino: Path, audio_dublado: Path | None = None) -> Path:
    cadeia = filtro_video
    if ass is not None:
        # fontsdir aponta pra pasta de fontes do repositório. O .ass pede
        # "Inter Black" pelo NOME (legendas.py), e o ubuntu do GitHub Actions
        # não tem Inter instalada — o libass caía calado numa fonte qualquer.
        # A legenda dos vídeos até 30/07 provavelmente não era Inter.
        cadeia += (f",subtitles='{_escapar(ass)}'"
                   f":fontsdir='{_escapar(FONTES_DIR)}'")

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


# Punch-in cíclico. Antes era um Ken Burns monotônico de 1.00→1.06 ao longo
# do clipe inteiro — o PLAYBOOK §5 classifica isso como "sutil demais" e pede
# variação de enquadramento a cada 5-8s, porque essa camada de edição é o que
# separa corte transformado de republicação (e sustenta o RPM).
#
# A oscilação é COSSENOIDAL de propósito: zoom que sobe e reinicia de golpe
# produziria o mesmo salto visível que o crop em degrau produzia (corrigido
# em enquadrar.py no mesmo dia). Cosseno não tem descontinuidade — o quadro
# respira, sem tranco em ponto nenhum do ciclo.
_PUNCH_AMPLITUDE = 0.10   # 1.00 -> 1.10 no pico do ciclo
_PUNCH_PERIODO_S = 6.5    # dentro da faixa de 5-8s que o corpus recomenda


def _ken_burns(bruto: Path, largura: int, altura: int) -> str:
    """Punch-in cíclico suave. Além de disfarçar trecho parado, é edição de
    verdade em cima do material — importa pra não cair em 'conteúdo
    reaproveitado sem transformação' quando o corte é de vídeo de terceiros.

    Usa o fps NATIVO da fonte (nunca força 30) — forçar conversão de frame
    rate no zoompan foi o que causou legenda dessincronizando do áudio.
    """
    fps = midia.fps(bruto)
    ciclo = max(1.0, _PUNCH_PERIODO_S) * fps          # frames por ciclo
    meia = _PUNCH_AMPLITUDE / 2
    # (1-cos)/2 varia 0..1 sem quina; 'on' é o número do frame de saída.
    z = f"1+{meia:.4f}*(1-cos(2*PI*on/{ciclo:.3f}))"
    return (f",zoompan=z='{z}':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={largura}x{altura}:fps={fps:.3f}")


def vertical(bruto: Path, ass: Path | None, destino: Path,
             audio_dublado: Path | None = None, titulo: str = "") -> Path:
    """9:16 para Shorts, com o quadro seguindo o rosto.

    `titulo` desenha o texto de abertura (ver filtro_titulo). Vem DEPOIS do
    punch-in de propósito: o zoompan reescala o quadro, e um drawtext antes
    dele seria ampliado e cortado junto.
    """
    l, a = midia.dimensoes(bruto)
    caminho = enquadrar.trajetoria(bruto, l, a)
    lv, av = config.VERTICAL
    filtro = (enquadrar.filtro_vertical(l, a, caminho)
              + _ken_burns(bruto, lv, av)
              + filtro_titulo(titulo, lv, av, destino.parent))
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
