# -*- coding: utf-8 -*-
"""Reconfere o campo `queda` do registro historico contra a serie de precos.

    python -m engine.reparar_queda              so' MEDE, nao escreve
    python -m engine.reparar_queda --escrever   reescreve, com copia antes

## O QUE ESTE SCRIPT NAO E'

⛔ Ele NAO poe o preco de hoje no registro historico. `produtos_publicados.
jsonl` e' append-only e o `preco` de cada linha e' o do DIA DA CAPTURA — isso
esta' certo e e' o desenho. Quem exibe preco le' a serie, e isso ja' foi
consertado em 15/09/2026.

## O QUE ELE CONSERTA

O campo `queda` e' a queda que NOS mediamos no momento em que a linha foi
escrita. Ele tem de ser reconstruivel: a maior leitura nossa ATE' AQUELE DIA
contra o preco daquele dia, com o mesmo piso de 2% que a pagina e o cartaz
usam. Quando nao e', o registro esta' errado — nao velho, errado.

## ⚠️ A PREMISSA COM QUE EU COMECEI ESTAVA ERRADA, E A MEDICAO DESMENTIU

O handoff dizia que o arquivo guardava as quedas FALSAS de 32,1% e 34,0% dos
campeoes. Nao guarda: medido em 16/09/2026, os dois campeoes citados (Carregador
120W e Fone Lenovo GM2 Pro) estao gravados com 0,0% e 0,5%/0,7%, e a maior
queda do arquivo inteiro e' 18,1%. Aquelas quedas falsas nasciam em
`garimpo.historico()`, que juntava varias leituras do mesmo dia — e foram
mortas la', consolidando pelo MENOR do dia.

⭐ O DEFEITO DE VERDADE ESTAVA DO OUTRO LADO, e por isso ninguem tinha olhado
pra ele: 87 de 87 linhas com `onde: varredura` foram gravadas com `queda: 0`,
todas na mesma hora (15/09 as 17h, um backfill). Oito delas eram produtos que
tinham caido DE VERDADE naquele mesmo dia — uma delas 42,7%.

⚠️ Errar a queda PRA MENOS e' o erro que ninguem reclama: o comprador chega na
loja e acha mais barato do que a gente disse. Mas ele apaga justamente o que
esta operacao vende. E' a mesma familia do preco velho de 15/09, pelo avesso.
"""
from __future__ import annotations

import argparse
import collections
import json
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLICADOS = RAIZ / "estado" / "produtos_publicados.jsonl"
PRECOS = RAIZ / "estado" / "precos_vistos.jsonl"

# ⛔ SEM PISO, E ISTO FOI UMA CORRECAO DE ROTA NO MEIO DO CONSERTO.
#
# A primeira versao usava o piso de 2% da pagina (`publicar_bio._antes`, linha
# 485) e do cartaz. Com ele davam 38 divergencias; sem ele, 8. As 30 de
# diferenca eram todas quedas pequenas (0,8% a 1,5%) que eu ia zerar.
#
# ⚠️ Elas nao estavam erradas. `garimpo.desconto_honesto` — que e' quem GRAVA
# este campo — nao tem piso nenhum: devolve qualquer queda positiva. Zerar
# aquelas linhas seria reescrever uma medicao historica com uma regra que ela
# nunca usou, e chamar de "reparo" a imposicao da minha regra sobre o passado.
#
# ⭐ O piso de 2% e' regra de EXIBICAO, nao de medicao. O registro guarda o
# que foi medido; a pagina e o cartaz decidem a partir de quanto vale a pena
# dizer que caiu. Sao papeis diferentes e esta' certo que divirjam.
PISO = 1.0

# ⚠️ Uma casa decimal, igual ao `garimpo`: `round(queda, 1)`. Comparar com mais
# precisao do que o produtor grava acusaria todo mundo.
TOLERANCIA = 0.1


def _num(preco: str) -> float:
    """"R$ 13,52" -> 13.52. Zero no que nao der pra ler."""
    try:
        return float(str(preco).replace("R$", "").replace(".", "")
                     .replace(",", ".").strip() or 0)
    except ValueError:
        return 0.0


def serie_por_dia() -> dict[int, dict[str, float]]:
    """id -> {dia: menor preco daquele dia}.

    ⛔ O MENOR DO DIA, e' a MESMA regra do `garimpo.historico()`. O mesmo id
    recebe precos de anuncios diferentes no mesmo dia (variante, kit maior,
    outro vendedor), e pegar o maior foi exatamente o que fabricou as quedas
    de 49% em produto que nao caiu.

    ⚠️ Aqui a serie NAO e' achatada em lista: o dia precisa sobreviver, porque
    o ponto deste script e' olhar so' o que ja' existia no dia da captura.
    """
    por_dia: dict[int, dict[str, float]] = collections.defaultdict(dict)
    if not PRECOS.exists():
        raise SystemExit(f"nao achei {PRECOS} — sem serie nao ha' o que conferir")
    for linha in PRECOS.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if not (d.get("id") and d.get("preco")):
            continue
        dia = str(d.get("quando") or "")[:10]
        try:
            v = float(d["preco"])
        except (TypeError, ValueError):
            continue
        if not dia or v <= 0:
            continue
        dias = por_dia[d["id"]]
        dias[dia] = min(dias[dia], v) if dia in dias else v
    return dict(por_dia)


def queda_do_dia(pid: int, dia: str, preco_do_dia: float,
                 serie: dict[int, dict[str, float]]) -> float | None:
    """A queda que este registro DEVERIA ter tido. None se nao da' pra saber.

    ⛔ SO' OS PONTOS ATE' `dia`, e este e' o coracao do script. Usar a serie
    inteira compararia o registro de 13/09 com um preco coletado em 15/09 e
    acusaria como defeito o funcionamento correto de um arquivo append-only.
    Medido: com a serie inteira dao 18 divergencias; so' com o passado, 15 —
    as tres de diferenca eram registros CERTOS.

    ⚠️ E `None` nao e' zero. Produto sem nenhuma leitura ate' aquele dia nao
    tem queda "de 0%": nao tem queda conhecida, e reescrever pra 0 seria
    inventar uma medicao. Falha fechada do lado de nao mexer.
    """
    ate = [v for d, v in serie.get(pid, {}).items() if d <= dia]
    if not ate or preco_do_dia <= 0:
        return None
    maior = max(ate)
    if maior <= preco_do_dia * PISO:
        return 0.0
    return round(100 * (maior - preco_do_dia) / maior, 1)


def auditar() -> tuple[list[dict], list[tuple]]:
    """Le' o registro e devolve (linhas, divergencias)."""
    serie = serie_por_dia()
    linhas = [json.loads(x) for x in
              PUBLICADOS.read_text(encoding="utf-8").splitlines() if x.strip()]
    divergencias = []
    for i, r in enumerate(linhas):
        pid = r.get("id")
        if not pid:
            # ⚠️ 29 linhas nao tem id (vieram do manifesto, pela vitrine).
            # Sem id nao ha' serie, e sem serie nao ha' o que conferir.
            continue
        esperada = queda_do_dia(int(pid), (r.get("quando") or "")[:10],
                                _num(r.get("preco")), serie)
        if esperada is None:
            continue
        gravada = float(r.get("queda") or 0)
        if abs(esperada - gravada) > TOLERANCIA:
            divergencias.append((i, gravada, esperada, r))
    return linhas, divergencias


def main() -> None:
    a = argparse.ArgumentParser(description="reconfere o campo queda")
    a.add_argument("--escrever", action="store_true",
                   help="reescreve o arquivo (faz copia antes)")
    o = a.parse_args()

    linhas, div = auditar()
    print(f"{len(linhas)} registros, {len(div)} com queda divergente\n")
    contra_nos = [d for d in div if d[2] > d[1]]
    a_nosso_favor = [d for d in div if d[2] < d[1]]
    # ⭐ OS DOIS LADOS SEPARADOS, e o segundo primeiro. Queda gravada MAIOR que
    # a serie sustenta e' desconto anunciado que nao existe — e' o unico lado
    # que custa credibilidade, mesmo sendo o lado menor.
    print(f"  a nosso favor (anunciamos queda a MAIS): {len(a_nosso_favor)}")
    for _, g, e, r in sorted(a_nosso_favor, key=lambda x: x[1] - x[2],
                             reverse=True)[:10]:
        print(f"      {g:5.1f}% -> {e:5.1f}%   {(r.get('nome') or '')[:46]}")
    print(f"\n  contra nos (anunciamos queda a MENOS): {len(contra_nos)}")
    for _, g, e, r in sorted(contra_nos, key=lambda x: x[2] - x[1],
                             reverse=True)[:10]:
        print(f"      {g:5.1f}% -> {e:5.1f}%   {(r.get('nome') or '')[:46]}")

    if not o.escrever:
        print("\n(so' medicao — use --escrever pra corrigir)")
        return
    if not div:
        print("\nnada a escrever")
        return

    # ⛔ COPIA ANTES, sempre. Este arquivo e' append-only por desenho e nao tem
    # como ser reconstruido: o `link` de cada linha carrega o tracking do
    # momento, e buscar o produto de novo amanha devolve outro link.
    copia = PUBLICADOS.with_suffix(".jsonl.antes_do_reparo_queda")
    shutil.copy2(PUBLICADOS, copia)
    print(f"\ncopia em {copia.name}")

    for i, _, esperada, _ in div:
        linhas[i]["queda"] = esperada
        # ⭐ A LINHA CONFESSA QUE FOI MEXIDA. Registro historico corrigido em
        # silencio e' pior que registro errado: quem ler daqui a um mes nao
        # tem como saber se aquele numero foi medido no dia ou reconstruido.
        linhas[i]["queda_reparada_em"] = "2026-09-16"

    # ⚠️ ESCREVE INTEIRO E DE UMA VEZ, sobre o arquivo original. Escrever
    # linha a linha deixaria o registro pela metade se algo estourar no meio.
    corpo = "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in linhas)
    PUBLICADOS.write_text(corpo, encoding="utf-8")

    # ⛔ E CONFERE DEPOIS DE ESCREVER. Escrever e anunciar sem reler e' o que
    # transformou "deployment complete" em prova falsa duas vezes este mes.
    _, restam = auditar()
    print(f"{len(div)} registros corrigidos; divergencias restantes: "
          f"{len(restam)}")
    if restam:
        raise SystemExit("sobrou divergencia depois do reparo — isto nao e' "
                         "sucesso, e a copia esta' do lado")


if __name__ == "__main__":
    main()
