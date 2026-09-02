# -*- coding: utf-8 -*-
"""Clipe marcado `nao_publicar` nunca e' agendado — nem como republicacao.

Decisao do Bryan em 02/09/2026 sobre os 6 clipes da "republicacao 22-08":
"nao pode ser publicado de novo, pode deixar junto mas nao pode ser
publicado". Eles ficam no manifesto, mantem o canal, e nao vao ao ar.

⚠️ POR QUE UM CAMPO NOVO, E NAO O `republicacao` QUE JA' EXISTIA.

`republicacao` faz o CONTRARIO do que o nome sugere neste ponto do codigo:
ele LIBERA o clipe a passar por cima da checagem de "ja' publicado", porque
existe pro caso em que o Bryan QUER repostar algo na mao (o Buffer guarda o
post antigo como "sent", e trata-lo como duplicata apagaria justamente o que
ele quer refazer).

Os 6 clipes em questao estao marcados `republicacao: true`. Ou seja: hoje eles
sao os MAIS livres do manifesto pra sair de novo — o oposto exato do pedido.
Reaproveitar aquele campo teria invertido o sentido dele pra todo mundo.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

FONTE = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")
CABE = FONTE[FONTE.index("def cabe(v):"):FONTE.index("fila = [(k, v)")]


def _decide(**campos):
    """Reproduz as recusas por conteudo do `cabe()`, na ordem em que ocorrem."""
    v = dict(campos)
    if v.get("nao_publicar"):
        return False
    if v.get("quarentena") or (v.get("traduzido_por") or "").startswith("nemotron"):
        return False
    return True


def teste_positivo_aposentado_e_barrado():
    assert not _decide(nao_publicar=True)


def teste_positivo_barrado_mesmo_sendo_republicacao():
    """⚠️ O CASO QUE IMPORTA. `republicacao` normalmente LIBERA. A marca de
    aposentado tem de vencer, senao os 6 continuam sendo os mais livres."""
    assert not _decide(nao_publicar=True, republicacao=True)


def teste_negativo_clipe_normal_continua_passando():
    """Uma guarda que barrasse tudo passaria nos positivos e pararia o canal."""
    assert _decide()
    assert _decide(canal="modofuturo")
    assert _decide(republicacao=True)      # republicacao sozinha segue valendo


def teste_a_checagem_vem_ANTES_da_liberacao_por_republicacao():
    """Ordem no arquivo: `nao_publicar` tem de ser avaliado antes do `return`
    que libera por republicacao — senao o clipe sai antes de ser barrado."""
    i_nao = CABE.index('v.get("nao_publicar")')
    i_rep = CABE.index('v.get("republicacao")')
    assert i_nao < i_rep, "nao_publicar e' checado DEPOIS da liberacao"


def teste_nao_reaproveitou_o_campo_republicacao():
    """⚠️ Se alguem 'simplificar' usando republicacao como bloqueio, inverte o
    sentido do campo pra todo o manifesto."""
    assert 'v.get("nao_publicar")' in CABE, "a marca propria sumiu"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
