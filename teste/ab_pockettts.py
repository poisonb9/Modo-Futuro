# -*- coding: utf-8 -*-
"""A/B entre PocketTTS e Chatterbox, com as duas vozes clonadas.

⚠️ NAO TOCA NO PIPELINE. Le' duas amostras de `vozes/`, sintetiza a mesma
frase de quatro jeitos (2 motores x 2 vozes) e grava em `saida_ab/`. Nada de
Drive, Release, Buffer ou corte de video.

O QUE O TESTE PRECISA RESPONDER, nesta ordem:

  1. A VOZ AINDA E' A PESSOA? Clonagem e' por MODELO — a mesma amostra soa
     diferente em cada motor. Nao e' "melhor" ou "pior", e' OUTRA VOZ. O Bryan
     aprovou a voz da Bruna como ela sai do Chatterbox; se no PocketTTS ela
     nao parecer com ela, a velocidade nao compra nada.
  2. QUANTO MAIS RAPIDO? O Chatterbox levou 89,4s pra uma frase de 105 chars
     no run #196. E' o custo dominante do pipeline.
  3. A DICCAO AGUENTA? Numero com unidade e nome proprio sao onde a sintese
     costuma errar — e ja' erraram aqui ("Kylie (pausa) Cosmetics").

A frase padrao carrega os tres casos de propósito: nome proprio composto,
numero com unidade, e uma frase longa o bastante pra ouvir o ritmo.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SAIDA = RAIZ / "saida_ab"
VOZES = RAIZ / "vozes"

# nome proprio composto + numero com unidade + fala corrida
PADRAO = ("Hoje eu vou usar a paleta de sombras da Kylie Cosmetics, "
          "que tem 200 ml de produto e custa 350 reais. "
          "Repare como eu bato o pincel antes de encostar na pele: "
          "isso evita que a cor fique concentrada num ponto so.")

AMOSTRAS = [("bryan", VOZES / "bryan.wav"), ("bruna", VOZES / "bruna.wav")]


def falar_pocket(texto: str, amostra: Path, destino: Path) -> float:
    """Sintetiza com PocketTTS. Devolve os segundos gastos."""
    from pocket_tts import TTSModel  # nome conforme o README do kyutai-labs
    t0 = time.monotonic()
    modelo = TTSModel.from_pretrained()
    modelo.generate_to_file(texto, str(destino), voice=str(amostra))
    return time.monotonic() - t0


def falar_chatterbox(texto: str, amostra: Path, destino: Path) -> float:
    import perth

    class _Sem:
        def __init__(self, *a, **k):
            pass

        def apply_watermark(self, wav, sample_rate=None):
            return wav
    perth.PerthImplicitWatermarker = _Sem
    import torchaudio as ta
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    t0 = time.monotonic()
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    wav = m.generate(texto, audio_prompt_path=str(amostra), language_id="pt")
    ta.save(str(destino), wav, m.sr)
    return time.monotonic() - t0


def duracao(p: Path) -> float:
    import json
    import subprocess
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(p)],
            capture_output=True, text=True, timeout=60)
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def main() -> None:
    texto = (os.environ.get("TEXTO") or "").strip() or PADRAO
    so_pocket = (os.environ.get("SO_POCKET") or "").lower() == "true"
    SAIDA.mkdir(exist_ok=True)
    palavras = len(texto.split())

    linhas = ["A/B PocketTTS x Chatterbox", "=" * 60, "",
              f"texto ({palavras} palavras, {len(texto)} chars):",
              texto, "", "=" * 60, ""]
    print("\n".join(linhas), flush=True)

    motores = [("pocket", falar_pocket)]
    if not so_pocket:
        motores.append(("chatterbox", falar_chatterbox))

    for nome_motor, fn in motores:
        for nome_voz, amostra in AMOSTRAS:
            if not amostra.exists():
                msg = f"[!] amostra ausente: {amostra.name} — pulando"
                print(msg, flush=True)
                linhas.append(msg)
                continue
            destino = SAIDA / f"{nome_motor}_{nome_voz}.wav"
            print(f"-> {nome_motor} / {nome_voz} ...", flush=True)
            try:
                gasto = fn(texto, amostra, destino)
            except Exception as e:
                # ⚠️ Falha de um motor NAO pode derrubar o outro: metade da
                # comparacao ainda e' informacao.
                msg = f"[!] {nome_motor}/{nome_voz} FALHOU: {type(e).__name__}: {str(e)[:160]}"
                print(msg, flush=True)
                linhas.append(msg)
                continue
            dur = duracao(destino)
            ppm = palavras / (dur / 60) if dur else 0
            fator = dur / gasto if gasto else 0
            linha = (f"{nome_motor:<12} {nome_voz:<6} "
                     f"sintese {gasto:>6.1f}s | audio {dur:>5.1f}s | "
                     f"{fator:>4.2f}x tempo real | {ppm:>5.0f} palavras/min")
            print(linha, flush=True)
            linhas.append(linha)

    linhas += ["", "=" * 60, "",
               "COMO JULGAR (ordem que importa):",
               "  1. a voz ainda parece a pessoa? clonagem e' por MODELO",
               "  2. a diccao erra em 'Kylie Cosmetics' ou em '200 ml'?",
               "  3. o ritmo soa natural, sem arrastar nem correr?",
               "  4. so' entao: quanto mais rapido?",
               "",
               "referencia medida no run #196 (Chatterbox, producao):",
               "  frase de 105 chars -> 89,4s de sintese",
               "referencia medida no run #17 (ritmo da fala sintetizada):",
               "  113 palavras/min em media (102 a 135)"]
    (SAIDA / "RELATORIO.txt").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas[-14:]))


if __name__ == "__main__":
    main()
