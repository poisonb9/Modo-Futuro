# -*- coding: utf-8 -*-
"""Series numeradas no titulo ("Goggins sem filtro #3: ...").

⭐ 27/09/2026 (dono aprovou o item 2 da analise do Sem Anestesia: "uma marca
propria dentro do corte"). Canal de corte de Goggins/Huberman em PT e' o que
mais tem; o que faz alguem seguir ESTE e' um formato reconhecivel. A selecao
escolhe a serie do trecho (campo `serie`); aqui ele ganha o numero.

⚠️ O NUMERO SAI DO `registro_clipes.json`, que o workflow de corte commita
depois de cada run: o maior "#N" ja' usado naquela serie, mais 1. Sem arquivo
novo de estado — um contador a parte divergiria do que foi ao ar.
⚠️ Serie fora da lista (ou canal sem series) nao mexe no titulo: falha aberta.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

SERIES: dict[str, tuple[str, ...]] = {
    "semanestesia.pod": ("Goggins sem filtro", "Protocolo",
                         "Seu cérebro desiste antes"),
}
REGISTRO = Path(__file__).resolve().parent.parent / "registro_clipes.json"


def _n(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower())
                   if unicodedata.category(c) != "Mn").strip()


def _titulos() -> list[str]:
    try:
        d = json.loads(REGISTRO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(v.get("titulo") or "") for v in (d.get("clipes") or {}).values()]


def ultimo(nome: str, titulos: list[str] | None = None) -> int:
    """O maior numero ja' usado nesta serie (0 se nunca saiu)."""
    alvo = re.compile(re.escape(_n(nome)) + r"\s*#\s*(\d+)")
    maior = 0
    for t in (_titulos() if titulos is None else titulos):
        m = alvo.match(_n(t))
        if m:
            maior = max(maior, int(m.group(1)))
    return maior


def da_lista(canal: str | None, serie) -> str | None:
    """O nome oficial da serie (como esta' em SERIES), ou None."""
    for nome in SERIES.get(canal or "", ()):
        if _n(nome) == _n(str(serie or "")):
            return nome
    return None


def numerar(c: dict, canal: str | None, usados: dict[str, int],
            titulos: list[str] | None = None) -> dict:
    """Poe "<serie> #N: " na frente do titulo. `usados` guarda os numeros ja'
    dados NESTE run (dois clipes da mesma serie no mesmo corte)."""
    try:
        from . import canais_registro
        canal = canais_registro.canonico(canal) or canal
    except Exception:  # noqa: BLE001
        pass
    nome = da_lista(canal, c.get("serie"))
    titulo = str(c.get("titulo") or "").strip()
    if not nome or not titulo or _n(titulo).startswith(_n(nome) + " #"):
        return c
    n = max(ultimo(nome, titulos), usados.get(nome, 0)) + 1
    usados[nome] = n
    c = dict(c)
    c["serie"] = f"{nome} #{n}"
    c["titulo"] = f"{nome} #{n}: {titulo}"
    return c
