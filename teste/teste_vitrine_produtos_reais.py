# -*- coding: utf-8 -*-
"""A vitrine do canal so' mostra produto que EXISTE e que PAGA.

⚠️ O defeito que esta guarda impede e' silencioso dos dois lados: produto sem
link vira cartao desligado numa pagina que promete "preco e link", e produto
no canal errado vende cozinha pra quem veio por maquiagem.
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
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


def escrever(linhas):
    d = Path(tempfile.mkdtemp())
    (d / "estado").mkdir()
    (d / "estado" / "produtos_publicados.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + chr(10) for x in linhas),
        encoding="utf-8")
    pb.RAIZ = d


BASE = {"canal": "truque.importado", "nome": "Serum facial", "preco": "R$ 39,90",
        "link": "https://s.click.aliexpress.com/e/_abc", "imagem": "http://i/1.jpg",
        "quando": "2026-09-14T10:00:00+00:00", "id": 1}

print("1. a chave e o @ PUBLICO, nao o nome interno")
# ⚠️ A pagina indexa por "achadinho.make"; gravar "truque.importado" poria o
# produto num canal que a pagina nao conhece, e a vitrine ficaria vazia sem
# ninguem ver erro nenhum.
escrever([BASE])
d = pb.produtos_reais()
checar("achadinho.make" in d, "truque.importado -> achadinho.make")
checar("truque.importado" not in d, "e o nome interno nao vira chave")
checar(d["achadinho.make"][0]["visto"] == "14/09", "a data vira dd/mm")

print("")
print("2. NEGATIVO - produto SEM link nao entra")
escrever([dict(BASE, link=""), dict(BASE, id=2, link=None)])
checar(pb.produtos_reais() == {}, "dois sem link -> vitrine vazia")

print("")
print("3. NEGATIVO - o mesmo produto nao aparece duas vezes")
# Sai pelo garimpo E pelo telegram: sao duas linhas, um produto so'.
escrever([dict(BASE, onde="garimpo"), dict(BASE, onde="telegram")])
checar(len(pb.produtos_reais()["achadinho.make"]) == 1, "dedup pelo id")

print("")
print("4. o mais novo primeiro, e no maximo quatro")
escrever([dict(BASE, id=i, nome="P%d" % i,
               quando="2026-09-%02dT10:00:00+00:00" % (i + 1))
          for i in range(1, 7)])
lista = pb.produtos_reais()["achadinho.make"]
checar(len(lista) == 4, "seis viram quatro")
checar(lista[0]["nome"] == "P6", "o mais novo na frente")

print("")
print("5. o Achadinho Total e a vitrine GERAL")
# ⚠️ `_todos` junta os canais todos, e e' o que a pagina usa pra mostrar os
# outros cantos da casa. Sem ele cada pagina so' saberia do proprio canal.
escrever([dict(BASE, id=1), dict(BASE, id=2, canal="atefalhar", nome="Luva")])
d = pb.produtos_reais()
checar(len(d["_todos"]) == 2, "_todos junta os dois canais")
checar(len(d["achadinho.make"]) == 1 and len(d["atefalhar"]) == 1,
       "e cada canal continua com o seu")

print("")
print("6. NEGATIVO - produto sem link fica fora do _todos tambem")
escrever([dict(BASE, link="")])
checar("_todos" not in pb.produtos_reais(), "vitrine geral vazia, nao chave vazia")

print("")
print("7. NEGATIVO - marcador sumido ESTOURA, nao passa batido")
# ⚠️ Se a substituicao falhasse calada, a pagina de exemplo iria pro ar com a
# etiqueta dizendo "exemplo" — e ninguem notaria que a real nunca subiu.
try:
    pb.injetar_produtos("<html>sem marcador</html>", {})
    checar(False, "devia ter estourado")
except SystemExit:
    checar(True, "html sem o marcador estoura")

print("")
print("8. e o marcador certo recebe os dados")
saida = pb.injetar_produtos(
    "  var PRODUTOS_REAIS = {};", {"achadinho.make": [{"nome": "X"}]})
checar('"achadinho.make"' in saida and '"X"' in saida, "os dados entram")
checar("var PRODUTOS_REAIS = {};" not in saida, "e o vazio sai")

print("")
print("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde")
sys.exit(1 if falhas else 0)
