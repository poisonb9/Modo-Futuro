# -*- coding: utf-8 -*-
"""O produto de afiliado do clipe — UM lugar so' define o formato.

⚠️ A DECISAO DA §2.2 DO FASE2.md, TOMADA EM 09/09/2026.

A pergunta pendente era: o produto vira campo do MANIFESTO, ou um registro
proprio ao lado dele? O argumento contra o manifesto era que ele ja' e' lido
por seis scripts.

**Vai no manifesto.** O que decide nao e' quantos leem — e' esta frase da
propria §2.2:

    "A pagina da bio e o grupo do WhatsApp precisam LER isso de algum lugar,
     e esse lugar tem de ser o mesmo que a legenda usa — senao o video diz um
     preco e a pagina diz outro."

A legenda e' montada a partir do manifesto. Registro separado cria duas
fontes para o mesmo preco, e duas fontes divergem — e' so' questao de tempo.
E' o mesmo raciocinio que ja' pos `sha`, `fonte_id` e `depende_de_anterior`
la' dentro: **o campo viaja pro manifesto porque quem decide so' le' o
manifesto.**

⚠️ E vai como UM campo aninhado (`produto`), nao como cinco soltos. Assim:
  - quem nao conhece o campo simplesmente nao o le' (os seis scripts atuais
    pegam chaves nomeadas; chave nova nao quebra nenhum);
  - os cinco canais de hoje ficam com `produto` AUSENTE, que e' diferente de
    "produto vazio" — ausente quer dizer "este clipe nao e' de afiliado".

## O QUE ESTE MODULO NAO FAZ

Nao publica, nao encurta link, nao consulta preco. Ele so' **valida e
normaliza**, num lugar so', pra que a legenda, a pagina da bio e o grupo do
WhatsApp leiam exatamente a mesma coisa.

⚠️ PRECO E' TEXTO, NAO NUMERO. De proposito. Preco de afiliado muda sozinho,
e um numero no manifesto envelhece calado — o clipe diz "R$ 39,90" pra sempre
enquanto a loja ja' mudou. Guardar como TEXTO deixa explicito que e' uma foto
do momento, e `preco_em` diz de quando.
"""
from __future__ import annotations

import re
from datetime import date

# Campos que um produto precisa ter pra servir a legenda E a pagina.
OBRIGATORIOS = ("nome", "link")

# ⚠️ So' http(s). Link de afiliado com esquema estranho (`intent://`,
# `javascript:`) nao e' link quebrado — e' vetor de ataque numa pagina que a
# gente publica. Falha FECHADA.
_LINK_OK = re.compile(r"^https?://[^\s]+$", re.I)


class ProdutoInvalido(ValueError):
    """Levantada quando o produto nao serve. NUNCA devolver produto pela
    metade: meio produto vira post com link quebrado, que e' pior que post
    sem link."""


def normalizar(bruto: dict | None) -> dict | None:
    """Devolve o produto pronto pro manifesto, ou None se nao houver.

    ⚠️ None e' "este clipe nao e' de afiliado" — o caso dos cinco canais de
    hoje. Nao confundir com produto invalido, que LEVANTA.
    """
    if not bruto:
        return None
    if not isinstance(bruto, dict):
        raise ProdutoInvalido(f"produto tem de ser objeto, veio {type(bruto).__name__}")

    faltando = [c for c in OBRIGATORIOS if not str(bruto.get(c, "")).strip()]
    if faltando:
        raise ProdutoInvalido(
            f"produto sem {', '.join(faltando)} — a pagina da bio e o grupo "
            f"leem estes campos, e um deles vazio vira card quebrado")

    link = str(bruto["link"]).strip()
    if not _LINK_OK.match(link):
        raise ProdutoInvalido(
            f"link nao e' http(s): {link[:60]!r}. Falha FECHADA de proposito — "
            f"este link vai parar numa pagina publica.")

    preco = str(bruto.get("preco", "")).strip()
    return {
        "nome": str(bruto["nome"]).strip(),
        "link": link,
        # ⚠️ TEXTO, nao numero. Ver o cabecalho.
        "preco": preco,
        # De quando e' essa foto do preco. So' existe se houver preco.
        "preco_em": (str(bruto.get("preco_em") or f"{date.today():%Y-%m-%d}")
                     if preco else ""),
        "loja": str(bruto.get("loja", "")).strip(),
        # Pra pagina da bio agrupar sem ter de adivinhar pelo canal.
        "categoria": str(bruto.get("categoria", "")).strip(),
    }


def do_manifesto(item: dict | None) -> dict | None:
    """Le o produto de um item do manifesto. Item antigo nao tem o campo, e
    isso e' normal — devolve None sem reclamar."""
    if not isinstance(item, dict):
        return None
    p = item.get("produto")
    return p if isinstance(p, dict) and p.get("link") else None


def linha_da_lista(item: dict) -> str | None:
    """Uma linha do produto, do jeito que o grupo do WhatsApp le'.

    ⚠️ E' a UNICA coisa que este repositorio pode entregar ao grupo hoje (a
    §2.5 do FASE2 e' explicita: publicar no grupo e' outro problema, sem
    integracao e sem credencial). Entao a lista sai daqui, pronta pra colar.
    """
    p = do_manifesto(item)
    if not p:
        return None
    partes = [p["nome"]]
    if p.get("preco"):
        partes.append(p["preco"])
    if p.get("loja"):
        partes.append(p["loja"])
    return " — ".join(partes) + f"\n{p['link']}"
