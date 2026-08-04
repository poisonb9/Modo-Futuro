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
import shutil
from pathlib import Path

from . import midia

IDIOMA_PADRAO = "pt"
_MODELO = None


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


def gerar_trilha(segmentos: list[dict], duracao_total: float, trabalho: Path,
                  amostra_voz: Path, idioma: str = IDIOMA_PADRAO) -> Path | None:
    """Mesma interface de dublagem.gerar_trilha, mas com a voz clonada."""
    from . import dublagem  # reaproveita _mixar, sem duplicar

    if not segmentos:
        return None
    if not amostra_voz.exists():
        raise RuntimeError(f"amostra de voz não encontrada: {amostra_voz}")

    trabalho.mkdir(parents=True, exist_ok=True)
    partes = []
    for i, seg in enumerate(segmentos):
        texto = seg["texto"].strip()
        if not texto:
            continue
        bruto = trabalho / f"voz_{i:03d}.wav"
        _falar(texto, bruto, amostra_voz, idioma)
        janela = max(0.3, seg["fim"] - seg["inicio"])
        ajustado = trabalho / f"voz_{i:03d}_ok.wav"
        _ajustar_duracao(bruto, janela, ajustado)
        partes.append((seg["inicio"], ajustado))

    if not partes:
        return None

    destino = trabalho / "trilha_dublada_clonada.wav"
    dublagem._mixar(partes, duracao_total, destino)
    return destino
