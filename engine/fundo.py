# -*- coding: utf-8 -*-
"""O FUNDO do original (ambiente, risada — a MUSICA sai) por baixo da dublagem.

    python -m engine.fundo --bruto trecho.mp4 --dublado voz.wav --saida mix.wav

## POR QUE EXISTE

Item 1 da dublagem (26/09/2026, dono: "Aplica Demucs!!!!"). Ate' aqui a
dublagem normal APAGAVA o audio original: a musica, o ambiente e as reacoes
sumiam, e o clipe virava uma voz sozinha sobre imagem. O Orca Dub chama isto
de "preservar audio de fundo" (acervo F128405); o acervo tambem poe o som
como uma das tres armas de retencao (F16919).

O Demucs (Meta, MIT, gratis) separa o original em VOZ e FUNDO. A voz
original sai; o fundo fica por baixo da dublagem, e ABAIXA sozinho enquanto
a dublagem fala (sidechain) e volta nas pausas.

## O ENCAIXE COM A CAUDA

`cauda.preencher_com_original` ja' devolve o som original INTEIRO depois da
ultima palavra. Se o fundo continuasse ali, sairia dobrado. Por isso o fundo
sai em fade no mesmo instante em que a cauda entra (`ate_s`).

## FALHA ABERTA

Demucs fora, erro, timeout: devolve None e o clipe sai como antes (so' a
voz). Um clipe sem fundo e' o de hoje; um clipe que nao sai e' pior.

⚠️ Tempo e memoria sao MEDIDOS a cada separacao e impressos no log
("[fundo] demucs ... s, pico ... MB") — a pergunta do dono foi se cabe nos
16 GB do runner, e a resposta tem de ser numero, nao estimativa.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ligado por env ate' o dono aprovar pela previa; depois vira True aqui
LIGADO = os.environ.get("FUNDO_ORIGINAL", "0") == "1"
MODELO = "htdemucs"
TIMEOUT_S = 900
# nivel do fundo nas PAUSAS, depois de normalizar as duas trilhas em -14 LUFS.
# Enquanto a voz fala, o sidechain derruba mais ~8-10 dB.
VOL_FUNDO = 0.45
FADE_S = 0.8
_LN = "loudnorm=I=-14:TP=-1.5:LRA=11"

# ⭐ FUNDO SEM MUSICA (26/09/2026, decisao do dono: "ambiente e risadas").
# Em programa de K-pop o fundo costuma ter MUSICA, e musica conhecida no
# TikTok = audio silenciado ou alcance cortado (acervo F10520, F09747,
# F134273/F134274: silenciar so' a musica e manter o resto). O fundo que o
# Demucs separa passa por um classificador de sons gratuito (YAMNet, Google,
# pelo MediaPipe que o motor ja' usa pro rosto) em janelas de ~1 s: onde e'
# MUSICA, o fundo some (com rampa curta); onde e' risada, aplauso, plateia ou
# ambiente, fica.
#
# Risada COM musica por tras: fica, se a musica nao for forte — a risada vale
# mais. Musica forte (>= MUSICA_FORTE) sai mesmo com risada.
#
# ⛔ Falha FECHADA: sem o classificador nao da' pra garantir "sem musica",
# entao o clipe sai so' com a voz (como antes do Demucs), nunca com o fundo
# inteiro. Medido 26/09: na sala limpa (musica de fundo) "Music" 0,8-0,9;
# no Goggins (so' conversa) "Music" 0,00.
YAMNET_URL = ("https://storage.googleapis.com/mediapipe-models/audio_classifier/"
              "yamnet/float32/latest/yamnet.tflite")
MUSICA_LIMIAR = 0.30
MUSICA_FORTE = 0.60
RISADA_LIMIAR = 0.30
RAMPA_S = 0.15
_RISADA = {"laughter", "giggle", "chuckle, chortle", "belly laugh", "baby laughter",
           "snicker", "applause", "cheering", "crowd", "clapping", "chatter"}
_MUSICA = {"singing", "choir", "song", "beat", "jingle (music)", "theme music",
           "background music", "soundtrack music", "musical instrument", "guitar",
           "drum", "drum kit", "piano", "keyboard (musical)", "synthesizer",
           "bass guitar", "orchestra", "rapping", "a capella", "vocal music"}


def _eh_musica(nome: str) -> bool:
    n = nome.lower()
    return n in _MUSICA or "music" in n


def _garantir_yamnet() -> Path | None:
    import config
    arq = config.RAIZ / "modelos" / "yamnet.tflite"
    if arq.exists() and arq.stat().st_size > 0:
        return arq
    try:
        import urllib.request
        arq.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(YAMNET_URL, arq)
        return arq if arq.stat().st_size > 0 else None
    except Exception as e:
        print(f"      [!] classificador de som indisponivel ({type(e).__name__})", flush=True)
        return None


def _decidir(janelas: list[tuple[float, float, float]]) -> list[tuple[float, float]]:
    """[(t, musica, risada)] por janela de ~1 s -> trechos (ini, fim) a TIRAR.
    Janelas seguidas viram um trecho so'. Exposto pro teste."""
    passo, trechos = 0.975, []
    for t, musica, risada in janelas:
        tirar = musica >= MUSICA_FORTE or (musica >= MUSICA_LIMIAR and risada < RISADA_LIMIAR)
        if not tirar:
            continue
        if trechos and t - trechos[-1][1] <= 0.05:
            trechos[-1] = (trechos[-1][0], t + passo)
        else:
            trechos.append((t, t + passo))
    return [(round(a, 3), round(b, 3)) for a, b in trechos]


def trechos_de_musica(wav: Path) -> list[tuple[float, float]] | None:
    """Onde o fundo e' musica (a tirar). None = nao deu pra classificar."""
    modelo = _garantir_yamnet()
    if modelo is None:
        return None
    try:
        import numpy as np
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import audio
        from mediapipe.tasks.python.components import containers
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1",
                              "-ar", "16000", "-f", "s16le", "-"],
                             check=True, capture_output=True, timeout=300).stdout
        sinal = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
        clf = audio.AudioClassifier.create_from_options(audio.AudioClassifierOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(modelo)),
            running_mode=audio.RunningMode.AUDIO_CLIPS, max_results=12))
        janelas = []
        for r in clf.classify(containers.AudioData.create_from_array(sinal, 16000)):
            cats = r.classifications[0].categories
            musica = max([c.score for c in cats if _eh_musica(c.category_name)], default=0.0)
            risada = max([c.score for c in cats if c.category_name.lower() in _RISADA],
                         default=0.0)
            janelas.append((r.timestamp_ms / 1000.0, musica, risada))
        clf.close()
        return _decidir(janelas)
    except Exception as e:
        print(f"      [!] classificacao do fundo falhou ({type(e).__name__}: "
              f"{str(e)[:80]})", flush=True)
        return None


def expr_sem_musica(trechos: list[tuple[float, float]]) -> str:
    """Ganho do fundo no tempo: 0 dentro de cada trecho de musica, 1 fora,
    com rampa de RAMPA_S nas bordas (sem estalo). Exposto pro teste."""
    if not trechos:
        return "1"
    r = RAMPA_S
    partes = [f"clip((t-{a - r:.3f})/{r},0,1)*clip(({b + r:.3f}-t)/{r},0,1)"
              for a, b in trechos]
    return f"1-min(1,{'+'.join(partes)})"


def separar(bruto: Path, pasta: Path) -> Path | None:
    """O FUNDO (tudo menos a voz) do audio de `bruto`, em wav. None se falhar."""
    pasta.mkdir(parents=True, exist_ok=True)
    entrada = pasta / "orig.wav"
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(bruto), "-vn",
                        "-ac", "2", "-ar", "44100", str(entrada)],
                       check=True, capture_output=True, timeout=300)
        cmd = [sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", MODELO,
               "-d", "cpu", "-o", str(pasta), str(entrada)]
        # /usr/bin/time -v da' o PICO de memoria (so' no Linux do runner)
        medir = shutil.which("time") or ("/usr/bin/time" if Path("/usr/bin/time").exists() else None)
        if medir and sys.platform.startswith("linux"):
            cmd = [medir, "-v"] + cmd
        t0 = time.monotonic()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
        dt = time.monotonic() - t0
        pico = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", r.stderr or "")
        print(f"      [fundo] demucs {dt:.0f}s"
              + (f", pico {int(pico.group(1)) // 1024} MB" if pico else ""), flush=True)
        if r.returncode != 0:
            print(f"      [!] demucs falhou: {(r.stderr or '')[-200:]}", flush=True)
            return None
        fundo = pasta / MODELO / "orig" / "no_vocals.wav"
        return fundo if fundo.exists() else None
    except Exception as e:
        print(f"      [!] fundo indisponivel ({type(e).__name__}: {str(e)[:80]})", flush=True)
        return None


# ⭐ VOZ ORIGINAL BAIXA POR BAIXO (26/09/2026, dono: "deixar as conversas
# originais de fundo assim como no Sem Anestesia, mas mais baixo" -> "testar
# no make, chips nao"). A voz que o Demucs ISOLOU (sem musica: a do fundo ja'
# sai pelo YAMNet, e canto na voz sai pelo mesmo classificador), a
# VOZ_ORIGINAL_DB abaixo da dublagem nas pausas e derrubada forte (ratio 10,
# como o voice-over) enquanto a dublagem fala. Vazio = desligado (padrao).
# So' a previa de referencia `make_vozorig` liga, ate' o dono ouvir.
VOZ_ORIGINAL_DB = os.environ.get("VOZ_ORIGINAL_DB", "").strip()


def _ganho_voz_original() -> float | None:
    try:
        return 10 ** (float(VOZ_ORIGINAL_DB) / 20) if VOZ_ORIGINAL_DB else None
    except ValueError:
        return None


def _corte(ate_s: float | None, trechos: list[tuple[float, float]] | None) -> str:
    corte = ""
    if trechos:
        corte += f",volume='{expr_sem_musica(trechos)}':eval=frame"
    if ate_s is not None and ate_s > 0:
        corte += (f",volume='if(gte(t,{ate_s:.3f}),0,1)':eval=frame,"
                  f"afade=t=out:st={max(0.0, ate_s - FADE_S):.3f}:d={FADE_S}")
    return corte


def filtro_mix(ate_s: float | None,
               sem_musica: list[tuple[float, float]] | None = None,
               voz_ganho: float | None = None,
               voz_sem_canto: list[tuple[float, float]] | None = None) -> str:
    """[0:a] = fundo, [1:a] = dublagem [, [2:a] = voz original] -> [a].
    Exposto pro teste. `sem_musica`: trechos em que o fundo e' musica e sai
    (ver trechos_de_musica). `voz_ganho`: liga a voz original baixa."""
    fundo = (f"[0:a]{_LN},volume={VOL_FUNDO}{_corte(ate_s, sem_musica)}[f];"
             f"[f][sc]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[fd];")
    if voz_ganho is None:
        return (f"[1:a]{_LN},asplit=2[d][sc];" + fundo
                + "[d][fd]amix=inputs=2:duration=first:normalize=0[a]")
    return (f"[1:a]{_LN},asplit=3[d][sc][sv];" + fundo
            + f"[2:a]{_LN},volume={voz_ganho:.4f}{_corte(ate_s, voz_sem_canto)}[v];"
            f"[v][sv]sidechaincompress=threshold=0.03:ratio=10:attack=15:release=400[vd];"
            "[d][fd][vd]amix=inputs=3:duration=first:normalize=0[a]")


def misturar(bruto: Path, dublado: Path, destino: Path,
             ate_s: float | None = None) -> Path | None:
    """Dublagem + fundo original (com ducking). None = segue so' a dublagem."""
    pasta = Path(tempfile.mkdtemp(prefix="fundo_"))
    fundo = separar(Path(bruto), pasta)
    if fundo is None:
        return None
    musica = trechos_de_musica(fundo)
    if musica is None:
        # falha FECHADA: sem saber onde ha' musica, nada de fundo
        print("      [fundo] sem classificador — segue so' a voz", flush=True)
        shutil.rmtree(pasta / MODELO, ignore_errors=True)
        return None
    if musica:
        seg = sum(b - a for a, b in musica)
        print(f"      [fundo] musica tirada em {len(musica)} trecho(s), "
              f"{seg:.1f}s: {musica[:6]}{' ...' if len(musica) > 6 else ''}", flush=True)
    else:
        print("      [fundo] sem musica no fundo — ambiente e risadas inteiros", flush=True)
    from . import diagnostico
    if diagnostico.ligado():
        # a previa guarda o fundo ANTES de tirar a musica (RETOMADA §1.4)
        try:
            import json
            shutil.copy2(fundo, Path(destino).with_name("fundo_demucs.wav"))
            Path(destino).with_name("fundo_musica.json").write_text(
                json.dumps({"musica": musica}), encoding="utf-8")
        except Exception:
            pass
    entradas = ["-i", str(fundo), "-i", str(dublado)]
    voz_ganho, canto = _ganho_voz_original(), None
    voz = fundo.with_name("vocals.wav")
    if voz_ganho is not None and voz.exists():
        canto = trechos_de_musica(voz)
        if canto is None:
            voz_ganho = None       # falha FECHADA: sem saber onde ha' canto
        else:
            entradas += ["-i", str(voz)]
            print(f"      [fundo] voz original a {VOZ_ORIGINAL_DB} dB por baixo"
                  f"{f', canto tirado em {len(canto)} trecho(s)' if canto else ''}",
                  flush=True)
            if diagnostico.ligado():
                try:
                    shutil.copy2(voz, Path(destino).with_name("voz_original_demucs.wav"))
                except Exception:
                    pass
    else:
        voz_ganho = None
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", *entradas,
                        "-filter_complex", filtro_mix(ate_s, musica, voz_ganho, canto),
                        "-map", "[a]",
                        "-ar", "44100", str(destino)],
                       check=True, capture_output=True, timeout=300)
        return Path(destino)
    except Exception as e:
        print(f"      [!] mistura do fundo falhou ({type(e).__name__})", flush=True)
        return None
    finally:
        shutil.rmtree(pasta / MODELO, ignore_errors=True)


def filtro_voice_over(vol_pausa: float = 0.55) -> str:
    """Voice-over: o ORIGINAL inteiro (com a voz da pessoa) abaixa so' enquanto
    a dublagem fala, em vez de ficar fixo a 0,18 o tempo todo.
    [0:a] = original, [1:a] = dublagem -> [vo] (sem loudnorm: o render poe)."""
    return (f"[0:a]{_LN},volume={vol_pausa}[o];"
            f"[1:a]{_LN},asplit=2[d][sc];"
            f"[o][sc]sidechaincompress=threshold=0.03:ratio=10:attack=15:release=400[od];"
            f"[od][d]amix=inputs=2:normalize=0[vo]")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bruto", required=True)
    ap.add_argument("--dublado", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()
    print(misturar(Path(a.bruto), Path(a.dublado), Path(a.saida), a.ate))
