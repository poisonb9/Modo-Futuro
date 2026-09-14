# -*- coding: utf-8 -*-
"""O nome do produto, escrito para GENTE.

    python -m engine.nome_produto --ensaio      mostra o que faria
    python -m engine.nome_produto               reescreve e grava o cache

## O QUE ISTO RESOLVE

MEDIDO em 14/09/2026, nos 25 produtos que estavam na pagina: **25 de 25**
titulos cortados no meio da palavra, 90 caracteres de media (o teto do
registro), 17 deles sao lista de palavra-chave separada por virgula.

    Luvas de boxe para criancas, luvas de boxe pu, protetor de mao para
    musculacao, treinament

Isso e' o titulo que o vendedor escreve pro BUSCADOR do AliExpress, nao pra
uma pessoa. Nenhum outro detalhe da pagina grita "site de afiliado" tao alto.

⭐ E o nome limpo nao serve so' a` pagina: serve ao Telegram, a` legenda do
clipe e ao titulo do video. Um trabalho, quatro lugares.

## ⚠️ A REGRA QUE SUSTENTA ISTO

**Todo numero do nome novo tem de existir no original.** Modelo reescrevendo
titulo inventa quantidade ("7 pecas" quando sao 18) e atributo ("a` prova
d'agua" quando nao e'), e essas duas mentiras chegam no cliente como promessa
de quem vendeu.

⚠️ FALHA FECHADA: nome que nao passa na conferencia e' DESCARTADO e o produto
fica com o corte do titulo original. Pior nome, zero mentira — mesma regra do
desconto, que e' zero quando nao ha' historico nosso.

## ⚠️ E O CACHE E' O PRODUTO DESTE MODULO

O nome sai do modelo UMA vez e fica gravado por id. Sem cache, toda publicacao
gastaria cota de novo e — pior — o mesmo produto teria nome diferente a cada
rodada, o que quebra a dedup por nome e confunde quem viu o clipe ontem.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLICADOS = RAIZ / "estado" / "produtos_publicados.jsonl"
CACHE = RAIZ / "estado" / "nomes_curtos.json"

# ⚠️ O MESMO MODELO DO CORTE EDITORIAL, e pelo mesmo motivo: ja' ha' medicao
# dele, e reescrever titulo curto nao pede modelo grande. Ver
# engine/rende_video.py, que documenta o rodizio das 14 chaves gratis.
MODELO = "nvidia/nemotron-3.5-lightning:free"
TEMPO_S = 30
TENTATIVAS_MAX = 3
POR_LOTE = 12

LIMITE = 46          # cabe em duas linhas do cartao, no celular
MINIMO = 8

PERGUNTA = """Reescreva cada titulo de produto do AliExpress como uma pessoa
falaria, em portugues do Brasil.

REGRAS:
- no maximo 46 caracteres
- diga O QUE E' e o que tem de util, nada mais
- NAO invente numero, medida, marca ou caracteristica que nao esteja no titulo
- NAO use adjetivo de propaganda ("incrivel", "imperdivel", "top")
- sem virgula listando palavra-chave

Responda SO' uma linha por produto, no formato:
<numero>|<nome novo>

Titulos:
"""


def _numeros(t: str) -> set[str]:
    """Os numeros do texto, sem pontuacao de milhar."""
    return set(re.findall(r"\d+", t.replace(".", "").replace(",", "")))


def _palavras(t: str) -> set[str]:
    return {p for p in re.findall(r"[a-zA-ZÀ-ÿ]{4,}", t.lower())}


def cortar(titulo: str, limite: int = LIMITE) -> str:
    """O nome de reserva: o titulo original, cortado onde ele para de nomear.

    ⚠️ A primeira virgula (ou dois-pontos) e' onde o vendedor chines termina o
    nome e comeca a listar palavra-chave. Cortar ali devolve o nome de verdade
    na maioria dos casos, sem modelo nenhum.
    """
    n = (titulo or "").split(",")[0].split(":")[0].strip()
    if len(n) > limite:
        n = n[:limite - 1].rsplit(" ", 1)[0].strip() + "…"
    return n


def confere(original: str, novo: str) -> tuple[bool, str]:
    """O nome novo pode ir pro ar? (pode, motivo da recusa)

    ⚠️ ESTA FUNCAO E' O PONTO DO MODULO. Sem ela, "reescrever com IA" e'
    exatamente o que a operacao passou a sessao inteira evitando: numero que
    ninguem mediu chegando ao cliente como promessa.
    """
    novo = (novo or "").strip()
    if not novo:
        return False, "vazio"
    if len(novo) > LIMITE:
        return False, f"longo demais ({len(novo)})"
    if len(novo) < MINIMO:
        return False, "curto demais"
    # ⚠️ NUMERO INVENTADO E' O DEFEITO MAIS PROVAVEL e o mais caro: "7 pecas"
    # quando sao 18 vira reclamacao de quem comprou.
    sobrando = _numeros(novo) - _numeros(original)
    if sobrando:
        return False, "numero que nao existe no original: " + ",".join(sorted(sobrando))
    # ⚠️ E O NOME TEM DE FALAR DO MESMO PRODUTO. Sem isto, o modelo podia
    # devolver "Kit de beleza" pra uma luva de treino e passar em tudo acima.
    if not (_palavras(novo) & _palavras(original)):
        return False, "nao compartilha palavra com o original"
    if novo.rstrip().endswith((",", "…", "-")):
        return False, "termina cortado"
    return True, ""


def _pedir(titulos: list[str], tentativa: int = 1) -> dict[int, str] | None:
    """Manda o lote pro modelo. None se nao deu — e ai' cai no `cortar`."""
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
                  "messages": [{"role": "user", "content": PERGUNTA + lista}]},
            timeout=TEMPO_S)
        if r.status_code in (402, 429):
            # mesma licao do rende_video: queima a chave e tenta a proxima
            rot.queimar(chave)
            if tentativa >= min(TENTATIVAS_MAX, len(rot)):
                return None
            return _pedir(titulos, tentativa + 1)
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [!] modelo falhou ({type(e).__name__}) — usando o corte")
        return None

    saida: dict[int, str] = {}
    for linha in texto.splitlines():
        partes = [x.strip() for x in linha.split("|")]
        if len(partes) < 2 or not partes[0].rstrip(".").isdigit():
            continue
        i = int(partes[0].rstrip(".")) - 1
        if 0 <= i < len(titulos):
            saida[i] = partes[1]
    return saida


def humanizar(titulos: list[str]) -> dict[str, str]:
    """{titulo original: nome curto} — so' os que passaram na conferencia."""
    bons: dict[str, str] = {}
    for i in range(0, len(titulos), POR_LOTE):
        lote = titulos[i:i + POR_LOTE]
        resposta = _pedir(lote)
        if not resposta:
            continue
        for j, novo in resposta.items():
            ok, porque = confere(lote[j], novo)
            if ok:
                bons[lote[j]] = novo
            else:
                print(f"  [x] recusado ({porque}): {novo[:50]!r}")
    return bons


def ler_cache() -> dict[str, str]:
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def nome_de(produto: dict) -> str:
    """O nome que vai pro ar: o curto se existir, senao o corte do original."""
    cache = ler_cache()
    original = produto.get("nome") or ""
    chave = str(produto.get("id") or original)
    return cache.get(chave) or cortar(original)


def main() -> None:
    a = argparse.ArgumentParser(description="nomes de produto para gente")
    a.add_argument("--ensaio", action="store_true",
                   help="mostra o que faria, nao grava")
    o = a.parse_args()

    if not PUBLICADOS.exists():
        raise SystemExit("nao ha produtos publicados ainda")
    vistos, produtos = set(), []
    for linha in PUBLICADOS.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        chave = str(d.get("id") or d.get("nome"))
        if not d.get("nome") or chave in vistos:
            continue
        vistos.add(chave)
        produtos.append((chave, d["nome"]))

    cache = ler_cache()
    faltam = [(c, n) for c, n in produtos if c not in cache]
    print(f"{len(produtos)} produtos, {len(cache)} ja' nomeados, "
          f"{len(faltam)} pra fazer")
    if not faltam:
        return

    bons = humanizar([n for _, n in faltam])
    novos = 0
    for chave, original in faltam:
        if original in bons:
            cache[chave] = bons[original]
            novos += 1
            print(f"  {original[:44]}")
            print(f"    -> {bons[original]}")
        else:
            print(f"  (reserva) {cortar(original)}")

    if o.ensaio:
        print(f"\n[ensaio] {novos} nome(s) — nada gravado.")
        return
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    print(f"\n{novos} nome(s) novo(s) — cache com {len(cache)}.")


if __name__ == "__main__":
    main()
