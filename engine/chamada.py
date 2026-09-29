# -*- coding: utf-8 -*-
"""A chamada pro link da bio — o degrau que faltava no funil.

## POR QUE ISTO EXISTE

Medido em 12/09/2026: NENHUM video da operacao manda alguem pro link. A
legenda era titulo + descricao + premium + hashtags, e mais nada. A
contra-capa ficou pronta, os convites dos grupos estao vivos, o livro 01
estreia no @semanestesia.pod — e ninguem era convidado a ir ate' la'.

O funil e' `video -> perfil -> link da bio -> grupo ou compra`. O primeiro
degrau nao existia.

## A REGRA DO TEXTO, e ela vem de medicao nossa

⭐ **A chamada MOSTRA o que tem la'; nao pergunta e nao promete explicacao.**

Playbook §23.9, 18 posts: titulo-PERGUNTA converteu 0 de 4; titulo que AFIRMA
converteu 7 de 14. Nao ha' razao pra uma chamada obedecer logica diferente da
de um titulo — e' a mesma pessoa decidindo se age.

    ✅ "O livro que nasceu deste canal esta' no link da bio."
    ❌ "Quer saber mais? Link na bio!"

## ⚠️ UMA CHAMADA POR CANAL, E SO' ONDE HA' DESTINO

Canal sem grupo e sem produto nao ganha chamada. Convidar pra uma pagina que
nao tem o que entregar gasta a unica frase que a pessoa ia ler ate' o fim, e
ensina que o nosso link nao vale o clique.

⚠️ E CANAL DESCONHECIDO NAO GANHA CHAMADA NENHUMA. Devolve vazio, nunca um
texto generico: chamada errada no canal errado e' pior que chamada nenhuma —
publico de tecnologia convidado pra grupo de promocao nao volta.
"""
from __future__ import annotations

from . import canais_registro

# canal canonico -> a linha que vai no fim da legenda.
#
# ⚠️ Cada uma diz O QUE TEM la', em vez de mandar clicar. E nenhuma promete o
# que a pagina nao entrega hoje: o @semanestesia.pod fala do livro porque o
# livro existe; os canais de achadinho falam do grupo porque o grupo existe.
# Vazio desde 25/09/2026: sem chamada em nenhum canal (decisao do dono).
# Os textos antigos estao guardados fora do repositorio.
# ⭐ 28/09/2026 (dono): o Chef volta a ter chamada — a pagina da bio entrega a
# receita completa (ficha em grama e °C). So' ele; os outros seguem sem.
# ⭐ 29/09/2026 (dono): "quero o link na legenda de todos os videos de todos os
# canais, de maneira inteligente sem agredir o cliente". Cada linha diz o que a
# pagina da bio ENTREGA HOJE (conferido no ar nesse dia: e-mail gratis no
# Geracao 2000 e no Modo Futuro, makes com preco no Make). O Pago Menos e o
# achadinhos.instantaneos entram quando a pagina mostrar a oferta do video.
CHAMADA: dict[str, str] = {
    "cozinha.importada": "📖 A receita completa, em grama e °C, está no link da bio.",
    "atefalhar": "📺 A nostalgia da semana, grátis no seu e-mail. Link da bio.",
    "modofuturo": "⚡ A tecnologia por dentro, grátis no seu e-mail. Link da bio.",
    "truque.importado": "💄 As makes dos vídeos, com preço conferido. Link da bio.",
}
# canais cuja chamada fica SO' na legenda (sem card desenhado no fim do video)
SO_LEGENDA = {"cozinha.importada", "atefalhar", "modofuturo", "truque.importado"}


def do_canal(canal: str | None) -> str:
    """A chamada deste canal, ou vazio.

    ⚠️ Resolve pelo `canais_registro` de proposito: ele aceita apelido e `@`,
    e devolve None pra desconhecido em vez de chutar. Chutar canal e' a causa
    medida de oito clipes irem parar no canal errado.
    """
    nome = canais_registro.canonico(canal)
    if not nome:
        return ""
    return CHAMADA.get(nome, "")


def com_chamada(legenda: str, canal: str | None) -> str:
    """Poe a chamada no fim da legenda, uma vez so'.

    ⚠️ A CHAMADA VAI DEPOIS DO TEXTO E ANTES DAS HASHTAGS e' o que quem chama
    quer — mas quem monta a legenda e' o `legenda_post`, e a ordem la' ja'
    esta' decidida. Aqui a funcao existe pra o caso de alguem montar a legenda
    por fora; ela NAO duplica se a chamada ja' estiver no texto.
    """
    c = do_canal(canal)
    if not c or not legenda:
        return legenda
    if c in legenda:
        return legenda
    return legenda.rstrip() + "\n\n" + c
