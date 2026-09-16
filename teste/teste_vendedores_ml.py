# -*- coding: utf-8 -*-
"""A prova social do Mercado Livre e' o NUMERO DE VENDEDORES — e so' ele. Sem rede.

## POR QUE EXISTE (17/09/2026)

A API do ML nao da' vendas; da' um anuncio por vendedor. O cartao escreve
"+2 vendedores desde 16/09" (cresceu) ou "13 vendedores na loja" (nao) — e
NUNCA "+N vendidos", que e' a frase do AliExpress e mede outra coisa.

⭐ Os casos: (1) POSITIVO — serie do ML com vol 9 -> 11 vira [11, 2, 'dd/mm'];
(2) um dia so' = sem crescimento, mas o "hoje" existe; (3) ⛔ NEGATIVO — o
`vol` do ML NAO entra em `_vendas_desde` ("vendidos"), mesmo crescendo; e o
`vol` do AliExpress NAO entra em `_vendedores`; (4) pontos com vol 0 (a
serie antes de 17/09) nao sao base nem hoje.
"""
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
import publicar_bio as pb  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


def com_serie(linhas):
    raiz = Path(tempfile.mkdtemp())
    (raiz / "estado").mkdir()
    (raiz / "estado" / "precos_vistos.jsonl").write_text(
        "\n".join(json.dumps(x) for x in linhas), encoding="utf-8")
    antigo = pb.RAIZ
    pb.RAIZ = raiz
    return antigo


ML = "Mercado Livre"
antigo = com_serie([
    # ML: 16/09 sem vendedores gravados (vol 0), 17/09 = 9, 18/09 = 11
    {"id": "MLB1", "preco": 70.0, "vol": 0, "loja": ML, "quando": "2026-09-16"},
    {"id": "MLB1", "preco": 70.0, "vol": 9, "loja": ML, "quando": "2026-09-17"},
    {"id": "MLB1", "preco": 70.0, "vol": 11, "loja": ML, "quando": "2026-09-18"},
    # ML: um dia so'
    {"id": "MLB2", "preco": 13.0, "vol": 4, "loja": ML, "quando": "2026-09-17"},
    # AliExpress: volume de VENDAS 1000 -> 1800 (sem campo loja, como o garimpo grava)
    {"id": 555, "preco": 20.0, "vol": 1000, "quando": "2026-09-14"},
    {"id": 555, "preco": 20.0, "vol": 1800, "quando": "2026-09-17"},
])
try:
    print("1. POSITIVO: 9 -> 11 vendedores")
    v = pb._vendedores()
    checar(v.get("MLB1") == [11, 2, "17/09"], f"MLB1 = {v.get('MLB1')} (esperado [11, 2, '17/09'])")
    print()
    print("2. UM DIA SO': hoje existe, crescimento 0")
    checar(v.get("MLB2") == [4, 0, "17/09"], f"MLB2 = {v.get('MLB2')}")
    print()
    print("3. ⛔ NEGATIVO: vendedores nao viram 'vendidos', e vendas nao viram 'vendedores'")
    vd = pb._vendas_desde()
    checar("MLB1" not in vd, f"o ML NAO entra em _vendas_desde ({vd.get('MLB1')})")
    checar(vd.get("555") == (800, "14/09"), f"o AliExpress continua em _vendas_desde ({vd.get('555')})")
    checar("555" not in v, "o AliExpress NAO entra em _vendedores")
    print()
    print("4. vol 0 (serie antiga) nao e' base: a base e' 17/09, nao 16/09")
    checar(v["MLB1"][2] == "17/09", "a data e' a do primeiro dia COM vendedores")
finally:
    pb.RAIZ = antigo

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
