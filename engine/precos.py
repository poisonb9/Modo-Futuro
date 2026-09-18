# -*- coding: utf-8 -*-
"""Reconfere na loja o preco de TODO o catalogo, e guarda o instantaneo.

    python -m engine.precos --atualizar          reconfere e grava
    python -m engine.precos --atualizar --ensaio mostra o que mudaria

## POR QUE EXISTE

Ordem do Bryan em 15/09/2026, depois de ver a medicao: "vamos atualizar de hora
em hora". A medicao era esta, contra a API, sobre produtos que estavam NO AR:

    na pagina R$  20,11   ultima leitura nossa R$   9,35   API 9.35
    na pagina R$  65,87                        R$  51,99   API 51.99
    na pagina R$ 142,10                        R$ 107,89   API 107.89

⭐ E CUSTA QUASE NADA, o que e' a razao de dar pra fazer de hora em hora. O
`productdetail.get` aceita LOTE — medido no mesmo dia:

     1 id pedido ->   1 devolvido  1,9 s
    50 ids       ->  50            3,2 s
   100 ids       ->  50            3,3 s   ⛔ cortou pela metade, code=200

Entao o catalogo inteiro sai em 4 chamadas e ~13 s. De hora em hora sao ~96
chamadas por dia, contra as centenas que o garimpo ja' gasta sem bater teto.

⛔ E O CORTE EM 50 E' SILENCIOSO: pedir 100 devolve 50 com `code=200` e sem
erro nenhum. Por isso o lote e' 50 e a contagem de volta e' CONFERIDA — se
faltar produto, isso aparece no relato em vez de sumir.

## ⚠️ POR QUE UM ARQUIVO SEPARADO, E NAO MAIS LINHAS NA SERIE

A tentacao era empilhar as leituras horarias em `precos_vistos.jsonl`. Sao 154
ids x 24 = ~3.700 linhas por dia, ~300 KB/dia, num arquivo commitado de hora em
hora: em um ano o repo carregaria mais de 100 MB de historico de preco.

E ha' uma razao melhor, que nao e' tamanho: a serie consolida cada dia pelo
MENOR preco visto. Isso esta' certo pra calcular QUEDA (na duvida, a conta
conservadora) e esta' errado pra EXIBIR preco — o menor do dia pode ser uma
promocao que acabou as 11h. Este instantaneo guarda a leitura MAIS RECENTE,
que e' o numero que o visitante vai encontrar se clicar agora.

⭐ Os dois convivem com papeis separados, e isso e' de proposito:

    precos_vistos.jsonl   a SERIE, um ponto por dia. De onde sai o "de" riscado
                          e a linha do grafico.
    precos_agora.json     o INSTANTANEO, um valor por produto. De onde sai o
                          preco que a pagina mostra.

## ⚠️ E O MERCADO LIVRE? — ENTROU EM 16/09/2026

Ate' 15/09 nao havia UM produto do ML no catalogo (301 linhas, 301 AliExpress)
e este modulo so' falava com o AliExpress. Decisao do Bryan em 16/09: o ML
sobe pra loja, e a serie vem PRIMEIRO — sem reconferencia o produto entra
hoje e a trava de 24h o derruba amanha.

    AliExpress   productdetail.get em lotes de 50   -> instantaneo
    ML           /products/{id}/items, 1 por produto -> instantaneo
                 + UM PONTO POR DIA na serie (precos_vistos.jsonl)

⚠️ A serie do ML e' escrita AQUI porque nao ha' garimpo diario do ML que a
escreva (no AliExpress quem escreve e' o `garimpo.guardar_preco`). Um ponto
por dia, so' se mudou — a mesma regra do AliExpress e do Awin. E' o que
faz o `_serie_de_precos` da pagina enxergar o produto como vivo.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "estado" / "produtos_publicados.jsonl"
AGORA = RAIZ / "estado" / "precos_agora.json"
SERIE = RAIZ / "estado" / "precos_vistos.jsonl"

# ⛔ MEDIDO, nao escolhido: acima disto a API devolve 50 e cala a boca.
LOTE = 50


def ids_do_catalogo(fonte: str = "aliexpress") -> list[str]:
    """Os ids distintos que o catalogo publica hoje, desta fonte, sem repetir."""
    if not CATALOGO.exists():
        return []
    vistos: list[str] = []
    ja = set()
    for linha in CATALOGO.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            r = json.loads(linha)
        except ValueError:
            continue
        if (r.get("fonte") or "aliexpress") != fonte:
            continue
        pid = str(r.get("id") or "").strip()
        if not pid or pid in ("None", "0") or pid in ja:
            continue
        ja.add(pid)
        vistos.append(pid)
    return vistos


def _ultimo_ponto(ids: set[str]) -> dict[str, tuple[str, float, int]]:
    """{id: (ultimo dia, preco, vol)} na serie, so' pros ids pedidos."""
    saida: dict[str, tuple[str, float, int]] = {}
    if not SERIE.exists():
        return saida
    for linha in SERIE.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        i, q = str(d.get("id") or ""), (d.get("quando") or "")[:10]
        if i not in ids or not q:
            continue
        try:
            v = float(d.get("preco") or 0)
        except (TypeError, ValueError):
            continue
        try:
            vol = int(d.get("vol") or 0)
        except (TypeError, ValueError):
            vol = 0
        antes = saida.get(i)
        if antes is None or q >= antes[0]:
            saida[i] = (q, v, vol)
    return saida


def anotar_serie(novos: dict, loja: str) -> int:
    """Um ponto por produto por dia na serie, so' se o preco (ou o volume)
    mudou. Devolve quantos gravou. E' a regra do `garimpo.guardar_preco` e
    do `awin.guardar_catalogo`, para quem nao tem garimpo diario proprio.

    ⭐ `novos` e' {id: preco} ou {id: (preco, vol)}. No Mercado Livre `vol`
    e' o NUMERO DE VENDEDORES (17/09/2026) — a API nao da' vendas, e e' o
    que o cartao usa como prova social. Vol que mudou tambem grava ponto:
    "+2 vendedores desde 16/09" so' existe se a serie guardou os dois.
    """
    from datetime import date
    hoje = f"{date.today():%Y-%m-%d}"
    ultimo = _ultimo_ponto(set(novos))
    n = 0
    SERIE.parent.mkdir(parents=True, exist_ok=True)
    with SERIE.open("a", encoding="utf-8") as f:
        for pid, v in novos.items():
            preco, vol = (v if isinstance(v, (tuple, list)) else (v, 0))
            antes = ultimo.get(pid)
            if antes and abs(antes[1] - preco) < 0.005 and int(antes[2]) == int(vol):
                continue
            f.write(json.dumps({"id": pid, "preco": round(preco, 2), "vol": int(vol),
                                "loja": loja, "quando": hoje},
                               ensure_ascii=False) + chr(10))
            n += 1
    return n


def ler_instantaneo() -> dict:
    if not AGORA.exists():
        return {}
    try:
        return json.loads(AGORA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # ⚠️ FALHA ABERTA AQUI, e so' aqui: instantaneo ilegivel volta vazio e
        # a pagina cai na serie do dia, que e' o comportamento antigo e
        # honesto. Estourar faria um arquivo de cache derrubar a publicacao.
        return {}


def fotos_de(d: dict) -> list[str]:
    """As fotos extras do anuncio, como a API manda (`product_small_image_urls`
    vem como {"string": [...]}), sem a principal repetida e sem vazio."""
    bruto = d.get("product_small_image_urls") or {}
    if isinstance(bruto, dict):
        bruto = bruto.get("string") or []
    if not isinstance(bruto, list):
        return []
    principal = d.get("product_main_image_url") or ""
    vistas, fim = set(), []
    for u in bruto:
        if isinstance(u, str) and u and u != principal and u not in vistas:
            vistas.add(u)
            fim.append(u)
    return fim


# ⚠️ As fotos saem por AQUI, e nao pela assinatura de `puxar`: os testes
# substituem `precos.puxar` por um lambda de UM argumento, e mudar a
# assinatura quebraria arquivo congelado. `puxar` escreve; `atualizar` le'.
ULTIMAS_FOTOS: dict[str, list[str]] = {}


def puxar(ids: list[str]) -> dict:
    """{id: preco} da loja, agora. Levanta se a chamada falhar.

    ⭐ FOTOS EXTRAS (18/09/2026). O mesmo DTO traz `product_small_image_urls`
    — varias fotos por anuncio — e ate' hoje so' a principal era guardada. A
    principal e' a que o lojista escolhe pra COMPETIR na busca do Ali: banner,
    "22 colors available~", texto por cima. Os Maestros (Analista de Loja
    Virtual EP.2) chamam isso de banner na pagina de produto e mandam tirar.
    Guardar as outras aqui custa ZERO chamada: e' campo que ja' vem. Quem
    escolhe a limpa e' o publicador, com criterio medido — nao este modulo.
    Escreve {id: [urls]} em `ULTIMAS_FOTOS`.
    """
    from . import aliexpress

    fora: dict[str, float] = {}
    ULTIMAS_FOTOS.clear()
    import time

    for i in range(0, len(ids), LOTE):
        pedaco = ids[i:i + LOTE]
        # ⚠️ RESPIRO ENTRE LOTES. A API recusa rajada, e a recusa nao vem como
        # erro HTTP: vem como envelope sem produtos. Quatro chamadas coladas
        # foi o que produziu a perda de 49.
        if i:
            time.sleep(2)
        r = aliexpress.chamar("aliexpress.affiliate.productdetail.get",
                              product_ids=",".join(pedaco),
                              target_currency="BRL", target_language="PT",
                              country="BR")
        # ⛔ ENGOLIR ESTE ERRO CUSTOU 49 PRODUTOS na primeira rodada de verdade,
        # e o relato dizia "153 reconferidos" enquanto o arquivo saia com 104.
        # A versao anterior fazia `except (KeyError, TypeError): prods = []` —
        # ou seja, uma CHAMADA QUE FALHOU (a API recusa rajada e devolve um
        # envelope de erro) virava "este lote nao tem produto", indistinguivel
        # de "estes produtos sairam do ar".
        #
        # ⚠️ Sao coisas opostas: produto fora do ar e' informacao, chamada
        # falhada e' ausencia de informacao. Confundir as duas apaga preco em
        # silencio — e o efeito na ponta e' a pagina mostrar preco velho
        # achando que reconferiu.
        try:
            prods = (r["aliexpress_affiliate_productdetail_get_response"]
                     ["resp_result"]["result"]["products"]["product"])
        except (KeyError, TypeError) as e:
            raise RuntimeError(
                f"a API nao devolveu produtos no lote {i // LOTE + 1} "
                f"({len(pedaco)} ids): {json.dumps(r, ensure_ascii=False)[:200]}"
            ) from e
        for d in prods:
            try:
                v = float(d.get("target_sale_price") or 0)
            except (TypeError, ValueError):
                continue
            # ⛔ `target_original_price` NUNCA entra: e' ~2x o de venda (medido
            # em 7 de 9), e no Tapete de Banheiro era exatamente o R$ 88,88
            # que nos gravamos um dia como se fosse preco.
            if v > 0:
                fora[str(d.get("product_id"))] = v
                ULTIMAS_FOTOS[str(d.get("product_id"))] = fotos_de(d)
        if len(prods) < len(pedaco):
            print(f"      [!] pedi {len(pedaco)} e vieram {len(prods)} — "
                  f"produto fora do ar, ou o corte silencioso do lote")
    return fora


def atualizar(ensaio: bool = False) -> dict:
    """Reconfere tudo e grava o instantaneo. Devolve o que mudou."""
    ids = ids_do_catalogo()
    ids_ml = ids_do_catalogo("mercadolivre")
    if not ids and not ids_ml:
        print("catalogo vazio — nada a reconferir")
        return {}
    antes = ler_instantaneo()
    ULTIMAS_FOTOS.clear()
    novos = puxar(ids) if ids else {}
    fotos = dict(ULTIMAS_FOTOS)
    # ⭐ O MERCADO LIVRE, pela porta dele. Falha aqui NAO derruba o
    # instantaneo do AliExpress: sao fontes independentes, e o que ja' foi
    # reconferido acima e' informacao boa. O erro sobe DEPOIS de gravar.
    erro_ml = None
    fichas_ml: dict[str, tuple] = {}
    novos_ml: dict[str, float] = {}
    if ids_ml:
        from . import mercadolivre
        try:
            # ⭐ preco E vendedores numa chamada so' (17/09/2026)
            fichas_ml = mercadolivre.fichas_atual(ids_ml)
            novos_ml = {pid: v[0] for pid, v in fichas_ml.items()}
            print(f"ML: {len(ids_ml)} no catalogo | {len(novos_ml)} reconferidos | "
                  f"{len(ids_ml) - len(novos_ml)} sem vendedor hoje")
        except Exception as e:                       # noqa: BLE001
            erro_ml = e
            print(f"ML: reconferencia FALHOU ({type(e).__name__}) — "
                  "leituras anteriores mantidas")
    novos.update(novos_ml)
    ids = ids + ids_ml
    quando = datetime.now(timezone.utc).isoformat(timespec="seconds")
    mudou = {}
    for pid, v in novos.items():
        velho = (antes.get(pid) or {}).get("preco")
        if velho is None or abs(float(velho) - v) > 0.005:
            mudou[pid] = (velho, v)
    print(f"{len(ids)} no catalogo | {len(novos)} reconferidos | "
          f"{len(ids) - len(novos)} sem resposta | {len(mudou)} mudaram")
    for pid, (velho, v) in list(mudou.items())[:8]:
        de = f"R$ {float(velho):.2f}" if velho is not None else "(novo)"
        print(f"   {pid}  {de:>12} -> R$ {v:.2f}")
    if ensaio:
        print("\n[ensaio] nada foi gravado")
        return mudou
    # ⚠️ O QUE NAO RESPONDEU FICA COM A LEITURA ANTERIOR, e nao some. Apagar
    # faria o produto cair na trava de 24h da pagina por causa de uma falha de
    # rede nossa — e o preco anterior continua sendo a melhor coisa que temos.
    # O carimbo `quando` e' que envelhece, e e' ele que a trava le'.
    saida = dict(antes)
    for pid, v in novos.items():
        saida[pid] = {"preco": round(v, 2), "quando": quando}
        # ⭐ fotos extras do Ali (ver `puxar`); quem nao respondeu hoje
        # mantem as de ontem junto com o preco de ontem
        if fotos.get(pid):
            saida[pid]["imagens"] = fotos[pid]
        elif (antes.get(pid) or {}).get("imagens"):
            saida[pid]["imagens"] = antes[pid]["imagens"]
    # ⭐ ML (regua v2, 17/09/2026): frete gratis e reputacao do vendedor do
    # anuncio mais barato entram no instantaneo — a Confianca MEDIDA do ML.
    if fichas_ml:
        from . import mercadolivre as _ml
        for pid, f in fichas_ml.items():
            if len(f) >= 4:
                rep = _ml.reputacao(f[3])
                saida[pid]["frete_gratis"] = bool(f[2])
                if rep:
                    saida[pid]["reputacao"] = rep
                # ⭐ o anuncio que TEM esse preco — o cartao linka nele (18/09)
                if len(f) >= 5 and f[4]:
                    saida[pid]["item_id"] = str(f[4])
    AGORA.parent.mkdir(parents=True, exist_ok=True)
    AGORA.write_text(json.dumps(saida, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"gravado: {AGORA.name} com {len(saida)} produtos")
    if fichas_ml:
        n = anotar_serie({pid: (f[0], f[1]) for pid, f in fichas_ml.items()}, "Mercado Livre")
        print(f"serie ML: +{n} ponto(s)")
    if erro_ml is not None:
        raise RuntimeError("reconferencia do ML falhou (AliExpress gravado)") from erro_ml
    return mudou


def main() -> None:
    import argparse

    a = argparse.ArgumentParser(description="reconfere o preco do catalogo")
    a.add_argument("--atualizar", action="store_true")
    a.add_argument("--ensaio", action="store_true",
                   help="mostra o que mudaria, sem gravar")
    o = a.parse_args()
    if o.atualizar:
        atualizar(o.ensaio)
    else:
        a.print_help()


if __name__ == "__main__":
    main()
