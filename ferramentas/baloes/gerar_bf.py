# -*- coding: utf-8 -*-
"""Balões EXCLUSIVOS da Black Friday (preto brilhante + ouro).

Mesmo caminho grátis do gerar_balao.py (Cloudflare Workers AI flux-2-dev),
só troca o estilo. Saída: paginas/baloes/<nome>.webp + <nome>_p.webp (celular).

    python -X utf8 ferramentas/baloes/gerar_bf.py                 # gera a lista toda
    python -X utf8 ferramentas/baloes/gerar_bf.py bf_coroa "a royal crown" 21   # um só (nome, forma, semente)

Dica: semente diferente = balão diferente com a mesma forma. Se sair sombra
ou objeto a mais, gere de novo com outra semente.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gerar_balao as g  # noqa: E402

g.ESTILO = ("a single inflatable metallic foil party balloon shaped like {forma}, glossy jet BLACK mylar "
            "with shiny GOLD foil edges and gold details, realistic crinkled seams and puffy inflated edges, "
            "bright specular highlights, a thin curly gold ribbon hanging from the knot below, product photo, "
            "centered, full balloon visible, plain pure white background, soft studio lighting, no shadow on "
            "the background, no text, no letters, no numbers, no logo, no other objects")

LISTA = [  # (nome, forma, semente)
    ("bf_porcento", "a big percent sign", 11),
    ("bf_etiqueta", "a price tag", 11),
    ("bf_sacola", "a shopping bag", 11),
    ("bf_raio", "a lightning bolt", 11),
    ("bf_presente", "a gift box with a bow", 23),
    ("bf_lupa", "a magnifying glass", 11),
    ("bf_coroa", "a royal crown", 11),
    ("bf_carrinho", "a shopping cart", 11),
    ("bf_cifrao", "a dollar sign", 11),
    ("bf_relogio", "an alarm clock", 11),
    ("bf_estrela", "a five-pointed star", 11),
    ("bf_cupom", "a coupon ticket with notches on both sides", 11),
]

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        g.gerar(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 11)
    else:
        for nome, forma, semente in LISTA:
            print(nome, g.gerar(nome, forma, semente))
