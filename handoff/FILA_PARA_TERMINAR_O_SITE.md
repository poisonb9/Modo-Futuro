# Fila para terminar o site — anotada em 20/09/2026

Anotada a pedido do Bryan ("anote todas as sugestoes"), para nao se perder
enquanto a sessao segue no que ele quer mexer agora.

## O QUE SO' O BRYAN FAZ (trava o resto)

1. **Cloudflare — 5 CNAMEs dos subdominios** (`make`, `chef`, `pagomenos`,
   `hoje`, `livro`). Detalhe em `PARA_FAZER_NO_CLOUDFLARE.md`.
2. **Cloudflare — Redirect Rule www -> raiz.** Hoje o `www` funciona por JS.
3. **Awin — colar Site e URL do Blog no perfil.** ⛔ O mais urgente da lista:
   ha' ~20 pedidos sendo julgados, e cada avaliador abre o endereco que
   estiver no cadastro no instante da avaliacao.
4. **Search Console** — remover a entrada da raiz e enviar `sitemap.xml`.
5. **GitHub Secrets** — `AWIN_TOKEN` e `AWIN_PUBLISHER_ID`.
6. Reclame Aqui · BotFather · foto do quem-somos (falta o arquivo).

## O QUE EU FACO SOZINHO

7. **Termometro R$ 16,90** na vitrine.
8. **SEO / metadados** da vitrine (o que sobrou depois do sitemap).
9. **Medir quantos dos 148 titulos estao feios** — decide se o
   `engine/titulo_vendavel.py` (pronto, medido e DESACONSELHADO: 7 de 10
   voltaram identicos) chega a valer.
10. **Funil**: 193 visitas em 7 dias, 0 vendas. O site esta' aprovado no
    desenho; o buraco medido e' conversao, nao estetica.

## 🔴 DEFEITO MEDIDO EM 20/09 (suite)

`teste/teste_vitrine_produtos_reais.py:101` quebra com `KeyError: '_todos'`.
Os outros 7 testes do site passam. Nao foi investigado ainda — anotado aqui
para nao virar surpresa na proxima publicacao.
