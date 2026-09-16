# -*- coding: utf-8 -*-
"""Preco, "de" riscado e queda do cartao do topo contam UMA historia. Sem rede.

## ⛔ POR QUE ESTE TESTE EXISTE

Em 16/09/2026 o topo da bio mostrou "R$ 73,69 ~~R$ 73,69~~ ↓21%". A causa:
`produtos_reais` lia `queda` do REGISTRO publicado (calculada no dia da
captura, com o historico antigo que somava anuncios diferentes), enquanto
`preco` e `antes` vinham da serie de HOJE. Tres numeros de tres momentos.

⭐ Os casos, na ordem: (1) o NEGATIVO — registro diz "caiu 21%", a serie diz
que nao caiu: o cartao sai SEM queda e SEM riscado; (2) o POSITIVO — a serie
ve' queda de 20%: queda 20 e riscado com o maior visto; (3) a guarda
`_coerente` nunca deixa riscado igual ao preco exibido.
"""
import json
import sys
import tempfile
from datetime import date
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


HOJE = date.today().isoformat()


def com_estado(serie, publicados):
    raiz = Path(tempfile.mkdtemp())
    (raiz / "estado").mkdir()
    (raiz / "estado" / "precos_vistos.jsonl").write_text(
        "\n".join(json.dumps(x) for x in serie), encoding="utf-8")
    (raiz / "estado" / "produtos_publicados.jsonl").write_text(
        "\n".join(json.dumps(x) for x in publicados), encoding="utf-8")
    antigo = pb.RAIZ
    pb.RAIZ = raiz
    return antigo


def primeiro(reais):
    for chave, itens in reais.items():
        if not chave.startswith("_") and itens:
            return itens[0]
    return None


print("1. ⛔ NEGATIVO: registro diz 'caiu 21%', a serie NAO ve' queda")
antigo = com_estado(
    [{"id": 73, "preco": 73.69, "quando": "2026-09-14"},
     {"id": 73, "preco": 73.69, "quando": "2026-09-15"},
     {"id": 73, "preco": 73.69, "quando": HOJE}],
    [{"id": 73, "nome": "Cabo", "canal": "atefalhar", "preco": "R$ 73,69",
      "queda": 21.0, "link": "x", "quando": HOJE + "T10:00:00+00:00"}])
try:
    p = primeiro(pb.produtos_reais())
    checar(p is not None, "o produto entrou na vitrine")
    checar(p and p["queda"] == 0.0, f"queda do REGISTRO (21%) foi ignorada: {p and p['queda']}")
    checar(p and p["antes"] == "", f"sem queda, sem riscado: {p and p['antes']!r}")
    checar(p and p["preco"] == "R$ 73,69", "o preco exibido e' o da serie de hoje")
finally:
    pb.RAIZ = antigo

print()
print("2. POSITIVO: a serie ve' 20% de queda => queda 20, riscado = maior visto")
antigo = com_estado(
    [{"id": 74, "preco": 20.00, "quando": "2026-09-14"},
     {"id": 74, "preco": 20.00, "quando": "2026-09-15"},
     {"id": 74, "preco": 16.00, "quando": HOJE}],
    [{"id": 74, "nome": "Fita", "canal": "atefalhar", "preco": "R$ 20,00",
      "queda": 0.0, "link": "x", "quando": HOJE + "T10:00:00+00:00"}])
try:
    p = primeiro(pb.produtos_reais())
    checar(p and abs(p["queda"] - 20.0) < 0.05, f"queda medida na serie, nao no registro: {p and p['queda']}")
    checar(p and p["antes"] == "R$ 20,00" and p["preco"] == "R$ 16,00",
           f"riscado {p and p['antes']} != exibido {p and p['preco']}")
    geral = pb.produtos_reais().get("_todos") or []
    checar(geral and geral[0]["queda"] == p["queda"] and geral[0]["antes"] == p["antes"],
           "o bloco `_todos` segue a mesma regra")
finally:
    pb.RAIZ = antigo

print()
print("3. A GUARDA: riscado igual ao exibido nunca sai")
c = pb._coerente({"preco": "R$ 73,69", "antes": "R$ 73,69", "queda": 21.0})
checar(c["antes"] == "" and c["queda"] == 0.0, "antes == preco => sem riscado e sem queda")
c = pb._coerente({"preco": "R$ 16,00", "antes": "R$ 20,00", "queda": 20.0})
checar(c["antes"] == "R$ 20,00" and c["queda"] == 20.0, "trio coerente passa intacto")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
