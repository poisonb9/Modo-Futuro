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
from engine import legenda_post
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


def video_do_post(token: str, pid: str) -> str | None:
    """URL do video que ESTA' no post agendado (nao a do manifesto)."""
    try:
        d = ab.consultar(token, """query($i: PostInput!){ post(input:$i){
          assets { ... on VideoAsset { source } } } }""", {"i": {"id": pid}})
        for x in (d.get("post") or {}).get("assets") or []:
            if x.get("source"):
                return x["source"]
    except Exception as e:  # noqa: BLE001
        print(f"  [!] nao li o video do post: {str(e)[:200]}")
    return None


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


# ⛔ 27/09/2026, simulacao do make: o post "O contorno da mandibula... estilo
# Noze" ganhou uma legenda sobre a Rose' do BLACKPINK. Nome proprio do titulo
# (a idol, o convidado) TEM de aparecer na legenda nova.
_COMUNS = {"o", "a", "os", "as", "de", "da", "do", "e", "com", "para", "no", "na",
           "que", "um", "uma", "como", "por", "seu", "sua", "este", "esta"}


def fala_de_quem_o_titulo_fala(titulo: str, corpo: str) -> bool:
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", titulo)
    nomes = [w for i, w in enumerate(palavras)
             if i > 0 and w[:1].isupper() and not w.isupper()
             and _n(w) not in _COMUNS and len(w) > 2]
    if not nomes:
        return True
    return any(_n(w) in _n(corpo) for w in nomes)


def _editar(token: str, p: dict, texto: str, url: str, titulo: str) -> bool:
    """editPost SUBSTITUI o post inteiro: texto, video, horario e metadata."""
    d = ab.consultar(token, """mutation($input: EditPostInput!) {
      editPost(input: $input) { __typename
        ... on PostActionSuccess { post { id dueAt } }
        ... on InvalidInputError { message }
        ... on UnexpectedError { message }
        ... on RestProxyError { message } } }""", {"input": {
        "id": p["id"], "text": texto, "dueAt": p["dueAt"],
        "mode": "customScheduled", "schedulingType": "automatic",
        "assets": [{"video": {"url": url}}],
        "metadata": {"tiktok": {"isAiGenerated": True, "title": titulo[:90]}},
    }})["editPost"]
    if d["__typename"] != "PostActionSuccess":
        print(f"  [!] editPost recusou: {d['__typename']} {d.get('message', '')[:150]}")
        return False
    print(f"  ✓ trocado (horario mantido: {d['post'].get('dueAt')})")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--simular", action="store_true")
    ap.add_argument("--id", help="so' este post do Buffer")
    ap.add_argument("--texto", help="com --id: o CORPO da legenda escrito a mao")
    ap.add_argument("--video", help="com --id: troca SO' o video (url), mantem o texto")
    ap.add_argument("--so-hashtags", action="store_true",
                    help="so' corta pra 3 hashtags; mantem texto, video e horario")
    a = ap.parse_args()
    nome = canais_registro.canonico(a.canal)
    c = canais_registro.CANAIS[nome]
    token = os.environ[c.env].strip()
    os.environ["CANAL_ESPERADO"] = nome
    manif = ab.manifesto(ab._token_github(), None)
    por_titulo = {_n(m.get("titulo")): m for m in manif.values() if m.get("titulo")}
    posts = agendados(token, c.org, c.canal_id)
    if a.id:
        posts = [p for p in posts if p["id"] == a.id]
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
        url = a.video or m["url"]
        if a.so_hashtags:
            # ⛔ 28/09/2026: o TikTok aceita 3 hashtags; os agendados tinham 5.
            # O video tem de ser o QUE ESTA' NO POST (os da Wonhee ja' foram
            # trocados pelo selo corrigido — o do manifesto desfaria isso).
            novo = legenda_post.limitar_hashtags(texto)
            atual = video_do_post(token, p["id"])
            antes, depois = len(re.findall(r"#\w+", texto)), len(re.findall(r"#\w+", novo))
            print(f"\n--- {p['dueAt']}  {titulo[:60]}\n  hashtags: {antes} -> {depois}"
                  f"  video: {atual or 'NAO ACHADO'}")
            if novo == texto or a.simular:
                continue
            if not atual:
                print("  [!] video atual nao lido, pulado (nao arrisco trocar o video)")
                continue
            if _editar(token, p, novo, atual, titulo):
                trocados += 1
            continue
        if a.video:
            # ⭐ 28/09/2026: selo "PARTE 3" gravado errado — so' o video muda
            print(f"\n--- {p['dueAt']}  {titulo[:70]}\nVIDEO NOVO: {url}")
            if a.simular:
                continue
            _editar(token, p, texto, url, titulo)
            trocados += 1
            continue
        corpo = a.texto.replace("\\n", "\n") if a.texto else None
        for _ in range(0 if corpo else 2):
            corpo = nova_legenda(nome, titulo, texto[len(titulo):])
            if corpo and fala_de_quem_o_titulo_fala(titulo, corpo):
                break
            corpo = None
        if not corpo and a.texto:
            corpo = a.texto
        if not corpo:
            print(f"  [!] legenda nao gerada ou fala de OUTRA pessoa, pulado: {titulo[:60]}")
            continue
        tags = " ".join(re.findall(r"#\w+", texto))
        novo = f"{titulo}\n\n{corpo}\n\n{tags}".strip()
        print(f"\n--- {p['dueAt']}  {titulo[:70]}\nANTES ({len(texto)}): {texto[:160]!r}\n"
              f"DEPOIS ({len(novo)}):\n{novo}")
        if a.simular:
            continue
        if _editar(token, p, novo, url, titulo):
            trocados += 1
    print(f"\n{trocados} legenda(s) trocada(s){' (SIMULADO)' if a.simular else ''}.")


if __name__ == "__main__":
    main()
