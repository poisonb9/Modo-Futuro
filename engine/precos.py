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

## ⚠️ E O MERCADO LIVRE?

Nao ha' UM produto de Mercado Livre em jogo hoje — medido em 15/09/2026: 301
linhas no catalogo, 301 com `fonte: aliexpress`, e `garimpo.do_mercado_livre()`
existe e nunca foi chamada. Quando entrar, a regra vale igual e a porta e'
outra (`/items/MLB...` devolve o preco atual). Este modulo so' sabe falar com o
AliExpress, e e' melhor que ele nao finja saber: produto de outra fonte fica de
fora do instantaneo e cai na trava de 24h da pagina, que e' o lado seguro.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "estado" / "produtos_publicados.jsonl"
AGORA = RAIZ / "estado" / "precos_agora.json"

# ⛔ MEDIDO, nao escolhido: acima disto a API devolve 50 e cala a boca.
LOTE = 50


def ids_do_catalogo() -> list[str]:
    """Os ids distintos que o catalogo publica hoje, sem repetir."""
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
        # ⚠️ So' AliExpress. Ver a nota do cabecalho sobre o Mercado Livre.
        if (r.get("fonte") or "aliexpress") != "aliexpress":
            continue
        pid = str(r.get("id") or "").strip()
        if not pid or pid in ("None", "0") or pid in ja:
            continue
        ja.add(pid)
        vistos.append(pid)
    return vistos


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


def puxar(ids: list[str]) -> dict:
    """{id: preco} da loja, agora. Levanta se a chamada falhar."""
    from . import aliexpress

    fora: dict[str, float] = {}
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
        if len(prods) < len(pedaco):
            print(f"      [!] pedi {len(pedaco)} e vieram {len(prods)} — "
                  f"produto fora do ar, ou o corte silencioso do lote")
    return fora


def atualizar(ensaio: bool = False) -> dict:
    """Reconfere tudo e grava o instantaneo. Devolve o que mudou."""
    ids = ids_do_catalogo()
    if not ids:
        print("catalogo vazio — nada a reconferir")
        return {}
    antes = ler_instantaneo()
    novos = puxar(ids)
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
    AGORA.parent.mkdir(parents=True, exist_ok=True)
    AGORA.write_text(json.dumps(saida, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"gravado: {AGORA.name} com {len(saida)} produtos")
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
