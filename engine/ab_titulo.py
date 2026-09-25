# -*- coding: utf-8 -*-
"""Teste A/B do TITULO NA TELA (25/09/2026, pedido do dono).

    A = o titulo como sai hoje (afirmacao: "A maquina de 400 milhoes")
    B = o MESMO fato reescrito como PERGUNTA ("Por que essa maquina custa 400 milhoes?")

So' o titulo NA TELA muda (os 2 s de abertura, que tambem sao a capa). A
legenda do post continua igual nos dois grupos: variar duas coisas juntas e'
o erro de 09/09, quando ninguem soube qual mexeu no numero.

O grupo sai do HASH do trecho (fonte + inicio), entao e' meio a meio, sem
escolha humana, e o mesmo trecho cai sempre no mesmo grupo. O grupo viaja no
post.json e no manifesto (`ab_titulo`) para a leitura de desempenho separar.

⚠️ B que falhou (modelo fora, resposta ruim) sai como A e e' marcado
`B_falhou`: entra na conta de NENHUM grupo. Misturar deixaria o B parecido
com o A e o teste diria "tanto faz" sem ter testado.
"""
from __future__ import annotations

import hashlib
import os

LIGADO = os.environ.get("AB_TITULO", "1") != "0"
MAX_CHARS = 70


def grupo(fonte: str, inicio_s) -> str:
    h = hashlib.sha1(f"{fonte}|{round(float(inicio_s or 0), 1)}".encode()).hexdigest()
    return "A" if int(h[:8], 16) % 2 == 0 else "B"


def _limpar(t: str) -> str:
    t = (t or "").strip().strip('"').strip("'").splitlines()[0].strip() if t else ""
    return t


def como_pergunta(titulo: str) -> str | None:
    from . import modelo_texto
    r = modelo_texto.perguntar(
        "Reescreva o titulo abaixo de um video curto como UMA pergunta curiosa em "
        "portugues do Brasil, que faca a pessoa querer ver a resposta no video. "
        "Mantenha o mesmo fato, os mesmos nomes e numeros; nao invente nada. "
        f"No maximo {MAX_CHARS} caracteres, termina com '?', sem aspas, sem emoji, "
        "sem explicacao. Responda so' a pergunta.\n\n"
        f"Titulo: {titulo}")
    p = _limpar(r or "")
    if not p or not p.endswith("?") or len(p) > MAX_CHARS + 10 or len(p) < 12:
        return None
    return p


def aplicar(c: dict, fonte: str) -> str:
    """Decide o grupo, grava em `c` e devolve o titulo que vai NA TELA."""
    titulo = c.get("titulo", "")
    if not LIGADO or not titulo:
        return titulo
    g = grupo(fonte, c.get("inicio_s"))
    c["ab_titulo"] = g
    c["titulo_tela"] = titulo
    if g == "B":
        p = como_pergunta(titulo)
        if p:
            c["titulo_tela"] = p
        else:
            c["ab_titulo"] = "B_falhou"
    print(f"      A/B do titulo: grupo {c['ab_titulo']} -> \"{c['titulo_tela'][:60]}\"")
    return c["titulo_tela"]
