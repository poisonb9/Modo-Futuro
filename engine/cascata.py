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

LARGURA_FRAC = 0.52     # largura do selo sobre a largura do video
MARGEM_FRAC = 0.055
BASE_FRAC = 0.60        # topo do primeiro selo
GAP_FRAC = 0.012        # respiro entre eles


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


def montar_filtro(n: int, x: int, ys: list[int], fim_video: float) -> str:
    """A cadeia de filtro dos `n` selos. Separada pra poder ser lida e testada.

    ⚠️ AS EXPRESSOES VAO ENTRE ASPAS SIMPLES no `overlay=x='...'`. Assim as
    virgulas de `min(a,b)` NAO precisam de barra invertida — e barra invertida
    dentro de f-string de Python gerada por heredoc foi o defeito que mais se
    repetiu nesta sessao.
    """
    partes, entrada = [], "0:v"
    ultimo_entra = INICIO_S + ESCALONA_S * (n - 1)
    comeca_sair = ultimo_entra + ENTRA_S + FICA_S
    for i in range(n):
        t0 = INICIO_S + ESCALONA_S * i
        t1 = comeca_sair + ESCALONA_S * i
        alvo = f"v{i}" if i < n - 1 else "v"
        # ease-out cubico na entrada e na saida
        p = f"min(1,max(0,(t-{t0:.3f})/{ENTRA_S}))"
        q = f"min(1,max(0,(t-{t1:.3f})/{SAI_S}))"
        desl = (f"{x}-{DESLOC_PX}*pow(1-{p},3)-{DESLOC_PX}*pow({q},3)")
        partes.append(
            f"[{i+1}:v]format=rgba,"
            f"fade=t=in:st={t0:.3f}:d={ENTRA_S}:alpha=1,"
            f"fade=t=out:st={t1:.3f}:d={SAI_S}:alpha=1[s{i}];"
            f"[{entrada}][s{i}]overlay=x='{desl}':y={ys[i]}:"
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
        prontos, ys, y = [], [], int(alt * BASE_FRAC)
        for png in tres:
            p, h = _preparar(png, int(larg * LARGURA_FRAC), pasta)
            prontos.append(p)
            ys.append(y)
            y += h + int(alt * GAP_FRAC)

        # ⚠️ CONFERE SE A PILHA CABE. Tres selos ocupam ~35% da altura; com
        # BASE_FRAC alto o ultimo sai da tela — e sair da tela NAO levanta
        # erro, o selo so' nao aparece e ninguem entende por que.
        if y > alt:
            print(f"      [!] a pilha passa da tela ({y} > {alt}) — "
                  f"baixe BASE_FRAC ou LARGURA_FRAC")
            return video

        entradas = []
        for p in prontos:
            entradas += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(p)]
        filtro = montar_filtro(len(prontos), int(larg * MARGEM_FRAC), ys, dur)
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
