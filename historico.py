# -*- coding: utf-8 -*-
"""Registro local do que ja' foi publicado + serie temporal de views.

POR QUE EXISTE

1. DEDUP SEM API. A protecao contra duplicata do `agendar_buffer.py` consulta o
   Buffer e para em 4 paginas pra poupar orcamento — ou seja, ela e' CEGA pro
   que e' antigo. Foi essa cegueira que republicou um clipe em 25/08 e derrubou
   o alcance do dia. Com este arquivo, a checagem passa a ser completa,
   instantanea e sem gastar requisicao nenhuma.

2. CRESCIMENTO DE VIEWS. Uma medicao isolada nao diz se um video esta subindo ou
   parado. Cada execucao grava um PONTO por post; com dois pontos da' pra ver a
   velocidade. Sem isso, a mesma pergunta e' respondida do zero toda semana.

⚠️ Um video com poucas horas de vida mostrando 0 NAO e' bloqueio — o TikTok
demora a atualizar. So' chame de 0 depois de uma noite inteira.

Uso:
    python historico.py                 # puxa do Buffer e grava um ponto novo
    python historico.py --crescimento   # so' le' o disco, nao toca na API
"""
from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

import agendar_buffer as ab

RAIZ = Path(__file__).resolve().parent
PUBLICADOS = RAIZ / "estado" / "publicados.json"
SERIE = RAIZ / "estado" / "serie_views.jsonl"
ORG = "6ab9939bd05c27f623993733"
CANAL = "6ab994eaea19ca0bde09dc31"
FUSO_SP = datetime.timedelta(hours=3)


def _ler_publicados() -> dict:
    if PUBLICADOS.exists():
        try:
            return json.loads(PUBLICADOS.read_text(encoding="utf-8"))
        except Exception:
            print(f"[!] {PUBLICADOS.name} ilegivel, tratando como vazio.")
    return {}


def ja_publicado(chave: str) -> bool:
    """Checagem completa e offline. Nao gasta requisicao."""
    return chave in _ler_publicados()


def puxar(token: str, teto_paginas: int = 8,
          org: str = ORG, canal: str = CANAL) -> list[dict]:
    """Posts ja' enviados de UM canal.

    ⚠️ Recebe org/canal em vez de usar so' as constantes do topo. Ate'
    03/09/2026 este registro cobria APENAS o @modofuturo — e ele e' a rede
    offline contra REPOSTAR, a que existe justamente porque a consulta ao
    Buffer para em poucas paginas. Os outros quatro canais nao tinham rede
    nenhuma, e ninguem tinha como notar: o arquivo existia e parecia certo.
    """
    saida, cursor, paginas = [], None, 0
    while paginas < teto_paginas:
        d = ab.consultar(token, """
          query($i: PostsInput!, $a: String){ posts(input:$i, after:$a){
            pageInfo { hasNextPage endCursor }
            edges { node { id text sentAt metricsUpdatedAt
                           metrics { name value } } } } }""",
          {"i": {"organizationId": org,
                 "filter": {"status": ["sent"], "channelIds": [canal]}},
           "a": cursor})["posts"]
        saida += [e["node"] for e in d["edges"] if e["node"].get("sentAt")]
        paginas += 1
        if not d["pageInfo"]["hasNextPage"]:
            break
        cursor = d["pageInfo"]["endCursor"]
    return saida


def gravar(posts: list[dict], canal: str = "") -> tuple[int, int]:
    pub = _ler_publicados()
    novos = 0
    agora = datetime.datetime.now(datetime.timezone.utc).isoformat()[:19]
    linhas = []
    for p in posts:
        texto = p.get("text") or ""
        chave = ab._chave_texto(texto)
        if not chave:
            continue
        if chave not in pub:
            pub[chave] = {"titulo": texto.split("#")[0].strip()[:80],
                          "sentAt": p.get("sentAt")}
            novos += 1
        # ⭐ 27/09/2026 (dono: "medir cada canal separado dos outros"). O
        # post vem do Buffer JA' filtrado por canal — e' so' nao jogar fora.
        if canal and not pub[chave].get("canal"):
            pub[chave]["canal"] = canal
        v = {m["name"]: m["value"] for m in (p.get("metrics") or [])}
        confiavel = bool(p.get("metricsUpdatedAt") and p.get("sentAt")
                         and p["metricsUpdatedAt"] > p["sentAt"])
        linhas.append(json.dumps({
            "quando": agora, "chave": chave, "canal": canal,
            "sentAt": p.get("sentAt"),
            "views": v.get("Views", 0), "reacoes": v.get("Reactions", 0),
            "comentarios": v.get("Comments", 0), "shares": v.get("Shares", 0),
            "confiavel": confiavel}, ensure_ascii=False))
    PUBLICADOS.parent.mkdir(parents=True, exist_ok=True)
    PUBLICADOS.write_text(json.dumps(pub, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    with open(SERIE, "a", encoding="utf-8") as fh:
        fh.write("\n".join(linhas) + "\n")
    return novos, len(linhas)


def crescimento() -> None:
    if not SERIE.exists():
        print("Sem serie ainda. Rode `python historico.py` uma vez.")
        return
    pontos: dict[str, list[dict]] = {}
    for linha in SERIE.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        d = json.loads(linha)
        pontos.setdefault(d["chave"], []).append(d)

    instantes = sorted({d["quando"] for v in pontos.values() for d in v})
    print(f"{len(instantes)} medicao(oes) no disco: {', '.join(instantes)}\n")
    if len(instantes) < 2:
        print("So' ha um instante — o crescimento aparece na proxima rodada.")
        return

    ant, atu = instantes[-2], instantes[-1]
    print(f"{'titulo':50s} {'antes':>7s} {'agora':>7s} {'+/-':>7s}")
    pub = _ler_publicados()
    linhas, sem_medicao = [], []
    for chave, v in pontos.items():
        a = next((x for x in v if x["quando"] == ant), None)
        b = next((x for x in v if x["quando"] == atu), None)
        if not a or not b:
            continue
        titulo = pub.get(chave, {}).get("titulo", chave)[:50]
        # ZERO NAO MEDIDO NAO E' ZERO. O `confiavel` ja' era gravado na serie,
        # mas esta tabela imprimia `views` cru — entao post que o Buffer nunca
        # mediu aparecia como "0 views", identico a um fracasso real.
        #
        # Isso nao e' cosmetico: em 28 e 29/08/2026 o Bryan apagou um video e
        # quase apagou outro por causa deste 0. O da ASML mostrava 0 aqui e
        # 373 no print do TikTok, no mesmo instante.
        #
        # A sincronizacao do Buffer trava em LOTE: quando ela para, TODO post
        # publicado depois herda o 0. Por isso os zeros vem em sequencia — e
        # e' exatamente esse padrao que faz parecer contagio de alcance.
        if not b.get("confiavel", True):
            sem_medicao.append(titulo)
            continue
        linhas.append((b["views"] - a["views"], a["views"], b["views"], titulo))
    for d, a, b, t in sorted(linhas, reverse=True):
        print(f"{t:50s} {a:7.0f} {b:7.0f} {d:+7.0f}")

    if sem_medicao:
        print(f"\n{len(sem_medicao)} post(s) SEM MEDICAO — o Buffer nao atualizou "
              f"a metrica depois da publicacao.")
        print("Estes NAO estao com zero view: estao sem numero nenhum. Use o "
              "print do TikTok pra saber o valor real.")
        for t in sem_medicao:
            print(f"   (sem medicao)  {t}")


def main() -> None:
    p = argparse.ArgumentParser(description="Registro local e serie de views")
    p.add_argument("--crescimento", action="store_true",
                   help="so' le' o disco; nao toca na API do Buffer")
    a = p.parse_args()
    if a.crescimento:
        crescimento()
        por_canal()
        return
    # ⚠️ TODOS OS CANAIS, nao so' o @modofuturo.
    #
    # Ate' 03/09/2026 esta linha era `puxar(ab._token_buffer())`, que usa o
    # token e o canal padrao — o registro offline cobria UM canal de cinco.
    # Os outros quatro ficavam sem rede contra repostar, e o arquivo existia
    # e parecia certo, entao nada denunciava a falta.
    #
    # A cozinha fica de fora de proposito: o motor dela e' outro repositorio,
    # com manifesto proprio (ver o cabecalho do repor_fila.py).
    import os
    try:
        from conferir_postados import CANAIS
    except Exception:
        CANAIS = {"modofuturo": (ORG, CANAL, "BUFFER_TOKEN")}

    total_lidos = total_novos = 0
    for nome, (org, canal, env) in CANAIS.items():
        token = (os.environ.get(env) or "").strip()
        if not token:
            # ⚠️ AVISA. Canal sem token nao e' canal sem posts — e' canal que
            # nao foi olhado. Pular calado repetiria o defeito que este
            # conserto corrige.
            print(f"  [!] {nome}: sem {env} no ambiente — NAO conferido")
            continue
        try:
            posts = puxar(token, org=org, canal=canal)
        except Exception as e:
            print(f"  [!] {nome}: falhou ({str(e)[:60]}) — NAO conferido")
            continue
        novos, n = gravar(posts, canal=nome)
        total_lidos += n
        total_novos += novos
        print(f"  {nome:20} {n:4} post(s) lidos, {novos} novo(s) no registro")

    print(f"\n{total_lidos} post(s) publicado(s) lidos; {total_novos} entraram "
          f"novos no registro.")
    print(f"registro: {len(_ler_publicados())} textos ja' publicados (dedup offline)")
    crescimento()
    por_canal()


PAINEL = RAIZ / "estado" / "desempenho_por_canal.json"


def por_canal(dias: int = 7) -> dict:
    """O painel POR CANAL: a ultima leitura CONFIAVEL de cada post, somada
    por canal (total e ultimos `dias`). Grava `estado/desempenho_por_canal.json`.

    ⭐ 27/09/2026 (dono). O canal vem da leitura (desde hoje) ou, para a serie
    antiga que nao tinha o campo, do `publicados.json` — que ganha o canal na
    primeira passada nova, porque o Buffer devolve as ultimas paginas de cada
    canal. Post sem canal conhecido fica em "(sem canal)", nunca somado a outro.
    ⚠️ Leitura nao confiavel (Buffer sem metrica) NAO entra como zero.
    """
    import statistics
    if not SERIE.exists():
        return {}
    pub = _ler_publicados()
    ult: dict[str, dict] = {}
    for linha in SERIE.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        d = json.loads(linha)
        if not d.get("confiavel"):
            continue
        if d["chave"] not in ult or d["quando"] >= ult[d["chave"]]["quando"]:
            ult[d["chave"]] = d
    agora = datetime.datetime.now(datetime.timezone.utc)
    corte = (agora - datetime.timedelta(days=dias)).isoformat()[:19]
    canais: dict[str, dict] = {}
    for chave, d in ult.items():
        canal = d.get("canal") or pub.get(chave, {}).get("canal") or "(sem canal)"
        c = canais.setdefault(canal, {"posts": 0, "views": 0, "reacoes": 0,
                                      "comentarios": 0, "shares": 0,
                                      "_v": [], "_rec": []})
        c["posts"] += 1
        for k in ("views", "reacoes", "comentarios", "shares"):
            c[k] += int(d.get(k) or 0)
        c["_v"].append(int(d.get("views") or 0))
        if (d.get("sentAt") or "")[:19] >= corte:
            c["_rec"].append((int(d.get("views") or 0),
                              pub.get(chave, {}).get("titulo", chave)[:60]))
    saida = {"medido_em": agora.isoformat()[:19], "janela_dias": dias,
             "canais": {}}
    print(f"\n{'canal':22s} {'posts':>5s} {'views':>8s} {'mediana':>8s} "
          f"{'eng%':>5s} {'ult.' + str(dias) + 'd':>7s} {'views ' + str(dias) + 'd':>8s}")
    for canal, c in sorted(canais.items(), key=lambda x: -x[1]["views"]):
        eng = ((c["reacoes"] + c["comentarios"] + c["shares"]) / c["views"] * 100
               if c["views"] else 0.0)
        rec = sorted(c["_rec"], reverse=True)
        saida["canais"][canal] = {
            "posts": c["posts"], "views": c["views"],
            "mediana_views": int(statistics.median(c["_v"])) if c["_v"] else 0,
            "reacoes": c["reacoes"], "comentarios": c["comentarios"],
            "shares": c["shares"], "engajamento_pct": round(eng, 2),
            "posts_recentes": len(rec),
            "views_recentes": sum(v for v, _ in rec),
            "melhores_recentes": [{"views": v, "titulo": t} for v, t in rec[:3]],
        }
        r = saida["canais"][canal]
        print(f"{canal:22s} {r['posts']:5d} {r['views']:8d} {r['mediana_views']:8d} "
              f"{r['engajamento_pct']:5.1f} {r['posts_recentes']:7d} {r['views_recentes']:8d}")
    PAINEL.write_text(json.dumps(saida, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    return saida


if __name__ == "__main__":
    main()
