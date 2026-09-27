# -*- coding: utf-8 -*-
"""Memoria de temas: o motor sabe o que o canal JA publicou.

    python -m engine.memoria_temas --canal modofuturo --titulo "A maquina de 400 milhoes"

## POR QUE EXISTE (27/09/2026, plano de virada item 2, aprovado pelo dono)

MEDIDO nas prints do @modofuturo: cada vez que uma historia voltava, rendia
menos — poeira 1.011 -> 327, maquina de 400 mi 730 -> 366, erro de US$ 500 mil
569 -> 305. O motor nao tinha como saber que ja' tinha contado aquilo.

## O QUE FAZ

1. `bloco_prompt(canal)`: lista os titulos ja' publicados no canal para o
   Gemini evitar o mesmo assunto na SELECAO (o jeito mais barato: ele nem
   escolhe o trecho repetido).
2. `marcar(clipes, canal)`: depois da selecao, compara cada titulo/gancho com
   o que ja' saiu. Parecido demais (>= LIMIAR) ganha a marca `tema_repetido`
   (com o titulo antigo) e perde PENALIDADE pontos SO' na ORDEM.
   ⚠️ NAO DESCARTA — mesmo cuidado que o dono pediu no item 5 ("nao
   generalize, podemos perder muitos bons videos"). A marca vai pro post.json
   para medir pelas views se a repeticao cai mesmo.

## DE ONDE VEM A MEMORIA

- `estado/temas_publicados.json`: semente (manifestos das releases x Buffer
  enviado + registros do Studio) — tudo o que saiu ate' 27/09/2026.
- `estado/trechos_usados.json`: cada envio ao Buffer grava canal e titulo
  (engine/trechos.py) e o workflow commita — a memoria cresce sozinha.

Falha aberta: sem arquivo, memoria vazia, motor segue como antes.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEMENTE = RAIZ / "estado" / "temas_publicados.json"
TRECHOS = RAIZ / "estado" / "trechos_usados.json"

LIMIAR = 0.5          # fracao de palavras de conteudo em comum (ver `parecido`)
PENALIDADE = 8
MAX_NO_PROMPT = 60

_VAZIAS = set("""a o as os um uma uns umas de da do das dos e em no na nos nas
por para pra com sem que se sua seu suas seus ele ela eles elas isso esse essa
este esta ao aos como mais menos muito muita todo toda todos todas quando onde
qual quais porque por que ja nao sim foi era ser sao tem ter vai vao esta
the of and to in on for with is are how why what""".split())


def palavras(texto: str) -> set[str]:
    """Palavras de conteudo, sem acento, com radical curto (6 letras).
    Numeros ficam: '400', '500' e '1100' sao o gancho do canal."""
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("milhoes", "milhao").replace("bilhoes", "bilhao")
    out = set()
    for w in re.findall(r"[a-z0-9]+", t):
        if w in _VAZIAS or (len(w) < 3 and not w.isdigit()):
            continue
        out.add(w[:6])
    return out


def parecido(a: str, b: str) -> float:
    """Palavras em comum / palavras do MENOR titulo (0 a 1). Usa o menor como
    base porque titulo novo curto sobre tema velho longo e' repeticao do mesmo
    jeito ('1 poeira destroi tudo' x 'Como 1 poeira pode destruir 1 milhao')."""
    pa, pb = palavras(a), palavras(b)
    if not pa or not pb:
        return 0.0
    return len(pa & pb) / min(len(pa), len(pb))


def publicados(canal: str | None) -> list[str]:
    if not canal:
        return []
    titulos = []
    try:
        d = json.loads(SEMENTE.read_text(encoding="utf-8"))
        titulos += [x["titulo"] for x in d.get("canais", {}).get(canal, [])]
    except Exception:
        pass
    try:
        d = json.loads(TRECHOS.read_text(encoding="utf-8"))
        titulos += [v.get("titulo", "") for v in d.values()
                    if isinstance(v, dict) and v.get("canal") == canal]
    except Exception:
        pass
    vistos, out = set(), []
    for t in titulos:
        k = t.strip().lower()
        if k and k not in vistos:
            vistos.add(k)
            out.append(t.strip())
    return out


def mais_parecido(titulo: str, canal: str | None) -> tuple[float, str]:
    melhor = (0.0, "")
    for t in publicados(canal):
        s = parecido(titulo, t)
        if s > melhor[0]:
            melhor = (s, t)
    return melhor


# ⭐ 27/09/2026 (dono: "gostei da ideia de reaproveitar o tema"). O que
# derrubou as views no Modo Futuro foi a MESMA HISTORIA de novo (1.011 -> 327).
# Tema vencedor com OUTRA historia/trecho/podcast e' o contrario: e' o assunto
# que o publico ja' provou que quer. Medido nos prints de 27/09: Goggins
# 490-603, desistencia/40% 526, dopamina 500, forca de vontade 577.
TEMAS_VENCEDORES: dict[str, str] = {
    "semanestesia.pod": ("David Goggins; desistir / a regra dos 40% / limite "
                         "mental; dopamina; força de vontade"),
}


def bloco_prompt(canal: str | None) -> str:
    ts = publicados(canal)[-MAX_NO_PROMPT:]
    if not ts:
        return ""
    lista = "\n".join(f"- {t}" for t in ts)
    try:
        from . import canais_registro
        _c = canais_registro.canonico(canal) or canal
    except Exception:  # noqa: BLE001
        _c = canal
    venc = TEMAS_VENCEDORES.get(_c or "")
    excecao = (f"EXCECAO — TEMAS QUE VENCERAM ({venc}): estes DEVEM voltar, "
               "com OUTRA historia, outro trecho ou outro podcast. O que nao "
               "pode e' a MESMA historia (o mesmo caso, o mesmo numero, a "
               "mesma frase).\n") if venc else ""
    return excecao + ("\n\nJA' PUBLICADOS NESTE CANAL (os mais recentes por ultimo). Cada "
            "historia repetida rendeu MENOS que a primeira (medido: 1.011 -> 327 "
            "views). NAO escolha trecho cujo ASSUNTO CENTRAL ja' esteja aqui; "
            "prefira historia, objeto ou numero que o canal ainda nao contou:\n"
            f"{lista}\n")


def marcar(clipes: list[dict], canal: str | None) -> list[dict]:
    for c in clipes:
        base = f"{c.get('titulo', '')} {c.get('gancho', '')}"
        s, t = mais_parecido(str(c.get("titulo") or ""), canal)
        s2, t2 = mais_parecido(base, canal)
        if s2 > s:
            s, t = s2, t2
        if s >= LIMIAR:
            c["tema_repetido"] = {"parecido_com": t, "semelhanca": round(s, 2)}
            try:
                c["nota"] = float(c.get("nota", 0)) - PENALIDADE
            except (TypeError, ValueError):
                pass
            print(f"   [tema] parecido ({s:.0%}) com \"{t[:50]}\": -{PENALIDADE} "
                  f"na ordem, NAO descartado: {str(c.get('titulo'))[:50]}", flush=True)
    return clipes


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--titulo", required=True)
    a = ap.parse_args()
    s, t = mais_parecido(a.titulo, a.canal)
    print(f"{s:.0%} parecido com: {t or '(nada)'}  ({len(publicados(a.canal))} publicados)")
