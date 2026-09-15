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
    """
    import json
    arq = RAIZ / "estado" / "precos_vistos.jsonl"
    if not arq.exists():
        return {}
    por_dia: dict = {}
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
    return por_dia


def montar_catalogo() -> str:
    """O HTML do catalogo, com os produtos e o brasao ja' dentro."""
    import json
    if not CATALOGO.exists():
        return ""
    # ⚠️ O CATALOGO PASSA PELA MESMA LIMPEZA da bio: os comentarios daqui
    # explicam a operacao (medicao, decisao, data de incidente) e nao tem por
    # que viajar pro repositorio publico. Sem isto o detector reprova — e
    # reprovou, na primeira tentativa.
    html = mascarar(tirar_comentarios(CATALOGO.read_text(encoding="utf-8")))
    dados = produtos_todos()
    # ⚠️ ESTOURA SE O MARCADOR SUMIR. Substituicao que nao acha o alvo e segue
    # publicaria um catalogo VAZIO com cara de pronto.
    for alvo, valor in (("  var PRODUTOS = [];",
                         "  var PRODUTOS = " + json.dumps(
                             dados, ensure_ascii=False) + ";"),
                        ('  var BRASAO = "";',
                         '  var BRASAO = "' + _brasao_total() + '";')):
        if alvo not in html:
            raise SystemExit("catalogo: marcador sumiu -> " + alvo.strip())
        html = html.replace(alvo, valor, 1)
    print(f"catalogo: {len(dados)} produto(s)")
    return html


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
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from engine import combina as _c
    _combina = _c.ler_cache()
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
        visto_em = serie.get(d.get("id"), ("", 0, 0.0, ""))[3]
        if not visto_em or visto_em < limite:
            continue
        vistos.add(marca)
        quando = (d.get("quando") or "")[:10]
        saida.append({
            "nome": _nome_bonito(d),
            "preco": _preco_de_hoje(por_dia, d) or d.get("preco", ""),
            "link": d["link"],
            "imagem": d.get("imagem", ""),
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
            "dias": _dias(serie, d),
            "pontos": serie.get(d.get("id"), ("", 0, 0.0, ""))[1],
            # ⭐ A SERIE DESENHADA. Vazia ate' haver 3 dias — ver
            # `_serie_curta`, que explica por que 2 pontos nao viram linha.
            "serie": _serie_curta(por_dia, d),
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
    return duplicata.sem_repetidos(saida)


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
    # ⭐ "MM-DD" e nao a data inteira: o ano nao cabe no eixo e nao muda nada
    # pra quem le. Sao ~14 bytes por ponto no JSON da pagina.
    return [[k[5:], round(v, 2)] for k, v in sorted(dias.items())]


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
    hoje = 0.0
    try:
        bruto = str(d.get("preco", "")).replace("R$", "").strip()
        hoje = float(bruto.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0
    if maior <= 0 or hoje <= 0 or hoje >= maior:
        return 0.0
    return round((maior - hoje) / maior * 100, 1)


def _antes(serie: dict, d: dict) -> str:
    """O maior preco que vimos, formatado — "" se nao houver queda real."""
    maior = serie.get(d.get("id"), ("", 0, 0.0, ""))[2]
    try:
        hoje = float(str(d.get("preco", "")).replace("R$", "")
                     .replace(".", "").replace(",", ".").strip() or 0)
    except ValueError:
        return ""
    # ⚠️ 2% de piso: abaixo disso e' arredondamento e cambio, nao queda.
    if not (maior and hoje) or maior <= hoje * 1.02:
        return ""
    return f"R$ {maior:.2f}".replace(".", ",")


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
        fila.append({
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
            "queda": round(float(d.get("queda") or 0), 1),
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
            # ha' quantos dias acompanhamos: "desde 13/09" faz a pessoa fazer
            # a conta; "ha' 2 dias" ja' entrega a conta feita.
            "dias": _dias(serie, d),
        })
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
    limite = (date.today() - timedelta(days=1)).isoformat()
    for d in sorted(linhas, key=lambda x: x.get("quando") or "", reverse=True):
        if not d.get("link") or not d.get("nome"):
            continue
        visto_em = serie.get(d.get("id"), ("", 0, 0.0, ""))[3]
        if not visto_em or visto_em < limite:
            continue
        quando = (d.get("quando") or "")[:10]
        geral.append({
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
            "queda": round(float(d.get("queda") or 0), 1),
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
            "dias": _dias(serie, d),
        })
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
    achados = []
    for termo, porque in proibido.items():
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


def _por_icone(destino) -> None:
    """Copia o icone pro diretorio que vai subir.

    ⚠️ Existe como funcao justamente porque sao DOIS diretorios (bios e site
    mae) e copiar em um so' e' o erro que aconteceu em 15/09/2026.
    """
    icone = Path(__file__).resolve().parent / "icone_achadinho_180.png"
    if icone.exists():
        (destino / "icone.png").write_bytes(icone.read_bytes())


def _carimbar(html: str) -> tuple[str, str]:
    """Poe um carimbo do conteudo no HTML e devolve (html, carimbo).

    ⭐ Entra como `<meta name="v">` logo apos o charset: e' a prova de que o
    byte servido e' o byte que este deploy montou.
    """
    import hashlib
    sha = hashlib.sha256(html.encode("utf-8")).hexdigest()[:12]
    marca = 'name="v" content="' + sha + '"'
    tag = "<meta " + marca + ">\n"
    if "<meta charset" in html:
        i = html.index("\n", html.index("<meta charset")) + 1
        return html[:i] + tag + html[i:], marca
    return tag + html, marca


def publicar_no_ar(html: str, parceiros: str = "",
                   catalogo: str = "") -> None:
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
    # ⚠️ UPLOAD DIRETO SUBSTITUI O DIRETORIO INTEIRO. Se a rota nao for
    # junto neste mesmo deploy, o deploy seguinte a APAGA — sem erro, sem
    # aviso, e o link que esta no perfil do Awin vira 404.
    if catalogo:
        (pasta / "todos").mkdir()
        (pasta / "todos" / "index.html").write_text(catalogo, encoding="utf-8")
    if parceiros:
        (pasta / "parceiros").mkdir()
        (pasta / "parceiros" / "index.html").write_text(
            parceiros, encoding="utf-8")
    try:
        for proj in PROJETOS:
            subprocess.run(["npx", "--yes", "wrangler", "pages", "deploy",
                            str(pasta), "--project-name", proj,
                            "--commit-dirty=true"],
                           env=amb, check=True, capture_output=True,
                           shell=(os.name == "nt"))
            print(f"  publicado: {proj}")
        # ⭐ O SITE MAE: mesma arte, outro papel. A raiz recebe o catalogo, e
        # `/parceiros` vai junto porque e' o endereco que o Awin abre.
        if catalogo:
            casa = Path(tempfile.mkdtemp())
            try:
                (casa / "index.html").write_text(catalogo, encoding="utf-8")
                # ⛔ O SITE MAE E' QUEM TEM A TAG `apple-touch-icon`. Sem esta
                # linha, a tag aponta pra um arquivo que nao existe e o
                # Cloudflare responde 200 servindo a pagina HTML no lugar do
                # PNG — foi o que aconteceu em 15/09/2026.
                _por_icone(casa)
                if parceiros:
                    (casa / "parceiros").mkdir()
                    (casa / "parceiros" / "index.html").write_text(
                        parceiros, encoding="utf-8")
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
                   marca_catalogo: str = "") -> list[str]:
    """Baixa cada pagina DO AR e procura a marca. Devolve quem nao tem.

    ⚠️ A PROVA E' O BYTE QUE O VISITANTE RECEBE. "Deployment complete" e commit
    verde ja' mentiram juntos uma vez — em 12/09/2026, e foi assim que a
    pagina com os botoes velhos ficou 40 minutos no ar sendo anunciada como
    nova.
    """
    import requests
    faltando = []
    for proj in PROJETOS:
        try:
            r = requests.get(f"https://{proj}.pages.dev/", timeout=30)
            if marca not in r.text:
                faltando.append(proj)
        except Exception as e:
            faltando.append(f"{proj} (nao respondeu: {e})")
        # ⚠️ A ROTA /todos TAMBEM SE CONFERE. E 200 NAO E' PROVA: o Pages
        # devolve a PAGINA RAIZ com status 200 quando o caminho nao existe.
        # Medido em 14/09/2026: `/todos` respondia 200 servindo a bio, e o
        # deploy nem tinha acontecido.
        if marca_catalogo:
            try:
                r = requests.get(f"https://{proj}.pages.dev/todos", timeout=30)
                if marca_catalogo not in r.text:
                    faltando.append(f"{proj}/todos")
            except Exception as e:
                faltando.append(f"{proj}/todos (nao respondeu: {e})")
        if not marca_parceiros:
            continue
        # ⚠️ A ROTA SE CONFERE SOZINHA. A raiz estar nova nao prova que
        # `/parceiros` subiu: sao dois arquivos no mesmo deploy, e e' o
        # segundo que esta' escrito no perfil do Awin.
        try:
            r = requests.get(f"https://{proj}.pages.dev/parceiros",
                             timeout=30)
            if marca_parceiros not in r.text:
                faltando.append(f"{proj}/parceiros")
        except Exception as e:
            faltando.append(f"{proj}/parceiros (nao respondeu: {e})")
    # ⚠️ NO SITE MAE A MARCA DO CATALOGO TEM DE ESTAR NA RAIZ. Conferir so'
    # os outros deixaria a casa da operacao fora da verificacao — e ela e' a
    # unica que nao tem bio pra servir de reserva se o deploy falhar.
    if marca_catalogo:
        try:
            r = requests.get(f"https://{PROJETO_MAE}.pages.dev/", timeout=30)
            if marca_catalogo not in r.text:
                faltando.append(PROJETO_MAE)
        except Exception as e:
            faltando.append(f"{PROJETO_MAE} (nao respondeu: {e})")
    return faltando


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subir", action="store_true", help="empurra pro repo bio")
    a = p.parse_args()

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
    catalogo = montar_catalogo()
    parceiros = (PARCEIROS.read_text(encoding="utf-8")
                 if PARCEIROS.exists() else "")
    sobrou = conferir(html) + conferir(parceiros) + conferir(catalogo)
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
    empurrado = subprocess.run(
        ["git", "-C", str(tmp), "push", "-u", "origin", "HEAD:main"],
        capture_output=True, text=True)
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

    print("\npublicando no Cloudflare Pages:")
    publicar_no_ar(html, parceiros, catalogo)
    print(f"\nconferindo no ar (procurando {marca!r}):")
    faltando = conferir_no_ar(marca, marca_p, marca_c)
    if faltando:
        raise SystemExit(
            "NAO ESTA' NO AR em: " + ", ".join(faltando) +
            "\nO push pode ter dado certo e o site continuar velho "
            "— foi exatamente isso em 12/09/2026. Nao anuncie como publicado.")
    print(f"  confirmado em {len(PROJETOS)} projeto(s)")


if __name__ == "__main__":
    main()
