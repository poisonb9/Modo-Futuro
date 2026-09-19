# -*- coding: utf-8 -*-
"""O que o Google ve' do site mae — e o que NAO ve'. Sem rede.

## POR QUE EXISTE (17/09/2026)

Dominio proprio comprado (achadinhototal.com.br); a fase e' marketing. A
pagina e' montada por JS, e o crawler precisa de: canonical no dominio (a
mesma pagina responde no pages.dev), um indice estatico com nome/preco/link,
robots.txt apontando o sitemap, e www -> raiz.

⭐ Casos: (1) o indice estatico escapa HTML e marca o link como sponsored;
(2) produto sem link fica FORA; (3) ⛔ NEGATIVO — as lojas externas (Nike,
Kabum...) nao entram no indice: "so' o ouro do ouro" (Bryan, 17/09);
(4) robots e sitemap apontam pro dominio, nunca pro pages.dev; (5) o
`_redirects` manda www pro raiz e NAO toca no pages.dev (e' onde a marca e'
conferida); (6) a pagina fonte tem canonical e o marcador que o publicador
preenche.
"""
import sys
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


print("1. INDICE ESTATICO: escapa HTML, aponta pra PROPRIA pagina (?p=id), preco e loja")
# 19/09/2026: o link de afiliado (1 KB, nofollow) saiu do indice — pesava
# 155 KB e nao servia ao Google. O item aponta pra pagina com o produto em 1o.
h = pb.indice_estatico([{"nome": "Cabo <USB> & tal", "preco": "R$ 9,90", "id": "10<0>1",
                         "link": "https://x.y/?a=1&b=2", "loja": "AliExpress"}])
checar('href="?p=10&lt;0&gt;1"' in h, "href e' ?p=<id>, escapado")
checar("s.click" not in h and "https://x.y" not in h, "NEGATIVO: o link de afiliado nao esta' no indice")
checar("Cabo &lt;USB&gt; &amp; tal" in h, "nome escapado")
checar("R$ 9,90" in h and "AliExpress" in h, "preco e loja no texto")

print()
print("2. SEM ID, FORA")
h = pb.indice_estatico([{"nome": "Sem id", "preco": "R$ 1,00", "link": "https://x.y"}])
checar("<li>" not in h, "produto sem id nao vira item")

print()
print("2b. LINKS FORA DO HTML: primeira tela fica, o resto vai pro links.json")
L = "https://s.click.aliexpress.com/s/" + "x" * 1000
dados = ([{"id": "t%d" % i, "topo": i, "link": L} for i in range(1, 11)]
         + [{"id": "v", "vitrine": True, "link": L}]
         + [{"id": "r%d" % i, "link": L} for i in range(1, 6)]
         + [{"id": "semlink"}])
fora = pb.separar_links(dados)
fica = [p["id"] for p in dados if p.get("link")]
checar(set(fica) == {"t%d" % i for i in range(1, 11)} | {"v", "r1", "r2"},
       "ficam com link: 10 do topo + vitrine + %d seguintes" % pb.LINKS_EMBUTIDOS_EXTRA)
checar(set(fora) == {"r3", "r4", "r5"} and all(v == L for v in fora.values()),
       "os outros saem, com o link inteiro, por id")
checar("semlink" not in fora and "link" not in dados[-1], "NEGATIVO: sem link nao entra no arquivo")
checar(pb.LINKS_ARQUIVO == "links.json", "o arquivo e' links.json (a pagina le' LINKS_ARQUIVO)")
pagina = (RAIZ / "paginas" / "todos.html").read_text(encoding="utf-8")
checar('var LINKS_ARQUIVO = "";' in pagina and "function carregarLinks" in pagina
       and 'a.vitrine[data-pid]' in pagina,
       "a pagina tem o marcador, o carregador e encaixa o href no cartao E na vitrine")

print()
print("3. ⛔ NEGATIVO: o indice recebe o CATALOGO (produtos_todos), nunca as lojas externas")
src = (RAIZ / "paginas" / "publicar_bio.py").read_text(encoding="utf-8")
checar("indice_estatico(dados)" in src and "indice_estatico(catalogo_awin" not in src
       and "indice_estatico(externos" not in src,
       "a chamada e' com `dados` (produtos_todos); Nike/Kabum ficam fora")

print()
print("4. ROBOTS E SITEMAP NO DOMINIO")
r = pb.robots_txt()
checar("Sitemap: https://achadinhototal.com.br/sitemap.xml" in r and "Disallow" not in r,
       "robots: tudo liberado, sitemap no dominio")
sm = pb.sitemap_xml(["/", "/parceiros"])
checar("<loc>https://achadinhototal.com.br/</loc>" in sm and "pages.dev" not in sm,
       "sitemap no dominio, sem pages.dev")

print()
print("5. REDIRECT: www -> raiz, e o pages.dev fica em paz")
checar(pb.REDIRECTS.startswith("https://www.achadinhototal.com.br/* https://achadinhototal.com.br/:splat 301"),
       "www -> raiz, 301")
checar("pages.dev" not in pb.REDIRECTS, "pages.dev NAO redireciona (conferir_no_ar le' a marca la')")

print()
print("6. A PAGINA FONTE")
html = (RAIZ / "paginas" / "todos.html").read_text(encoding="utf-8")
checar('<link rel="canonical" href="https://achadinhototal.com.br/">' in html, "canonical no dominio")
checar(html.count('<section id="indice-estatico" aria-hidden="true"></section>') == 1,
       "um marcador vazio, que o publicador preenche")
checar('getElementById("indice-estatico")' in html, "o script remove o indice quando a grade desenha")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
