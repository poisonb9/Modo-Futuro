# -*- coding: utf-8 -*-
"""Descobre de qual video do YouTube veio um bruto que chegou pelo Drive.

## O BURACO QUE ISTO TAPA

Quando o bruto e' BAIXADO pelo motor, a URL de origem fica guardada. Quando o
Bryan sobe o arquivo direto no Drive — que e' o caminho normal dele — ela nao
existe, e o manifesto sai com `fonte: fonte.mp4` e `url_origem: ""`.

⚠️ SEM A ORIGEM, A BUSCA DE EPISODIOS ANTERIORES NAO FUNCIONA. Em 01/09/2026
o Bryan pediu pra achar os episodios que faltavam de um corte que comeca no
"dia 3". O clipe existia, o canal existia — e nao havia como saber QUAL video
do YouTube era. Cheguei nele por horario de run e nome de arquivo, o que e'
inferencia minha, nao dado do sistema.

## COMO ELE DESCOBRE

Pelo NOME DO ARQUIVO. O `yt-dlp` batiza o arquivo com o titulo do video,
entao o nome que chega ao Drive e' o titulo do YouTube — as vezes com os
caracteres proibidos trocados por espaco.

⚠️ E' PALPITE, E SAI MARCADO COMO TAL. O campo `confianca` diz "alta" so'
quando o titulo do candidato bate quase exatamente com o nome do arquivo.
Guardar um palpite com cara de certeza seria pior que nao guardar: alguem
buscaria os episodios do canal errado e nao teria como desconfiar.

⚠️ E NAO ADIVINHA COM NOME GENERICO. `fonte.mp4`, `video.mp4` e afins nao
casam com nada — devolvem vazio em vez de trazer o primeiro resultado de uma
busca por "fonte", que seria ruido puro apresentado como origem.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3"

# Nomes que o motor mesmo poe, e que nao dizem nada sobre o video.
GENERICOS = {"fonte", "video", "input", "bruto", "temp", "output", "short"}


def _chaves() -> list[str]:
    ks = []
    if v := os.getenv("YOUTUBE_API_KEY"):
        ks.append(v.strip())
    for i in range(2, 41):
        if v := os.getenv(f"YOUTUBE_API_KEY_{i}"):
            ks.append(v.strip())
    return ks


def limpar(nome: str) -> str:
    """Nome de arquivo -> titulo provavel.

    Tira extensao, sufixos de baixador (YTDown.com_YouTube_, vidssave.com),
    o `(1)` de copia, e troca `_` por espaco.
    """
    t = re.sub(r"\.(mp4|mkv|webm|mov)$", "", nome or "", flags=re.I)
    t = re.sub(r"^(YTDown\.com_YouTube_|vidssave\.com\s*)", "", t, flags=re.I)
    t = re.sub(r"\s*\(\d+\)$", "", t)
    return re.sub(r"\s+", " ", t.replace("_", " ")).strip()


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def descobrir(nome_arquivo: str) -> dict:
    """`{url, video_id, titulo, canal, confianca}` — ou `{}` se nao der.

    Nunca levanta: origem e' informacao ADICIONAL. Um corte que nao sai
    porque a busca de origem falhou seria trocar um incomodo por um prejuizo.
    """
    titulo = limpar(nome_arquivo)
    if not titulo or _norm(titulo) in {_norm(g) for g in GENERICOS}:
        return {}
    chaves = _chaves()
    if not chaves:
        return {}

    for chave in chaves:
        url = f"{API}/search?" + urllib.parse.urlencode(
            {"part": "snippet", "q": titulo[:100], "type": "video",
             "maxResults": 5, "key": chave})
        try:
            d = json.load(urllib.request.urlopen(url, timeout=25))
        except Exception:
            continue
        alvo = _norm(titulo)
        melhor, nota_melhor = None, 0.0
        for it in d.get("items", []):
            t = it["snippet"]["title"]
            n = _norm(t)
            if not n:
                continue
            # quanto do nome do arquivo aparece no titulo do candidato
            comum = len(os.path.commonprefix([alvo, n]))
            nota = comum / max(len(alvo), len(n))
            if nota > nota_melhor:
                melhor, nota_melhor = it, nota
        if melhor is None:
            return {}
        # ⚠️ O LIMIAR SEPARA "achei" de "chutei". Abaixo de 0.5 o titulo mal
        # se parece com o arquivo — devolver isso como origem plantaria um
        # link errado no manifesto, e ninguem confere origem depois.
        if nota_melhor < 0.5:
            return {}
        vid = melhor["id"]["videoId"]
        return {"url": f"https://www.youtube.com/watch?v={vid}",
                "video_id": vid,
                "titulo": melhor["snippet"]["title"],
                "canal": melhor["snippet"]["channelTitle"],
                "confianca": "alta" if nota_melhor >= 0.85 else "media",
                "semelhanca": round(nota_melhor, 2)}
    return {}
