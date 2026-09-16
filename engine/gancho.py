# -*- coding: utf-8 -*-
"""A primeira linha do post do canal: um fato MEDIDO, dito de um jeito que para.

    python -m engine.gancho --ensaio     mostra o gancho do catalogo inteiro

## POR QUE ELA EXISTE

Decisao do Bryan em 16/09/2026: o nome do produto aparecia DUAS vezes no post
— no cartaz e na primeira linha da legenda. Ele pediu pra tirar da legenda e
pôr "algo interessante, impressionante", podendo consultar o Gemini.

⛔ E "IMPRESSIONANTE" AQUI NAO PODE SIGNIFICAR "INVENTADO". Esta e' a linha
mais alta do post, a que decide se a pessoa para de rolar — e e' exatamente
onde uma frase de propaganda faria o estrago maior. A operacao inteira passou
duas semanas tirando desconto falso da pagina; nao vai reinstalar propaganda
pela legenda.

⭐ ENTAO O GANCHO SAI DO DADO, SEMPRE. O modulo primeiro escolhe QUAL fato
medido e' o mais forte que existe sobre aquele produto, e so' depois pergunta
ao modelo como dizer aquele fato. O modelo escolhe a FRASE, nunca o FATO.

## A ORDEM DOS FATOS, do mais forte pro mais fraco

    1. caiu X%           a queda medida contra a NOSSA serie de preco
    2. menor ja' visto   o preco de hoje e' o piso da serie, e ha' N dias dela
    3. X vendidos        o volume que a loja declara
    4. o preco           o ultimo recurso: so' o numero, sem adjetivo

⚠️ E O QUARTO NAO E' DERROTA. Produto sem queda, sem serie e sem volume nao
tem nada de impressionante pra dizer — e inventar ali seria fabricar o que o
dado nao tem. O cartaz ja' mostra a foto, o nome e o preco; a legenda pode
simplesmente nao gritar.

## ⛔ A GUARDA: NUMERO QUE O MODELO INVENTOU NAO VAI AO AR

Mesma regra do `nome_produto.confere`, e pelo mesmo motivo. Todo numero da
frase final tem de existir no fato que foi mandado. Se sobrar um, a frase e'
DESCARTADA e vale a versao deterministica — que sempre existe e nunca mente.
"""
from __future__ import annotations

import re

# ⚠️ O MESMO PISO DE 2% da pagina e do cartaz. Abaixo disso e' arredondamento
# e cambio, nao queda — e anunciar "caiu 1%" e' pior que nao anunciar nada.
QUEDA_MINIMA = 2.0

# ⚠️ VOLUME SO' IMPRESSIONA A PARTIR DE ALGUM LUGAR. "12 pessoas compraram"
# nao para ninguem; abaixo deste piso o fato existe e nao vale a linha.
VENDAS_MINIMO = 100

# ⚠️ A SERIE PRECISA TER FOLEGO pra "menor preco que ja' vimos" significar
# algo. Com dois dias de serie a frase e' tecnicamente verdadeira e
# praticamente vazia — e' o mesmo motivo pelo qual o grafico de 3 pontos ficou
# de fora da pagina.
SERIE_MINIMA = 4

PERGUNTA = """Você escreve a primeira linha de um post de achadinhos no
Telegram, em português do Brasil.

O FATO MEDIDO, que é a única coisa que você pode dizer:
{fato}

O produto é: {nome}

REGRAS:
- no máximo 70 caracteres
- diga o FATO, com outras palavras, de um jeito que faça parar de rolar
- NÃO invente nenhum número que não esteja no fato acima
- NÃO use adjetivo de propaganda ("imperdível", "incrível", "corre")
- NÃO repita o nome do produto: ele já aparece na imagem
- sem emoji

Responda só a linha, nada mais."""


def _num(preco) -> float:
    """"R$ 13,52" -> 13.52. Zero no que nao der pra ler."""
    try:
        return float(str(preco).replace("R$", "").replace(".", "")
                     .replace(",", ".").strip() or 0)
    except ValueError:
        return 0.0


def _numeros(t: str) -> set[str]:
    """Os numeros do texto, sem pontuacao de milhar nem centavos."""
    return set(re.findall(r"\d+", str(t).replace(".", "").replace(",", "")))


def fato(p: dict, serie: list[float] | None = None) -> tuple[str, str]:
    """O fato mais forte que existe sobre este produto: (fato, frase pronta).

    A `frase` e' a versao deterministica — a que vai ao ar quando o modelo nao
    responde, ou quando a resposta dele e' recusada. Ela nunca falta.

    ⚠️ `serie` sao os precos que NOS vimos (um por dia, o menor de cada dia —
    a mesma consolidacao do `garimpo.historico`). Quem chama e' que a busca,
    porque este modulo roda em lote e abrir a serie por produto seria reler o
    arquivo inteiro uma vez por post.
    """
    hoje = _num(p.get("preco"))
    antes = _num(p.get("preco_antes"))
    serie = [x for x in (serie or []) if x > 0]

    # 1. A QUEDA MEDIDA. O fato mais forte que esta operacao tem.
    if antes and hoje and antes > hoje * (1 + QUEDA_MINIMA / 100):
        caiu = round(100 * (antes - hoje) / antes)
        if caiu >= QUEDA_MINIMA:
            f = (f"caiu {caiu}% desde que começamos a acompanhar: "
                 f"estava R$ {antes:.2f} e hoje está R$ {hoje:.2f}"
                 ).replace(".", ",")
            return f, f"Caiu {caiu}% desde que a gente começou a olhar."

    # 2. O PISO DA SERIE. So' vale com serie que tenha folego.
    if hoje and len(serie) >= SERIE_MINIMA and hoje <= min(serie) * 1.001:
        dias = len(serie)
        f = (f"é o menor preço em {dias} dias de acompanhamento nosso: "
             f"R$ {hoje:.2f}").replace(".", ",")
        return f, f"Menor preço em {dias} dias de olho nele."

    # 3. O VOLUME QUE A LOJA DECLARA.
    #
    # ⚠️ E A FRASE DIZ DE ONDE VEM. Este numero e' da loja, nao nosso — e
    # apresenta-lo como medicao propria seria emprestar a nossa credibilidade
    # pra um dado que a gente nao conferiu.
    vendas = int(_num(p.get("_vendas") or p.get("vendas") or 0))
    if vendas >= VENDAS_MINIMO:
        f = f"a loja registra {vendas} vendas deste produto"
        return f, f"{vendas} pessoas já levaram, segundo a loja."

    # 4. O ULTIMO RECURSO: so' o preco, sem adjetivo nenhum.
    if hoje:
        f = f"o preço de hoje é R$ {hoje:.2f}".replace(".", ",")
        return f, ("Preço de hoje: R$ %.2f" % hoje).replace(".", ",")
    return "", ""


def confere(fato_dito: str, frase: str) -> tuple[bool, str]:
    """A frase do modelo pode ir ao ar? (pode, motivo da recusa)

    ⛔ ESTA FUNCAO E' O PONTO DO MODULO, igual a` `nome_produto.confere`. Sem
    ela, "deixar o Gemini escrever o gancho" e' pôr numero que ninguem mediu na
    linha mais visivel do post.
    """
    frase = (frase or "").strip().strip('"').strip()
    if not frase:
        return False, "vazio"
    if len(frase) > 70:
        return False, f"longa demais ({len(frase)})"
    if len(frase) < 12:
        return False, "curta demais"
    sobrando = _numeros(frase) - _numeros(fato_dito)
    if sobrando:
        return False, "numero que nao esta no fato: " + ",".join(sorted(sobrando))
    if chr(10) in frase:
        return False, "mais de uma linha"
    # ⚠️ ADJETIVO DE PROPAGANDA E' RECUSA, e nao so' pedido no prompt. Pedir
    # no texto e conferir no codigo sao coisas diferentes: a primeira e' um
    # desejo, a segunda e' uma garantia.
    baixo = frase.lower()
    for ruim in ("imperdível", "imperdivel", "incrível", "incrivel", "corre",
                 "aproveite", "só hoje", "so hoje", "última chance",
                 "ultima chance", "promoção imperdível"):
        if ruim in baixo:
            return False, f"adjetivo de propaganda: {ruim!r}"
    return True, ""


MODELO_GEMINI = "gemini-3.6-flash"
TEMPO_S = 25
TENTATIVAS_MAX = 3


def _gemini(pedido: str, tentativa: int = 1) -> str | None:
    """A primeira via. None se nao deu — e ai' o ModelScope tenta."""
    import requests

    from . import keys
    try:
        rot = keys.gemini()
    except RuntimeError:
        return None
    if not len(rot):
        return None
    chave = rot.proxima()
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODELO_GEMINI}:generateContent?key={chave.strip()}",
            json={"contents": [{"parts": [{"text": pedido}]}],
                  # ⚠️ TEMPERATURA ACIMA DE ZERO, ao contrario do resto do
                  # motor. Aqui o alvo nao e' a resposta certa (essa e' o FATO,
                  # que ja' esta' decidido) — e' uma frase que nao pareca a
                  # mesma em 150 posts seguidos. O risco que a temperatura
                  # traz e' numero inventado, e esse o `confere` pega.
                  "generationConfig": {"temperature": 0.4}},
            timeout=TEMPO_S)
        # ⚠️ 403 TAMBEM QUEIMA A CHAVE, e nao so' 429 — mesma licao medida em
        # 14/09/2026 no `combina.py`.
        if r.status_code in (403, 429):
            rot.queimar(chave)
            if tentativa >= min(TENTATIVAS_MAX, len(rot)):
                return None
            return _gemini(pedido, tentativa + 1)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        codigo = getattr(getattr(e, "response", None), "status_code", "?")
        print(f"      [!] gancho: gemini falhou ({type(e).__name__} {codigo})")
        return None


def _pedir(fato_dito: str, nome: str) -> str | None:
    """Pede a frase ao modelo. None se nao deu — e ai' vale a deterministica.

    ⚠️ MESMA CASCATA do resto do motor, e na mesma ordem: Gemini, depois
    ModelScope. O OpenRouter fica de fora aqui de proposito — a cota dele e'
    disputada com o corte editorial, que roda dentro do garimpo e NAO tem
    versao deterministica pra cair. Aqui tem.
    """
    from . import modelscope
    pedido = PERGUNTA.format(fato=fato_dito, nome=nome[:90])
    resposta = _gemini(pedido)
    if resposta is None:
        resposta = modelscope.perguntar(pedido, temperatura=0.3)
    if not (resposta or "").strip():
        return None
    return resposta.strip().splitlines()[0]


def de(p: dict, serie: list[float] | None = None,
       com_modelo: bool = True) -> str:
    """O gancho deste produto. Nunca vazio quando ha' preco.

    ⚠️ `com_modelo=False` e' o caminho de teste E o caminho da pressa: a
    versao deterministica ja' e' verdadeira e publicavel. O modelo e' melhora,
    nao dependencia — se ele sumir, o canal continua postando.
    """
    fato_dito, deterministica = fato(p, serie)
    if not fato_dito:
        return ""
    if not com_modelo:
        return deterministica
    frase = _pedir(fato_dito, p.get("nome") or "")
    if frase is None:
        return deterministica
    ok, porque = confere(fato_dito, frase)
    if not ok:
        print(f"      [x] gancho recusado ({porque}): {frase[:60]!r}")
        return deterministica
    return frase


def main() -> None:
    import argparse
    import json
    import sys
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(raiz))
    a = argparse.ArgumentParser(description="o gancho da legenda do canal")
    a.add_argument("--ensaio", action="store_true",
                   help="so' a versao deterministica, sem gastar cota")
    a.add_argument("--quantos", type=int, default=12)
    o = a.parse_args()

    from engine import garimpo, vitrine
    h = garimpo.historico()
    for p in vitrine.pendentes(o.quantos):
        serie = h.get(int(p.get("_id") or 0) or -1, [])
        print(f"  {(p.get('nome') or '')[:52]}")
        print(f"    -> {de(p, serie, com_modelo=not o.ensaio)!r}")


if __name__ == "__main__":
    main()
