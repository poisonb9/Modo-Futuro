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
QUEDA_MIN = 0.10   # 04/10/2026 (dono): era 0.15 — catalogo esgotado, 0 ofertas novas. # 30/09/2026 (dono): era 0.25 — so' 1 oferta nova passava; queda continua REAL e medida
DIAS_MIN = 7
NOTA_MIN = 4.7
VENDAS_MIN = 1000
JANELA_DIAS = 10   # 04/10/2026 (dono): era 21
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


# ⭐ 04/10/2026 (dono: "comecar, divisao, liberar, criar categorias"): as lojas
# da Awin entram nas ofertas. O feed so' grava ponto na serie quando o preco
# MUDA (engine/awin.py, guardar_catalogo), entao a serie de um id `awin:` e'
# esticada dia a dia ate' ontem (`_diaria`) antes da mediana — sem isso um
# tenis com preco parado ha' 18 dias teria "1 dia" de serie.
# ⛔ O AliExpress pela Awin fica de fora: o mesmo produto ja' vem pelo garimpo
# direto, com nota e vendas lidas, e la' a regra de marca continua valendo.
AWIN_FORA = {"Aliexpress BR & LATAM"}
SEM_FOTO = "noimage"


def _agora_awin() -> dict[str, dict]:
    """{"awin:<id>": registro no formato do precos_agora} das lojas oficiais."""
    from engine import categorias
    try:
        inst = json.load(open(RAIZ / "estado" / "awin_catalogo.json", encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for p in inst.get("produtos", []):
        if p["loja"] in AWIN_FORA or not p.get("imagem") or SEM_FOTO in p["imagem"]:
            continue
        cat = categorias.categoria_de(p["loja"], p.get("categoria", ""), p.get("nome", ""))
        out["awin:" + str(p["id"])] = {
            "quando": inst["quando"], "preco": p["preco"], "imagens": [p["imagem"]],
            "nota": None, "vendas": None, "link": p["link"], "loja": p["loja"],
            "categoria": cat, "nome": _nome_curto(p["nome"]), "origem": "awin"}
    return out


def _nome_curto(nome: str, limite: int = 48) -> str:
    nome = re.sub(r"\s+", " ", nome).strip()
    if len(nome) <= limite:
        return nome
    return nome[:limite].rsplit(" ", 1)[0].rstrip(" ,;-–")


def agora_todos() -> dict[str, dict]:
    """precos_agora (AliExpress/ML) + lojas oficiais da Awin."""
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))
    agora.update(_agora_awin())
    return agora


def _diaria(serie: list, hoje: str) -> list[float]:
    """Pontos de mudanca -> um preco por dia, do 1o ponto ate' ontem."""
    from datetime import date as _d
    pts = sorted((q[:10], p) for q, p in serie if q[:10] < hoje)
    if not pts:
        return []
    out, i, preco = [], 0, pts[0][1]
    dia, fim = _d.fromisoformat(pts[0][0]), _d.fromisoformat(hoje)
    while dia < fim:
        while i < len(pts) and pts[i][0] <= dia.isoformat():
            preco = pts[i][1]
            i += 1
        out.append(preco)
        dia += timedelta(days=1)
    return out


def antes_de(pid: str, serie: list, hoje: str) -> list[float]:
    """Os precos dos ultimos 30 dias antes de hoje, como a mediana espera."""
    if str(pid).startswith("awin:"):
        return _diaria(serie, hoje)[-30:]
    return [p for q, p in sorted(serie) if q < hoje][-30:]


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


# ⛔ BLOQUEADOS pelo dono (nunca viram oferta). Motivo e data em cada um.
BLOQUEADOS = {
    # 30/09/2026: "suporte dobravel de aluminio para laptop", mas as fotos do
    # anuncio mostram um TRIPE DE CELULAR — produto diferente do anunciado.
    "1005011940143389",
}


def avaliar(pid: str, agora: dict, serie: list, nome: str) -> tuple[dict | None, str]:
    """(oferta, motivo). `oferta` None = fica de fora, e o motivo diz por que."""
    if str(pid) in BLOQUEADOS:
        return None, "bloqueado pelo dono"
    hoje = agora["quando"][:10]
    antes = antes_de(pid, serie, hoje)
    if len(antes) < DIAS_MIN:
        return None, f"serie curta ({len(antes)} dias)"
    ref = statistics.median(antes)
    queda = 1 - agora["preco"] / ref
    if queda < QUEDA_MIN:
        return None, f"queda {queda:.0%}"
    if agora.get("origem") == "awin":
        # ⭐ 04/10/2026 (dono: "liberar"): loja OFICIAL, sem nota/vendas no
        # feed e sem risco de replica — a regra de marca nao se aplica.
        return {"id": pid, "nome": nome, "agora": agora["preco"], "ref": round(ref, 2),
                "dias": len(antes), "queda": round(queda, 3), "nota": None, "vendas": None,
                "loja": agora["loja"], "categoria": agora["categoria"]}, "ok"
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
    agora = agora_todos()
    nomes = json.load(open(RAIZ / "estado" / "nomes_curtos.json", encoding="utf-8"))
    nomes.update({pid: a["nome"] for pid, a in agora.items() if a.get("origem") == "awin"})
    serie = _serie()
    corte = (dia - timedelta(days=JANELA_DIAS)).isoformat()
    ja = {f["id"] for f in _feitas() if f.get("dia", "") >= corte}
    boas = []
    for pid, a in agora.items():
        if pid in ja or pid not in nomes or not (pid.isdigit() or pid.startswith("awin:")):
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


# ⭐ 30/09/2026 (pendente 4 do handoff): DIVISAO POR NICHO. O nicho do produto
# e' o canal em que o GARIMPO o achou (estado/produtos_publicados.jsonl, linhas
# que nao sao `video_oferta`). Pago Menos = eletronico; Instantaneos = casa /
# irritacao resolvida; Achadinho Total = o resto. Dentro do nicho, SEMPRE a
# maior queda primeiro; nicho sem oferta completa com a melhor que sobrou —
# nicho nunca passa uma oferta pior na frente de uma melhor do mesmo canal.
NICHO = {
    "fatura.chora": ("fatura.chora", "modofuturo"),
    "achadinhos.instantaneos": ("achadinhos.instantaneos", "cozinha.importada",
                                "varredura.jardim", "varredura.ferramentas"),
    "achadinhototal": None,   # None = qualquer origem
}


def _origem() -> dict[str, str]:
    out: dict[str, str] = {}
    arq = RAIZ / "estado" / "produtos_publicados.jsonl"
    if not arq.exists():
        return out
    for l in arq.read_text(encoding="utf-8").splitlines():
        try:
            x = json.loads(l)
        except ValueError:
            continue
        if x.get("id") and x.get("onde") != "video_oferta" and x.get("canal"):
            out.setdefault(str(x["id"]), x["canal"])
    return out


def do_dia(dia: date | None = None) -> dict[str, list[dict]]:
    """{canal: [ofertas]} — POR_DIA por canal, por nicho, maiores quedas primeiro."""
    boas = candidatas(dia)          # ja' vem da maior queda para a menor
    origem = _origem()
    saida: dict[str, list[dict]] = {c: [] for c in CANAIS}
    usados: set[str] = set()
    # 1a passada: cada canal pega o melhor DO SEU nicho (os de nicho fechado primeiro)
    for canal in sorted(CANAIS, key=lambda c: NICHO.get(c) is None):
        aceita = NICHO.get(canal)
        for o in boas:
            if len(saida[canal]) >= POR_DIA:
                break
            if o["id"] in usados:
                continue
            if o.get("categoria"):
                # ⭐ 04/10/2026: produto Awin vai pelo canal da CATEGORIA
                # (engine/categorias.py), nao pela origem do garimpo.
                from engine import categorias
                if categorias.canal_de(o["categoria"]) != canal:
                    continue
                saida[canal].append(o)
                usados.add(o["id"])
                continue
            if aceita and origem.get(str(o["id"])) not in aceita:
                continue
            if aceita is None and any(origem.get(str(o["id"])) in (n or ()) for n in NICHO.values()):
                continue            # o Total nao rouba produto de nicho de outro canal
            saida[canal].append(o)
            usados.add(o["id"])
    # 2a passada: sobra vai pra quem ficou curto, sempre a maior queda restante
    for o in boas:
        if o["id"] in usados:
            continue
        curtos = [c for c in CANAIS if len(saida[c]) < POR_DIA]
        if not curtos:
            break
        saida[min(curtos, key=lambda c: len(saida[c]))].append(o)
        usados.add(o["id"])
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
