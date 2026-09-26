# -*- coding: utf-8 -*-
"""Le' o GUIA DE VOZ de cada canal (.claude/skills/guia-de-voz).

    python -m engine.guia_voz --canal truque.importado      mostra o que o motor usa

## POR QUE EXISTE

Pedido do dono em 25-26/09/2026 (um guia de dublagem por canal, "isso vai
ser muito util"). Nasceu com outro nome; o dono pediu a troca em 26/09
(a palavra era de uso sagrado) — ficou GUIA DE VOZ. O prompt de narracao era UM so' para todos os canais: o de
chips e o de maquiagem recebiam o mesmo tom, e nome de idol saia pronunciado
de qualquer jeito ("Risabae" lido letra a letra pela voz clonada).

Uma fonte so', legivel pelo dono e pelo motor:
  - `## Tom`, `## Glossário`, `## Proibido` -> bloco no prompt da narracao
  - `## Pronúncia` (tabela escrita | falada) -> troca SO' no texto falado;
    a legenda continua com a grafia oficial

FALHA ABERTA: canal desconhecido, sem arquivo ou arquivo quebrado = string
vazia / texto intacto. O motor segue como antes.
"""
from __future__ import annotations

import argparse
import os
import re
from functools import lru_cache
from pathlib import Path

PASTA = (Path(__file__).resolve().parent.parent / ".claude" / "skills"
         / "guia-de-voz" / "canais")


def _canal(canal: str | None) -> str | None:
    if not canal:
        return None
    try:
        from . import canais_registro
        return canais_registro.canonico(canal)
    except Exception:
        return None


@lru_cache(maxsize=16)
def secoes(canal: str | None) -> dict[str, str]:
    """{titulo_da_secao_minusculo: corpo} do arquivo do canal, ou {}."""
    nome = _canal(canal)
    if not nome:
        return {}
    arq = PASTA / f"{nome}.md"
    if not arq.exists():
        return {}
    out, atual = {}, None
    for linha in arq.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", linha)
        if m:
            atual = m.group(1).strip().lower()
            out[atual] = []
        elif atual is not None:
            out[atual].append(linha)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def _secao(canal, *nomes) -> str:
    s = secoes(canal)
    for n in nomes:
        if s.get(n):
            return s[n]
    return ""


def bloco_prompt(canal: str | None) -> str:
    """O trecho que entra no prompt de narracao. Vazio sem guia de voz."""
    tom = _secao(canal, "tom")
    glos = _secao(canal, "glossário", "glossario")
    proib = _secao(canal, "proibido")
    if not (tom or glos or proib):
        return ""
    partes = ["GUIA DE VOZ DO CANAL (vale acima das regras gerais quando conflitar):"]
    if tom:
        partes.append(f"TOM: {tom}")
    if glos:
        partes.append(f"GLOSSÁRIO:\n{glos}")
    if proib:
        partes.append(f"PROIBIDO:\n{proib}")
    return "\n".join(partes) + "\n\n"


@lru_cache(maxsize=16)
def pronuncias(canal: str | None) -> tuple[tuple[str, str], ...]:
    """((escrita, falada), ...) da tabela; '(a conferir)' e' tirado da fala."""
    pares = []
    for linha in _secao(canal, "pronúncia", "pronuncia").splitlines():
        cel = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(cel) < 2 or not cel[0] or set(cel[0]) <= {"-", ":"}:
            continue
        if cel[0].lower() in ("escrita",):
            continue
        falada = re.sub(r"\(a conferir\)", "", cel[1]).strip()
        if falada:
            pares.append((cel[0], falada))
    # o mais longo primeiro: "Stray Kids" antes de "Kids"
    return tuple(sorted(pares, key=lambda p: -len(p[0])))


def para_fala(texto: str, canal: str | None = None) -> str:
    """Troca a GRAFIA pela FALA, palavra inteira, sem diferenciar maiuscula.
    So' para o texto que vai ao TTS — nunca para legenda ou titulo."""
    if canal is None:
        canal = os.environ.get("CANAL_ESPERADO")
    for escrita, falada in pronuncias(canal):
        texto = re.sub(rf"(?<!\w){re.escape(escrita)}(?!\w)", falada, texto,
                       flags=re.IGNORECASE)
    return texto


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    a = ap.parse_args()
    print(bloco_prompt(a.canal) or "(sem guia de voz para este canal)")
    for e, f in pronuncias(a.canal):
        print(f"  {e!r} -> {f!r}")
