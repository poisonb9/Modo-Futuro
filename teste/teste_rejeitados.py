# -*- coding: utf-8 -*-
"""Teste da guarda de REJEITADOS — a decisao editorial do Bryan.

POR QUE EXISTE

Em 30/08/2026 o clipe "666 MILHOES de Transistores" apareceu agendado pro dia
01/09, pela QUARTA vez, depois de o Bryan ter apagado as tres anteriores. A
dedup nova (engine/dedup.py) nao pegou, e nao tinha como: ela compara contra o
que foi PUBLICADO, e apagar um post agendado no Buffer nao deixa rastro
nenhum — some do `scheduled` e nunca entra no `sent`.

Quem deveria pegar e' o `engine/rejeitados.py`. Ele falhou por DOIS motivos
independentes, e este teste cobre os dois:

  1. A LISTA NAO CHEGAVA NA NUVEM. O `.gitignore` tinha `estado/*` com uma
     unica excecao (`videos_trabalhados.json`), entao o runner do Actions
     nascia com o registro VAZIO e a checagem nunca era verdadeira. Corrigido
     com uma segunda excecao.

  2. A COMPARACAO ERA POR IGUALDADE. Mesmo defeito que a dedup ja' tinha: a
     chave guardada e' o titulo curto, mas o texto real traz titulo+descricao
     na mesma linha. Prova de que doia: o registro tem DUAS entradas pro mesmo
     clipe 666, uma curta e uma longa, porque a curta nao casava.

OS CASOS NEGATIVOS  (sem eles o teste nao prova nada)

  falso positivo    dos 101 posts reais, so' os que ESTAO no registro podem
                    casar. Medido: 11 casam, 90 nao. Uma guarda que recusa
                    tudo passaria num teste so' de caso positivo — e nunca
                    publicaria nada.

  ganho medido      igualdade pega 9, prefixo pega 11. Os +2 sao rejeicoes de
                    verdade. Se o ganho sumir, a regra regrediu.

Roda com: python teste/teste_rejeitados.py
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import dedup, rejeitados

POSTS = RAIZ / "teste" / "dados" / "posts_modofuturo.json"
falhas = []


def chave(t: str) -> str:
    t = (t or "").split("#")[0]
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", t.lower())[:70]


def checar(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


print(__doc__.splitlines()[0])

# --- 1. a lista existe e chega ao disco ------------------------------------
print("\n[1] o registro esta' versionado e legivel")
arq = RAIZ / "estado" / "rejeitados.json"
checar(arq.exists(), f"{arq.relative_to(RAIZ)} existe")
reg = rejeitados.chaves()
checar(len(reg) >= 18, f"registro com {len(reg)} chave(s), esperado >= 18")

gi = (RAIZ / ".gitignore").read_text(encoding="utf-8")
checar("!estado/rejeitados.json" in gi,
       ".gitignore abre excecao pro registro (senao o runner nasce vazio)")

# --- 2. caso POSITIVO: o clipe que voltou 4x ------------------------------
print("\n[2] caso positivo: o '666 MILHOES' e' barrado")
k666 = chave("666 MILHOES de Transistores em 1mm²! O Novo Chip do Capiroto da IBM")
checar(dedup.ja_visto(k666, reg), "o texto LONGO (titulo+descricao) casa")
checar(dedup.ja_visto(chave("666 MILHOES de Transistores em 1mm2"), reg),
       "o texto CURTO (so' titulo) tambem casa")

# --- 3. caso NEGATIVO: nao pode barrar quem nao foi rejeitado -------------
print("\n[3] caso negativo: 90 dos 101 posts reais NAO podem casar")
textos = [p if isinstance(p, str) else (p.get("text") or "")
          for p in json.loads(POSTS.read_text(encoding="utf-8"))]
casam = [t for t in textos if dedup.ja_visto(chave(t), reg)]
checar(len(textos) == 101, f"{len(textos)} posts reais carregados")
checar(len(casam) == 11, f"{len(casam)} casam, esperado exatamente 11")

# --- 4. o ganho do prefixo sobre a igualdade ------------------------------
print("\n[4] o prefixo ganha da igualdade, e o ganho e' legitimo")
exato = [t for t in textos if chave(t) in reg]
checar(len(exato) == 9, f"igualdade pega {len(exato)}, esperado 9")
ganho = [t for t in casam if t not in exato]
checar(len(ganho) == 2, f"prefixo pega +{len(ganho)}, esperado +2")

# --- 5. clipe novo passa ---------------------------------------------------
print("\n[5] um clipe que nunca foi rejeitado passa")
novo = chave("A megafabrica de chips de Elon Musk que quer mudar o mundo")
checar(not dedup.ja_visto(novo, reg), "clipe limpo da fila atual nao e' barrado")
checar(not dedup.ja_visto("", reg), "chave vazia nunca casa com nada")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
