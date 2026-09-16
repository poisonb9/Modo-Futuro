# -*- coding: utf-8 -*-
"""O teto da vitrine e o segmento existem, e ninguem os contorna. Sem rede.

## ⛔ O QUE ESTA GUARDA PROTEGE

A pagina abre ordenada por `ganho x vendas`. Um tenis de marca rende ~R$ 37
por venda contra ~R$ 2 de um achadinho — entao, sem teto, o primeiro par que
entrar no catalogo assume a frente e empurra todo achadinho pra baixo. A
pagina viraria loja de tenis sem ninguem ter decidido isso.

⚠️ E o defeito NAO apareceria em teste de dado: hoje nao ha' calcado nem
produto acima de R$ 250 no catalogo, entao a regra e' invisivel ate' o dia em
que ela for necessaria. Por isso a guarda e' estrutural — ela checa que os
TRES lugares que precisam do recorte o aplicam, e nao que a tela de hoje
esta' bonita.

⭐ Os tres lugares sao: a grade, o CARTAO DO TOPO (que pesca "os 8 que mais
cairam" e traria o tenis sozinho pra primeira tela) e a CONTAGEM do seletor
(que mentiria "tudo 67" sobre uma grade de 63).
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HTML = (RAIZ / "paginas" / "todos.html").read_text(encoding="utf-8")

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


print("1. AS DUAS REGRAS EXISTEM E TEM UM NUMERO SO'")
checar("var TETO_VITRINE = 250;" in HTML, "o teto e' R$ 250 e mora num lugar so'")
checar('var SO_NO_SEGMENTO = ["Calçados"];' in HTML,
       "Calçados so' existe dentro do segmento (regra B)")
# ⛔ o titulo do bloco tem de DERIVAR do teto. Se alguem trocar o teto pra 300
# e o titulo continuar escrito "250", a pagina passa a mentir por conta.
# ⚠️ Desde 16/09/2026 o teto e' do CONTEXTO: 250 na categoria, 150 dentro
# da loja (`tetoAtual()`). O titulo continua derivando do numero, nunca
# escrito a mao — e' isso que a guarda protege, nao o nome da variavel.
checar('"Até R$ " + tetoAtual()' in HTML and '"Acima de R$ " + tetoAtual()' in HTML,
       "os titulos dos blocos derivam do teto (tetoAtual), nao sao texto cravado")
checar("var TETO_LOJA = 150;" in HTML and 'return (loja && !canal) ? TETO_LOJA : TETO_VITRINE;' in HTML,
       "dentro da loja o corte e' 150; na categoria e na principal continua 250")
# ⚠️ SO' O CODIGO, sem os comentarios — a primeira versao desta checagem
# reprovou por causa de um "Ate' R$ 250" escrito DENTRO de um comentario que
# explica a regra. Guarda com alarme falso e' pior que guarda nenhuma: na vez
# em que ela acertar, ninguem acredita.
CODIGO = "\n".join(re.sub(r"\s*//.*$", "", L) for L in HTML.splitlines())
checar('R$ 250"' not in CODIGO, "nao ha' '250' escrito a mao em titulo nenhum")

print()
print("2. ⛔ OS TRES LUGARES APLICAM O RECORTE — nao so' a grade")
grade = re.search(r"function desenhar\(\) \{.*?\n  \}", HTML, re.S)
checar(bool(grade) and "if (!visivel(p)) { return false; }" in grade.group(0),
       "a grade filtra por visivel()")
vivo = re.search(r"function animarVivo\(\) \{.*?\n  \}", HTML, re.S)
checar(bool(vivo) and "!caro(p) && !soNoSegmento(p)" in vivo.group(0),
       "o cartao do topo filtra ANTES de ordenar por queda")
chips = re.search(r"function montarChips\(\) \{.*?\n  \}", HTML, re.S)
checar(bool(chips) and "&& visivel(p)" in chips.group(0),
       "a contagem do seletor usa o mesmo recorte da grade")

print()
print("3. NAVEGAR E' PASSIVO, BUSCAR E' INTENCAO")
vis = re.search(r"function visivel\(p\) \{(.*?)\n  \}", HTML, re.S)
corpo = vis.group(1) if vis else ""
checar("if (canal || loja) { return true; }" in corpo,
       "escolher a categoria OU a loja mostra tudo dela")
checar("busca.value" in corpo, "digitar na busca mostra tudo que casa")
checar("return !caro(p) && !soNoSegmento(p);" in corpo,
       "e so' quem nao pediu nada ve' a lista recortada")
checar('normal(p.canal || "").indexOf(termo)' in HTML,
       "a busca casa tambem com a CATEGORIA (digitar 'calçados' acha)")

print()
print("4. ⛔ O ENDERECO NAO VIRA TEXTO NA PAGINA")
url = re.search(r"function daUrl\(\) \{.*?\n  \}", HTML, re.S)
corpo_url = url.group(0) if url else ""
checar(bool(url), "daUrl() existe")
checar("normal(p.canal) === h" in corpo_url,
       "o valor da url e' COMPARADO com as categorias que ja' existem")
checar('return "";' in corpo_url, "o que nao casar e' ignorado")
# ⚠️ o caso que importa: nada de innerHTML com coisa vinda da url
checar("innerHTML" not in corpo_url,
       "daUrl() nao escreve no DOM — sem porta de injecao")
checar("decodeURIComponent" in corpo_url and "try {" in corpo_url,
       "url malformada nao derruba a pagina (decodeURIComponent estoura)")

print()
print("5. OS BLOCOS — e a ordem que o Bryan pediu")
bl = HTML.index('bloco("Até R$ ')
ba = HTML.index('bloco("Acima de R$ ')
checar(bl < ba, "o barato vem PRIMEIRO na pagina")
checar("var PASSO_BLOCO = 15;" in HTML, "15 por bloco, com 'ver mais' proprio")
checar("lista.some(caro) && lista.some(function (p) {" in HTML,
       "a divisao so' aparece quando os DOIS grupos existem")
checar("mostrandoAlto = PASSO_BLOCO;" in HTML and
       "mostrandoBaixo = PASSO_BLOCO;" in HTML,
       "trocar de categoria reinicia os dois contadores")

print()
if falhas:
    print(f"[x] {len(falhas)} falha(s)")
    for f in falhas:
        print("   -", f)
    raise SystemExit(1)
print("tudo verde")
