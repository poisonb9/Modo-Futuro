# -*- coding: utf-8 -*-
"""Janela diz ONDE PROCURAR; recorte diz que nao ha' o que procurar.

⚠️ O DEFEITO, MEDIDO EM 04/09/2026. A fila mandava a janela de 1200s pelo
`--recorte`, e o `--recorte` significa "o trecho JA' E' o clipe, pule a
selecao". O motor entao tratava 20 minutos inteiros como UM clipe:

    [3/5] recorte manual 4692.0s->5892.0s (pula selecao do Gemini)
    [4/5] clipe 1/1 -> nota 92
          Groq transcrevendo (36.8 MB)...
       [!] clipe 1 perdido: clip_01.flac tem 36.8 MB, acima do limite de 25 MB

⚠️ NAO ERA INTERMITENTE. Toda janela tem 1200s, todo FLAC de 1200s passa de
25 MB, e o teto do Groq e' 25 MB — a falha era CERTA. 12 runs seguidos,
~11 horas de runner, zero clipe. E o lote das 07:00:24 UTC foi disparado no
RESET da cota e falhou igual, que e' a prova de que nao era cota.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

MAIN = (RAIZ / "main.py").read_text(encoding="utf-8")
FILA = (RAIZ / "cortar_fila.py").read_text(encoding="utf-8")
WF = (RAIZ / ".github/workflows/cortar_de_bruto.yml").read_text(encoding="utf-8")

import config


# ------------------------------------------------- o caminho existe

def teste_o_motor_aceita_janela():
    assert '"--janela"' in MAIN, "main.py nao tem --janela"
    assert "janela: tuple[float, float] | None" in MAIN, "processar nao recebe janela"


def teste_a_janela_chega_ao_motor_pelo_workflow():
    assert "--janela {0}" in WF, "o workflow nao passa --janela pro main"
    assert "janela:" in WF, "o workflow nao declara a entrada janela"


def teste_a_fila_manda_janela_e_nao_recorte():
    """⚠️ ESTE E' O CONSERTO. O campo do item continua se chamando `recorte`
    (esta' gravado assim em 15 itens), mas ele viaja como `janela`."""
    assert 'entradas["janela"] = item["recorte"]' in FILA
    assert 'entradas["recorte"] = item["recorte"]' not in FILA


# ------------------------------------------------- os negativos

def teste_negativo_a_janela_NAO_pula_a_selecao():
    """⚠️ TEOREMATICO, e e' o coracao do defeito. Se a janela pulasse a
    selecao como o recorte faz, o clipe voltaria a ser a janela inteira e o
    FLAC voltaria a estourar o Groq. O caminho da janela TEM de chamar
    selecao.escolher; o do recorte TEM de chamar selecao.metadados."""
    i = MAIN.index("if janela:")
    j = MAIN.index("elif recorte:")
    bloco_janela = MAIN[i:j]
    assert "selecao.escolher" in bloco_janela, "a janela nao esta' selecionando"
    assert "selecao.metadados" not in bloco_janela, (
        "a janela esta' tratando o trecho como clipe pronto — o defeito voltou")


def teste_negativo_o_recorte_manual_continua_intacto():
    """O `--recorte` e' do Bryan refazendo um corte que funcionou. Consertar a
    janela nao pode mudar o que ele faz."""
    i = MAIN.index("elif recorte:")
    bloco = MAIN[i:i + 1600]
    assert "selecao.metadados" in bloco, "o recorte manual parou de ser manual"
    assert "pula seleção do Gemini" in bloco


def teste_negativo_a_janela_devolve_o_tempo_pro_bruto():
    """⚠️ Sem o deslocamento, o Gemini fala do segundo 120 DA JANELA e o corte
    final leria o segundo 120 do BRUTO — clipe de outro assunto, sem erro
    nenhum aparecendo."""
    i = MAIN.index("if janela:")
    bloco = MAIN[i:MAIN.index("elif recorte:")]
    assert '+ ini_j' in bloco, "os tempos da janela nao voltam pra linha do bruto"


def teste_negativo_o_clipe_da_janela_cabe_no_groq():
    """A conta que o defeito nao fez. Clipe de DUR_MAX segundos tem de caber
    com folga no teto do Groq; a janela de 1200s nunca coube."""
    # FLAC 16kHz mono ~= 32 kB/s, medido nos clipes reais do projeto.
    kb_por_s = 32
    mb_clipe = config.DUR_MAX * kb_por_s / 1024
    mb_janela = 1200 * kb_por_s / 1024
    assert mb_clipe < config.GROQ_LIMITE_MB, (
        f"clipe de {config.DUR_MAX}s daria {mb_clipe:.1f} MB")
    assert mb_janela > config.GROQ_LIMITE_MB, (
        "a janela de 1200s deveria estourar o teto — se nao estoura, esta "
        "conta nao esta' medindo o que o defeito era")


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
