# -*- coding: utf-8 -*-
"""A fila alterna canal/varredura, e a legenda nao repete o nome.

Duas decisoes do Bryan em 16/09/2026, e uma guarda pra cada.

## 1. A FILA ALTERNA

Por `ganho x vendas` puro, os primeiros da fila eram ferramenta, carro e
jardim — produtos da VARREDURA, que rendem bem e nao vem de canal nenhum. O
canal abria com tres posts seguidos sem a linha "do Achadinho Make", que e'
justamente a que impede o feed de virar monte anonimo de link.

⛔ E INTERCALAR NAO PODE VIRAR FILTRAR. A guarda central aqui e' a de que
`_intercalar` devolve exatamente o mesmo CONJUNTO que recebeu — mesma
quantidade, mesmos produtos, nenhum repetido. Uma implementacao que jogasse
fora o excedente do lado maior passaria na checagem de alternancia com nota
dez e perderia 60 produtos em silencio.

## 2. A LEGENDA NAO REPETE O NOME — MAS SO' QUANDO HA' CARTAZ

Com cartaz, o nome ja' esta' na imagem em corpo grande. Sem cartaz (a reserva
de quando a foto nao baixa) nao ha' imagem nenhuma dizendo o que e' o produto,
e um post que abre em "Caiu 43%" sem nunca dizer 43% de QUE e' pior que o post
repetitivo. Os dois caminhos se conferem, e e' o segundo que e' o caso
negativo do primeiro.

## 3. O GANCHO NAO INVENTA NUMERO

E' a linha mais alta do post. A operacao passou duas semanas tirando desconto
falso da pagina; deixar um modelo escrever livremente ali reinstalaria
propaganda pela legenda. Todo numero da frase tem de existir no fato medido.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import gancho, vitrine  # noqa: E402

UM_CANAL = "truque.importado"        # esta' em vitrine.ORIGEM
DA_VARREDURA = "varredura.carro"     # NAO esta'


def _p(i, canal):
    return {"nome": f"Produto {i}", "_canal": canal, "link": f"https://x/{i}",
            "preco": "R$ 10,00"}


def teste_alterna_comecando_pelo_canal():
    fila = ([_p(i, DA_VARREDURA) for i in range(5)]
            + [_p(100 + i, UM_CANAL) for i in range(5)])
    saida = vitrine._intercalar(fila)
    lados = ["C" if vitrine.ORIGEM.get(p["_canal"]) else "v" for p in saida]
    assert lados == list("CvCvCvCvCv"), lados


def teste_nada_se_perde_nem_se_repete():
    """⛔ O CASO QUE IMPORTA: intercalar reordena, nao filtra."""
    fila = ([_p(i, UM_CANAL) for i in range(7)]
            + [_p(100 + i, DA_VARREDURA) for i in range(2)])
    saida = vitrine._intercalar(fila)
    assert len(saida) == len(fila), (len(saida), len(fila))
    antes = sorted(p["nome"] for p in fila)
    depois = sorted(p["nome"] for p in saida)
    assert antes == depois, "a fila mudou de conteudo, nao so' de ordem"
    assert len({p["nome"] for p in saida}) == len(saida), "produto repetido"


def teste_a_ordem_dentro_de_cada_lado_e_preservada():
    """A intercalacao nao pode desfazer a ordenacao por ganho x vendas."""
    fila = []
    for i in range(4):
        fila.append(_p(i, UM_CANAL))
        fila.append(_p(100 + i, DA_VARREDURA))
    saida = vitrine._intercalar(fila)
    so_canal = [p["nome"] for p in saida if vitrine.ORIGEM.get(p["_canal"])]
    assert so_canal == [f"Produto {i}" for i in range(4)], so_canal


def teste_um_lado_vazio_nao_quebra_nem_some():
    for canal in (UM_CANAL, DA_VARREDURA):
        fila = [_p(i, canal) for i in range(6)]
        saida = vitrine._intercalar(fila)
        assert [p["nome"] for p in saida] == [p["nome"] for p in fila], canal


def teste_com_cartaz_a_legenda_nao_traz_o_nome():
    p = {"nome": "Fone Lenovo GM2 Pro", "link": "https://x/1",
         "preco": "R$ 40,69", "preco_em": "2026-09-16", "loja": "Loja X"}
    t = vitrine.postar_texto(p, "truque.importado", com_link=False,
                             gancho="Caiu 43% desde que a gente olhou.")
    assert "Fone Lenovo" not in t, t
    assert "Caiu 43%" in t, t
    # ⚠️ o resto do post continua inteiro: tirar o nome nao pode tirar o preco
    assert "R$ 40,69" in t and "Loja X" in t and "do Achadinho Make" in t, t


def teste_sem_cartaz_o_nome_VOLTA():
    """⛔ O CASO NEGATIVO do teste acima.

    Sem ele, uma implementacao que apagasse o nome em TODO caminho passaria no
    positivo — e o post de reserva iria ao ar sem dizer de que produto fala.
    """
    p = {"nome": "Fone Lenovo GM2 Pro", "link": "https://x/1",
         "preco": "R$ 40,69", "preco_em": "2026-09-16", "loja": "Loja X"}
    t = vitrine.postar_texto(p, "truque.importado")
    assert "Fone Lenovo GM2 Pro" in t, t
    # e o link tem de estar la': o post de texto nao tem botao pra carregar
    assert "https://x/1" in t, t


def teste_sem_gancho_a_legenda_volta_pro_nome():
    """Gancho e' melhora, nao conteudo: sem ele o post de ontem."""
    p = {"nome": "Fone Lenovo GM2 Pro", "link": "https://x/1",
         "preco": "R$ 40,69", "preco_em": "2026-09-16", "loja": "Loja X"}
    t = vitrine.postar_texto(p, "truque.importado", com_link=False, gancho="")
    assert "Fone Lenovo GM2 Pro" in t, t


def teste_o_fato_escolhido_e_o_mais_forte_que_existe():
    # queda ganha de volume, mesmo com volume alto
    f, _ = gancho.fato({"nome": "X", "preco": "R$ 40,00",
                        "preco_antes": "R$ 80,00", "_vendas": 9000})
    assert "caiu 50%" in f, f
    # sem queda, o piso da serie ganha do volume
    f, _ = gancho.fato({"nome": "X", "preco": "R$ 10,00", "_vendas": 9000},
                       [20.0, 15.0, 12.0, 10.0])
    assert "menor preço" in f, f
    # ⚠️ SERIE CURTA NAO VALE. Com 3 pontos a frase e' tecnicamente verdadeira
    # e praticamente vazia — mesmo motivo do grafico de 3 pontos ficar fora.
    f, _ = gancho.fato({"nome": "X", "preco": "R$ 10,00", "_vendas": 9000},
                       [20.0, 15.0, 10.0])
    assert "9000" in f, f


def teste_queda_abaixo_do_piso_nao_vira_gancho():
    """1% e' cambio e arredondamento, nao queda."""
    f, _ = gancho.fato({"nome": "X", "preco": "R$ 99,00",
                        "preco_antes": "R$ 100,00"})
    assert "caiu" not in f, f


def teste_numero_inventado_pelo_modelo_e_recusado():
    """⛔ A guarda que faz o modelo poder escrever esta linha."""
    fato = "caiu 43%: estava R$ 71,00 e hoje está R$ 40,69"
    ok, porque = gancho.confere(fato, "Caiu 43%, de R$ 71,00 para R$ 39,00.")
    assert not ok and "numero" in porque, porque
    # e o caso positivo, pra provar que ela nao reprova tudo
    ok, porque = gancho.confere(fato, "Caiu 43% desde que começamos a olhar.")
    assert ok, porque


def teste_propaganda_e_recusada_no_codigo_e_nao_so_no_prompt():
    fato = "caiu 43%: estava R$ 71,00 e hoje está R$ 40,69"
    ok, porque = gancho.confere(fato, "Imperdível: caiu 43% de verdade.")
    assert not ok and "propaganda" in porque, porque


def teste_sem_preco_nao_ha_gancho():
    """Falha fechada: sem dado nenhum, a linha nao se inventa."""
    assert gancho.de({"nome": "X", "preco": ""}, [], com_modelo=False) == ""


if __name__ == "__main__":
    for nome, f in sorted(globals().items()):
        if nome.startswith("teste_"):
            f()
            print("  ok", nome)
    print("verde")
