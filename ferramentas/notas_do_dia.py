# -*- coding: utf-8 -*-
"""Todo dia no Telegram do dono: o texto do BALÃO ("No que você está pensando?")
de cada canal — NÃO a legenda dos posts.

⭐ 06/10/2026 (dono: "mande junto no telegram diariamente o que eu devo escrever
nos balões de cada canal"). Regra da nota (memória `nota-do-avatar`, 27/09):
teaser do PRÓXIMO post agendado, curto (cabe em 2 linhas, ≤ 40 caracteres),
concreto (número/objeto/nome), sem adjetivo de hype, no máximo 1 emoji discreto,
no tom do canal. Exemplo aprovado: "Hoje: a máquina de 180 toneladas".

Fonte: o próximo post AGENDADO de cada canal no Buffer (só leitura).
Texto: Gemini flash (engine/modelo_texto); sem modelo, cai num molde "Hoje: <título>".
Roda no GitHub Actions (.github/workflows/notas_do_dia.yml), 08:00 BRT.

Uso: python ferramentas/notas_do_dia.py [--simular]
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import agendar_buffer as ab  # noqa: E402
from engine import canais_registro as cr  # noqa: E402

LIMITE = 40


def proximo_post(c) -> str | None:
    tok = (os.environ.get(c.env) or "").strip()
    if not tok:
        return None
    org = ab.consultar(tok, "query { account { organizations { id } } }")["account"]["organizations"][0]["id"]
    chs = ab.consultar(tok, "query($i: ChannelsInput!) { channels(input: $i) { id service } }",
                       {"i": {"organizationId": org}})["channels"]
    tk = [x["id"] for x in chs if x["service"] == "tiktok"]
    if not tk:
        return None
    d = ab.consultar(tok, """query($i: PostsInput!) { posts(input: $i, first: 20) {
        edges { node { dueAt text } } } }""",
                     {"i": {"organizationId": org, "filter": {"status": ["scheduled"], "channelIds": tk[:1]}}})
    nos = sorted((e["node"] for e in d["posts"]["edges"]), key=lambda n: n.get("dueAt") or "9")
    agora = dt.datetime.now(dt.timezone.utc).isoformat()
    nos = [n for n in nos if (n.get("dueAt") or "9") >= agora]
    return (nos[0].get("text") or "").strip() if nos else None


def _titulo(texto: str) -> str:
    linha = next((l for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")), "")
    return re.sub(r"#\w+", "", linha).strip()[:80]


def nota(arroba: str, texto: str) -> str:
    t = _titulo(texto)
    try:
        from engine import modelo_texto
        r = modelo_texto.perguntar(
            "Escreva a NOTA de perfil do TikTok (o balão em cima da foto) do canal " + arroba + ".\n"
            "Ela é um teaser do próximo vídeo. Regras: no máximo " + str(LIMITE) + " caracteres; concreto "
            "(número, objeto ou nome do vídeo); sem adjetivos de exagero (incrível, chocante, insano); "
            "no máximo 1 emoji discreto; português do Brasil; tom do canal. Exemplo bom: "
            "\"Hoje: a máquina de 180 toneladas\".\n"
            "Legenda do próximo vídeo:\n" + texto[:600] + "\n\nResponda SÓ com a nota, sem aspas.")
        if r:
            r = r.strip().strip('"').strip("“”").splitlines()[0].strip()
            if 0 < len(r) <= LIMITE + 5:
                return r
    except Exception as e:                                # noqa: BLE001
        print(f"  [!] modelo: {str(e)[:60]}")
    curto = t if len(t) <= LIMITE - 6 else t[:LIMITE - 7].rsplit(" ", 1)[0] + "…"
    return f"Hoje: {curto}"


def main() -> None:
    a = argparse.ArgumentParser(); a.add_argument("--simular", action="store_true"); a = a.parse_args()
    linhas = [f"💬 NOTAS DO DIA — balão 'No que você está pensando?' ({dt.date.today():%d/%m})",
              "Copie e cole no perfil de cada canal:", ""]
    for nome, c in cr.CANAIS.items():
        try:
            txt = proximo_post(c)
        except Exception as e:                            # noqa: BLE001
            linhas.append(f"{c.arroba}: (não li a fila — {str(e)[:50]})"); continue
        if txt is None:
            linhas.append(f"{c.arroba}: (sem post agendado — manter a nota atual)"); continue
        linhas.append(f"{c.arroba}\n   {nota(c.arroba, txt)}")
    msg = "\n".join(linhas)
    print(msg)
    if not a.simular:
        from engine import telegram
        print("telegram:", telegram.enviar(msg[:telegram.LIMITE_MSG]))


if __name__ == "__main__":
    main()
