# -*- coding: utf-8 -*-
"""Mede a DINAMICA do audio original pra aplicar na dublagem.

Pedido do Bryan em 01/09/2026, depois de ouvir o corte do "Master Discipline":
"a entonacao muda da minha voz para a voz original — teria como analisar a
entonacao da voz original e aplicar na dublagem?".

## O QUE ISTO E', E O QUE NAO E'

⚠️ NAO E' TRANSFERENCIA DE ENTONACAO. Copiar a curva de tom do original pra
voz clonada exigiria ressintetizar o audio num vocoder pra seguir o F0 da
fonte — pesado pra CPU na nuvem, e degrada a voz clonada. O Chatterbox nao
aceita um contorno de tom alvo: ele gera a prosodia dele a partir do texto e
da amostra de voz.

O que da' pra fazer sao TRES aproximacoes de dinamica, e juntas elas tiram o
tom monotono. Chamo de dinamica, nao de entonacao, pra nao vender o que nao
entrego:

  1. ENFASE POR FRASE   trecho intenso no original -> sintese mais expressiva
  2. ENVELOPE DE VOLUME os picos e quedas do original aplicados na dublagem
  3. PAUSAS             o silencio entre falas do original, respeitado

## COMO A INTENSIDADE E' MEDIDA

RMS por bloco, em dBFS, mais a VARIACAO do RMS dentro do bloco. Volume alto
sozinho nao e' enfase — um trecho pode ser alto e monotono. Quem grita muda
de volume; quem le' bula nao. Por isso a variacao pesa junto.

⚠️ A MEDIDA E' RELATIVA AO PROPRIO VIDEO, nunca absoluta. Cada fonte chega
num volume diferente (e' por isso que o render tem `loudnorm`). Um limiar fixo
em dBFS classificaria o video inteiro como "intenso" ou "calmo" conforme a
gravacao, nao conforme a fala.
"""
from __future__ import annotations

import array
import math
import subprocess
from pathlib import Path

# Faixa de enfase aceita. O padrao do Chatterbox e' 0.5.
#
# ⚠️ NAO ABRA MAIS QUE ISTO SEM MEDIR. Enfase muito alta faz o modelo
# arrastar silabas e inventar entonacao que o texto nao pede; muito baixa
# devolve o robo. 0.35-0.75 e' passo curto em volta do padrao — a ideia e'
# variar entre frases, nao empurrar todas pro extremo.
ENFASE_MIN = 0.35
ENFASE_MAX = 0.75

# Quanto o envelope pode mexer no volume de uma frase, em dB.
#
# ⚠️ TETO BAIXO DE PROPOSITO. O `loudnorm` no fim do render vai reequilibrar
# tudo; envelope agressivo aqui vira bombeamento audivel depois dele. 3 dB
# muda a percepcao sem brigar com a normalizacao.
GANHO_MAX_DB = 3.0


def _pcm(caminho: Path, inicio_s: float, fim_s: float,
         taxa: int = 8000) -> array.array:
    """Um trecho do audio como PCM 16 bits mono. Vazio se nao der pra ler.

    8 kHz basta: aqui so' se mede energia, nao se reproduz nada. Decodificar
    em 48 kHz custaria 6x mais por nenhum ganho de medida.
    """
    if fim_s <= inicio_s:
        return array.array("h")
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{inicio_s:.3f}",
           "-to", f"{fim_s:.3f}", "-i", str(caminho),
           "-ac", "1", "-ar", str(taxa), "-f", "s16le", "-"]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=120)
    except Exception:
        return array.array("h")
    if r.returncode != 0 or not r.stdout:
        return array.array("h")
    a = array.array("h")
    a.frombytes(r.stdout[:len(r.stdout) // 2 * 2])
    return a


def _rms_db(amostras) -> float:
    """RMS em dBFS. -90 pra silencio (evita log de zero)."""
    if not len(amostras):
        return -90.0
    soma = 0.0
    for v in amostras:
        soma += float(v) * float(v)
    rms = math.sqrt(soma / len(amostras)) / 32768.0
    return 20.0 * math.log10(rms) if rms > 1e-9 else -90.0


def medir_blocos(fonte: Path, blocos: list[tuple[float, float]],
                 taxa: int = 8000) -> list[dict]:
    """Energia e variacao de cada bloco de fala do ORIGINAL.

    `blocos` sao pares (inicio_s, fim_s) — os mesmos trechos que viraram
    frases na dublagem.
    """
    medidas = []
    for ini, fim in blocos:
        pcm = _pcm(fonte, ini, fim, taxa)
        db = _rms_db(pcm)
        # variacao: desvio do RMS de janelas de 100 ms dentro do bloco
        janela = max(1, taxa // 10)
        pedacos = [pcm[i:i + janela] for i in range(0, len(pcm), janela)]
        dbs = [_rms_db(p) for p in pedacos if len(p) > janela // 2]
        if len(dbs) > 1:
            media = sum(dbs) / len(dbs)
            desvio = math.sqrt(sum((d - media) ** 2 for d in dbs) / len(dbs))
        else:
            desvio = 0.0
        medidas.append({"inicio_s": ini, "fim_s": fim,
                        "db": db, "variacao_db": desvio})
    return medidas


def _posicao(valor: float, valores: list[float]) -> float:
    """Onde `valor` cai entre o menor e o maior da lista, de 0 a 1.

    ⚠️ RELATIVO AO PROPRIO VIDEO. Ver o cabecalho: limiar fixo em dBFS
    classificaria a gravacao, nao a fala.
    """
    if not valores:
        return 0.5
    lo, hi = min(valores), max(valores)
    if hi - lo < 1e-6:
        return 0.5
    return (valor - lo) / (hi - lo)


def enfase_por_bloco(medidas: list[dict]) -> list[float]:
    """Quanto de enfase pedir ao TTS em cada frase, de ENFASE_MIN a MAX.

    Energia e variacao pesam METADE cada. Volume sozinho nao e' enfase: um
    trecho pode ser alto e monotono. Quem grita muda de volume; quem le' bula
    nao.
    """
    if not medidas:
        return []
    dbs = [m["db"] for m in medidas]
    vars_ = [m["variacao_db"] for m in medidas]
    saida = []
    for m in medidas:
        p = 0.5 * _posicao(m["db"], dbs) + 0.5 * _posicao(m["variacao_db"], vars_)
        saida.append(ENFASE_MIN + p * (ENFASE_MAX - ENFASE_MIN))
    return saida


def ganho_por_bloco(medidas: list[dict]) -> list[float]:
    """Multiplicador de volume de cada frase, centrado em 1.0.

    O bloco mais forte do video sobe ate' +GANHO_MAX_DB; o mais fraco desce a
    mesma coisa. A MEDIA fica em 1.0 pra nao mexer no volume geral — quem
    cuida disso e' o `loudnorm` no fim do render.
    """
    if not medidas:
        return []
    dbs = [m["db"] for m in medidas]
    saida = []
    for m in medidas:
        # -1 a +1 em volta do meio da faixa
        desvio = (_posicao(m["db"], dbs) - 0.5) * 2.0
        saida.append(10.0 ** (desvio * GANHO_MAX_DB / 20.0))
    return saida


def pausas_originais(blocos: list[tuple[float, float]]) -> list[float]:
    """Silencio, em segundos, ANTES de cada bloco de fala.

    A primeira frase nao tem pausa antes (o clipe ja' comeca nela). As demais
    herdam o intervalo que existia no original — e' o que quebra o ritmo
    constante de sintetizar frase atras de frase.

    ⚠️ Pausa negativa vira zero: blocos podem se sobrepor por arredondamento
    do alinhamento, e uma pausa negativa embaralharia a montagem.
    """
    if not blocos:
        return []
    pausas = [0.0]
    for anterior, atual in zip(blocos, blocos[1:]):
        pausas.append(max(0.0, atual[0] - anterior[1]))
    return pausas
