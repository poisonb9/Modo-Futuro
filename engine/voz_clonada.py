"""Dublagem com a voz clonada do Bryan (Chatterbox Multilingual, self-hosted,
grátis, MIT — ver [[modofuturo]] handoff 04/08/2026).

Roda 100% na nuvem do Actions (CPU, sem GPU) — não na máquina do Bryan, que é
fraca demais pra isso. Medido em 04/08/2026 (run #30867337829):
  - instalar dependências: ~165s
  - carregar o modelo:      ~48s
  - gerar 1 frase (24 palavras): ~154s

O modelo é caro de carregar (48s) — por isso fica em cache no módulo e só
carrega UMA VEZ por execução do main.py, reaproveitado entre todos os
clipes do lote (`--qtd`), não recarregado por clipe.

Watermarker (resemble-perth) tem um bug de ambiente (pkg_resources faltando
em alguns setups) que derruba o carregamento do modelo com
`TypeError: 'NoneType' object is not callable` — contornado com um stub
vazio antes do import, ao custo de o áudio sair sem o carimbo "gerado por
IA" da Resemble (não achamos alternativa: 3 tentativas de consertar a causa
raiz falharam, ver commits 61bc8b8/202e3f6/98bfa2a).
"""
import re
import shutil
from pathlib import Path

from . import midia

IDIOMA_PADRAO = "pt"
_MODELO = None
_PAUSA_ENTRE_FRASES_S = 0.15


def _bypass_watermarker():
    import perth

    class _SemMarcaDagua:
        def __init__(self, *a, **k):
            pass

        def apply_watermark(self, wav, sample_rate=None):
            return wav

    perth.PerthImplicitWatermarker = _SemMarcaDagua


def _carregar_modelo():
    global _MODELO
    if _MODELO is None:
        _bypass_watermarker()
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        print("      carregando modelo de voz clonada (Chatterbox)...")
        _MODELO = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    return _MODELO


def _falar(texto: str, destino: Path, amostra_voz: Path, idioma: str) -> Path:
    import torchaudio as ta
    modelo = _carregar_modelo()
    wav = modelo.generate(texto, audio_prompt_path=str(amostra_voz), language_id=idioma)
    ta.save(str(destino), wav, modelo.sr)
    return destino


def _ajustar_duracao(audio: Path, alvo_s: float, destino: Path) -> Path:
    dur = midia.duracao(audio)
    if dur <= 0:
        shutil.copy(audio, destino)
        return destino
    fator = dur / max(0.1, alvo_s)
    fator = max(0.7, min(1.6, fator))
    midia.roda(["ffmpeg", "-y", "-i", str(audio),
                "-filter:a", f"atempo={fator:.3f}",
                "-ar", "44100", str(destino)])
    return destino


def _dividir_frases(texto: str) -> list[str]:
    """Divide pela pontuação de fim de frase (. ! ?), não por janela de
    tempo arbitrária — cada pedaço vira uma chamada de TTS curta, que é o
    regime em que o Chatterbox soa bem (ver módulo: ~154s pra 24 palavras;
    um texto de 90s inteiro numa síntese só saiu arrastado e com dicção
    ruim, medido com o Bryan em 05/08/2026)."""
    partes = re.split(r"(?<=[.!?])\s+", texto.strip())
    return [p.strip() for p in partes if p.strip()]


def _concatenar_com_pausas(caminhos: list[Path], destino: Path,
                            pausa_s: float = _PAUSA_ENTRE_FRASES_S) -> Path:
    """Junta os áudios de cada frase em sequência, com uma pausa curta e
    fixa entre elas (o silêncio natural de troca de frase de um narrador,
    não o silêncio de início/fim que o TTS já bota em cada pedaço isolado)."""
    if len(caminhos) == 1:
        shutil.copy(caminhos[0], destino)
        return destino

    cmd = ["ffmpeg", "-y"]
    for c in caminhos:
        cmd += ["-i", str(c)]

    n = len(caminhos)
    filtros, rotulos = [], []
    for i in range(n):
        if i < n - 1:
            filtros.append(f"[{i}:a]apad=pad_dur={pausa_s}[a{i}]")
            rotulos.append(f"[a{i}]")
        else:
            rotulos.append(f"[{i}:a]")
    filtro = ";".join(filtros) + ";" + "".join(rotulos) + f"concat=n={n}:v=0:a=1[out]"

    cmd += ["-filter_complex", filtro, "-map", "[out]", "-ar", "44100", str(destino)]
    midia.roda(cmd)
    return destino


def gerar_trilha(segmentos: list[dict], duracao_total: float, trabalho: Path,
                  amostra_voz: Path, idioma: str = IDIOMA_PADRAO) -> Path | None:
    """Mesma interface de dublagem.gerar_trilha, mas com a voz clonada.

    Sintetiza FRASE POR FRASE (não um trechinho por janela de ~4s, que
    cortava no meio da frase e dessincronizava as pausas da legenda; nem o
    trecho inteiro numa síntese só, que saiu arrastado e com dicção ruim —
    o Chatterbox não é feito pra 90s contínuos, ver `_dividir_frases`),
    concatena com uma pausa curta fixa entre frases, e só então ajusta a
    duração total do resultado pro tamanho do clipe (um único atempo suave
    no final, não por pedaço)."""
    if not segmentos:
        return None
    if not amostra_voz.exists():
        raise RuntimeError(f"amostra de voz não encontrada: {amostra_voz}")

    texto_completo = " ".join(
        seg["texto"].strip() for seg in segmentos if seg["texto"].strip())
    frases = _dividir_frases(texto_completo)
    if not frases:
        return None

    trabalho.mkdir(parents=True, exist_ok=True)
    partes = []
    for i, frase in enumerate(frases):
        p = trabalho / f"voz_frase_{i:03d}.wav"
        _falar(frase, p, amostra_voz, idioma)
        partes.append(p)

    concatenado = trabalho / "voz_concatenada.wav"
    _concatenar_com_pausas(partes, concatenado)

    destino = trabalho / "trilha_dublada_clonada.wav"
    _ajustar_duracao(concatenado, duracao_total, destino)
    return destino
