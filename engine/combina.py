# -*- coding: utf-8 -*-
"""Quais produtos COMBINAM entre si — julgado por modelo, guardado em cache.

    python -m engine.combina --ensaio     mostra os pares, nao grava
    python -m engine.combina              grava estado/combinacoes.json

## POR QUE ISTO EXISTE

O upsell do site mae escolhia o complemento por sobreposicao de palavras
(Jaccard). Isso separa "mesmo produto" de "produto diferente" — e so'. Ele nao
sabe que **esponja combina com base**, que **pote combina com descascador**, e
que **corda de pular NAO combina com luva de boxe** (as duas sao treino, mas
quem compra uma nao quer a outra hoje).

⭐ Pedido do Bryan em 14/09/2026: *"se voce ficar na duvida de qual produto bate
com qual podemos usar o gemini para avaliar"*.

## ⚠️ O QUE ESTE MODULO **NAO** PODE FAZER

**Nao pode sugerir substituto.** Complemento e' o que se usa JUNTO; substituto
e' a mesma coisa com outro nome, e sugerir substituto faz a pessoa reconsiderar
a compra que ela ja' tinha decidido — tira venda em vez de somar.

⚠️ FALHA FECHADA: par que o modelo nao devolver, ou que nao passar na
conferencia, simplesmente NAO vira sugestao. A pagina cai na regra de palavras,
que e' pior mas e' conhecida — nunca em "sugere qualquer coisa".

## ⚠️ E O CACHE E' POR PAR, NAO POR RODADA

Produto novo entra e o modulo julga SO' ele contra os que ja' existem. Sem
isso, cada publicacao gastaria cota pra reconfirmar o que ja' se sabe — e o
mesmo par poderia receber respostas diferentes em dias diferentes, fazendo a
vitrine mudar de opiniao sozinha.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "estado" / "combinacoes.json"

MODELO_GEMINI = "gemini-3.6-flash"
TEMPO_S = 45
TENTATIVAS_MAX = 8
# ⚠️ Um produto por chamada, com ate' 24 candidatos na lista. Mandar todos
# contra todos seria N^2 e nao cabe em nenhuma cota.
CANDIDATOS_MAX = 24

PERGUNTA = """Você organiza uma vitrine de achadinhos brasileira.

O CLIENTE JÁ ESCOLHEU este produto:
{base}

Dos produtos abaixo, diga quais são COMPLEMENTARES a ele — coisas que a pessoa
usaria JUNTO com o que ela escolheu, ou que fazem sentido na mesma compra.

NÃO são complementares:
- o mesmo produto com outro nome (substituto)
- outra versão/marca da mesma coisa
- algo que resolve o mesmo problema

Responda SÓ os números dos complementares, separados por vírgula, do melhor
para o pior. Se nenhum combinar, responda: nenhum

Produtos:
{lista}
"""


def _ler(arq: Path) -> dict:
    if not arq.exists():
        return {}
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def ler_cache() -> dict:
    return _ler(CACHE)


def _pedir(base: str, candidatos: list[str], tentativa: int = 1) -> list[int] | None:
    """Os indices (1-based) que o modelo considerou complementares."""
    import requests

    from . import keys

    rot = keys.gemini()
    if not len(rot):
        return None
    lista = chr(10).join(f"{i+1}. {t[:90]}" for i, t in enumerate(candidatos))
    chave = rot.proxima()
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODELO_GEMINI}:generateContent?key={chave.strip()}",
            json={"contents": [{"parts": [{"text": PERGUNTA.format(
                base=base[:110], lista=lista)}]}],
                "generationConfig": {"temperature": 0}},
            timeout=TEMPO_S)
        # ⚠️ 403 TAMBEM QUEIMA A CHAVE, e nao so' 429.
        #
        # MEDIDO em 14/09/2026: com 28 chaves no anel, uma rodada inteira
        # morreu em 403 (PERMISSION_DENIED — chave revogada ou sem a API
        # ligada), enquanto MINUTOS ANTES outras chaves do mesmo anel tinham
        # respondido 200. Tratar so' 429 como 'chave ruim' fazia o modulo
        # desistir na primeira recusada em vez de andar pro proximo slot.
        if r.status_code in (403, 429):
            rot.queimar(chave)
            if tentativa >= min(TENTATIVAS_MAX, len(rot)):
                return None
            return _pedir(base, candidatos, tentativa + 1)
        r.raise_for_status()
        texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        # ⚠️ O NOME DA EXCECAO NAO BASTA. "HTTPError" pode ser cota (429),
        # sobrecarga (503) ou prompt recusado (400) — e a decisao de esperar
        # ou consertar depende disso. Medido em 14/09/2026: perdi uma rodada
        # inteira sem saber qual dos tres era.
        codigo = getattr(getattr(e, "response", None), "status_code", "?")
        print(f"  [!] gemini falhou ({type(e).__name__} {codigo})")
        return None

    if "nenhum" in texto.lower():
        return []
    # ⚠️ SO' NUMERO QUE EXISTE NA LISTA. O modelo as vezes devolve "1, 4, 9"
    # quando so' havia 6 candidatos — indice inventado viraria produto errado.
    achados = []
    for n in re.findall(r"\d+", texto):
        i = int(n)
        if 1 <= i <= len(candidatos) and i not in achados:
            achados.append(i)
    return achados


def julgar(produtos: list[dict], so_faltantes: bool = True,
           gravando: bool = True) -> dict:
    """{id do produto: [ids que combinam]} — acrescenta ao cache."""
    cache = ler_cache()
    for p in produtos:
        chave = str(p.get("id") or p.get("nome"))
        if so_faltantes and chave in cache:
            continue
        outros = [o for o in produtos
                  if str(o.get("id") or o.get("nome")) != chave][:CANDIDATOS_MAX]
        if not outros:
            continue
        indices = _pedir(p.get("nome") or "", [o.get("nome") or "" for o in outros])
        if indices is None:
            print(f"  (sem resposta) {(p.get('nome') or '')[:44]}")
            continue
        cache[chave] = [str(outros[i - 1].get("id") or outros[i - 1].get("nome"))
                        for i in indices]
        # ⚠️ GRAVA A CADA ACERTO. A primeira versao so' gravava no fim, e uma
        # rodada que morreu de cota no meio jogou fora TUDO o que ja' tinha
        # sido pago — inclusive o que o ensaio anterior tinha acabado de
        # descobrir.
        if gravando:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2)
                             + chr(10), encoding="utf-8")
        nomes = ", ".join((outros[i - 1].get("nome") or "")[:26] for i in indices[:3])
        print(f"  {(p.get('nome') or '')[:40]}")
        print(f"    combina com: {nomes or '(nada)'}")
    return cache


def main() -> None:
    import sys

    a = argparse.ArgumentParser(description="quais produtos combinam entre si")
    a.add_argument("--ensaio", action="store_true", help="nao grava")
    o = a.parse_args()

    sys.path.insert(0, str(RAIZ / "paginas"))
    sys.path.insert(0, str(RAIZ))
    import publicar_bio as pb

    produtos = pb.produtos_todos()
    cache_antes = ler_cache()
    print(f"{len(produtos)} produtos, {len(cache_antes)} ja' julgados")
    cache = julgar(produtos, gravando=not o.ensaio)
    novos = len(cache) - len(cache_antes)

    if o.ensaio:
        print(f"[ensaio] {novos} produto(s) julgado(s) — nada gravado.")
        return
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + chr(10),
                     encoding="utf-8")
    print(f"{novos} novo(s) — cache com {len(cache)} produto(s).")


if __name__ == "__main__":
    main()
