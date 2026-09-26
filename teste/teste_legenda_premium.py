# -*- coding: utf-8 -*-
"""Guarda do estilo 3 (legenda PREMIUM) de engine/legendas.py.

POR QUE EXISTE

Autópsia de 25/09/2026 na legenda estilo 2, sobre a PREVIA3: letra pequena
(3,8% da altura), grupo fixo de 3 cortando a frase ("MILHÕES PORQUE UMA"),
cores sem critério, sumiço em fundo claro e karaokê desligado. O Bryan
aprovou o premium na comparação lado a lado.

⚠️ O DEFEITO QUE SÓ APARECEU NA TELA: com os 60 ms de antecipação, o grupo
novo entrava antes do anterior sair. O libass trata isso como colisão e
empurra o grupo novo pra cima — uma caixa escura fantasma acima da frase o
tempo todo. Nada no render reclama; por isso [3] mede a sobreposição.

Roda com: python teste/teste_legenda_premium.py
"""
import os
import re
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import legendas, destaque  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def fala(texto, passo=0.32, pausas=()):
    """Palavras com tempo; `pausas` = índices depois dos quais há silêncio."""
    out, t = [], 0.0
    for i, w in enumerate(texto.split()):
        out.append({"palavra": w, "inicio": t, "fim": t + passo - 0.02})
        t += passo + (0.6 if i in pausas else 0)
    return out


def eventos(arq):
    ev = []
    for l in Path(arq).read_text(encoding="utf-8").splitlines():
        if not l.startswith("Dialogue:"):
            continue
        c = l.split(",", 9)
        seg = lambda s: (lambda h, m, x: int(h) * 3600 + int(m) * 60 + float(x))(*s.split(":"))
        ev.append({"layer": int(c[0].split()[-1]), "ini": seg(c[1]), "fim": seg(c[2]),
                   "estilo": c[3], "ml": int(c[5]), "mr": int(c[6]), "texto": c[9]})
    return ev


def plano(txt):
    return re.sub(r"\{[^}]*\}", "", txt)


TMP = Path(tempfile.mkdtemp())
FRASE = "milhões porque uma poeira só pode destruir um chip inteiro"

print(__doc__.splitlines()[0])

print("\n[1] o premium NÃO chama o Gemini (quem acende é o tempo da fala)")
chamou = []
original = destaque.marcar
destaque.marcar = lambda g: chamou.append(1) or [(None, None)] * len(g)
arq = legendas.escrever(fala(FRASE), TMP / "p.ass", 1080, 1920, estilo=3)
checar(not chamou, "estilo 3 não chamou destaque.marcar")
legendas.escrever(fala(FRASE), TMP / "e2.ass", 1080, 1920, estilo=2)
checar(bool(chamou), "NEGATIVO: estilo 2 continua chamando (não foi tocado)")
destaque.marcar = original

ev = eventos(arq)
sombras = [e for e in ev if e["estilo"] == "S"]
textos = [e for e in ev if e["estilo"] == "P"]

print("\n[2] grupo por sentido: nenhum termina em palavra fraca")
for s in sombras[:-1]:
    ultima = plano(s["texto"]).replace("\\N", " ").split()[-1].lower()
    checar(ultima not in legendas.PALAVRA_FRACA, f"'{plano(s['texto'])}' não termina em '{ultima}'")
grupos = [plano(s["texto"]).replace("\\N", " ") for s in sombras]
checar(" ".join(grupos) == FRASE.upper(), "nenhuma palavra some nem repete")

print("\n[3] sem sobreposição na mesma camada (a caixa fantasma)")
for camada in (sombras, textos):
    ordem = sorted(camada, key=lambda e: e["ini"])
    sobre = [(a["texto"][-20:], b["texto"][-20:]) for a, b in zip(ordem, ordem[1:])
             if b["ini"] < a["fim"] - 1e-6]
    checar(not sobre, f"camada {camada[0]['estilo']}: {len(sobre)} sobreposição(ões)")

print("\n[4] karaokê: em cada instante, UMA palavra acesa em âmbar")
for e in textos:
    checar(e["texto"].count(legendas._PREMIUM_ACENTO) == 1,
           f"{plano(e['texto'])!r} tem exatamente um acento")

print("\n[5] a quebra de linha é a MESMA na sombra e no texto")
estreito = [(0.0, 1e9, 0.20, "ambos")]     # a coluna de botões do app
longa = ("o chip passa porque uma poeira microscópica destrói a "
         "internacionalização da transformação tecnológica")
arq2 = legendas.escrever(fala(longa), TMP / "q.ass", 1080, 1920,
                         estilo=3, estreito=estreito)
ev2 = eventos(arq2)
cabe = int((1080 - 2 * 216) / (int(1920 * legendas._PREMIUM_CORPO) * legendas._PREMIUM_LETRA))
for s in [e for e in ev2 if e["estilo"] == "S"]:
    txt = plano(s["texto"])
    irmaos = [e for e in ev2 if e["estilo"] == "P" and s["ini"] <= e["ini"] < s["fim"]]
    checar({plano(e["texto"]).count("\\N") for e in irmaos} == {txt.count("\\N")},
           f"'{txt}': sombra e texto quebram igual")
    for linha in txt.split("\\N")[:-1]:
        checar(linha.split()[-1].lower() not in legendas.PALAVRA_FRACA,
               f"'{linha}' não deixa palavra fraca pendurada")
    if max(len(x) for x in txt.split("\\N")) > cabe:
        checar("\\fs" in s["texto"], f"'{txt}' passa de {cabe} letras e ENCOLHE")
checar(any("\\fs" in e["texto"] for e in ev2), "palavra gigante sozinha ENCOLHE")
checar(all(e["ml"] == e["mr"] == 216 for e in ev2), "margens do balão chegam ao evento")
checar(not any("\\N" in e["texto"] for e in ev2),
       "com a coluna normal (20%) grupo de até 16 letras cabe numa linha")
balao = [(0.0, 1e9, 0.28, "ambos")]      # balão largo na tela
ev3 = eventos(legendas.escrever(fala(FRASE), TMP / "b.ass", 1080, 1920,
                                estilo=3, estreito=balao))
checar(any(plano(e["texto"]) == "SÓ PODE\\NDESTRUIR" for e in ev3 if e["estilo"] == "S"),
       "balão largo: 'SÓ PODE / DESTRUIR' quebra no ponto certo")

print("\n[6] NEGATIVO: frase curta não quebra")
checar(not any("\\N" in e["texto"] for e in ev), "'UM CHIP INTEIRO' fica numa linha")

print("\n[7] capa limpa: nada antes do título sair")
arq3 = legendas.escrever(fala(FRASE), TMP / "c.ass", 1080, 1920, estilo=3, oculto_ate=1.0)
checar(min(e["ini"] for e in eventos(arq3)) >= 1.0 - legendas._PREMIUM_ANTECIPA - 1e-6,
       "primeiro evento só depois de oculto_ate")

print("\n[8] faixa_ocupada cobre a letra premium (a cascata pergunta aqui)")
topo, base = legendas.faixa_ocupada(1920)
corpo = int(1920 * legendas._PREMIUM_CORPO)
checar(base - topo >= 2 * corpo, f"faixa de {base - topo}px cabe 2 linhas de {corpo}px")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
