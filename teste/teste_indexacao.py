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


print("1. INDICE ESTATICO: escapa HTML, link sponsored, preco e loja")
h = pb.indice_estatico([{"nome": "Cabo <USB> & tal", "preco": "R$ 9,90",
                         "link": "https://x.y/?a=1&b=2", "loja": "AliExpress"}])
checar('rel="sponsored nofollow"' in h, "link de afiliado declarado ao Google")
checar("Cabo &lt;USB&gt; &amp; tal" in h and 'href="https://x.y/?a=1&amp;b=2"' in h,
       "nome e link escapados")
checar("R$ 9,90" in h and "AliExpress" in h, "preco e loja no texto")

print()
print("2. SEM LINK, FORA")
h = pb.indice_estatico([{"nome": "Sem link", "preco": "R$ 1,00", "link": ""}])
checar("<li>" not in h, "produto sem link nao vira item")

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
