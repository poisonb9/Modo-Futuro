# -*- coding: utf-8 -*-
"""O roteiro nao pode afirmar o que nao sabemos, e uma frase por produto.

⚠️ NAO TEMOS O PRODUTO. Nunca usamos, nao sabemos se dura, se e' macio, se
vale. Afirmar qualidade de produto que nunca vimos e' propaganda enganosa,
cai sobre a conta que precisa estar limpa pro TikTok Shop, e queima a unica
coisa que um canal de achados tem pra vender: a confianca de quem assiste.

⚠️ O DETECTOR DE AFIRMACAO E' REDE, NAO CONTROLE. Quem deve evitar e' o
prompt; a lista de palavras pega o que escapar. Lista nunca cobre todas as
formas de afirmar qualidade — serve pra transformar o descuido comum em erro
visivel. O teste cobra as duas direcoes: pega o ruim E deixa passar o bom.

⚠️ E MENOS FRASES QUE PRODUTOS TEM DE SER RECUSADO. Se passar, a cena 3
recebe a fala do produto 2 e o video ANUNCIA O PRECO ERRADO — erro que
ninguem percebe revisando texto, so' assistindo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import roteiro_produto as rp  # noqa: E402

falhas = []

# ---- POSITIVO: roteiro limpo nao gera alerta ---------------------------
limpo = {
    "abertura": "Achados de beleza a partir de doze reais.",
    "produtos": [
        "O pincel kabuki denso serve para aplicar base liquida e custa "
        "vinte e quatro reais.",
        "A esponja tem formato de gota e sai por doze reais e cinquenta.",
    ],
    "fechamento": "O link de todos os produtos esta na bio.",
}
if rp.alertas(limpo):
    falhas.append(f"acusou roteiro limpo: {rp.alertas(limpo)}")

# ---- NEGATIVO: cada tipo de afirmacao proibida tem de ser pega ---------
RUINS = [
    "Esse pincel e' excelente e vale muito a pena.",
    "Material super resistente que dura anos.",
    "Eu testei e recomendo demais.",
    "Vai mudar sua rotina de maquiagem.",
    "O melhor custo-beneficio da categoria.",
]
for frase in RUINS:
    r = {"abertura": "", "produtos": [frase], "fechamento": ""}
    if not rp.alertas(r):
        falhas.append(f"NAO pegou afirmacao sem base: {frase!r}")

# ---- contagem: menos frases que produtos e' recusado -------------------
fonte = (Path(__file__).resolve().parent.parent
         / "engine/roteiro_produto.py").read_text(encoding="utf-8")
if "len(frases) != len(produtos)" not in fonte:
    falhas.append("nao confere se ha' uma frase por produto — o video "
                  "anunciaria o preco errado")

# ---- o prompt proibe explicitamente ------------------------------------
for termo in ("NAO INVENTE", "PROIBIDO", "NUNCA o usou"):
    if termo not in rp.PROMPT_ROTEIRO:
        falhas.append(f"o prompt perdeu a proibicao: {termo!r}")
# e pede tamanho de frase parecido, que a montagem precisa
if "12 e 22 palavras" not in rp.PROMPT_ROTEIRO:
    falhas.append("o prompt nao limita o tamanho da frase — cena ficaria "
                  "de 9s ou virava corte seco")

# ---- entrada vazia nao explode ----------------------------------------
if rp.gerar([]) != {}:
    falhas.append("lista vazia deveria devolver {} sem chamar o modelo")
if rp.em_frases({}) != []:
    falhas.append("roteiro vazio deveria devolver lista vazia")

# ---- a ordem das frases e' abertura, produtos, fechamento --------------
ordem = rp.em_frases(limpo)
if ordem[0] != limpo["abertura"] or ordem[-1] != limpo["fechamento"]:
    falhas.append(f"ordem errada das frases: {ordem}")
if len(ordem) != 4:
    falhas.append(f"esperava 4 frases (1+2+1), veio {len(ordem)}")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_roteiro_produto: {len(RUINS)} afirmacoes sem base pegas, "
      "roteiro limpo passa, contagem conferida")
