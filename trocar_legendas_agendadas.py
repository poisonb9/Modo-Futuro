# -*- coding: utf-8 -*-
"""Troca a LEGENDA dos posts JA' AGENDADOS no Buffer pelo formato do canal.

⭐ 27/09/2026 (dono: "atualize as legendas dos proximos videos que ja' estao
encadeados no buffer"). Os agendados foram escritos com o formato antigo
(fatos + setas do Modo Futuro) antes de `engine/legenda_canais.py` existir.

⚠️ `editPost` SUBSTITUI O POST INTEIRO (handoff 25/08): vai texto, video,
horario e metadata juntos, senao o Buffer responde "Post must have either
text or media". O video sai do manifesto da release (casado pelo titulo).
⚠️ O HORARIO NAO MUDA: reenviamos o `dueAt` que o post ja' tinha.

    python trocar_legendas_agendadas.py --canal truque.importado --simular
    python trocar_legendas_agendadas.py --canal truque.importado
"""
from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata

import agendar_buffer as ab
from engine import canais_registro, legenda_canais, traducao


def _n(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower())
                   if unicodedata.category(c) != "Mn")


def agendados(token: str, org: str, canal: str) -> list[dict]:
    d = ab.consultar(token, """
      query($i: PostsInput!){ posts(input:$i){ edges { node {
        id text dueAt } } } }""",
      {"i": {"organizationId": org,
             "filter": {"status": ["scheduled"], "channelIds": [canal]}}})
    return [e["node"] for e in d["posts"]["edges"]]


def nova_legenda(canal: str, titulo: str, texto_antigo: str) -> str | None:
    prompt = legenda_canais.prompt_do_canal(canal)
    if not prompt:
        return None
    fala = ("TITULO DO VIDEO: " + titulo + "\nLEGENDA ANTIGA (use SO' o que for do "
            "assunto do video; ignore dados de industria/economia/tecnologia): "
            + texto_antigo[:1400])
    r = traducao._traduzir_texto(fala, prompt=prompt)
    r = re.sub(r"^```.*?$|^```$", "", r or "", flags=re.M).strip()
    return r or None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()
    nome = canais_registro.canonico(a.canal)
    c = canais_registro.CANAIS[nome]
    token = os.environ[c.env].strip()
    os.environ["CANAL_ESPERADO"] = nome
    manif = ab.manifesto(ab._token_github(), None)
    por_titulo = {_n(m.get("titulo")): m for m in manif.values() if m.get("titulo")}
    posts = agendados(token, c.org, c.canal_id)
    print(f"{nome}: {len(posts)} agendado(s)")
    trocados = 0
    for p in posts:
        texto = p.get("text") or ""
        m = max((v for k, v in por_titulo.items() if k and _n(texto).startswith(k)),
                key=lambda v: len(v.get("titulo", "")), default=None)
        if not m or not m.get("url"):
            print(f"  [!] sem video no manifesto, pulado: {texto[:60]!r}")
            continue
        titulo = m["titulo"].strip()
        corpo = nova_legenda(nome, titulo, texto[len(titulo):])
        if not corpo:
            print(f"  [!] legenda nao gerada, pulado: {titulo[:60]}")
            continue
        tags = " ".join(re.findall(r"#\w+", texto))
        novo = f"{titulo}\n\n{corpo}\n\n{tags}".strip()
        print(f"\n--- {p['dueAt']}  {titulo[:70]}\nANTES ({len(texto)}): {texto[:160]!r}\n"
              f"DEPOIS ({len(novo)}):\n{novo}")
        if a.simular:
            continue
        d = ab.consultar(token, """mutation($input: EditPostInput!) {
          editPost(input: $input) { __typename
            ... on PostActionSuccess { post { id dueAt } }
            ... on InvalidInputError { message }
            ... on UnexpectedError { message }
            ... on RestProxyError { message } } }""", {"input": {
            "id": p["id"], "text": novo, "dueAt": p["dueAt"],
            "mode": "customScheduled", "schedulingType": "automatic",
            "assets": [{"video": {"url": m["url"]}}],
            "metadata": {"tiktok": {"isAiGenerated": True, "title": titulo[:90]}},
        }})["editPost"]
        if d["__typename"] != "PostActionSuccess":
            print(f"  [!] editPost recusou: {d['__typename']} {d.get('message', '')[:150]}")
            continue
        trocados += 1
        print(f"  ✓ trocado (horario mantido: {d['post'].get('dueAt')})")
    print(f"\n{trocados} legenda(s) trocada(s){' (SIMULADO)' if a.simular else ''}.")


if __name__ == "__main__":
    main()
