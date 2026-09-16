# -*- coding: utf-8 -*-
"""A reconferencia de hora em hora fala com o ML e alimenta a serie dele. Sem rede.

⛔ O que protege (16/09/2026):
1. produto `fonte: mercadolivre` entra no instantaneo pela porta do ML, e o
   AliExpress continua pela dele — os dois no mesmo `precos_agora.json`;
2. a serie do ML ganha UM ponto por dia por produto, so' se o preco mudou
   (sem isto a trava de 24h da pagina derruba o produto amanha);
3. ⛔ ML fora do ar NAO apaga o AliExpress: grava o que veio, e SO' DEPOIS
   estoura — a leitura anterior do ML fica no instantaneo;
4. (17/09) o NUMERO DE VENDEDORES entra na serie como `vol`, e vendedor a
   mais com o MESMO preco tambem grava ponto — e' a prova social do ML.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import precos, mercadolivre  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


tmp = Path(tempfile.mkdtemp())
orig = (precos.CATALOGO, precos.AGORA, precos.SERIE, precos.puxar, mercadolivre.fichas_atual)
try:
    precos.CATALOGO = tmp / "produtos_publicados.jsonl"
    precos.AGORA = tmp / "precos_agora.json"
    precos.SERIE = tmp / "precos_vistos.jsonl"
    precos.CATALOGO.write_text(
        json.dumps({"id": 1005, "nome": "Cabo", "fonte": "aliexpress", "link": "x"}) + "\n"
        + json.dumps({"id": "MLB1", "nome": "Air Fryer", "fonte": "mercadolivre", "link": "y"}) + "\n"
        + json.dumps({"id": "MLB2", "nome": "Liquidificador", "fonte": "mercadolivre", "link": "z"}) + "\n",
        encoding="utf-8")
    precos.puxar = lambda ids: {"1005": 9.9}
    mercadolivre.fichas_atual = lambda ids: {"MLB1": (200.0, 3), "MLB2": (70.0, 9)}

    print("1. AS DUAS FONTES NO MESMO INSTANTANEO, E A SERIE DO ML NASCE")
    checar(precos.ids_do_catalogo() == ["1005"] and precos.ids_do_catalogo("mercadolivre") == ["MLB1", "MLB2"],
           "ids separados por fonte")
    precos.atualizar()
    agora = json.loads(precos.AGORA.read_text(encoding="utf-8"))
    checar(set(agora) == {"1005", "MLB1", "MLB2"} and agora["MLB2"]["preco"] == 70.0,
           f"instantaneo com os 3 ({sorted(agora)})")
    serie = [json.loads(l) for l in precos.SERIE.read_text(encoding="utf-8").splitlines()]
    checar([s["id"] for s in serie] == ["MLB1", "MLB2"] and serie[1]["loja"] == "Mercado Livre",
           "serie do ML: 2 pontos, loja carimbada; o AliExpress NAO entra aqui (quem escreve e' o garimpo)")
    checar(serie[1]["vol"] == 9, f"o `vol` do ML e' o numero de vendedores ({serie[1]['vol']})")

    print()
    print("2. MESMO PRECO => SEM PONTO NOVO; PRECO MUDOU => UM PONTO")
    precos.atualizar()
    n2 = len(precos.SERIE.read_text(encoding="utf-8").splitlines())
    mercadolivre.fichas_atual = lambda ids: {"MLB1": (189.9, 3), "MLB2": (70.0, 9)}
    precos.atualizar()
    n3 = len(precos.SERIE.read_text(encoding="utf-8").splitlines())
    checar((n2, n3) == (2, 3), f"repeticao +0, uma mudanca +1 (veio {(n2, n3)})")
    # ⭐ vendedor a mais, MESMO preco => ponto novo (senao "+N desde" nao existe)
    mercadolivre.fichas_atual = lambda ids: {"MLB1": (189.9, 3), "MLB2": (70.0, 11)}
    precos.atualizar()
    serie = [json.loads(l) for l in precos.SERIE.read_text(encoding="utf-8").splitlines()]
    checar(len(serie) == 4 and serie[-1]["id"] == "MLB2" and serie[-1]["vol"] == 11,
           f"vendedores 9 -> 11 com o mesmo preco grava ponto (vol {serie[-1]['vol']})")

    print()
    print("3. ⛔ ML FORA DO AR: AliExpress gravado, ML mantido, e estoura DEPOIS")
    precos.puxar = lambda ids: {"1005": 8.8}
    def _cai(ids):
        raise RuntimeError("429 simulado")
    mercadolivre.fichas_atual = _cai
    estourou = False
    try:
        precos.atualizar()
    except RuntimeError:
        estourou = True
    agora = json.loads(precos.AGORA.read_text(encoding="utf-8"))
    checar(estourou, "levantou erro (a rodada nao pode parecer verde)")
    checar(agora["1005"]["preco"] == 8.8, "o AliExpress novo FOI gravado antes de estourar")
    checar(agora["MLB1"]["preco"] == 189.9, "a leitura anterior do ML ficou no instantaneo (nao sumiu)")
    checar(len(precos.SERIE.read_text(encoding="utf-8").splitlines()) == 4, "e a serie nao ganhou ponto falso")
finally:
    precos.CATALOGO, precos.AGORA, precos.SERIE, precos.puxar, mercadolivre.fichas_atual = orig
    shutil.rmtree(tmp, ignore_errors=True)

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
