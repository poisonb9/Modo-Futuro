# -*- coding: utf-8 -*-
"""Acento que o modelo comeu no titulo — o que da' pra consertar, e o resto.

## O CASO QUE ORIGINOU ISTO

09/09/2026, @semanestesia.pod, na tarja do video E na legenda do post:

    "Por que contratar amigos e um ERRO e usar inimigos FUNCIONA"

O primeiro "e" e' o verbo: tinha de ser "É". Palavras do Bryan: "nao vamos
deletar, mas nao podemos ter esse tipo de erro de gramatica".

⚠️ O ACENTO NAO FOI PERDIDO AQUI DENTRO. Conferido arquivo por arquivo: nada
no caminho do titulo tira acento (as duas funcoes que normalizam para ASCII
sao de HASHTAG e de CHAVE de registro, e nenhuma toca o titulo). O modelo
gerou assim. Ou seja: nao ha' bug pra consertar, ha' saida pra CONFERIR.

## POR QUE ISTO NAO E' UM CORRETOR

Corretor de portugues de verdade decide pelo sentido, e decidir errado num
titulo publicado e' pior que o erro original. Entao aqui sao duas coisas
separadas, de proposito:

    CORRIGE   so' o que NAO EXISTE sem acento. "nao", "voce", "tambem" nao
              sao palavras do portugues — nao ha' o que interpretar.
    AVISA     o resto. "e um" pode ser verbo ("isso É um erro") ou conjuncao
              ("amigos E um inimigo"), e quem sabe qual e' quem le' a frase.

⚠️ A UNICA EXCECAO e' o `e um/uma` seguido de uma palavra de JULGAMENTO
(ERRO, MITO, ARMADILHA...). "contratar amigos e um erro" nao e' lista de duas
coisas — ninguem "contrata amigos e um erro". Nessa forma o "e" e' verbo
sempre, e a lista e' fechada pra ficar assim.
"""
from __future__ import annotations

import re

# Palavras que NAO EXISTEM em portugues sem o acento. Corrigir e' seguro
# porque nao ha' segunda leitura possivel.
#
# ⚠️ FICAM DE FORA de proposito: "so" (e' palavra em ingles, e titulo cita
# nome estrangeiro), "esta"/"e"/"a"/"para" (existem sem acento com OUTRO
# sentido) e qualquer palavra em que a forma sem acento seja legitima.
SEM_ACENTO_NAO_EXISTE = {
    "nao": "não", "voce": "você", "voces": "vocês", "tambem": "também",
    "entao": "então", "alem": "além", "apos": "após", "atraves": "através",
    "ninguem": "ninguém", "alguem": "alguém", "porem": "porém",
    "dificil": "difícil", "facil": "fácil", "possivel": "possível",
    "impossivel": "impossível", "historia": "história", "memoria": "memória",
    "video": "vídeo", "videos": "vídeos", "musica": "música",
    "publico": "público", "unico": "único", "unica": "única",
    "ultimo": "último", "ultima": "última", "proprio": "próprio",
    "propria": "própria", "familia": "família", "milhoes": "milhões",
    "bilhoes": "bilhões", "questao": "questão", "razao": "razão",
    "decisao": "decisão", "atencao": "atenção", "informacao": "informação",
    "ilusao": "ilusão", "tres": "três", "mes": "mês", "seculo": "século",
    "medico": "médico", "pratica": "prática", "logica": "lógica",
    "estrategia": "estratégia", "experiencia": "experiência",
    "consequencia": "consequência", "ciencia": "ciência",
    "inteligencia": "inteligência", "diferenca": "diferença",
    # ⚠️ A FAMILIA DO TIL, acrescentada em 09/09/2026 depois do segundo caso
    # no mesmo dia: "Sabae de IRMA MAIS VELHA" no @achadinho.make. O modelo
    # perde o til com mais frequencia em CAIXA ALTA, e nenhuma destas existe
    # sem ele.
    "irma": "irmã", "irmas": "irmãs", "irmao": "irmão", "irmaos": "irmãos",
    "mae": "mãe", "maes": "mães", "manha": "manhã", "amanha": "amanhã",
    "coracao": "coração", "opiniao": "opinião", "reuniao": "reunião",
    "versao": "versão", "missao": "missão", "visao": "visão",
    "pressao": "pressão", "explicacao": "explicação",
    "situacao": "situação", "condicao": "condição", "relacao": "relação",
    "geracao": "geração", "criacao": "criação", "producao": "produção",
    "reacao": "reação", "solucao": "solução", "intencao": "intenção",
    "obsessao": "obsessão", "expressao": "expressão", "licao": "lição",
    "traicao": "traição", "ambicao": "ambição", "aviao": "avião",
    "orgao": "órgão", "orfao": "órfão", "cristao": "cristão",
    "alemao": "alemão", "capitao": "capitão", "campeao": "campeão",
    "campeoes": "campeões", "padrao": "padrão", "sertao": "sertão",
    "reflexao": "reflexão", "obrigacao": "obrigação", "punicao": "punição",
}

# Palavras de JULGAMENTO: depois de "e um/uma", o "e" e' verbo, nunca
# conjuncao. Ninguem "contrata amigos e um erro".
JULGAMENTO = {
    "erro", "mito", "armadilha", "ilusão", "ilusao", "problema", "golpe",
    "desperdício", "desperdicio", "risco", "sinal", "fracasso", "engano",
    "cilada", "furada", "burrice", "perda", "veneno", "vício", "vicio",
    "luxo", "privilégio", "privilegio", "milagre", "absurdo",
}

# ⚠️ O PRECO DESTA LISTA, dito na cara: nome proprio estrangeiro que coincida
# com uma delas vira palavra portuguesa. "Irma Vep" (o filme) sairia "Irmã
# Vep". Aceito de propósito — em titulo pt-BR "irmã" aparece muitas ordens de
# grandeza mais que o nome "Irma", e o caso que foi ao ar era o primeiro. Se
# um canal passar a falar de alguem chamado Irma, tire a linha; o teste tem o
# caso marcado.


_PALAVRA = re.compile(r"[A-Za-zÀ-ÿ]+")
_E_UM = re.compile(r"\b([Ee])\s+(um|uma)\s+([A-Za-zÀ-ÿ]+)")


def _troca_preservando_caixa(original: str, correta: str) -> str:
    if original.isupper():
        return correta.upper()
    if original[:1].isupper():
        return correta[:1].upper() + correta[1:]
    return correta


def corrigir(texto: str) -> str:
    """Devolve o texto com os acentos que NAO tem segunda leitura.

    ⚠️ Preserva a caixa: o motor usa CAIXA ALTA pra enfase no titulo, e
    devolver "não" onde estava "NAO" estragaria o desenho da tarja.
    """
    if not texto:
        return texto

    def _troca(m: re.Match) -> str:
        p = m.group(0)
        certa = SEM_ACENTO_NAO_EXISTE.get(p.lower())
        return _troca_preservando_caixa(p, certa) if certa else p

    texto = _PALAVRA.sub(_troca, texto)

    def _verbo(m: re.Match) -> str:
        e, artigo, palavra = m.group(1), m.group(2), m.group(3)
        if palavra.lower() not in JULGAMENTO:
            return m.group(0)
        return f"{'É' if e.isupper() else 'é'} {artigo} {palavra}"

    return _E_UM.sub(_verbo, texto)


def suspeitas(texto: str) -> list[str]:
    """O que eu NAO conserto, e alguem tem de olhar.

    ⚠️ Existe pra o caso duvidoso nao passar calado. Um corretor que so'
    conserta o obvio e fica quieto no resto da a impressao de que o resto
    esta' certo.
    """
    achados = []
    for m in _E_UM.finditer(texto or ""):
        if m.group(3).lower() not in JULGAMENTO:
            achados.append(
                f'"{m.group(0)}" — se o "e" for verbo, falta o acento (É)')
    return achados
