# -*- coding: utf-8 -*-
"""As ofertas do dia dos canais de achado (Pago Menos e achadinhos.instantaneos).

    python -X utf8 -m engine.ofertas            mostra a escolha de hoje (nada grava)

⭐ 29/09/2026 (dono): "sempre confianca, sempre". Um produto so' vira video se
passar TODAS as guardas abaixo — e na duvida, fica de fora:

  1. QUEDA REAL: preco de agora >= QUEDA_MIN abaixo da MEDIANA da nossa serie
     (>= DIAS_MIN dias). Nunca o "de" do vendedor.
  2. LOJA BOA: nota >= NOTA_MIN e vendas >= VENDAS_MIN (lidos pela API em
     `engine/precos.py`). Produto sem nota lida ainda NAO entra.
  3. SEM MARCA FAMOSA: no AliExpress, marca famosa no titulo quase sempre e'
     replica. Quem compra replica achando que e' original nao volta — e
     denuncia.
  4. SEM REPETIR: o mesmo produto nao volta em JANELA_DIAS dias, e nunca sai
     nos dois canais.
"""
from __future__ import annotations

import json
import re
import statistics
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FEITAS = RAIZ / "estado" / "ofertas_feitas.jsonl"
QUEDA_MIN = 0.25
DIAS_MIN = 7
NOTA_MIN = 4.7
VENDAS_MIN = 1000
JANELA_DIAS = 21
POR_DIA = 4
# ⭐ 30/09/2026: @achadinhototal entra na divisao (plano, 3º canal). Um produto
# nunca sai em dois canais — a alternancia abaixo garante.
CANAIS = ("fatura.chora", "achadinhos.instantaneos", "achadinhototal")

# minusculo, palavra inteira. Lista curta de proposito: e' o que mais aparece
# falsificado no Ali; cresce quando aparecer um caso.
MARCAS = ("apple", "iphone original", "airpods", "samsung", "nike", "adidas", "puma",
          "rare beauty", "dior", "chanel", "gucci", "louis vuitton", "prada",
          "jbl", "sony", "bose", "beats", "dyson", "rolex", "ray-ban", "stanley",
          "lego", "disney", "marvel", "pokemon", "hello kitty", "sephora", "mac cosmetics")


def _serie() -> dict[str, list[tuple[str, float]]]:
    s: dict[str, list] = {}
    for l in open(RAIZ / "estado" / "precos_vistos.jsonl", encoding="utf-8"):
        if l.strip():
            x = json.loads(l)
            s.setdefault(str(x["id"]), []).append((x["quando"], float(x["preco"])))
    return s


def _feitas() -> list[dict]:
    if not FEITAS.exists():
        return []
    return [json.loads(l) for l in FEITAS.read_text(encoding="utf-8").splitlines() if l.strip()]


def marca_suspeita(nome: str) -> str | None:
    n = nome.lower()
    for m in MARCAS:
        if re.search(r"(?<![a-z])" + re.escape(m) + r"(?![a-z])", n):
            return m
    return None


def avaliar(pid: str, agora: dict, serie: list, nome: str) -> tuple[dict | None, str]:
    """(oferta, motivo). `oferta` None = fica de fora, e o motivo diz por que."""
    hoje = agora["quando"][:10]
    antes = [p for q, p in sorted(serie) if q < hoje][-30:]
    if len(antes) < DIAS_MIN:
        return None, f"serie curta ({len(antes)} dias)"
    ref = statistics.median(antes)
    queda = 1 - agora["preco"] / ref
    if queda < QUEDA_MIN:
        return None, f"queda {queda:.0%}"
    if not agora.get("nota"):
        return None, "sem nota lida"
    if agora["nota"] < NOTA_MIN:
        return None, f"nota {agora['nota']}"
    if (agora.get("vendas") or 0) < VENDAS_MIN:
        return None, f"poucas vendas ({agora.get('vendas') or 0})"
    m = marca_suspeita(nome)
    if m:
        return None, f"marca famosa ({m}) — risco de replica"
    return {"id": pid, "nome": nome, "agora": agora["preco"], "ref": round(ref, 2),
            "dias": len(antes), "queda": round(queda, 3), "nota": agora["nota"],
            "vendas": agora["vendas"]}, "ok"


def _com_video() -> set[str]:
    """Produtos com video pra demonstracao: oficial do vendedor OU trecho do
    YouTube aprovado pelo Gemini (estado/demos_drive.json, item 16)."""
    ids = set()
    try:
        agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))
        ids |= {pid for pid, a in agora.items() if a.get("video")}
    except (OSError, ValueError):
        pass
    try:
        ids |= set(json.load(open(RAIZ / "estado" / "demos_drive.json", encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return ids


def candidatas(dia: date | None = None) -> list[dict]:
    """TODAS as ofertas que passam nas guardas hoje, na ordem de preferencia.

    Ordem: maior queda provada. `tem_video` e' so' informacao (o demo_local
    usa pra saber pra quem ainda falta video).
    """
    dia = dia or date.today()
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))
    nomes = json.load(open(RAIZ / "estado" / "nomes_curtos.json", encoding="utf-8"))
    serie = _serie()
    corte = (dia - timedelta(days=JANELA_DIAS)).isoformat()
    ja = {f["id"] for f in _feitas() if f.get("dia", "") >= corte}
    boas = []
    for pid, a in agora.items():
        if pid in ja or pid not in nomes or not pid.isdigit():
            continue
        o, _ = avaliar(pid, a, serie.get(pid, []), nomes[pid])
        if o:
            boas.append(o)
    video = _com_video()
    for o in boas:
        o["tem_video"] = o["id"] in video
    # ⛔ 30/09/2026 (dono): a ordem e' SEMPRE a melhor oferta (maior queda
    # provada). Ter video NAO passa ninguem na frente — o trabalho e' conseguir
    # o video pra oferta escolhida, nao escolher a oferta pelo video.
    boas.sort(key=lambda o: o["queda"], reverse=True)
    return boas


def do_dia(dia: date | None = None) -> dict[str, list[dict]]:
    """{canal: [ofertas]} — POR_DIA por canal, maiores quedas primeiro, alternando."""
    boas = candidatas(dia)
    saida: dict[str, list[dict]] = {c: [] for c in CANAIS}
    for i, o in enumerate(boas[:POR_DIA * len(CANAIS)]):
        saida[CANAIS[i % len(CANAIS)]].append(o)
    return saida


def registrar(canal: str, oferta: dict, dia: date | None = None) -> None:
    with open(FEITAS, "a", encoding="utf-8") as f:
        f.write(json.dumps({"dia": (dia or date.today()).isoformat(), "canal": canal,
                            "id": oferta["id"], "agora": oferta["agora"],
                            "numero": oferta.get("numero"),
                            "comentario": oferta.get("comentario", "")},
                           ensure_ascii=False) + "\n")


if __name__ == "__main__":
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))
    nomes = json.load(open(RAIZ / "estado" / "nomes_curtos.json", encoding="utf-8"))
    serie = _serie()
    motivos: dict[str, int] = {}
    for pid, a in agora.items():
        if pid in nomes:
            _, m = avaliar(pid, a, serie.get(pid, []), nomes[pid])
            m = re.sub(r"[ (].*", "", m) if not m.startswith(("sem", "serie", "poucas")) else m.split(" (")[0]
            motivos[m] = motivos.get(m, 0) + 1
    print("por que ficaram de fora:", dict(sorted(motivos.items(), key=lambda x: -x[1])))
    for c, os_ in do_dia().items():
        print(f"\n{c}:")
        for o in os_:
            print(f"  -{o['queda']:.0%}  R$ {o['agora']:.2f} (mediana {o['ref']:.2f}, {o['dias']}d)  "
                  f"nota {o['nota']}  {o['vendas']} vendas  {o['nome']}")
