# -*- coding: utf-8 -*-
"""Transforma uma lista de produtos no roteiro falado do video.

E' a peca entre o radar (que traz os produtos) e a montagem (que precisa de
uma frase por cena, com a duracao de cada uma).

## ⚠️ A REGRA QUE MANDA EM TUDO AQUI: NAO INVENTAR

Nao temos o produto na mao. Nunca usamos, nunca testamos, nao sabemos se dura,
se e' macio, se vale a pena. Toda frase sai do que o ANUNCIO diz — titulo,
preco, categoria — e nada alem.

Isso nao e' escrupulo abstrato: afirmar qualidade de produto que nunca vimos
e' propaganda enganosa, cai sobre a conta que precisa estar limpa pro TikTok
Shop, e destroi a unica coisa que um canal de achados tem pra vender, que e'
a confianca de quem assiste.

O prompt proibe explicitamente adjetivo de qualidade e promessa de resultado.

## ⚠️ O GANCHO VIVE NOS 2 PRIMEIROS SEGUNDOS

Retencao e' o gargalo MEDIDO deste projeto — a audiencia sai em 0:02. Por isso
a abertura e' curta e concreta, e o preco entra CEDO: preco e' o que segura
quem esta' passando o dedo, nao a descricao do produto.

## ⚠️ CADA FRASE VIRA UMA CENA

O roteiro devolve UMA frase por produto. A `montagem` usa a duracao da fala
pra dimensionar a cena — entao frase gigante vira cena de 9 segundos com foto
parada, e frase de tres palavras vira corte seco. O prompt pede frases de
tamanho parecido pela mesma razao.
"""
from __future__ import annotations

import json
import re

PROMPT_ROTEIRO = """Voce escreve a narracao de um video curto de "achados" para
TikTok, em portugues do Brasil, sobre os produtos listados abaixo.

REGRA MAIS IMPORTANTE — NAO INVENTE NADA.
Quem escreve NAO tem o produto e NUNCA o usou. Voce so' sabe o que esta na
lista: nome, preco e categoria. E PROIBIDO:
  - dizer que e' bom, otimo, resistente, durvel, macio, potente, de qualidade;
  - prometer resultado ("vai mudar sua rotina", "resolve de vez");
  - inventar material, tamanho, tempo de bateria, rendimento;
  - comparar com marca famosa;
  - dizer que voce testou, usou, recomenda ou aprova.
Se o titulo do anuncio nao disser, voce nao sabe. Fale do que o produto SERVE
(a funcao, que esta no proprio nome) e do PRECO.

FORMATO
Uma frase por produto, na ordem em que aparecem. Cada frase:
  - entre 12 e 22 palavras — frases de tamanhos parecidos entre si;
  - diz PRA QUE serve e QUANTO custa;
  - linguagem falada, sem ponto de exclamacao, sem emoji, sem hashtag.

Alem das frases dos produtos, escreva:
  - "abertura": UMA frase de ate 12 palavras que prende nos 2 primeiros
    segundos. Concreta, sem promessa. Pode citar a faixa de preco.
  - "fechamento": UMA frase de ate 10 palavras dizendo que o link esta na
    bio. Sem pedir like nem seguir.

Responda SOMENTE com JSON valido, sem markdown:
{{"abertura": "<frase>", "produtos": ["<frase 1>", "<frase 2>", ...],
  "fechamento": "<frase>"}}

PRODUTOS:
{texto}"""


def _lista_para_texto(produtos: list[dict]) -> str:
    linhas = []
    for i, p in enumerate(produtos, 1):
        linhas.append(
            f"{i}. {str(p.get('titulo') or '').strip()}"
            f" | preco: {str(p.get('preco') or 'nao informado').strip()}"
            f" | categoria: {str(p.get('categoria') or 'nao informada').strip()}")
    return "\n".join(linhas)


def _limpar(t: str) -> str:
    return re.sub(r"^```(?:json)?|```$", "", (t or "").strip(),
                  flags=re.M).strip()


def gerar(produtos: list[dict]) -> dict:
    """`{"abertura", "produtos": [...], "fechamento"}` — ou `{}` se nao der.

    ⚠️ NUNCA LEVANTA. Sem roteiro nao ha' video, mas derrubar o processo aqui
    perderia tambem os produtos ja' coletados. Quem chama decide se segue sem.
    """
    if not produtos:
        return {}
    from . import traducao
    try:
        bruto = traducao._traduzir_texto(
            _lista_para_texto(produtos), prompt=PROMPT_ROTEIRO)
        d = json.loads(_limpar(bruto))
    except Exception as e:
        print(f"   [!] roteiro nao gerado ({str(e)[:70]})", flush=True)
        return {}

    frases = [str(x).strip() for x in (d.get("produtos") or []) if str(x).strip()]
    # ⚠️ O MODELO PODE DEVOLVER MENOS FRASES QUE PRODUTOS. Se isso passar, a
    # cena 3 recebe a fala do produto 2 e o video anuncia o preco errado — o
    # tipo de erro que ninguem percebe revisando o texto, so' assistindo.
    if len(frases) != len(produtos):
        print(f"   [!] roteiro com {len(frases)} frase(s) para "
              f"{len(produtos)} produto(s) — descartado", flush=True)
        return {}
    return {"abertura": str(d.get("abertura") or "").strip(),
            "produtos": frases,
            "fechamento": str(d.get("fechamento") or "").strip()}


def em_frases(roteiro: dict) -> list[str]:
    """O roteiro na ordem em que sera' falado."""
    if not roteiro:
        return []
    return [f for f in ([roteiro.get("abertura")]
                        + list(roteiro.get("produtos") or [])
                        + [roteiro.get("fechamento")]) if f]


# Palavras que denunciam afirmacao sobre produto que nao temos.
#
# ⚠️ E' REDE DE SEGURANCA, NAO O CONTROLE PRINCIPAL. O prompt e' quem deve
# evitar; esta lista pega o que escapar. Uma lista de palavras nunca cobre
# todas as formas de afirmar qualidade — serve pra transformar o descuido
# comum em erro visivel, nao pra garantir que nao ha' nenhum.
SUSPEITAS = (
    "excelente", "otimo", "ótimo", "melhor", "incrivel", "incrível",
    "durav", "durável", "resistente", "de qualidade", "top de linha",
    "eu testei", "eu usei", "recomendo", "aprovado por mim",
    "vai mudar", "resolve de vez", "nunca mais",
)


def alertas(roteiro: dict) -> list[str]:
    """Frases que afirmam algo que nao sabemos. Vazio = nada suspeito."""
    achados = []
    for f in em_frases(roteiro):
        b = f.lower()
        for s in SUSPEITAS:
            if s in b:
                achados.append(f"{s!r} em: {f[:60]}")
                break
    return achados
