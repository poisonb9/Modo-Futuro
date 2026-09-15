# -*- coding: utf-8 -*-
""""Isso rende video?" — o corte editorial, em primeira versao.

## O QUE ESTE MODULO ADMITE SOBRE SI MESMO

⚠️ **Isto NAO e' julgamento editorial. E' um proxy grosseiro dele.** O corte
de verdade e' do Bryan, olhando a lista. O que esta' aqui tira o obvio pra ele
nao gastar atencao com papel higienico — nada alem disso.

E' importante estar escrito, porque a tentacao de daqui a um mes vai ser
tratar a saida disto como veredito. Nao e'. Quando houver medicao de quais
produtos renderam view, ESSA medicao substitui este arquivo.

## A IDEIA, e ela veio de um contraste medido

⭐ **No AliExpress, vender muito e' sinal de QUALIDADE. No Mercado Livre,
vender muito e' sinal de COMMODITY.**

O pincel Kabuki com 32 mil vendas no AliExpress e' raro: alguem descobriu e a
coisa presta. O papel higienico Neve em 1o lugar no Mercado Livre e' o oposto:
todo mundo ja' compra no automatico, e ninguem assiste a um video sobre isso.

Achadinho e' o que a pessoa NAO sabia que existia. Ser o mais vendido do pais
e' evidencia CONTRA isso.

## O QUE ELE OLHA

1. reposicao — o que acaba e se recompra sem pensar
2. marca de supermercado — quem ja' esta' no carrinho nao precisa de descoberta
3. o produto explica o que faz em uma frase? (nao da' pra medir; nao entra)

⚠️ O item 3 e' o que realmente separa, e e' justamente o que eu nao sei
escrever. Fica registrado como o buraco que ele e'.
"""
from __future__ import annotations

import re

# ⚠️ REPOSICAO, e nao "categoria ruim". Papel higienico nao e' um produto
# pior que uma creatina — ele so' nao precisa ser apresentado a ninguem.
REPOSICAO = (
    "papel higiênico", "papel higienico", "sabão em pó", "sabao em po",
    "amaciante", "detergente", "desinfetante", "água sanitária",
    "agua sanitaria", "sabão líquido", "sabao liquido", "alvejante",
    "tira manchas", "percarbonato", "guardanapo", "papel toalha",
    "fralda", "absorvente", "ração", "racao", "areia para gato",
    "café em pó", "cafe em po", "açúcar", "acucar", "arroz", "feijão",
    "óleo de soja", "oleo de soja", "leite em pó", "leite em po",
)

# ⚠️ E' sobre o produto ser CONHECIDO, nao sobre a marca ser ruim. O Boticario
# faz bom perfume; so' que ninguem precisa de um video pra saber que ele
# existe. A descoberta ja' aconteceu ha' trinta anos.
JA_CONHECIDO = (
    "o boticário", "o boticario", "natura", "avon", "eudora", "omo",
    "ariel", "ypê", "ype", "veja", "pinho sol", "neve", "personal",
    "sadia", "nestlé", "nestle", "coca-cola", "heineken", "skol",
)


def rende(nome: str) -> tuple[bool, str]:
    """(rende video?, por que). O `por que` existe pra calibrar."""
    t = (nome or "").lower()
    if not t.strip():
        return False, "sem nome"
    for termo in REPOSICAO:
        # ⛔ ANCORADO NO INICIO DA PALAVRA. Antes era `termo in t`, substring
        # solta, e isso apagava produto em SILENCIO. MEDIDO em 15/09/2026, em
        # 111 candidatos: 7 de 8 cortes eram falsos, todos por "ração" —
        #
        #     "Caixa de som bluetooth, vibração"   -> vib(ração)
        #     "Clipes de Liberação Rápida"         -> libe(ração)
        #     "Luzes de tira led ... decoração"    -> deco(ração)
        #
        # ⚠️ A guarda ja' existia LOGO ABAIXO, na lista de marcas, com o
        # comentario certo ("filtro que casa demais reprova o que deveria
        # passar, e isso e' invisivel — o produto so' some"). Faltava aqui.
        #
        # ⭐ E so' no INICIO, nao nos dois lados: com `\btermo\b`, "fralda"
        # deixaria de casar com "fraldas" e o filtro passaria a errar pro
        # outro lado. Prefixo pega o plural e nao pega o meio de palavra.
        if re.search(rf"\b{re.escape(termo)}", t):
            return False, f"reposição ({termo}) — não precisa de descoberta"
    for marca in JA_CONHECIDO:
        # ⚠️ `\b` de proposito: "neve" casaria dentro de "neveira" e de
        # qualquer palavra com essas letras. Filtro que casa demais reprova o
        # que deveria passar, e isso e' invisivel — o produto so' some.
        if re.search(rf"\b{re.escape(marca)}\b", t):
            return False, f"marca de supermercado ({marca}) — já está no carrinho"
    return True, "passa"


def peneirar(produtos: list[dict]) -> tuple[list[dict], list[tuple[str, str]]]:
    """Separa o que rende do que nao rende. Devolve (passaram, recusados)."""
    passaram, fora = [], []
    for p in produtos:
        ok, porque = rende(p.get("nome", ""))
        (passaram if ok else fora).append(p if ok else (p.get("nome", ""), porque))
    return passaram, fora


# ⚠️ O MODELO, e por que um `:free`. O Bryan tem 14 contas OpenRouter com ~50
# chamadas gratis por dia cada (MEDIDO em 11/09/2026) — ~700/dia paradas. Um
# corte editorial de 30 titulos por rodada cabe folgado nisso.
#
# ⚠️ E O TETO E' DIARIO POR CHAVE: quando bate, so' volta no dia seguinte, e
# o rodizio NAO resolve (esta' escrito no `keys.openrouter`).
# ⚠️ MEDIDO em 13/09/2026: o `llama-3.3-70b:free` SAIU do plano gratis e
# devolve 404 dizendo "use a versao paga". Modelo gratis nao e' contrato:
# ele sai da lista quando quiserem, e o motor tem de cair na lista de
# palavras em vez de quebrar — foi o que aconteceu, e funcionou.
#
# ⭐ Nemotron porque ja' temos medicao dele no outro projeto, e porque
# classificar SIM/NAO nao pede modelo grande.
MODELO = "nvidia/nemotron-3.5-lightning:free"
# ⚠️ 25s, e nao 45. O nemotron:free e' lento e, com rodizio de 14 chaves,
# uma rodada ruim viraria 14 x 45s = 10 minutos parada dentro do garimpo.
# O corte e' um BONUS: ele nao pode segurar a rodada.
TEMPO_S = 25

# ⚠️ E NO MAXIMO TRES CHAVES POR RODADA. Sem teto, uma cota esgotada em
# todas faria o garimpo varrer as 14 antes de desistir.
TENTATIVAS_MAX = 3

PERGUNTA = """Voce decide se um produto rende um video curto de TikTok para um
canal de achadinhos brasileiro.

RENDE quando a pessoa NAO sabia que aquilo existia, ou quando o resultado
aparece na tela (antes/depois, o problema sendo resolvido).

NAO RENDE quando e' reposicao que a pessoa ja' compra no automatico (papel
higienico, sabao), marca que todo mundo ja' conhece, ou algo cujo uso e'
obvio demais para haver o que mostrar.

Responda SO' com uma linha por produto, no formato:
<numero>|SIM ou NAO|motivo em ate' 6 palavras

Produtos:
"""


def _pedir(titulos: list[str], tentativa: int = 1) -> dict[int, tuple[bool, str]] | None:
    """Manda os titulos pro modelo. None se nao deu — e ai' cai na lista.

    ⚠️ FALHA ABERTA PARA A LISTA, nunca para o "sim". Se o modelo nao
    responder, o corte volta a ser o `rende()` de palavras — que e' pior, mas
    conhecido. Deixar passar tudo seria trocar um filtro grosseiro por filtro
    nenhum, e ai' papel higienico volta pro canal de beleza.
    """
    import json as _j
    import requests
    from . import keys

    rot = keys.openrouter()
    if not len(rot):
        return None
    lista = "\n".join(f"{i+1}. {t[:110]}" for i, t in enumerate(titulos))
    chave = rot.proxima()
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": "Bearer " + chave,
                     "Content-Type": "application/json"},
            json={"model": MODELO, "temperature": 0,
                  "messages": [{"role": "user",
                                "content": PERGUNTA + lista}]},
            timeout=TEMPO_S)
        if r.status_code in (402, 429):
            # ⚠️ QUEIMA A CHAVE E TENTA A PROXIMA, e nao desiste na primeira.
            # MEDIDO em 13/09/2026: a chave 1 devolveu 429
            # ("free-models-per-day") e a chave 2 respondeu 200 no mesmo
            # segundo. Desistir aqui jogaria fora 13 chaves vivas.
            rot.queimar(chave)
            if tentativa >= min(TENTATIVAS_MAX, len(rot)):
                return None
            return _pedir(titulos, tentativa + 1)
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"      [!] corte por IA falhou ({type(e).__name__}) — "
              f"usando a lista de palavras")
        return None

    saida: dict[int, tuple[bool, str]] = {}
    for linha in texto.splitlines():
        partes = [x.strip() for x in linha.split("|")]
        if len(partes) < 2 or not partes[0].rstrip(".").isdigit():
            continue
        i = int(partes[0].rstrip(".")) - 1
        if 0 <= i < len(titulos):
            saida[i] = (partes[1].upper().startswith("S"),
                        partes[2] if len(partes) > 2 else "")
    return saida


def peneirar_com_ia(produtos: list[dict]) -> tuple[list[dict], list[tuple[str, str]]]:
    """O corte editorial feito por um modelo, com a lista como rede.

    ⭐ A lista de palavras acerta o obvio (papel higienico) e erra o resto: ela
    nao sabe o que e' "descoberta". Um modelo lendo o titulo sabe — e e' de
    graca dentro da cota que ja' esta' parada.

    ⚠️ A LISTA CONTINUA RODANDO ANTES, e nao e' redundancia: ela e' barata,
    deterministica, e tira o lixo evidente sem gastar chamada. O modelo decide
    so' o que sobrou.
    """
    passaram, fora = peneirar(produtos)
    if not passaram:
        return passaram, fora
    julgado = _pedir([p.get("nome", "") for p in passaram])
    # ⚠️ RESPOSTA INCOMPLETA E' RESPOSTA RUIM, e a checagem mora AQUI, em quem
    # USA — nao dentro do `_pedir`. MEDIDO em 13/09/2026: com ela la' dentro,
    # um teste que substituiu o `_pedir` passou por cima da guarda inteira.
    # Quem recebe o julgamento e' que tem de conferir se ele esta' completo.
    #
    # O modelo as vezes devolve 8 de 30 linhas; aceitar isso deixaria 22
    # produtos sem julgamento nenhum e ninguem notaria — a lista so' viria
    # menor.
    if julgado is None:
        return passaram, fora
    if len(julgado) < len(passaram) * 0.8:
        print(f"      [!] o modelo julgou {len(julgado)} de {len(passaram)} — "
              f"descartando e usando a lista de palavras")
        return passaram, fora
    fica, cai = [], list(fora)
    for i, p in enumerate(passaram):
        ok, porque = julgado.get(i, (True, ""))
        if ok:
            fica.append(p)
        else:
            cai.append((p.get("nome", ""), f"IA: {porque}"))
    return fica, cai
