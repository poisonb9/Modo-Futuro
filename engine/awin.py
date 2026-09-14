# -*- coding: utf-8 -*-
"""Awin: ver o estado das candidaturas sem abrir o painel.

    python -m engine.awin              o placar: aprovado, pendente, recusado
    python -m engine.awin --links      o link de afiliado de cada aprovado

## ⚠️ O QUE ESTE MODULO RESOLVE

Candidatura no Awin nao avisa quando muda. A aprovacao chega por e-mail, e
e-mail se perde — e um anunciante aprovado que ninguem percebeu e' comissao
parada. Aqui o estado se le' em dois segundos.

⚠️ E A MAQUINA ALCANCA O AWIN, ao contrario do AliExpress (ver
`engine/aliexpress.py`): `api.awin.com` responde 401 sem token, que e'
resposta. Entao isto roda aqui mesmo.

## ⚠️ O TOKEN E' DE LEITURA E ESCRITA — TRATE COMO SENHA

Ele vive no `.env`, que nao e' versionado. Nunca no repositorio: este e'
publico.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

RAIZ = Path(__file__).resolve().parent.parent
# ⚠️ VERSIONADO de proposito (vai no commit do garimpo). Sem isso o runner
# efemero nasce sem linha de base todo dia, e "mudou desde ontem" viraria
# "mudou desde ha' cinco minutos" — ou seja, nunca avisaria nada.
ESTADO = RAIZ / "estado" / "awin_programas.json"

API = "https://api.awin.com"
# ⚠️ O `joined` e' o que importa: so' anunciante aprovado gera comissao.
# `pending` e' expectativa, e confundir os dois faz a gente publicar produto
# de loja que ainda nao nos aceitou — link que leva a lugar nenhum.
RELACOES = ("joined", "pending", "rejected", "suspended")


def _credencial() -> tuple[str, str]:
    t = os.getenv("AWIN_TOKEN")
    p = os.getenv("AWIN_PUBLISHER_ID")
    if not (t and p):
        raise RuntimeError(
            "faltam AWIN_TOKEN / AWIN_PUBLISHER_ID no .env "
            "(o token sai em Conta -> Credenciais de API)")
    return t, p


def programas(relacao: str = "joined") -> list[dict]:
    tok, pid = _credencial()
    r = requests.get(f"{API}/publishers/{pid}/programmes",
                     params={"relationship": relacao},
                     headers={"Authorization": "Bearer " + tok}, timeout=30)
    r.raise_for_status()
    return r.json()


def link(destino: str, id_anunciante: int) -> str:
    """O link de afiliado pra uma pagina da loja.

    ⚠️ `awclick.php` com `mid` (o anunciante) e `id` (nos) e' o formato que o
    Awin rastreia. Link sem o `id` funciona e NAO paga — e' o jeito mais
    silencioso de perder comissao, porque a pagina abre normalmente.
    """
    _, pid = _credencial()
    from urllib.parse import quote
    return (f"https://www.awin1.com/cread.php?awinmid={id_anunciante}"
            f"&awinaffid={pid}&ued={quote(destino, safe='')}")


def _instantaneo() -> dict:
    """{nome do anunciante: relacao} pra TODAS as relacoes, agora."""
    return {x.get("name") or str(x.get("id")): rel
            for rel in RELACOES for x in programas(rel)}


def _salvo() -> dict | None:
    if not ESTADO.exists():
        return None
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))["programas"]
    except (ValueError, KeyError):
        return None


def vigiar(avisar: bool = True) -> list[str]:
    """Compara com a ultima leitura e devolve as linhas do que MUDOU.

    ⭐ POR QUE ISTO EXISTE: candidatura aprovada nao avisa ninguem. A
    aprovacao chega por e-mail, e e-mail se perde — anunciante aprovado que
    ninguem percebeu e' comissao parada enquanto o canal publica AliExpress
    a 7%.

    ⚠️ PRIMEIRA LEITURA NAO AVISA NADA. Sem linha de base, as 28 pendentes
    de hoje seriam 28 "novidades" — e um aviso que grita na estreia ensina a
    ignorar o aviso. Grava a base e fica quieto.

    ⚠️ E SO' GRAVA SE A LEITURA DEU CERTO. Gravar apos falha apagaria a
    linha de base, e a proxima rodada acusaria mudanca que nao houve.
    """
    agora = _instantaneo()          # se estourar, nao grava nada: e' de proposito
    antes = _salvo()
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(
        {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "programas": agora}, ensure_ascii=False, indent=2) + chr(10),
        encoding="utf-8")
    if antes is None:
        print(f"awin: linha de base gravada ({len(agora)} anunciantes). "
              "Da proxima vez eu comparo.")
        return []

    linhas = []
    for nome, rel in sorted(agora.items()):
        rel_antes = antes.get(nome)
        if rel_antes == rel:
            continue
        if rel_antes is None:
            linhas.append(f"NOVO      {nome} ({rel})")
        elif rel == "joined":
            # ⭐ A unica linha que vale dinheiro hoje.
            linhas.append(f"APROVADO  {nome}  <- da pra publicar produto dele")
        else:
            linhas.append(f"mudou     {nome}: {rel_antes} -> {rel}")
    for nome in sorted(set(antes) - set(agora)):
        linhas.append(f"sumiu     {nome} (era {antes[nome]})")

    if linhas:
        print("awin mudou:")
        for L in linhas:
            print("   " + L)
        if avisar:
            # ⚠️ O MOTIVO DA RECUSA NAO VEM POR AQUI. A API de programmes so'
            # da' a relacao; o porque' chega no e-mail do Awin (medido em
            # 14/09/2026: a 365Rider recusou por "O site nao complementa a
            # marca do anunciante"). Entao o aviso manda olhar o e-mail em vez
            # de inventar uma explicacao.
            from . import telegram
            telegram.enviar("Awin mudou:" + chr(10) + chr(10)
                            + chr(10).join(linhas) + chr(10) + chr(10)
                            + "O motivo (se houve recusa) so' vem no e-mail.")
    else:
        print("awin: nada mudou.")
    return linhas

def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="estado das candidaturas no Awin")
    a.add_argument("--links", action="store_true",
                   help="mostra o link de afiliado dos aprovados")
    a.add_argument("--vigiar", action="store_true",
                   help="avisa so' o que MUDOU desde a ultima leitura")
    o = a.parse_args()

    if o.vigiar:
        vigiar()
        return

    for rel in RELACOES:
        try:
            d = programas(rel)
        except requests.HTTPError as e:
            print(f"{rel:10} — {e}")
            continue
        print(f"\n{rel.upper()}: {len(d)}")
        for x in sorted(d, key=lambda y: y.get("name") or ""):
            print(f"   {x.get('name')}  ({x.get('primarySector') or 'sem setor'})")
            if o.links and rel == "joined":
                print("      ", link(x.get("displayUrl", ""), x["id"]))


if __name__ == "__main__":
    main()
