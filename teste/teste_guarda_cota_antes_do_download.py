# -*- coding: utf-8 -*-
"""Sem cota, o run tem de morrer BARATO — e nao punir a fonte.

⚠️ O DEFEITO, medido em 04/09/2026. `engine/traducao.py` tem reserva
(Nemotron, com quarentena); `engine/selecao.py` NAO tem. Sem Gemini o run
morre na escolha de clipes — so' que depois de baixar o bruto e traduzir
tudo. No run 33803772922 o motor baixou 0,11 GB, traduziu (ja' na reserva,
20:46:52) e so' as 20:48:42 descobriu que nao tinha como escolher.

Cada run desses gasta de 40 a 100 minutos de runner com desfecho conhecido.

⚠️ ESTA GUARDA NAO DA' RESERVA A` SELECAO. Isso mudaria QUAIS clipes vao ao
ar, e e' decisao do Bryan. Ela so' evita o gasto.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

WF = (RAIZ / ".github/workflows/cortar_de_bruto.yml").read_text(encoding="utf-8")
WF_YT = (RAIZ / ".github/workflows/cortar.yml").read_text(encoding="utf-8")

import cortar_fila
import guarda_cota


def teste_a_guarda_roda_antes_do_download():
    """⚠️ O PONTO INTEIRO. Guarda depois do download nao economiza nada — e
    foi assim que ela nasceu na primeira tentativa, com o nome dizendo ANTES
    e o lugar dizendo depois."""
    i_guarda = WF.index("guarda_cota.py")
    i_download = WF.index("baixar_bruto_drive.py")
    assert i_guarda < i_download, "a guarda esta' DEPOIS do download"


def teste_a_guarda_roda_antes_do_que_custa_caro():
    """Instalar o Chatterbox e baixar a amostra de voz tambem custam minutos."""
    i_guarda = WF.index("guarda_cota.py")
    # ⚠️ Pelo COMANDO, nao pelo nome: "chatterbox-tts" aparece antes num
    # COMENTARIO, e a primeira versao deste teste reprovou por casar com ele.
    # Procurar nome solto num YAML acha texto, nao passo.
    for caro in ("pip install chatterbox-tts", "Baixar amostra de voz do Drive"):
        assert i_guarda < WF.index(caro), f"a guarda esta' depois de: {caro}"


def teste_a_guarda_roda_depois_do_pip():
    """Antes do pip ela nao tem com que rodar."""
    assert WF.index("pip install -r requirements.txt") < WF.index("guarda_cota.py")


def teste_a_guarda_recebe_as_chaves():
    i = WF.index("Sondar cota do Gemini")
    bloco = WF[i:WF.index("guarda_cota.py", i)]
    assert bloco.count("GEMINI") > 10, "a guarda nao recebe o rodizio de chaves"


# ------------------------------------------------- o negativo que importa

def teste_negativo_a_mensagem_NAO_pune_a_fonte():
    """⚠️ TEOREMATICO, e e' o risco real deste conserto.

    `cortar_fila.falhou_por_cota()` classifica a falha lendo o LOG. Se a
    mensagem desta guarda nao casar com nenhuma marca, a falha vira "defeito
    da fonte" — e tres delas expulsam da fila um video perfeito. Aconteceu em
    01/09 com "The Only 13 Minutes You Need To Master Discipline".
    """
    MARCAS = ("SEM COTA", "chaves do Gemini", "todas as chaves esgotadas",
              "sem quota")
    assert any(m in guarda_cota.MARCA for m in MARCAS) or \
        any(m in MARCAS for m in [guarda_cota.MARCA]), \
        f"a marca {guarda_cota.MARCA!r} nao e' reconhecida pelo classificador"
    # e a marca tem de estar nas MARCAS do classificador, nao so' parecida
    fonte = (RAIZ / "cortar_fila.py").read_text(encoding="utf-8")
    assert guarda_cota.MARCA in fonte, (
        "a marca da guarda sumiu do classificador — a fonte seria punida")


def teste_negativo_cota_ok_nao_aborta():
    """Um detector que sempre aborta pararia a fabrica inteira e passaria em
    todos os testes acima."""
    real = cortar_fila.tem_cota
    try:
        cortar_fila.tem_cota = lambda: (True, "3 de 5 vivas")
        assert guarda_cota.main() == 0, "abortou mesmo COM cota"
        cortar_fila.tem_cota = lambda: (False, "0 de 5")
        assert guarda_cota.main() == 1, "nao abortou SEM cota"
    finally:
        cortar_fila.tem_cota = real


# ------------------------------------------------- o OUTRO caminho de corte

def teste_o_caminho_do_youtube_tambem_tem_a_guarda():
    """⚠️ ESTE TESTE NASCEU DE UM BURACO MEU, medido em 05/09/2026.

    Eu pus a guarda so' no `cortar_de_bruto.yml` e dei o conserto por
    fechado. O `cortar.yml` — o caminho que baixa do YouTube — ficou sem
    ela. Dois cortes do @truque.importado baixaram o video inteiro e so'
    morreram na traducao, por cota: exatamente o gasto que a guarda existe
    pra evitar.

    Ha' DOIS caminhos ate' o motor. Guarda que cobre um so' nao e' guarda."""
    assert "guarda_cota.py" in WF_YT, "o cortar.yml esta' sem a guarda de cota"
    i_guarda = WF_YT.index("guarda_cota.py")
    assert WF_YT.index("pip install -r requirements.txt") < i_guarda
    # e antes do download: no cortar.yml quem baixa e' o proprio main.py
    assert i_guarda < WF_YT.index("main.py"), "a guarda esta' depois do corte"


def teste_a_guarda_do_youtube_recebe_as_chaves():
    i = WF_YT.index("Sondar cota do Gemini")
    bloco = WF_YT[i:WF_YT.index("guarda_cota.py", i)]
    assert bloco.count("GEMINI") > 10, "a guarda do cortar.yml nao recebe o rodizio"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
