# -*- coding: utf-8 -*-
"""Monta a pagina de achados a partir do `catalogo.json`.

O Bryan gostou da ideia em 02/09/2026: uma pagina curada que serve de destino
pro "link na bio" dos canais e pro canal do Telegram.

## O QUE ELA E', E O QUE ELA NAO E'

⚠️ NAO E' LOJA. Nao pede cartao, nao processa pagamento, nao promete entrega.
Leva pro anuncio no marketplace, onde confianca, pagamento e frete ja' estao
resolvidos.

A razao e' de conversao, nao de preguica: um estranho vindo do TikTok, pra
comprar num site desconhecido, precisa confiar no site, digitar cartao E
acreditar que o produto chega. Shopee e Mercado Livre ja' venceram essas tres
barreiras; uma pagina nova comeca com zero avaliacoes.

⚠️ E ELA NAO GERA TRAFEGO. E' destino, nao fonte. Quem traz gente e' o TikTok.
Cada degrau a mais no caminho derruba conversao — esta pagina se justifica
porque um link na bio precisa apontar pra algum lugar, e apontar pra UMA lista
curada e' melhor que pra um marketplace inteiro.

## ⚠️ CUMULATIVO, E ISSO NAO E' DETALHE

Decidido com o Bryan em 02/09/2026. A bio do TikTok tem UM link, fixo; o
catalogo muda a cada video novo. Quem visse um video na terca e clicasse na
quinta encontraria os produtos de quinta — nao os que viu.

Por isso a pagina ACUMULA: os achados ficam agrupados por data, os mais novos
no topo, e quem chega de um video antigo rola e encontra. E' a unica forma que
funciona com um link estatico.

⚠️ E acumular tem um segundo ganho: pagina que cresce ganha busca do Google
com o tempo — trafego que nao depende de feed nem de algoritmo. E' o unico
ativo desta operacao que se valoriza sozinho.

⚠️ COM TETO DE DIAS. Sem limite, a pagina cresceria pra sempre e o celular em
rede ruim pararia de abrir — matando justamente o requisito que o formato tem.
Item mais velho que o teto sai da PAGINA, nao do arquivo: o dado fica, so' nao
e' desenhado.

## POR QUE HTML SOLTO, SEM FRAMEWORK

Publico de TikTok e' celular em rede ruim. A pagina inteira e' um arquivo, sem
script externo, sem fonte remota, sem framework. Carrega antes de a pessoa
desistir — que e' o unico requisito que importa aqui.

## ⚠️ CUIDADO COM O REPOSITORIO

A pagina vive em `poisonb9/times-report`, dentro de `/achados/`. Esse
repositorio guarda o arquivo `tiktokxUKx...txt`, que e' a VERIFICACAO DE
DOMINIO do TikTok. Nada aqui toca nele — e nunca deve tocar. Perder aquele
arquivo custa refazer a verificacao.
"""
from __future__ import annotations

import datetime
import html
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ / "catalogo.json"
SAIDA = RAIZ / "achados_index.html"

SELO = {"shopee": "Shopee", "mercadolivre": "Mercado Livre",
        "aliexpress": "AliExpress"}

# Quantos dias de achados a pagina desenha. 90 dias sao ~13 semanas de
# conteudo — o bastante pra quem chega de video antigo, longe do ponto em que
# o peso da pagina incomoda no celular.
DIAS_NA_PAGINA = 90

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
     background:#0f0f10;color:#f2f2f2;padding:20px 14px 60px}
header{max-width:640px;margin:0 auto 26px}
h1{font-size:26px;letter-spacing:-.5px}
.sub{color:#9a9a9f;font-size:14px;margin-top:6px}
main{max-width:640px;margin:0 auto;display:grid;gap:14px}
a.card{display:flex;gap:14px;background:#1a1a1d;border:1px solid #2a2a2f;
       border-radius:14px;padding:12px;text-decoration:none;color:inherit}
a.card:active{background:#222226}
.thumb{width:96px;height:96px;flex:none;border-radius:10px;object-fit:cover;
       background:#26262b}
.nome{font-weight:600;font-size:15px;line-height:1.3}
.porque{color:#a8a8ae;font-size:13px;margin-top:5px}
.linha{display:flex;align-items:center;gap:8px;margin-top:8px;flex-wrap:wrap}
.preco{font-weight:700;font-size:15px}
.selo{font-size:11px;color:#0f0f10;background:#d8d8de;border-radius:20px;
      padding:2px 9px;font-weight:600}
.grupo{color:#7a7a80;font-size:12px;text-transform:uppercase;
       letter-spacing:.10em;margin:20px 0 -4px}
.vazio{color:#9a9a9f;text-align:center;padding:44px 10px;line-height:1.7}
footer{max-width:640px;margin:34px auto 0;color:#6a6a70;font-size:12px}
"""


def cartao(i: dict) -> str:
    e = lambda x: html.escape(str(x or ""))          # noqa: E731
    img = (f'<img class="thumb" src="{e(i.get("imagem"))}" alt="" loading="lazy">'
           if i.get("imagem") else '<div class="thumb"></div>')
    selo = SELO.get(str(i.get("onde", "")).lower(), i.get("onde", ""))
    porque = f'<div class="porque">{e(i["porque"])}</div>' if i.get("porque") else ""
    # ⚠️ `rel=nofollow sponsored` porque link de afiliado E' publicidade.
    # Omitir isso e' o tipo de detalhe que derruba a pagina numa auditoria.
    return (f'<a class="card" href="{e(i.get("link"))}" target="_blank" '
            f'rel="nofollow sponsored noopener">{img}<div>'
            f'<div class="nome">{e(i.get("titulo"))}</div>{porque}'
            f'<div class="linha"><span class="preco">{e(i.get("preco"))}</span>'
            f'<span class="selo">{e(selo)}</span></div></div></a>')


def _rotulo_data(iso: str) -> str:
    """'2026-09-02' -> 'hoje' / 'ontem' / '02 de setembro'."""
    MES = ("janeiro fevereiro março abril maio junho julho agosto setembro "
           "outubro novembro dezembro").split()
    try:
        d = datetime.date.fromisoformat(iso[:10])
    except Exception:
        return iso or "sem data"
    hoje = datetime.date.today()
    dias = (hoje - d).days
    if dias == 0:
        return "hoje"
    if dias == 1:
        return "ontem"
    return f"{d.day:02d} de {MES[d.month - 1]}"


def montar(dados: dict) -> str:
    itens = list(dados.get("itens") or [])
    hoje = datetime.date.today()

    # ⚠️ O TETO TIRA DA PAGINA, NAO DO ARQUIVO. Item velho continua no
    # catalogo.json; so' deixa de ser desenhado, pra pagina nao pesar.
    def recente(i):
        try:
            d = datetime.date.fromisoformat(str(i.get("data", ""))[:10])
        except Exception:
            return True          # sem data, mostra — perder achado e' pior
        return (hoje - d).days <= DIAS_NA_PAGINA

    itens = [i for i in itens if recente(i)]
    # mais novos primeiro; sem data vai pro fim
    itens.sort(key=lambda i: str(i.get("data") or ""), reverse=True)

    if itens:
        grupos: dict[str, list] = {}
        for i in itens:
            grupos.setdefault(str(i.get("data") or "")[:10], []).append(i)
        corpo = "".join(
            f'<div class="grupo">{html.escape(_rotulo_data(dia))}</div>'
            + "".join(cartao(i) for i in lista)
            for dia, lista in grupos.items())
    else:
        # ⚠️ PAGINA VAZIA E' MELHOR QUE PAGINA COM PRODUTO INVENTADO. Alguem
        # clica, o produto nao existe, e a confianca vai junto — e confianca e'
        # o unico ativo que esta pagina tem.
        corpo = ('<div class="vazio">Nenhum achado publicado ainda.<br>'
                 'Os itens aparecem aqui assim que forem escolhidos.</div>')
    return (
        '<!doctype html><html lang="pt-BR"><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Achados</title>'
        '<meta name="description" content="Seleção de achados com link direto '
        'para o anúncio.">'
        f'<style>{CSS}</style></head><body>'
        '<header><h1>Achados</h1>'
        '<div class="sub">Os mais recentes primeiro. '
        'O link leva direto para o anúncio.</div>'
        '</header>'
        f'<main>{corpo}</main>'
        '<footer>Os links podem gerar comissão para este perfil, sem custo '
        'para você.</footer>'
        '</body></html>')


def main() -> None:
    dados = json.loads(DADOS.read_text(encoding="utf-8"))
    SAIDA.write_text(montar(dados), encoding="utf-8")
    n = len(dados.get("itens") or [])
    print(f"  {SAIDA.name}: {n} item(ns), {SAIDA.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
