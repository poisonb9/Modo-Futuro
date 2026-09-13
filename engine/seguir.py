# -*- coding: utf-8 -*-
"""O selo "siga" que pula no meio do clipe, com um som discreto.

    python -m engine.seguir --video clipe.mp4 --arroba @achadinho.make

## ⚠️ PASSO SEPARADO, DEPOIS DO RENDER — de proposito

O `render.py` monta quatro arranjos de `-filter_complex` diferentes (com e sem
dublagem, com e sem chamada). Enfiar mais um overlay e um mix de audio la'
dentro mexeria nos quatro, e e' o lugar onde este motor mais quebra.

Aqui e' uma passada so': entra um mp4 pronto, sai o mesmo mp4 com o selo. Se
der errado, devolve o original — nunca um video pela metade.

## ⚠️ O QUE A MEDICAO DIZ SOBRE ISTO, e ela nao e' toda favoravel

⭐ **Playbook §23.9: titulo que PERGUNTA converteu 0 de 4; o que MOSTRA, 7 de
14.** Um selo pedindo "siga" e' um PEDIDO, nao uma demonstracao — e' do lado
que converteu zero. Por isso o texto e' curto e o selo e' pequeno: ele lembra,
nao implora.

⚠️ **E o @modofuturo perde a audiencia em 0:02** (medido: 98,7% vem da Para
Voce, e a saida e' nos dois primeiros segundos). Um selo aos 6s so' e' visto
por quem JA' ficou — ou seja, ele nao conserta retencao, e nao deve ser
cobrado por isso. O que ele pode melhorar e' a conversao de quem assistiu.

⚠️ **ISTO PRECISA DE GRUPO DE CONTROLE.** Ligar em todos os canais ao mesmo
tempo repete o erro de 09/09 (punch-in e card de titulo juntos: quando o
numero mexeu, nao se soube qual foi). Ligar em alguns, medir, e so' depois
espalhar.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

# ⚠️ AOS 6 SEGUNDOS, e nao aos 3. Antes disso a pessoa ainda esta' decidindo se
# fica; interromper a decisao com um pedido e' pedir na hora errada. Depois de
# 6s ela ja' escolheu ficar, e ai' o pedido cabe.
SEGUIR_EM_S = 6.0
SEGUIR_DURACAO_S = 2.2

# ⚠️ PEQUENO DE PROPOSITO: ~14% da largura. Selo grande tapa o conteudo e
# parece anuncio; o que a gente quer e' um lembrete no canto do olho.
LARGURA_FRAC = 0.34
MARGEM_FRAC = 0.055

# O som: duas notas curtas, suaves. ⚠️ BAIXO (-26 dB) e' o ponto — som que
# compete com a voz faz a pessoa sair, que e' o oposto do objetivo.
NOTA_1, NOTA_2 = 880.0, 1318.5      # la' e mi, uma quinta — soa "resolvido"
SOM_DB = -26.0
SOM_DUR_S = 0.45


RAIZ = Path(__file__).resolve().parent
FONTES = RAIZ / "fontes"


def desenhar_selo(arroba: str, largura_px: int, acento: str = "#FFFFFF",
                  destino: Path | None = None) -> Path:
    """O PNG do selo, com fundo transparente.

    ⚠️ O @ ENTRA NO SELO, e nao so' a palavra "seguir". Quem ve' o clipe na
    Para Voce muitas vezes nao sabe de que perfil e' — o selo que diz "siga"
    sem dizer QUEM manda a pessoa procurar. Dizer o @ e' a diferenca entre
    lembrete e pedido vago.
    """
    from PIL import Image, ImageDraw, ImageFont

    alt = int(largura_px * 0.26)
    img = Image.new("RGBA", (largura_px, alt), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    raio = alt // 2
    # pilula escura translucida: legivel sobre qualquer fundo, sem tapar
    d.rounded_rectangle([0, 0, largura_px - 1, alt - 1], radius=raio,
                        fill=(18, 18, 22, 214))
    corpo = int(alt * 0.40)
    try:
        f = ImageFont.truetype(str(FONTES / "Poppins-Bold.ttf"), corpo)
    except OSError:
        f = ImageFont.load_default()
    # o + num circulo do acento, como o botao do proprio TikTok/Instagram
    cx, cy, r = int(alt * 0.62), alt // 2, int(alt * 0.26)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=acento)
    esp = max(2, int(r * 0.22))
    d.line([cx - r * 0.5, cy, cx + r * 0.5, cy], fill=(18, 18, 22), width=esp)
    d.line([cx, cy - r * 0.5, cx, cy + r * 0.5], fill=(18, 18, 22), width=esp)
    texto = arroba if arroba.startswith("@") else "@" + arroba
    d.text((cx + r + int(alt * 0.20), cy), texto, font=f,
           fill=(255, 255, 255, 255), anchor="lm")
    destino = destino or Path(tempfile.mkdtemp()) / "selo_seguir.png"
    img.save(destino)
    return destino


def fazer_som(destino: Path | None = None) -> Path:
    """Duas notas curtas, geradas pelo ffmpeg — nenhum arquivo pra versionar.

    ⚠️ SINTETIZADO, e nao um mp3 no repo: som de banco tem licenca, e licenca
    de audio em video publicado e' problema que aparece tarde e caro.
    """
    destino = destino or Path(tempfile.mkdtemp()) / "pling.wav"
    meio = SOM_DUR_S / 2
    filtro = (
        f"sine=frequency={NOTA_1}:duration={meio},"
        f"afade=t=out:st={meio * 0.45:.3f}:d={meio * 0.55:.3f}[n1];"
        f"sine=frequency={NOTA_2}:duration={meio},"
        f"adelay={int(meio * 1000)}|{int(meio * 1000)},"
        f"afade=t=out:st={meio * 0.5:.3f}:d={meio * 0.5:.3f}[n2];"
        f"[n1][n2]amix=inputs=2:normalize=0,volume={SOM_DB}dB[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error",
                    "-f", "lavfi", "-i", f"sine=frequency={NOTA_1}:duration=0.01",
                    "-filter_complex", filtro, "-map", "[a]",
                    "-ar", "48000", "-ac", "2", str(destino)],
                   check=True, capture_output=True)
    return destino


def aplicar(video: Path, arroba: str, acento: str = "#FFFFFF",
            em_s: float = SEGUIR_EM_S, destino: Path | None = None) -> Path:
    """Poe o selo e o som no video. Devolve o caminho final.

    ⚠️ FALHA ABERTA, e essa e' a escolha certa aqui: se qualquer coisa der
    errado, devolve o VIDEO ORIGINAL intacto. Um selo e' enfeite; perder o
    clipe por causa dele seria trocar um ganho pequeno por um estrago grande.
    O contrario (falha fechada) vale pra link de afiliado, nao pra isto.
    """
    video = Path(video)
    saida = Path(destino) if destino else video.with_name(
        video.stem + "_seguir" + video.suffix)
    try:
        # ⚠️ MEDE O VIDEO antes de posicionar: 1080x1920 e' o padrao, mas
        # bruto de fonte diferente ja' chegou com outra dimensao, e um selo
        # posicionado por numero fixo sai da tela sem erro nenhum.
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0",
             str(video)], check=True, capture_output=True, text=True)
        larg, alt = (int(x) for x in r.stdout.strip().split(",")[:2])

        # ⚠️ A DURACAO TEM DE SER MEDIDA, e o `-loop 1` da imagem TEM DE SER
        # LIMITADO por ela. MEDIDO em 13/09/2026: sem o `-t`, a entrada da
        # imagem nunca chega ao fim e o ffmpeg escreve pra sempre — um clipe
        # de 10s virou 125 MB em tres horas, ainda crescendo.
        #
        # ⭐ E o pior nao foi o arquivo: foi eu ter mandado esse mp4 pro
        # Bryan olhando o TAMANHO em vez de conferir. Sem o indice final
        # (moov atom), nenhum player abre — e eu disse que estava pronto.
        rd = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video)],
            check=True, capture_output=True, text=True)
        dur = float(rd.stdout.strip())

        selo_w = int(larg * LARGURA_FRAC)
        selo = desenhar_selo(arroba, selo_w, acento)
        som = fazer_som()
        x = int(larg * MARGEM_FRAC)
        y = int(alt * 0.70)
        fim = em_s + SEGUIR_DURACAO_S

        # ⭐ O PULO: a escala cresce de 0,72 a 1,0 nos primeiros 0,22s e para.
        # `min(...)` trava no 1,0 — sem ele a imagem continuaria crescendo ate'
        # sair da tela, e isso nao levanta erro, so' fica feio.
        t = f"(t-{em_s:.3f})"
        esc = rf"min(1\,0.72+{t}*1.27)"
        filtro = (
            f"[1:v]scale='iw*{esc}':'ih*{esc}':eval=frame[selo];"
            f"[0:v][selo]overlay="
            f"x={x}+({selo_w}-w)/2:y={y}:"
            f"enable='between(t,{em_s:.3f},{fim:.3f})'[v];"
            f"[2:a]adelay={int(em_s * 1000)}|{int(em_s * 1000)}[pling];"
            # ⚠️ `normalize=0` e' obrigatorio: sem ele o amix ABAIXA a voz pra
            # caber o som, e o clipe inteiro fica mais baixo por causa de um
            # pling de meio segundo.
            f"[0:a][pling]amix=inputs=2:duration=first:normalize=0[a]")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(video),
             # ⚠️ `-t` ANTES do `-i` da imagem: limita a ENTRADA, nao a
             # saida. Depois do `-i` ele nao vale pra esse input.
             "-loop", "1", "-t", f"{dur:.3f}", "-i", str(selo),
             "-i", str(som),
             "-filter_complex", filtro, "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
             # ⚠️ CINTO E SUSPENSORIO: o `-t` ja' resolve, mas
             # `-shortest` garante que qualquer entrada infinita que
             # apareca amanha nao derrube isto de novo.
             "-shortest",
             str(saida)], check=True, capture_output=True)
        return saida
    except Exception as e:
        msg = getattr(e, "stderr", b"") or b""
        if isinstance(msg, bytes):
            msg = msg.decode("utf-8", "replace")
        print(f"      [!] selo de seguir falhou ({type(e).__name__}) — "
              f"video segue sem ele")
        if msg.strip():
            print("          ffmpeg: " + msg.strip().splitlines()[-1][:200])
        return video


def main() -> None:
    a = argparse.ArgumentParser(description="o selo de seguir")
    a.add_argument("--video", required=True)
    a.add_argument("--arroba", required=True)
    a.add_argument("--acento", default="#FFFFFF")
    a.add_argument("--em", type=float, default=SEGUIR_EM_S)
    o = a.parse_args()
    print(aplicar(Path(o.video), o.arroba, o.acento, o.em))


if __name__ == "__main__":
    main()
