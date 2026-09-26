# -*- coding: utf-8 -*-
"""Final em loop: o ultimo meio segundo se dissolve no quadro 0.

POR QUE EXISTE (26/09/2026, pedido do dono: "final em loop e' interessante
demais")

O TikTok e o Shorts recomecam o video sozinhos. Se o fim salta pra uma
imagem diferente, o espectador percebe que acabou e rola. O acervo:
- F134044 (DEMONSTRADO): videos que, ao terminar, "retornem exatamente ao
  primeiro frame", pra reproducao continua e mais tempo assistido;
- F134046: comecar e terminar no mesmo quadro esconde o ponto do loop.

⚠️ O loop INVISIVEL das fichas (F134045) e' pra video de 5-8 s. Os nossos
tem >= 65 s (`config.DUR_MIN`, regra de dinheiro), entao nao da' pra fazer
o video inteiro circular. O que se faz aqui e' tirar o SALTO: nos ultimos
`FUNDE_S` a imagem vira o quadro 0 (a capa com o titulo) e a voz termina com
um fade de 150 ms, sem estalo. A outra metade do loop e' de ROTEIRO: a
ultima frase nao se despede e puxa de volta pro comeco (regra 12 do
`traducao.PROMPT_NARRACAO`).

Roda por ULTIMO na versao vertical (depois de balao, selo, cor e ritmo): o
quadro 0 tem de ser o que vai ao ar, senao o fim funde numa imagem que o
espectador nunca viu.

Falha ABERTA: qualquer erro deixa o video como estava.
Env `LOOP_FINAL=0` desliga.
"""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path

LIGADO = os.environ.get("LOOP_FINAL", "1") != "0"
FUNDE_S = 0.5
FADE_VOZ_S = 0.15


def aplicar_no_lugar(video: Path) -> bool:
    if not LIGADO:
        return False
    from . import midia
    video = Path(video)
    novo = video.with_name(video.stem + "_loop.mp4")
    try:
        dur = midia.duracao(video)
        if dur < 3 * FUNDE_S:
            return False
        fps = midia.fps(video)
        l, a = midia.dimensoes(video)
        with tempfile.TemporaryDirectory() as tmp:
            q0 = Path(tmp) / "q0.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                            "-frames:v", "1", str(q0)],
                           check=True, capture_output=True, timeout=120)
            ini = dur - FUNDE_S
            filtro = (f"[0:v]fps={fps:.3f},settb=AVTB,setsar=1[v0];"
                      f"[1:v]scale={l}:{a},format=yuv420p,fps={fps:.3f},"
                      f"settb=AVTB,setsar=1[q];"
                      f"[v0][q]xfade=transition=fade:duration={FUNDE_S}:"
                      f"offset={ini:.3f}[v];"
                      f"[0:a]afade=t=out:st={dur - FADE_VOZ_S:.3f}:d={FADE_VOZ_S}[au]")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                            "-loop", "1", "-t", f"{FUNDE_S + 0.2:.2f}", "-i", str(q0),
                            "-filter_complex", filtro, "-map", "[v]", "-map", "[au]",
                            "-t", f"{dur:.3f}",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", str(novo)],
                           check=True, capture_output=True, timeout=900)
        if not novo.exists() or novo.stat().st_size < 1000:
            raise RuntimeError("saida vazia")
        print(f"      final em loop: ultimos {FUNDE_S}s fundem no quadro 0")
    except Exception as e:
        print(f"      [!] final em loop nao aplicado ({type(e).__name__})")
        novo.unlink(missing_ok=True)
        return False
    video.unlink(missing_ok=True)
    novo.rename(video)
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    print(aplicar_no_lugar(Path(ap.parse_args().video)))
