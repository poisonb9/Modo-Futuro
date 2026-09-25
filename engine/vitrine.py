# -*- coding: utf-8 -*-
"""A vitrine: UM canal de Telegram pra todos os produtos.

    python -m engine.vitrine --ensaio            monta e mostra, nao posta
    python -m engine.vitrine                     posta o que ainda nao foi

## POR QUE UM CANAL SO', E POR QUE TELEGRAM

Decisao do Bryan em 12/09/2026: "vamos fazer por Telegram mas apenas 1 canal
para todos os produtos".

O WhatsApp nao tem essa porta. A Cloud API oficial e' 1:1 com template
aprovado — grupo e comunidade estao FORA do produto, nao e' permissao que
falta. As bibliotecas nao oficiais postam em grupo e sao banimento quando
pegam volume, e o que se perde e' o NUMERO e os grupos, nao uma cota. Telegram
tem broadcast oficial, gratuito e ilimitado pra canal.

⚠️ CANAL, NAO GRUPO. Em canal so' o admin escreve, e e' isso que se quer:
lista de produto com 200 pessoas conversando por cima nao e' vitrine, e' ruido.

## ⚠️ O QUE UM CANAL SO' CUSTA, e ele custa alguma coisa

Publico de maquiagem, de cozinha, de academia e de cartao de credito no mesmo
feed. Quem entrou pelo @truque.importado vai ver halter e fatura. O preco disso
nao e' teorico: e' a saida do canal, e ela e' SILENCIOSA — o Telegram mostra a
contagem de inscritos, entao da' pra medir, mas so' se alguem olhar.

A troca em favor: concentra o publico, e' um link so' na bio e um post so' por
produto. Com o volume de hoje (poucos produtos por semana) a diluicao e'
pequena. Se um dia a saida doer, a divisao natural e' por CATEGORIA e nao por
canal — o campo `categoria` do produto ja' existe pra isso.

## E A ORIGEM NAO SE PERDE

Sete canais apontando pro mesmo destino apagaria de onde a pessoa veio. Nao
apaga: a contra-capa conta o clique POR CANAL antes de mandar, e cada post
carrega a linha de origem. O que o Telegram nao conta, o Supabase conta.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

from . import produto as _produto
from . import telegram

RAIZ = Path(__file__).resolve().parent.parent
JA_POSTADOS = RAIZ / "estado" / "vitrine_postados.json"

# ⚠️ O @ DO CANAL MORA NO .env, e nao aqui. Nao e' segredo (canal publico e'
# publico), mas e' configuracao de ambiente: a nuvem e a maquina local tem de
# poder apontar pra canais diferentes sem editar codigo — senao o primeiro
# teste posta de verdade no canal de verdade.
ENV_CANAL = "TELEGRAM_CANAL_VITRINE"

# canal interno -> como ele se apresenta no post.
#
# ⚠️ ISTO E' A ORIGEM, e e' o que impede o feed de virar um monte anonimo de
# link. Quem ve' "do Achadinho Make" entende por que um batom apareceu entre
# dois halteres.
ORIGEM = {
    "truque.importado": "Achadinho Make",
    "cozinha.importada": "Achadinho Chef",
    # nome novo, @ antigo: a troca do @ tem janela propria (trava de 30 dias)
    "fatura.chora": "Pago menos",
    "achadinhos.instantaneos": "Achadinhos Instantâneos",
    "atefalhar": "Até Falhar",
    "semanestesia.pod": "Sem Anestesia",
    "modofuturo": "Modo Futuro",
}


def canal() -> str | None:
    """O @ do canal da vitrine, ou None se ainda nao foi criado."""
    v = (os.getenv(ENV_CANAL) or "").strip()
    return v or None


ROTULO_BOTAO = "Ver na loja"
ROTULO_AVISO = "🔔 Avisar se baixar"
SITE = "https://achadinhototal.com.br"


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _dd_mm(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}" if len(iso or "") >= 10 else ""


def legenda_premium(p: dict) -> str:
    """A legenda do padrao aprovado pelo Bryan em 24/09/2026.

    ⭐ CADA NUMERO APARECE UMA VEZ. O padrao anterior dizia o preco tres vezes
    (cartaz, gancho, 💰) porque, sem fato medido, o gancho do modelo so'
    repetia o preco. Agora o gancho e' DETERMINISTICO e sai dos MESMOS campos
    que o site mostra (`publicar_bio.produtos_todos`): queda contra a nossa
    serie, vendidos medidos desde que acompanhamos, % de avaliacoes positivas.
    Sem fato forte, a primeira linha e' o nome curto — nunca uma frase vazia.

    ⛔ Nenhum numero daqui e' inventado ou arredondado pra cima: a queda sai do
    par `preco`/`preco_antes` que o cartaz desenha (o mesmo selo), e o
    `vendeu` e' o que NOS medimos, nao o contador da loja.
    """
    from html import escape
    r = p.get("_site") or {}
    preco = p.get("preco") or ""
    queda = 0.0
    try:
        from .cartaz import QUEDA_MINIMA, queda_do_par
        queda = queda_do_par(_num(preco), _num(p.get("preco_antes", "")) or None)
    except Exception:
        QUEDA_MINIMA = 5.0
    vendeu = r.get("vendeu") or []
    nota = float(r.get("nota") or 0)
    fatos = []
    if queda >= QUEDA_MINIMA:
        fatos.append(("queda", f"📉 <b>Caiu {queda:.0f}%</b> — era {p['preco_antes']}"))
    if len(vendeu) == 2 and int(vendeu[0]) >= 50:
        fatos.append(("vendeu", f"🔥 <b>+{_milhar(int(vendeu[0]))} vendidos</b> desde {vendeu[1]}"))
    if nota >= 90:
        fatos.append(("nota", f"⭐ <b>{nota:.0f}%</b> de avaliações positivas"))
    # a linha de cima: o fato mais forte; sem fato forte (so' nota), o nome
    if fatos and fatos[0][0] != "nota":
        topo, resto = fatos[0][1], [t for _, t in fatos[1:]]
    else:
        topo, resto = f"<b>{escape(p['nome'])}</b>", [t for _, t in fatos]
    quando = _dd_mm(p.get("preco_em") or f"{date.today():%Y-%m-%d}")
    linhas = [topo, "", f"💰 <b>{escape(preco)}</b> · preço de hoje, {quando}"]
    linhas += resto
    onde = " · ".join(x for x in (r.get("loja") or p.get("loja") or "",
                                  r.get("canal") or "") if x)
    if onde:
        linhas.append("🏪 " + escape(onde))
    nome_origem = ORIGEM.get(p.get("_canal") or "", "")
    if nome_origem:
        linhas.append(f"📺 do {nome_origem}")
    return chr(10).join(linhas)


def postar_texto(p: dict, origem: str | None = None,
                 com_link: bool = True, gancho: str = "") -> str:
    """O post de um produto.

    ⚠️ MOSTRA o que e', nao pergunta se a pessoa quer. Mesma regra medida dos
    titulos (§23.9: pergunta converteu 0 de 4; o que afirma, 7 de 14) e mesma
    regra da chamada no fim do clipe. Nao ha' razao pra um post obedecer logica
    diferente — e' a mesma pessoa decidindo se clica.

    ⭐ A PRIMEIRA LINHA DEPENDE DE TER CARTAZ, e essa e' a decisao do Bryan de
    16/09/2026. Com cartaz, o nome do produto JA' esta' na imagem, em corpo
    grande — repeti-lo aqui gastava a linha mais alta do post pra dizer o que
    a pessoa acabou de ler. No lugar dele vai o `gancho`: um fato medido sobre
    o produto (ver `engine/gancho.py`).

    ⛔ SEM CARTAZ, O NOME VOLTA. O post em texto puro e' a reserva de quando a
    foto nao baixa, e la' nao ha' imagem nenhuma dizendo o que e' o produto —
    um post que comeca em "Caiu 43%" e nunca diz 43% de QUE e' pior do que o
    post repetitivo.
    """
    # ⚠️ O EMOJI E' ROTULO, NAO ENFEITE. Cada um marca um campo sempre no
    # mesmo lugar, pra quem rola o feed no polegar achar o preco sem ler. Por
    # isso sao POUCOS e FIXOS: emoji sorteado a cada post vira ruido, e ai' a
    # pessoa volta a ter de ler tudo — que e' exatamente o que ele evita.
    if gancho and not com_link:
        linhas = ["✨ " + gancho, ""]
    else:
        linhas = ["🏷️ " + p["nome"], ""]
    if p.get("preco"):
        linhas.append("💰 " + p["preco"])
    if p.get("loja"):
        linhas.append("🏪 " + p["loja"])
    if p.get("preco") and p.get("preco_em"):
        # ⚠️ A DATA DO PRECO VAI JUNTO. Preco de afiliado muda sozinho, e post
        # antigo com preco velho e' o jeito mais rapido de perder a confianca
        # de quem clicou. Dizer de quando e' o preco e' honesto e barato.
        linhas.append(f"📅 preço visto em {p['preco_em']}")
    nome_origem = ORIGEM.get(origem or "", "")
    if nome_origem:
        linhas.append(f"📺 do {nome_origem}")
    # ⚠️ `com_link=False` E' SO' PRO POST COM BOTAO, e existe por medicao: o
    # link de afiliado do AliExpress tem 1.065 caracteres (mediana de 277
    # posts), e sozinho ele estourava a legenda da foto em 272 deles. Quando o
    # link viaja no botao, repeti-lo aqui traria o estouro de volta.
    #
    # ⛔ O texto SEM link nunca pode sair sozinho. Post de produto sem link e'
    # anuncio que nao vende — quem chama esta funcao com False tem de garantir
    # o botao, e cair pro texto COM link se o botao nao for.
    if com_link:
        linhas += ["", "🔗 " + p["link"]]
    return chr(10).join(linhas)


def _num(preco: str) -> float:
    """"R$ 13,52" -> 13.52. Zero no que nao der pra ler."""
    try:
        return float(str(preco).replace("R$", "").replace(".", "")
                     .replace(",", ".").strip() or 0)
    except ValueError:
        return 0.0


def cartaz_de(p: dict, tempo: int = 25) -> bytes | None:
    """O cartaz 9x16 deste produto, em JPEG. None se nao deu pra montar.

    ⭐ POR QUE O POST GANHOU IMAGEM. Ate' 15/09/2026 a vitrine postava texto
    puro, e nao por decisao: o `produto.normalizar` descartava o campo
    `imagem`, que ja' viajava no manifesto e que a pagina e o catalogo liam ha'
    dias. O feed do Telegram rola no polegar — sete linhas de texto entre duas
    outras sete linhas de texto nao param ninguem.

    ⛔ E FALHA ABERTA, DE PROPOSITO — o contrario da regra de sempre. Foto que
    nao baixa, CDN fora do ar, JPEG corrompido: tudo devolve None e o post sai
    como saia antes. A imagem e' a MOLDURA; o produto, o preco e o link sao o
    conteudo. Perder o post por causa da moldura seria trocar o principal pelo
    acessorio — a mesma regra que derrubou a versao 2 do menu de filtros.

    ⚠️ E O SELO DE QUEDA NAO E' DECIDIDO AQUI. Este modulo so' repassa o par de
    precos que veio no manifesto; quem mede a queda e' `garimpo.maior_visto`,
    sobre a serie consolidada. Se `preco_antes` vier vazio, o cartaz sai sem
    selo — e' o que tem de acontecer.
    """
    url = (p.get("imagem") or "").strip()
    if not url:
        return None
    preco = _num(p.get("preco", ""))
    if not preco:
        return None
    try:
        import io

        import requests
        from PIL import Image

        from . import cartaz as _cartaz

        # ⚠️ O CDN DO ALIEXPRESS RECUSA REQUISICAO SEM `User-Agent`: responde
        # 403, medido em 15/09/2026. Nao e' bloqueio da nossa conta.
        r = requests.get(url, timeout=tempo,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        foto = Image.open(io.BytesIO(r.content))
        img = _cartaz.montar_claro(foto, p["nome"], preco,
                                   _num(p.get("preco_antes", "")) or None,
                                   rodape="achadinhototal.com.br")
        saco = io.BytesIO()
        img.save(saco, format="JPEG", quality=88)
        return saco.getvalue()
    except Exception as e:
        print(f"      [!] sem cartaz ({type(e).__name__}: {str(e)[:70]}); "
              f"o post vai em texto")
        return None


def _gancho_de(p: dict) -> str:
    """O gancho deste produto, ou "" se nao deu.

    ⛔ FALHA ABERTA, e de proposito: gancho e' melhora, nao conteudo. Modelo
    fora do ar, cota seca, serie ilegivel — nada disso pode segurar um post
    que ja' tem foto, preco e link. Sem gancho a primeira linha volta a ser o
    nome, que e' o comportamento de ontem.
    """
    try:
        from . import gancho as _g
        from . import garimpo
        try:
            pid = int(p.get("_id") or p.get("id") or 0)
        except (TypeError, ValueError):
            pid = 0
        serie = garimpo.historico().get(pid, []) if pid else []
        return _g.de(p, serie)
    except Exception as e:
        print(f"      [!] sem gancho ({type(e).__name__}: {str(e)[:60]}); "
              f"a legenda volta a abrir pelo nome")
        return ""


def _ja_postados() -> dict:
    if not JA_POSTADOS.exists():
        return {}
    try:
        return json.loads(JA_POSTADOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # ⚠️ FALHA FECHADA. Registro ilegivel devolveria vazio, e vazio faz
        # repostar tudo — o oposto do que se quer. Entao e' erro alto.
        raise RuntimeError(
            f"{JA_POSTADOS} esta' ilegivel. Consertar antes de postar: com ele "
            f"vazio a vitrine reposta o catalogo inteiro no canal.")


def ja_foi(link: str) -> bool:
    return link in _ja_postados()


def _chave_id(p: dict) -> str:
    """A identidade do PRODUTO, quando ela existe. "" se nao da' pra saber."""
    pid = str(p.get("id") or p.get("_id") or "").strip()
    if pid and pid not in ("None", "0"):
        return "id:" + pid
    # ⚠️ Sem id, a foto e' a segunda melhor identidade — e' a mesma escolha do
    # `engine/duplicata.py`, e pelo mesmo motivo: o NOME nao serve (medido la',
    # "pinceis" x "esponjas" pontua 0,50 e sao produtos diferentes).
    img = (p.get("imagem") or "").strip()
    return "foto:" + img if img else ""


def ja_foi_produto(p: dict) -> bool:
    """Este PRODUTO ja' foi ao canal — pelo link OU pela identidade.

    ⛔ O DEFEITO QUE ISTO IMPEDE, medido em 15/09/2026 sobre o catalogo:

        302 linhas com link  ->  276 links unicos
                                 154 ids unicos
                                 152 fotos unicas

    O mesmo produto aparece ate' 27 VEZES no registro, cada vez com um
    `promotion_link` diferente — o garimpo regenera o link a cada rodada. Com a
    chave sendo so' o link, o canal reposta o mesmo conjunto de esponjas 27
    vezes e nada reclama.

    ⚠️ E isso nao e' hipotese nem estetica: duplicata e' a causa MEDIDA dos
    dois colapsos de alcance do @modofuturo (02/08 e 25/08). O link e' onde o
    dinheiro entra; o id e' quem o produto E'.
    """
    d = _ja_postados()
    if (p.get("link") or "").strip() in d:
        return True
    chave = _chave_id(p)
    return bool(chave) and chave in d


def marcar(link: str, quando: str | None = None,
           produto: dict | None = None) -> None:
    """Guarda que este link ja' foi ao ar — e, se der, QUAL produto era.

    ⚠️ A CHAVE E' O LINK, nao o nome. Dois posts do mesmo produto com o nome
    reescrito sao o mesmo produto pra quem le' o canal — e nome e' justamente
    o campo que a gente mexe.

    ⭐ E DESDE 15/09/2026 A IDENTIDADE VAI JUNTO, numa chave `id:<pid>` no
    mesmo arquivo. O formato continua `{chave: data}`, entao registro antigo
    segue valendo e nada precisou ser migrado.
    """
    d = _ja_postados()
    quando = quando or f"{date.today():%Y-%m-%d}"
    d[link] = quando
    if produto:
        chave = _chave_id(produto)
        if chave:
            d[chave] = quando
    JA_POSTADOS.parent.mkdir(parents=True, exist_ok=True)
    JA_POSTADOS.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                           encoding="utf-8")


def postar(bruto: dict, origem: str | None = None,
           ensaio: bool = False) -> str | None:
    """Manda um produto pro canal. Devolve o texto, ou None se nao mandou.

    ⚠️ NORMALIZA ANTES DE POSTAR, de proposito: o `produto.normalizar` LEVANTA
    em link que nao e' http(s), e este e' um dos dois lugares do motor onde um
    link de esquema estranho chegaria em publico.
    """
    p = _produto.normalizar(bruto)
    if not p:
        return None
    if ja_foi_produto(p):
        return None
    texto = postar_texto(p, origem)
    if ensaio:
        return texto
    destino = canal()
    if not destino:
        raise RuntimeError(
            f"Falta {ENV_CANAL} no .env. O canal ainda nao existe: quem cria "
            f"canal de Telegram e' uma PESSOA no app (bot nao cria), e depois "
            f"o bot tem de virar admin dele pra poder postar.")
    # ⚠️ O CARTAZ VAI COM A LEGENDA NUMA BOLHA SO', e o link vai no BOTAO.
    # Repetir o link na legenda estouraria o limite de 1024 em 272 dos 277
    # posts medidos — o link sozinho tem 1.065 caracteres.
    #
    # ⛔ E SE A FOTO NAO SAIR, CAI PRO TEXTO COM O LINK DENTRO. O caminho que
    # nao pode existir e' o post ir ao ar sem link nenhum: produto no feed sem
    # para onde ir e' pior do que produto que nao apareceu.
    foto = cartaz_de(p)
    entregue = False
    if foto is not None:
        # ⚠️ O GANCHO SO' SE PEDE QUANDO HA' CARTAZ. Ele custa uma chamada de
        # modelo, e no caminho de texto puro ele nem seria usado — a primeira
        # linha la' volta a ser o nome.
        # ⭐ PADRAO DE 24/09/2026: legenda premium (sem chamada de modelo) e
        # dois botoes — a loja (afiliado) e o "avise-me" do site, que e' onde
        # a pessoa deixa o contato. O 2o so' existe quando o produto esta' no
        # site; sem `_id` nao ha' pagina pra onde levar.
        botoes = [("🛒 " + ROTULO_BOTAO, p["link"])]
        if p.get("_site") and p.get("_id"):
            botoes.append((ROTULO_AVISO, f"{SITE}/?p={p['_id']}&de=telegram"))
        entregue = telegram.enviar_foto(
            foto, legenda_premium(p), destino, botoes=botoes, html=True)
    # ⛔ 25/09/2026 (Bryan, vendo o canal no iPhone: "apague todos que
    # estiverem assim"): o post em TEXTO PURO, com o link de afiliado de
    # 1.065 caracteres escrito por extenso, nao vai mais ao ar. Sem cartaz,
    # o produto NAO e' marcado e volta na proxima rodada — post atrasado nao
    # custa nada; paredao de link custa a cara do canal.
    if not entregue:
        print(f"      [adiado] sem cartaz entregue: {p['nome'][:44]}")
        return None
    marcar(p["link"], produto=p)
    # ⚠️ SO' DEPOIS DE O TELEGRAM ACEITAR. Anotar antes registraria como
    # publicado o que nao saiu — e o placar mentiria pro nosso lado, que e' o
    # lado que ninguem confere.
    try:
        from . import resultado
        resultado.anotar_publicado(dict(p, _id=p.get("id")), origem or "",
                                   "telegram")
    except Exception:
        pass
    return texto


CATALOGO = RAIZ / "estado" / "produtos_publicados.jsonl"


def preco_de_hoje(pid: int, registro: dict | None = None) -> float:
    """O preco de HOJE pela MESMA regra da pagina (`_preco_hoje_num`):
    o instantaneo de hora em hora primeiro; senao a ultima leitura da serie;
    senao o que o registro traz.

    ⛔ O DEFEITO QUE ISTO CONSERTA (18/09/2026, achado pelo teste 8 de
    `teste_vitrine_com_cartaz`, que ficou 2 dias sem rodar ate' o fim): a
    pagina comparava o maior visto com o preco de HOJE, e o canal com o preco
    do DIA DA CAPTURA gravado em `produtos_publicados.jsonl`. Resultado
    medido no catalogo: "Pular corda" com "de R$ 17,54" no canal e sem
    queda na pagina; "Luzes de tira led" ao contrario. E' o mesmo defeito
    que `_preco_hoje_num` consertou na pagina em 16/09 — a outra metade.
    """
    from . import garimpo, precos
    agora = precos.ler_instantaneo().get(str(pid)) or {}
    try:
        v = float(agora.get("preco") or 0)
    except (TypeError, ValueError):
        v = 0.0
    if v > 0:
        return v
    serie = garimpo.historico().get(pid) or []
    if serie:
        return float(serie[-1])
    return _num((registro or {}).get("preco", ""))


def preco_antes_de(registro: dict, hoje: float | None = None) -> str:
    """O maior preco que vimos deste produto, ou "" se ele nao caiu.

    `hoje` e' o preco de agora quando quem chama ACABOU de conferir na loja
    (`atualizar_preco`); sem ele, sai de `preco_de_hoje` — nunca do campo
    `preco` do registro, que e' o do dia da captura.

    ⛔ ESTE NUMERO TEM DE SER O MESMO QUE A PAGINA MOSTRA, e nao "parecido".
    A pagina calcula em `publicar_bio._antes`, sobre a serie consolidada; aqui
    a conta sai de `garimpo.maior_visto`, sobre `garimpo.historico()` — que
    consolida pela MESMA regra (o menor preco de cada dia).

    ⚠️ Duas contas que deveriam concordar sao duas contas que podem divergir,
    e divergir aqui significa o site anunciando 18% e o canal anunciando outra
    coisa do mesmo produto, no mesmo dia. Por isso ha' guarda cruzando as duas
    sobre o catalogo inteiro (`teste_vitrine_com_cartaz.py`), e nao so' fe'.
    """
    from . import garimpo
    try:
        pid = int(registro.get("id") or 0)
    except (TypeError, ValueError):
        return ""
    if not pid:
        return ""
    maior = garimpo.maior_visto({"product_id": pid}, garimpo.historico())
    if hoje is None:
        hoje = preco_de_hoje(pid, registro)
    # ⚠️ 2% de piso, o mesmo da pagina: abaixo disso e' arredondamento e
    # cambio, nao queda. Sem este piso o canal marcaria "-1%" onde o site nao
    # marca nada.
    if not (maior and hoje) or maior <= hoje * 1.02:
        return ""
    return f"R$ {maior:.2f}".replace(".", ",")


class PrecoVelho(RuntimeError):
    """O preco deste produto nao pode ser confirmado agora."""


def atualizar_preco(p: dict) -> dict:
    """Confere o preco na loja AGORA e devolve o produto com o preco de hoje.

    ⛔ ORDEM DO BRYAN, 15/09/2026: "sempre vamos postar com os precos
    atualizados do momento ou do dia". E ela veio de um defeito real, medido no
    mesmo dia contra a API, sobre 9 produtos que estavam NO AR:

        no ar R$ 20,11  ->  hoje R$  9,35        no ar R$  53,73  ->  R$  38,99
        no ar R$ 15,95  ->  hoje R$  6,83        no ar R$ 142,10  ->  R$ 107,89
        no ar R$ 65,87  ->  hoje R$ 51,99        no ar R$ 250,52  ->  R$ 218,99

    NOVE DE NOVE, e sempre pra cima. A causa e' o desenho, nao um bug: o
    `produtos_publicados.jsonl` e' um registro HISTORICO, append-only — o
    `preco` gravado la' e' o do dia da captura, e a pagina e o canal liam esse
    numero como se fosse o de hoje.

    ⚠️ O ERRO ESTA' DO LADO "SEGURO" (anunciamos mais caro do que e'), e por
    isso ninguem reclamaria — o comprador chega na loja e acha mais barato.
    Mas ele apaga justamente o que este projeto vende: se o preco real caiu
    mais do que o nosso, a queda que anunciamos esta' ERRADA PRA MENOS e o
    achadinho de verdade passa despercebido.

    ⛔ FALHA FECHADA: se a API nao responde, se o produto sumiu, ou se o preco
    volta zerado, isto LEVANTA e o produto nao vai ao ar. Preco e' a unica
    coisa do post que nao pode ser aproximada — post atrasado nao custa nada,
    post com preco errado custa a confianca de quem clicou.
    """
    from . import aliexpress

    pid = str(p.get("_id") or "").strip()
    if not pid or pid in ("None", "0"):
        raise PrecoVelho("produto sem id — nao da' pra confirmar o preco")
    try:
        r = aliexpress.chamar("aliexpress.affiliate.productdetail.get",
                              product_ids=pid, target_currency="BRL",
                              target_language="PT", country="BR")
        d = (r["aliexpress_affiliate_productdetail_get_response"]["resp_result"]
             ["result"]["products"]["product"][0])
    except Exception as e:
        raise PrecoVelho(f"{type(e).__name__}: {str(e)[:80]}") from e
    try:
        agora = float(d.get("target_sale_price") or 0)
    except (TypeError, ValueError):
        agora = 0.0
    if agora <= 0:
        raise PrecoVelho("a loja devolveu preco zerado")
    # ⛔ O `target_original_price` NAO ENTRA AQUI, em hipotese nenhuma. Medido
    # neste mesmo dia: ele e' ~2x o preco de venda em 7 dos 9 conferidos (e no
    # Tapete era exatamente o R$ 88,88 que nos gravamos como se fosse preco).
    # Quem decide o "de" e' a NOSSA serie, em `preco_antes_de`.
    novo = dict(p)
    novo["preco"] = f"R$ {agora:.2f}".replace(".", ",")
    novo["preco_em"] = f"{date.today():%Y-%m-%d}"
    # ⛔ E O "DE" TEM DE SER RECALCULADO CONTRA O PRECO NOVO. Sem esta linha o
    # selo sairia com a conta do preco VELHO: o produto que caiu de R$ 31,90
    # pra R$ 18,21 mostraria a queda de ontem, menor que a de hoje. Seria a
    # queda falsa de 15/09 pelo avesso — errada pra menos, e do lado que nao
    # incomoda ninguem, que e' justamente o que nunca se confere.
    novo["preco_antes"] = preco_antes_de({"id": pid}, hoje=agora)
    return novo


def pendentes(limite: int | None = None) -> list[dict]:
    """Os produtos do catalogo que ainda NAO foram ao canal, os melhores na
    frente.

    ⭐ A ORDEM E' A MESMA DO CATALOGO: `ganho x vendas`, a decisao do Bryan de
    14/09/2026. Postar por data poria o pior produto na estreia do canal so'
    por ele ter sido garimpado primeiro.

    ⚠️ E A CHAVE E' O LINK, igual ao `ja_foi`. Produto que voltou ao catalogo
    com o nome reescrito continua sendo o mesmo post pra quem le' o canal.
    """
    if not CATALOGO.exists():
        return []
    site = _do_site()
    vistos: set[str] = set()
    fila: list[tuple[float, dict]] = []
    for linha in CATALOGO.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            r = json.loads(linha)
        except ValueError:
            continue
        link = (r.get("link") or "").strip()
        if not link or link in vistos:
            continue
        vistos.add(link)
        # ⛔ E A IDENTIDADE TAMBEM SEGURA A FILA, nao so' o registro do que ja'
        # saiu. Medido no catalogo: 302 linhas com link, 154 ids. Sem isto a
        # fila entrega quatro "Carregador 120W" seguidos — mesmo produto,
        # quatro `promotion_link` gerados em rodadas diferentes.
        ident = _chave_id(r)
        if ident:
            if ident in vistos:
                continue
            vistos.add(ident)
        if ja_foi_produto(r):
            continue
        # ⛔ PREMIUM = SO' O QUE O SITE MOSTRA (24/09/2026). O site ja' aplica
        # as travas que a vitrine nao tinha: preco reconferido em 48h, esgotado
        # fora, mesmo produto de dois lojistas num cartao so', nome curto.
        # Fora do site, fora do canal.
        rico = site.get(str(r.get("id") or ""))
        if site and not rico:
            continue
        if rico and not _foto_serve(rico.get("imagem") or r.get("imagem") or ""):
            continue
        bruto = dict(r, preco_antes=preco_antes_de(r))
        if rico:
            bruto["nome"] = rico.get("nome") or bruto.get("nome")
            bruto["imagem"] = rico.get("imagem") or bruto.get("imagem")
        try:
            p = _produto.normalizar(bruto)
        except _produto.ProdutoInvalido:
            continue
        if not p:
            continue
        # ⚠️ A ORIGEM VIAJA NUM CAMPO PRIVADO. O `normalizar` devolve um dicio
        # fechado (e e' bom que seja), mas sem o canal o post perde a linha "do
        # Achadinho Make" — que e' o que impede o feed de virar monte anonimo.
        p["_canal"] = (r.get("canal") or "").strip()
        # ⚠️ O id viaja junto pra `marcar` poder gravar a identidade, e nao so'
        # o link. Sem ele o produto volta pra fila com outro link amanha.
        p["_id"] = r.get("id")
        if rico:
            p["_site"] = rico
        # ⚠️ `ganho_previsto` e `vendas` ja' vem gravados pelo garimpo. Faltando
        # um dos dois o produto vai pro fim da fila em vez de sumir: ele e'
        # legitimo, so' nao da' pra ordenar.
        peso = _num(r.get("ganho_previsto", 0)) * float(r.get("vendas") or 0)
        fila.append((peso, p))
    fila.sort(key=lambda x: x[0], reverse=True)
    escolhidos = _intercalar([p for _, p in fila])
    return escolhidos[:limite] if limite else escolhidos


_SITE: dict | None = None


def _do_site() -> dict[str, dict]:
    """{id: produto como o SITE o mostra}. Vazio se o gerador do site falhar.

    ⚠️ Vazio desliga o filtro premium em vez de zerar a fila: o canal parado
    em silencio e' pior (a guarda do workflow reprova run sem post, mas so'
    depois). O aviso sai alto no log.
    """
    global _SITE
    if _SITE is None:
        try:
            import sys
            sys.path.insert(0, str(RAIZ / "paginas"))
            import publicar_bio
            _SITE = {str(x.get("id")): x for x in publicar_bio.produtos_todos()}
        except Exception as e:
            print(f"      [!] sem os dados do site ({type(e).__name__}: "
                  f"{str(e)[:80]}) — a fila volta ao registro cru")
            _SITE = {}
    return _SITE


def _foto_serve(url: str) -> bool:
    """So' reprova foto JA' julgada como colagem ou nota < 5 (`foto_julga`).
    Nao julgada passa: julgar custa modelo e o cartaz nao pode travar nisso."""
    try:
        from . import foto_julga
        j = foto_julga._cache().get(url) or {}
    except Exception:
        return True
    if not j:
        return True
    return not j.get("colagem") and int(j.get("nota") or 0) >= 5


def _intercalar(fila: list[dict]) -> list[dict]:
    """Um de canal, um de varredura, um de canal — mantendo a ordem de cada.

    ⭐ DECISAO DO BRYAN, 16/09/2026. Por `ganho x vendas` puro, os primeiros da
    fila eram ferramenta, carro e jardim: produtos da VARREDURA, que rendem bem
    e nao vem de canal nenhum. O canal abria com tres posts seguidos sem linha
    de origem — "do Achadinho Make", "do Pago menos" — e e' justamente ela que
    impede o feed de virar um monte anonimo de link.

    ⚠️ E A FRONTEIRA NAO E' UM CAMPO NOVO: e' `ORIGEM`. Produto cujo canal esta'
    la' tem como se apresentar; o resto, nao. Inventar uma flag `_varredura`
    criaria uma segunda verdade que pode divergir daquela — e quem decide e' a
    mesma tabela que escreve a linha no post.

    ⛔ NADA E' DESCARTADO E NENHUMA ORDEM SE PERDE. Acabando um dos dois lados,
    o outro segue inteiro na ordem em que estava: isto reordena a fila, nao a
    filtra. A varredura nao vai pro fim (ela rende) nem lidera (ela nao se
    apresenta) — ela alterna.
    """
    de_canal = [p for p in fila if ORIGEM.get(p.get("_canal") or "")]
    de_varredura = [p for p in fila if not ORIGEM.get(p.get("_canal") or "")]
    saida: list[dict] = []
    # ⚠️ COMECA PELO CANAL. Empatado o resto, a primeira coisa que alguem ve'
    # ao abrir o canal tem de ter origem.
    for a, b in zip(de_canal, de_varredura):
        saida.append(a)
        saida.append(b)
    n = min(len(de_canal), len(de_varredura))
    saida += de_canal[n:] + de_varredura[n:]
    return saida


def _do_manifesto(caminho: Path, ensaio: bool) -> int:
    itens = json.loads(caminho.read_text(encoding="utf-8"))
    if isinstance(itens, dict):
        itens = itens.get("itens", [])
    n = 0
    for item in itens:
        p = _produto.do_manifesto(item)
        if not p:
            continue
        t = postar(p, item.get("canal"), ensaio=ensaio)
        if t:
            n += 1
            print(("[ensaio] " if ensaio else "[postado] ")
                  + t.splitlines()[0])
    return n


def do_catalogo(quantos: int, espaco: int = 90, ensaio: bool = False) -> int:
    """Manda os `quantos` melhores produtos que ainda nao foram ao canal.

    ⭐ O LOTE E' A DECISAO DO BRYAN DE 15/09/2026: tres de manha, tres a` tarde
    e tres a` noite. O canal nao tem publico ainda, e o que se quer por ora nao
    e' alcance — e' **nao parecer abandonado**. Constancia, nao volume.

    ⚠️ E POR ISSO HA' ESPACO ENTRE UM POST E O OUTRO. Tres mensagens no mesmo
    segundo sao uma rajada, e rajada e' o oposto de constancia: quem abre o
    canal ve' tres posts do mesmo minuto e um vazio de seis horas. 90 segundos
    e' barato (o processo fica vivo 3 minutos) e desmancha o bloco.
    """
    import time

    # ⚠️ A FILA VEM MAIOR QUE O LOTE, de proposito. Produto cujo preco nao se
    # confirma e' PULADO, e sem folga um lote de tres viraria um lote de um num
    # dia de API instavel — o oposto da constancia que a cadencia existe pra
    # dar. Tres vezes e' folga barata: sao chamadas de ~2 s.
    fila = pendentes(quantos * 3)
    if not fila:
        print("nada pendente — o catalogo inteiro ja' foi ao canal")
        return 0
    n = pulados = 0
    for p in fila:
        if n >= quantos:
            break
        try:
            p = atualizar_preco(p)
        except PrecoVelho as e:
            pulados += 1
            print(f"      [pulado] {p['nome'][:44]} — {e}")
            continue
        t = postar(p, p.get("_canal"), ensaio=ensaio)
        if t:
            n += 1
            print(("[ensaio] " if ensaio else "[postado] ") + t.splitlines()[0])
            print(f"           preco conferido agora: {p['preco']}")
        if espaco and not ensaio and n < quantos:
            time.sleep(espaco)
    if pulados:
        print(f"\n{pulados} pulado(s) por preco nao confirmado — e' falha "
              f"fechada, nao defeito")
    return n


def main() -> None:
    a = argparse.ArgumentParser(description="a vitrine no Telegram")
    a.add_argument("--do-manifesto", metavar="ARQ",
                   default="estado/manifesto.json")
    a.add_argument("--quantos", type=int, metavar="N",
                   help="manda os N melhores do catalogo que ainda nao foram")
    a.add_argument("--espaco", type=int, default=90, metavar="SEG",
                   help="segundos entre um post e o proximo (padrao 90)")
    a.add_argument("--ensaio", action="store_true",
                   help="monta e mostra, nao posta")
    o = a.parse_args()
    if o.quantos:
        n = do_catalogo(o.quantos, o.espaco, o.ensaio)
        faltam = len(pendentes())
        print(f"\n{n} produto(s) " + ("montado(s)" if o.ensaio
                                      else f"postado(s) em {canal() or '?'}")
              + f" — faltam {faltam} no catalogo")
        return
    arq = RAIZ / o.do_manifesto
    if not arq.exists():
        raise SystemExit(f"nao achei {arq}")
    n = _do_manifesto(arq, o.ensaio)
    print(f"\n{n} produto(s) " + ("montado(s)" if o.ensaio
                                  else f"postado(s) em {canal() or '?'}"))


if __name__ == "__main__":
    main()
