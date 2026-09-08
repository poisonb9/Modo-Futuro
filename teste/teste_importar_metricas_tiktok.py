# -*- coding: utf-8 -*-
"""O export do TikTok Studio vira metrica do ciclo — sem chutar coluna.

⚠️ POR QUE ESTE IMPORTADOR EXISTE, medido em 08/09/2026:

    view do Buffer   ZERO em posts de 6 e 7 dias que tinham 338, 359 e 142
                     views reais. Nem a ORDEM se preserva.
    print do perfil  numero real, mas a olho e so' o que cabe na tela.
    export do Studio numero real, TODOS os posts, legivel por maquina.

O QUE PRECISA SER PROVADO

O caminho feliz (ler um CSV) e' trivial. O que estraga o ranking em silencio
e' pegar a COLUNA ERRADA — importar "profile views" achando que e' "video
views" troca o desempenho do POST pelo do PERFIL, e nada no resultado
denuncia isso. Por isso o teste mais importante daqui e' a armadilha das
duas colunas parecidas.

E o segundo: recusar em vez de chutar quando a coluna nao existe.
"""
import io
import json
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import importar_metricas_tiktok as imp

TMP = pathlib.Path(tempfile.mkdtemp())


def _csv(nome: str, conteudo: str) -> pathlib.Path:
    p = TMP / nome
    p.write_text(conteudo, encoding="utf-8")
    return p


def teste_positivo_le_export_em_ingles():
    p = _csv("en.csv",
             "Post time,Video title,Video views,Likes\n"
             "2026-09-01,Regras extremas da fabrica limpa,2473,88\n")
    linhas, aviso = imp.ler(p)
    assert len(linhas) == 1
    assert linhas[0]["views"] == 2473


def teste_positivo_le_export_em_portugues_com_ponto_e_milhar():
    """Conta pt-BR: separador `;` e numero "1.234"."""
    p = _csv("pt.csv",
             "Data de publicação;Título do vídeo;Visualizações do vídeo\n"
             "2026-09-01;Post em portugues;1.234\n")
    linhas, _ = imp.ler(p)
    assert linhas[0]["views"] == 1234, "nao entendeu o ponto de milhar"


def teste_ARMADILHA_profile_views_nao_pode_virar_video_views():
    """⚠️ O teste que mais importa aqui.

    Se o importador pegar "Profile views", o ranking passa a medir o
    desempenho do PERFIL e nao o do post — e nada no resultado denuncia.
    """
    p = _csv("trap.csv",
             "Post time,Profile views,Video title,Video views,Likes\n"
             "2026-09-01,999999,Post de teste,2473,88\n")
    linhas, aviso = imp.ler(p)
    assert linhas[0]["views"] == 2473, "pegou a coluna do PERFIL"
    assert "Video views" in aviso


def teste_NEGATIVO_sem_coluna_de_views_ele_RECUSA():
    """Chutar coluna e' como se importa curtida achando que e' view."""
    p = _csv("ruim.csv", "Data,Curtidas\n2026-09-01,10\n")
    linhas, aviso = imp.ler(p)
    assert linhas == []
    assert "NAO chutei" in aviso
    # e diz quais colunas existiam, senao quem le' fica sem saida
    assert "Curtidas" in aviso


def teste_NEGATIVO_arquivo_vazio_nao_vira_import_vazio_silencioso():
    p = _csv("vazio.csv", "Post time,Video title,Video views\n")
    linhas, aviso = imp.ler(p)
    assert linhas == [] and aviso


def teste_o_MESMO_PONTO_significa_coisas_opostas():
    """⚠️ ACHADO POR ESTE TESTE, em 08/09/2026, e o erro era de 10x.

    A primeira versao apagava todo `.` e `,` antes de aplicar o sufixo, entao
    "1.2K" virava 12 * 1000 = 12000 em vez de 1200. Um valor inflado 10x poe
    o post errado em primeiro lugar e manda baixar 5 fontes no rumo dele — e
    nada na saida denunciaria.

        COM sufixo  ->  separador DECIMAL   "1.2K"  = 1200
        SEM sufixo  ->  separador MILHAR    "1.234" = 1234

    ⚠️ Eu tinha escrito no modulo que o erro "nao muda ranking". Mudava.
    """
    assert imp._numero("1.2K") == 1200
    assert imp._numero("1,2K") == 1200
    assert imp._numero("1.5M") == 1_500_000
    assert imp._numero("1.234") == 1234
    assert imp._numero("1,234") == 1234
    assert imp._numero("2 473") == 2473
    assert imp._numero("999") == 999
    # lixo nao vira numero
    assert imp._numero("") is None
    assert imp._numero("abc") is None
    assert imp._numero("1.2.3K") is None


def teste_view_so_sobe_no_registro():
    """O import SOMA: um export mais antigo nao pode rebaixar um numero que
    ja' se sabe. O historico do TikTok para em 60 dias, entao o registro
    local e' o unico lugar onde o que passou disso sobrevive."""
    txt = (RAIZ / "importar_metricas_tiktok.py").read_text(encoding="utf-8")
    assert "max(int(anterior or 0), x[\"views\"])" in txt


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
