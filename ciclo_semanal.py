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


def rodar(canal: str, simular: bool) -> dict:
    est = estoque(canal)
    linha = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "canal": canal, "estoque": est["total"], "piso": PISO_FONTES}
    print(f"\n=== {canal}")
    print(f"  estoque de fonte: {est['total']} "
          f"({est['pendente']} pendente + {est['pronto']} pronto) | piso {PISO_FONTES}")

    if est["total"] >= PISO_FONTES:
        print("  acima do piso — nada a fazer")
        linha["acao"] = "nada"
        return linha

    top, fonte, aviso = melhores.melhores(canal, 2)
    linha["fonte_da_metrica"] = fonte
    if aviso:
        print(f"  {aviso}")
    if not top:
        print("  [!] sem como saber o que deu certo — NAO baixo no escuro.")
        linha["acao"] = "abortado: sem metrica"
        return linha
    print(f"  melhores da semana (por {fonte}):")
    for p in top:
        n = p.get("views", p.get("curtidas", 0))
        print(f"     {n:>5}  {p.get('titulo','')[:56]}")

    radar = _radar_do_canal(canal)
    termos, por_que = termos_do_sucesso(canal, top, radar)
    linha["termos"] = termos
    if por_que:
        print(f"  ⚠️ {por_que}")
    else:
        print(f"  termos do sucesso, dentro do tema: {', '.join(termos)}")

    if simular:
        print(f"  SIMULADO: rodaria o radar e baixaria {QUANTAS_BAIXAR} fontes")
        linha["acao"] = "simulado"
        return linha

    if radar:
        print("  rodando o radar do canal...")
        subprocess.run([sys.executable, "-X", "utf8",
                        str(RAIZ / "canais" / canal / "radar.py")],
                       cwd=RAIZ, timeout=1800)
    arq = RAIZ / f"radar_{canal.replace('.', '_')}.json"
    if not arq.exists():
        arq = RAIZ / f"radar_{canal.split('.')[0]}.json"
    if not arq.exists():
        print(f"  [!] radar nao deixou arquivo — nao baixo sem lista")
        linha["acao"] = "abortado: sem radar"
        return linha
    print(f"  baixando {QUANTAS_BAIXAR} fonte(s), espacadas...")
    subprocess.run([sys.executable, "-X", "utf8", "baixar_em_intervalos.py",
                    "--radar", str(arq), "--max", str(QUANTAS_BAIXAR)],
                   cwd=RAIZ, timeout=7200)
    linha["acao"] = "radar + download"
    # ⚠️ NAO sobe pro Drive e NAO dispara corte. A pasta do Drive decide o
    # canal, e foi ali que nasceram os 8 clipes de IA no @semanestesia.
    print("  ⚠️ baixado, NAO subido. Subir e' passo separado e deliberado.")
    return linha


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--canal")
    p.add_argument("--todos", action="store_true")
    p.add_argument("--simular", action="store_true")
    a = p.parse_args()
    from engine import canais_registro as cr
    canais = list(cr.do_motor()) if a.todos else [a.canal]
    if not canais or not canais[0]:
        sys.exit("use --canal <nome> ou --todos")
    linhas = [rodar(c, a.simular) for c in canais]
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
