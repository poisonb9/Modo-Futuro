# -*- coding: utf-8 -*-
"""Enfileira clipes no Buffer, na ordem certa, respeitando o teto do plano.

POR QUE EXISTE
O plano gratuito do Buffer guarda no máximo 10 posts agendados por canal. Não
é limite de total, é de FILA: a cada post enviado, um slot volta. Então a fila
não precisa ser profunda — precisa ser reabastecida. Este script faz isso.

AS TRÊS REGRAS, todas pedidas pelo Bryan e todas com motivo:

1. ORDEM CRONOLÓGICA DENTRO DO MESMO VÍDEO-FONTE. Ordenar por nota embaralha a
   narrativa: no run #159 a nota 95 estava aos 141s do fonte, a 93 aos 1210s e
   a 92 aos 54s — o trecho dos 20 minutos ia ao ar antes do trecho do primeiro
   minuto. Ordena por `inicio_s`, que o `publicar_release.py` carrega até o
   manifesto.

2. UMA VAGA SEMPRE LIVRE. Enche até 9 dos 10, pro Bryan conseguir encaixar algo
   na mão sem precisar apagar nada.

3. RÓTULO DE IA SEMPRE MARCADO (`isAiGenerated`). A interface do Buffer não
   expõe esse campo — a API expõe. É a única forma de marcar esses vídeos.

DEDUPLICAÇÃO SEM REGISTRO LOCAL: compara o texto dos posts que já estão no
Buffer com a legenda do clipe. Arquivo de registro não serviria, porque este
script roda tanto na VPS quanto no runner do GitHub, e no runner ele nasce
vazio a cada execução.

Uso:
    python agendar_buffer.py --simular    # mostra o que faria, não manda nada
    python agendar_buffer.py              # enfileira de verdade
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import requests

API_BUFFER = "https://api.buffer.com/"
API_GITHUB = "https://api.github.com"
REPO = os.environ.get("GITHUB_REPO", "poisonb9/Modo-Futuro")

# Teto do plano gratuito, medido em 25/08/2026 (o app avisa "1 post left" com
# 9 na fila). RESERVA fica de fora de propósito — ver regra 2.
LIMITE_FILA = 10
RESERVA_MANUAL = 1

RAIZ = Path(__file__).resolve().parent


def _token_buffer() -> str:
    v = (os.environ.get("BUFFER_TOKEN") or "").strip()
    if v:
        return v
    arq = RAIZ / "buffer_token.txt"
    if arq.exists():
        return arq.read_text(encoding="utf-8").strip()
    sys.exit("Falta BUFFER_TOKEN (variável de ambiente ou buffer_token.txt).")


def _token_github() -> str:
    for nome in ("GITHUB_TOKEN", "GH_TOKEN"):
        v = (os.environ.get(nome) or "").strip()
        if v:
            return v
    arq = RAIZ / "github_token.txt"
    if arq.exists():
        return arq.read_text(encoding="utf-8").strip()
    sys.exit("Falta GITHUB_TOKEN — sem ele não dá pra ler o manifesto.")


def consultar(token: str, query: str, variaveis: dict | None = None) -> dict:
    r = requests.post(API_BUFFER,
                      headers={"Authorization": f"Bearer {token}",
                               "Content-Type": "application/json"},
                      json={"query": query, "variables": variaveis or {}},
                      timeout=180)
    d = r.json()
    if "errors" in d:
        raise RuntimeError(json.dumps(d["errors"], ensure_ascii=False)[:400])
    return d["data"]


def contexto_buffer(token: str) -> tuple[str, str, list[dict]]:
    """Devolve (organizationId, channelId do TikTok, posts já agendados)."""
    org = consultar(token, "{ account { organizations { id } } }")
    org_id = org["account"]["organizations"][0]["id"]

    canais = consultar(token, """
      query($i: ChannelsInput!) { channels(input: $i) { id service name } }""",
      {"i": {"organizationId": org_id}})["channels"]
    tiktok = [c for c in canais if c["service"] == "tiktok"]
    if not tiktok:
        sys.exit("Nenhum canal TikTok conectado nesta conta do Buffer.")

    agendados, cursor = [], None
    while True:
        d = consultar(token, """
          query($i: PostsInput!, $a: String) { posts(input: $i, after: $a) {
            pageInfo { hasNextPage endCursor }
            edges { node { id status text dueAt } } } }""",
          {"i": {"organizationId": org_id,
                 "filter": {"status": ["scheduled"],
                            "channelIds": [tiktok[0]["id"]]}}, "a": cursor})["posts"]
        agendados += [e["node"] for e in d["edges"]]
        if not d["pageInfo"]["hasNextPage"]:
            break
        cursor = d["pageInfo"]["endCursor"]
    return org_id, tiktok[0]["id"], agendados


def manifesto(token_gh: str, tag: str | None = None) -> dict:
    """Lê o manifesto.json das releases de clipes.

    Junta TODAS as releases `clipes-*`, não só a do mês: um clipe de fim de mês
    pode ser agendado no mês seguinte, e ele mora na release antiga.
    """
    h = {"Authorization": f"Bearer {token_gh}", "Accept": "application/vnd.github+json"}
    r = requests.get(f"{API_GITHUB}/repos/{REPO}/releases?per_page=100", headers=h, timeout=60)
    r.raise_for_status()
    tudo = {}
    for rel in r.json():
        if tag and rel["tag_name"] != tag:
            continue
        if not tag and not rel["tag_name"].startswith("clipes-"):
            continue
        for a in rel.get("assets", []):
            if a["name"] == "manifesto.json":
                try:
                    tudo.update(requests.get(a["browser_download_url"], timeout=60).json())
                except Exception as e:
                    print(f"  [!] manifesto de {rel['tag_name']} ilegível: {str(e)[:70]}")
    return tudo


def _chave_texto(t: str) -> str:
    """Normaliza pra comparar legenda de clipe com texto de post do Buffer.

    Sem acento, sem hashtag, sem pontuação, minúsculo. O Buffer às vezes
    devolve o texto com espaçamento diferente do que foi enviado, então
    comparação literal não serve.
    """
    t = (t or "").split("#")[0]
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", t.lower())[:70]


def ordenar(clipes: dict) -> list[tuple[str, dict]]:
    """Ordem de postagem: por vídeo-fonte, e dentro dele por posição no original.

    Os vídeos-fonte entram na ordem em que foram publicados na release; dentro
    de cada um, o corte mais no início do vídeo vai primeiro. É a regra 1.
    """
    itens = list(clipes.items())
    primeira_aparicao = {}
    for _, v in itens:
        f = v.get("fonte") or ""
        d = v.get("publicado_em") or ""
        if f not in primeira_aparicao or d < primeira_aparicao[f]:
            primeira_aparicao[f] = d

    def chave(par):
        _, v = par
        # Republicacao vai pro FIM da fila, sempre. Sao clipes que ja' foram ao
        # ar uma vez (ou que foram tirados da fila por terem sido postados sem
        # rotulo de IA) e voltam pelo pipeline. Sem isto eles entrariam na
        # FRENTE, porque a ordenacao usa a data de publicacao na release e o
        # lote deles e' mais antigo — o oposto do que o Bryan pediu em 25/08.
        rep = 1 if v.get("republicacao") else 0
        fonte = v.get("fonte") or ""
        # inicio_s ausente (clipe antigo, de antes do manifesto) cai pro fim do
        # seu grupo em vez de quebrar a ordenação
        inicio = v.get("inicio_s")
        return (rep, primeira_aparicao.get(fonte, ""), fonte,
                float("inf") if inicio is None else float(inicio))

    return sorted(itens, key=chave)


def enfileirar(token: str, canal: str, clipe: dict, simular: bool) -> str:
    legenda = (clipe.get("legenda") or clipe.get("titulo") or "").strip()
    titulo = (clipe.get("titulo") or legenda.split("#")[0]).strip()[:90]
    if simular:
        return "SIMULADO"
    m = """mutation($input: CreatePostInput!) {
      createPost(input: $input) { __typename
        ... on PostActionSuccess { post { id status dueAt } }
        ... on RestProxyError { code message }
        ... on LimitReachedError { message }
        ... on InvalidInputError { message }
        ... on UnauthorizedError { message }
        ... on UnexpectedError { message } } }"""
    d = consultar(token, m, {"input": {
        "channelId": canal,
        "text": legenda,
        "mode": "addToQueue",          # o Buffer encaixa no próximo slot da agenda
        "schedulingType": "automatic",
        "assets": [{"video": {"url": clipe["url"]}}],
        "metadata": {"tiktok": {"isAiGenerated": True, "title": titulo}},
    }})["createPost"]
    if d["__typename"] != "PostActionSuccess":
        raise RuntimeError(f"{d['__typename']}: {d.get('message', '')[:160]}")
    return d["post"].get("dueAt") or "sem horário"


def main() -> None:
    p = argparse.ArgumentParser(description="Enfileira clipes no Buffer")
    p.add_argument("--simular", action="store_true",
                   help="mostra o que faria, sem mandar nada")
    p.add_argument("--tag", help="usa só uma release (padrão: todas as clipes-*)")
    p.add_argument("--reserva", type=int, default=RESERVA_MANUAL,
                   help="vagas deixadas livres pro Bryan (padrão 1)")
    a = p.parse_args()

    tb, tg = _token_buffer(), _token_github()
    _, canal, agendados = contexto_buffer(tb)
    alvo = LIMITE_FILA - a.reserva
    vagas = alvo - len(agendados)
    print(f"fila: {len(agendados)}/{LIMITE_FILA} agendados, "
          f"{a.reserva} reservada(s) -> {max(0, vagas)} vaga(s) pra encher")
    if vagas <= 0:
        print("nada a fazer: fila cheia.")
        return

    todos = manifesto(tg, a.tag)
    if not todos:
        print("manifesto vazio — nenhum clipe publicado em release ainda.")
        return

    ja = {_chave_texto(x["text"]) for x in agendados}
    fila = [(k, v) for k, v in ordenar(todos)
            if _chave_texto(v.get("legenda") or v.get("titulo") or "") not in ja]
    print(f"{len(todos)} clipe(s) no manifesto, {len(fila)} ainda não agendado(s)\n")

    enviados = 0
    for chave, clipe in fila:
        if enviados >= vagas:
            break
        titulo = (clipe.get("titulo") or "")[:56]
        try:
            quando = enfileirar(tb, canal, clipe, a.simular)
        except Exception as e:
            print(f"  [!] {titulo}: {str(e)[:140]}")
            continue
        ini = clipe.get("inicio_s")
        pos = f"{float(ini):.0f}s do fonte" if ini is not None else "posição ?"
        print(f"  nota {clipe.get('nota', 0):.0f}  {pos:>14}  {titulo}")
        print(f"       -> {quando}")
        enviados += 1

    print(f"\n{enviados} clipe(s) {'simulado(s)' if a.simular else 'enfileirado(s)'}; "
          f"{len(fila) - enviados} esperando a próxima vaga.")


if __name__ == "__main__":
    main()
