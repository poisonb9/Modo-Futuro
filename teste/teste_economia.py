# -*- coding: utf-8 -*-
"""O montante de hoje e o multometro do RADAR (queda encontrada). Sem rede.

⛔ O que protege (16/09/2026):
1. "a menos hoje" = soma de (antes - preco) so' onde `antes` existe, e o
   ultimo ponto da linha E' esse numero (nao o da serie consolidada — os
   dois divergiam: R$ 344 x R$ 293 na mesma tela);
2. o multometro e' do RADAR (decisao do Bryan): por produto, maior preco
   visto - menor preco visto, piso de 2%; produto fora do ar continua contando;
3. ⛔ so' sobe, por construcao — preco que volta a subir AUMENTA a queda
   encontrada, nunca reduz;
4. sem serie, total 0 (a pagina esconde, nao mostra R$ 0).
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "paginas"))
import publicar_bio  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


tmp = Path(tempfile.mkdtemp()); (tmp / "estado").mkdir()
raiz = publicar_bio.RAIZ
try:
    publicar_bio.RAIZ = tmp
    (tmp / "estado" / "precos_vistos.jsonl").write_text("\n".join(json.dumps(x) for x in [
        {"id": 1, "preco": 20.0, "quando": "2026-09-10"}, {"id": 1, "preco": 10.0, "quando": "2026-09-14"},
        {"id": 2, "preco": 50.0, "quando": "2026-09-12"}, {"id": 2, "preco": 40.0, "quando": "2026-09-15"},
    ]) + "\n", encoding="utf-8")

    print("1. O NUMERO DE HOJE E O FIM DA LINHA")
    from datetime import date
    dados = [{"id": 1, "preco": "R$ 10,00", "antes": "R$ 20,00"},
             {"id": 2, "preco": "R$ 40,00", "antes": "R$ 50,00"},
             {"id": 3, "preco": "R$ 9,00", "antes": ""}]
    e = publicar_bio.economia(dados)
    checar(e["hoje"] == 20.0 and e["n"] == 2, f"hoje = 10 + 10 = 20 em 2 produtos ({e['hoje']}, {e['n']})")
    checar(e["serie"] and e["serie"][-1] == [date.today().isoformat()[5:], 20.0],
           f"o ultimo ponto e' o de hoje E vale o numero do cartao ({e['serie'][-1:]})")

    print()
    print("2. O MULTOMETRO DO RADAR: maior - menor por produto, piso de 2%, so' sobe")
    r = publicar_bio.economia_radar(dias=10)
    checar(r["total"] == 20.0 and r["produtos"] == 2, f"20-10 + 50-40 = 20 em 2 produtos ({r['total']}, {r['produtos']})")
    vals = [v for _d, v in r["serie"]]
    checar(all(b >= a for a, b in zip(vals, vals[1:])) and vals[-1] == 20.0,
           f"a linha nunca desce e termina no total ({vals})")
    # ⛔ caso negativo teorematico: preco que SOBE depois nao reduz nada, e
    # oscilacao de 1% nao conta
    with (tmp / "estado" / "precos_vistos.jsonl").open("a", encoding="utf-8") as f:
        for x in ({"id": 1, "preco": 30.0, "quando": "2026-09-16"},
                  {"id": 7, "preco": 100.0, "quando": "2026-09-15"},
                  {"id": 7, "preco": 99.0, "quando": "2026-09-16"}):
            f.write(json.dumps(x) + chr(10))
    r2 = publicar_bio.economia_radar(dias=10)
    checar(r2["total"] == 30.0 and r2["produtos"] == 2,
           f"preco que subiu pra 30 AUMENTA a queda encontrada (30-10); 1% nao conta ({r2['total']}, {r2['produtos']})")

    print()
    print("3. SEM SERIE, ZERO E VAZIO")
    (tmp / "estado" / "precos_vistos.jsonl").write_text("", encoding="utf-8")
    r3 = publicar_bio.economia_radar(dias=5)
    checar(r3["total"] == 0.0 and r3["produtos"] == 0, f"zero ({r3['total']})")
finally:
    publicar_bio.RAIZ = raiz
    shutil.rmtree(tmp, ignore_errors=True)

print()
print("4. A PAGINA: o bloco e' o radar, com linha, e some quando zero")
HTML = (RAIZ / "paginas" / "todos.html").read_text(encoding="utf-8")
import re
f = re.search(r"function montarEconomia\(\) \{(.*?)" + chr(10) + r"  \}", HTML, re.S)
corpo = f.group(1) if f else ""
checar("(ECONOMIA || {}).radar" in corpo and "grafico({ serie: r.serie" in corpo, "le' ECONOMIA.radar e desenha a serie dele")
checar("if (!(r.total > 0)) { return; }" in corpo, "R$ 0 nao aparece")
checar("economia no bolso dos clientes" in corpo and "queda de preço encontrada pelo radar" in corpo,
       "rotulo curto na tela, e a definicao honesta no title")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
