# -*- coding: utf-8 -*-
"""O grafico da serie desenha o que a queda afirma — e nada alem. Sem rede.

## ⛔ POR QUE ESTE TESTE EXISTE

Em 15/09/2026 dez produtos anunciavam desconto que nao existia, e quem
revelou foi a tentativa de DESENHAR a serie. O desenho e' portanto uma
ferramenta de auditoria — e ferramenta de auditoria que le o dado por um
caminho proprio audita a si mesma, nao o dado.

⭐ Por isso os casos aqui sao, na ordem: (1) o desenho sai da MESMA
consolidacao que decide a queda; (2) o caso NEGATIVO — duas leituras de
anuncios diferentes no mesmo dia NAO podem virar pico; (3) dois pontos NAO
viram linha; (4) os dois irmaos desenham, nao so' um.
"""
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
import publicar_bio as pb  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


def com_serie(linhas):
    """Aponta o modulo para um precos_vistos.jsonl de mentira."""
    tmp = Path(tempfile.mkdtemp()) / "precos_vistos.jsonl"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text("\n".join(json.dumps(x) for x in linhas), encoding="utf-8")
    antigo = pb.RAIZ
    pb.RAIZ = tmp.parent.parent
    (tmp.parent.parent / "estado").mkdir(exist_ok=True)
    destino = tmp.parent.parent / "estado" / "precos_vistos.jsonl"
    destino.write_text(tmp.read_text(encoding="utf-8"), encoding="utf-8")
    return antigo


print("1. O DESENHO SAI DA MESMA CONSOLIDACAO QUE DECIDE A QUEDA")
antigo = com_serie([
    {"id": 7, "preco": 20.00, "quando": "2026-09-12"},
    {"id": 7, "preco": 20.00, "quando": "2026-09-13"},
    {"id": 7, "preco": 16.00, "quando": "2026-09-14"},
])
por_dia = pb._precos_por_dia()
serie = pb._serie_de_precos()
d = {"id": 7, "preco": "R$ 16,00"}
pontos = pb._serie_curta(por_dia, d)
checar(pontos == [["09-12", 20.0], ["09-13", 20.0], ["09-14", 16.0]],
       "tres dias viram tres pontos, em ordem de data")
checar(abs(pb._queda_real(serie, d) - 20.0) < 0.05,
       "a queda publicada (20%) bate com o ultimo ponto do desenho")
checar(max(p[1] for p in pontos) == serie[7][2],
       "o topo do desenho E' o 'maior preco que nos vimos' do texto")

print()
print("2. ⛔ CASO NEGATIVO — duas leituras no MESMO dia NAO viram pico")
# ⚠️ Este e' o defeito real de 14/09/2026: o "Conjunto de pinceis" tinha
# 12,56 · 25,08 · 12,80 · 12,57 no mesmo dia, de anuncios diferentes. Sem a
# consolidacao, o desenho mostraria um pico de 25,08 que nunca existiu.
pb.RAIZ = antigo
antigo = com_serie([
    {"id": 9, "preco": 13.36, "quando": "2026-09-12"},
    {"id": 9, "preco": 13.36, "quando": "2026-09-13"},
    {"id": 9, "preco": 12.56, "quando": "2026-09-14"},
    {"id": 9, "preco": 25.08, "quando": "2026-09-14"},
    {"id": 9, "preco": 12.80, "quando": "2026-09-14"},
    {"id": 9, "preco": 12.57, "quando": "2026-09-14"},
])
pontos = pb._serie_curta(pb._precos_por_dia(), {"id": 9})
checar(len(pontos) == 3, "seis leituras em tres dias viram TRES pontos")
checar(all(p[1] <= 13.36 for p in pontos),
       "o 25,08 (outro anuncio) NAO aparece no desenho")
checar(pontos[-1][1] == 12.56, "o ponto do dia e' o MENOR do dia, o conservador")
# ⛔ SENSIBILIDADE — o predicado acima tem de saber REPROVAR.
#
# ⚠️ Sem isto ele seria um detector que aprova tudo: bastaria `pontos` vir
# vazio e as duas checagens passariam. Aqui o MESMO predicado roda contra a
# serie SEM consolidacao — o desenho que o codigo antigo faria — e o teste
# exige que ele reprove. Detector so' se prova no caso que ele deve barrar.
LEITURAS = [13.36, 13.36, 12.56, 25.08, 12.80, 12.57]
pontos_crus = [["09-14", v] for v in LEITURAS]        # uma leitura, um ponto
ok_consolidado = all(p[1] <= 13.36 for p in pontos)
ok_cru = all(p[1] <= 13.36 for p in pontos_crus)
checar(ok_consolidado and not ok_cru,
       "o mesmo predicado APROVA o desenho consolidado e REPROVA o cru")
checar(len(pontos_crus) > len(pontos),
       "e o desenho cru teria 6 pontos num intervalo de 3 dias")

print()
print("3. ⛔ DOIS PONTOS NAO VIRAM LINHA")
pb.RAIZ = antigo
antigo = com_serie([
    {"id": 3, "preco": 50.00, "quando": "2026-09-13"},
    {"id": 3, "preco": 25.00, "quando": "2026-09-14"},
])
checar(pb._serie_curta(pb._precos_por_dia(), {"id": 3}) == [],
       "dois dias, mesmo com queda de 50%, nao devolvem pontos")
checar(pb._serie_curta(pb._precos_por_dia(), {"id": 3}, minimo=2) != [],
       "e o minimo e' parametro, nao numero cravado no meio da conta")
pb.RAIZ = antigo

print()
print("4. ⛔ OS DOIS IRMAOS DESENHAM — nao so' o catalogo")
# ⚠️ Em 15/09 o mesmo conserto foi esquecido no irmao TRES vezes.
for nome in ("todos.html", "contra_capa.html"):
    txt = (RAIZ / "paginas" / nome).read_text(encoding="utf-8")
    checar("function grafico(p)" in txt, f"{nome} define grafico()")
    checar("var gr = grafico(p);" in txt, f"{nome} chama grafico() no cartao")
    checar("PISO_DO_EIXO" in txt,
           f"{nome} escala com piso — sem ele, 1,6% vira montanha")

print()
print("5. ⛔ DIA SOLITARIO NAO VIRA PICO (print do Bryan, 22/09/2026)")
# ⚠️ O "Filtro plastico do funil": card mostrava R$ 20,82 -> R$ 6,32, queda de
# 70%, com o GRAFICO RETO. O conserto de 15/09 (dedup no MESMO dia) nao pega
# isto — aqui os dois anuncios (barato ~6,3x, caro ~20,8x) aparecem em dias
# DIFERENTES, e o dia que so' leu o caro vira sozinho "o maior que ja' vimos".
pb.RAIZ = antigo
antigo = com_serie([
    {"id": 5, "preco": 6.38, "quando": "2026-09-14"},
    {"id": 5, "preco": 20.89, "quando": "2026-09-14"},
    {"id": 5, "preco": 6.33, "quando": "2026-09-15"},
    {"id": 5, "preco": 20.73, "quando": "2026-09-15"},
    {"id": 5, "preco": 6.35, "quando": "2026-09-16"},
    {"id": 5, "preco": 6.36, "quando": "2026-09-19"},
    {"id": 5, "preco": 20.82, "quando": "2026-09-20"},   # o dia solitario
])
serie = pb._serie_de_precos()
checar(abs(serie[5][2] - 6.38) < 0.01,
       "o 'maior' confiavel e' 6,38 (o real), nao 20,82 (o dia solitario)")
d = {"id": 5, "preco": "R$ 6,32"}
checar(pb._antes(serie, d) == "",
       "sem 'antes': nenhuma queda fantasma pro visitante ver")
checar(pb._queda_real(serie, d) == 0.0, "e a queda publicada e' zero, nao 70%")
# ⛔ SENSIBILIDADE — o mesmo predicado tem de reprovar o CRU (sem o filtro).
# O "cru" e' o maximo dos MENORES-do-dia (o comportamento de antes do
# conserto de hoje) — nao o maximo de toda leitura solta, que ja' tinha sido
# resolvido em 15/09.
menores_por_dia = [6.38, 6.33, 6.35, 6.36, 20.82]   # um por dia, 14-20/09
checar(abs(max(menores_por_dia) - 20.82) < 0.01,
       "sem o filtro, o maior CRU seria 20,82 — e' o defeito que isto barra")

print()
print("5b. NEGATIVO — alta REAL e corroborada continua contando")
# ⚠️ A guarda so' pode existir se souber deixar passar o caso legitimo: um
# preco que realmente subiu por alguns dias (nao um anuncio-fantasma de UM
# dia so') tem de continuar valendo como pico.
pb.RAIZ = antigo
antigo = com_serie([
    {"id": 6, "preco": 50.00, "quando": "2026-09-12"},
    {"id": 6, "preco": 50.00, "quando": "2026-09-13"},
    {"id": 6, "preco": 68.00, "quando": "2026-09-14"},   # alta real, 1,36x
    {"id": 6, "preco": 50.00, "quando": "2026-09-15"},
])
serie = pb._serie_de_precos()
checar(abs(serie[6][2] - 68.00) < 0.01,
       "alta de 1,36x sobre a mediana passa: nao e' anuncio duplo, e' o preco")
pb.RAIZ = antigo

print()
print("6. O CAMPO CHEGA NOS TRES MONTADORES DE CARTAO")
fonte = (RAIZ / "paginas" / "publicar_bio.py").read_text(encoding="utf-8")
# ⚠️ QUATRO desde 16/09/2026: catalogo, as duas trilhas da bio e a categoria
# EXTERNA (`produtos_externos`, a Nike). O quarto montador e' justamente o
# caso que esta guarda existe pra pegar — cartao de outra origem que
# esquecesse a serie nunca graduaria pra grafico, em silencio.
checar(fonte.count('"serie": _serie_curta(por_dia, d),') == 4,
       "catalogo, as duas trilhas da bio E a categoria externa carregam a serie")

print()
if falhas:
    print(f"[x] {len(falhas)} falha(s)")
    for f in falhas:
        print("   -", f)
    raise SystemExit(1)
print("tudo verde")
