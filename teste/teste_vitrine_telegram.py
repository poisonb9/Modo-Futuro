# -*- coding: utf-8 -*-
"""A vitrine posta uma vez, nao posta link torto, e nao posta sem canal."""
import io
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import produto as _produto      # noqa: E402
from engine import vitrine                  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


# ⚠️ REGISTRO DE MENTIRA. Sem isto o teste escreveria no estado de producao —
# e pior, o `ja_foi` leria links de verdade e o teste passaria por acidente.
_tmp = Path(tempfile.mkdtemp()) / "vitrine_postados.json"
vitrine.JA_POSTADOS = _tmp

print("1. o post MOSTRA o produto, e diz de onde veio")
P = {"nome": "Halter ajustavel 20 kg", "preco": "R$ 189", "loja": "Shopee",
     "preco_em": "2026-09-12", "link": "https://exemplo.com/halter"}
t = vitrine.postar_texto(_produto.normalizar(P), "atefalhar")
checar("?" not in t, "sem pergunta (§23.9: pergunta converteu 0 de 4)")
checar("Até Falhar" in t, "diz a origem — senao o feed vira monte anonimo")
checar(t.strip().endswith(P["link"]), "o link e' a ultima linha")
checar("preço visto em 2026-09-12" in t, "a data do preco vai junto")

print("\n2. NEGATIVO — nao posta o mesmo produto duas vezes")
checar(vitrine.postar(P, "atefalhar", ensaio=True) is not None,
       "1a vez: monta")
vitrine.marcar(P["link"])
checar(vitrine.postar(P, "atefalhar", ensaio=True) is None,
       "2a vez: NAO monta (a chave e' o link)")
# ⚠️ CASO NEGATIVO DO CASO NEGATIVO: a chave e' o link, entao trocar o NOME
# nao pode liberar repost. Sem isto, a guarda passaria acusando pelo nome.
outro_nome = dict(P, nome="Halter ajustavel — 20kg promocao")
checar(vitrine.postar(outro_nome, "atefalhar", ensaio=True) is None,
       "mesmo link com nome reescrito TAMBEM nao reposta")
checar(vitrine.postar(dict(P, link="https://exemplo.com/outro"),
                      "atefalhar", ensaio=True) is not None,
       "link novo posta — senao a guarda so' estaria travando tudo")

print("\n3. NEGATIVO — link de esquema estranho nao vai a publico")
# ⚠️ Falha FECHADA. Esta e' a unica porta do motor que manda link pra um canal
# publico sem ninguem ler antes.
for torto in ("javascript:alert(1)", "intent://x", "ftp://x", ""):
    try:
        vitrine.postar(dict(P, link=torto, link_novo=1), "atefalhar",
                       ensaio=True)
        checar(False, f"{torto!r} passou — NAO deveria")
    except _produto.ProdutoInvalido:
        checar(True, f"{torto!r} recusado")

print("\n4. NEGATIVO — sem canal no .env, estoura em vez de postar no vazio")
_antes = os.environ.pop(vitrine.ENV_CANAL, None)
try:
    checar(vitrine.canal() is None, "sem .env -> canal() None")
    try:
        vitrine.postar(dict(P, link="https://exemplo.com/z"), "atefalhar")
        checar(False, "postou sem canal — NAO deveria")
    except RuntimeError as e:
        checar("bot nao cria" in str(e),
               "estoura dizendo que o canal e' criado por PESSOA")
finally:
    if _antes is not None:
        os.environ[vitrine.ENV_CANAL] = _antes

print("\n5. registro ilegivel FALHA ALTO (vazio faria repostar tudo)")
_tmp.write_text("{isto nao e json", encoding="utf-8")
try:
    vitrine.ja_foi("https://x")
    checar(False, "leu lixo e seguiu — NAO deveria")
except RuntimeError:
    checar(True, "registro corrompido estoura em vez de repostar o catalogo")
_tmp.write_text("{}", encoding="utf-8")

print("\n6. todo canal da pagina sabe se apresentar no post")
_pag = io.open("paginas/contra_capa.html", encoding="utf-8").read()
import re  # noqa: E402
for banco in set(re.findall(r'banco: "([^"]+)"', _pag)):
    checar(banco in vitrine.ORIGEM, f"{banco}: tem nome de origem")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
