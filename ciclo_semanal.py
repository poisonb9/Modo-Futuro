# -*- coding: utf-8 -*-
"""O canal esta' ficando sem fonte? Entao busca mais, no rumo do que deu certo.

Ordem do Bryan em 08/09/2026:

    "Quando um canal comecar a ficar sem videos para cortar voce vai rodar um
     radar em cima dos 2 videos que mais viralizaram na semana em
     visualizacoes, ai' voce vai baixar 5 novas fontes e por pra cortar. Vai
     testar isso sucessivamente por 1 mes."

E a trava editorial, no mesmo dia: **nunca fuja do tema principal do canal.**

## O QUE FALTAVA, E ERA SO' ISTO

Baixar espacado, radar por canal, upload pro Drive e registro mestre ja'
existiam. O que nao existia era o GATILHO: o `repor_fila` olha a fila do
BUFFER (clipe pronto pra postar), e nunca o ESTOQUE DE FONTE (bruto pra
cortar). Um canal podia estar com 10 posts agendados e zero material pra
cortar depois — que e' exatamente como a cozinha chegou a seis dias em zero.

    fonte (bruto)  ->  corte  ->  clipe  ->  fila do Buffer  ->  post
    ^^^^^^^^^^^^^                            ^^^^^^^^^^^^^^
    este script                              o repor_fila

## COMO O TEMA FICA TRAVADO

Os termos de busca saem dos titulos dos 2 melhores da semana, mas **so'
passam os que casam com a lista TEMA do radar daquele canal**. Um titulo
campeao que fale de algo fora do tema nao arrasta o canal pra la'.

⚠️ Isso pode devolver ZERO termos — e ai' o ciclo usa so' as buscas fixas do
radar, em vez de inventar. Buscar no rumo do sucesso e' um bonus; nao fugir
do tema e' a regra.

Uso:
    python ciclo_semanal.py --canal atefalhar --simular
    python ciclo_semanal.py --todos --simular
    python ciclo_semanal.py --canal atefalhar
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from engine import melhores  # noqa: E402

FILA = RAIZ / "fila_cortes.json"
DIARIO = RAIZ / "estado" / "ciclo_semanal.jsonl"

# Abaixo disto o canal "esta' ficando sem video pra cortar".
#
# ⚠️ O NUMERO E' ESCOLHIDO, NAO MEDIDO. Tres fontes rendem ~6 a 15 clipes, o
# que cobre de 1,5 a 4 dias de postagem a 4/dia. E' folga pra uma rodada de
# radar + download acontecer sem o canal secar no meio. Se um canal secar com
# o piso em 3, o numero e' que esta' errado.
PISO_FONTES = 3

QUANTAS_BAIXAR = 5


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def estoque(canal: str) -> dict:
    """Quantas FONTES esse canal ainda tem pra cortar."""
    try:
        d = json.loads(FILA.read_text(encoding="utf-8"))
    except Exception:
        return {"pendente": 0, "pronto": 0, "total": 0}
    itens = d.get("itens", d if isinstance(d, list) else [])
    meus = [i for i in itens if (i.get("canal") or "").lower() == canal.lower()]
    # ⚠️ `pronto` conta: e' fonte ja' cortada esperando vaga, ou seja,
    # material que ainda vai render post. `desistido` e `sem_fonte` NAO
    # contam — sao exatamente o oposto de estoque.
    pend = sum(1 for i in meus if i.get("estado") == "pendente")
    pron = sum(1 for i in meus if i.get("estado") == "pronto")
    return {"pendente": pend, "pronto": pron, "total": pend + pron}


def _radar_do_canal(canal: str):
    """Importa o radar.py daquele canal, se ele existir."""
    p = RAIZ / "canais" / canal / "radar.py"
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"radar_{canal}", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        return None
    return mod


def termos_do_sucesso(canal: str, top: list[dict], radar) -> tuple[list, str]:
    """Palavras dos titulos campeoes que TAMBEM estao no tema do canal.

    ⚠️ A INTERSECAO E' A TRAVA. Ordem do Bryan: "nunca fuja do tema principal
    do canal". Um titulo campeao que fale de outra coisa nao pode arrastar o
    radar pra fora — entao so' passa o termo que ja' era do tema.
    """
    tema = [t.lower() for t in getattr(radar, "TEMA", [])] if radar else []
    if not tema:
        return [], "o radar deste canal nao declara TEMA — nao enviesei nada"
    achados = []
    for p in top:
        for t in tema:
            if t in _norm(p.get("titulo", "")) and t not in achados:
                achados.append(t)
    if not achados:
        return [], ("nenhum termo dos campeoes casa com o TEMA do canal — "
                    "usei so' as buscas fixas do radar, sem enviesar")
    return achados, ""


def rodar(canal: str, simular: bool, est_drive: dict | None = None,
          usados: set | None = None) -> dict:
    """⭐ 08/10/2026 (dono: "faz o ciclo semanal subir sozinho"): o ciclo agora
    entra no MESMO trilho do abastecer_loop, em vez de baixar por conta propria
    para trabalho/brutos (onde 17 brutos ficaram esquecidos sem nunca virar
    estoque, e o radar usado no atefalhar era o de ACADEMIA):

      campeoes do canal -> buscas extras (engine/buscas_do_sucesso)
        -> radar CERTO do canal (abastecer_loop.CANAIS) com as extras
        -> Gemini assiste ANTES de baixar (mesmo criterio, reprovados lembrados)
        -> JDownloader -> abastecer_loop.subir_prontos sobe para RAW/<PASTA do
           canal> com conferencia de bytes e apaga do PC.

    A trava antiga ("a pasta do Drive decide o canal") segue respeitada: so'
    sobe o que o Gemini aprovou PARA AQUELE TEMA, na pasta daquele canal.
    """
    import abastecer_loop as al
    from engine import buscas_do_sucesso as bs
    linha = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "canal": canal, "piso": al.PISO}
    print(f"\n=== {canal}")
    estado = al.ler_estado()
    na_fila = sum(1 for p in estado["pendentes"].values() if p["canal"] == canal)
    n = (est_drive or {}).get(canal, 0)
    linha["estoque"] = n
    print(f"  estoque no Drive: {n} + {na_fila} baixando | piso {al.PISO}")
    if n + na_fila >= al.PISO:
        print("  acima do piso — nada a fazer")
        linha["acao"] = "nada"
        return linha

    r = bs.gerar(canal, gravar=not simular)
    linha["buscas_extras"] = r.get("buscas", [])
    if r.get("erro"):
        print(f"  ⚠️ buscas extras: {r['erro']} — uso so' as buscas fixas do radar")
    else:
        print("  campeoes do mes: " + " | ".join(t[:40] for t in r["campeoes"][:3]))
        print("  buscas extras: " + "; ".join(r["buscas"]))
    if simular:
        print("  SIMULADO: rodaria radar + Gemini e mandaria os aprovados ao JD")
        linha["acao"] = "simulado"
        return linha

    itens = al.escolher(canal, al.CANAIS[canal], usados if usados is not None else set())
    if not itens:
        print("  nenhum candidato passou no criterio — nao baixo nada fraco")
        linha["acao"] = "radar + gemini: nada aprovado"
        return linha
    if not al.mandar_jd(canal, itens):
        print("  [!] JDownloader nao respondeu — o vigia_saude reinicia e reenvia")
        linha["acao"] = "abortado: JD mudo"
        return linha
    # ⚠️ relê o estado JA' na hora de gravar: o abastecer_loop pode ter escrito
    # no meio (janela curta; pendente perdido o vigia_saude detecta e reenvia).
    estado = al.ler_estado()
    for i in itens:
        estado["pendentes"][i["id"]] = {"canal": canal, "titulo": i["titulo"], "url": i["url"],
                                        "nota": i["gemini"].get("nota"), "origem": "ciclo_semanal",
                                        "quando": datetime.now().isoformat(timespec="minutes")}
        if usados is not None:
            usados.add(i["id"])
    al.gravar_estado(estado)
    al.log(f"⬇️ {canal}: {len(itens)} no JDownloader (ciclo_semanal, buscas do sucesso)")
    linha["acao"] = f"{len(itens)} aprovados no JD — sobem sozinhos ao RAW"
    linha["aprovados"] = [i["titulo"][:80] for i in itens]
    return linha


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--canal")
    p.add_argument("--todos", action="store_true")
    p.add_argument("--simular", action="store_true")
    a = p.parse_args()
    import abastecer_loop as al
    canais = list(al.CANAIS) if a.todos else [a.canal]
    if not canais or not canais[0]:
        sys.exit("use --canal <nome> ou --todos")
    est_drive, ids_drive = al.estoque_drive()
    usados = al.ids_usados(al.ler_estado()) | ids_drive
    linhas = [rodar(c, a.simular, est_drive, usados) for c in canais]
    if not a.simular:
        # O diario e' o que torna "testar por 1 mes" uma medicao, e nao uma
        # impressao. Uma linha por rodada, com o estoque que a disparou.
        DIARIO.parent.mkdir(parents=True, exist_ok=True)
        with open(DIARIO, "a", encoding="utf-8") as f:
            for l in linhas:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")
    print(f"\n{sum(1 for l in linhas if l.get('acao','nada')!='nada')} "
          f"canal(is) precisaram de reposicao de fonte.")


if __name__ == "__main__":
    main()
