# -*- coding: utf-8 -*-
"""A busca dirigida do ML devolve o produto pedido, pelo MENOR preco. Sem rede.

## ⛔ O QUE ESTA GUARDA PROTEGE (tudo medido em 16/09/2026)

1. ficha sem vendedor (404 "No winners found") e' PULADA, nao estoura;
2. o menor anuncio vence — o primeiro da lista NAO e' o mais barato;
3. livro sai (MLB-BOOKS na frente de "air fryer");
4. peca de dominio minoritario sai (acoplador a R$ 9,50 na frente do
   liquidificador);
5. ficha de 1 vendedor so' entra se nao houver com 2+;
6. o link leva a etiqueta do canal;
7. quando a primeira pagina nao enche a cota, a busca pagina E tenta
   termo + marca — e as marcas vem das fichas, nao de tabela nossa.

⚠️ Caso negativo teorematico: `_get` de mentira registra CADA caminho
chamado; se a pagina 2 ou a busca por marca nao forem pedidas quando a cota
ja' esta' cheia, e' por construcao do laco, nao por sorte.
"""
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import mercadolivre as ml  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


def ficha(pid, nome, dom, marca="Marca X"):
    return {"id": pid, "name": nome, "domain_id": dom,
            "pictures": [{"url": f"https://f/{pid}.jpg"}],
            "attributes": [{"id": "BRAND", "value_name": marca}]}


def anuncio(preco, frete=False):
    return {"price": preco, "shipping": {"free_shipping": frete}}


class Dublê:
    def __init__(self, paginas, itens):
        self.paginas, self.itens, self.chamadas = paginas, itens, []

    def __call__(self, caminho, **params):
        self.chamadas.append((caminho, dict(params)))
        if caminho == "/products/search":
            chave = (params.get("q"), params.get("offset", 0))
            return {"results": self.paginas.get(chave, [])}
        if caminho.endswith("/items"):
            pid = caminho.split("/")[2]
            if pid not in self.itens:
                r = requests.Response(); r.status_code = 404
                raise requests.HTTPError("404 No winners found", response=r)
            return {"results": self.itens[pid]}
        raise AssertionError("caminho inesperado " + caminho)


get_real = ml._get
try:
    print("1. UMA PAGINA CHEIA: fantasma pula, livro sai, peca sai, menor preco vence")
    pg1 = [
        ficha("F1", "Liquidificador Fantasma", "MLB-BLENDERS"),
        ficha("L1", "Receitas na Air Fryer", "MLB-BOOKS"),
        ficha("P1", "Arraste Acoplador Copo", "MLB-BLENDER_AND_HAND_BLENDER_DRIVE_COUPLINGS"),
        ficha("A1", "Liquidificador Mondial L-550", "MLB-BLENDERS", "Mondial"),
        ficha("A2", "Liquidificador Oster", "MLB-BLENDERS", "Oster"),
        ficha("S1", "Liquidificador de 1 vendedor", "MLB-BLENDERS"),
        ficha("F2", "Outro fantasma", "MLB-BLENDERS"),
    ]
    itens = {
        "L1": [anuncio(30.0)],
        "P1": [anuncio(9.5), anuncio(11.0)],
        "A1": [anuncio(149.99), anuncio(72.0, True), anuncio(120.0)],   # 1o NAO e' o menor
        "A2": [anuncio(319.9), anuncio(289.0)],
        "S1": [anuncio(15.0)],
    }
    d = Dublê({("liquidificador", 0): pg1}, itens)
    ml._get = d
    r = ml.buscar("liquidificador", quantos=2, canal="cozinha.importada")
    checar([x["_id"] for x in r] == ["A1", "A2"], f"vieram A1 e A2, nesta ordem ({[x['_id'] for x in r]})")
    checar(r and r[0]["preco"] == "R$ 72,00" and r[0]["frete_gratis"] is True,
           "A1 sai a R$ 72,00 (o MENOR dos tres anuncios), com o frete DESSE anuncio")
    checar(all(x["_id"] != "L1" for x in r), "o livro (MLB-BOOKS) ficou fora")
    checar(all(x["_id"] != "P1" for x in r), "a peca (dominio minoritario) ficou fora, mesmo sendo a mais barata")
    checar(all(x["_id"] != "S1" for x in r), "ficha de 1 vendedor ficou fora porque ha' fichas com 2+")
    checar(r and "matt_word=achadinhochef" in r[0]["link"] and "/p/A1" in r[0]["link"],
           "o link e' /p/<id> com a etiqueta do canal")
    checar(r and r[0]["imagem"] == "https://f/A1.jpg", "a foto vem da propria busca (sem chamada extra)")
    print()
    print("2. ⛔ COTA CHEIA NA PAGINA 1 => NAO pagina, NAO busca por marca")
    buscas = [c for c in d.chamadas if c[0] == "/products/search"]
    checar(len(buscas) == 1 and buscas[0][1].get("offset", 0) == 0,
           f"uma busca so', offset 0 ({len(buscas)} busca(s))")
    checar(not any(c[0].endswith("/items") and "/products/L1/" in c[0] for c in d.chamadas),
           "o livro nem teve o anuncio consultado (filtro ANTES da chamada)")

    print()
    print("3. COTA VAZIA NA PAGINA 1 => pagina 2 E termo + marca, marca vinda das fichas")
    pg1 = [ficha("F1", "Fantasma", "MLB-BLENDERS", "Mondial"),
           ficha("F2", "Fantasma 2", "MLB-BLENDERS", "Mondial"),
           ficha("F3", "Fantasma 3", "MLB-BLENDERS", "Oster")]
    pg2 = [ficha("B1", "Liquidificador Philips", "MLB-BLENDERS", "Philips")]
    por_marca = [ficha("M1", "Liquidificador Mondial Turbo", "MLB-BLENDERS", "Mondial")]
    d = Dublê({("liquidificador", 0): pg1, ("liquidificador", 50): pg2,
               ("liquidificador Mondial", 0): por_marca}, {
        "B1": [anuncio(99.0), anuncio(89.9)],
        "M1": [anuncio(129.0), anuncio(119.0)],
    })
    ml._get = d
    r = ml.buscar("liquidificador", quantos=5, paginas=2)
    ids = [x["_id"] for x in r]
    checar(ids == ["B1", "M1"], f"pagina 2 (B1) e busca por marca (M1) entraram, por preco ({ids})")
    qs = [c[1].get("q") for c in d.chamadas if c[0] == "/products/search"]
    checar("liquidificador Mondial" in qs, "a marca mais frequente das fichas (Mondial, 2x) virou busca")
    checar(qs.count("liquidificador Mondial") == 1, "e uma vez so'")
    checar("liquidificador Oster" in qs, "a segunda marca (Oster) tambem, ate' 3")

    print()
    print("4. ⛔ NADA COM VENDEDOR => lista vazia, sem estourar")
    d = Dublê({("xyz", 0): [ficha("F1", "Fantasma", "MLB-X")]}, {})
    ml._get = d
    checar(ml.buscar("xyz", quantos=3, paginas=1) == [], "fantasma em tudo => []")
finally:
    ml._get = get_real

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
