"""SSR da primeira tela (20/09/2026): o publicador roda o script da pagina num
DOM de mentira (ferramentas/ssr/ssr.js) e cola prova, chips, vitrine e os
primeiros cartoes no HTML. Aqui se prova que:

1. o harness monta a primeira tela a partir do HTML real do catalogo;
2. os numeros da prova sao os FINAIS (nao o meio da contagem de 700 ms);
3. a copia e' inerte e parseavel: sem <a> dentro de <a>, sem <canvas>;
4. NEGATIVO: entrada sem #grade -> exit 1 e nada no stdout;
5. o publicador chama o SSR ANTES do carimbo, e cai com aviso sem node/jsdom;
6. a pagina nao conta os numeros de 0 quando a prova ja' veio montada.
"""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
sys.argv = ["x"]
import publicar_bio as pb  # noqa: E402

FALHAS = 0


def checar(ok, msg):
    global FALHAS
    print(("  ok   " if ok else "  [x]  ") + msg)
    if not ok:
        FALHAS += 1


print("1. O HARNESS MONTA A PRIMEIRA TELA DO HTML REAL")
html, _ = pb.montar_catalogo()
checar('<div class="grade" id="grade"></div>' in html, "antes: grade vazia no HTML")
saida = pb.ssr_primeira_tela(html)
checar(saida != html and len(saida) > len(html), "depois: o HTML cresceu (primeira tela dentro)")
grade = re.search(r'<div class="grade" id="grade">(.*?)</div>\s*<!-- 20/09', saida, re.S)
cartoes = len(re.findall(r'<a class="item"', saida.split('id="grade">', 1)[1][:200000]))
checar(cartoes >= 8, f"pelo menos 8 cartoes na grade pre-montada ({cartoes})")
checar('id="chips"><div class="fila-chips">' in saida, "chips montados")
checar('id="vitrine"><a class="vitrine"' in saida, "vitrine montada")

print()
print("2. OS NUMEROS DA PROVA SAO OS FINAIS")
ns = re.findall(r'<strong class="n">([^<]*)</strong>', saida)[:3]
dados = pb.produtos_todos()
ext = pb.produtos_externos()
total = len(dados) + sum(len(b["produtos"]) for b in ext.values())
checar(ns and ns[0] == f"{total:,}".replace(",", "."), f"vigiados = {ns[0] if ns else '?'} (catalogo + externas = {total})")

print()
print("3. A COPIA E' INERTE E PARSEAVEL")
bloco = saida.split('id="vitrine">', 1)[1].split("<!-- 20/09", 1)[0]
checar("<canvas" not in bloco, "sem <canvas> na copia")
aninhado = re.search(r'<a [^>]*>(?:(?!</a>).)*<a ', bloco, re.S)
checar(aninhado is None, "sem <a> dentro de <a> (o parser partiria o cartao)")

print()
print("4. NEGATIVO: entrada sem #grade -> exit 1, stdout vazio")
r = subprocess.run(["node", str(pb.SSR)], input=b"<html><body>nada</body></html>",
                   capture_output=True, timeout=60)
checar(r.returncode == 1 and not r.stdout, f"exit {r.returncode}, stdout {len(r.stdout)} B")

print()
print("5. O PUBLICADOR CHAMA O SSR ANTES DO CARIMBO, E CAI COM AVISO SEM NODE")
src = (RAIZ / "paginas" / "publicar_bio.py").read_text(encoding="utf-8")
i_ssr = src.index("catalogo = ssr_primeira_tela(catalogo)")
i_car = src.index("catalogo, marca_c = _carimbar(catalogo)")
checar(i_ssr < i_car, "ssr_primeira_tela vem antes de _carimbar (o carimbo e' do byte servido)")
checar("publicando sem a primeira tela" in src and "SEM node/jsdom" in src,
       "sem node/jsdom ou com falha: publica e avisa (preco na hora > primeira tela)")
checar(pb.ssr_primeira_tela("") == "", "html vazio passa reto")

print()
print("6. A PAGINA NAO CONTA DE 0 QUANDO A PROVA JA' VEIO MONTADA")
pagina = (RAIZ / "paginas" / "todos.html").read_text(encoding="utf-8")
checar('PROVA_PRE_MONTADA = !!caixa.querySelector(".cela")' in pagina
       and "if (PROVA_PRE_MONTADA) { return; }" in pagina,
       "montarProva marca e contarNumeros respeita")
checar('caixa.querySelectorAll(".cela, .fim").forEach' in pagina, "montarProva limpa as celas pre-montadas (sem duplicar)")
checar("/[?&]p=/.test(location.search) || location.hash.length > 1" in pagina,
       "?p= e #categoria limpam a grade pre-montada (ordem diferente da abertura)")

print()
print("tudo verde" if not FALHAS else f"{FALHAS} FALHA(S)")
sys.exit(1 if FALHAS else 0)
