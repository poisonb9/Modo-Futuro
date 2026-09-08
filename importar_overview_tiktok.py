# -*- coding: utf-8 -*-
"""Importa o Overview do TikTok Studio: a serie DIARIA de cada conta.

Pedido do Bryan em 08/09/2026: "consegui de todas as contas, podemos fazer
isso todos os meses. isso e' ouro".

⚠️ ESTE EXPORT NAO E' O MESMO QUE O CICLO SEMANAL PRECISA, e confundir os
dois custa caro.

    Overview   uma linha por DIA, somando a conta inteira. Colunas: Date,
               Video Views, Profile Views, Likes, Comments, Shares.
               -> serve pra SAUDE do canal: tendencia, queda, recuperacao.
    por POST   uma linha por VIDEO, com as views daquele video.
               -> e' o que ranqueia os 2 melhores da semana. Ainda falta.

O `importar_metricas_tiktok.py` le' o segundo. Este le' o primeiro. Um nao
substitui o outro: com o Overview da' pra saber que o canal caiu, nunca QUAL
video caiu.

## O QUE ESTA SERIE JA' PROVOU, no primeiro import (08/09/2026)

Ela corrigiu duas coisas que o projeto dava como medidas:

  1. O colapso de agosto nao foi um dia — foram **19 DIAS**. O @modofuturo
     saiu de 957 views/dia (27/07-02/08) para **30/dia** (03/08-21/08), uma
     queda de 97%, e so' voltou em 22/08.
  2. **O "colapso de 25/08" nunca existiu.** Naquele dia o canal fez 1843
     views, entre 780 e 2189 dos vizinhos. Era o meio da melhor fase.

⚠️ A causa registrada pros dois colapsos era DUPLICATA. Um dos dois nao era
colapso, entao a evidencia dessa causa e' metade do que estava escrito. A
duplicata continua sendo coisa a evitar — mas ela deixou de ser um fato
medido duas vezes e voltou a ser uma hipotese apoiada em UM caso.

⚠️ E o rotulo de IA (`isAiGenerated`) NAO explica a recuperacao: ele entrou no
codigo em 25/08 (commit 2c22052), e a recuperacao comecou em 22/08 — TRES
DIAS ANTES. Uma causa nao pode vir depois do efeito.

## O HISTORICO PARA EM 60 DIAS

Por isso "todo mes" e' o intervalo certo, e por isso este script ACUMULA em
disco em vez de substituir: o que nao for importado dentro da janela some do
TikTok pra sempre.

Uso:
    python importar_overview_tiktok.py --pasta "C:\\...\\Overview Agosto-Setembro"
    python importar_overview_tiktok.py --pasta ... --simular
    python importar_overview_tiktok.py --relatorio
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SERIE = RAIZ / "estado" / "overview_tiktok.json"

MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5,
         "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10,
         "novembro": 11, "dezembro": 12,
         "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
         "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
         "november": 11, "december": 12}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _data(txt: str, ano: int) -> str | None:
    """"3 de agosto" e "August 3, 2026" viram "2026-08-03".

    ⚠️ O ANO NAO VEM NA COLUNA quando o formato e' "3 de agosto" — o export
    so' traz dia e mes. Ele e' deduzido do nome do arquivo, e por isso o nome
    do arquivo entra na conta. Chutar o ano atual quebraria a virada de
    dezembro pra janeiro, em silencio.
    """
    t = _norm(txt)
    m = re.match(r"(\d{1,2})\s+de\s+(\w+)", t)
    if m and m.group(2) in MESES:
        return f"{ano:04d}-{MESES[m.group(2)]:02d}-{int(m.group(1)):02d}"
    m = re.match(r"(\w+)\s+(\d{1,2})(?:,\s*(\d{4}))?", t)
    if m and m.group(1) in MESES:
        a = int(m.group(3)) if m.group(3) else ano
        return f"{a:04d}-{MESES[m.group(1)]:02d}-{int(m.group(2)):02d}"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", t)
    return m.group(0) if m else None


def _canal_e_ano(nome: str) -> tuple[str, int]:
    """`Overview_2026-07-09_1788719289_modofuturo.zip` -> (modofuturo, 2026)."""
    base = Path(nome).stem
    ano = int(m.group(1)) if (m := re.search(r"(20\d{2})-\d{2}-\d{2}", base)) else 2026
    return base.rsplit("_", 1)[-1], ano


def ler(caminho: Path) -> tuple[str, list[dict], str]:
    canal, ano = _canal_e_ano(caminho.name)
    if caminho.suffix.lower() == ".zip":
        z = zipfile.ZipFile(caminho)
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not nomes:
            return canal, [], "zip sem csv dentro"
        texto = z.read(nomes[0]).decode("utf-8-sig", errors="replace")
    else:
        texto = caminho.read_text(encoding="utf-8-sig", errors="replace")
    linhas = list(csv.DictReader(io.StringIO(texto)))
    if not linhas:
        return canal, [], "csv sem linhas"
    cab = {_norm(k): k for k in linhas[0]}
    c_data = cab.get("date") or cab.get("data")
    c_vw = cab.get("video views") or cab.get("visualizacoes do video")
    if not c_data or not c_vw:
        return canal, [], (
            "nao achei as colunas Date/Video Views. NAO chutei nenhuma.\n"
            f"  colunas: {', '.join(linhas[0].keys())}")

    def num(v):
        s = re.sub(r"[.,\s]", "", str(v or "0"))
        return int(s) if s.isdigit() else 0

    saida = []
    for r in linhas:
        dia = _data(r.get(c_data, ""), ano)
        if not dia:
            continue
        saida.append({
            "dia": dia, "views": num(r.get(c_vw)),
            "curtidas": num(r.get(cab.get("likes") or cab.get("curtidas"), 0)),
            "comentarios": num(r.get(cab.get("comments") or cab.get("comentarios"), 0)),
            "shares": num(r.get(cab.get("shares") or cab.get("compartilhamentos"), 0)),
            "perfil": num(r.get(cab.get("profile views") or cab.get("visualizacoes do perfil"), 0)),
        })
    return canal, saida, f"colunas: {c_data!r} / {c_vw!r}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pasta")
    p.add_argument("--simular", action="store_true")
    p.add_argument("--relatorio", action="store_true")
    a = p.parse_args()

    try:
        serie = json.loads(SERIE.read_text(encoding="utf-8"))
    except Exception:
        serie = {}

    if a.pasta:
        arqs = sorted(Path(a.pasta).glob("*.zip")) + sorted(Path(a.pasta).glob("*.csv"))
        if not arqs:
            sys.exit(f"nenhum .zip ou .csv em {a.pasta}")
        for f in arqs:
            canal, linhas, aviso = ler(f)
            if not linhas:
                print(f"[!] {f.name}: {aviso}")
                continue
            antes = len(serie.get(canal, {}))
            # ⚠️ ACUMULA por DIA. O historico do TikTok para em 60 dias; o
            # que ja' esta' aqui e' a unica copia do que passou disso.
            por_dia = serie.setdefault(canal, {})
            for l in linhas:
                por_dia[l["dia"]] = {k: v for k, v in l.items() if k != "dia"}
            print(f"{canal:<24} {len(linhas):>3} dias lidos | "
                  f"registro: {antes} -> {len(por_dia)}")
        if not a.simular:
            SERIE.parent.mkdir(parents=True, exist_ok=True)
            SERIE.write_text(json.dumps(serie, ensure_ascii=False, indent=1,
                                        sort_keys=True), encoding="utf-8")
            print(f"\ngravado em {SERIE.name}")
        else:
            print("\nSIMULADO — nada gravado.")

    if a.relatorio or a.pasta:
        print(f"\n{'canal':<24} {'dias':>5} {'views':>9} {'media/dia':>10} "
              f"{'melhor dia':>12}")
        print("-" * 66)
        for canal, dias in sorted(serie.items()):
            vs = [d["views"] for d in dias.values()]
            ativos = [v for v in vs if v > 0]
            melhor = max(dias.items(), key=lambda kv: kv[1]["views"]) if dias else None
            print(f"{canal:<24} {len(dias):>5} {sum(vs):>9} "
                  f"{(sum(ativos)/len(ativos) if ativos else 0):>10.0f} "
                  f"{melhor[0][5:]+' '+str(melhor[1]['views']):>12}")


if __name__ == "__main__":
    main()
