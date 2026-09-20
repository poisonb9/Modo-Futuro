# -*- coding: utf-8 -*-
"""Reescrita RESTRITA do titulo do produto: limpa, nunca inventa.

Pedido do Bryan (20/09/2026): "pode rodar no gemini um titulo ideal ou
perfeito de acordo com o acervo para cada produto que seja extremamente
vendavel" — e, depois de eu expor o risco, ele escolheu: "quero a reescrita
restrita".

⛔ POR QUE RESTRITA, E NAO "VENDAVEL". O acervo do projeto prescreve copy
vinda de FONTE: "ler as avaliacoes do AliExpress pra achar beneficios antes
da copy ... uma linha de beneficio por produto, vinda das avaliacoes, NAO DA
CABECA" (DEMONSTRADO). E a secao 4 recusa explicitamente gatilho de urgencia
e escassez no titulo, porque contradizem a regua de sinais medidos.
Um modelo solto faz o que modelo faz: "Limpa vidro carro com cabo longo e
escova" vira "Limpa-vidros PROFISSIONAL com cabo TELESCOPICO e escova de
MICROFIBRA" — tres atributos que ninguem verificou. O site inteiro se apoia
em nao mentir sobre preco; mentir sobre o produto queima o mesmo ativo.

O QUE E' PERMITIDO: cortar palavra repetida, reordenar, consertar a traducao
de maquina, pontuar. O QUE NAO E': acrescentar substantivo, material, uso,
medida ou superlativo que nao esteja no titulo de origem.

⭐ E A REGRA NAO E' CONFIANCA, E' GUARDA: `so_reordena()` compara palavra por
palavra e RECUSA o titulo novo se aparecer palavra sem raiz no original. Sem
essa guarda, "restrita" seria so' uma frase simpatica dentro do prompt.
"""
from __future__ import annotations

import re
import unicodedata

from . import modelo_texto

# palavras de ligacao entram e saem a vontade: nao carregam atributo
LIGACAO = {
    "a", "as", "ao", "aos", "o", "os", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "com", "sem", "para", "pra", "por", "e", "ou", "que", "the", "of",
}

PROMPT = """Voce limpa titulos de produto de marketplace para uma vitrine.

TITULO DE ORIGEM:
{titulo}

REGRAS ABSOLUTAS:
1. Use SOMENTE palavras cujo sentido ja' esta' no titulo de origem.
2. NAO acrescente material, medida, uso, marca, publico nem superlativo.
   Nada de "profissional", "premium", "resistente", "ideal para", "ajustavel"
   se a palavra nao estiver na origem.
3. Pode: cortar repeticao, reordenar, corrigir a traducao de maquina,
   ajustar concordancia e pontuar.
4. No maximo 8 palavras. Comece pelo SUBSTANTIVO do produto.
5. PRESERVE EXATAMENTE a caixa das palavras da origem: marca, modelo e sigla
   continuam como estao (8BitDo, Xbox, RGB, TWS, Lenovo, Wi-Fi). NAO passe
   nada para minusculo.

Responda APENAS com o titulo limpo, em uma linha, sem aspas nem explicacao."""


def _normalizar(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def _palavras(t: str) -> list[str]:
    return [p for p in _normalizar(t).split() if p]


def _tem_raiz(palavra: str, originais: list[str]) -> bool:
    """A palavra existe no original, tolerando plural e genero.

    ⚠️ Raiz de 4 letras, nao igualdade: "escovas" tem de casar com "escova",
    "telescopico" com "telescopica". Palavra de 3 letras ou menos exige
    igualdade — em palavra curta, 4 letras de raiz nao sobram e qualquer
    coisa casaria com qualquer coisa.
    """
    if palavra in LIGACAO:
        return True
    if len(palavra) <= 3:
        return palavra in originais
    raiz = palavra[:4]
    return any(o.startswith(raiz) or palavra.startswith(o[:4]) for o in originais
               if len(o) > 3)


def so_reordena(origem: str, novo: str) -> tuple[bool, str]:
    """(aceita, motivo). A guarda: nada de palavra que nao veio da origem."""
    if not novo or not novo.strip():
        return False, "vazio"
    orig = _palavras(origem)
    novas = _palavras(novo)
    if not novas:
        return False, "sem palavras"
    if len(novas) > 8:
        return False, f"{len(novas)} palavras (teto 8)"
    if len(novo) > len(origem) + 2:
        return False, "ficou mais longo que a origem"
    inventadas = [p for p in novas if not _tem_raiz(p, orig)]
    if inventadas:
        return False, "palavra inventada: " + ", ".join(inventadas)
    # ⛔ CAIXA E' CONTEUDO EM MARCA E SIGLA. MEDIDO na primeira amostra real
    # (20/09): das 3 mudancas que o modelo fez, DUAS foram estragos — "8BitDo
    # Ultimate C para Xbox com RGB" virou "8bitdo ultimate c para xbox com
    # rgb", e "Lenovo LP40" virou "lenovo lp40". A culpa era do meu prompt,
    # que mandava "resto minusculo". Prompt corrigido, e a guarda fica: se a
    # origem tinha maiuscula no meio da palavra ou palavra toda maiuscula, o
    # novo tem de manter.
    def _marcas(t):
        return {p for p in re.findall(r"[A-Za-z0-9-]+", t or "")
                if (p.isupper() and len(p) > 1) or (p[:1].isupper() and any(c.isupper() for c in p[1:]))}
    perdidas = sorted(m for m in _marcas(origem)
                      if m not in novo and _normalizar(m).strip() in _palavras(novo))
    if perdidas:
        return False, "caixa perdida em: " + ", ".join(perdidas)
    return True, "ok"


def limpar(titulo: str) -> tuple[str, str]:
    """(titulo final, motivo). Na duvida devolve a ORIGEM — sem modelo, ou
    com modelo inventando, o produto continua tendo nome."""
    origem = (titulo or "").strip()
    if not origem:
        return origem, "origem vazia"
    resposta = modelo_texto.perguntar(PROMPT.format(titulo=origem))
    if not resposta:
        return origem, "modelo nao respondeu"
    novo = resposta.strip().strip('"').strip("'").split("\n")[0].strip()
    ok, motivo = so_reordena(origem, novo)
    if not ok:
        return origem, "RECUSADO (" + motivo + ")"
    return novo, "ok"
