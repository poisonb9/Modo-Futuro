# -*- coding: utf-8 -*-
"""Busca do site sem resultado: juiz de pertinencia e os tres estados. Sem rede.

⛔ O que protege (medido em 16/09/2026): "macbook" voltava "com fonte" com
capa de teclado e hub USB. Acessorio nao e' o produto. E quando o modelo
nao responde, o estado e' "nao julgado" — nunca "atendido", nunca "sem
fonte". Fonte fora do ar tambem nao e' "sem fonte".
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import buscas_site as bs, modelo_texto  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


ACHADOS = [{"fonte": "AliExpress", "nome": "Capa de teclado para MacBook", "preco": 8.1, "vendas": 900, "link": "a"},
           {"fonte": "Mercado Livre", "nome": "Apple MacBook Air M1 13", "preco": 6000.0, "vendas": 4, "link": "b"},
           {"fonte": "Mercado Livre", "nome": "Hub USB-C 8 em 1", "preco": 27.0, "vendas": 30, "link": "c"}]

perguntar_real = modelo_texto.perguntar
marcados = []
try:
    print("1. O JUIZ TIRA O ACESSORIO E DEIXA O PRODUTO")
    modelo_texto.perguntar = lambda pergunta, tentativas=3: "2"
    r, julgado = bs.pertinentes("macbook", ACHADOS)
    checar(julgado and [x["nome"] for x in r] == ["Apple MacBook Air M1 13"], "so' o MacBook passou")
    modelo_texto.perguntar = lambda pergunta, tentativas=3: "Os que sao o produto: 2, 3."
    r, _ = bs.pertinentes("macbook", ACHADOS)
    checar([x["link"] for x in r] == ["b", "c"], "resposta com texto em volta ainda e' lida pelos numeros")
    modelo_texto.perguntar = lambda pergunta, tentativas=3: "0"
    r, julgado = bs.pertinentes("macbook", ACHADOS)
    checar(julgado and r == [], "'0' = nenhum e' o produto => lista vazia, julgado")

    print()
    print("2. ⛔ SEM MODELO: devolve tudo E diz que nao julgou")
    modelo_texto.perguntar = lambda pergunta, tentativas=3: None
    r, julgado = bs.pertinentes("macbook", ACHADOS)
    checar(len(r) == 3 and julgado is False, "3 achados, julgado=False")
    r, julgado = bs.pertinentes("macbook", [])
    checar(r == [] and julgado is True, "sem achados nao precisa de juiz (julgado=True, vazio)")

    print()
    print("3. OS ESTADOS DO ATENDIMENTO — e o que e' marcado no banco")
    bs.marcar = lambda ids, como, nota="": marcados.append((tuple(ids), como))
    bs.SEM_FONTE = Path(__file__).with_name("_sem_fonte_tmp.jsonl")
    bs.SEM_FONTE.unlink(missing_ok=True)
    bs.pendentes = lambda dias=7: [{"termo": "macbook", "vezes": 2, "ids": [1, 2]}]

    bs.procurar = lambda termo, canal="": (ACHADOS[1:2], [], True)
    e = bs.atender()[0]["estado"]
    checar(e == "com fonte" and not marcados, f"achado julgado => 'com fonte', NAO marca ({e})")

    bs.procurar = lambda termo, canal="": (ACHADOS, [], False)
    e = bs.atender()[0]["estado"]
    checar(e.startswith("pendente") and not marcados, f"achado sem juiz => pendente, NAO marca ({e})")

    bs.procurar = lambda termo, canal="": ([], ["Mercado Livre: HTTPError 429"], True)
    e = bs.atender()[0]["estado"]
    checar(e.startswith("pendente") and not marcados, f"fonte fora do ar => pendente, NAO marca ({e})")

    bs.procurar = lambda termo, canal="": ([], [], True)
    e = bs.atender()[0]["estado"]
    checar(e == "sem fonte" and marcados == [((1, 2), "sem_fonte")],
           f"nada nas 3 fontes, julgado => 'sem fonte' e marca os 2 ids ({e}, {marcados})")
    checar(bs.SEM_FONTE.exists() and '"termo": "macbook"' in bs.SEM_FONTE.read_text(encoding="utf-8"),
           "e entra no registro versionado buscas_sem_fonte.jsonl")
finally:
    modelo_texto.perguntar = perguntar_real
    try:
        bs.SEM_FONTE.unlink(missing_ok=True)
    except Exception:
        pass

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
