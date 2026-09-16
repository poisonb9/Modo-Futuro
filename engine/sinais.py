# -*- coding: utf-8 -*-
"""Sinais de preco: o que a SERIE diz hoje que vale um post ou um rebaixo.

## POR QUE EXISTE

Bryan, 16/09/2026, sobre "o que fazer quando o preco sobe": *"subida depois
de queda = fim de promocao -> ultima chance; o produto que voltou ao minimo
vira 'voltou a cair', que e' gatilho de compra de verdade"* — "excelente
ideia, vamos implementar".

## OS SINAIS (todos contra a NOSSA serie, nunca o de/por da loja)

    voltou_a_cair    hoje caiu (>= 2% vs ontem) e esta' no menor preco que ja'
                     vimos (ou abaixo) DEPOIS de ter subido — o comprador que
                     esperou foi recompensado
    novo_minimo      hoje caiu e e' o menor preco da historia do produto, sem
                     ter subido antes (primeira queda funda)
    ultima_chance    hoje SUBIU (>= 2% vs ontem) mas ainda esta' >= 5% abaixo
                     do maior que vimos — a promocao esta' acabando
    subiu            subiu e ja' esta' perto do maior: sem post; so' rebaixa
                     no ranking (o site nao anuncia o que ficou caro)

⚠️ "ontem" e' o ultimo dia com leitura ANTES de hoje; se o produto nao tem
leitura de hoje, nao ha' sinal — sinal e' sobre o que aconteceu HOJE.

⚠️ O canal pode REPOSTAR um produto por sinal (o registro do canal barra
duplicata por id, e aqui a duplicata e' legitima: e' outro fato). O registro
proprio `estado/sinais_postados.json` guarda id+dia+sinal, entao o mesmo
sinal do mesmo produto no mesmo dia sai UMA vez.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SERIE = RAIZ / "estado" / "precos_vistos.jsonl"
AGORA = RAIZ / "estado" / "precos_agora.json"
CATALOGO = RAIZ / "estado" / "produtos_publicados.jsonl"
POSTADOS = RAIZ / "estado" / "sinais_postados.json"

PISO_MUDANCA = 0.02      # abaixo disso e' cambio/arredondamento
LONGE_DO_MAIOR = 0.05    # "ultima chance" so' se ainda >= 5% abaixo do maior


def por_dia() -> dict:
    """{id: {dia: MENOR preco do dia}} — a mesma leitura da pagina."""
    saida: dict = {}
    if not SERIE.exists():
        return saida
    for linha in SERIE.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        i, q = d.get("id"), (d.get("quando") or "")[:10]
        try:
            v = float(d.get("preco") or 0)
        except (TypeError, ValueError):
            continue
        if not i or not q or v <= 0:
            continue
        dias = saida.setdefault(str(i), {})
        dias[q] = min(dias[q], v) if q in dias else v
    return saida


def _agora() -> dict:
    if not AGORA.exists():
        return {}
    try:
        return json.loads(AGORA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def sinal_de(dias: dict, hoje_preco: float | None = None,
             hoje: str | None = None) -> dict | None:
    """O sinal de um produto a partir da serie dele, ou None."""
    hoje = hoje or date.today().isoformat()
    if hoje_preco is None:
        hoje_preco = dias.get(hoje)
    if not hoje_preco:
        return None
    antes = {q: v for q, v in dias.items() if q < hoje}
    if not antes:
        return None
    ontem = antes[max(antes)]
    menor_antes, maior_antes = min(antes.values()), max(antes.values())
    caiu = hoje_preco <= ontem * (1 - PISO_MUDANCA)
    subiu = hoje_preco >= ontem * (1 + PISO_MUDANCA)
    ja_subiu_antes = maior_antes > menor_antes * (1 + PISO_MUDANCA) and \
        max(antes, key=lambda q: antes[q]) > min(antes, key=lambda q: antes[q])
    if caiu and hoje_preco <= menor_antes * (1 + 0.005):
        return {"tipo": "voltou_a_cair" if ja_subiu_antes else "novo_minimo",
                "hoje": hoje_preco, "ontem": ontem,
                "menor": min(menor_antes, hoje_preco), "maior": maior_antes}
    if subiu and hoje_preco <= maior_antes * (1 - LONGE_DO_MAIOR):
        return {"tipo": "ultima_chance", "hoje": hoje_preco, "ontem": ontem,
                "menor": menor_antes, "maior": maior_antes}
    if subiu:
        return {"tipo": "subiu", "hoje": hoje_preco, "ontem": ontem,
                "menor": menor_antes, "maior": maior_antes}
    return None


def _catalogo() -> dict[str, dict]:
    """{id: ultimo registro publicado} — nome, link, imagem, canal."""
    saida: dict[str, dict] = {}
    if not CATALOGO.exists():
        return saida
    for linha in CATALOGO.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(linha)
        except ValueError:
            continue
        if r.get("id") is not None and r.get("link"):
            saida[str(r["id"])] = r
    return saida


def de_hoje() -> list[dict]:
    """Os sinais de hoje, so' de produtos que estao no catalogo, com o
    registro junto. Ordem: voltou_a_cair, novo_minimo, ultima_chance, subiu."""
    pd = por_dia()
    agora = _agora()
    cat = _catalogo()
    ordem = {"voltou_a_cair": 0, "novo_minimo": 1, "ultima_chance": 2, "subiu": 3}
    saida = []
    for pid, reg in cat.items():
        dias = dict(pd.get(pid) or {})
        # ⭐ o preco de HOJE e' o do instantaneo horario quando existe — e' o
        # que o site mostra; a serie so' tem o menor do dia
        inst = (agora.get(pid) or {}).get("preco")
        s = sinal_de(dias, float(inst) if inst else None)
        if s:
            s["id"], s["registro"] = pid, reg
            saida.append(s)
    saida.sort(key=lambda x: (ordem[x["tipo"]], -(x["maior"] - x["hoje"])))
    return saida


def _postados() -> set[str]:
    if not POSTADOS.exists():
        return set()
    try:
        return set(json.loads(POSTADOS.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def _marcar_postado(chave: str) -> None:
    s = _postados()
    s.add(chave)
    POSTADOS.parent.mkdir(parents=True, exist_ok=True)
    POSTADOS.write_text(json.dumps(sorted(s), ensure_ascii=False, indent=0),
                        encoding="utf-8")


def frase(s: dict) -> str:
    """A primeira linha do post: o fato medido, na voz do site."""
    r = lambda v: f"R$ {v:.2f}".replace(".", ",")   # noqa: E731
    if s["tipo"] == "voltou_a_cair":
        return f"voltou a cair: {r(s['ontem'])} → {r(s['hoje'])}, de novo no menor preço que eu já vi"
    if s["tipo"] == "novo_minimo":
        return f"menor preço desde que eu acompanho: {r(s['hoje'])} (era {r(s['ontem'])})"
    if s["tipo"] == "ultima_chance":
        return (f"última chance: subiu de {r(s['ontem'])} para {r(s['hoje'])}, "
                f"mas ainda está abaixo dos {r(s['maior'])} que eu já vi")
    return f"subiu: {r(s['ontem'])} → {r(s['hoje'])}"


def postar_sinais(quantos: int = 2, ensaio: bool = False) -> int:
    """Posta no canal os sinais que valem post (nao o 'subiu'). Devolve
    quantos sairam. UMA vez por produto/sinal/dia."""
    from . import vitrine, telegram, produto as _produto
    hoje = date.today().isoformat()
    ja = _postados()
    n = 0
    for s in de_hoje():
        if s["tipo"] == "subiu" or n >= quantos:
            continue
        chave = f"{s['id']}:{hoje}:{s['tipo']}"
        if chave in ja:
            continue
        reg = dict(s["registro"])
        reg["preco"] = f"R$ {s['hoje']:.2f}".replace(".", ",")
        p = _produto.normalizar(reg)
        if not p:
            continue
        texto = vitrine.postar_texto(p, reg.get("canal"), com_link=False, gancho=frase(s))
        print(f"  [{s['tipo']}] {p['nome'][:48]}  —  {frase(s)}")
        if ensaio:
            n += 1
            continue
        destino = vitrine.canal()
        if not destino:
            raise RuntimeError("falta TELEGRAM_CANAL_VITRINE no .env")
        try:
            foto = vitrine.cartaz_de(p)
        except Exception as e:                       # noqa: BLE001
            # ⚠️ sem Pillow (runner do garimpo) ou foto que nao baixa: o post
            # sai em texto; o sinal nao pode morrer por causa do cartaz
            print(f"     cartaz falhou ({type(e).__name__}) — texto puro")
            foto = None
        entregue = telegram.enviar_foto(foto, texto, destino,
                                        botao=(vitrine.ROTULO_BOTAO, p["link"])) if foto else False
        if not entregue:
            entregue = telegram.enviar(vitrine.postar_texto(p, reg.get("canal")), destino)
        if entregue:
            _marcar_postado(chave)
            n += 1
    return n


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="sinais de preco de hoje")
    a.add_argument("--postar", action="store_true", help="manda pro canal (ate' --quantos)")
    a.add_argument("--quantos", type=int, default=2)
    a.add_argument("--ensaio", action="store_true")
    o = a.parse_args()
    if o.postar:
        n = postar_sinais(o.quantos, o.ensaio)
        print(f"sinais: {n} post(s){' (ensaio)' if o.ensaio else ''}")
        return
    sin = de_hoje()
    if not sin:
        print("sinais: nenhum hoje (sem leitura de hoje, ou nada mudou >= 2%)")
        return
    for s in sin:
        print(f"{s['tipo']:14} {s['registro'].get('nome', '')[:44]:44} {frase(s)}")


if __name__ == "__main__":
    main()
