# -*- coding: utf-8 -*-
"""A fila tem de mandar `recorte` e `conta_saida` — e nao mandar recorte a` toa.

Duas correcoes de 02/09/2026, as duas no dispatch do `cortar_fila.py`:

  conta_saida  onde o BRUTO esta' nao e' onde o CLIPE vai. 'A POSTAR'
               pertence a` conta principal, e a reserva devolve 404 nela.
               Subir com credencial da reserva nunca podia dar certo, e o
               passo vem DEPOIS do corte — o run 33622779969 perdeu 79,4 min.

  recorte      janela que faz podcast longo caber no teto de 6h do Actions.
               O workflow e o main.py ja' aceitavam; so' a fila nao pedia.

⚠️ ATUALIZADO EM 04/09/2026, E A DOCSTRING ACIMA E' A PROVA DO DEFEITO: ela
diz, com todas as letras, que `recorte` era a JANELA. Mas `--recorte` no
main.py significa "o trecho JA' E' o clipe, pule a selecao" — outra coisa.
Mandada por ali, a janela de 1200s virava um clipe de 20 min, o FLAC dava
36-39 MB contra o teto de 25 MB do Groq, e 12 runs seguidos morreram sem
produzir nada (~11h de runner).

O campo do ITEM continua se chamando `recorte` (esta' gravado assim em 15
itens da fila). O que mudou e' o nome da ENTRADA do workflow: vai como
`janela`. A propriedade que este teste guarda nao mudou — a chave so' pode
entrar quando o item de fato pede.
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

FONTE = (RAIZ / "cortar_fila.py").read_text(encoding="utf-8")
WF = (RAIZ / ".github" / "workflows" / "cortar_de_bruto.yml").read_text(encoding="utf-8")

# o bloco que monta os inputs do dispatch
BLOCO = FONTE[FONTE.index("entradas = {"):FONTE.index("_gh(f\"actions/workflows/{WF}/dispatches\"")]


def teste_positivo_manda_conta_saida():
    assert '"conta_saida"' in BLOCO, "o dispatch nao manda conta_saida"


def teste_conta_saida_e_diferente_da_conta_do_bruto():
    """⚠️ O DEFEITO EM UMA LINHA. Se as duas apontarem pro mesmo valor, o
    conserto nao consertou nada."""
    m_in = re.search(r'"conta":\s*"(\w+)"', BLOCO)
    m_out = re.search(r'"conta_saida":\s*"(\w+)"', BLOCO)
    assert m_in and m_out, BLOCO[:200]
    assert m_in.group(1) != m_out.group(1), \
        f"conta e conta_saida com o mesmo valor ({m_in.group(1)})"


def teste_workflow_declara_conta_saida():
    """Mandar input que o workflow nao declara faz o dispatch ser recusado."""
    assert "conta_saida:" in WF, "o workflow nao declara conta_saida"


def teste_workflow_usa_conta_saida_no_passo_de_subir():
    # ⚠️ A LINHA DE EXECUCAO, nao a primeira mencao: `subir_drive.py` aparece
    # tambem em comentario, e casar com ele reprovava um workflow correto.
    exec_ = [l for l in WF.split("\n")
             if "subir_drive.py" in l and l.lstrip().startswith("run:")]
    assert exec_, "nao achei a linha `run:` do subir_drive.py"
    for linha in exec_:
        assert "inputs.conta_saida" in linha, \
            f"subir_drive ainda usa a conta do bruto: {linha.strip()[:90]}"


def teste_positivo_manda_recorte_quando_existe():
    """O item guarda `recorte`; a entrada do workflow se chama `janela`."""
    assert 'entradas["janela"] = item["recorte"]' in FONTE
    assert 'entradas["recorte"] = item["recorte"]' not in FONTE, (
        "a janela voltou a viajar como recorte — o defeito de 04/09 voltou")


def teste_negativo_NAO_manda_recorte_quando_nao_ha():
    """⚠️ TEOREMATICO, e o motivo de este teste existir.

    Se o recorte fosse mandado sempre — vazio inclusive — TODA fonte curta
    passaria a ir com uma janela em branco, e as que hoje funcionam
    quebrariam. A chave so' pode entrar quando o item de fato pede.
    """
    i = FONTE.index('entradas["janela"]')
    antes = FONTE[:i].rstrip().split("\n")[-1]
    assert antes.strip().startswith("if item.get(\"recorte\")"), \
        f"a janela nao esta' sob condicional: ...{antes}"
    assert '"janela":' not in BLOCO, \
        "janela esta' no dicionario fixo — vai junto mesmo quando vazia"


def teste_workflow_declara_recorte():
    assert "recorte:" in WF, "o workflow nao declara recorte"
    assert "janela:" in WF, "o workflow nao declara janela"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
