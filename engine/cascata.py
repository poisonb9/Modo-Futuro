# -*- coding: utf-8 -*-
"""Os tres selos cromados entrando em cascata: CURTA · COMENTE · SIGA.

    python -m engine.cascata --video c.mp4 --canal atefalhar

## DE ONDE VEM A ARTE

PNGs cromados gerados pelo Bryan (13/09/2026) e versionados em
`engine/selos/`. ⚠️ A margem transparente foi APARADA na entrada: o gerador
deixa folga em volta, e sem aparar o botao flutua longe da borda e o
espacamento entre os tres mente.

⚠️ SAO ARTE FIXA, e nao texto desenhado. Isso tem um custo que precisa estar
escrito: **cada canal precisa do seu proprio `siga_<canal>.png`**, porque o @
esta' dentro da imagem. O `curta` e o `comente` servem a todos.

## O MOVIMENTO — e por que ele nao usa `scale`

    entra deslizando da esquerda, com ease-out cubico, escalonado 0,30s
    fica
    sai deslizando pra esquerda, na mesma ordem

⚠️ A ANIMACAO E' NA POSICAO (`x`), NUNCA NA ESCALA. Em 13/09/2026 a versao com
`scale` animado custou meia hora: a expressao fica negativa fora da janela e o
ffmpeg recusa com `Invalid argument` -22 sem dizer qual argumento.

⭐ `x` NEGATIVO E' LEGITIMO — e' posicao, nao tamanho; o selo so' fica fora da
tela. Por isso animar posicao e' seguro onde animar tamanho nao e'.

## ⚠️ TRES PEDIDOS, E O DADO NAO E' TODO A FAVOR

Playbook §23.9: pedir converte MENOS que mostrar (titulo-pergunta 0 de 4;
titulo que afirma 7 de 14). Tres pedidos sao tres vezes mais pedido.

⭐ O que joga a favor: **curtida e' o unico preditor medido de seguidores**
(+0,52 sem o outlier). Retencao nao preve, views nao preveem. Por isso o CURTA
vem PRIMEIRO — nao e' ordem estetica.

⚠️ E POR ISSO ISTO PRECISA DE EXPERIMENTO, nao de fe': ligar em todos os
canais de uma vez repete o erro de 09/09 (punch-in e card juntos; quando o
numero mexeu, ninguem soube qual foi).
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

SELOS = Path(__file__).resolve().parent / "selos"

INICIO_S = 5.0          # quando o primeiro entra
ESCALONA_S = 0.30       # atraso entre um e o proximo
ENTRA_S = 0.45          # duracao do deslize de entrada
SAI_S = 0.40
FICA_S = 4.5            # tempo parado, depois que o ultimo entrou
DESLOC_PX = 320         # de quanto vem da esquerda

LARGURA_FRAC = 0.52     # largura base do selo sobre a largura do video

# ⚠️ MULTIPLICADOR POR SELO, na ordem CURTA / COMENTE / SIGA. O SIGA e'
# maior por pedido do Bryan em 13/09/2026 — e faz sentido: dos tres pedidos
# ele e' o unico que carrega o NOME do canal, e e' o que a pessoa precisa
# conseguir ler pra agir depois, fora do video.
#
# ⚠️ Mexer aqui muda a ALTURA tambem, e altura maior pode encostar na
# legenda ou sair da tela. Nao confie no numero: o `colocar` confere e
# recusa a cascata inteira se der encontro.
ESCALA_POR_SELO = (1.00, 1.00, 1.18)
MARGEM_FRAC = 0.055
GAP_FRAC = 0.012        # respiro entre eles
FOLGA_FRAC = 0.025      # respiro entre a pilha e a legenda

# ⚠️ TETO: acima disto e' a zona do card de titulo. A pilha que nao couber
# entre este teto e a legenda NAO entra — ver `posicionar`.
TETO_FRAC = 0.18

# ⚠️ A FAIXA DA PLATAFORMA, embaixo: nome do perfil, legenda do TikTok,
# musica, e a barra de gestos do celular. Selo que entra aqui EXISTE e
# ninguem ve'.
#
# ⚠️ ESTE LIMITE FALTAVA ATE' 13/09/2026. O `colocar` conferia legenda e
# borda da tela, e deixou passar o SIGA aumentado terminando em 0,889 — eu
# so' vi porque fui conferir a conta depois de mexer no tamanho. Guarda que
# nao olha uma das bordas nao e' guarda, e' sorte.
UI_BASE_FRAC = 0.86


# ⚠️ AS TRES POSICOES, e elas vieram de um desenho do Bryan em 13/09/2026:
# ele marcou de branco na tela onde queria cada selo. Eu medi as marcas
# ancorando pela legenda (que sabemos estar em 0,70) e deram 0,056 / 0,459 /
# 0,869 da altura.
#
# ⚠️ DUAS FORAM AJUSTADAS, e e' honesto dizer quais e por que:
#
#   0,056 -> 0,105   a marca ficava na borda de cima. O TikTok poe a barra de
#                    "seguindo / para voce" ali, e o Instagram poe o cabecalho
#                    do Reels. Selo encostado no topo fica atras dos dois.
#
#   0,869 -> 0,735   a marca caia DENTRO da faixa de interface de baixo (nome
#                    do perfil, legenda da plataforma, musica). O selo
#                    existiria e ninguem veria. 0,735 e' logo abaixo da nossa
#                    legenda e acima dessa faixa.
#
# ⭐ O `lado` decide de onde o selo ENTRA: o da direita desliza de fora pela
# direita, o da esquerda pela esquerda. Um selo da direita entrando pela
# esquerda atravessaria a tela inteira e cobriria o rosto no caminho.
# (lado onde FICA, fracao da altura, lado por onde ENTRA)
#
# ⚠️ ONDE FICA E DE ONDE VEM SAO COISAS SEPARADAS, e ate' 13/09/2026 eu tinha
# amarrado as duas. O Bryan pediu o SIGA entrando da direita pra esquerda
# mesmo ficando a' esquerda — e faz sentido: e' o ultimo e o maior, e
# atravessar a tela da' a ele uma chegada que os outros nao tem.
#
# ⚠️ Quando o lado de entrada e' o OPOSTO de onde fica, o deslocamento nao e'
# o `DESLOC_PX`: e' o quanto for preciso pra comecar FORA da tela. Usar 320
# faria o selo brotar no meio do video em vez de entrar.
ZONAS = (
    ("dir", 0.105, "dir"),
    ("esq", 0.459, "esq"),
    ("esq", 0.735, "dir"),
)


def colocar(larg: int, alt: int, larguras: list[int],
            alturas: list[int]) -> list[tuple[int, int, int]] | None:
    """(x, y, deslocamento) de cada selo. O sinal diz de que lado ele entra.

    ⚠️ CONFERE A LEGENDA EM VEZ DE CONFIAR NAS ZONAS. As frações de `ZONAS`
    foram escolhidas livres da legenda HOJE — mas a legenda se move: o
    `LEGENDA_MARGEM_V_FRAC` e' variavel de ambiente, e ja' foi usado pra
    desviar de UI na fonte. Se alguem mexer nele, as zonas colidem CALADAS.

    ⭐ Por isso a checagem pergunta a `legendas.faixa_ocupada` na hora, e
    devolve None se der encontro. None = cascata nao entra, que e' melhor do
    que entrar por cima do texto.
    """
    from . import legendas
    topo_leg, base_leg = legendas.faixa_ocupada(alt)
    margem = int(larg * MARGEM_FRAC)
    saida = []
    for (lado, frac, entra), lw, lh in zip(ZONAS, larguras, alturas):
        y = int(alt * frac)
        if not (y + lh < topo_leg or y > base_leg):
            print(f"      [!] a zona {frac} bate na legenda "
                  f"({topo_leg}-{base_leg}) — cascata NAO entra")
            return None
        # ⭐ SE PASSAR DA FAIXA DA PLATAFORMA, SOBE — nao desiste nem ignora.
        # O selo cresce quando o `ESCALA_POR_SELO` muda, e exigir que o Bryan
        # recalcule a fracao a cada ajuste de tamanho e' transformar um numero
        # de gosto num numero de engenharia.
        limite = int(alt * UI_BASE_FRAC)
        if y + lh > limite:
            y = limite - lh
            # ⚠️ e ai' TEM DE CONFERIR A LEGENDA DE NOVO: subir pra escapar da
            # interface pode jogar o selo em cima do texto.
            if not (y + lh < topo_leg or y > base_leg):
                print(f"      [!] a zona {frac} nao cabe entre a legenda e a "
                      f"interface — cascata NAO entra")
                return None
        if y + lh > alt or y < 0:
            print(f"      [!] a zona {frac} sai da tela — cascata NAO entra")
            return None
        x = (larg - lw - margem) if lado == "dir" else margem
        # ⚠️ O DESLOCAMENTO E' CALCULADO, nao fixo. Se o selo entra pelo lado
        # oposto ao que fica, ele tem de comecar FORA da tela — senao brota no
        # meio do video. Do mesmo lado, um passo curto basta e fica sutil.
        if entra == "dir":
            desl = (larg - x) if lado == "esq" else DESLOC_PX
        else:
            desl = -(x + lw) if lado == "dir" else -DESLOC_PX
        saida.append((x, y, desl))
    return saida


def selos_do_canal(canal: str) -> list[Path] | None:
    """Os tres PNGs deste canal, ou None se faltar o `siga` dele.

    ⚠️ FALHA FECHADA no `siga`: o @ mora DENTRO da imagem, entao usar o selo
    de outro canal mandaria a audiencia pro perfil errado. Melhor nao por
    cascata nenhuma do que por a cascata de outro canal.
    """
    siga = SELOS / f"siga_{canal}.png"
    if not siga.exists():
        return None
    tres = [SELOS / "curta.png", SELOS / "comente.png", siga]
    return tres if all(p.exists() for p in tres) else None


def _preparar(png: Path, largura: int, pasta: Path) -> tuple[Path, int]:
    """Redimensiona fora do ffmpeg e devolve (caminho, altura).

    ⚠️ O REDIMENSIONAMENTO SAI DO FFMPEG DE PROPOSITO. Filtro `scale` com
    expressao foi a fonte de todos os `Invalid argument` de hoje; PIL faz isso
    uma vez, antes, e o ffmpeg so' compoe. Menos coisa pra dar errado no lugar
    onde errado e' silencioso.
    """
    from PIL import Image
    im = Image.open(png).convert("RGBA")
    a = im.getbbox()          # apara a folga transparente, se sobrou alguma
    if a:
        im = im.crop(a)
    altura = round(im.size[1] * largura / im.size[0])
    saida = pasta / png.name
    im.resize((largura, altura), Image.LANCZOS).save(saida)
    return saida, altura


def montar_filtro(pos: list[tuple[int, int, int]], fim_video: float) -> str:
    """A cadeia de filtro. `pos` = (x, y, deslocamento) de cada selo.

    ⚠️ AS EXPRESSOES VAO ENTRE ASPAS SIMPLES no `overlay=x='...'`. Assim as
    virgulas de `min(a,b)` nao precisam de barra invertida — barra invertida
    em f-string foi o defeito que mais se repetiu nesta sessao.

    ⚠️ E A ANIMACAO E' NA POSICAO, NUNCA NA ESCALA. `x` negativo e' legitimo:
    e' posicao, o selo so' fica fora da tela. Escala negativa derruba o ffmpeg
    com `Invalid argument` -22 sem dizer qual argumento.
    """
    partes, entrada = [], "0:v"
    n = len(pos)
    ultimo_entra = INICIO_S + ESCALONA_S * (n - 1)
    comeca_sair = ultimo_entra + ENTRA_S + FICA_S
    for i, (x, y, desl) in enumerate(pos):
        t0 = INICIO_S + ESCALONA_S * i
        t1 = comeca_sair + ESCALONA_S * i
        alvo = f"v{i}" if i < n - 1 else "v"
        d = desl                     # de que lado ele vem, e pra onde volta
        p = f"min(1,max(0,(t-{t0:.3f})/{ENTRA_S}))"
        q = f"min(1,max(0,(t-{t1:.3f})/{SAI_S}))"
        # ease-out cubico na entrada; o mesmo desenho, invertido, na saida
        desl = f"{x}+{d}*pow(1-{p},3)+{d}*pow({q},3)"
        partes.append(
            f"[{i+1}:v]format=rgba,"
            f"fade=t=in:st={t0:.3f}:d={ENTRA_S}:alpha=1,"
            f"fade=t=out:st={t1:.3f}:d={SAI_S}:alpha=1[s{i}];"
            f"[{entrada}][s{i}]overlay=x='{desl}':y={y}:"
            f"enable='between(t,{t0:.3f},{min(t1 + SAI_S, fim_video):.3f})'"
            f"[{alvo}]")
        entrada = alvo
    return ";".join(partes)


def aplicar(video: Path, canal: str, destino: Path | None = None) -> Path:
    """Poe a cascata no video. FALHA ABERTA: devolve o original se der errado.

    ⚠️ Enfeite nao pode custar o clipe. (O contrario — falha fechada — vale
    pro link de afiliado, que e' dinheiro, nao enfeite.)
    """
    video = Path(video)
    saida = Path(destino) if destino else video.with_name(
        video.stem + "_cta" + video.suffix)
    try:
        tres = selos_do_canal(canal)
        if not tres:
            print(f"      [!] sem selo 'siga_{canal}.png' — cascata NAO entra")
            return video

        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0",
             str(video)], check=True, capture_output=True, text=True)
        larg, alt = (int(v) for v in r.stdout.strip().split(",")[:2])
        rd = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video)],
            check=True, capture_output=True, text=True)
        dur = float(rd.stdout.strip())

        pasta = Path(tempfile.mkdtemp())
        prontos, larguras, alturas = [], [], []
        for png, mult in zip(tres, ESCALA_POR_SELO):
            lw = int(larg * LARGURA_FRAC * mult)
            pr, h = _preparar(png, lw, pasta)
            prontos.append(pr)
            larguras.append(lw)
            alturas.append(h)

        # ⭐ CADA SELO NA SUA ZONA, e a colisao com a legenda e' CONFERIDA na
        # hora — nao confiada nas fracoes escolhidas hoje.
        pos = colocar(larg, alt, larguras, alturas)
        if pos is None:
            return video

        entradas = []
        for p in prontos:
            entradas += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(p)]
        filtro = montar_filtro(pos, dur)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(video), *entradas,
             "-filter_complex", filtro, "-map", "[v]", "-map", "0:a?",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
             "-shortest", str(saida)],
            check=True, capture_output=True)
        return saida
    except Exception as e:
        msg = getattr(e, "stderr", b"") or b""
        if isinstance(msg, bytes):
            msg = msg.decode("utf-8", "replace")
        print(f"      [!] cascata falhou ({type(e).__name__}) — video sem ela")
        if msg.strip():
            print("          ffmpeg:" + chr(10) + msg.strip()[-600:])
        return video


def main() -> None:
    a = argparse.ArgumentParser(description="a cascata de selos")
    a.add_argument("--video", required=True)
    a.add_argument("--canal", required=True)
    a.add_argument("--saida")
    o = a.parse_args()
    print(aplicar(Path(o.video), o.canal,
                  Path(o.saida) if o.saida else None))


if __name__ == "__main__":
    main()


# ⚠️ QUAIS CANAIS RECEBEM A CASCATA. Vazio = ninguem, e e' o padrao de
# proposito: nada muda em producao ate' o Bryan escolher.
#
# ⭐ E A ESCOLHA E' UM EXPERIMENTO, nao um gosto. Ligar nos sete de uma vez
# repete o erro de 09/09/2026 — punch-in e card de titulo entraram juntos, e
# quando o numero mexeu ninguem soube qual dos dois foi. Dois ou tres canais
# com, o resto sem, e em duas semanas o dado decide.
#
# ⚠️ E o grupo de controle ja' esta' menor: o @atefalhar saiu dele em 13/09
# quando ganhou chamada. Sobrou o @modofuturo — NAO ligue nele.
CANAIS_COM_CASCATA: set[str] = set()


def ligado(canal: str) -> bool:
    """Este canal recebe a cascata? Resolve pelo registro, nao pelo texto.

    ⚠️ O mesmo canal chega escrito de tres jeitos (nome_buffer, @, apelido).
    Comparar texto cru deixaria a cascata ligada num e desligada noutro sem
    ninguem perceber.
    """
    from . import canais_registro
    nome = canais_registro.canonico(canal)
    return bool(nome) and nome in CANAIS_COM_CASCATA


def aplicar_no_lugar(video: Path, canal: str) -> bool:
    """Poe a cascata SOBRESCREVENDO o arquivo. Devolve se entrou.

    ⚠️ So' troca o arquivo depois que o novo existe E ABRE. Substituir antes
    de conferir e' o mesmo erro de hoje, quando mandei um mp4 sem indice final
    pro Bryan: o arquivo existia e nenhum player abria.
    """
    from . import canais_registro
    video = Path(video)
    if not ligado(canal):
        return False
    novo = aplicar(video, canais_registro.canonico(canal) or canal,
                   destino=video.with_name(video.stem + "_cta.mp4"))
    if novo == video or not Path(novo).exists():
        return False
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(novo)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        print("      [!] a cascata gerou um mp4 que nao abre — fica o original")
        Path(novo).unlink(missing_ok=True)
        return False
    video.unlink(missing_ok=True)
    Path(novo).rename(video)
    return True
