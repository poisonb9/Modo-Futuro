# -*- coding: utf-8 -*-
"""Calendario de capas: a DATA do momento entra no titulo e na legenda.

⭐ 03/10/2026 (dono, "sim!!!! Perfeito"): revista teen fazia capa por ocasiao
(volta as aulas, Dia dos Namorados, aniversario do idolo); o acervo de
marketing confirma que contexto de data cria urgencia. Aqui so' existe a
SUGESTAO: o modelo usa se combinar com o fato, e nunca inventa ligacao.

⚠️ Aniversario so' entra com data CONFERIDA. Data errada de idol e' o tipo de
erro que fa corrige nos comentarios — pior que nao citar.
"""
from __future__ import annotations

import datetime

# (mes, dia, nome, dias de antecedencia, canais — vazio = todos)
DATAS = [
    (1, 1, "Ano Novo", 3, ()),
    (2, 3, "volta as aulas", 10, ("truque.importado", "camarim.kpop", "cozinha.importada")),
    (3, 8, "Dia da Mulher", 2, ()),
    (6, 12, "Dia dos Namorados", 7, ()),
    (6, 24, "festa junina", 10, ("cozinha.importada", "truque.importado")),
    (7, 28, "volta as aulas", 7, ("truque.importado", "camarim.kpop", "cozinha.importada")),
    (10, 12, "Dia das Criancas", 7, ("atefalhar", "camarim.kpop", "cozinha.importada")),
    (10, 31, "Halloween", 7, ("truque.importado", "camarim.kpop", "atefalhar", "cozinha.importada")),
    (12, 25, "Natal", 10, ()),
    (12, 31, "Reveillon", 4, ("truque.importado", "cozinha.importada")),
]

# Aniversarios conferidos (Stray Kids e aespa/IVE), so' K-pop.
ANIVERSARIOS = {
    "bang chan": (10, 3), "lee know": (10, 25), "changbin": (8, 11),
    "hyunjin": (3, 20), "han": (9, 14), "felix": (9, 15),
    "seungmin": (9, 22), "i.n": (2, 8),
    "karina": (4, 11), "winter": (1, 1), "wonyoung": (8, 31),
}
KPOP = ("camarim.kpop", "truque.importado")


def _faltam(hoje: datetime.date, mes: int, dia: int) -> int:
    alvo = datetime.date(hoje.year, mes, dia)
    if alvo < hoje:
        alvo = datetime.date(hoje.year + 1, mes, dia)
    return (alvo - hoje).days


def ocasiao(canal: str, titulo: str = "", hoje: datetime.date | None = None) -> str:
    """Frase curta com a data que vale AGORA para o canal, ou ''."""
    hoje = hoje or datetime.date.today()
    t = f" {(titulo or '').lower()} "
    if canal in KPOP:
        for nome, (m, d) in ANIVERSARIOS.items():
            # palavra inteira: "han" nao pode casar "hand"/"chance"
            if f" {nome} " in t.replace(",", " ").replace("!", " ") and _faltam(hoje, m, d) <= 3:
                dias = _faltam(hoje, m, d)
                return (f"aniversario de {nome.title()} "
                        + ("e' HOJE" if dias == 0 else f"em {dias} dia(s)"))
    for m, d, nome, antes, canais in DATAS:
        if canais and canal not in canais:
            continue
        dias = _faltam(hoje, m, d)
        if dias <= antes:
            return nome + (" e' hoje" if dias == 0 else f" em {dias} dia(s)")
    return ""


def dica(canal: str, titulo: str = "", hoje: datetime.date | None = None) -> str:
    """Linha pronta para colar no prompt (vazia quando nao ha' data)."""
    o = ocasiao(canal, titulo, hoje)
    return (f"\nDATA DO MOMENTO: {o}. SO' se combinar naturalmente com o fato, "
            "ligue a chamada/pergunta a essa data; senao, ignore.\n") if o else ""
