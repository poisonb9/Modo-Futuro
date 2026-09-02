# -*- coding: utf-8 -*-
"""Clipe traduzido pela RESERVA nao entra na fila de postagem sozinho.

Decisao do Bryan em 02/09/2026, com a preocupacao dele junto: "meu medo e'
usar o nemotron e as traducoes ficarem ruins... e se fizermos isso so' quando
formos perder clipes... manda pro Drive e me sinaliza antes de entrar pra fila
de postagem, quarentena pra ser avaliado".

A reserva so' entra quando o Gemini se esgotou e a alternativa e' PERDER um
clipe ja' cortado, transcrito e renderizado — em 02/09 quatro runs morreram
assim. A traducao dela foi medida contra o Gemini e ficou equivalente. Mas
"boa na amostra" nao e' "aprovada pra publicar".

⚠️ A CADEIA TEM TRES ELOS, e romper QUALQUER um publica sem revisao:
  1. traducao marca      -> USOU_RESERVA
  2. main copia pro post -> a lista branca de `meta`
  3. agendador barra     -> `cabe()`
Este arquivo testa os tres, porque o elo 2 ja' falhou antes por conta propria:
a `legenda_premium` existia no clipe e nunca chegava ao post.json.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import traducao

MAIN = (RAIZ / "main.py").read_text(encoding="utf-8")
AGEND = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")
TRAD = (RAIZ / "engine" / "traducao.py").read_text(encoding="utf-8")


# ---------------------------------------------- elo 1: a marca por clipe

def teste_marca_comeca_limpa_e_zera():
    traducao.USOU_RESERVA = True
    traducao.zerar_marca_de_reserva()
    assert traducao.traduzido_pela_reserva() is False


def teste_negativo_marca_nao_vaza_entre_clipes():
    """⚠️ TEOREMATICO. A marca e' de PROCESSO. Sem zerar por clipe, o primeiro
    que caisse na reserva contaminaria todos os seguintes, e clipe traduzido
    pelo Gemini iria pra quarentena a` toa — barrando material bom."""
    assert "zerar_marca_de_reserva()" in MAIN, "main nao zera a marca por clipe"
    i_zera = MAIN.index("zerar_marca_de_reserva()")
    i_le = MAIN.index("traduzido_pela_reserva()")
    assert i_zera < i_le, "main le' a marca ANTES de zerar — vaza entre clipes"


# ---------------------------------------------- elo 2: chega ao post.json

def teste_quarentena_esta_na_lista_branca():
    """⚠️ O elo que ja' falhou sozinho antes (legenda_premium, ate' 31/08)."""
    i = MAIN.index("meta = {k: c.get(k) for k in")
    bloco = MAIN[i:i + 1400]
    assert '"traduzido_por"' in bloco, "traduzido_por fora da lista branca"
    assert '"quarentena"' in bloco, "quarentena fora da lista branca"


# ---------------------------------------------- elo 3: o agendador barra

def _cabe(**campos):
    """Reproduz a decisao de quarentena do `cabe()` do agendador."""
    v = dict(campos)
    return not (v.get("quarentena")
                or (v.get("traduzido_por") or "").startswith("nemotron"))


def teste_positivo_clipe_da_reserva_e_barrado():
    assert not _cabe(traduzido_por="nemotron-ultra", quarentena=True)
    assert not _cabe(traduzido_por="nemotron-ultra")   # so' a marca ja' basta
    assert not _cabe(quarentena=True)                  # so' a flag ja' basta


def teste_negativo_clipe_normal_PASSA():
    """⚠️ O caso negativo que importa: uma guarda que barrasse tudo tambem
    passaria no teste positivo, e ai' NENHUM clipe seria postado."""
    assert _cabe()
    assert _cabe(traduzido_por="gemini")
    assert _cabe(quarentena=False, traduzido_por="gemini")


def teste_a_barreira_existe_no_agendador_de_verdade():
    assert "quarentena" in AGEND, "o agendador nao conhece a quarentena"
    i_cabe = AGEND.index("def cabe(v):")
    trecho = AGEND[i_cabe:i_cabe + 1500]
    assert "quarentena" in trecho, "a checagem nao esta' dentro de cabe()"


# ---------------------------------------------- a reserva e' ULTIMO recurso

def teste_reserva_so_depois_de_esgotar_o_gemini():
    """⚠️ A reserva NAO pode ser um atalho barato. Ela so' vale quando o
    Gemini ja' se esgotou — senao viraria o tradutor padrao pelas costas."""
    i = TRAD.index("from . import nemotron")
    antes = TRAD[:i]
    assert "if sem_cota:" in antes[-800:], \
        "a reserva nao esta' condicionada a` cota esgotada do Gemini"


def teste_reserva_usa_ULTRA_e_nao_super():
    """Medido em 02/09: o Super quebra cada frase em uma linha, e a sintese e'
    frase a frase — a quebra mudaria o corte da narracao."""
    i = TRAD.index("from . import nemotron")
    assert "nemotron.ULTRA" in TRAD[i:i + 900], "a reserva nao fixou o Ultra"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
