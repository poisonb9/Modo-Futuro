# -*- coding: utf-8 -*-
"""As fotos extras do Ali entram no instantaneo horario. Sem rede.

⭐ 18/09/2026 (MAESTROS_DESIGN_DO_SITE.md, defeito 1): a foto principal do
anuncio e' banner de lojista. O DTO do `productdetail.get` ja' traz
`product_small_image_urls`; guardar custa zero chamada.

O que protege:
1. `fotos_de` le' o formato da API ({"string": [...]}), tira a principal
   repetida, vazio e duplicata — e devolve LISTA VAZIA pra lixo, nunca lixo;
2. `atualizar` grava `imagens` em quem respondeu e MANTEM as de ontem em
   quem nao respondeu hoje (mesma regra do preco: falha nossa nao apaga);
3. ⛔ caso negativo: produto sem foto extra NAO ganha campo `imagens`
   (campo vazio na pagina viraria "sem foto", e o cartao tem a principal).
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


print("1. fotos_de: formato da API, sem principal, sem vazio, sem repetida")
d = {"product_main_image_url": "https://a/p.jpg",
     "product_small_image_urls": {"string": ["https://a/p.jpg", "https://a/1.jpg", "",
                                             "https://a/2.jpg", "https://a/1.jpg", 7]}}
checar(precos.fotos_de(d) == ["https://a/1.jpg", "https://a/2.jpg"],
       f"duas fotos limpas (veio {precos.fotos_de(d)})")
checar(precos.fotos_de({"product_small_image_urls": ["https://a/3.jpg"]}) == ["https://a/3.jpg"],
       "lista crua tambem serve")
for lixo in ({}, {"product_small_image_urls": None}, {"product_small_image_urls": "x"},
             {"product_small_image_urls": {"string": "x"}}, {"product_small_image_urls": 5}):
    checar(precos.fotos_de(lixo) == [], f"lixo vira lista vazia: {lixo!r}")

print()
print("2. atualizar grava `imagens` e mantem as de ontem em quem nao respondeu")
tmp = Path(tempfile.mkdtemp())
orig = (precos.CATALOGO, precos.AGORA, precos.SERIE, precos.puxar, mercadolivre.fichas_atual)
try:
    precos.CATALOGO = tmp / "produtos_publicados.jsonl"
    precos.AGORA = tmp / "precos_agora.json"
    precos.SERIE = tmp / "precos_vistos.jsonl"
    precos.CATALOGO.write_text(
        json.dumps({"id": 1, "nome": "Luva", "fonte": "aliexpress", "link": "x"}) + "\n"
        + json.dumps({"id": 2, "nome": "Grip", "fonte": "aliexpress", "link": "y"}) + "\n"
        + json.dumps({"id": 3, "nome": "Cabo", "fonte": "aliexpress", "link": "z"}) + "\n",
        encoding="utf-8")
    mercadolivre.fichas_atual = lambda ids: {}

    def _puxar_dia1(ids):
        precos.ULTIMAS_FOTOS.clear()
        precos.ULTIMAS_FOTOS.update({"1": ["https://a/l1.jpg", "https://a/l2.jpg"],
                                     "2": ["https://a/g1.jpg"], "3": []})
        return {"1": 10.0, "2": 20.0, "3": 30.0}
    precos.puxar = _puxar_dia1
    precos.atualizar()
    agora = json.loads(precos.AGORA.read_text(encoding="utf-8"))
    checar(agora["1"]["imagens"] == ["https://a/l1.jpg", "https://a/l2.jpg"], "produto 1 com as duas fotos")
    checar(agora["2"]["imagens"] == ["https://a/g1.jpg"], "produto 2 com a sua")
    checar("imagens" not in agora["3"], "⛔ produto SEM foto extra nao ganha campo `imagens`")

    def _puxar_dia2(ids):
        precos.ULTIMAS_FOTOS.clear()
        precos.ULTIMAS_FOTOS.update({"2": ["https://a/g9.jpg"]})
        return {"2": 21.0}                     # o 1 nao respondeu hoje
    precos.puxar = _puxar_dia2
    precos.atualizar()
    agora = json.loads(precos.AGORA.read_text(encoding="utf-8"))
    checar(agora["1"]["imagens"] == ["https://a/l1.jpg", "https://a/l2.jpg"],
           "quem nao respondeu hoje mantem as fotos de ontem (como mantem o preco)")
    checar(agora["2"]["imagens"] == ["https://a/g9.jpg"], "quem respondeu troca pelas de hoje")
finally:
    precos.CATALOGO, precos.AGORA, precos.SERIE, precos.puxar, mercadolivre.fichas_atual = orig
    shutil.rmtree(tmp, ignore_errors=True)

print()
print("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde")
sys.exit(1 if falhas else 0)
