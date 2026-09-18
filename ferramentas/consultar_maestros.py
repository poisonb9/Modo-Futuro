# -*- coding: utf-8 -*-
"""Consulta o acervo destilado por PROBLEMA, com pesos por palavra e temas.

Nasceu em 18/09/2026, das tres consultas sobre o site do Achadinho Total
(MAESTROS_DESIGN_DO_SITE.md, MAESTROS_ESTETICA_DO_SITE.md no Modo-Futuro).
Ate' entao a mecanica era reescrita no chat a cada pergunta.

⚠️ NAO ENVIESA NEM LIMITA A BUSCA: e' so' o parse do `por_resultado.md` +
uma pontuacao por palavra que VOCE passa na linha de comando. Mudou a
pergunta, mudam as palavras — o acervo e' lido inteiro toda vez.

    python ferramentas/consultar_maestros.py "landing page=4" "prova social=4" "afiliad=3" --min 7
    python ferramentas/consultar_maestros.py --tema "IMAGEM=foto|imagem" --tema "CTA=bot[aã]o|cta" ...
    python ferramentas/consultar_maestros.py --video "Design for Startups"     # tudo de um video

Saida: DEMONSTRADO primeiro, depois OPINIAO (sao poucas e carregam principio),
depois AFIRMADO. Cada linha: [base pontos] situacao -> saida · video.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# MORA NO PROJETO, nao no acervo (Bryan, 18/09/2026: "nao coloca dentro da
# propria skill, posso usar o maestros para outros projetos e nao quero
# vies"). O acervo e' so' LIDO daqui.
SKILL = (Path.home() / "Documents" / "skills_de_trabalho" / ".claude" / "skills"
         / "maestros-da-ia" / "referencias" / "por_resultado.md")
ORDEM = {"DEMONSTRADO": 0, "OPINIAO": 1, "AFIRMADO": 2}


def fichas() -> list[dict]:
    txt = SKILL.read_text(encoding="utf-8")
    sec, out = None, []
    for line in txt.splitlines():
        if line.startswith("## "):
            sec = line[3:].split()[0]
            continue
        if line.startswith("- "):
            out.append({"sec": sec, "sit": line[2:], "lines": []})
        elif line.startswith("  - ") and out:
            out[-1]["lines"].append(line.strip())
    for f in out:
        f["txt"] = f["sit"] + " " + " ".join(f["lines"])
        f["saida"] = next((l for l in f["lines"] if "Saída" in l), "")[14:]
        src = next((l for l in f["lines"] if l.startswith("- _")), "")
        m = re.search(r"· (?:\d{4}-\d\d-\d\d|\?) · (.*?)_?$", src)
        f["video"] = (m.group(1) if m else "").strip("_ ")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("pesos", nargs="*", help='"regex=peso"')
    p.add_argument("--min", type=int, default=7)
    p.add_argument("--tema", action="append", default=[], help='"NOME=regex"')
    p.add_argument("--video", default="", help="substring do titulo do video")
    p.add_argument("--max", type=int, default=60)
    a = p.parse_args()
    todas = fichas()
    # ⛔ GUARDA (Bryan, 18/09: "a skill vai mudar muito, isso pode ficar
    # desatualizado"): este script so' conhece o FORMATO do indice, nao o
    # conteudo. Se o gerar_skill.py mudar o formato, falha aqui, alto —
    # nunca uma consulta vazia que parece "o acervo nao tem nada".
    if len(todas) < 1000 or sum(1 for f in todas if f["saida"]) < len(todas) // 2:
        sys.exit(f"formato do indice mudou? li {len(todas)} fichas, "
                 f"{sum(1 for f in todas if f['saida'])} com 'Saída' — ver fichas() e gerar_skill.py")
    if a.video:
        sel = [f for f in todas if a.video.lower() in f["video"].lower()]
        for f in sorted(sel, key=lambda f: ORDEM.get(f["sec"], 9)):
            print(f"[{f['sec'][:3]}] {f['sit'][:120]} -> {f['saida'][:200]}")
        print(f"\n{len(sel)} fichas de '{a.video}'", file=sys.stderr)
        return
    pesos = []
    for x in a.pesos:
        rx, _, w = x.rpartition("=")
        pesos.append((re.compile(rx, re.I), int(w or 1)))
    if not pesos:
        sys.exit("passe pelo menos um 'regex=peso'")
    for f in todas:
        f["s"] = sum(w for rx, w in pesos if rx.search(f["txt"]))
    hits = [f for f in todas if f["s"] >= a.min]
    hits.sort(key=lambda f: (ORDEM.get(f["sec"], 9), -f["s"]))
    print(f"{len(todas)} fichas; {len(hits)} com pontos >= {a.min}: "
          f"{dict(Counter(f['sec'] for f in hits))}", file=sys.stderr)
    temas = [(t.split("=", 1)[0], re.compile(t.split("=", 1)[1], re.I)) for t in a.tema]
    if temas:
        for nome, rx in temas:
            sel = [f for f in hits if rx.search(f["txt"])]
            print(f"\n#### {nome}: {len(sel)}")
            for f in sel[:a.max]:
                print(f"[{f['sec'][:3]} {f['s']}] {f['sit'][:110]} -> {f['saida'][:170]} · {f['video'][:40]}")
    else:
        for f in hits[:a.max]:
            print(f"[{f['sec'][:3]} {f['s']}] {f['sit'][:110]} -> {f['saida'][:170]} · {f['video'][:40]}")


if __name__ == "__main__":
    main()
