# -*- coding: utf-8 -*-
"""Previa da CALIBRAGEM da voz clonada: as mesmas frases em varias variantes,
pra o dono ouvir lado a lado ANTES de mudar a producao.

    python -X utf8 ferramentas/previa_voz.py --saida previa_voz

Roda na nuvem (workflow `previa_voz.yml`): o Chatterbox nao cabe na maquina
local. Usa o MESMO `voz_clonada._falar` da producao — a previa e' o que o
clipe teria, nao uma imitacao.

Saida: um mp3 por frase com as variantes em sequencia (1,2 s de silencio
entre elas, na ordem de VARIANTES), mais os wav soltos.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import midia, voz_clonada  # noqa: E402

# (rotulo, exaggeration, cfg_weight ou None = padrao do modelo)
# A = o de hoje (enfase no meio da faixa da dinamica, cfg padrao 0,5)
VARIANTES = [
    ("A_atual", 0.55, None),
    ("B_cfg03", 0.55, 0.3),
    ("C_expressiva", 0.70, 0.3),
]

# uma frase por tipo de canal, na voz que o canal usa
FRASES = [
    ("make", "bruna",
     "Olha só esse truque: você aplica o corretivo em triângulo, espalha com a "
     "esponja úmida e pronto, a olheira some na hora."),
    ("podcast", "bryan",
     "Ele disse uma coisa que me pegou: disciplina não é motivação. É fazer "
     "mesmo quando você não quer, todos os dias."),
    ("chips", "bryan",
     "Essa máquina custa 400 milhões de dólares, e só uma empresa no mundo "
     "inteiro sabe fabricar."),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="previa_voz")
    ap.add_argument("--vozes", default="vozes")
    a = ap.parse_args()
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    vozes = Path(a.vozes)

    for nome, quem, texto in FRASES:
        amostra = vozes / f"{quem}_amostra.wav"
        if not amostra.exists():
            print(f"[!] sem amostra {amostra} — pulando '{nome}'")
            continue
        wavs = []
        for rot, exag, cfg in VARIANTES:
            if cfg is None:
                os.environ.pop("VOZ_CFG_PESO", None)
            else:
                os.environ["VOZ_CFG_PESO"] = str(cfg)
            p = saida / f"{nome}_{rot}.wav"
            print(f"== {nome} / {rot} (exaggeration={exag}, cfg={cfg or 'padrao'})",
                  flush=True)
            voz_clonada._falar(texto, p, amostra, "pt", enfase=exag)
            wavs.append(p)
        # um arquivo por frase, variantes em sequencia, pra ouvir no celular
        cmd = ["ffmpeg", "-y", "-v", "error"]
        for w in wavs:
            cmd += ["-i", str(w)]
        filtros = "".join(f"[{i}:a]aresample=24000,apad=pad_dur=1.2[a{i}];"
                          for i in range(len(wavs)))
        filtros += "".join(f"[a{i}]" for i in range(len(wavs)))
        filtros += f"concat=n={len(wavs)}:v=0:a=1[o]"
        cmd += ["-filter_complex", filtros, "-map", "[o]", "-b:a", "160k",
                str(saida / f"COMPARAR_{nome}.mp3")]
        midia.roda(cmd)
        print(f"   -> COMPARAR_{nome}.mp3 (ordem: "
              f"{', '.join(r for r, _, _ in VARIANTES)})", flush=True)


if __name__ == "__main__":
    main()
