# PLANO DO SITE QUE VENDE — achadinhototal.com.br (iniciado 05/10/2026)

> Documento-mestre. Tudo que descobrimos e o que estamos construindo para o site virar máquina de vendas.
> Regra: cada item entra aqui ANTES de ser feito e é marcado quando estiver no ar e conferido.
> Detalhe técnico de cada mudança (sintoma → causa → correção) vai no REGISTRO do dia.
> Aprovado pelo dono em 05/10: "concordo com tudo... vamos fazer isso com excelência".

---

## 0. Diagnóstico (medido em 05/10/2026, ~19 h)

| medida | valor | leitura |
|---|---|---|
| páginas no ar | `/`, `/cupons/`, `/top10/` (+8 nichos), `/parceiros/`, `/privacidade` | todas 200, 0,09–0,33 s |
| **cliques em produto, 30 dias** | **45** (23 de 148 produtos receberam algum clique) | o gargalo é TRÁFEGO, não a página |
| **sitemap.xml** | **2 endereços** (`/` e `/parceiros`) | Google não sabia de /cupons/, /top10/ e nichos |
| vitrine principal | **145 de 148 = AliExpress** | ML e as 15 lojas quase invisíveis na 1ª tela |
| catálogo total | 69.734 produtos, 17 lojas; ~128 mil ids com preço acompanhado desde 12/09 | ativo enorme e sem página indexável |
| cupons | 112 ativos, atualizados de hora em hora | só 1 página (/cupons/), sem página por loja |

**Conclusão:** a máquina de preço é boa; quase ninguém chega. Prioridade = Google (tráfego que não paga anúncio) + lista
(quem veio uma vez volta). Sem isso, melhorar a vitrine mexe em cima de 45 cliques/mês.

---

## 1. O que o acervo diz (fichas consultadas em 05/10, busca semântica + rerank-2.5)

- **Afiliado que vende:** conteúdo que mostra o produto antes do link; **página-ponte** (bridge page) entre o vídeo e a loja,
  com bônus/conteúdo extra e captura de contato; oferta simples (poucos bullets) e teste A/B com tráfego real.
- **Captura de contato:** padrão das lojas que faturam alto — pop-up/faixa oferecendo **cupom ou desconto em troca de e-mail/telefone**,
  com gatilho de tempo (ex.: 5 s), rolagem ou intenção de saída. Lista serve para remarketing e para voltar a vender.
- **SEO de afiliado:** páginas que respondem a buscas (review, ranking, "melhores X"), **tabelas de comparação** com os itens mais
  avaliados do ML, guia passo a passo com links no início para temas de alta intenção de compra.
- **Indexação:** Google Search Console → verificar a propriedade (tag HTML ou DNS) → enviar o sitemap → "Inspeção de URL → Solicitar
  indexação" nas páginas novas.
- **⛔ Risco:** "scaled content abuse" — milhares de páginas autogeradas SEM conteúdo único são punidas (doorway pages / thin content).
  Nossa defesa: cada página tem DADO PRÓPRIO que ninguém tem (histórico real de preço, menor preço em N dias, cupom conferido na hora).
  Página sem dado próprio suficiente NÃO é gerada (ou recebe `noindex`).
- **Prova social:** para público frio, números concretos, avaliações e selos de confiança perto da oferta.
- **Ticket/recorrência:** kits "compre junto", alerta de recompra, fidelidade.

---

## 2. Frentes (ordem aprovada) — estado

| # | frente | o que é | estado |
|---|---|---|---|
| 1a | **Sitemap completo** | `/`, `/cupons/`, `/top10/` + 8 nichos, `/parceiros`, `/privacidade` (11 endereços) | ✅ código 05/10 (`publicar_bio.py`, `TOP10_NICHOS_MAPA`); vai no ar na próxima publicação |
| 1b | **Google Search Console** | verificar domínio, enviar sitemap, pedir indexação | ⏳ precisa do DONO (login Google) — passo a passo na seção 3 |
| 1c | **Páginas de cupom por loja** `/cupons/<loja>/` | 1 por loja COM cupom ativo (hoje 14); título "Cupom <Loja> hoje: N cupons conferidos (mês)", canonical, BreadcrumbList, links internos "Cupons por loja" | ✅ código 05/10 (`engine/cupons.py` `pagina_html(slug)`, `lojas()`); no sitemap |
| 1d | **Página por produto rastreado** `/p/<slug>/` | histórico de preço, menor em 60 dias, cupom da loja, alerta | ⏳ a construir (começar pelos ~500 com mais série) |
| 1e | **"Melhores X até R$ Y"** | listas por nicho/faixa a partir do Top 10 + série de preço | ⏳ a construir |
| 2 | **"Receba os cupons da [loja] antes de todo mundo"** | bloco VIP preto/ouro em /cupons/ e em cada /cupons/<loja>/: botão Telegram (`/start alerta_cupons-<loja>`) + e-mail (Supabase `contato`, origem `cupons`) | ✅ código 05/10; aviso automático de cupom novo no Telegram (`engine/alertas.avisar_cupons`, de hora em hora no precos.yml) |
| 3 | **Mercado Livre na vitrine** | 8 mais vendidos do ML intercalados (1 a cada 2 cartões, máx. 2 por área, sem remédio) + 4 ofertas "muito boas" no topo | ✅ código 05/10 (`misturar_ml_na_vitrine`); testado localmente |
| 4 | **Prova e confiança** | números reais (preços acompanhados, economia da semana), selo "menor em 60 dias" na 1ª dobra | ⏳ |
| 5 | **Vídeo → página-ponte** | cada vídeo de oferta leva à `/p/<produto>/` (gráfico + cupom + alerta) | ⏳ depende do 1d |
| 6 | **Black Friday** | Detector de Black Fraude + `/blackfriday` indexável até ~27/10 | ⏳ plano em CAMPANHA_BLACK_FRIDAY_2026.md |

---

## 3. Respostas às perguntas do dono (05/10)

### Como fazer o Google indexar
1. **Search Console** (search.google.com/search-console) com a conta Google do dono → "Adicionar propriedade" → **Domínio**
   `achadinhototal.com.br` → o Google dá um registro TXT → colocar no DNS da Cloudflare (Claude faz, se o dono passar o TXT).
2. Em "Sitemaps", enviar `https://achadinhototal.com.br/sitemap.xml`.
3. "Inspeção de URL" → colar `/`, `/cupons/`, `/top10/` → "Solicitar indexação". Repetir para cada página nova importante.
4. Também: Bing Webmaster Tools (importa direto do Search Console, 1 clique) — tráfego extra de graça.
5. Links de fora ajudam o Google achar e confiar: bios dos 8 canais já apontam para o site (✅), Telegram, Pinterest (futuro).

### Como fazer o sitemap completo
- Gerado pelo publicador a cada publicação (já feito para as páginas fixas). Quando houver `/p/` e `/cupons/<loja>/`, o sitemap passa a
  ser **índice de sitemaps** (`sitemap.xml` → `sitemap-produtos.xml`, `sitemap-cupons.xml`…), cada um até 50.000 endereços, com
  `lastmod` = última mudança REAL de preço (não a data de hoje em tudo — o Google desconfia de lastmod que muda sem conteúdo mudar).

### Página por produto rastreado — como e quanto custa
- **Como:** o publicador gera `/p/<slug>/` estático (HTML pronto, sem banco): nome, foto, preço de agora, **gráfico do histórico**,
  menor/maior preço que vimos, "está X% abaixo da média de 30 dias", cupom ativo da loja, botão "ver na loja", "me avise se cair",
  produtos parecidos, JSON-LD `Product` + `Offer` (preço, moeda, disponibilidade) para aparecer com preço no Google.
- **Custo:** dinheiro ≈ **zero** (Cloudflare Pages grátis aceita até 20.000 arquivos por deploy; dados já existem; sem IA por página).
  Custo real = tempo de publicação (mais arquivos) e cuidado com qualidade. Começar com **~500 produtos** com série longa;
  crescer por lotes conforme o Search Console mostrar indexação.
- **Guarda anti-punição:** só ganha página quem tem ≥ 7 dias de série e foto boa; produto que saiu de linha → página fica com aviso
  "fora de estoque, veja parecidos" (não some — link quebrado também pune).

### Páginas de cupom por loja — não vai ficar coisa demais?
- **Não, se for feito certo.** O visitante continua com UMA porta (/cupons/, com filtro). As páginas `/cupons/kabum/` existem
  sobretudo para o **Google**: "cupom kabum", "cupom nike" são buscas enormes e de quem está PRONTO para comprar. Quem chega por
  elas cai direto nos cupons daquela loja (+ produtos com queda real da loja) — menos cliques até a compra, não mais.
- Cada página: cupons ativos conferidos de hora em hora, "última conferência: hoje 14:17", cupons que expiraram (histórico = conteúdo
  único), produtos da loja com queda real, e a captura "receba os cupons da Kabum antes de todo mundo".

### "Melhores X até R$ Y"
- Sim, também para indexar e para converter (busca de alta intenção: "melhor fone bluetooth até 100 reais").
- Gerado do Top 10 + série de preço + nota/vendas do ML: tabela de comparação (acervo), "por que está aqui", preço de hoje e
  menor preço que vimos. Começar com ~20 listas nos nichos que já temos (academia, eletrônicos, beleza, casa, cozinha, pet, infantil, saúde).

---

## 4. Diário de execução
- 05/10 19 h — diagnóstico (seção 0), consulta ao acervo (seção 1), plano aprovado.
- 05/10 — sitemap completo (11 endereços) e ML intercalado na vitrine (8 itens, máx. 2 por área): código pronto e testado.
- 05/10 — lista VIP de cupons + /cupons/<loja>/ (14 lojas) + aviso de cupom novo no Telegram. Conferido na prévia (1400 px e 375 px).
- 05/10 — ACHADO: `cupons.yml` (cron :17) NUNCA rodou por agendamento (GitHub descarta cron disputado); o JSON do site estava parado
  desde 10:43. Cupons passaram para dentro do `precos.yml` (roda de hora em hora de fato).
- 05/10 — ACHADO: a Awin agora devolve promoções de PRODUTO da Kabum (160) além dos cupons → Kabum com 181 itens. Mantido
  (são ofertas reais, com link), mas avaliar separar "cupom" de "promoção de produto" na página.
- (próximo) página por produto `/p/<slug>/` (piloto com ~500) e "melhores X até R$ Y"; Search Console (depende do dono).
