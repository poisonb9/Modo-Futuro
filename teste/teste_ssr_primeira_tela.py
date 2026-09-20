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
print("7. O TOPO (BRASAO E LINHA VIVA) TAMBEM VEM PRE-MONTADO")
# ⭐ 20/09: o video do Bryan (02:24) mostrou a primeira pintura CORRETA mas
# com dois buracos no cabecalho — logo e linha viva, ambos escritos pelo
# motor, que agora chega em `defer`. Sem estes, a piscada volta.
checar('<span class="marca-logo" id="logo"></span>' in html,
       "antes: logo vazio no HTML")
checar('<span class="marca-logo" id="logo"></span>' not in saida
       and 'decoding="sync"' in saida,
       "depois: brasao dentro do HTML, com decoding=sync")
checar('<span class="vivo-nome" id="vivo_nome"></span>' in html,
       "antes: linha viva vazia no HTML")
m_vivo = re.search(r'<span class="vivo-nome[^"]*" id="vivo_nome">(.+?)</span>', saida)
checar(bool(m_vivo and m_vivo.group(1).strip()),
       f"depois: nome do produto do topo no HTML ({(m_vivo.group(1)[:34] + '...') if m_vivo else 'vazio'})")
m_preco = re.search(r'<span class="vivo-preco[^"]*" id="vivo_preco">(.+?)</span>', saida, re.S)
checar(bool(m_preco and "R$" in m_preco.group(1)), "depois: preco do topo no HTML")

print()
print("8. NEGATIVO: `data-mede` NAO PODE VIAJAR NO HTML")
# ⛔ `animarVivo` usa `data-mede` como "ja' liguei o clique aqui". Congelado
# no HTML, o motor pula a linha e o clique no produto do topo — o mais
# visivel da pagina — deixa de ser medido. Nao aparece na tela: so' este
# teste pega. O caso positivo (o atributo existe depois do JS) esta' provado
# pela propria pagina; aqui se prova que ele NAO chegou ao byte servido.
i_vivo = saida.find('<a class="vivo" id="vivo"')
abre = saida[i_vivo:saida.find(">", i_vivo) + 1] if i_vivo >= 0 else ""
checar(i_vivo >= 0, "o <a class=vivo> continua no HTML")
checar("data-mede" not in abre, f"sem data-mede no <a> servido ({abre[:70]})")
checar('if (!alvo.dataset.mede)' in pagina,
       "e a pagina REALMENTE usa data-mede como trava (senao este teste nao guarda nada)")

print()
print("tudo verde" if not FALHAS else f"{FALHAS} FALHA(S)")
sys.exit(1 if FALHAS else 0)
