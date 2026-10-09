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
POR_DIA = 5   # 08/10/2026 (dono): era 4 — 5 por dia, >= 3 h entre posts
# ⭐ 08/10/2026: o @achadinho.make (truque.importado) e' canal de CORTE de K-pop
# (4/dia) e recebe so' 1 oferta de beleza por dia, como 5o post.
POR_DIA_CANAL = {"truque.importado": 1}
SO_NICHO = {"truque.importado"}   # nunca recebe sobra de outro nicho
# ⭐ 30/09/2026: @achadinhototal entra na divisao (plano, 3º canal). Um produto
# nunca sai em dois canais — a alternancia abaixo garante.
CANAIS = ("fatura.chora", "achadinhos.instantaneos", "achadinhototal", "truque.importado")

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


def _agora_ml(agora: dict) -> dict[str, dict]:
    """08/10/2026 (dono: "inclui os produtos do mercado livre, de uma atencao
    especial para eles, as pessoas gostam muito"). O preco vem do precos_agora;
    nome, foto e link de afiliado (matt_tool) vem do garimpo-ml."""
    from engine import categorias
    out = {}
    arq = RAIZ / "estado" / "produtos_publicados.jsonl"
    for l in arq.read_text(encoding="utf-8").splitlines():
        try:
            x = json.loads(l)
        except ValueError:
            continue
        pid = str(x.get("id", ""))
        if not pid.startswith("MLB") or x.get("onde") == "video_oferta" or pid not in agora:
            continue
        if not x.get("imagem") or "mercadolivre" not in str(x.get("link", "")):
            continue
        a = agora[pid]
        out[pid] = {**a, "imagens": [x["imagem"]], "nome": _nome_curto(x["nome"]),
                    "link": x["link"], "origem": "ml", "loja": "Mercado Livre",
                    "vendas": x.get("vendas"), "nota": None,
                    "reputacao_nivel": (a.get("reputacao") or {}).get("nivel") or 0,
                    "categoria": categorias.categoria_de("", "", x["nome"])}
    return out


def agora_todos() -> dict[str, dict]:
    """precos_agora (AliExpress/ML) + lojas oficiais da Awin."""
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))
    agora.update(_agora_ml(agora))
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
    if agora.get("origem") == "ml":
        return {"id": pid, "nome": nome, "agora": agora["preco"], "ref": round(ref, 2),
                "dias": len(antes), "queda": round(queda, 3), "nota": None,
                "vendas": agora.get("vendas"), "loja": "Mercado Livre",
                "categoria": agora.get("categoria"), "origem": "ml"}, "ok"
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


# 08/10/2026 (dono): saude, suplementos, multivitaminicos e cabelo "vendem
# muito" e podem ir para QUALQUER achadinho; ML tem "atencao especial".
DESTAQUE_CATS = {"saude_farmacia", "suplementos", "cabelo"}
ACHADINHOS = ("fatura.chora", "achadinhos.instantaneos", "achadinhototal")
DESTAQUE_POR_CANAL = 2      # de 5 vagas/dia, 2 sao de ML ou saude
REPUTACAO_ML_MIN = 4


_GENERICAS = {"de", "da", "do", "com", "para", "e", "em", "sem", "kit", "suplemento", "alimentar",
              "mineral", "sabor", "gotas", "suspensao", "oral", "ml", "g", "unidades", "capsulas",
              "masculina", "masculino", "feminina", "feminino", "unissex", "uso", "branco", "preto"}


def _palavras(nome: str) -> set[str]:
    import unicodedata
    t = "".join(c for c in unicodedata.normalize("NFD", nome.lower()) if unicodedata.category(c) != "Mn")
    return {w for w in re.findall(r"[a-z0-9]+", t) if len(w) > 2 and w not in _GENERICAS}


def parecido(a: str, b: str) -> bool:
    """08/10/2026: "Folifer Gotas" e "Folifer Suspensao" sao o mesmo produto pro
    publico. Mesma MARCA/nucleo (>= 60% das palavras significativas do menor)."""
    pa, pb = _palavras(a), _palavras(b)
    if not pa or not pb:
        return False
    return len(pa & pb) / min(len(pa), len(pb)) >= 0.6 or (len(pa & pb) >= 1 and min(len(pa), len(pb)) == 1)


def _destaque(pid: str, a: dict) -> bool:
    if a.get("origem") == "ml":
        return (a.get("reputacao_nivel") or 0) >= REPUTACAO_ML_MIN
    return a.get("categoria") in DESTAQUE_CATS


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
    # ⛔ 08/10/2026: o MESMO produto volta com outro id (variante de tamanho/cor na
    # Awin): "Regata Nike Dri-FIT Miler" saiu 2x no mesmo dia no @achadinhototal.
    # Nome igual ao de uma oferta da janela, ou ja' escolhido hoje, fica de fora.
    def _chave(n: str) -> str:
        return re.sub(r"[^a-z0-9]", "", (n or "").lower())[:40]
    ja_nomes = {_chave(nomes.get(i, "")) for i in ja if nomes.get(i)}
    boas = []
    for pid, a in agora.items():
        if pid in ja or pid not in nomes or not (pid.isdigit() or pid.startswith(("awin:", "MLB"))):
            continue
        if _chave(nomes[pid]) in ja_nomes:
            continue
        o, m = avaliar(pid, a, serie.get(pid, []), nomes[pid])
        if o:
            boas.append(o)
        elif _destaque(pid, a) and (m.startswith("serie curta") or m.startswith("queda")):
            # 08/10/2026: ML e saude/suplemento/cabelo sem queda PROVADA entram
            # como ACHADO: o video mostra so' o preco de hoje (provada=False no
            # video_oferta) -- nunca uma queda inventada.
            boas.append({"id": pid, "nome": nomes[pid], "agora": a["preco"], "ref": a["preco"],
                         "dias": 0, "queda": 0.0, "nota": a.get("nota"), "vendas": a.get("vendas"),
                         "loja": a.get("loja"), "categoria": a.get("categoria"),
                         "origem": a.get("origem"), "sem_queda": True})
    video = _com_video()
    for o in boas:
        o["tem_video"] = o["id"] in video
    # ⛔ 30/09/2026 (dono): a ordem e' SEMPRE a melhor oferta (maior queda
    # provada). Ter video NAO passa ninguem na frente — o trabalho e' conseguir
    # o video pra oferta escolhida, nao escolher a oferta pelo video.
    boas.sort(key=lambda o: o["queda"], reverse=True)
    unicas, vistos = [], set()
    for o in boas:              # entre variantes de mesmo nome, fica a de maior queda
        k = _chave(o["nome"])
        if k not in vistos:
            vistos.add(k)
            unicas.append(o)
    return unicas


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
    "truque.importado": ("truque.importado",),   # beleza (Awin pela categoria) + garimpo de make
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


def _foto_viva(url: str) -> bool:
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-2047"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status in (200, 206)
    except Exception:
        return False


def _com_foto_viva(boas: list[dict]) -> list[dict]:
    """⛔ 09/10/2026: 3 produtos da Drogal (Awin) passaram em todas as guardas
    com a foto do feed MORTA (404/403); o video falhava no gerar e a vaga do
    canal ficava vazia (truque.importado saiu com 1 de 4). Produto Awin com a
    foto principal fora do ar nao entra na escolha: a vaga vai para o proximo."""
    from concurrent.futures import ThreadPoolExecutor
    agora = agora_todos()
    foto = {o["id"]: (o.get("imagens") or agora.get(o["id"], {}).get("imagens") or [None])[0]
            for o in boas if str(o["id"]).startswith("awin:")}
    awin = [o for o in boas if foto.get(o["id"])]
    with ThreadPoolExecutor(16) as ex:
        vivas = dict(zip((o["id"] for o in awin), ex.map(lambda o: _foto_viva(foto[o["id"]]), awin)))
    mortas = [o for o in awin if not vivas[o["id"]]]
    for o in mortas[:10]:
        print(f"  [-] foto fora do ar, fora da escolha: {o['id']} {o['nome'][:50]}")
    if len(mortas) > 10:
        print(f"  [-] ... e mais {len(mortas) - 10} com foto fora do ar")
    return [o for o in boas if vivas.get(o["id"], True)]


def do_dia(dia: date | None = None) -> dict[str, list[dict]]:
    """{canal: [ofertas]} — POR_DIA por canal, por nicho, maiores quedas primeiro."""
    boas = candidatas(dia)          # ja' vem da maior queda para a menor
    boas = _com_foto_viva(boas)
    origem = _origem()
    saida: dict[str, list[dict]] = {c: [] for c in CANAIS}

    class _Usados(set):
        """ids escolhidos hoje + nomes, para barrar PARECIDO em outro canal."""
        nomes: list[str] = []
        def add(self, pid):            # noqa: D401
            super().add(pid)
            o = por_id.get(pid)
            if o:
                self.nomes.append(o["nome"])
        def __contains__(self, pid):
            if set.__contains__(self, pid):
                return True
            o = por_id.get(pid)
            return bool(o) and any(parecido(o["nome"], n) for n in self.nomes)
    por_id = {o["id"]: o for o in boas}
    usados = _Usados()
    usados.nomes = []
    # 0a passada (08/10/2026): DESTAQUE, nunca o mesmo produto em dois canais.
    # Cada achadinho: 1 vaga de MERCADO LIVRE (no nicho do canal quando houver)
    # + 1 de SAUDE/SUPLEMENTO/CABELO. Queda provada sempre na frente do achado.
    # O @achadinho.make pode pegar ML de BELEZA (e so' beleza).
    from engine import categorias as _cat
    def _ordem(o):
        return (not o.get("sem_queda") and o["queda"] > 0, o["queda"], o.get("vendas") or 0)
    ml = sorted((o for o in boas if o.get("origem") == "ml"), key=_ordem, reverse=True)
    # dono: "suplementos, multivitaminicos, cabelo" na frente da farmacia generica
    saude = sorted((o for o in boas if o.get("origem") != "ml"
                    and o.get("categoria") in DESTAQUE_CATS),
                   key=lambda o: (o.get("categoria") in ("suplementos", "cabelo")
                                  or bool(re.search(r"vitamin|suplement|cabelo|capilar|shampoo|whey|creatina|col[aá]geno",
                                                    o["nome"].lower())),) + _ordem(o), reverse=True)

    def _pegar(lista, canal, so_nicho=False):
        livres = [o for o in lista if o["id"] not in usados]
        no_nicho = [o for o in livres if _cat.canal_de(o.get("categoria") or "outros") == canal]
        if so_nicho:
            return no_nicho[0] if no_nicho else None
        fora_make = [o for o in livres if o.get("categoria") != "beleza"]
        return (no_nicho or fora_make or [None])[0]

    if "truque.importado" in CANAIS:
        o = _pegar(ml, "truque.importado", so_nicho=True)
        if o:
            saida["truque.importado"].append(o)
            usados.add(o["id"])
    for _ in range(max(1, DESTAQUE_POR_CANAL // 2)):
        for canal in ACHADINHOS:
            for lista in (ml, saude):
                o = _pegar(lista, canal) or _pegar(saude if lista is ml else ml, canal)
                if o:
                    saida[canal].append(o)
                    usados.add(o["id"])
    boas = [o for o in boas if not o.get("sem_queda")]   # achado sem queda so' no destaque
    # 1a passada: cada canal pega o melhor DO SEU nicho (os de nicho fechado primeiro)
    for canal in sorted(CANAIS, key=lambda c: NICHO.get(c) is None):
        aceita = NICHO.get(canal)
        for o in boas:
            if len(saida[canal]) >= POR_DIA_CANAL.get(canal, POR_DIA):
                break
            if o["id"] in usados:
                continue
            if o.get("categoria"):
                # ⭐ 04/10/2026: produto Awin vai pelo canal da CATEGORIA
                # (engine/categorias.py), nao pela origem do garimpo.
                from engine import categorias
                livre = o["categoria"] in DESTAQUE_CATS and canal in ACHADINHOS
                if categorias.canal_de(o["categoria"]) != canal and not livre:
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
        # o @achadinho.make so' recebe beleza (1a passada) -- sobra de eletronico
        # nao entra num canal de maquiagem
        curtos = [c for c in CANAIS if c not in SO_NICHO
                  and len(saida[c]) < POR_DIA_CANAL.get(c, POR_DIA)]
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
