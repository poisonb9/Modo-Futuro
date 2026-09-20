# -*- coding: utf-8 -*-
"""A primeira tela tem de entregar o PRODUTO INTEIRO, com preco visivel.

Nasceu do defeito de 20/09/2026, que o Bryan viu e eu nao: com a barra do
Safari aparecendo, a tela util cai para ~660 px e o anuncio principal ficava
CORTADO pela barra de abas — o preco dele 89 px abaixo dela, invisivel.

⛔ E O DEFEITO NAO VEIO DE UM PASSO ERRADO. A linha viva, o botao "Comprar
agora" e a prova social foram cada um uma decisao boa, medida na hora. O que
ninguem mediu foi a SOMA: quanto do primeiro quadro sobrava para o produto
depois de tudo. Este teste existe para que a soma tenha dono.

⚠️ O QUE ELE NAO FAZ: nao mede layout de verdade. Medir altura renderizada
exige motor de renderizacao, e aqui so' ha' jsdom (que nao faz layout).
Entao ele guarda as INVARIANTES que produziram o defeito, que e' o que da'
para guardar com honestidade:

  1. a media query de altura existe e encolhe as pecas do topo;
  2. toda altura FIXA declarada no topo tem contrapartida em tela baixa —
     se alguem acrescentar peca nova ao cabecalho sem pensar no orcamento,
     isto reprova;
  3. a regra da foto em tela baixa VENCE a quadrada na cascata. Com caso
     negativo: e' exatamente o erro que eu cometi — escrevi a regra, ela
     perdeu para outra de mesma especificidade mais abaixo no arquivo, e o
     cartao continuou em 358 px com a regra "aplicada".
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_BRUTO = (RAIZ / "paginas" / "todos.html").read_text(encoding="utf-8")
# ⛔ COMENTARIO FORA ANTES DE QUALQUER COISA. A primeira versao deste teste
# reprovou o caso negativo por motivo errado: os `/* ... */` do CSS entraram
# no que eu chamava de "seletor", e cada ponto do texto ("nao e' excecao
# nova.") virou uma classe na conta de especificidade. O detector estava
# medindo prosa. Guarda que le' comentario nao le' codigo.
PAGINA = re.sub(r"/\*.*?\*/", " ", _BRUTO, flags=re.S)

FALHAS = 0


def checar(ok, msg):
    global FALHAS
    print(("  ok   " if ok else "  [x]  ") + msg)
    if not ok:
        FALHAS += 1


def span_media(texto: str, consulta: str) -> tuple[int, int]:
    """(inicio, fim) do corpo de um `@media (...)`, contando chaves."""
    i = texto.find("@media (" + consulta + ")")
    if i < 0:
        return (-1, -1)
    j = texto.find("{", i)
    nivel, k = 0, j
    while k < len(texto):
        if texto[k] == "{":
            nivel += 1
        elif texto[k] == "}":
            nivel -= 1
            if nivel == 0:
                return (j + 1, k)
        k += 1
    return (-1, -1)


def bloco_media(texto: str, consulta: str) -> str:
    a, b = span_media(texto, consulta)
    return texto[a:b] if a >= 0 else ""


def especificidade(seletor: str) -> tuple[int, int, int]:
    """(ids, classes/atributos/pseudo-classes, elementos). Basta para o que
    esta' em jogo aqui; nao pretende ser um parser de CSS completo."""
    s = re.sub(r"::[a-z-]+", " ", seletor)
    ids = len(re.findall(r"#[\w-]+", s))
    classes = len(re.findall(r"\.[\w-]+", s)) + len(re.findall(r"\[[^\]]+\]", s))
    elementos = len(re.findall(r"(?:^|[\s>+~])([a-z][\w-]*)", s))
    return (ids, classes, elementos)


print("1. A MEDIA QUERY DE ALTURA EXISTE E ENCOLHE O TOPO")
curto = bloco_media(PAGINA, "max-height: 740px")
checar(bool(curto), "existe @media (max-height: 740px)")
for peca in (".marca-logo", "header", "h1", ".vivo"):
    checar(peca in curto, f"encolhe {peca} em tela baixa")
# ⚠️ altura, nao largura: o defeito aparece no MESMO aparelho conforme a
# barra do Safari aparece e some. `max-width` nao veria isso.
checar("max-width" not in (PAGINA[PAGINA.find("@media (max-height: 740px)") - 80:
                           PAGINA.find("@media (max-height: 740px)")] or ""),
       "a guarda e' por ALTURA (o Safari muda a altura, nao a largura)")

print()
print("2. O ORCAMENTO TEM DONO: altura fixa no topo exige contrapartida")
# alturas fixas declaradas nas pecas do cabecalho, fora da media de altura
fora_da_media = PAGINA.replace(curto, "") if curto else PAGINA
alvos = (".vivo", ".marca-logo")
for alvo in alvos:
    m = re.search(re.escape(alvo) + r"\s*\{[^}]*?\bheight:\s*(\d+)px", fora_da_media)
    if not m:
        continue
    checar(alvo in curto,
           f"{alvo} tem altura fixa ({m.group(1)}px) E contrapartida em tela baixa")

print()
print("3. A REGRA DA FOTO EM TELA BAIXA VENCE A QUADRADA")


def foto_vence(texto: str) -> tuple[bool, str]:
    """A ultima palavra sobre `aspect-ratio` da foto da vitrine em tela
    baixa e' 4/3? Devolve (venceu, porque)."""
    regras = []
    for m in re.finditer(r"([#.][^{};@]*?\bvfoto\b[^{}]*?)\{([^}]*)\}", texto):
        sel, corpo = m.group(1).strip(), m.group(2)
        ar = re.search(r"aspect-ratio:\s*([^;]+);", corpo)
        if ar:
            regras.append((especificidade(sel), m.start(), sel, ar.group(1).strip()))
    if not regras:
        return False, "nenhuma regra de aspect-ratio na foto"
    ini, fim = span_media(texto, "max-height: 740px")
    # ⛔ POR POSICAO, NAO POR TEXTO. A primeira versao perguntava se o
    # seletor vencedor "estava dentro" do bloco com `in` — e `.vitrine
    # .vfoto` aparece nos DOIS lugares, entao a resposta era sempre sim e o
    # caso negativo nunca reprovava. Guarda que confunde duas regras iguais
    # por texto nao guarda cascata nenhuma.
    dentro = lambda pos: ini >= 0 and ini <= pos < fim
    if not any(dentro(r[1]) for r in regras):
        return False, "nao ha' regra de foto dentro da media de altura"
    # vence quem tem maior especificidade; empate, quem vem depois
    campea = max(regras, key=lambda r: (r[0], r[1]))
    return dentro(campea[1]), f"quem vence e' `{campea[2]}` -> {campea[3]}"


ok, porque = foto_vence(PAGINA)
checar(ok, "a regra de tela baixa ganha a cascata (" + porque + ")")

# ⛔ CASO NEGATIVO, e e' o coracao deste arquivo: sem o `#vitrine` a regra
# empata em especificidade com a quadrada, que vem DEPOIS no arquivo e
# vence. Foi exatamente o que aconteceu comigo: a regra estava escrita, o
# build passava, e o cartao continuava em 358 px. Se o detector nao reprovar
# aqui, ele nao esta' detectando nada.
sem_id = PAGINA.replace("#vitrine .vitrine .vfoto", ".vitrine .vfoto")
ok_neg, porque_neg = foto_vence(sem_id)
checar(not ok_neg,
       "NEGATIVO: sem o `#vitrine`, o detector REPROVA (" + porque_neg + ")")

print()
print("tudo verde" if not FALHAS else f"{FALHAS} FALHA(S)")
sys.exit(1 if FALHAS else 0)
