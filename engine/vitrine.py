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


def postar_texto(p: dict, origem: str | None = None,
                 com_link: bool = True) -> str:
    """O post de um produto.

    ⚠️ MOSTRA o que e', nao pergunta se a pessoa quer. Mesma regra medida dos
    titulos (§23.9: pergunta converteu 0 de 4; o que afirma, 7 de 14) e mesma
    regra da chamada no fim do clipe. Nao ha' razao pra um post obedecer logica
    diferente — e' a mesma pessoa decidindo se clica.
    """
    # ⚠️ O EMOJI E' ROTULO, NAO ENFEITE. Cada um marca um campo sempre no
    # mesmo lugar, pra quem rola o feed no polegar achar o preco sem ler. Por
    # isso sao POUCOS e FIXOS: emoji sorteado a cada post vira ruido, e ai' a
    # pessoa volta a ter de ler tudo — que e' exatamente o que ele evita.
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
        img = _cartaz.montar(foto, p["nome"], preco,
                             _num(p.get("preco_antes", "")) or None)
        saco = io.BytesIO()
        img.save(saco, format="JPEG", quality=88)
        return saco.getvalue()
    except Exception as e:
        print(f"      [!] sem cartaz ({type(e).__name__}: {str(e)[:70]}); "
              f"o post vai em texto")
        return None


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


def marcar(link: str, quando: str | None = None) -> None:
    """Guarda que este link ja' foi ao ar.

    ⚠️ A CHAVE E' O LINK, nao o nome. Dois posts do mesmo produto com o nome
    reescrito sao o mesmo produto pra quem le' o canal — e nome e' justamente
    o campo que a gente mexe.
    """
    d = _ja_postados()
    d[link] = quando or f"{date.today():%Y-%m-%d}"
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
    if ja_foi(p["link"]):
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
        entregue = telegram.enviar_foto(
            foto, postar_texto(p, origem, com_link=False), destino,
            botao=(ROTULO_BOTAO, p["link"]))
    if not entregue:
        entregue = telegram.enviar(texto, destino)
    if not entregue:
        return None
    marcar(p["link"])
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


def main() -> None:
    a = argparse.ArgumentParser(description="a vitrine no Telegram")
    a.add_argument("--do-manifesto", metavar="ARQ",
                   default="estado/manifesto.json")
    a.add_argument("--ensaio", action="store_true",
                   help="monta e mostra, nao posta")
    o = a.parse_args()
    arq = RAIZ / o.do_manifesto
    if not arq.exists():
        raise SystemExit(f"nao achei {arq}")
    n = _do_manifesto(arq, o.ensaio)
    print(f"\n{n} produto(s) " + ("montado(s)" if o.ensaio
                                  else f"postado(s) em {canal() or '?'}"))


if __name__ == "__main__":
    main()
