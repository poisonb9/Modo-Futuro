# -*- coding: utf-8 -*-
"""Gera a versao PUBLICA da contra-capa, mascarada, e sobe pro repo `bio`.

    python paginas/publicar_bio.py            gera em paginas/_publicado/
    python paginas/publicar_bio.py --subir    gera, empurra E PUBLICA

## 🚨 LEIA ISTO ANTES DE DIZER QUE ALGUMA COISA "ESTA' NO AR"

⚠️ **EMPURRAR PRO `poisonb9/bio` NAO PUBLICA NADA.** Os projetos do Cloudflare
Pages sao de **upload direto** (`"source": null` na API), e NAO estao ligados
ao repositorio. O repo e' historico; quem serve o site e' o deploy.

Medido em 12/09/2026 as 21:57: o `--subir` tinha empurrado o commit certo e eu
anunciei "no ar". O site continuava com os botoes de WhatsApp, de um deploy
das 21:14. O `git push` deu certo e o SITE ESTAVA VELHO — nada no push avisa.

⭐ **A regra que sobrou disso: o unico jeito de saber e' BAIXAR A PAGINA DO
AR e procurar a mudanca nela.** `curl https://<projeto>.pages.dev/` e conferir.
Status de push, "Deployment complete" e commit verde nao sao prova; a prova e'
o byte que o visitante recebe. Por isso o `--subir` agora publica e CONFERE, e
estoura se o ar nao tiver a mudanca.

## POR QUE EXISTE

Ordem do Bryan em 12/09/2026: "evita por nomes que nao precise, use codigos,
deixe nosso repo mascarado".

A pagina que a gente edita e' cheia de comentario explicando o motor: nomes de
arquivo (`engine/canais_registro.py`), medicao (`playbook §23.9`), decisao de
negocio, data de incidente. Isso tudo e' util PRA GENTE e nao tem por que
estar num repositorio publico — quem abre o link quer os botoes, nao o mapa da
operacao.

⚠️ O QUE NAO DA' PRA MASCARAR, e nem deveria: o nome do canal, o @, a promessa
e os botoes. Eles SAO a pagina. Mascarar o que o visitante tem de ler seria
esconder o produto de quem ele existe pra servir.

⚠️ E O QUE SOBRA DE VERDADE depois do corte sao os nomes INTERNOS
(`truque.importado`, `cozinha.importada`) — eles nao aparecem na tela, so' no
codigo, e revelam a estrutura interna. Viram codigo aqui.

## A CHAVE DE LEITURA MORA FORA

O decodificador (qual codigo e' qual canal) vai pra
`BACKUP_SISTEMA\\SEGREDOS_NAO_SUBIR\\CODIGOS_DA_BIO.md`, que nao e' versionado.
Guardar a chave junto do texto cifrado e' nao cifrar nada.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import os
from pathlib import Path

from dotenv import load_dotenv

# ⚠️ O .env NAO SE CARREGA SOZINHO num script solto. Sem isto o passo de
# publicar reclamava de credencial que existe — e a tentacao seria
# concluir que o token acabou.
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# ⚠️ E O .env TRAZ UM `GITHUB_TOKEN` JUNTO, que e' o PAT fine-grained e NAO
# alcanca o repo `bio` — quem alcanca e' o `gh` logado nesta maquina. Com a
# variavel presente o git obedece a ela e o push morre com 128, sem dizer
# por que. Medido em 12/09/2026: sem a linha abaixo, o publicador para de
# funcionar no dia em que alguem carregar o .env.
os.environ.pop('GITHUB_TOKEN', None)
os.environ.pop('GH_TOKEN', None)

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "paginas" / "contra_capa.html"
# ⚠️ A PAGINA DO ANUNCIANTE, e nao da bio. Ela vai como ROTA `/parceiros`
# dentro dos MESMOS projetos, e nao num projeto novo: a conta bateu o teto
# de 10 projetos no Cloudflare (medido em 14/09/2026, os 10 ocupados, 4
# deles enderecos reservados do Ate Falhar).
#
# ⭐ E isto resolve o problema real: o Awin aceita UM endereco no perfil.
# Apontar pra `/parceiros` faz o avaliador ver a operacao inteira sem
# poluir a bio do canal, que tem outro trabalho (converter quem veio do
# video).
PARCEIROS = RAIZ / "paginas" / "quem_somos.html"
# ⚠️ O CATALOGO. Vai como rota `/todos` nos mesmos projetos (a conta bateu o
# teto de 10), e e' a MESMA pagina que o site mae servira' na raiz quando
# houver endereco pra ele.
CATALOGO = RAIZ / "paginas" / "todos.html"
# ⭐ PRIVACIDADE (18/09/2026). O catalogo grava clique e busca no Supabase;
# o kit minimo de credibilidade dos Maestros (ecommercenapratica, DEMONSTRADO)
# e a LGPD pedem que a pagina diga isso. Vai como rota `/privacidade` em
# TODOS os projetos, pelo mesmo motivo de `/parceiros`: upload direto
# substitui o diretorio inteiro, e o link do rodape nao pode virar 404.
PRIVACIDADE = RAIZ / "paginas" / "privacidade.html"
DESTINO = RAIZ / "paginas" / "_publicado"
SEGREDOS = (RAIZ.parent.parent.parent / "BACKUP_SISTEMA" / "SEGREDOS_NAO_SUBIR")
REPO = "poisonb9/bio"

# ⚠️ CADA CANAL TEM SEU ENDERECO NO CLOUDFLARE PAGES, e o endereco e' o que
# vai na bio. O nome do projeto e' a porta: a pagina le' `location.hostname`
# e sabe qual canal e'.
#
# ⚠️ NOME TOMADO NAO DA' ERRO NA CLOUDFLARE — ela cria com um sufixo aleatorio
# (`olivro` virou `olivro-oe0`). Medido em 12/09/2026 criando um nome sem
# sentido, que saiu limpo: sufixo significa "e' de outra pessoa". Conferir o
# `subdomain` da resposta e' a unica forma de saber.
PORTAS = {
    "oachadinho": "c1",        # Achadinho Make
    "meulivro": "c2",          # Sem Anestesia — reservado, fora da bio ate' a Kiwify
    "achadinhochef": "c5",
    "pagomenos": "c6",         # Fatura Chora
    "achadinhodehoje": "c7",
}

# nome interno -> codigo. So' entram os que NAO aparecem na tela.
CODIGOS = {
    "truque.importado": "c1",
    "semanestesia.pod": "c2",
    "atefalhar": "c3",
    "modofuturo": "c4",
    "cozinha.importada": "c5",
    "fatura.chora": "c6",
    "achadinhos.instantaneos": "c7",
}


# ⚠️ A CHAVE DA PAGINA E' O @ PUBLICO, nao o nome interno do canal. Sai do
# proprio registro (`canais_registro`) em vez de uma lista nova aqui: duas
# listas discordando e' exatamente o defeito que aquele modulo documenta.
def _chave_da_pagina(nome_buffer: str) -> str:
    # ⚠️ A RAIZ ENTRA NO PATH AQUI. Este script vive em `paginas/` e e'
    # chamado de la': sem isto o `import engine` so' funciona de dentro do
    # teste, que ja' arrumou o path — e o defeito aparece SO' na publicacao.
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import canais_registro
    c = canais_registro.CANAIS.get(nome_buffer)
    return c.arroba.lstrip("@") if c else nome_buffer


def _serie_de_precos() -> dict:
    """{id: (primeira data vista, quantos pontos)} — a nossa serie.

    ⭐ ISTO E' O QUE TORNA A FRASE DO CARTAO VERDADEIRA. "Acompanhando desde
    12/09" so' pode ser escrito porque ha' 1.871 pontos gravados em
    `precos_vistos.jsonl` — se a serie nao existisse, a frase seria enfeite,
    e enfeite sobre preco e' exatamente o que a gente nao faz.
    ## ⛔ O DEFEITO QUE ESTA FUNCAO CONSERTOU, em 15/09/2026

    ⚠️ Ela fazia `maior = max(maior, v)` sobre TODOS os pontos. Mas o mesmo
    `id` recebe precos de ANUNCIOS DIFERENTES no mesmo dia — variante, kit
    maior, outro vendedor. O "Conjunto de pinceis" tinha isto:

        12/09  13,36
        13/09  13,36
        14/09  12,56  | 25,08  | 12,80  | 12,57   <- quatro no MESMO dia

    O 25,08 entrava como "maior preco ja' visto" e a pagina anunciava
    **queda de 49%** num produto que nao caiu. Medido em 8 dos 62 do
    catalogo, e o espalhamento do dia batia quase 1:1 com a queda mostrada:

        52% de espalhamento -> 51,9% de "queda"
        50%                 -> 49,0%
        46%                 -> 44,7%
        34%                 -> 34,0%   (Fone Lenovo GM2 Pro)
        32%                 -> 32,1%   (Carregador 120W)

    ⛔ Os dois ultimos sao CAMPEOES que abrem a pagina. A vitrine anunciava
    desconto que nao existia — exatamente o oposto do que ela promete
    ("o desconto e' medido contra o preco que NOS vimos").

    ⭐ O CONSERTO: cada DIA vira um valor so', e o valor e' o MENOR do dia.
    Menor, e nao media, porque na duvida entre duas variantes a conservadora
    e' a barata: ela puxa a "queda" pra baixo. Errar a favor do desconto e'
    o erro que ninguem reclama e que destroi a credibilidade.

    ⚠️ E `pontos` passa a contar DIAS distintos, nao linhas. "Acompanhando
    ha' 3 dias" com quatro leituras num dia so' seria mentira pequena, do
    tipo que ninguem confere e que nao deveria existir.
    """
    por_dia = _precos_por_dia()
    serie: dict = {}
    for i, dias in por_dia.items():
        if not dias:
            continue
        chaves = sorted(dias)
        serie[i] = (chaves[0], len(chaves), max(dias.values()), chaves[-1])
    return serie


def _precos_por_dia() -> dict:
    """{id: {dia: MENOR preco daquele dia}} — a serie consolidada, crua.

    ⭐ SEPARADA DE PROPOSITO: dois usos dependem dela e NAO podem divergir —
    `_serie_de_precos`, que decide a queda publicada, e o grafico do cartao,
    que a DESENHA. Se o desenho consolidasse por conta propria, ele poderia
    mostrar uma linha que a queda nao confirma.

    ⚠️ E isso nao e' hipotese: em 15/09/2026 foi exatamente a tentativa de
    DESENHAR a serie que revelou que dez produtos anunciavam desconto
    inexistente. Ferramenta de auditoria que le por um caminho proprio audita
    a si mesma, nao o dado.

    ⭐ A regra do MENOR do dia esta' explicada em `_serie_de_precos`, e mora
    aqui agora: um `id` recebe precos de ANUNCIOS DIFERENTES no mesmo dia.

    ⭐ TAMBEM GUARDA O MAIOR do dia (22/09/2026), so' pra alimentar
    `serie_limpa.detectar_oferta_dupla`: um dia com leitura BARATA e CARA
    juntas e' a prova de que o id tem duas ofertas de verdade, nao um
    ruido temporal. Ver o docstring de `sem_ponto_solto`.
    """
    import json
    arq = RAIZ / "estado" / "precos_vistos.jsonl"
    if not arq.exists():
        return {}
    por_dia: dict = {}
    maiores: dict = {}
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        i, q = d.get("id"), (d.get("quando") or "")[:10]
        if not i or not q:
            continue
        try:
            v = float(d.get("preco") or 0)
        except (TypeError, ValueError):
            continue
        if v <= 0:
            continue
        dias = por_dia.setdefault(i, {})
        dias[q] = min(dias[q], v) if q in dias else v
        altos = maiores.setdefault(i, {})
        altos[q] = max(altos[q], v) if q in altos else v
    return {i: _sem_ponto_solto(d, i, maiores.get(i)) for i, d in por_dia.items()}


# ⭐ A LIMPEZA MORA EM `engine/serie_limpa.py`, e nao aqui. TRES caminhos
# consolidam esta mesma serie -- a pagina, o `garimpo.historico` (cartaz do
# Telegram) e o `vitrine.preco_antes_de` (post do canal) -- e eles NAO podem
# divergir. Quando a limpeza existia so' aqui, o `teste_vitrine_com_cartaz`
# pegou na hora: o site dizia "sem queda" e o canal continuava anunciando
# "de R$ 21,73" do mesmo produto, no mesmo dia. Uma regra, um arquivo.
def _sem_ponto_solto(dias: dict, pid=None, maiores_do_dia: dict | None = None) -> dict:
    # ⛔ A RAIZ NO PATH ANTES DO IMPORT -- e' a convencao deste arquivo
    # (linhas 133, 350, 357 fazem o mesmo). Sem isso, `python
    # paginas/publicar_bio.py --subir` estoura ModuleNotFoundError: rodando
    # assim, o diretorio no path e' `paginas/`, nao a raiz. A suite NAO pega
    # porque os testes inserem a raiz eles mesmos.
    # ⚠ E' a SEGUNDA vez hoje que eu tropeco nisto (a primeira foi o
    # `foto_julga` no topo do modulo). Import dentro da funcao resolve o
    # teste; o path e' o que resolve a publicacao.
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import serie_limpa
    return serie_limpa.sem_ponto_solto(dias, pid, maiores_do_dia)


# ⭐ CATEGORIAS QUE NAO VIAJAM NA PAGINA — baixam quando a pessoa clica.
#
# Decisao do Bryan em 16/09/2026: "nao quero o site lento; se baixa so'
# quando a pessoa clica ai' e' outra coisa, mas inicialmente eu quero tudo bem
# fluido como ja' e'". MEDIDO no mesmo dia: a pagina pesa 258 KB (210 KB so'
# de JSON, 1.517 B por cartao); a Nike ate' R$ 150 sao 905 cartoes de 421 B
# = 372 KB — quase dobra a pagina sozinha. Entao a categoria vai num arquivo
# ao lado (`nike.json`) e o HTML leva so' o nome, a contagem e o passo.
#
# ⚠️ `passo` e' quantos cartoes por "ver mais" DENTRO dessa categoria: 50,
# e nao os 15 do `PASSO_BLOCO` — pedido do Bryan ("50 cards, mais baratos
# primeiro, depois os outros 50 mais caros").
EXTERNAS = {
    # loja no feed -> (nome da categoria na tela, arquivo, passo)
    "Nike BR": ("Nike", "nike.json", 50),
    # ⭐ BELEZA DE MARCA, UMA CATEGORIA POR MARCA — decisao do Bryan em
    # 16/09/2026: "Eudora, Avon, O Boticario ficam em uma secao separada
    # igual a Nike". Pedidas no Awin em 16/09; ate' aprovarem, o feed nao as
    # traz e o mapa e' inerte. Mesmo raciocinio do Calçados: produto de
    # marca no meio de organizador de R$ 11 muda o que a pagina parece ser.
    #
    # ⚠️ A CHAVE E' O `merchant_name` DO FEED, e ele so' se mede depois da
    # aprovacao. Os tres nomes abaixo sao os da API de programas; se o CSV
    # vier diferente ("O Boticário" sem "BR", por exemplo), a loja cai no
    # aviso de "loja sem mapa" do `produtos_externos` — e' so' corrigir a
    # chave. Nunca casar por "contem": "Avon" casaria "Avon Cosméticos
    # Revendedora" de outro anunciante.
    "oBoticario BR": ("O Boticário", "boticario.json", 50),
    "Eudora BR": ("Eudora", "eudora.json", 50),
    "Avon BR": ("Avon", "avon.json", 50),
    # ⭐ APROVADOS NA HORA em 16/09/2026 (joined foi de 1 pra 7 no mesmo dia
    # do pedido). Cada loja e' categoria propria pela regra da Nike — loja de
    # marca/ticket alto atras do menu. Nomes = API de programas; o
    # `merchant_name` do feed so' se mede com a chave (aviso "sem mapa").
    "Clovis Calçados BR": ("Clovis Calçados", "clovis.json", 50),
    "Lauri Esporte": ("Lauri Esporte", "lauri.json", 50),
    "Carraro BR": ("Carraro", "carraro.json", 50),
    "Leveros BR": ("Leveros", "leveros.json", 50),
    "Exypna": ("Exypna", "exypna.json", 50),
    "Radiale Pneus": ("Radiale Pneus", "radiale.json", 50),
    # aprovados na noite de 16/09
    "Kabum BR": ("Kabum", "kabum.json", 50),
    "Lacoste BR": ("Lacoste", "lacoste.json", 50),
    "Shark-Ninja BR": ("Shark Ninja", "sharkninja.json", 50),
    # aprovados em 18/09 (Bryan: "Arno cozinha, Camilovers beleza")
    "Arno BR": ("Arno", "arno.json", 50),
    "Camilovers BR": ("Camilovers", "camilovers.json", 50),
}
# ⛔ LOJAS APROVADAS QUE NAO ENTRAM NO SITE (Bryan, 18/09/2026, resposta ao
# ponto 4 da AUDITORIA: "dispersao — Carraro/Leveros/Radiale sem fit"; "OK,
# cortar lojas sem fit do site, ficam na serie"). Pneu e ar-condicionado
# no meio de organizador de R$ 11 mudam o que a pagina parece ser. A SERIE
# continua colhendo o feed delas (engine/awin.py nao muda): e' a pagina que
# nao as mostra. Continuam mapeadas em EXTERNAS de proposito — voltar e'
# tirar daqui, nao redescobrir a categoria.
# ⛔ Clovis (Bryan, 18/09/2026 a` noite): "tirar por enquanto — nao gostei do
# site deles, ruim de comprar, vai ser ruim pros clientes". Somou-se ao preco
# do feed que nao batia com a loja (regua_vitrine.QUARENTENA). A serie
# continua colhendo; a Awin aceitou mais parceiros — avaliar e incluir.
FORA_DO_SITE = {"Carraro BR", "Leveros BR", "Radiale Pneus", "Clovis Calçados BR"}
# ⭐ TETO DE TROCAS DE FOTO por publicacao (ver `_foto` em produtos_todos).
# Subiu em etapas em 18/09: 3 da calibracao -> 13 ("os proximos 10") -> SEM
# TETO ("gostei, pode aplicar em todas", Bryan, 18/09 12:50). Fica a
# constante pra voltar a limitar se uma rodada de fotos novas sair torta.
FOTOS_TROCAS_MAX = 10 ** 6
# ⚠️ IDADE MAXIMA DO INSTANTANEO. A mesma regra dos 24h do AliExpress: preco
# que nao foi reconferido hoje nao vai pro ar. Instantaneo velho = categoria
# fora, com aviso — nao categoria com preco de ontem.
EXTERNO_MAX_HORAS = 24
# ⚠️ queda de externa acima disto nao conta no heroi: e' o feed trocando
# variante, nao preco caindo (medido em 18/09 na Kabum: ate' 89% num dia).
EXTERNA_QUEDA_MAX = 60.0  # Bryan, 18/09: "pode ate 60%"


# ⭐ SELO "A LOJA DIZ" (Bryan, 17/09/2026): a Nike preenche `product_price_old`
# em 100% do feed. Se esse "de" e' maior que o MAIOR preco que a nossa serie
# ja' viu, com >= DE_INFLADO_DIAS_MIN dias de radar, o cartao diz: "a loja diz
# de R$ 349,99 · nunca vimos acima de R$ 249,99 em N dias". Ninguem faz isso
# porque a loja e' o anunciante. ⚠️ Nao e' acusacao de fraude: e' a nossa
# medicao ao lado do numero dela, e a pessoa decide.
DE_INFLADO_DIAS_MIN = 3
DE_INFLADO_FOLGA = 1.02


def _de_inflado(por_dia: dict, d: dict, de_loja: float) -> dict:
    if de_loja <= 0:
        return {}
    dias = por_dia.get(d.get("id")) or {}
    if len(dias) < DE_INFLADO_DIAS_MIN:
        return {}
    maior = max(dias.values())
    if maior <= 0 or de_loja <= maior * DE_INFLADO_FOLGA:
        return {}
    return {"loja": f"R$ {de_loja:.2f}".replace(".", ","),
            "nosso": f"R$ {maior:.2f}".replace(".", ","),
            "dias": len(dias)}


def _link_ml(d: dict, agora: dict) -> str:
    """Produto do ML: o link do ANUNCIO mais barato (o preco que o cartao
    mostra), vindo do instantaneo horario. "" = fica o link do registro.
    Ver mercadolivre.link_do_anuncio (defeito medido em 18/09)."""
    if (d.get("fonte") or "") != "mercadolivre":
        return ""
    item = (agora.get(str(d.get("id"))) or {}).get("item_id")
    if not item:
        return ""
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import mercadolivre as _ml
    return _ml.link_do_anuncio(item, d.get("canal") or "")


def _comissao_awin(loja: str) -> float:
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import awin as _awin
    return _awin.comissao_de(loja)


def _nome_externo(nome: str) -> str:
    """O nome do feed sem o codigo de SKU.

    ⭐ reparo 3 (18/09/2026, MAESTROS_ESTETICA §autopsia): "Kit com 3 Pares de
    Meias Sortidas Lupo - 03225 PRETO 41/44", "... - KSHPR256". O Ali passa
    pelo `nome_produto` (modelo); a externa nao, e o cartao mostrava SKU. Aqui
    e' REGRA, sem cota: cai o " - <codigo>..." do fim, o token de SKU
    (>= 6 chars com letras E digitos, ex.: KSHPR256, FB1362) e numero de
    6+ digitos (8513313). Fica o que e' especificacao curta (ABNT2, 700VA,
    M280) e a variante (PRETO 34) — na Clovis cada variante e' um produto.
    """
    import re as _re
    n = str(nome or "")
    # ⛔ 18/09 (Bryan): "Kit ... Olympikus - 1902 BRANCO 01 33/38" e "... -
    # 81924 BRANCO 39/44" viravam o MESMO nome, porque o corte levava tudo
    # depois do codigo — inclusive a cor e o TAMANHO, que e' o que os separa.
    # Cai so' o token do codigo; a variante fica.
    n = _re.sub(r"\s+-\s+\d\S*", " ", n)
    n = _re.sub(r"\s+-\s+[A-Z0-9-]{6,}\s*$", "", n)
    n = _re.sub(r"\b(?=[A-Z0-9-]{6,}\b)(?=[A-Z0-9-]*\d{2})(?=[A-Z0-9-]*[A-Z]{2})[A-Z0-9-]+\b", "", n)
    n = _re.sub(r"\b\d{6,}\b", "", n)
    n = _re.sub(r"\s{2,}", " ", n).strip(" -–—·,")
    return n or str(nome or "")


def _categoria_externa(loja: str, categoria_feed: str, nome: str) -> str:
    """A AREA do produto externo, na mesma escala do catalogo proprio.

    ⛔ Bryan, 18/09/2026: "a categoria nunca pode ser o nome da loja, tem que
    ser o que e' sobre a loja de fato". Ate' aqui a externa entrava com
    canal = loja ("Nike", "Kabum"), e o menu Categoria misturava Cozinha,
    Fitness... com nomes de loja. Loja e' o menu Loja; aqui e' a area.

    O feed da Nike/Kabum traz caminho de categoria; Clovis e Lauri vem sem
    nada, e o nome decide (Tenis/Bota/Sandalia -> Calcados). O que nao casa
    cai na area padrao da loja — nunca no nome dela.
    """
    import re as _re
    c = (categoria_feed or "").lower()
    n = (nome or "").lower()
    calcado = _re.search(r"\b(t[eê]nis|sand[aá]lia|bota|chinelo|sapat|sapatilha|tamanco|chuteira|papete|mocassim|rasteir)", n)
    if loja == "Kabum BR":
        if _re.search(r"eletroport|aspirador|cafeteira|air ?fryer|liquidificador|ventilador|purificador", c + " " + n):
            return "Casa"
        if _re.search(r"roupas|camiseta|bon[eé]|mochila", c):
            return "Moda"
        if _re.search(r"escrit[oó]rio|cadeira|mesa", c):
            return "Casa"
        return "Eletrônicos"
    if loja == "Nike BR":
        if "calçados" in c or "calcados" in c or calcado:
            return "Calçados"
        return "Moda"
    if loja == "Clovis Calçados BR":
        return "Calçados" if calcado or not _re.search(r"\b(meia|bolsa|carteira|cinto|mochila|bon[eé])", n) else "Moda"
    if loja == "Lauri Esporte":
        return "Calçados" if calcado else "Fitness"
    if loja == "Arno BR":
        return "Cozinha"
    if loja == "Shark-Ninja BR":
        return "Cozinha" if _re.search(r"ninja|liquidificador|creami|pote|air ?fryer|panela", n) else "Casa"
    if loja == "Exypna":
        return "Mercado"
    if loja == "Lacoste BR":
        return "Calçados" if calcado else "Moda"
    if loja == "Camilovers BR":
        return "Beleza"
    return "Achadinhos"


def produtos_externos() -> dict[str, dict]:
    """{categoria: {"arquivo", "passo", "produtos": [cartoes]}} — o que vai
    em arquivo separado. {} quando nao ha' instantaneo valido.

    ⭐ NAO TOCA NA REDE. Le' `estado/awin_catalogo.json`, gravado por
    `python -m engine.awin --guardar` na nuvem. Publicar e' montar; coletar e'
    outro passo, com outra credencial.

    ⭐ O CARTAO E' O MESMO do AliExpress: `pontos`, `serie`, `queda`, `antes`
    e `dias` saem da MESMA serie (`precos_vistos.jsonl`, id `awin:<id>`).
    Produto que entrou hoje cai em "achados novos" (pontos < 2) e sem
    grafico (< 3 dias) — a pagina ja' faz isso sozinha, e foi o padrao que o
    Bryan fixou em 16/09: "A com o selo do C, sempre pode ser assim".

    ⚠️ `vendas` = 0 e `ganho` = preco x 7,5% — o feed nao diz quantos a loja
    vendeu. A ordem "mais baratos primeiro" e' feita pela PAGINA para
    categoria externa (ver `todos.html`), nao por este campo.
    """
    import json
    from datetime import datetime, timezone
    arq = RAIZ / "estado" / "awin_catalogo.json"
    if not arq.exists():
        print("externos: sem estado/awin_catalogo.json — nenhuma categoria "
              "externa vai ao ar")
        return {}
    try:
        inst = json.loads(arq.read_text(encoding="utf-8"))
        quando = datetime.fromisoformat(inst["quando"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"externos: instantaneo ilegivel ({e}) — categoria fora")
        return {}
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=timezone.utc)
    idade_h = (datetime.now(timezone.utc) - quando).total_seconds() / 3600
    if idade_h > EXTERNO_MAX_HORAS:
        print(f"externos: instantaneo tem {idade_h:.0f}h (> {EXTERNO_MAX_HORAS}h)"
              " — categoria FORA do ar ate' a proxima coleta")
        return {}
    serie = _serie_de_precos()
    por_dia = _precos_por_dia()
    saida: dict[str, dict] = {}
    from engine import tendencias_ml as _tm
    _termos_alta = _tm.termos()
    sem_mapa: dict[str, int] = {}
    fora: dict[str, int] = {}
    for p in inst.get("produtos") or []:
        if (p.get("loja") or "") in FORA_DO_SITE:
            fora[p["loja"]] = fora.get(p["loja"], 0) + 1
            continue
        cfg = EXTERNAS.get(p.get("loja") or "")
        if not cfg:
            # ⚠️ LOJA APROVADA SEM CATEGORIA: nao entra e AVISA. Silencio aqui
            # e' "a Eudora aprovou e nunca apareceu no site" sem ninguem saber.
            sem_mapa[p.get("loja") or "?"] = sem_mapa.get(p.get("loja") or "?", 0) + 1
            continue
        if not p.get("link") or not p.get("nome"):
            continue
        cat, arquivo, passo = cfg
        try:
            preco = float(p.get("preco") or 0)
        except (TypeError, ValueError):
            continue
        if preco <= 0:
            continue
        pid = "awin:" + str(p.get("id"))
        d = {"id": pid, "preco": f"R$ {preco:.2f}".replace(".", ",")}
        saida.setdefault(cat, {"arquivo": arquivo, "passo": passo,
                               "produtos": []})["produtos"].append({
            "nome": _nome_externo(p["nome"]),
            "preco": d["preco"],
            "link": p["link"],
            "imagem": p.get("imagem", ""),
            "queda": _queda_real(serie, d),
            "vendas": 0,
            # ⭐ pela comissao REAL da loja (awin.comissao_de) — ate' 17/09
            # eram 7,5% pra todas, o numero da Nike; o Kabum paga 1,15%.
            "ganho": round(preco * _comissao_awin(p.get("loja") or "") / 100, 2),
            "antes": _antes(serie, d),
            "subiu": _subiu(serie, por_dia, d),
            "dias": _dias(serie, d),
            "pontos": serie.get(pid, ("", 0, 0.0, ""))[1],
            "serie": _serie_curta(por_dia, d),
            "visto": f"{inst['quando'][8:10]}/{inst['quando'][5:7]}",
            # ⭐ 18/09: canal = AREA do produto (Eletrônicos, Calçados...), e a
            # loja fica no seu campo. O arquivo/menu Loja continua por `cat`.
            "canal": _categoria_externa(p.get("loja") or "", p.get("categoria") or "", p.get("nome") or ""),
            "id": pid,
            "combina": [],
            "loja": cat,
            # ⭐ SELO 3: {"loja": "R$ 349,99", "nosso": "R$ 249,99", "dias": N}
            # quando a loja anuncia um "de" acima do MAIOR preco que NOS ja'
            # vimos em >= 3 dias. Vazio senao.
            "de_inflado": _de_inflado(por_dia, d, float(p.get("de_loja") or 0)),
            "em_alta": _tm.em_alta(p["nome"], _termos_alta),
        })
    for loja, n in sem_mapa.items():
        print(f"externos: ⚠️ loja SEM MAPA em EXTERNAS: {loja!r} ({n} produtos) "
              "— aprovada no Awin mas fora do site ate' ganhar categoria")
    for loja, n in fora.items():
        print(f"externos: {loja!r} fica FORA do site por decisao ({n} produtos; "
              "FORA_DO_SITE)")
    for cat, bloco in saida.items():
        bloco["produtos"].sort(key=lambda x: float(
            x["preco"].replace("R$", "").replace(",", ".")))
        print(f"externos: {cat} {len(bloco['produtos'])} produto(s) "
              f"-> {bloco['arquivo']}")
    # ⭐ Nota de Vitrine tambem nas externas (Confianca = 0 ate' haver dado)
    from engine import regua_vitrine
    for b in saida.values():
        _marcar_cliques(b["produtos"])
        regua_vitrine.pontuar(b["produtos"])
    return saida


def economia(dados: list[dict], dias: int = 14) -> dict:
    """Quanto a menos se paga HOJE comprando um de cada produto que caiu —
    e a mesma soma, dia a dia, pra linha.

    ⭐ Pedido do Bryan em 16/09/2026: "um grafico medindo o valor que ja' foi
    economizado, somando o desconto de cada produto: custava 20, hoje custa
    10, esses 10 e' o economizado — montar isso num montante".

    ⚠️ E' ECONOMIA OFERECIDA, nao realizada: a operacao ainda nao tem venda
    medida, entao o numero diz "comprando um de cada hoje", e o rotulo da
    pagina diz isso. Inflar seria facil (somar o "de/por" da loja); por isso
    a conta e' a MESMA do cartao: `antes` (maior dia visto por nos) menos o
    preco de hoje, e so' quando `antes` existe (queda real >= 2%).

    ⚠️ A linha e' calculada com a serie consolidada (`_precos_por_dia`), a
    MESMA do grafico de cada cartao: pra cada dia D, soma de (maior preco
    ate' D) - (ultimo preco ate' D), sobre os produtos que estao no ar HOJE.
    So' produtos de hoje, de proposito: o que saiu do ar nao "economiza".
    """
    from datetime import date, timedelta
    hoje_total, n = 0.0, 0
    for d in dados:
        if not d.get("antes"):
            continue
        try:
            a = float(d["antes"].replace("R$", "").replace(".", "").replace(",", ".").strip())
            h = float(str(d["preco"]).replace("R$", "").replace(".", "").replace(",", ".").strip())
        except ValueError:
            continue
        if a > h:
            hoje_total += a - h
            n += 1
    por_dia = _precos_por_dia()
    ids = [d.get("id") for d in dados]
    # ids da serie podem ser int (AliExpress) ou str (ML/awin); casa os dois
    def _dias_de(i):
        return por_dia.get(i) or (por_dia.get(int(i)) if str(i).isdigit() else None) or {}
    serie = []
    for k in range(dias - 1, -1, -1):
        dia = (date.today() - timedelta(days=k)).isoformat()
        total = 0.0
        for i in ids:
            ds = _dias_de(i)
            ate = {q: v for q, v in ds.items() if q <= dia}
            if not ate:
                continue
            ultimo = ate[max(ate)]
            maior = max(ate.values())
            if maior > ultimo * 1.02:
                total += maior - ultimo
        serie.append([dia[5:], round(total, 2)])
    # ⚠️ corta os dias iniciais em que nada existia (linha comeca do primeiro
    # dia com serie), senao o desenho abre com um zero artificial
    while serie and serie[0][1] == 0 and len(serie) > 3:
        serie.pop(0)
    # ⛔ O ULTIMO PONTO E' O NUMERO DO CARTAO. A serie consolida o dia pelo
    # MENOR preco visto; o cartao mostra a ULTIMA leitura (instantaneo de hora
    # em hora). Medido em 16/09: R$ 344 pela serie x R$ 293 pelos cartoes.
    # Dois totais do mesmo dado na mesma tela e' exatamente o que a pagina
    # nao faz — o que o visitante soma nos cartoes tem de ser o fim da linha.
    if serie and serie[-1][0] == date.today().isoformat()[5:]:
        serie[-1][1] = round(hoje_total, 2)
    return {"hoje": round(hoje_total, 2), "n": n, "serie": serie}


def economia_radar(dias: int = 30) -> dict:
    """O MULTOMETRO: quanto de queda o radar JA' ENCONTROU, somando todos os
    produtos que passaram por ele — e a soma dia a dia, que SO' SOBE.

    ⭐ Decisao do Bryan em 16/09/2026: "o volume vai ser o valor de economia
    dos RADARES, nao de vendas — ainda nao temos volume de venda, e mudar o
    multometro no futuro vai pegar mal". Ele fica assim desde o dia 1.

    ⭐ A DEFINICAO QUE SO' SOBE: por produto, (maior preco que NOS vimos) -
    (menor preco que NOS vimos). O maior so' cresce e o menor so' cai, entao
    a diferenca nunca diminui — sem truque de acumulo. Produto que saiu do ar
    continua contando: a queda foi encontrada e medida.

    ⚠️ O QUE ELE E': queda encontrada pelo radar, contra a nossa propria
    serie (a mesma do "de" riscado). O QUE NAO E': dinheiro que alguem pos no
    bolso — isso pede venda, e o rotulo da pagina diz "que o radar ja'
    encontrou", nao "economizado por voce". Piso de 2% por produto, igual ao
    cartao: abaixo disso e' arredondamento e cambio, nao queda.
    """
    from datetime import date, timedelta
    por_dia = _precos_por_dia()
    serie = []
    total_hoje, n_hoje = 0.0, 0
    for k in range(dias - 1, -1, -1):
        dia = (date.today() - timedelta(days=k)).isoformat()
        total, n = 0.0, 0
        for _i, ds in por_dia.items():
            # ⛔ SO' O QUE O RADAR VIGIA (18/09/2026). A serie das lojas externas
            # vem do FEED, uma leitura por dia, e o feed da Kabum trocou
            # R$ 15.599 por R$ 5.999 no mesmo id de um dia pro outro (variante
            # ou "de"/"por"). Isso levou o multometro de R$ 3.602 a R$ 128.907
            # numa tarde — erro a nosso favor, o que ninguem contesta. Queda
            # "encontrada pelo radar" e' a que o radar reconfere de hora em hora.
            if str(_i).startswith("awin:"):
                continue
            ate = [v for q, v in ds.items() if q <= dia]
            if len(ate) < 2:
                continue
            maior, menor = max(ate), min(ate)
            if maior > menor * 1.02:
                total += maior - menor
                n += 1
        serie.append([dia[5:], round(total, 2)])
        total_hoje, n_hoje = total, n
    while serie and serie[0][1] == 0 and len(serie) > 3:
        serie.pop(0)
    return {"total": round(total_hoje, 2), "produtos": n_hoje, "serie": serie}



# ⭐ A GALERIA DO DESTAQUE NO PC (24/09/2026, Bryan: "em vez dessa imagem
# gigante e muitas vezes desconexa ou esticada, varias imagens do mesmo
# anuncio de maneira organizada"). As fotos JA' existiam: `precos.puxar`
# guarda `product_small_image_urls` do Ali em `precos_agora.json` desde
# 18/09 (MEDIDO hoje: 164 de 168 produtos, 157 com 5), e so' serviam para
# escolher a capa. Sobem num arquivo AO LADO, que so' o PC baixa: no celular
# o custo e' zero.
#
# Acervo: Maestros/WooCommerce (DEMONSTRADO) -- principal + secundarias; e a
# regra de quando NAO usar: "se os produtos nao tiverem imagens secundarias".
# Por isso o piso: menos de GALERIA_MIN fotos boas = o produto fica com a
# foto unica de sempre.
#
# ⛔ QUEM SAI: foto JULGADA pelo modelo de visao (`foto_julga`) que e'
# colagem ou tem nota abaixo de GALERIA_NOTA_MIN. Foto NAO julgada entra,
# depois das julgadas boas: na galeria, detalhe com medida escrita ajuda; o
# que desmonta a vitrine e' colagem e banner. (Hoje so' 53 das 809 extras
# estao julgadas -- rodar `foto_julga.medir` nelas melhora o filtro.)
GALERIAS_ARQUIVO = "galerias.json"
GALERIA_MIN = 3
GALERIA_MAX = 5
GALERIA_NOTA_MIN = 5


def montar_galerias(dados: list[dict]) -> dict[str, list[str]]:
    from engine import foto_julga
    agora = _precos_agora()
    fim: dict[str, list[str]] = {}
    for p in dados:
        pid = str(p.get("id") or "")
        principal = p.get("imagem") or ""
        extras = (agora.get(pid) or {}).get("imagens") or []
        if not pid or not principal or not extras:
            continue
        boas, sem_julgamento = [], []
        for u in extras:
            if not u or u == principal:
                continue
            j = foto_julga.julgado(u)
            if not j:
                sem_julgamento.append(u)
            elif not j.get("colagem") and int(j.get("nota") or 0) >= GALERIA_NOTA_MIN:
                boas.append((int(j.get("nota") or 0), u))
        boas.sort(key=lambda x: -x[0])
        fotos = [principal] + [u for _, u in boas] + sem_julgamento
        vistas, lista = set(), []
        for u in fotos:
            if u not in vistas:
                vistas.add(u)
                lista.append(u)
        if len(lista) >= GALERIA_MIN:
            fim[pid] = lista[:GALERIA_MAX]
    return fim


def montar_catalogo() -> tuple[str, dict[str, str]]:
    """O HTML do catalogo com os produtos e o brasao dentro, e os arquivos
    das categorias externas ({nome do arquivo: JSON}) que sobem ao lado."""
    import json
    if not CATALOGO.exists():
        return "", {}
    # ⚠️ O CATALOGO PASSA PELA MESMA LIMPEZA da bio: os comentarios daqui
    # explicam a operacao (medicao, decisao, data de incidente) e nao tem por
    # que viajar pro repositorio publico. Sem isto o detector reprova — e
    # reprovou, na primeira tentativa.
    html = mascarar(tirar_comentarios(CATALOGO.read_text(encoding="utf-8")))
    dados = produtos_todos()
    externos = produtos_externos()
    # ⚠️ O HTML LEVA SO' O INDICE das externas: nome, arquivo, quantos e o
    # passo. Os cartoes ficam no arquivo ao lado.
    # ⭐ 18/09: alem da contagem por area (`cats`), os CLIQUES de 30 dias por
    # loja e por area (`cliques`, `cats_cliques`) — e' por eles que os menus
    # Categoria e Loja se ordenam (Bryan: "em primeiro as que mais vendem";
    # venda ainda nao ha' pra medir, clique e' o sinal que temos).
    indice = {}
    for cat, b in externos.items():
        cats: dict[str, int] = {}
        cats_cl: dict[str, int] = {}
        cl = 0
        caiu = 0
        for x in b["produtos"]:
            cats[x["canal"]] = cats.get(x["canal"], 0) + 1
            cats_cl[x["canal"]] = cats_cl.get(x["canal"], 0) + int(x.get("cliques_30") or 0)
            cl += int(x.get("cliques_30") or 0)
            # ⭐ "baixaram de preco" do heroi conta a externa tambem (Bryan,
            # 18/09: "apenas 30?" — era so' o catalogo proprio). Teto de 30%:
            # acima disso, no feed, e' variante trocada (Kabum: 7 itens com
            # "queda" ate' 89% no mesmo dia), nao queda. O radar proprio nao
            # tem teto porque reconfere de hora em hora.
            if 5 <= float(x.get("queda") or 0) <= EXTERNA_QUEDA_MAX:
                caiu += 1
        indice[cat] = {"arquivo": b["arquivo"], "n": len(b["produtos"]),
                       "passo": b["passo"], "cats": cats,
                       "cliques": cl, "cats_cliques": cats_cl, "caiu": caiu}
    arquivos = {b["arquivo"]: json.dumps(
        {"categoria": cat, "produtos": b["produtos"]}, ensure_ascii=False)
        for cat, b in externos.items()}
    # 19/09: o link de afiliado do Ali (1.065 chars, nao comprime) sai do
    # HTML e vai em `links.json`; a primeira tela fica com o link dentro.
    links = separar_links(dados)
    if links:
        arquivos[LINKS_ARQUIVO] = json.dumps({"links": links}, ensure_ascii=False)
    galerias = montar_galerias(dados)
    if galerias:
        arquivos[GALERIAS_ARQUIVO] = json.dumps({"galerias": galerias}, ensure_ascii=False)
    print(f"galerias: {len(galerias)} produto(s) com {GALERIA_MIN}+ fotos boas")
    # ⚠️ ESTOURA SE O MARCADOR SUMIR. Substituicao que nao acha o alvo e segue
    # publicaria um catalogo VAZIO com cara de pronto.
    eco = economia(dados)
    eco["radar"] = economia_radar()
    for alvo, valor in (("  var PRODUTOS = [];",
                         "  var PRODUTOS = " + json.dumps(
                             dados, ensure_ascii=False) + ";"),
                        ("  var ECONOMIA = {};",
                         "  var ECONOMIA = " + json.dumps(eco) + ";"),
                        ("  var EXTERNOS = {};",
                         "  var EXTERNOS = " + json.dumps(
                             indice, ensure_ascii=False) + ";"),
                        ('  var BRASAO = "";',
                         '  var BRASAO = "' + _brasao_total() + '";'),
                        ("  var SIMBOLOS = {};",
                         "  var SIMBOLOS = " + json.dumps(simbolos_lojas()) + ";"),
                        ('  var LINKS_ARQUIVO = "";',
                         '  var LINKS_ARQUIVO = "' + (LINKS_ARQUIVO if links else "") + '";'),
                        ('  var GALERIAS_ARQUIVO = "";',
                         '  var GALERIAS_ARQUIVO = "' + (GALERIAS_ARQUIVO if galerias else "") + '";'),
                        # ⭐ selo 2: o @ do bot do "avise-me"; "" = sem botao
                        ('  var BOT_ALERTA = "";',
                         '  var BOT_ALERTA = "' + _bot_alerta() + '";'),
                        # ⭐ a hora da ultima reconferencia (painel do garimpo, 18/09)
                        ('  var ULTIMA_CONFERENCIA = "";',
                         '  var ULTIMA_CONFERENCIA = "' + _ultima_conferencia() + '";'),
                        # ⚠️ elemento, nao comentario: os comentarios saem
                        # ANTES desta troca (tirar_comentarios)
                        ('  <section id="indice-estatico" aria-hidden="true"></section>',
                         '  <section id="indice-estatico" aria-hidden="true">'
                         + indice_estatico(dados) + '</section>')):
        if alvo not in html:
            raise SystemExit("catalogo: marcador sumiu -> " + alvo.strip())
        html = html.replace(alvo, valor, 1)
    print(f"multometro: R$ {eco['radar']['total']:.2f} de queda encontrada em "
          f"{eco['radar']['produtos']} produto(s), linha de {len(eco['radar']['serie'])} dia(s)")
    print(f"catalogo: {len(dados)} produto(s)"
          + (f" + externas: " + ", ".join(
              f"{c} {v['n']}" for c, v in indice.items()) if indice else ""))
    return html, arquivos


# ⭐ OS SIMBOLOS OFICIAIS DAS LOJAS (kit de afiliado), em data URI.
#
# Pedido do Bryan em 16/09/2026: o simbolo oficial no lugar da sigla ("Ali",
# "ML"). O arquivo vem do KIT DE AFILIADO de cada programa — nao de imagem
# baixada da internet — e o nome do arquivo e' o nome da loja como aparece
# em `LOJA_DA_FONTE` / no campo `loja` do cartao: `Mercado Livre.png`,
# `AliExpress.svg`, `Nike.png`. Loja sem arquivo continua com a sigla.
#
# ⚠️ PNG/WebP sao reduzidos a 32 px de altura antes de virar data URI: o
# selo tem 14 px e a pagina inteira viaja em cada visita. SVG vai como esta'.
SIMBOLOS_DIR = RAIZ / "paginas" / "simbolos_lojas"


_CLIQUES: dict = {}


def _cliques_30() -> dict:
    """{produto_id: cliques nos ultimos 30 dias} do Supabase (PAT local).
    ⚠️ FALHA ABERTA: sem PAT ou sem rede devolve {} e os cartoes saem sem
    `cliques_medidos` — o kill de 30 dias nao dispara por falta de dado."""
    if "d" in _CLIQUES:
        return _CLIQUES["d"]
    try:
        if str(RAIZ) not in sys.path:
            sys.path.insert(0, str(RAIZ))
        from engine import cliques as _cl
        d = {k: v["cliques"] for k, v in _cl.por_produto(30).items()}
        _CLIQUES["d"] = d
        _CLIQUES["ok"] = True
    except Exception as e:                            # noqa: BLE001
        print(f"cliques: nao lidos ({type(e).__name__}) — kill de 30 dias desligado nesta rodada")
        _CLIQUES["d"] = {}
        _CLIQUES["ok"] = False
    return _CLIQUES["d"]


def _marcar_cliques(cartoes: list[dict]) -> None:
    d = _cliques_30()
    for c in cartoes:
        c["cliques_30"] = int(d.get(str(c.get("id")), 0))
        c["cliques_medidos"] = bool(_CLIQUES.get("ok"))


def _ultima_conferencia() -> str:
    """ISO da leitura mais nova do instantaneo horario ("" se nao houver)."""
    try:
        agora = _precos_agora()
        return max((v.get("quando") or "") for v in agora.values()) if agora else ""
    except Exception:  # noqa: BLE001
        return ""


def _bot_alerta() -> str:
    """O @ do bot do "avise-me quando cair" (engine/alertas.py), ou "" —
    e sem @ a pagina nao desenha o botao. Nunca inventa um @."""
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import alertas as _al
    return _al.bot_username() or ""


def simbolos_lojas() -> dict[str, str]:
    """{loja: data URI} de tudo que houver em `paginas/simbolos_lojas/`."""
    import base64
    import io
    if not SIMBOLOS_DIR.is_dir():
        return {}
    saida: dict[str, str] = {}
    for arq in sorted(SIMBOLOS_DIR.iterdir()):
        ext = arq.suffix.lower()
        if ext == ".svg":
            saida[arq.stem] = ("data:image/svg+xml;base64,"
                               + base64.b64encode(arq.read_bytes()).decode("ascii"))
        elif ext in (".png", ".webp", ".jpg", ".jpeg"):
            from PIL import Image
            im = Image.open(arq).convert("RGBA")
            if im.height > 32:
                im = im.resize((max(1, round(im.width * 32 / im.height)), 32), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=90)
            saida[arq.stem] = ("data:image/webp;base64,"
                               + base64.b64encode(buf.getvalue()).decode("ascii"))
    return saida


def _brasao_total() -> str:
    """A lupa, em data URI. Vazio se a arte nao existir (a pagina aguenta)."""
    arq = RAIZ / "paginas" / "avatares" / "_data_uris.txt"
    if not arq.exists():
        return ""
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if linha.startswith("achadinho.total	"):
            return linha.split("	", 1)[1]
    return ""


def _nome_bonito(d: dict) -> str:
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import nome_produto
    return nome_produto.nome_de(d)


def _desde(serie: dict, d: dict) -> str:
    """dd/mm da primeira vez que vimos o preco deste produto."""
    q = serie.get(d.get("id"), ("", 0, 0.0, ""))[0]
    return f"{q[8:10]}/{q[5:7]}" if len(q) == 10 else ""


def _inteiro(pid):
    """O mesmo id como INTEIRO, ou None quando nao for numero.

    ⚠ Existe so' para atravessar a fronteira de tipo entre a serie
    (chave int, de precos_vistos.jsonl) e o instantaneo (chave str, de
    precos_agora.json). Devolver None em vez de levantar mantem a guarda
    falhando FECHADA: id torto continua sem leitura, nao vira leitura falsa.
    """
    try:
        return int(pid)
    except (TypeError, ValueError):
        return None


def _visto_em(serie: dict, agora: dict, pid) -> str:
    """A data da ULTIMA LEITURA do produto: o maior entre o ultimo ponto da
    serie e a reconferencia horaria (`precos_agora.json`, campo `quando`).

    ⛔ MEDIDO EM 19/09/2026 00:10: o site ia amanhecer com 1 PRODUTO. A
    guarda de 24h lia so' a serie, e a serie ganha ponto so' quando o preco
    MUDA (`anotar_serie`) ou no garimpo diario — e o garimpo de 18/09 perdeu
    o push (corrida com outro commit, sem rebase). Dia quieto + push perdido
    = "ninguem foi visto ontem" = catalogo vazio. A reconferencia horaria
    existe e diz a verdade: 157 de 160 reconferidos as 23:33.
    """
    pid = str(pid or "")
    # ⛔ A SERIE E' CHAVEADA POR INTEIRO, o instantaneo por TEXTO.
    # MEDIDO em 21/09/2026: precos_vistos.jsonl grava "id": 1005007542604477
    # (int) e precos_agora.json grava "1005007096727922" (str). Com pid
    # normalizado para TEXTO, serie.get(pid) NUNCA casava, e esta metade da
    # guarda estava MORTA em producao: o _todos inteiro dependia so' do
    # instantaneo horario. E' o "amanhecer com 1 produto" descrito acima —
    # o reparo de 19/09 mascarou o defeito de tipo em vez de corrigi-lo.
    # Procurar pelos DOIS tipos e' o unico jeito de a serie voltar a contar.
    da_serie = (serie.get(pid) or serie.get(_inteiro(pid))
                or ("", 0, 0.0, ""))[3] or ""
    reg = agora.get(pid) if isinstance(agora, dict) else None
    da_hora = (reg.get("quando") or "")[:10] if isinstance(reg, dict) else ""
    return max(da_serie, da_hora)


def produtos_todos() -> list[dict]:
    """TODOS os produtos que ainda valem — o catalogo do site mae.

    ⚠️ A DIFERENCA PRA `produtos_reais` NAO E' SO' O TAMANHO. Ali a regra e'
    vitrine (4 por canal, os mais novos); aqui e' catalogo: tudo o que ainda
    esta' de pe', com o canal junto pra dar pra filtrar.

    ⚠️ E A MESMA TRAVA DE HONESTIDADE: so' entra quem teve o preco
    reconferido nas ultimas 48h. Catalogo grande com preco velho e' pior que
    catalogo pequeno — quem clica encontra outro numero na loja.
    """
    import json
    from datetime import date, timedelta
    arq = RAIZ / "estado" / "produtos_publicados.jsonl"
    if not arq.exists():
        return []
    serie = _serie_de_precos()
    por_dia = _precos_por_dia()
    notas = _notas()
    vendas_desde = _vendas_desde()
    vendedores = _vendedores()
    agora = _precos_agora()
    from engine import tendencias_ml as _tm
    _termos_alta = _tm.termos()
    from engine import alertas as _al, regua_vitrine as _rv
    _olho = _al.de_olho()
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import combina as _c
    _combina = _c.ler_cache()
    from engine import foto_limpa as _fl
    _medidas_fotos = _fl.medidas()
    # ⚠️ EM ETAPAS, ordem do Bryan (18/09/2026, "vai tocando com os proximos
    # 10"): 3 trocas foram ao ar com a calibracao; agora mais 10. O teto vale
    # na ordem do catalogo (mais novos primeiro), entao o conjunto e' estavel
    # entre publicacoes. Subir o teto = decisao dele, depois de olhar.
    _trocas_feitas = [0]

    def _foto(d):
        principal = d.get("imagem", "")
        if _trocas_feitas[0] >= FOTOS_TROCAS_MAX:
            return principal
        extras = (agora.get(str(d.get("id") or "")) or {}).get("imagens") or []
        esc = _fl.escolher(principal, extras, _medidas_fotos)
        if esc != principal:
            _trocas_feitas[0] += 1
        return esc
    # ⚠️ 24 HORAS, e nao 48 — decisao do Bryan em 15/09/2026 ("48 e' muito").
    #
    # ⛔ E A TRAVA FALHA FECHADA AGORA. Ela era `if visto_em and visto_em <
    # limite`, entao produto SEM leitura nenhuma na serie passava direto: a
    # guarda so' barrava quem tinha data velha, e deixava entrar quem nao
    # tinha data. "Preco reconferido nas ultimas 24h" tem de significar que a
    # reconferencia EXISTE. Custo medido da mudanca: 158 -> 152 produtos.
    limite = (date.today() - timedelta(days=1)).isoformat()
    vistos, saida = set(), []
    linhas = []
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            linhas.append(json.loads(linha))
        except ValueError:
            continue
    for d in sorted(linhas, key=lambda x: x.get("quando") or "", reverse=True):
        if not d.get("link") or not d.get("nome"):
            continue
        marca = d.get("id") or d.get("nome")
        if marca in vistos:
            continue
        visto_em = _visto_em(serie, agora, d.get("id"))
        if not visto_em or visto_em < limite:
            continue
        vistos.add(marca)
        quando = (d.get("quando") or "")[:10]
        saida.append({
            "nome": _nome_bonito(d),
            "preco": _preco_de_hoje(por_dia, d) or d.get("preco", ""),
            "link": _link_ml(d, agora) or d["link"],
            # ⭐ A FOTO SEM BANNER (18/09/2026, MAESTROS_DESIGN_DO_SITE.md,
            # defeito 1): entre as fotos do anuncio, a que e' o MESMO produto
            # com menos texto — medido na nuvem (engine/foto_limpa.py).
            # Falha aberta: sem medida, a principal.
            "imagem": _foto(d),
            # ⛔ A QUEDA E' RECALCULADA AQUI, e nao lida do registro.
            #
            # ⚠️ O valor gravado em `produtos_publicados.jsonl` foi calculado
            # com o historico ANTIGO, que somava varias leituras do MESMO dia
            # — leituras de anuncios diferentes sob o mesmo id. Em 15/09/2026
            # isso publicava "caiu 49%" num produto que nao caiu, em 8 dos 62
            # do catalogo. `engine/garimpo.py` ja' foi consertado, mas o que
            # ja' esta' gravado continuaria mentindo ate' o produto sair.
            #
            # ⭐ `_serie_de_precos()` ja' devolve o maior preco POR DIA
            # consolidado, entao recalcular aqui conserta o que esta' no ar
            # sem precisar reescrever o registro.
            "queda": _queda_real(serie, d),
            "vendas": int(d.get("vendas") or 0),
            # ⭐ O QUE O PRODUTO RENDE POR VENDA. Cruzado com `vendas` no
            # navegador, vira a ordem do catalogo: primeiro o que tem mais
            # chance de virar dinheiro, nao o que entrou por ultimo.
            #
            # ⚠️ NAO E' CONVERSAO NOSSA. `vendas` e' o que o mercado inteiro
            # comprou na loja, nao o que nos vendemos — nao vendemos nada
            # ainda. Serve pra COMPARAR dois produtos; nao serve pra prometer
            # faturamento. Vira medicao de verdade quando o `tracking_id` por
            # canal existir e houver venda atribuida.
            "ganho": round(float(d.get("ganho_previsto") or 0), 2),
            "antes": _antes(serie, d),
            "subiu": _subiu(serie, por_dia, d),
            "dias": _dias(serie, d),
            "pontos": serie.get(d.get("id"), ("", 0, 0.0, ""))[1],
            # ⭐ A SERIE DESENHADA. Vazia ate' haver 3 dias — ver
            # `_serie_curta`, que explica por que 2 pontos nao viram linha.
            "serie": _serie_curta(por_dia, d),
            # ⭐ % DE AVALIACOES POSITIVAS (evaluate_rate do AliExpress), que o
            # garimpo grava na serie e o registro publicado nao guarda. So'
            # aparece no cartao com fogo; e' um dos criterios dele.
            "nota": notas.get(str(d.get("id")), 0.0),
            "ja_esteve": _ja_esteve(por_dia, d),
            # ⭐ {"dias": N} quando hoje e' o menor da serie com N >= 14 dias
            "recorde": _recorde(por_dia, d),
            # ⭐ O MENOR PRECO QUE NOS VIMOS (21/09/2026). Irmao do `antes`,
            # que e' o maior. A capa usa os dois para dizer onde o preco de
            # hoje esta' na faixa que ja' andou.
            "menor": _menor(por_dia, d),
            # ⭐ [vendidos desde que acompanhamos, "dd/mm"] ou []
            "vendeu": list(vendas_desde.get(str(d.get("id")), ())),
            # ⭐ so' ML: [vendedores hoje, a mais desde, "dd/mm"] ou []
            "vendedores": vendedores.get(str(d.get("id")), []),
            # ⭐ so' ML (regua v2): frete gratis e reputacao do vendedor, do
            # instantaneo horario. Ausentes = sem dado, nunca "ruim".
            "frete_gratis": bool((agora.get(str(d.get("id"))) or {}).get("frete_gratis", False)),
            # ⭐ envio (so' ML por enquanto): {"full": bool, "de": "SP"}
            "envio": (agora.get(str(d.get("id"))) or {}).get("envio") or {},
            # ⭐ termo em alta no Mercado Livre contido no nome (regua v2) ou ""
            "em_alta": _tm.em_alta(_nome_bonito(d), _termos_alta),
            # ⭐ #3 (18/09): quantas pessoas pediram aviso (numero real) e se e'
            # consumivel (ganha "lembrar em 30 dias" no botao)
            "de_olho": int(_olho.get(str(d.get("id")), 0)),
            "recorrente": bool(_rv.recorrente({"nome": _nome_bonito(d)})),
            "reputacao": (agora.get(str(d.get("id"))) or {}).get("reputacao") or {},
            # ⭐ quando o preco foi reconferido pela ultima vez ("hoje 19:00" ou
            # "15/09"): a ancora que TODO produto tem, quando nao ha' Promo
            # nem vendas medidas — a promessa da pagina dita em numero
            "conferido": _conferido_em(d),
            "visto": f"{quando[8:10]}/{quando[5:7]}" if len(quando) == 10 else "",
            # ⚠️ O NOME DE EXIBICAO, nao a chave. A chave e' nome interno
            # (`atefalhar`, `fatura.chora`) e vazaria a estrutura da operacao
            # pra dentro do JSON da pagina publica — a guarda pegou.
            # ⭐ E de quebra o filtro fica legivel: "Até Falhar", nao "@atefalhar".
            # ⚠️ AREA, e nao canal: ver AREA_DO_CANAL. O campo continua se
            # chamando `canal` porque e' a chave que o upsell usa pra dizer
            # "vai bem com" — mas o que viaja e o que aparece e' a area.
            "canal": _area(d.get("canal") or ""),
            # ⭐ QUEM COMBINA COM ESTE, julgado por modelo e guardado em
            # cache (ver engine/combina.py). Vazio = a pagina cai na regra
            # de palavras, que e' pior mas e' conhecida.
            "id": str(d.get("id") or d.get("nome")),
            "combina": _combina.get(str(d.get("id") or d.get("nome")), []),
            # ⭐ A LOJA E' CAMPO DO CARTAO desde 16/09/2026 — decisao do Bryan:
            # selo de canto na cor da loja, so' a marca, sem escrever o nome;
            # e um seletor "Loja" ao lado de "Categoria". E' o que torna
            # honesto mostrar o MESMO produto duas vezes (Brasil rapido x
            # AliExpress barato): o comprador escolhe o prazo, nao a gente.
            "loja": LOJA_DA_FONTE.get(d.get("fonte") or "aliexpress", "AliExpress"),
        })
    # ⭐ O MESMO PRODUTO DE DOIS LOJISTAS VIRA UM CARTAO SO'.
    #
    # ⚠️ A dedupe acima e' por `id` do anuncio, e nunca teve como pegar isto:
    # dois lojistas vendendo o mesmo Ralador tem ids diferentes. O Bryan viu
    # dois cartoes iguais no iPhone em 15/09 — "isso nao pode acontecer".
    #
    # ⛔ E nao da' pra resolver pelo nome: medido, "pinceis x esponjas"
    # (DIFERENTES) pontua mais alto que "Espelho x Espelho" (O MESMO). Ver
    # `engine/duplicata.py` — quem decide e' a foto.
    from engine import duplicata
    # ⛔ A DEDUPE E' POR LOJA, nunca ENTRE lojas. O mesmo liquidificador no
    # AliExpress e no Mercado Livre tem a MESMA foto — e e' pra aparecer nos
    # dois cartoes (regra do Bryan, 16/09: "publica o melhor de cada canal,
    # o cliente escolhe na hora"). Fundir os dois esconderia justamente a
    # escolha que a pagina existe pra dar.
    por_loja: dict[str, list[dict]] = {}
    for x in saida:
        por_loja.setdefault(x["loja"], []).append(x)
    fim: list[dict] = []
    for grupo in por_loja.values():
        fim += duplicata.sem_repetidos(grupo)
    # ordem original (a vitrine decide a ordem, nao a dedupe)
    pos = {id(x): i for i, x in enumerate(saida)}
    fim = sorted(fim, key=lambda x: pos[id(x)])
    fim = sem_salto_de_variante(fim, por_dia)
    # ⭐ SELO 1 (17/09/2026): o mesmo produto em OUTRA loja, lado a lado.
    n_pares = duplicata.pares_entre_lojas(fim)
    if n_pares:
        print(f"pares entre lojas: {n_pares} cartao(oes) com irmao em outra loja")
    # ⭐ A NOTA DE VITRINE (17/09/2026, CRITERIOS_DA_VITRINE.md): uma regua
    # so' para a ordem, o fogo e a 2a posicao do ML. Escreve `vitrine_nota`
    # e `vitrine_fora` em cada cartao; fogo e ML leem a nota abaixo.
    from engine import regua_vitrine
    _marcar_cliques(fim)
    regua_vitrine.pontuar(fim)
    marcar_fogo(fim)
    marcar_vitrine_ml(fim)
    marcar_topo(fim)
    marcar_capa(fim)
    return fim


# ⭐ OS 10 PRIMEIROS DA VITRINE: 5 ate' R$ 99,90 + 5 livres, INTERCALADOS, o
# barato abrindo ("Eu garimpo. Voce paga menos"). Decisao do Bryan, 17/09/2026,
# depois dos mentores: ENP (R$ 8-50 tira o medo) x Hormozi (ganho por clique).
# E' um TESTE DE 30 DIAS: os cliques por produto (clique_produto) decidem em
# 17/10 se o teto vira regra ou se o misto fica.
#
# ⛔ BARATO SO' SE RENDER — "nao podemos postar so' porque e' barato e nao
# lucrar" (Bryan). Piso: ganho por venda >= TOPO_GANHO_MIN (o mesmo do fogo).
# O fone de R$ 41 com 67 mil vendas rende R$ 2,86: fica fora do topo.
TOPO_BARATO = 99.90
TOPO_GANHO_MIN = 3.0        # = FOGO_GANHO_MIN (definido abaixo); um piso so'
TOPO_N = 10


# rodizio da capa: uma troca a cada 3 horas (24/09/2026, Bryan)
CAPA_RODIZIO_S = 3 * 3600


def marcar_capa(dados: list[dict]) -> dict | None:
    """Escreve `capa: True` no UNICO produto que abre a vitrine. Devolve ele.

    ⭐ A CAPA NAO É MAIS "O PRIMEIRO DA LISTA". Até 21/09/2026 o heroi era
    `lista[0]` -- o primeiro do TOPO, que por desenho é o melhor BARATO, nao
    o melhor produto. MEDIDO no mesmo dia: o topo1 tinha nota 79,4 enquanto o
    topo2 e o topo4 tinham 80,5. A capa mostrava o mais barato qualificado, e
    o Bryan queria o melhor.

    Os pisos estao em CAPA_* e no comentario delas. Entre os que passam,
    ganha a maior `vitrine_nota`; empate, o maior ganho x vendas.

    ⚠ PODE DEVOLVER None, e a pagina tem de aguentar: em dia sem queda forte
    nenhum produto passa. Nesse caso a vitrine cai no comportamento antigo
    (o primeiro da lista), que é pior mas nao é vazio.
    """
    # ⚠ IMPORT AQUI DENTRO, e nao no topo do modulo. O
    # `teste_guarda_confirma_nomeando` importa `publicar_bio` com a pasta
    # `paginas` no path mas SEM a raiz, e um `from engine import ...` no topo
    # derruba o import inteiro com ModuleNotFoundError. `regua_vitrine` ja
    # era importada dentro da funcao pelo mesmo motivo -- eu quebrei o padrao
    # e a suite pegou.
    from engine import foto_julga
    # ⭐ O INSTANTANEO E' LIDO UMA VEZ, e nao por produto: e' dele que saem
    # as fotos EXTRAS do anuncio, e `_precos_agora()` le arquivo.
    agora_fotos = _precos_agora()
    trocas = []
    for p in dados:
        p.pop("capa", None)
    # ⭐ CAPA FIXADA A MAO (24/09/2026, Bryan: "ja' sobe o SSD pra vitrine").
    # `estado/capa_fixa.json` = {"id": "...", "ate": "AAAA-MM-DDTHH:MM"} (UTC).
    # Vale ate' `ate`; depois o rodizio volta sozinho. E' ordem do dono: passa
    # por cima da regua E do piso da foto -- o log diz isso com todas as letras.
    import json as _json, datetime as _dt
    fixa = RAIZ / "estado" / "capa_fixa.json"
    if fixa.exists():
        try:
            f = _json.loads(fixa.read_text(encoding="utf-8"))
            if _dt.datetime.utcnow().isoformat() < str(f.get("ate") or ""):
                for p in dados:
                    if str(p.get("id")) == str(f.get("id")) and not p.get("vitrine_fora"):
                        p["capa"] = True
                        p["fogo"] = True
                        print("capa: FIXADA A MAO ate' " + str(f.get("ate")) + " UTC -- "
                              + (p.get("nome") or "")[:46])
                        return p
                print("capa: fixada a mao, mas o id " + str(f.get("id")) + " nao esta' no catalogo -- segue a regua")
        except (ValueError, OSError) as e:
            print("capa: capa_fixa.json ilegivel (" + str(e) + ") -- segue a regua")
    cand = []
    for p in dados:
        if p.get("vitrine_fora"):
            continue
        preco = _preco_hoje_num(p)
        ganho = float(p.get("ganho") or 0)
        regua = (0 < preco <= CAPA_PRECO_MAX
                 and ganho / preco * 100 >= CAPA_GANHO_PCT_MIN
                 and float(p.get("nota") or 0) >= FOGO_NOTA_MIN
                 and float(p.get("queda") or 0) >= FOGO_QUEDA_MIN
                 and int(p.get("vendas") or 0) >= FOGO_VENDAS_MIN
                 and len(p.get("serie") or []) >= CAPA_SERIE_MIN)
        # ⭐ 24/09/2026 (Bryan: "entre foguinho e os da regra, rotacionando a
        # cada 3 horas"): quem tem FOGUINHO tambem entra no rodizio da capa,
        # desde que tenha grafico (3+ pontos) e passe no piso da foto abaixo.
        fogo_ok = bool(p.get("fogo")) and preco > 0 and len(p.get("serie") or []) >= 3
        if not (regua or fogo_ok):
            if p.get("fogo"):
                print("capa: foguinho sem grafico (%d ponto(s)) -- %s"
                      % (len(p.get("serie") or []), (p.get("nome") or "")[:46]))
            continue
        # ⭐ A FOTO TAMBEM E' PISO (21/09/2026). A regua acertou todos os
        # numeros -- 62.879 vendas, 19,4% de ganho, 61,5% de queda -- e
        # escolheu uma COLAGEM de quatro cenas com texto queimado. Nem o OCR
        # nem o CLIP pegavam: o primeiro mede texto (0,0356, ABAIXO da
        # mediana de 0,0568) e o segundo mede semelhanca contra a principal,
        # que E' a colagem. Quem responde a pergunta certa e' um modelo de
        # visao -- ver engine/foto_julga.py e a aferição de 6 fotos que esta'
        # no cabecalho dele.
        # ⚠ FALHA ABERTA: foto sem julgamento PASSA. A guarda barra colagem
        # conhecida; ela nao pode esvaziar a capa quando a API esta' fora.
        if not foto_julga.serve_de_capa(p.get("imagem") or "", CAPA_FOTO_NOTA_MIN):
            # ⭐ FOTO RUIM TROCA, E SO' DESQUALIFICA SE NAO HOUVER TROCA.
            # Ordem do Bryan em 21/09: "temos que ter uma extra boa pra nao
            # perder vendas". Ate' aqui a foto ruim matava o produto, e o
            # preco dele era o melhor da lista.
            #
            # ⚠️ O TAMANHO DO PREJUIZO, MEDIDO no catalogo de 21/09: dos 7
            # produtos que passam em TODO o resto da regua, 5 eram barrados
            # SO' pela foto -- 71%. Depois de julgar as 23 extras desses 5,
            # 2 voltam com foto nota 10 e nota 9. Os candidatos a capa vao
            # de 2 para 4.
            #
            # ⛔ E A TROCA E' ESCOLHA, NUNCA EDICAO. `engine/fidelidade.py`
            # registra que o inpainting REFEZ o produto com menos detalhe e
            # ainda assim tirou 0,9786 -- acima de qualquer limiar util. A
            # guarda de fidelidade nao pega degradacao, entao redesenhar
            # quebraria a ordem de 15/09 ("nao pode ir pra internet o
            # produto que nao e' de acordo") sem nada ficar vermelho.
            extras = (agora_fotos.get(str(p.get("id") or "")) or {}).get("imagens") or []
            nova = foto_julga.melhor_foto(p.get("imagem") or "", extras,
                                          CAPA_FOTO_NOTA_MIN)
            if nova == (p.get("imagem") or ""):
                print("capa: fora do rodizio, sem foto boa -- " + (p.get("nome") or "")[:46])
                continue
            trocas.append((p.get("nome") or "", nova))
            p["imagem"] = nova
        cand.append(p)
    # ⚠️ A TROCA APARECE NO LOG. Publicacao que troca a foto do produto em
    # silencio e' exatamente o tipo de mudanca que ninguem confere depois.
    for nome, url in trocas:
        print("capa: foto trocada por extra nota "
              + str(foto_julga.julgado(url).get("nota")) + " -- " + nome[:46])
    if not cand:
        # ⭐ RESERVA POR QUEDA REAL (22/09/2026). Ate' hoje, sem ninguem na
        # regua, a vitrine caia no 1o da lista -- um regador que SUBIU de
        # preco (59,39 -> 60,09) virou capa e o Bryan perguntou por que o
        # grafico "comeca de baixo". A capa tem de mostrar um grafico que
        # vem do caro para o barato, e a unica forma honesta e' escolher um
        # produto que CAIU de verdade -- nunca desenhar queda onde nao ha'.
        # Entre os que tem queda >= 5% e serie de 3+ pontos, a maior queda
        # ganha; a foto continua sendo piso (troca por extra boa, senao pula).
        # ⚠ SEM foguinho: a reserva nao passou na regua mais dura, e o fogo
        # diz exatamente isso.
        reserva = [p for p in dados
                   if not p.get("vitrine_fora")
                   and float(p.get("queda") or 0) >= 5
                   and len(p.get("serie") or []) >= 3
                   and _preco_hoje_num(p) > 0]
        reserva.sort(key=lambda x: (-float(x.get("queda") or 0),
                                    -float(x.get("vitrine_nota") or 0)))
        for p in reserva:
            img = p.get("imagem") or ""
            if not foto_julga.serve_de_capa(img, CAPA_FOTO_NOTA_MIN):
                extras = (agora_fotos.get(str(p.get("id") or "")) or {}).get("imagens") or []
                nova = foto_julga.melhor_foto(img, extras, CAPA_FOTO_NOTA_MIN)
                if nova == img:
                    continue
                p["imagem"] = nova
                print("capa: foto trocada por extra nota "
                      + str(foto_julga.julgado(nova).get("nota")) + " -- "
                      + (p.get("nome") or "")[:46])
            p["capa"] = True
            print(f"capa: NENHUM passou na regua -- reserva pela maior queda real: "
                  f"{(p.get('nome') or '')[:40]} ({float(p.get('queda') or 0):.0f}%, "
                  f"{len(p.get('serie') or [])} pontos)")
            return p
        print("capa: NENHUM produto passou na regua nem na reserva -- a vitrine cai no 1o da lista")
        return None
    cand.sort(key=lambda x: (-float(x.get("vitrine_nota") or 0),
                             -(float(x.get("ganho") or 0) * int(x.get("vendas") or 0))))
    # ⭐ RODIZIO DE 3 HORAS (24/09/2026, Bryan). A janela e' o relogio (UTC
    # // 3 h), nao o numero de publicacoes: o vigia publica quando a janela
    # vira (ver `janela_capa` em publicar_ao_mudar_agendado.ps1). Com 8
    # janelas por dia, 2-3 candidatos passam 3-4 vezes cada pela capa.
    import time as _t
    janela = int(_t.time() // CAPA_RODIZIO_S)
    escolhido = cand[janela % len(cand)]
    escolhido["capa"] = True
    # ⭐ OS OUTROS DO RODIZIO ABREM A GRADE, logo depois da capa (Bryan: "nao
    # estando na vitrine, deixe eles como os primeiros produtos"). Entram na
    # frente do topo da regua (`marcar_topo`), que desce uma casa por eles.
    resto = [p for p in cand if p is not escolhido]
    for p in resto:
        p.pop("topo", None)
    k = len(resto)
    for p in dados:
        if isinstance(p.get("topo"), int):
            p["topo"] += k
    for i, p in enumerate(resto, 1):
        p["topo"] = i
    # ⭐ A CAPA ACENDE O FOGUINHO, e isso e' decisao, nao efeito colateral.
    # Pedido do Bryan: "esses produtos da capa devem ter essa informacao".
    # Ele nao ganharia o fogo sozinho porque `marcar_fogo` usa o piso
    # ABSOLUTO de R$ 3 -- e acabamos de medir que esse piso e' o que barra os
    # melhores baratos. A capa passou por uma regua MAIS DURA (o mesmo
    # nota+queda+vendas, mais ganho proporcional e serie de 5 pontos), entao
    # negar o fogo a ela seria a mesma medida errada duas vezes.
    escolhido["fogo"] = True
    pr = _preco_hoje_num(escolhido)
    print(f"capa: rodizio de {len(cand)}, janela {janela % len(cand) + 1}; escolhido nota "
          f"{escolhido.get('vitrine_nota')} a R$ {pr:.2f} "
          f"(ganho {float(escolhido.get('ganho') or 0) / pr * 100:.1f}% do preco, "
          f"queda {float(escolhido.get('queda') or 0):.0f}%, "
          f"{len(escolhido.get('serie') or [])} pontos de serie)")
    return escolhido


def marcar_topo(dados: list[dict]) -> list[dict]:
    """Escreve `topo` (1..10) nos escolhidos; a pagina os poe na frente."""
    for p in dados:
        p.pop("topo", None)
    vivos = [p for p in dados if not p.get("vitrine_fora")]
    vivos.sort(key=lambda p: -float(p.get("vitrine_nota") or 0))
    baratos = [p for p in vivos if _preco_hoje_num(p) <= TOPO_BARATO
               and float(p.get("ganho") or 0) >= TOPO_GANHO_MIN]
    livres = [p for p in vivos if p not in baratos]
    # ⚠️ SEM NOME REPETIDO NO TOPO: duas "Balanca digital de cafe" (anuncios
    # diferentes, fotos diferentes) ocupavam a 3a e a 9a posicao em 17/09.
    # A chave e' o comeco do nome (4 palavras, sem acento).
    import unicodedata as _u

    def _raiz(p):
        n = _u.normalize("NFKD", str(p.get("nome") or "")).encode("ascii", "ignore").decode().lower()
        return " ".join(n.split()[:4])
    vistos: set = set()

    def _proximo(fila):
        while fila:
            c = fila.pop(0)
            if _raiz(c) not in vistos:
                vistos.add(_raiz(c))
                return c
        return None
    saida: list[dict] = []
    while len(saida) < TOPO_N and (baratos or livres):
        c = _proximo(baratos)
        if c:
            saida.append(c)
        if len(saida) < TOPO_N:
            c = _proximo(livres)
            if c:
                saida.append(c)
        if not baratos and not livres:
            break
    for i, p in enumerate(saida, 1):
        p["topo"] = i
    return saida


# ⛔ SALTO DE VARIANTE = ESGOTADO. Medido em 16/09/2026 no kit de 46 chaves:
# serie R$ 34,10 / 46,09 / 34,79 em 14/09 e R$ 112,59 em 15/09 — a variante
# barata ESGOTOU, a API passou a devolver a cara, e o site vendia "o kit de
# R$ 34" a R$ 112 com "no radar ha' 2 dias". O Bryan abriu a loja e viu
# "Esgotado". A API de afiliado nao expoe estoque (37 campos, nenhum); o
# salto e' o unico sinal, e ele e' claro: preco de hoje > 1,8x o menor visto
# nao e' alta de preco, e' outro produto.
SALTO_VARIANTE = 1.8


def sem_salto_de_variante(dados: list[dict], por_dia: dict) -> list[dict]:
    fica = []
    for p in dados:
        dias = por_dia.get(p.get("id")) or (por_dia.get(int(p["id"])) if str(p.get("id", "")).isdigit() else None) or {}
        try:
            hoje = float(str(p.get("preco", "")).replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
        except ValueError:
            hoje = 0.0
        if dias and hoje > SALTO_VARIANTE * min(dias.values()):
            print(f"fora (salto de variante {hoje / min(dias.values()):.1f}x, provavel esgotado): "
                  f"{p.get('nome', '')[:50]}")
            continue
        fica.append(p)
    return fica


def marcar_vitrine_ml(dados: list[dict]) -> dict | None:
    """Poe `vitrine: True` no MELHOR produto do Mercado Livre — a pagina o
    encaixa na 2a posicao do topo.

    ⭐ Bryan, 16/09/2026: "coloque 1 dos melhores do ML junto com os do Ali
    que estao no topo; a pagina principal e' nossa vitrine". Sem isto o ML
    nunca chegaria ao topo: a ordem de abertura e' ganho x vendas, e no ML
    `vendas` e' o numero de VENDEDORES (a API nao da' volume), sempre pequeno.

    ⚠️ O melhor pela NOSSA regua, nao o mais barato: vendedores x ganho por
    venda — quem tem mais gente vendendo e rende mais. Um por dia; se a
    regua empatar, fica o mais barato.
    """
    ml = [p for p in dados if p.get("loja") == "Mercado Livre"
          and float(str(p.get("preco", "0")).replace("R$", "").replace(".", "").replace(",", ".").strip() or 0) <= 250]
    for p in dados:
        p["vitrine"] = False
    if not ml:
        return None
    # ⭐ desde 17/09/2026: pela Nota de Vitrine; desempate pelo antigo
    # vendedores x ganho, depois o mais barato. Quem esta' no piso nao entra.
    ml = [p for p in ml if not p.get("vitrine_fora")] or ml
    ml.sort(key=lambda x: (-float(x.get("vitrine_nota") or 0),
                           -(int(x.get("vendas") or 0) * float(x.get("ganho") or 0)),
                           float(str(x.get("preco", "0")).replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)))
    ml[0]["vitrine"] = True
    return ml[0]


def _vendas_desde() -> dict[str, tuple[int, str]]:
    """{id: (vendidos desde o 1o dia da serie, 'dd/mm')} — crescimento do
    volume da loja MEDIDO POR NOS, entre a primeira e a ultima leitura.

    ⭐ Bryan, 16/09/2026: "teria como voltar alguma coisa das vendas que fosse
    mais real?". O total da loja (113 mil) nao se confere na pagina dela
    ("este vendedor: 10.000+"); o que a gente mediu — "+792 vendidos desde
    14/09" — e' nosso, cresce todo dia e nao briga com numero nenhum.

    ⚠️ CONSERVADOR por construcao: o garimpo so' grava o volume quando ele
    anda >= 10% (VOLUME_MUDOU_FRAC), entao o crescimento e' "pelo menos".
    """
    import json as _j
    arq = RAIZ / "estado" / "precos_vistos.jsonl"
    vol: dict[str, dict[str, int]] = {}
    if not arq.exists():
        return {}
    for linha in arq.read_text(encoding="utf-8").splitlines():
        try:
            d = _j.loads(linha)
        except ValueError:
            continue
        try:
            v = int(d.get("vol") or 0)
        except (TypeError, ValueError):
            continue
        q = (d.get("quando") or "")[:10]
        # ⛔ NO MERCADO LIVRE `vol` E' VENDEDORES, nao vendas (17/09/2026):
        # "+2 vendidos" com 2 vendedores novos seria mentira pequena. Ver
        # `_vendedores`.
        if v <= 0 or not q or d.get("loja") == "Mercado Livre":
            continue
        dias = vol.setdefault(str(d.get("id")), {})
        dias[q] = max(dias.get(q, 0), v)
    saida: dict[str, tuple[int, str]] = {}
    for i, dias in vol.items():
        if len(dias) < 2:
            continue
        ordem = sorted(dias)
        ganho = dias[ordem[-1]] - dias[ordem[0]]
        if ganho > 0:
            saida[i] = (ganho, f"{ordem[0][8:10]}/{ordem[0][5:7]}")
    return saida


def _vendedores() -> dict[str, list]:
    """{id: [vendedores hoje, quantos a mais desde o 1o dia, 'dd/mm']} — so'
    Mercado Livre.

    ⭐ A PROVA SOCIAL DO ML (17/09/2026). A API nao da' vendas; da' um anuncio
    por vendedor, e esse numero a pessoa confere na pagina da loja. O cartao
    escreve "+2 vendedores desde 16/09" quando cresceu, "13 vendedores na
    loja" quando nao — nunca um "vendidos" que nao medimos.

    ⚠️ O ultimo `vol` > 0 do ultimo dia e' o "hoje"; o primeiro dia com
    `vol` > 0 e' a base. Pontos com vol 0 (a serie de 16/09, antes de a
    reconferencia gravar vendedores) nao contam como base nem como hoje.
    """
    import json as _j
    arq = RAIZ / "estado" / "precos_vistos.jsonl"
    if not arq.exists():
        return {}
    vol: dict[str, dict[str, int]] = {}
    for linha in arq.read_text(encoding="utf-8").splitlines():
        try:
            d = _j.loads(linha)
        except ValueError:
            continue
        if d.get("loja") != "Mercado Livre":
            continue
        try:
            v = int(d.get("vol") or 0)
        except (TypeError, ValueError):
            continue
        q = (d.get("quando") or "")[:10]
        if v <= 0 or not q:
            continue
        dias = vol.setdefault(str(d.get("id")), {})
        dias[q] = max(dias.get(q, 0), v)
    saida: dict[str, list] = {}
    for i, dias in vol.items():
        ordem = sorted(dias)
        hoje, base = dias[ordem[-1]], dias[ordem[0]]
        saida[i] = [hoje, max(0, hoje - base) if len(ordem) > 1 else 0,
                    f"{ordem[0][8:10]}/{ordem[0][5:7]}"]
    return saida


def _conferido_em(d: dict) -> str:
    from datetime import datetime, timezone, timedelta
    reg = _precos_agora().get(str(d.get("id") or ""))
    q = (reg or {}).get("quando") or ""
    try:
        t = datetime.fromisoformat(q)
    except ValueError:
        return ""
    t = t.astimezone(timezone(timedelta(hours=-3)))          # BRT
    hoje = datetime.now(timezone(timedelta(hours=-3))).date()
    return f"hoje às {t:%H:%M}" if t.date() == hoje else f"{t:%d/%m}"


def _notas() -> dict[str, float]:
    """{id: ultima nota (%) vista na serie}."""
    import json as _j
    arq = RAIZ / "estado" / "precos_vistos.jsonl"
    saida: dict[str, float] = {}
    if not arq.exists():
        return saida
    for linha in arq.read_text(encoding="utf-8").splitlines():
        try:
            d = _j.loads(linha)
        except ValueError:
            continue
        try:
            v = float(d.get("nota") or 0)
        except (TypeError, ValueError):
            continue
        if v > 0:
            saida[str(d.get("id"))] = v
    return saida


# ⭐ O FOGUINHO — Bryan, 16/09/2026: "produtos extremamente selecionados, bons
# para o cliente e para nos, com chance grande de vender; leva em conta
# principalmente satisfacao; velocidade de entrega tambem".
#
# ⚠️ REGUA MEDIDA ANTES DE LIGAR (catalogo de 16/09, 148 produtos): com
# "vendas >= 3x mediana" passavam ZERO; com a regua abaixo passam 3 a 5.
# Raro e' o que da' valor ao sinal — por isso o TETO.
#
# O que cada criterio responde:
#   nota      >= 95%   bom pro cliente (evaluate_rate; a mediana e' 98%, o
#                      garimpo ja' corta os ruins na entrada)
#   queda     >= 15%   contra a NOSSA serie, nunca o de/por da loja
#   vendas    >= 1000  gente comprou (unico "numero de pessoas" que a API da')
#   rende     ganho >= R$ 3/venda OU comissao >= 10%   vale pra nos
#   entrega            so' o ML expoe (Mercado Envios Full); conta a favor
#                      como DESEMPATE, nao como exigencia — o AliExpress nao
#                      tem prazo na API de afiliado (37 campos, nenhum)
FOGO_NOTA_MIN = 95.0
FOGO_QUEDA_MIN = 15.0
FOGO_VENDAS_MIN = 1000
FOGO_GANHO_MIN = 3.0
FOGO_COMISSAO_MIN = 10.0
FOGO_TETO = 6

# ⭐ A REGUA DA CAPA (21/09/2026). O heroi da vitrine deixou de ser "o
# primeiro da lista" e passou a ser ESCOLHIDO: pedido do Bryan -- "tem que ser
# um produto top que esteja vendendo muito muito e que nos de' um bom lucro e
# que seja elegivel para estar na capa", com foguinho e grafico.
#
# ⛔ O PISO DE GANHO AQUI É PROPORCIONAL, E ESSA É A MUDANCA. MEDIDO em
# 21/09/2026, entre os 120 produtos vivos de até R$ 99:
#
#   passam em nota + queda + vendas .......... 14
#   desses, passam no ganho >= R$ 3 ........... 1   <- a trava
#   afrouxar a QUEDA de 15% para 5% ........... 1   <- NAO era a queda
#
# O piso absoluto matava justamente os melhores da faixa barata POR SEREM
# baratos: R$ 1,45 num produto de R$ 6,36 é 22,8% do preco -- proporcionalmente
# muito melhor que R$ 3 num de R$ 150, que é 2%. Os 14 barrados tinham 62 mil
# a 113 mil vendas e quedas de 46% a 69%.
#
# ⚠ ISTO NAO ABANDONA A REGRA DE 17/09 ("nao podemos postar so' porque é
# barato e nao lucrar"): muda a UNIDADE, de reais para proporcao. O ganho
# absoluto por venda cai para ~R$ 1,50 e só se paga no volume -- que estes
# produtos tem. O piso de R$ 3 continua valendo no TOPO e no FOGO da grade.
CAPA_PRECO_MAX = 99.0
CAPA_GANHO_PCT_MIN = 6.0
# ⚠ SERIE MINIMA: a capa mostra o GRAFICO, e grafico precisa de historia.
# Com 3 pontos ele existe (`_serie_curta`), mas a capa exige 5 -- a auditoria
# estetica de 18/09 já tinha decidido que "a linha do grafico quando é reta
# é ornamento", e na capa ela ocupa espaco nobre.
CAPA_SERIE_MIN = 5
# ⭐ O PISO DA NOTA DA FOTO, agora MEDIDO em 138 das 148 (21/09/2026). O 7
# era chute, tirado de uma aferição de SEIS fotos, e ele estava errado.
#
# 'Limpa' = sem colagem, sem texto queimado, fundo limpo e produto inteiro:
#
#   nota 10 ... 18 limpas / 0 sujas        piso  7 ... 32 sujas de 77 (42%)
#   nota  9 ... 20 limpas / 2 sujas        piso  8 ... 11 de 56 (20%)
#   nota  8 ...  7 limpas / 9 sujas        piso  9 ...  2 de 40 ( 5%)
#   nota <=7 .. 0 limpas / 61 sujas        piso 10 ...  0 de 18 ( 0%)
#
# ⭐ ABAIXO DE 8 NAO EXISTE UMA UNICA FOTO LIMPA -- 61 de 61 tem colagem,
# texto queimado, fundo poluido ou produto cortado. O piso 7 aprovava 32
# fotos sujas, 42% de tudo que ele deixava passar: era ele a porta por onde
# a colagem de quatro cenas entrou na capa.
#
# ⚠ E 9, NAO 10: o 10 descarta 27 das 45 fotos limpas para ganhar 2 sujas
# a menos. O 9 erra 5% e guarda a folga -- e com 148 produtos a capa precisa
# de candidato sobrando, nao de perfeicao.
#
# ⚠ MEDIDO no catalogo de hoje: 2 candidatos a capa com piso 7, 8, 9 E 10.
# As duas fotos que chegam ao fim da regua tiram 10 -- apertar de 7 para 9
# nao custa candidato nenhum hoje, so' fecha a porta.
# ⚠ A distribuicao NAO e' bimodal. Com 69 julgadas eu disse que era e havia
# um 'vale' no 7; com 138 ele sumiu. Era tamanho de amostra.
CAPA_FOTO_NOTA_MIN = 9


def marcar_fogo(dados: list[dict]) -> list[dict]:
    """Poe `fogo: True` nos que passam na regua, ate' o teto. Devolve eles."""
    import json as _j
    comissao: dict[str, float] = {}
    arq = RAIZ / "estado" / "produtos_publicados.jsonl"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            try:
                r = _j.loads(linha)
                comissao[str(r.get("id"))] = float(r.get("comissao") or 0)
            except (ValueError, TypeError):
                continue
    cand = []
    for p in dados:
        p["fogo"] = False
        nota = float(p.get("nota") or 0)
        ganho = float(p.get("ganho") or 0)
        com = comissao.get(str(p.get("id")), 0.0)
        if (nota >= FOGO_NOTA_MIN and float(p.get("queda") or 0) >= FOGO_QUEDA_MIN
                and int(p.get("vendas") or 0) >= FOGO_VENDAS_MIN
                and (ganho >= FOGO_GANHO_MIN or com >= FOGO_COMISSAO_MIN)):
            cand.append(p)
    # ⭐ desde 17/09/2026 a ORDEM dos candidatos e' a Nota de Vitrine (uma
    # regua so'); desempate pelo antigo ganho x vendas. Os pisos acima ficam.
    cand = [p for p in cand if not p.get("vitrine_fora")]
    cand.sort(key=lambda x: (-float(x.get("vitrine_nota") or 0),
                             -(float(x.get("ganho") or 0) * int(x.get("vendas") or 0))))
    for p in cand[:FOGO_TETO]:
        p["fogo"] = True
    return cand[:FOGO_TETO]


# fonte no registro -> nome da loja no cartao (o que o seletor "Loja" mostra)
LOJA_DA_FONTE = {
    "aliexpress": "AliExpress",
    "mercadolivre": "Mercado Livre",
    "shopee": "Shopee",
    "shein": "Shein",
}


# ⚠️ O SITE MAE NAO FALA DE CANAL.
#
# Decisao do Bryan em 14/09/2026: quem abre a casa da operacao nao precisa
# saber que existem cinco TikToks por tras. Isso e' estrutura NOSSA, e nao
# informacao util pra quem esta' comprando — no melhor caso e' ruido, no pior
# parece que estamos separando o que mostramos pra cada um.
#
# ⭐ O QUE SOBRA NO LUGAR E' MELHOR: a area do produto. "Beleza" e "Cozinha"
# dizem ao comprador o que ele vai achar ali; "Achadinho Make" nao diz nada a
# quem nunca viu o canal.
AREA_DO_CANAL = {
    "truque.importado": "Beleza",
    "cozinha.importada": "Cozinha",
    "atefalhar": "Fitness",
    "achadinhos.instantaneos": "Casa",
    "fatura.chora": "Eletrônicos",
    "modofuturo": "Tecnologia",
    "semanestesia.pod": "Livros",
    # ⭐ PSEUDO-CANAIS DA VARREDURA — 15/09/2026. Eles existem so' pra dar
    # AREA a produto que nenhum canal cobre: a varredura larga trouxe 26
    # pecas de carro, jardim e ferramenta, e sem isto todas cairiam em
    # "Achadinhos", que e' o balaio de quem nao tem casa.
    #
    # ⚠️ E nao ha' bio de carro nem de jardim: estes aparecem no catalogo do
    # site mae e em vitrine nenhuma. Isso e' proposital, nao esquecimento.
    "varredura.carro": "Carro",
    "varredura.jardim": "Jardim",
    "varredura.ferramentas": "Ferramentas",
}


def _area(nome_buffer: str) -> str:
    return AREA_DO_CANAL.get(nome_buffer, "Achadinhos")


def _nome_do_canal(nome_buffer: str) -> str:
    """"truque.importado" -> "Achadinho Make". Sai do registro da vitrine."""
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import vitrine
    return vitrine.ORIGEM.get(nome_buffer, nome_buffer)


_MEMO_HORAS: dict = {}


def _por_hora() -> dict:
    """{id: [(carimbo, preco), ...]} das leituras horarias, ou {}.

    ⭐ ELAS SAO SO' PARA O DESENHO. A queda, o riscado e a trava de 24 h
    continuam saindo da serie DIARIA -- mudar isso mudaria numeros que a
    pagina ja' promete, e a serie consolida o dia pelo MENOR preco de
    proposito (conservador para queda).
    ⚠ Arquivo ausente devolve {} e tudo cai na serie diaria: a gravacao
    horaria comecou em 21/09/2026 e produto antigo nao tem nada aqui.
    """
    global _MEMO_HORAS
    if _MEMO_HORAS:
        return _MEMO_HORAS
    import json as _json
    arq = RAIZ / "estado" / "precos_horas.jsonl"
    if not arq.exists():
        return {}
    fora: dict = {}
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            r = _json.loads(linha)
            pid, q, v = str(r["id"]), str(r["quando"]), float(r["preco"])
        except (ValueError, KeyError, TypeError):
            continue
        if v > 0:
            fora.setdefault(pid, []).append((q, round(v, 2)))
    for v in fora.values():
        v.sort()
    _MEMO_HORAS = fora
    return fora


def _serie_curta(por_dia: dict, d: dict, minimo: int = 3) -> list:
    """Os pontos que o cartao DESENHA — [] quando nao ha' o que desenhar.

    ⛔ MINIMO DE TRES DIAS, e o numero nao e' gosto. Com dois pontos o
    desenho e' um SEGMENTO: ele sempre sobe ou sempre desce, com a mesma
    inclinacao convincente, tendo o preco oscilado 0,5% ou 40%. Duas leituras
    nao mostram tendencia nenhuma — e desenhar uma seria inventar com tinta o
    que o texto se recusa a inventar com numero (ver `_queda_real`, que
    devolve ZERO quando nao sabe).

    ⚠️ Vem de `_precos_por_dia`, a MESMA leitura que decide a queda. Um dia
    vira um ponto, e o ponto e' o MENOR preco do dia — se o desenho lesse o
    arquivo cru, cada anuncio diferente do mesmo id viraria um pico, que e'
    exatamente a mentira consertada em 15/09/2026.
    """
    dias = por_dia.get(d.get("id")) or {}
    if len(dias) < minimo:
        return []
    # ⛔ O PONTO DE HOJE ENTRA AQUI, e sem ele o desenho CONTRADIZ o preco.
    #
    # MEDIDO em 21/09/2026, no produto que a regua escolheu para a capa:
    #
    #   serie ... 09-19 R$ 9,48 | 09-20 R$ 24,63   (ultimo ponto: ONTEM)
    #   preco exibido .......... R$ 9,48           (instantaneo de HOJE)
    #
    # O cartao dizia "caiu 62%, R$ 9,48" e a linha do grafico SUBIA ate' o
    # fim. Os dois estavam certos: o preco caiu mesmo de ontem para hoje, e
    # a serie so' ia ate' ontem porque ela e' consolidada por DIA e o
    # garimpo de hoje ainda nao escreveu. Errado era desenhar um sem o outro.
    #
    # ⚠ E o proprio `_preco_de_hoje` avisa disto: "tres numeros do mesmo
    # cartao (preco, de riscado e linha do grafico) que saissem de leituras
    # diferentes poderiam se contradizer na mesma tela". Quando ele passou a
    # preferir o instantaneo horario, o grafico ficou para tras.
    #
    # ⭐ A regra: se o instantaneo tem preco e o ultimo ponto e' de outro
    # dia, o instantaneo VIRA o ponto de hoje. O desenho passa a terminar no
    # numero que esta' escrito ao lado dele.
    from datetime import date as _d
    hoje = _d.today().isoformat()
    reg = _precos_agora().get(str(d.get("id") or ""))
    if isinstance(reg, dict) and reg.get("preco"):
        try:
            agora = round(float(reg["preco"]), 2)
        except (TypeError, ValueError):
            agora = 0.0
        if agora > 0:
            # ⛔ SUBSTITUI o ponto de hoje, nao so' acrescenta quando falta.
            # MEDIDO em 21/09 na capa: a serie diaria tinha 09-21 = R$ 19,61
            # e o instantaneo das 18:58 dizia R$ 11,89. O cartao anunciava
            # 11,89 e a linha SUBIA ate' 19,61 -- o grafico contradizendo o
            # numero escrito ao lado dele, que foi o que o Bryan viu.
            # ⚠ O ponto diario e' o MENOR do dia consolidado ate' a ultima
            # gravacao; o instantaneo e' a leitura MAIS RECENTE, e e' ele que
            # a pagina exibe. O desenho tem de terminar onde o preco termina.
            # ⭐ E isto vale so' para DESENHAR: `dias` e' uma copia. Queda,
            # riscado e trava de 24 h continuam saindo da serie intacta.
            dias = dict(dias)
            dias[hoje] = agora
    # ⭐ AS LEITURAS HORARIAS GANHAM DO DIARIO, quando ha' o bastante.
    # Pedido do Bryan em 21/09: "vai gerar movimento no grafico". E gera de
    # verdade -- sao leituras que nos fizemos, nao interpolacao. MEDIDO no
    # dado antes de escrever isto: a serie diaria tem 80.727 pares (id, dia)
    # distintos para 82.206 leituras, ou seja, praticamente uma por dia; o
    # movimento que faltava nunca esteve la' para ser desenhado.
    #
    # ⛔ E E' UMA FONTE SO' POR DESENHO, nunca as duas misturadas: o ponto
    # diario e' o MENOR do dia e o horario e' a leitura em si. Misturar faria
    # a linha descer todo fim de dia por artefato da consolidacao, e nao
    # porque o preco caiu.
    horas = _por_hora().get(str(d.get("id") or "")) or []
    # ⛔ O LIMIAR DE 4 PONTOS ESTAVA ERRADO E MATOU A REGUA DA CAPA.
    # MEDIDO em 21/09: depois de quatro publicacoes na mesma hora, TODO
    # produto tinha 4 leituras horarias -- todas do mesmo dia, todas com o
    # mesmo preco. Com `>= 4` elas GANHAVAM do historico diario, e a serie
    # de cada cartao virou uma reta de uma hora. Efeito em cascata: ninguem
    # mais tinha 5 pontos, `marcar_capa` nao achou UM candidato e a vitrine
    # caiu no modo de reserva.
    # ⭐ Quatro leituras em uma hora nao sao historia. A serie horaria so'
    # substitui a diaria quando cobre ao menos DOIS DIAS e tem 8 pontos --
    # ai' ela conta algo que o ponto-por-dia nao contava.
    # ⚠ E ate' la' o diario manda, que e' o que sustenta queda, riscado e
    # a trava de 24 h.
    dias_cobertos = {q[:10] for q, _ in horas}
    if len(horas) >= 8 and len(dias_cobertos) >= 2:
        # ⭐ EMENDA, E NAO TROCA (22/09/2026). Ate' hoje as horas SUBSTITUIAM
        # o diario inteiro: o cartao dizia "rastreando ha' 9 dias" e desenhava
        # ~21 horas -- e jogava fora justamente os dias em que o preco tinha
        # se mexido (MEDIDO na capa: 59,39 -> 60,50 -> 59,99 no diario, e 93
        # leituras horarias quase todas a 59,99). O Bryan viu reto e perguntou.
        # ⚠ Continua valendo "uma fonte so' POR INSTANTE": dia diario entra
        # so' ANTES do primeiro dia coberto pelas horas, entao nenhum dia tem
        # as duas fontes e o artefato "desce todo fim de dia" nao existe.
        # O eixo x do desenho e' por TEMPO (ver `grafico()` na pagina), senao
        # 8 dias ficariam espremidos no canto de 93 horas.
        inicio = min(dias_cobertos)
        antes = [[k[5:], round(v, 2)] for k, v in sorted(dias.items()) if k < inicio]
        return antes + [[q[5:16].replace("T", " "), v] for q, v in horas]
    # ⭐ "MM-DD" e nao a data inteira: o ano nao cabe no eixo e nao muda nada
    # pra quem le. Sao ~14 bytes por ponto no JSON da pagina.
    return [[k[5:], round(v, 2)] for k, v in sorted(dias.items())]


_MEMO_HOJE: dict = {}


def _preco_hoje_num(d: dict) -> float:
    """O preco de HOJE do produto, em numero — o mesmo que o cartao exibe.

    ⛔ O DEFEITO QUE ISTO CONSERTA (16/09/2026): `_antes` e `_queda_real`
    liam `d["preco"]`, que no registro publicado e' o preco DO DIA DA
    CAPTURA. O conserto de 15/09 trocou o preco EXIBIDO pela ultima leitura,
    mas o "de" riscado e o selo "caiu" continuavam comparando o maior visto
    com o preco velho — e davam VAZIO em produto que caiu de verdade. Medido
    na Fita organizadora: serie 7,59 -> 7,00 (-7,8%), cartao sem "de" e sem
    selo. "32 baixaram" estava subcontado por isso.

    ⚠️ Memo por rodada: `_precos_por_dia` le' o arquivo inteiro, e isto e'
    chamado por produto. A chave e' o mtime do arquivo, entao uma rodada
    nova (ou o teste com RAIZ trocada) invalida sozinha.
    """
    arq = RAIZ / "estado" / "precos_vistos.jsonl"
    chave = (str(arq), arq.stat().st_mtime if arq.exists() else 0)
    if _MEMO_HOJE.get("chave") != chave:
        _MEMO_HOJE.clear()
        _MEMO_HOJE["chave"] = chave
        _MEMO_HOJE["por_dia"] = _precos_por_dia()
    txt = _preco_de_hoje(_MEMO_HOJE["por_dia"], d) or str(d.get("preco", ""))
    try:
        return float(txt.replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
    except ValueError:
        return 0.0


def _ja_esteve(por_dia: dict, d: dict) -> dict:
    """{"preco": "R$ 6,79", "em": "14/09"} quando o produto SUBIU mas ainda
    esta' abaixo do maior que vimos — senao {}.

    ⭐ Bryan, 16/09/2026: "quando um item estiver subido mas ainda abaixo do
    valor original, colocar de forma elegante 'ja' esteve a R$ x e a data'".
    E' a informacao que a loja nunca da', e deixa a pessoa decidir esperar.

    ⚠️ Tres condicoes, todas contra a NOSSA serie: hoje > menor visto (com o
    piso de 2%, senao cambio vira "subiu"); hoje < maior visto (se ja' esta'
    no maior, nao "ja' esteve" — simplesmente subiu tudo); e o menor nao e'
    hoje. Quem esta' no minimo ganha o "de" riscado, nao esta linha.
    """
    dias = por_dia.get(d.get("id")) or {}
    if len(dias) < 2:
        return {}
    hoje = _preco_hoje_num(d)
    if hoje <= 0:
        return {}
    dia_min = min(dias, key=lambda q: dias[q])
    menor, maior = dias[dia_min], max(dias.values())
    if hoje > menor * 1.02 and hoje < maior:
        from datetime import date as _date
        try:
            ha = max(0, (_date.today() - _date(int(dia_min[:4]), int(dia_min[5:7]),
                                                int(dia_min[8:10]))).days)
        except ValueError:
            ha = 0
        # ⭐ SELO "ESPERE" (Bryan, 17/09/2026): o cartao manda NAO comprar
        # agora — "espere: ja' esteve a R$ 34 ha' 6 dias". Custa a venda de
        # hoje e compra a credibilidade das outras (Hormozi: de', de', de').
        return {"preco": f"R$ {menor:.2f}".replace(".", ","),
                "em": f"{dia_min[8:10]}/{dia_min[5:7]}", "ha": ha}
    return {}


# ⭐ SELO "RECORDE" (Bryan, 17/09/2026): o produto ADQUIRE o selo no momento
# em que o preco de hoje e' o MENOR de toda a nossa serie, com pelo menos
# RECORDE_DIAS_MIN dias de radar. Nao e' estatico: aparece no dia do recorde,
# fica enquanto o preco segurar, some quando subir (ai' vira "espere").
# Menos de 14 dias nao e' recorde — e' estreia.
RECORDE_DIAS_MIN = 14


def _menor(por_dia: dict, d: dict) -> float:
    """O MENOR preco que nos vimos neste produto, ou 0.

    ⭐ O IRMAO DO `antes`. `_antes` devolve o MAIOR valor da nossa serie (o
    riscado); este devolve o MENOR. Juntos eles dao a faixa em que o preco
    andou desde que acompanhamos, e é isso que o grafico da capa desenha --
    "voce está a R$ 2 do menor preco que eu já vi" só se pode dizer com os
    dois. Até 21/09/2026 só o maior era calculado.

    ⚠ Lé `por_dia`, a mesma leitura da queda e do grafico: um dia é um
    ponto, e o ponto é o MENOR preco do dia. Ler o arquivo cru faria cada
    anuncio do mesmo id virar um vale.
    """
    dias = por_dia.get(d.get("id")) or {}
    if not dias:
        return 0.0
    try:
        return round(min(dias.values()), 2)
    except (TypeError, ValueError):
        return 0.0


def _recorde(por_dia: dict, d: dict) -> dict:
    """{"dias": N} quando hoje e' o menor preco da serie com N >= 14 dias;
    senao {}. Empate com o menor (ate' 0,5%) conta como recorde: o recorde
    e' "nunca esteve mais barato", nao "esta' mais barato que nunca"."""
    dias = por_dia.get(d.get("id")) or {}
    if len(dias) < 2:
        return {}
    ordem = sorted(dias)
    from datetime import date as _date
    try:
        primeiro = _date(int(ordem[0][:4]), int(ordem[0][5:7]), int(ordem[0][8:10]))
    except ValueError:
        return {}
    n = (_date.today() - primeiro).days
    if n < RECORDE_DIAS_MIN:
        return {}
    hoje = _preco_hoje_num(d)
    menor = min(dias.values())
    if hoje <= 0 or hoje > menor * 1.005:
        return {}
    return {"dias": n}


def _queda_real(serie: dict, d: dict) -> float:
    """Quanto caiu contra o MAIOR PRECO POR DIA que nos vimos.

    ⚠️ Zero quando nao ha' historico, e zero quando o preco de hoje e' maior
    ou igual ao que ja' vimos. Nao e' "desconhecido": e' zero, e o cartao nao
    fala de desconto nenhum. Falha fechada, do lado que nao mente.
    """
    reg = serie.get(d.get("id"))
    if not reg:
        return 0.0
    maior = float(reg[2] or 0)
    hoje = _preco_hoje_num(d)
    if maior <= 0 or hoje <= 0 or hoje >= maior:
        return 0.0
    return round((maior - hoje) / maior * 100, 1)


def _antes(serie: dict, d: dict) -> str:
    """O maior preco que vimos, formatado — "" se nao houver queda real."""
    maior = serie.get(d.get("id"), ("", 0, 0.0, ""))[2]
    hoje = _preco_hoje_num(d)
    # ⚠️ 2% de piso: abaixo disso e' arredondamento e cambio, nao queda.
    if not (maior and hoje) or maior <= hoje * 1.02:
        return ""
    return f"R$ {maior:.2f}".replace(".", ",")


def _subiu(serie: dict, por_dia: dict, d: dict) -> str:
    """O MENOR preco que vimos, formatado — "" se hoje nao for o pico.

    ⭐ 23/09/2026 (Bryan, print do celular: "R$ 55,49 sem riscado" — um
    produto que subiu ACIMA do maior que a serie ja tinha visto. `_antes`
    so' cobre queda (hoje < maior): quando hoje E' o maior, ele fica vazio
    de proposito e o cartao nao mostrava nada — nem elogio nem aviso.
    Espelho de `_antes`, na direcao oposta: se hoje e' o proprio pico da
    serie, mostra o MENOR que ja vimos, pra virar "voce perde R$ X" no
    cartao (confirmado por Bryan: "55,49 GRANDE, e menor o preco antigo
    riscado embaixo").

    ⚠️ MUTUAMENTE EXCLUSIVO com `_antes` por construcao: so' dispara
    quando `maior <= hoje*1,02` -- exatamente o caso em que `_antes` ja'
    devolve "". Nunca os dois preenchidos ao mesmo tempo.
    """
    tid = d.get("id")
    maior = serie.get(tid, ("", 0, 0.0, ""))[2]
    hoje = _preco_hoje_num(d)
    if not (maior and hoje) or maior > hoje * 1.02:
        return ""
    # ⭐ reusa `_menor` (o irmao do `antes`) em vez de reler `por_dia` aqui
    # -- a mesma queda ja' ensinou que dois caminhos pro mesmo calculo
    # divergem em silencio (ver docstring de `_precos_por_dia`).
    menor = _menor(por_dia, d)
    # ⚠️ mesmo piso de 2% de `_antes`: abaixo disso e' cambio, nao subida.
    if not menor or hoje <= menor * 1.02:
        return ""
    return f"R$ {menor:.2f}".replace(".", ",")


def _preco_de_hoje(por_dia: dict, d: dict) -> str:
    """O preco da ULTIMA leitura nossa, formatado. "" se nao houver serie.

    ## ⛔ O DEFEITO QUE ESTA FUNCAO CONSERTA, medido em 15/09/2026

    O `produtos_publicados.jsonl` e' um registro HISTORICO, append-only: o
    campo `preco` de uma linha e' o preco do dia em que o produto foi
    capturado. A pagina lia esse campo e o mostrava como se fosse o de hoje.

    Conferido contra a API do AliExpress, sobre produtos que estavam NO AR:

        na pagina R$  20,11   ultima leitura nossa R$   9,35   API 9.35
        na pagina R$  65,87                        R$  51,99   API 51.99
        na pagina R$ 142,10                        R$ 107,89   API 107.89
        na pagina R$  88,88                        R$  22,69   API 22.73

    14 de 14 diferentes, e sempre pra cima.

    ⭐ E O MAIS IMPORTANTE: o preco CERTO ja' estava no nosso banco. O garimpo
    reconfere todo dia e grava em `precos_vistos.jsonl`; a trava de 24h da
    pagina consulta essa mesma serie e aprova com razao — e ai' a pagina
    imprimia o numero velho da linha. O conserto nao custa uma chamada de API.

    ⚠️ E ELE USA A MESMA `_precos_por_dia` do grafico e da queda, de proposito.
    Tres numeros do mesmo cartao (preco, "de" riscado e linha do grafico) que
    saissem de leituras diferentes poderiam se contradizer na mesma tela.

    ⚠️ RESSALVA HONESTA: a serie consolida cada dia pelo MENOR preco visto, e
    isso existe pra nao inflar a queda. Como preco EXIBIDO, o menor do dia e' o
    lado arriscado — se duas variantes forem lidas sob o mesmo id, mostramos a
    barata e o comprador pode achar mais caro. Nos 6 que deu pra cruzar, o
    menor do dia era exatamente o `target_sale_price` da API. Quem elimina a
    ressalva de vez e' a reconferencia de hora em hora.
    """
    # ⭐ O INSTANTANEO VEM PRIMEIRO, quando existe. Ele e' a leitura MAIS
    # RECENTE (`engine/precos.py`, de hora em hora); a serie e' consolidada
    # pelo MENOR preco do dia, que esta' certo pra calcular queda e e' o lado
    # arriscado pra preco exibido — o menor do dia pode ser uma promocao que
    # acabou as 11h, e o visitante chegaria na loja e acharia mais caro.
    agora = _precos_agora().get(str(d.get("id") or ""))
    if agora and agora.get("preco"):
        try:
            return f"R$ {float(agora['preco']):.2f}".replace(".", ",")
        except (TypeError, ValueError):
            pass
    dias = por_dia.get(d.get("id")) or {}
    if not dias:
        return ""
    return f"R$ {dias[max(dias)]:.2f}".replace(".", ",")


def _precos_agora() -> dict:
    """O instantaneo de `engine/precos.py`, ou {} se nao houver.

    ⚠️ LE' `RAIZ` NA HORA DA CHAMADA, e nao no import: os testes trocam
    `publicar_bio.RAIZ` por uma pasta de mentira, e um caminho fixado no import
    faria o teste ler o estado de PRODUCAO sem ninguem ver.
    """
    import json as _json
    arq = RAIZ / "estado" / "precos_agora.json"
    if not arq.exists():
        return {}
    try:
        return _json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # falha aberta: sem instantaneo a pagina cai na serie do dia, que e' o
        # comportamento anterior e continua honesto.
        return {}


def _dias(serie: dict, d: dict) -> int:
    """Ha' quantos dias este produto esta' na nossa serie."""
    from datetime import date
    q = serie.get(d.get("id"), ("", 0, 0.0, ""))[0]
    if len(q) != 10:
        return 0
    try:
        a, m, dd = int(q[:4]), int(q[5:7]), int(q[8:10])
        return max(0, (date.today() - date(a, m, dd)).days)
    except ValueError:
        return 0


def _coerente(p: dict) -> dict:
    """O trio preco / "de" riscado / queda tem de contar UMA historia.

    ⛔ O DEFEITO (16/09/2026, cartao do topo da bio): "R$ 73,69 ~~R$ 73,69~~
    ↓21%". `produtos_reais` lia `queda` do REGISTRO (calculada no dia da
    captura, com o historico antigo) enquanto `antes` e `preco` vinham da
    serie de hoje — tres numeros de tres momentos na mesma linha. Medido em
    17/09: "Clipes liberacao rapida" saia com ↓7% e SEM "de" (a serie nao
    via queda nenhuma). Agora `queda` e' `_queda_real`, como no catalogo, e
    esta guarda tira o riscado quando ele e' igual ao preco exibido — a
    contradicao que o Bryan viu na tela nunca mais sai, venha de onde vier.
    """
    if p.get("antes") and p.get("antes") == p.get("preco"):
        p["antes"] = ""
    if not p.get("antes"):
        p["queda"] = 0.0
    return p


def produtos_reais(por_canal: int = 4) -> dict[str, list[dict]]:
    """O que o garimpo escolheu, agrupado pela chave que a pagina usa.

    ⚠️ SO' ENTRA PRODUTO COM LINK. Cartao sem link aparece desligado, e um
    cartao desligado numa pagina que promete "preco e link" e' pior que
    cartao nenhum: quem clica e' justamente quem confiou.

    ⚠️ O MAIS NOVO PRIMEIRO, e no maximo `por_canal`. O que envelhece aqui e'
    PRECO — produto de duas semanas atras mostra numero que ja' mudou.
    """
    import json
    arq = RAIZ / "estado" / "produtos_publicados.jsonl"
    if not arq.exists():
        return {}
    serie = _serie_de_precos()
    por_dia = _precos_por_dia()
    linhas = []
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            linhas.append(json.loads(linha))
        except ValueError:
            continue        # linha torta nao derruba a vitrine inteira
    saida: dict[str, list[dict]] = {}
    vistos: dict[str, set] = {}
    for d in sorted(linhas, key=lambda x: x.get("quando") or "", reverse=True):
        if not d.get("link") or not d.get("nome"):
            continue
        chave = _chave_da_pagina(d.get("canal") or "")
        # ⚠️ DEDUP PELO ID: o mesmo produto sai pelo garimpo E pelo telegram,
        # e apareceria duas vezes na mesma vitrine.
        marca = d.get("id") or d.get("nome")
        if marca in vistos.setdefault(chave, set()):
            continue
        vistos[chave].add(marca)
        fila = saida.setdefault(chave, [])
        if len(fila) >= por_canal:
            continue
        quando = (d.get("quando") or "")[:10]
        fila.append(_coerente({
            # ⭐ O NOME ESCRITO PRA GENTE, nao pro buscador do AliExpress.
            # Sem cache e sem modelo ainda ha' nome: o corte na primeira
            # virgula, que e' onde o vendedor para de nomear e comeca a
            # listar palavra-chave. Ver engine/nome_produto.py.
            "nome": _nome_bonito(d),
            # o titulo cru fica: e' o que a dedup e o registro conhecem
            "nome_loja": d["nome"],
            "preco": _preco_de_hoje(por_dia, d) or d.get("preco", ""),
            "visto": f"{quando[8:10]}/{quando[5:7]}" if len(quando) == 10 else "",
            "link": d["link"],
            "imagem": d.get("imagem", ""),
            # ⭐ A QUEDA E' A PROVA QUE SO' NOS TEMOS: ela e' medida contra o
            # preco que NOS vimos, nao contra o "de/por" do vendedor (que e'
            # inflado — medido: R$ 31,48 "de R$ 122,22").
            "queda": _queda_real(serie, d),
            "vendas": int(d.get("vendas") or 0),
            # desde quando acompanhamos ESTE produto, e quantas vezes olhamos
            "desde": _desde(serie, d),
            "pontos": serie.get(d.get("id"), ("", 0, 0.0, ""))[1],
            # ⭐ A SERIE DESENHADA. Vazia ate' haver 3 dias — ver
            # `_serie_curta`, que explica por que 2 pontos nao viram linha.
            "serie": _serie_curta(por_dia, d),
            # ⭐ O PRECO ANTERIOR E' O QUE TORNA A QUEDA VERIFICAVEL: e' o
            # maior valor que NOS vimos na serie, nao o "de" do vendedor.
            # Sem ele, "caiu 8%" e' um numero que a pessoa tem de acreditar.
            "antes": _antes(serie, d),
            "subiu": _subiu(serie, por_dia, d),
            # ha' quantos dias acompanhamos: "desde 13/09" faz a pessoa fazer
            # a conta; "ha' 2 dias" ja' entrega a conta feita.
            "dias": _dias(serie, d),
        }))
    # ⚠️ `_todos` E' O ACHADINHO TOTAL: a vitrine geral, o que saiu em
    # QUALQUER canal. A pagina usa isto pra mostrar os outros cantos da casa
    # sem precisar saber quais canais existem.
    geral = []
    # ⚠️ O ACHADINHO DE ONTEM NAO SE PERDE — se o preco AINDA VALE.
    #
    # ⭐ Pedido do Bryan em 14/09: "os itens mais baratos que achei hoje
    # amanha nao podem ser perdidos se ainda valerem a pena a compra". Antes
    # disto a vitrine so' mostrava a ultima rodada, e um achado bom sumia em
    # 24h por nao ter sido republicado.
    #
    # ⚠️ E A TRAVA E' O PRECO RECONFERIDO, nao a data da publicacao. Produto
    # velho com preco velho e' o jeito mais facil de a pagina passar a mentir
    # sozinha: quem clica encontra outro numero na loja. So' fica quem o
    # garimpo VIU de novo nas ultimas 48h (campeoes e varredura reconferem).
    from datetime import date, timedelta
    # ⚠️ 24 HORAS, e nao 48 — decisao do Bryan em 15/09/2026 ("48 e' muito").
    #
    # ⛔ E A TRAVA FALHA FECHADA AGORA. Ela era `if visto_em and visto_em <
    # limite`, entao produto SEM leitura nenhuma na serie passava direto: a
    # guarda so' barrava quem tinha data velha, e deixava entrar quem nao
    # tinha data. "Preco reconferido nas ultimas 24h" tem de significar que a
    # reconferencia EXISTE. Custo medido da mudanca: 158 -> 152 produtos.
    agora = _precos_agora()
    limite = (date.today() - timedelta(days=1)).isoformat()
    for d in sorted(linhas, key=lambda x: x.get("quando") or "", reverse=True):
        if not d.get("link") or not d.get("nome"):
            continue
        visto_em = _visto_em(serie, agora, d.get("id"))
        if not visto_em or visto_em < limite:
            continue
        quando = (d.get("quando") or "")[:10]
        geral.append(_coerente({
            # ⭐ O NOME ESCRITO PRA GENTE, nao pro buscador do AliExpress.
            # Sem cache e sem modelo ainda ha' nome: o corte na primeira
            # virgula, que e' onde o vendedor para de nomear e comeca a
            # listar palavra-chave. Ver engine/nome_produto.py.
            "nome": _nome_bonito(d),
            # o titulo cru fica: e' o que a dedup e o registro conhecem
            "nome_loja": d["nome"],
            "preco": _preco_de_hoje(por_dia, d) or d.get("preco", ""),
            "visto": f"{quando[8:10]}/{quando[5:7]}" if len(quando) == 10 else "",
            "link": d["link"],
            "imagem": d.get("imagem", ""),
            # ⭐ A QUEDA E' A PROVA QUE SO' NOS TEMOS: ela e' medida contra o
            # preco que NOS vimos, nao contra o "de/por" do vendedor (que e'
            # inflado — medido: R$ 31,48 "de R$ 122,22").
            "queda": _queda_real(serie, d),
            "vendas": int(d.get("vendas") or 0),
            # desde quando acompanhamos ESTE produto, e quantas vezes olhamos
            "desde": _desde(serie, d),
            "pontos": serie.get(d.get("id"), ("", 0, 0.0, ""))[1],
            # ⭐ A SERIE DESENHADA. Vazia ate' haver 3 dias — ver
            # `_serie_curta`, que explica por que 2 pontos nao viram linha.
            "serie": _serie_curta(por_dia, d),
            # ⭐ O PRECO ANTERIOR E' O QUE TORNA A QUEDA VERIFICAVEL: e' o
            # maior valor que NOS vimos na serie, nao o "de" do vendedor.
            # Sem ele, "caiu 8%" e' um numero que a pessoa tem de acreditar.
            "antes": _antes(serie, d),
            "subiu": _subiu(serie, por_dia, d),
            "dias": _dias(serie, d),
        }))
        if len(geral) >= 12:
            break
    if geral:
        saida["_todos"] = geral

    # ⚠️ A ORDEM DOS CANAIS SAI DE VENDA, e nao do alfabeto.
    #
    # ⭐ Ordem do Bryan em 14/09/2026: quem vende mais aparece primeiro; sem
    # venda, quem tem MAIS CHANCE de vender.
    #
    # ⚠️ E HOJE NAO HA' VENDA NOSSA: `order.listbyindex` devolve "the result
    # is empty" (zero pedidos), e mesmo quando houver, ha' UM tracking_id pra
    # operacao inteira — a venda nao diz de qual canal veio. Ver
    # engine/resultado.py e o item 2 do PARA_FAZER.
    #
    # ⭐ Entao a chance de vender e' medida por PROXY: o volume de vendas que
    # os produtos daquele canal ja' tem NA LOJA. E' o mercado dizendo o que
    # sai, e e' medido — nao e' palpite sobre qual canal e' melhor.
    #
    # ⚠️ E o proxy TROCA SOZINHO pelo numero de verdade no dia em que houver
    # venda por canal: e' so' `vendas_por_canal` existir.
    forca = {}
    for chave, itens in saida.items():
        if chave.startswith("_"):
            continue
        forca[chave] = sum(p.get("vendas") or 0 for p in itens)
    saida["_ordem"] = sorted(forca, key=lambda c: -forca[c])
    return saida


def injetar_produtos(html: str, dados: dict | None = None) -> str:
    """Troca o `PRODUTOS_REAIS = {}` da pagina pelo que o garimpo achou.

    ⚠️ ESTOURA SE O MARCADOR NAO EXISTIR. Substituicao que nao acha o alvo e
    segue em silencio publicaria a pagina de exemplo achando que publicou a
    real — e a etiqueta ainda diria "exemplo", entao ninguem notaria.
    """
    import json
    dados = produtos_reais() if dados is None else dados
    alvo = "  var PRODUTOS_REAIS = {};"
    if alvo not in html:
        raise SystemExit(
            "nao achei o marcador PRODUTOS_REAIS na pagina — "
            "alguem mexeu no contra_capa.html")
    corpo = json.dumps(dados, ensure_ascii=False, indent=2)
    return html.replace(alvo, "  var PRODUTOS_REAIS = " + corpo + ";", 1)

def tirar_comentarios(html: str) -> str:
    """Tira comentario de JS, de CSS e de HTML.

    ⚠️ SO' A LINHA INTEIRA no caso do `//`: um `//` no meio da linha pode ser
    parte de uma URL (`https://...`), e cortar ali quebraria o link. A regra e'
    "linha cujo primeiro conteudo e' //", que e' exatamente o formato dos
    comentarios que a gente escreve.
    """
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"/\*.*?\*/", "", html, flags=re.S)
    linhas = [l for l in html.splitlines() if not l.lstrip().startswith("//")]
    # duas linhas em branco viram uma
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas))


def tirar_previa(html: str) -> str:
    """Remove a caixa de previa — ela e' ferramenta nossa, nao pagina.

    ⚠️ MEDIDO em 12/09/2026, olhando a pagina JA' PUBLICADA: a caixa estava no
    ar. Ela diz, com todas as letras, "previa · nao vai ao ar" — e foi ao ar.
    Junto vinham as abas de trocar de canal: quem chegasse pelo TikTok do
    @achadinho.make via um quadro tracejado e botoes pros outros seis canais.

    A primeira versao deste publicador tirava comentario e achava que bastava.
    Comentario e' o que EXPLICA a ferramenta; a caixa e' a ferramenta.
    """
    return re.sub(r'\s*<section class="previa">.*?</section>', "", html,
                  flags=re.S)


def mascarar(html: str) -> str:
    """Troca os nomes internos por codigo, dentro das aspas."""
    for nome, codigo in CODIGOS.items():
        html = html.replace(f'banco: "{nome}"', f'banco: "{codigo}"')
    return html


def conferir(html: str) -> list[str]:
    """O que NAO pode sobrar na versao publica.

    ⚠️ Esta funcao e' o ponto do arquivo. Gerar mascarado e nao conferir e'
    confiar que a substituicao pegou tudo — e a substituicao erra calada.
    """
    proibido = {
        "engine/": "caminho de arquivo do motor",
        "playbook": "referencia ao playbook",
        "§23": "referencia a medicao",
        "canais_registro": "nome de modulo interno",
        "calibrag": "vocabulario interno",
        "manifesto": "vocabulario interno",
        "service_role": "CHAVE DE SERVICO",
        "sb_secret_": "CHAVE DE SERVICO",
        # ⚠️ Este entra na lista dos SENSIVEIS A CAIXA (ver abaixo): "medido"
        # minusculo e' portugues comum — "o desconto e' medido contra o preco
        # que nos vimos" e' TEXTO DE VITRINE, e reprovava.
        "MEDIDO": "nota de medicao",
        "Bryan": "nome do dono",
        "não vai ao ar": "a CAIXA DE PREVIA (ela foi ao ar em 12/09)",
        'class="abas"': "as abas de trocar de canal",
    }
    # ⚠️ ESTES SO' CONTAM EM CAIXA ALTA. Sao marcas de comentario interno,
    # nao palavras: em minusculo eles aparecem em portugues normal e a guarda
    # reprovava pagina correta (medido em 14/09/2026, na estreia do catalogo).
    SENSIVEL_A_CAIXA = ("MEDIDO",)
    # ⚠️ O NOME DO DONO E' PALAVRA INTEIRA: "Camiseta Nike Kobe BRYANt" (feed
    # da Nike, 16/09/2026) reprovava a publicacao inteira. "Bryan" dentro de
    # outra palavra nao e' o dono.
    import re as _re
    PALAVRA_INTEIRA = ("Bryan",)
    achados = []
    for termo, porque in proibido.items():
        if termo in PALAVRA_INTEIRA:
            achou = bool(_re.search(r"\b" + _re.escape(termo) + r"\b", html, _re.I))
        else:
            achou = (termo in html if termo in SENSIVEL_A_CAIXA
                     else termo.lower() in html.lower())
        if achou:
            achados.append(f"{termo!r} ({porque})")

    # ⚠️ SO' OS NOMES QUE SAO DE VERDADE INTERNOS.
    #
    # A primeira versao desta guarda reprovava os sete, e estava errada: cinco
    # deles SAO o @ publico do canal (`@modofuturo`, `@atefalhar`...), aparecem
    # na tela e no link do TikTok. Exigir que sumissem seria exigir que a
    # pagina escondesse o proprio produto.
    #
    # Interno e' o nome que NAO bate com o @ publico: hoje sao dois, e sao
    # justamente os que revelam historia da operacao — o canal de maquiagem se
    # chama `truque.importado` por dentro, e a cozinha `cozinha.importada`.
    so_internos = [n for n in CODIGOS
                   if f"@{n}" not in html and n not in ("modofuturo",)]
    for nome in so_internos:
        # se o nome aparece SEM ser precedido de @, vazou
        if re.search(rf"(?<!@){re.escape(nome)}", html):
            achados.append(f"{nome!r} (nome interno de canal)")
    return achados


def escrever_decodificador() -> Path:
    linhas = ["# Códigos da página de bio — NAO SUBIR", "",
              "A página pública usa código no lugar do nome interno do canal.",
              "Esta é a chave de leitura, e ela mora FORA do repositório —",
              "guardar a chave junto do texto cifrado é não cifrar nada.", "",
              "| código | canal (nome_buffer) |", "|---|---|"]
    for nome, codigo in CODIGOS.items():
        linhas.append(f"| `{codigo}` | `{nome}` |")
    linhas += ["", "Gerado por `paginas/publicar_bio.py`. Se um canal mudar de",
               "nome, o código NÃO muda — é justamente para isso que ele serve."]
    SEGREDOS.mkdir(parents=True, exist_ok=True)
    alvo = SEGREDOS / "CODIGOS_DA_BIO.md"
    alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return alvo


# ⚠️ OS PROJETOS QUE ESTAO NO AR. Nao e' a mesma lista de PORTAS: ha' projeto
# reservado sem pagina (os cinco do Ate Falhar) e ha' projeto que existe mas
# fica fora da bio (o `meulivro`, ate' a Kiwify). Publicar so' nestes.
PROJETOS = ("oachadinho", "achadinhochef", "pagomenos", "achadinhodehoje",
            "meulivro")

# ⚠️ O SITE MAE E' OUTRO TIPO DE PAGINA, e por isso nao entra em PROJETOS.
#
# Nos outros enderecos a RAIZ e' a bio de um canal e o catalogo mora em
# `/todos`. Aqui e' o contrario: a raiz E' o catalogo, com a lupa e sem canal
# nenhum na frente — e' a casa da operacao inteira.
#
# ⚠️ Criado em 14/09/2026 apagando o reservado `treinodefora` (0 deploys), a
# pedido do Bryan: a conta bate o teto de 10 projetos.
PROJETO_MAE = "achadinhototal"

# ⭐ O DOMINIO PROPRIO (registro.br, 16/09/2026) — o endereco canonico do
# site mae. `achadinhototal.pages.dev` continua respondendo (e' onde o
# `conferir_no_ar` le' a marca), mas o Google deve indexar so' este.
DOMINIO = "https://achadinhototal.com.br"


# LINKS FORA DO HTML (19/09/2026). MEDIDO no ar: 582 KB, ~310 KB so' de
# link de afiliado do Ali (1.065 caracteres aleatorios, repetidos no
# PRODUTOS e no indice estatico). O Bryan viu a pagina crua no 4G. O HTML
# guarda o link so' de quem abre a primeira tela (topo, vitrine e os 2
# seguintes); o resto vai em `links.json` ao lado e a pagina encaixa o href
# quando chega (todos.html: carregarLinks).
LINKS_ARQUIVO = "links.json"
LINKS_EMBUTIDOS_EXTRA = 2


def separar_links(dados: list[dict]) -> dict[str, str]:
    """Tira `link` dos produtos fora da primeira tela e devolve {id: link}.
    Muda `dados` no lugar. Quem fica: `topo`, `vitrine` e os primeiros
    LINKS_EMBUTIDOS_EXTRA sem topo (a ordem da pagina e' topo primeiro)."""
    fora: dict[str, str] = {}
    extras = 0
    for p in dados:
        if not p.get("link") or p.get("id") in (None, ""):
            continue
        if p.get("topo") is not None or p.get("vitrine"):
            continue
        if extras < LINKS_EMBUTIDOS_EXTRA:
            extras += 1
            continue
        fora[str(p["id"])] = p.pop("link")
    return fora


# SSR DA PRIMEIRA TELA (20/09/2026). O Bryan viu 5 vezes a pagina "crua"
# (esqueleto) ao recarregar no 4G: o script grande so' roda quando o HTML
# inteiro chega. Agora a primeira tela (prova, chips, vitrine, 8 cartoes) ja'
# vai montada no HTML. Quem monta e' O PROPRIO SCRIPT DA PAGINA, rodando num
# DOM de mentira (jsdom) em `ferramentas/ssr/ssr.js` — o cartao nao existe em
# dois lugares. Sem node/jsdom, publica sem SSR e AVISA (preco na hora vale
# mais do que a primeira tela bonita).
SSR = RAIZ / "ferramentas" / "ssr" / "ssr.js"


# ⭐ O MOTOR SAI DE DENTRO DO HTML (20/09/2026). Bryan: "recarregar da'
# uma piscada". O script da pagina tem ~116 KB e, morando dentro do HTML,
# o Safari tinha de ler e compilar tudo ANTES de pintar a primeira tela —
# que o SSR ja' tinha deixado pronta ali do lado, parada, esperando.
#
# MEDIDO em 20/09 (aba visivel, localhost): o arranque sozinho custa 128-185
# ms e o parse so' fechava aos 768 ms. Tirar o script pra fora e marcar
# `defer` inverte a ordem: o navegador pinta o que o SSR escreveu e so'
# depois busca o motor.
#
# ⭐ E O GANHO MAIOR E' NO RECARREGAR, que e' o gesto que ele descreveu
# ("as pessoas vao ficar recarregando pra ver se tem desconto novo"): o
# arquivo tem nome fixo e versao na query, entao fica no cache do telefone
# e some do fio na segunda visita — o HTML cai de ~310 KB para ~195 KB.
#
# ⚠️ A ORDEM IMPORTA: isto roda DEPOIS do `ssr_primeira_tela` (o jsdom
# executa os <script> INLINE do documento; se o motor ja' estivesse fora,
# o SSR nao montaria nada) e ANTES do `conferir` (o corpo do js passa pelo
# mesmo detector de vazamento que o HTML, pela volta do `externos`).
MOTOR_ARQUIVO = "motor.js"


def externalizar_motor(html: str) -> tuple[str, str, str]:
    """Tira o maior <script> inline do HTML e devolve (html, corpo, marca).

    Corpo vem carimbado com o sha do proprio js; a mesma marca vai na query
    do `src`, entao versao nova = endereco novo = cache velho nao pega.
    Nao achou script grande: devolve o html intacto e corpo vazio.
    """
    import hashlib
    import re
    melhor = None
    for m in re.finditer(r"<script(?![^>]*\bsrc=)([^>]*)>(.*?)</script>",
                         html, re.S):
        if "module" in m.group(1):
            continue
        if melhor is None or len(m.group(2)) > len(melhor.group(2)):
            melhor = m
    # ⚠️ LIMIAR: abaixo disso nao e' o motor, e' o pre-script que limpa a
    # pre-montagem — esse TEM de continuar inline e sincrono, senao ele roda
    # depois da pintura e a pessoa ve' a tela errada por um quadro.
    if melhor is None or len(melhor.group(2)) < 50000:
        return html, "", ""
    corpo = melhor.group(2)
    sha = hashlib.sha256(corpo.encode("utf-8")).hexdigest()[:12]
    marca = "/*carimbo:" + sha + "*/"
    tag = ('<script src="' + MOTOR_ARQUIVO + "?v=" + sha
           + '" defer></script>')
    return html[:melhor.start()] + tag + html[melhor.end():], marca + corpo, marca


def _carimbar_js(corpo: str) -> tuple[str, str]:
    """O js ja' sai carimbado de `externalizar_motor`; aqui so' se le a marca."""
    import re
    sem_bytes_de_controle(corpo, "motor.js")
    m = re.match(r"/\*carimbo:([0-9a-f]{12})\*/", corpo)
    if not m:
        raise SystemExit("motor.js sem carimbo — nao publico o que nao sei conferir")
    return corpo, m.group(0)


def marcar_fundo_do_heroi(html: str) -> str:
    """Carimba `fundo-cena` / `fundo-estudio` no cartao do heroi, no HTML.

    ⚠️ POR QUE AQUI, E NAO SO' NO NAVEGADOR. O JS mede a foto num canvas e
    SO' ENTAO troca o desenho — e o visitante VIA a troca acontecer (Bryan,
    21/09: "quando eu recarrego a pagina mostra em um flash a imagem do
    anuncio menor e volta"). Medir na publicacao e mandar a resposta pronta
    tira o flash. De quebra faz valer em `/todos/`, que hoje nao executa JS
    nenhum (o `motor.js` de la' devolve HTML e o navegador recusa por MIME).

    ⚠️ A CONTA E' A MESMA DO JS, de proposito: reduz para 96x96, olha a moldura
    de 3 px e conta pixel quase-branco (min(r,g,b) > 233). Se as duas contas
    divergirem, o carimbo e o retoque do navegador brigam e o flash VOLTA,
    invertido. Mudou uma, muda a outra.

    Falhar (sem rede, sem PIL, foto estranha) devolve o HTML intacto: o JS
    ainda mede no navegador. Perde-se o flash, nao a pagina.
    """
    m = re.search(r'<img class="vfoto"[^>]*?src="([^"]+)"', html)
    if not m:
        return html
    try:
        import io
        import requests
        from PIL import Image
        r = requests.get(m.group(1), timeout=30)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB").resize((96, 96))
        px = im.load()
    except Exception as e:  # noqa: BLE001
        print(f"heroi: nao medi o fundo da foto ({e}) -> o navegador mede")
        return html
    L, k = 96, 3
    borda = brancos = soma = 0
    for y in range(L):
        for x in range(L):
            if x < k or y < k or x >= L - k or y >= L - k:
                c = px[x, y]
                borda += 1
                soma += c[0] + c[1] + c[2]
                if min(c) > 233:
                    brancos += 1
    frac = brancos / borda
    media = soma / (borda * 3)
    if frac <= 0.50:
        classe = "fundo-cena"
    elif frac >= 0.90:
        classe = "fundo-estudio" + (" puro" if media > 250 else "")
    else:
        # ⚠️ A FAIXA DO MEIO fica sem classe, igual ao JS: nem cena nem
        # estudio, e chutar estraga mais do que nao fazer nada.
        print(f"heroi: fundo na faixa do meio (borda {frac:.0%} branca) -> sem classe")
        return html
    alvo = '<a class="vitrine"'
    if alvo not in html:
        return html
    # ⭐ O CORTE DO TOPO, MEDIDO NESTA FOTO -- e nao 12% para todas.
    #
    # ⚠ O corte fixo resolvia o traco e cobrava de quem nao tinha traco
    # nenhum: toda foto de estudio perdia 12% da altura. Aqui a mesma imagem
    # que ja' esta' carregada diz quantas linhas do topo NAO sao fundo --
    # varre de cima para baixo enquanto a linha inteira for clara e para na
    # primeira que destoa. Se nao destoa nenhuma, o corte e' ZERO.
    #
    # ⛔ E E' CORTE, NAO EDICAO. Nenhum pixel novo, nada hospedado por nos:
    # a foto continua vindo do CDN do anunciante e o `clip-path` so' decide
    # o que aparece. Editar de verdade esbarra no `fidelidade.py`, que mediu
    # que o inpainting refaz o produto com menos detalhe e ainda passa.
    corte = 0
    try:
        im2 = Image.open(io.BytesIO(r.content)).convert("RGB")
        W, H = im2.size
        p2 = im2.load()
        passo = max(1, W // 40)
        anterior = None
        for y in range(0, int(H * 0.18)):
            linha = [sum(p2[x, y]) / 3 for x in range(0, W, passo)]
            m = sum(linha) / len(linha)
            # ⚠ 8 niveis: abaixo disso e' ruido de JPEG, e cortar por ruido
            # comeria foto boa. O degrau que o Bryan viu tinha 34.
            if anterior is not None and abs(m - anterior) > 8:
                corte = y
            anterior = m
        # ⛔ A CONVERSAO DE IMAGEM PARA CAIXA, que eu errei na primeira vez.
        # O `clip-path` corta a CAIXA do <img>, e com `object-fit: contain` a
        # imagem so' comeca depois do respiro de 5% e termina 5% antes do fim
        # -- ela ocupa 90% da caixa. Um degrau a 4,5% da IMAGEM esta' a
        # 5 + 4,5 x 0,90 = 9% da CAIXA.
        # ⚠ Sem essa conta eu cortava 6% e o traco continuava: 6% da caixa
        # e' 1% da imagem, ou seja, quase so' respiro. Medido na tela duas
        # vezes antes de eu procurar a causa.
        if corte:
            na_imagem = corte / H * 100
            corte = min(int(5 + na_imagem * 0.90) + 2, 16)
        else:
            corte = 0
    except Exception as e:  # noqa: BLE001
        print(f"heroi: nao medi o corte do topo ({e}) -> sem corte")
    print(f"heroi: fundo medido -> {classe} "
          f"(borda {frac:.0%} branca, media {media:.0f}, corte {corte}%)")
    novo_alvo = '<a class="vitrine ' + classe + '"'
    if corte:
        novo_alvo += ' style="--corte:' + str(corte) + '%"'
    return html.replace(alvo, novo_alvo, 1)


def ssr_primeira_tela(html: str) -> str:
    import shutil
    import subprocess
    if not html:
        return html
    node = shutil.which("node")
    if not node or not SSR.exists() or not (SSR.parent / "node_modules").exists():
        print("ssr: SEM node/jsdom (ferramentas/ssr: npm install) -> primeira tela "
              "vazia ate' o script chegar")
        return html
    try:
        r = subprocess.run([node, str(SSR)], input=html.encode("utf-8"),
                           capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("ssr: TEMPO ESGOTADO (120 s) -> publicando sem a primeira tela")
        return html
    aviso = r.stderr.decode("utf-8", "replace").strip()
    if r.returncode != 0 or not r.stdout:
        print("ssr: FALHOU -> publicando sem a primeira tela")
        if aviso:
            print("  " + aviso.replace(chr(10), chr(10) + "  "))
        return html
    if aviso:
        print(aviso)
    return r.stdout.decode("utf-8")


def indice_estatico(dados: list[dict]) -> str:
    """HTML puro com os produtos do catalogo, pro crawler. Um `<li>` por
    produto: nome, preco de hoje e o endereco da PROPRIA pagina com o
    produto em primeiro (`?p=<id>`). 19/09: antes era o link de afiliado
    (1 KB cada, nofollow: nao servia ao Google e pesava 155 KB)."""
    import html as _h
    itens = []
    for p in dados:
        nome, preco, pid = p.get("nome") or "", p.get("preco") or "", p.get("id")
        if not (nome and pid not in (None, "")):
            continue
        loja = p.get("loja") or ""
        itens.append(f'<li><a href="?p={_h.escape(str(pid), quote=True)}">'
                     f'{_h.escape(nome)}</a> — {_h.escape(preco)}'
                     + (f' · {_h.escape(loja)}' if loja else '') + '</li>')
    return ("<h2>Todos os achadinhos</h2>" + chr(10) + "<ul>" + chr(10)
            + chr(10).join(itens) + chr(10) + "</ul>")


def robots_txt() -> str:
    return ("User-agent: *" + chr(10) + "Allow: /" + chr(10) + chr(10)
            + f"Sitemap: {DOMINIO}/sitemap.xml" + chr(10))


def sitemap_xml(caminhos: list[str]) -> str:
    from datetime import date
    hoje = date.today().isoformat()
    urls = "".join(f"  <url><loc>{DOMINIO}{c}</loc><lastmod>{hoje}</lastmod>"
                   f"<changefreq>daily</changefreq></url>" + chr(10) for c in caminhos)
    return ('<?xml version="1.0" encoding="UTF-8"?>' + chr(10)
            + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + chr(10)
            + urls + '</urlset>' + chr(10))


# ⭐ www -> raiz (decisao do Bryan, 17/09). Arquivo `_redirects` do Pages.
# ⚠️ O pages.dev NAO redireciona ainda: e' nele que `conferir_no_ar` le' a
# marca, e o dominio so' passa a existir quando a zona ativar.
# ⛔ E `/todos` -> RAIZ, SO' NO SITE MAE (21/09/2026). MEDIDO no ar:
#
#   achadinhototal.com.br/motor.js        200  application/javascript  226 KB
#   achadinhototal.com.br/todos/motor.js  200  text/html               114 KB
#
# Nas bios o catalogo mora em `/todos/` e os externos vao junto, entao la'
# o motor existe. No site mae a RAIZ e' o catalogo e os externos ficam na
# raiz -- a pasta `todos/` nunca e' criada. Quem abria `/todos/` recebia a
# pagina raiz (o Pages devolve a raiz para caminho inexistente), e o
# `<script src="motor.js?v=...">` RELATIVO virava `/todos/motor.js`, que
# devolve HTML. O navegador recusa por MIME e a pagina fica SEM JS NENHUM:
# sem lupa, sem filtro, sem carregar link.
#
# ⚠ E O SINTOMA ENGANA DE DOIS JEITOS. Primeiro, tudo responde 200.
# Segundo, `/todos` SEM barra funcionava (o relativo resolve para
# `/motor.js`) -- so' a forma COM barra quebrava. Por isso a conferencia do
# publicador passava verde: ela olha a raiz e o `/todos` sem barra.
#
# ⭐ REDIRECIONAR, E NAO ESPELHAR (decisao do Bryan, 21/09). Espelhar
# criaria uma segunda copia identica do mesmo HTML no mesmo dominio --
# conteudo duplicado, com o `sitemap.xml` listando so' a raiz, e mais um
# motor de 235 KB por deploy. `/todos/` nao precisa ser pagina DIFERENTE da
# raiz: no site mae a raiz JA' E' o catalogo.
REDIRECTS = ("https://www.achadinhototal.com.br/* " + DOMINIO + "/:splat 301"
             + chr(10) + "/todos/* / 301" + chr(10)
             + "/todos / 301" + chr(10))

# ⭐ O MOTOR FICA NO CACHE DO TELEFONE (20/09/2026). Sem isto, tirar o
# script pra fora do HTML nao ganharia nada no RECARREGAR — que e' o gesto
# que o Bryan descreveu ("as pessoas vao ficar recarregando pra ver se tem
# desconto novo"): o telefone baixaria os 116 KB de novo toda vez.
#
# ⚠️ `immutable` SO' E' SEGURO PORQUE O ENDERECO CARREGA A VERSAO
# (`motor.js?v=<sha>`): motor novo = endereco novo = o cache velho nao
# responde por ele. Com nome fixo e sem query, isto deixaria gente com
# codigo velho por um ano.
# ⭐ OS TRES CABECALHOS FACEIS (20/09/2026, autorizado pelo Bryan). Sao
# instrucoes que o servidor manda junto com a pagina, dizendo ao navegador
# o que ele pode ou nao fazer. O visitante nunca ve.
#
#   frame-ancestors 'none' (+ X-Frame-Options por navegador velho)
#     impede que OUTRO site ponha o nosso dentro de um iframe e finja ser
#     nos — com um botao falso por cima. Risco zero: nada nosso e' embutido
#     em lugar nenhum.
#
#   Permissions-Policy
#     desliga o que a pagina nao usa: camera, microfone, localizacao,
#     pagamento, USB. Se um dia entrar script estranho, ele nem consegue
#     pedir. Risco zero: conferido que o site nao chama nenhuma delas.
#
#   Strict-Transport-Security
#     obriga o navegador a so' falar HTTPS com a gente.
#     ⚠️ COMECA CURTO DE PROPOSITO: 86400 = 1 dia. HSTS e' a unica coisa
#     aqui que o navegador GUARDA e obedece mesmo contra a nossa vontade;
#     se algo der errado, um dia depois expira sozinho. Subir para um ano
#     e' decisao para depois de ver que nao quebrou nada.
#     E SEM `includeSubDomains`: `www` e' subdominio e hoje se resolve por
#     JS — incluir subdominios podia prender um caminho que ainda muda.
#
# ⛔ CSP DE CONTEUDO (script-src/img-src) FICA DE FORA POR ORA, por decisao
# dele. Ela precisa da lista dos 18 dominios que o site carrega, e `img-src`
# e' lista ABERTA: muda a cada anunciante novo. CSP apertada demais some com
# a foto de uma loja futura em silencio — guarda que quebra o negocio sem
# avisar e' pior que guarda nenhuma. Aqui so' entra `frame-ancestors`, que
# nao tem nada a ver com carregar recurso.
CABECALHOS = (
    "/*" + chr(10) +
    "  X-Frame-Options: DENY" + chr(10) +
    "  Content-Security-Policy: frame-ancestors 'none'" + chr(10) +
    "  Permissions-Policy: camera=(), microphone=(), geolocation=(), "
    "payment=(), usb=()" + chr(10) +
    "  Strict-Transport-Security: max-age=86400" + chr(10) +
    "/motor.js" + chr(10) +
    "  Cache-Control: public, max-age=31536000, immutable" + chr(10) +
    "/todos/motor.js" + chr(10) +
    "  Cache-Control: public, max-age=31536000, immutable" + chr(10)
)



def _por_icone(destino) -> None:
    """Copia o icone pro diretorio que vai subir.

    ⚠️ Existe como funcao justamente porque sao DOIS diretorios (bios e site
    mae) e copiar em um so' e' o erro que aconteceu em 15/09/2026.
    """
    aqui = Path(__file__).resolve().parent
    # ⚠️ SAO DOIS ARQUIVOS DIFERENTES DE PROPOSITO, e trocar um pelo outro
    # estraga um dos dois lugares:
    #
    #   icone.png        FAVICON da aba. Fundo TRANSPARENTE — a aba do
    #                    navegador tem fundo proprio (claro ou escuro), e um
    #                    quadrado escuro fixo vira uma mancha nela.
    #   icone_app.png    APPLE-TOUCH-ICON, a tela de inicio do iPhone. Fundo
    #                    OPACO, obrigatoriamente: o iOS NAO respeita alfa aqui
    #                    — ele compoe o icone sobre PRETO. Um PNG transparente
    #                    viraria uma lupa dourada flutuando num quadrado preto,
    #                    que e' pior do que o fundo escuro que escolhemos.
    # ⭐ og_achadinho.png: a previa do link no chat (19/09, ferramentas/gerar_og.py)
    for nome, arquivo in (("icone.png", "icone_achadinho_favicon.png"),
                          ("icone_app.png", "icone_achadinho_180.png"),
                          ("og_achadinho.png", "og_achadinho.png"),
                          # inauguracao (24/09): ferramentas/og_inauguracao.py
                          ("og_inauguracao.png", "og_inauguracao.png"),
                          # buque da lupa (24/09): cena gerada, Desktop/inauguracao/og_buque_lupa.png
                          ("og_buque.png", "og_buque.png"),
                          ("og_buque_v3.png", "og_buque_v3.png"),
                          # v4 = v3 com acabamento (contraste 1,07, cor 1,05, nitidez leve)
                          ("og_buque_v4.png", "og_buque_v4.png")):
        origem = aqui / arquivo
        if origem.exists():
            (destino / nome).write_bytes(origem.read_bytes())
    # ⭐ OS BALOES DA INAUGURACAO (24/09/2026) moram aqui pelo mesmo motivo do
    # icone: upload direto substitui o diretorio inteiro, e o catalogo os pede
    # por caminho ABSOLUTO (`/baloes/...`) tanto no site mae quanto em
    # `/todos/` das bios. Faltando a pasta, o Pages responde 200 com HTML no
    # lugar da imagem e o balao some sem erro nenhum.
    baloes = aqui / "baloes"
    if baloes.is_dir():
        (destino / "baloes").mkdir(exist_ok=True)
        # 24/09: + `.png` -- a arte do e-mail (e-mail nao le' WebP no Outlook)
        for f in sorted(list(baloes.glob("*.webp")) + list(baloes.glob("*.png"))):
            (destino / "baloes" / f.name).write_bytes(f.read_bytes())
    # ⭐ E UM `favicon.ico` DE VERDADE (18/09/2026). Painel da Cloudflare,
    # Google e afins nao leem a tag `<link rel="icon">`: pedem `/favicon.ico`.
    # Sem o arquivo, o Pages devolve a raiz (HTML, 200) e o robo cai no
    # apple-touch-icon — que e' OPACO de proposito. O Bryan viu o quadrado
    # preto no painel da Cloudflare. O .ico sai do PNG transparente.
    fav = aqui / "icone_achadinho_favicon.png"
    if fav.exists():
        try:
            from PIL import Image
            im = Image.open(fav).convert("RGBA")
            im.save(destino / "favicon.ico", format="ICO",
                    sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        except Exception as e:                       # noqa: BLE001
            print(f"  [!] favicon.ico nao gerado ({type(e).__name__}) — segue sem")


def sem_bytes_de_controle(corpo: str, nome: str) -> str:
    """Estoura se `corpo` tem byte de controle. Devolve `corpo` intacto.

    ⛔ POR QUE ISTO EXISTE, e nao e' zelo. O byte 0x08 (o `\b` do teclado
    antigo) apareceu DUAS vezes neste projeto, e de uma delas ele saiu por
    commit e por suite verde: em `externalizar_motor`, dentro do
    `(?![^>]*src=)`, um `|` virou 0x08 e a lookahead deixou de casar --
    a funcao parou de pular `<script src=...>` e ninguem viu.

    ⚠️ A ARMADILHA E' O TERMINAL, e ela e' cruel: `sed -n '2353p'` imprime
    a linha e o TERMINAL EXECUTA o backspace, apagando na TELA o caractere
    anterior. A linha parece consertada e nao esta'. Nenhuma leitura de
    texto prova nada aqui -- so' byte. Por isso a conta e' sobre
    `corpo.encode('utf-8')`, e nao sobre o str.

    ⭐ E O LUGAR E' O CARIMBADOR porque ele e' o funil: todo byte que vai
    pro ar (html, motor.js, json externo) passa por um dos tres. Guarda em
    lugar mais cedo deixa porta; aqui nao ha' porta.
    """
    b = corpo.encode("utf-8")
    # ⚠️ TAB, LF e CR sao os unicos de controle legitimos num arquivo de texto.
    ruins = sorted({c for c in b if c < 32 and c not in (9, 10, 13)}
                   | ({127} & set(b)))
    if ruins:
        onde = []
        for c in ruins:
            i = b.index(bytes([c]))
            linha = b[:i].count(b"\n") + 1
            onde.append("0x%02x na linha %d" % (c, linha))
        raise SystemExit(
            "byte de controle em " + nome + ": " + "; ".join(onde) +
            " -- nao publico. NAO confira por sed/cat: o terminal executa o"
            " byte e a linha mente. Leia em bytes.")
    return corpo

def _carimbar(html: str) -> tuple[str, str]:
    """Poe um carimbo do conteudo no HTML e devolve (html, carimbo).

    ⭐ Entra como `<meta name="v">` logo apos o charset: e' a prova de que o
    byte servido e' o byte que este deploy montou.
    """
    import hashlib
    sem_bytes_de_controle(html, "html")
    sha = hashlib.sha256(html.encode("utf-8")).hexdigest()[:12]
    marca = 'name="v" content="' + sha + '"'
    tag = "<meta " + marca + ">\n"
    if "<meta charset" in html:
        i = html.index("\n", html.index("<meta charset")) + 1
        return html[:i] + tag + html[i:], marca
    return tag + html, marca


def _por_privacidade(pasta: Path, privacidade: str) -> None:
    """A rota `/privacidade`, em toda pasta que vai pro ar."""
    if privacidade:
        (pasta / "privacidade").mkdir(exist_ok=True)
        (pasta / "privacidade" / "index.html").write_text(
            privacidade, encoding="utf-8")


def publicar_no_ar(html: str, parceiros: str = "",
                   catalogo: str = "",
                   externos: dict[str, str] | None = None,
                   privacidade: str = "") -> None:
    """Sobe pro Cloudflare Pages e CONFERE no ar. Estoura se nao subiu.

    ⚠️ ISTO E' O PASSO QUE FALTAVA, e a falta dele fez eu anunciar uma pagina
    que nao existia. O `git push` do repo `bio` nao dispara deploy nenhum: os
    projetos sao de upload direto. Ver o cabecalho do arquivo.
    """
    import shutil
    import tempfile
    tok = os.getenv("CF_API_TOKEN")
    conta = os.getenv("CF_ACCOUNT_ID")
    if not (tok and conta):
        raise SystemExit("faltam CF_API_TOKEN / CF_ACCOUNT_ID no .env")
    amb = dict(os.environ, CLOUDFLARE_API_TOKEN=tok,
               CLOUDFLARE_ACCOUNT_ID=conta)
    pasta = Path(tempfile.mkdtemp())
    (pasta / "index.html").write_text(html, encoding="utf-8")
    # ⚠️ O ICONE VAI EM TODO DEPLOY, pelo mesmo motivo das rotas abaixo:
    # upload direto substitui o diretorio INTEIRO. Se ele nao subir junto,
    # o deploy seguinte o apaga sem erro e sem aviso — e o atalho que a
    # pessoa salvou na tela de inicio volta a ser uma letra "A" cinza.
    #
    # ⛔ E TEM DE IR NAS DUAS PASTAS. Este deploy monta DOIS diretorios: um
    # para os projetos de bio e outro (`casa`) para o site mae. Em 15/09/2026
    # eu copiei so' no primeiro, e a tag `apple-touch-icon` esta' justamente
    # no site mae: deu tag sem arquivo de um lado e arquivo sem tag do outro.
    #
    # ⚠️ E o sintoma ENGANA: `/icone.png` respondeu **200** — servindo a
    # pagina HTML inteira, porque o Cloudflare devolve a raiz quando o
    # caminho nao existe. Conferir por status daria "publicado".
    _por_icone(pasta)
    (pasta / "_headers").write_text(CABECALHOS, encoding="utf-8")
    # ⚠️ UPLOAD DIRETO SUBSTITUI O DIRETORIO INTEIRO. Se a rota nao for
    # junto neste mesmo deploy, o deploy seguinte a APAGA — sem erro, sem
    # aviso, e o link que esta no perfil do Awin vira 404.
    if catalogo:
        (pasta / "todos").mkdir()
        (pasta / "todos" / "index.html").write_text(catalogo, encoding="utf-8")
        # ⚠️ A CATEGORIA EXTERNA VAI AO LADO DO HTML QUE A PEDE. O fetch e'
        # relativo ("nike.json"): nas bios o catalogo mora em `/todos/`,
        # entao o arquivo tem de estar em `/todos/nike.json`; no site mae,
        # na raiz. Pasta errada = 200 servindo HTML no lugar do JSON (o
        # Pages devolve a raiz pra caminho inexistente) e a categoria abre
        # vazia sem erro nenhum.
        for nome, corpo in (externos or {}).items():
            (pasta / "todos" / nome).write_text(corpo, encoding="utf-8")
    if parceiros:
        (pasta / "parceiros").mkdir()
        (pasta / "parceiros" / "index.html").write_text(
            parceiros, encoding="utf-8")
    _por_privacidade(pasta, privacidade)
    try:
        for proj in PROJETOS:
            # 24/09/2026: o deploy de 01:10 caiu com rc=1 e o log so' tinha o
            # traceback -- o motivo do wrangler morria no capture_output.
            # Na falha, imprime o fim da saida dele antes de estourar.
            try:
                subprocess.run(["npx", "--yes", "wrangler", "pages", "deploy",
                                str(pasta), "--project-name", proj,
                                "--commit-dirty=true"],
                               env=amb, check=True, capture_output=True,
                               shell=(os.name == "nt"))
            except subprocess.CalledProcessError as e:
                def _fim(b):
                    t = (b or b"").decode("utf-8", "replace") if isinstance(b, bytes) else (b or "")
                    return t.strip()[-2000:]
                print(f"  NAO publicou: {proj} (wrangler rc={e.returncode})")
                for linha in (_fim(e.stderr) or _fim(e.stdout) or "(sem saida)").splitlines():
                    print(f"  wrangler Error: {linha}")
                raise
            print(f"  publicado: {proj}")
        # ⭐ O SITE MAE: mesma arte, outro papel. A raiz recebe o catalogo, e
        # `/parceiros` vai junto porque e' o endereco que o Awin abre.
        if catalogo:
            casa = Path(tempfile.mkdtemp())
            try:
                (casa / "index.html").write_text(catalogo, encoding="utf-8")
                # ⭐ indexacao (17/09/2026): robots, sitemap e www -> raiz
                (casa / "robots.txt").write_text(robots_txt(), encoding="utf-8")
                # ⭐ SEO (22/09/2026, item 8 da fila): `/privacidade` faltava
                # aqui — ela E' escrita no deploy (`_por_privacidade` mais
                # abaixo) mas nunca tinha entrado no mapa. Pagina real, sem
                # ela, so' fica visivel pra quem ja' sabe o endereco.
                (casa / "sitemap.xml").write_text(
                    sitemap_xml(["/", "/privacidade"]
                                + (["/parceiros"] if parceiros else [])),
                    encoding="utf-8")
                (casa / "_redirects").write_text(REDIRECTS, encoding="utf-8")
                (casa / "_headers").write_text(CABECALHOS, encoding="utf-8")
                # ⛔ O SITE MAE E' QUEM TEM A TAG `apple-touch-icon`. Sem esta
                # linha, a tag aponta pra um arquivo que nao existe e o
                # Cloudflare responde 200 servindo a pagina HTML no lugar do
                # PNG — foi o que aconteceu em 15/09/2026.
                _por_icone(casa)
                # ⭐ 404 SO' NO SITE MAE (24/09/2026). Nas bios nao: `/c1`...
                # dependem da raiz servida para caminho inexistente.
                nao_achei = Path(__file__).resolve().parent / "nao_achei.html"
                if nao_achei.exists():
                    (casa / "404.html").write_bytes(nao_achei.read_bytes())
                for nome, corpo in (externos or {}).items():
                    (casa / nome).write_text(corpo, encoding="utf-8")
                if parceiros:
                    (casa / "parceiros").mkdir()
                    (casa / "parceiros" / "index.html").write_text(
                        parceiros, encoding="utf-8")
                _por_privacidade(casa, privacidade)
                subprocess.run(
                    ["npx", "--yes", "wrangler", "pages", "deploy", str(casa),
                     "--project-name", PROJETO_MAE, "--commit-dirty=true"],
                    env=amb, check=True, capture_output=True,
                    shell=(os.name == "nt"))
                print(f"  publicado: {PROJETO_MAE} (site mae)")
            finally:
                shutil.rmtree(casa, ignore_errors=True)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)


def conferir_no_ar(marca: str, marca_parceiros: str = "",
                   marca_catalogo: str = "",
                   externos: dict[str, str] | None = None
                   ) -> tuple[list[str], list[str]]:
    """Baixa cada pagina DO AR e procura a marca.

    Devolve `(faltando, conferidos)` — os dois POR NOME.

    ⚠️ A PROVA E' O BYTE QUE O VISITANTE RECEBE. "Deployment complete" e commit
    verde ja' mentiram juntos uma vez — em 12/09/2026, e foi assim que a
    pagina com os botoes velhos ficou 40 minutos no ar sendo anunciada como
    nova.

    ⛔ E QUEM CONFIRMOU VOLTA NOMEADO, nao contado. Ate' 16/09/2026 o fim da
    publicacao imprimia `confirmado em {len(PROJETOS)} projeto(s)`: um numero
    FIXO, que nao vinha da verificacao e nao sabia o que ela tinha olhado. Ele
    dizia 5 logo depois de `publicado:` ter impresso 6 linhas (as cinco bios
    mais o site mae), e as rotas `/todos` e `/parceiros` — que sao o endereco
    escrito no perfil do Awin — nao apareciam em canto nenhum.

    ⭐ Guarda que conta sem nomear e' guarda que sera' ignorada: quando os dois
    numeros divergem, quem le' nao tem como saber se sobrou um endereco ou se
    faltou um, e a reacao barata e' parar de olhar. Agora a lista de
    confirmados E' a lista do que foi baixado, e some quando nada foi.
    """
    import requests
    faltando: list[str] = []
    conferidos: list[str] = []

    def _confere(rotulo: str, url: str, esperada: str) -> None:
        """Baixa `url` e exige `esperada` no corpo. Registra o desfecho."""
        try:
            r = requests.get(url, timeout=30)
            if esperada in r.text:
                conferidos.append(rotulo)
            else:
                faltando.append(rotulo)
        except Exception as e:
            faltando.append(f"{rotulo} (nao respondeu: {e})")

    for proj in PROJETOS:
        _confere(proj, f"https://{proj}.pages.dev/", marca)
        # ⚠️ A ROTA /todos TAMBEM SE CONFERE. E 200 NAO E' PROVA: o Pages
        # devolve a PAGINA RAIZ com status 200 quando o caminho nao existe.
        # Medido em 14/09/2026: `/todos` respondia 200 servindo a bio, e o
        # deploy nem tinha acontecido.
        if marca_catalogo:
            _confere(f"{proj}/todos", f"https://{proj}.pages.dev/todos",
                     marca_catalogo)
        if not marca_parceiros:
            continue
        # ⚠️ A ROTA SE CONFERE SOZINHA. A raiz estar nova nao prova que
        # `/parceiros` subiu: sao dois arquivos no mesmo deploy, e e' o
        # segundo que esta' escrito no perfil do Awin.
        _confere(f"{proj}/parceiros", f"https://{proj}.pages.dev/parceiros",
                 marca_parceiros)
    # ⚠️ NO SITE MAE A MARCA DO CATALOGO TEM DE ESTAR NA RAIZ. Conferir so'
    # os outros deixaria a casa da operacao fora da verificacao — e ela e' a
    # unica que nao tem bio pra servir de reserva se o deploy falhar.
    if marca_catalogo:
        _confere(f"{PROJETO_MAE} (site mae)",
                 f"https://{PROJETO_MAE}.pages.dev/", marca_catalogo)
        if marca_parceiros:
            # ⚠️ O SITE MAE TAMBEM SERVE `/parceiros`, e e' ELE que esta'
            # escrito no perfil do Awin (`achadinhototal.pages.dev/parceiros`).
            # O `publicar_no_ar` monta essa rota nas duas pastas desde
            # 15/09/2026; a verificacao olhava so' a das bios.
            _confere(f"{PROJETO_MAE}/parceiros",
                     f"https://{PROJETO_MAE}.pages.dev/parceiros",
                     marca_parceiros)
        # ⚠️ A CATEGORIA EXTERNA SE CONFERE PELO PROPRIO CARIMBO. O que se
        # procura e' `"carimbo": "<sha>"` dentro do JSON servido: se o Pages
        # devolver a raiz (HTML, 200) no lugar do arquivo, a marca nao esta'
        # la' e o endereco cai em `faltando` — com nome.
        for nome, marca_e in (externos or {}).items():
            _confere(f"{PROJETO_MAE}/{nome}",
                     f"https://{PROJETO_MAE}.pages.dev/{nome}", marca_e)
    return faltando, conferidos


def _carimbar_json(corpo: str) -> tuple[str, str]:
    """Poe `"carimbo": "<sha12>"` no JSON e devolve (json, marca)."""
    import hashlib
    sem_bytes_de_controle(corpo, "json externo")
    sha = hashlib.sha256(corpo.encode("utf-8")).hexdigest()[:12]
    marca = '"carimbo": "' + sha + '"'
    if not corpo.startswith("{"):
        raise SystemExit("externo: o arquivo nao e' um objeto JSON")
    return "{" + marca + ", " + corpo[1:], marca


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subir", action="store_true", help="empurra pro repo bio")
    a = p.parse_args()

    # UMA PUBLICACAO POR VEZ (20/09/2026). Em 18:20 a tarefa
    # `AchadinhoTotal_Publicar_Ao_Mudar` disparou sozinha no meio de uma
    # publicacao minha e os dois enviaram para os MESMOS seis projetos do
    # Pages. Upload direto substitui o diretorio inteiro: dois de uma vez
    # deixam o conjunto em estado misto, e a verificacao acusou tres
    # enderecos velhos. Nao e' azar — o vigia olha o hash de todos.html a
    # cada 10 min, entao todo push que toca a pagina agenda uma publicacao
    # automatica; publicar a mao logo depois E' a colisao esperada.
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
    try:
        import trava_de_publicacao as _trava
    except Exception:  # noqa: BLE001
        _trava = None
    if _trava is not None and not _trava.pegar():
        raise SystemExit(2)
    try:
        _publicar(a)
    finally:
        if _trava is not None:
            _trava.soltar()


def _publicar(a) -> None:

    # ⚠️ INJETAR ANTES DE MASCARAR: o `conferir()` roda depois e precisa ver
    # o que vai pro ar de verdade, produtos inclusive.
    html = mascarar(tirar_previa(injetar_produtos(
        tirar_comentarios(ORIGEM.read_text(encoding="utf-8")))))
    reais = produtos_reais()
    print("produtos reais por canal: " + (", ".join(
        f"{k}={len(v)}" for k, v in sorted(reais.items())) or "NENHUM"))

    # ⚠️ A pagina do anunciante passa pelo MESMO detector de vazamento. Ela
    # nao tem comentario de motor, mas tem nome de canal — e o detector ja'
    # pegou o nome do dono no rodape na primeira versao dela.
    # ⭐ A LEITURA DE AGORA VIRA PONTO DO GRAFICO (21/09/2026).
    # ⚠ AQUI, e nao no `engine/precos`: aquele roda na NUVEM e o arquivo
    # horario e' gitignorado -- seria escrito e descartado. O publicador roda
    # NESTA maquina e ja' tem o `precos_agora.json` puxado.
    # ⚠ A cadencia passa a ser a das PUBLICACOES, nao a das leituras: o
    # vigia publica quando o radar mexe, varias vezes ao dia. E' menos denso
    # que de hora em hora e MUITO mais denso que um ponto por dia -- e cada
    # ponto e' uma leitura que nos fizemos, nao interpolacao.
    try:
        from engine import precos as _pr
        _n = _pr.anotar_hora({k: (v or {}).get("preco")
                              for k, v in _precos_agora().items()})
        print(f"grafico: +{_n} leitura(s) na serie horaria")
    except Exception as e:  # noqa: BLE001
        print(f"grafico: nao anotei a leitura horaria ({e})")
    catalogo, externos = montar_catalogo()
    catalogo = ssr_primeira_tela(catalogo)
    catalogo = marcar_fundo_do_heroi(catalogo)
    # ⚠️ DEPOIS do SSR (o jsdom roda os <script> INLINE) e ANTES do
    # `conferir` logo abaixo: o corpo do motor entra em `externos` e passa
    # pelo mesmo detector de vazamento que o HTML.
    catalogo, motor_js, marca_motor = externalizar_motor(catalogo)
    if motor_js:
        externos[MOTOR_ARQUIVO] = motor_js
        print(f"motor: {len(motor_js)//1024} KB fora do HTML "
              f"({MOTOR_ARQUIVO}, defer, cache por versao)")
    parceiros = (PARCEIROS.read_text(encoding="utf-8")
                 if PARCEIROS.exists() else "")
    privacidade = (PRIVACIDADE.read_text(encoding="utf-8")
                   if PRIVACIDADE.exists() else "")
    sobrou = (conferir(html) + conferir(parceiros) + conferir(catalogo)
              + conferir(privacidade))
    # ⚠️ O JSON DA CATEGORIA EXTERNA PASSA PELO MESMO DETECTOR: ele leva
    # nome, loja e link de cada produto, e e' tao publico quanto o HTML.
    for corpo in externos.values():
        sobrou += conferir(corpo)
    if sobrou:
        print("NAO PUBLIQUEI. Sobrou coisa interna na versao publica:")
        for s in sobrou:
            print("  -", s)
        sys.exit(1)

    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "index.html").write_text(html, encoding="utf-8")
    antes = len(ORIGEM.read_text(encoding="utf-8"))
    print(f"gerado: {DESTINO / 'index.html'}")
    print(f"  {antes // 1024} KB -> {len(html) // 1024} KB "
          f"({antes - len(html)} bytes de comentario a menos)")
    print(f"decodificador: {escrever_decodificador()}")

    if not a.subir:
        print("\n[sem --subir] nada foi empurrado.")
        return

    tmp = DESTINO / "_repo"
    subprocess.run(["rm", "-rf", str(tmp)], check=False)
    subprocess.run(["gh", "repo", "clone", REPO, str(tmp)], check=True)
    (tmp / "index.html").write_text(html, encoding="utf-8")
    (DESTINO / "LEIA.md").exists() and (tmp / "LEIA.md").write_text(
        (DESTINO / "LEIA.md").read_text(encoding="utf-8"), encoding="utf-8")
    # ⚠️ IDENTIDADE LOCAL, no clone. O `user.name` global desta maquina esta'
    # VAZIO, e sem identidade o `git commit` falha — foi assim que a primeira
    # tentativa morreu. Local, e nao global, pra nao mexer na configuracao da
    # maquina por causa de um script.
    subprocess.run(["git", "-C", str(tmp), "config", "user.name",
                    "poisonb9"], check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.email",
                    "poisonb9@users.noreply.github.com"], check=True)

    # ⚠️ UMA PASTA POR CANAL, pro endereco ficar `/bio/c1` em vez de
    # `/bio/?c=c1`. E' o mesmo arquivo copiado: o Pages serve arquivo, nao
    # rota, entao "rota bonita" aqui e' literalmente uma pasta com um
    # index.html dentro.
    #
    # Custa ~129 KB por canal. Nao vale inventar redirecionamento pra economizar
    # isso: redirecionamento e' um salto a mais antes de a pagina aparecer, e
    # quem vem do TikTok desiste no salto.
    for codigo in sorted(set(CODIGOS.values())):
        pasta = tmp / codigo
        pasta.mkdir(exist_ok=True)
        (pasta / "index.html").write_text(html, encoding="utf-8")
    print(f"  {len(set(CODIGOS.values()))} pastas de canal (/c1 ... /c7)")
    if parceiros:
        (tmp / "parceiros").mkdir(exist_ok=True)
        (tmp / "parceiros" / "index.html").write_text(
            parceiros, encoding="utf-8")
    _por_privacidade(tmp, privacidade)

    subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True)
    # ⚠️ `check=True` no commit. Estava `False`, e o commit falhou CALADO — o
    # push seguinte reclamou de um branch sem commit nenhum, e a mensagem de
    # erro apontava pro lugar errado. Passo que pode falhar tem de falhar alto.
    r = subprocess.run(["git", "-C", str(tmp), "commit", "-m", "pagina de bio"],
                       capture_output=True, text=True)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        raise SystemExit("commit falhou:\n" + r.stdout + r.stderr)
    # ⚠️ O HISTORICO NAO PODE SEGURAR O AR.
    #
    # Este push vai pro repo `bio`, que e' ARQUIVO: ele nao publica nada (os
    # projetos do Pages sao de upload direto). Com `check=True` ele abortava a
    # funcao ANTES do deploy — medido em 14/09/2026: o catalogo ficou fora do
    # ar por causa de um push que nao tem nada a ver com publicar.
    #
    # ⭐ A ordem certa: primeiro o visitante, depois o arquivo. Falha aqui
    # AVISA ALTO e segue.
    # ⛔ SEM `GITHUB_TOKEN` NO AMBIENTE DO PUSH. O topo deste arquivo ja' tira
    # o token do `.env` (e' o PAT fine-grained, que NAO alcanca o `bio`) — mas
    # SEIS modulos do engine chamam `load_dotenv()` de novo ao importar
    # (awin, keys, mercadolivre, telegram...), e o token VOLTA pro ambiente
    # antes do push. O git ja' fala com o github.com pelo `gh` (config
    # global), e o `gh auth git-credential` obedece a variavel de ambiente
    # antes do chaveiro: com ela presente, 403 "denied to poisonb9" em toda
    # publicacao de 18/09; sem ela, o token classico do chaveiro, que tem
    # `push` no repo (medido: `gh api repos/poisonb9/bio -q .permissions`).
    amb_gh = {k: v for k, v in os.environ.items()
              if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
    empurrado = subprocess.run(
        ["git", "-C", str(tmp), "push", "-u", "origin", "HEAD:main"],
        capture_output=True, text=True, env=amb_gh)
    if empurrado.returncode == 0:
        print(f"\nempurrado para {REPO} (historico — isto NAO publica)")
    else:
        print(f"\n[!] O HISTORICO NAO SUBIU para {REPO} "
              f"(git saiu {empurrado.returncode}). A publicacao continua: "
              "isto nao afeta o que o visitante ve.")
        for linha in (empurrado.stderr or "").strip().splitlines()[-3:]:
            print("    " + linha)

    # ⛔ O CARIMBO VEM ANTES DO PUBLISH, e a ordem nao e' detalhe: carimbar
    # depois publicaria um HTML SEM carimbo e conferiria por um carimbo que
    # nao esta' no ar. A guarda reprovaria sempre, e a primeira reacao de
    # quem visse isso seria desligar a guarda.
    #
    # ⚠️ E A MARCA E' DERIVADA DO CONTEUDO, nao escrita a' mao. Antes eram
    # frases fixas ("Achados novos", "search bidding"): em 15/09/2026 eu
    # troquei o rotulo do filtro pra minuscula e a guarda passou a gritar
    # "NAO ESTA' NO AR" com a pagina nova publicada e CORRETA. Marca escrita
    # a' mao envelhece sozinha — e guarda com alarme falso e' pior que guarda
    # nenhuma: na vez em que ela acertar, ninguem vai acreditar.
    #
    # ⭐ O carimbo e' o sha do proprio HTML que sobe. Nao fica obsoleto, e
    # prova mais do que a frase provava: nao que "alguma versao nova" subiu,
    # e sim que subiu EXATAMENTE ESTA.
    html, marca = _carimbar(html)
    parceiros, marca_p = _carimbar(parceiros) if parceiros else ("", "")
    catalogo, marca_c = _carimbar(catalogo) if catalogo else ("", "")
    marcas_e: dict[str, str] = {}
    for nome in list(externos):
        # ⚠️ O motor nao e' JSON: ele ja' sai carimbado com `/*carimbo:*/`
        # e a conferencia no ar procura essa marca do mesmo jeito.
        carimbar = _carimbar_js if nome.endswith(".js") else _carimbar_json
        externos[nome], marcas_e[nome] = carimbar(externos[nome])

    print("\npublicando no Cloudflare Pages:")
    publicar_no_ar(html, parceiros, catalogo, externos, privacidade)
    print(f"\nconferindo no ar (procurando {marca!r}):")
    faltando, conferidos = conferir_no_ar(marca, marca_p, marca_c, marcas_e)
    for nome in conferidos:
        print(f"  confirmado: {nome}")
    if faltando:
        raise SystemExit(
            "NAO ESTA' NO AR em: " + ", ".join(faltando) +
            "\nO push pode ter dado certo e o site continuar velho "
            "— foi exatamente isso em 12/09/2026. Nao anuncie como publicado.")
    # ⛔ E O NUMERO SAI DA VERIFICACAO, nunca de `len(PROJETOS)`. Contar a
    # lista de projetos e chamar isso de "confirmado" e' afirmar sobre o pai o
    # que so' se mediu no filho: os enderecos conferidos incluem as rotas
    # `/todos` e `/parceiros`, e o site mae nao esta' em PROJETOS.
    if not conferidos:
        raise SystemExit(
            "a verificacao nao baixou pagina nenhuma — sem endereco conferido "
            "nao ha' o que confirmar. Isto nao e' sucesso.")
    print(f"  {len(conferidos)} endereco(s) conferidos no ar, "
          f"nenhum faltando")
    # o diario do site: uma entrada por publicacao confirmada (ordem do
    # Bryan, 20/09). Mora em ferramentas/ e nunca derruba a publicacao.
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
        import diario_do_site
        # ⚠️ O CATALOGO, NAO A BIO. `marca`/`html` sao da pagina de bio;
        # o site e' o catalogo, e era o tamanho da bio (240 KB) que ia
        # parar no diario no lugar dos 103 KB que o visitante recebe.
        diario_do_site.anotar(marca_c or marca, conferidos,
                              len(catalogo) if catalogo else len(html))
    except Exception as _e:
        print(f"  AVISO: diario nao anotado ({_e}). O site subiu igual.")


if __name__ == "__main__":
    main()
