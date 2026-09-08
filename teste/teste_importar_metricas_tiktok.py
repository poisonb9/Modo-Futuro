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


def teste_content_quebrado_do_tiktok_e_lido_pela_ANCORA():
    """⚠️ MEDIDO em 08/09/2026: o export do TikTok vem QUEBRADO.

    Numa das 15 linhas do @achadinho.make a descricao tinha virgulas e setas
    fora de aspas, e as colunas deslocaram — o campo "Total views" veio com a
    URL do video dentro, e os numeros verdadeiros sobraram num campo extra.

    Ler por nome de coluna devolve lixo em silencio. A ancora que nao desloca
    e' o LINK: depois dele vem sempre post time, likes, comments, shares,
    views.
    """
    linha_boa = '"8 de setembro","Titulo normal","https://www.tiktok.com/@x/video/1","5 de setembro","10","0","0","479"'
    linha_torta = ('"8 de setembro","Titulo com, virgula solta"," e mais texto",'
                   '"https://www.tiktok.com/@x/video/2","5 de setembro","34","0","0","616"')
    cabecalho = ('"Time","Video title","Video link","Post time","Total likes",'
                 '"Total comments","Total shares","Total views"')
    texto = "\n".join([cabecalho, linha_boa, linha_torta, ""])
    linhas = imp._ler_content_ancorado(texto)
    assert len(linhas) == 2, "a linha torta se perdeu"
    por_view = {x["views"]: x for x in linhas}
    assert 479 in por_view and 616 in por_view, "pegou o numero errado"
    assert "virgula solta" in por_view[616]["titulo"], "perdeu parte do titulo"


def teste_o_MESMO_post_por_duas_fontes_nao_vira_dois():
    """⚠️ MEDIDO: os '2 melhores' do @modofuturo vieram 2473 e 2473 — o MESMO
    post, uma vez pela print (titulo curto) e outra pelo export (titulo com a
    descricao colada). O ciclo enviesaria a busca com um sinal achando que
    tinha dois, e o segundo melhor de verdade nunca seria considerado."""
    from engine import melhores
    juntos = melhores._juntar_repetidos([
        {"titulo": "As regras extremas para entrar na fabrica mais limpa", "views": 2473},
        {"titulo": "As regras extremas para entrar na fabrica mais limpa do mundo Saiba como", "views": 2473},
        {"titulo": "Como 1 POEIRA pode DESTRUIR 1 milhao de dolares", "views": 1009},
    ])
    assert len(juntos) == 2, f"deviam sobrar 2, sobraram {len(juntos)}"
    # fica o titulo mais curto (o de verdade), com o maior numero
    assert juntos[0]["views"] == 2473
    assert juntos[0]["titulo"].endswith("limpa")


def teste_titulos_CURTOS_e_diferentes_nao_sao_juntados():
    """Senao a juncao viraria um bloqueio: dois posts curtos com comeco
    parecido virariam um so', e o ranking perderia material de verdade."""
    from engine import melhores
    juntos = melhores._juntar_repetidos([
        {"titulo": "Bolo de cenoura", "views": 100},
        {"titulo": "Bolo de fuba", "views": 90},
    ])
    assert len(juntos) == 2


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
