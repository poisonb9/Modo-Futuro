# -*- coding: utf-8 -*-
"""A tag de afiliado entra no link, e sem tag nao sai link. Sem rede."""
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import mercadolivre as ml  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


os.environ["MELI_MATT_WORD"] = "bryanexpand"
os.environ["MELI_MATT_TOOL"] = "87181766"
U = "https://www.mercadolivre.com.br/p/MLB25904875"

print("1. a tag entra no link")
q = parse_qs(urlparse(ml.com_afiliado(U)).query)
checar(q.get("matt_word") == ["bryanexpand"], "matt_word")
checar(q.get("matt_tool") == ["87181766"], "matt_tool")

print("\n2. NAO joga fora a query que ja' existia")
# ⚠️ URL de produto do ML vem com filtro; perder isso perde a VARIACAO
# escolhida (cor, tamanho) e o link leva pra outro item.
q = parse_qs(urlparse(ml.com_afiliado(U + "?pdp_filters=item_id:MLB39")).query)
checar(q.get("pdp_filters") == ["item_id:MLB39"], "pdp_filters preservado")
checar(q.get("matt_word") == ["bryanexpand"], "e a tag tambem entrou")

print("\n3. NAO duplica a tag se ela ja' estiver la'")
duas = ml.com_afiliado(ml.com_afiliado(U))
checar(duas.count("matt_word") == 1, "matt_word aparece uma vez so'")

print("\n4. ⭐ NEGATIVO — sem tag no ambiente, NAO devolve a url crua")
# ⚠️ Este e' o caso caro: link sem tag abre a pagina normalmente e nao paga
# nada. Um post assim parece certo pra sempre.
for falta in ("MELI_MATT_WORD", "MELI_MATT_TOOL"):
    guardado = os.environ.pop(falta)
    checar(ml.com_afiliado(U) == "", f"sem {falta} -> vazio, nao a url crua")
    os.environ[falta] = guardado
checar(ml.com_afiliado("") == "", "url vazia -> vazio")

print("\n5. as categorias apontam pra canais que existem")
from engine import garimpo  # noqa: E402
for canal in ml.CATEGORIAS:
    checar(canal in garimpo.CANAIS, f"{canal} tem perfil no garimpo")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
