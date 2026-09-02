# -*- coding: utf-8 -*-
"""A dedup de trecho conta o que foi POSTADO, nao o que foi arquivado.

⚠️ O DEFEITO QUE ESTE TESTE IMPEDE DE VOLTAR, medido em 02/09/2026.

`publicado_em` e' carimbado pelo `publicar_release.py` quando o clipe entra na
RELEASE do GitHub. A guarda de trecho lia esse campo como "ja' foi ao ar", e o
resultado era o clipe novo entrar no conjunto de trechos vistos e, na linha
seguinte, ser recusado por estar nele.

Dos 96 clipes do manifesto, 9 tinham `fonte_id` (campo criado naquele dia) e
os NOVE estavam auto-bloqueados. O agendador imprimia "0 ainda nao agendado"
com 10 vagas livres, e o @semanestesia.pod passou o dia vazio com o clipe dele
pronto na release.

⚠️ A PROTECAO TEM DE CONTINUAR: dois cortes do mesmo bruto no mesmo segundo
sao o MESMO clipe, por mais que titulo e traducao mudem — foi assim que a
cozinha ficou com tres pares duplicados, e duplicata derruba alcance.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

FONTE = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")

# o bloco que monta o conjunto de trechos ja' usados
I = FONTE.index("trechos_vistos = set()")
BLOCO = FONTE[I:FONTE.index("def trecho_ja_usado")]


def teste_nao_usa_mais_publicado_em():
    """⚠️ O campo ambiguo nao pode voltar a decidir isto."""
    assert '_v.get("publicado_em")' not in BLOCO, (
        "a guarda voltou a usar publicado_em — clipe novo vai se auto-bloquear")


def teste_usa_o_que_o_buffer_enviou():
    assert "ja_publicado" in BLOCO, (
        "a guarda nao esta' consultando o que o Buffer de fato enviou")


def teste_ja_publicado_existe_antes_da_guarda():
    """Ordem importa: se `ja_publicado` fosse montado depois, o nome existiria
    mas estaria vazio, e a guarda deixaria passar TUDO — inclusive duplicata
    de verdade."""
    i_pub = FONTE.index("ja_publicado = {")
    assert i_pub < I, "ja_publicado e' montado DEPOIS da guarda de trecho"


def teste_negativo_a_guarda_continua_existindo():
    """⚠️ TEOREMATICO. O conserto podia ser 'apagar a guarda', e ai' o teste
    positivo passaria e a duplicata voltaria. A comparacao por
    (fonte_id, inicio_s) tem de continuar de pe'."""
    assert "trecho_ja_usado" in FONTE, "a guarda de trecho sumiu"
    corpo = FONTE[FONTE.index("def trecho_ja_usado"):]
    corpo = corpo[:corpo.index("\n    def ", 1)]
    assert "trechos_vistos" in corpo, "trecho_ja_usado nao consulta mais o conjunto"
    assert "fonte_id" in corpo and "inicio_s" in corpo, \
        "a comparacao deixou de ser por (fonte_id, inicio_s)"


def teste_negativo_clipe_sem_fonte_id_nao_e_recusado():
    """Manifesto antigo nao tem `fonte_id`. Recusar por ausencia de dado
    travaria tudo que foi cortado antes de 02/09/2026 — 87 dos 96 clipes."""
    corpo = FONTE[FONTE.index("def trecho_ja_usado"):]
    corpo = corpo[:corpo.index("\n    def ", 1)]
    assert "return False" in corpo, \
        "clipe sem fonte_id precisa PASSAR, nao ser recusado"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
