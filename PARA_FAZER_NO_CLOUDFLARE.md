# Para fazer na Cloudflare (só o Bryan) — 18/09/2026

Tudo aqui é clique no painel: meu token é só de Pages, não escreve DNS nem regra.
Do meu lado **já está feito**: os 5 subdomínios estão registrados nos projetos Pages
(ficam "pending" até o CNAME existir) e o site mãe já responde no domínio.

Login: dash.cloudflare.com com **Bryanaw21212@gmail.com** → domínio **achadinhototal.com.br**.

## 1. DNS → Records → "Add record" — 5 vezes (subdomínios dos canais)

Sempre: Type **CNAME** · Proxy **ligado** (nuvem laranja) · TTL Auto · Save.

| Name | Target |
|---|---|
| `make` | `oachadinho.pages.dev` |
| `chef` | `achadinhochef.pages.dev` |
| `pagomenos` | `pagomenos.pages.dev` |
| `hoje` | `achadinhodehoje.pages.dev` |
| `livro` | `meulivro.pages.dev` |

Resultado: `make.achadinhototal.com.br` abre a bio do Achadinho Make, etc. Os `.pages.dev`
continuam funcionando — nada quebra enquanto isso. Certificado sai sozinho em 1–2 min.

## 2. Rules → Redirect Rules → "Create rule" → template **"Redirect from WWW to root"**
Só clicar em "Deploy". Hoje o `www` funciona por um JS na página; a regra dá o 301 de verdade.

## 3. (Opcional, 1 min) API token com DNS
My Profile → API Tokens → Create Token → template **"Edit zone DNS"** → Zone Resources:
Include → Specific zone → achadinhototal.com.br → Continue → Create → me manda o token.
Com ele eu faço os itens 1 e 2 sozinho da próxima vez (guardo como `CF_DNS_TOKEN` no `.env`).

## Fora da Cloudflare, na mesma sentada
- **Search Console** → Sitemaps: remover a entrada `https://achadinhototal.com.br/` (a raiz,
  que deu "está em HTML") e enviar **`sitemap.xml`**.
- **GitHub → Modo-Futuro → Settings → Secrets**: adicionar `AWIN_TOKEN` e
  `AWIN_PUBLISHER_ID` (mesmos do `.env`) — sem eles a nuvem lê as comissões da reserva.

## Depois que fizer o item 1, o que EU faço
1. Confiro os 5 subdomínios no ar (`curl`) e a marca de cada bio.
2. Troco o link da bio no TikTok? **Não** — isso é seu (app do TikTok, um por canal):
   `make.achadinhototal.com.br`, `chef.…`, `pagomenos.…`, `hoje.…`, `livro.…`
3. `conferir_no_ar` passa a conferir domínio e `.pages.dev`.
4. `?de=bio.<canal>` já está nos botões da bio — os cliques passam a dizer de qual canal vieram.
