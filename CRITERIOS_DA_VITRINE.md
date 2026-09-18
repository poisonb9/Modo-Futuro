# Critérios da vitrine — o que sobe pra loja, e por quê

Escrito em 17/09/2026 a partir do banco **Maestros da IA** (`ia mind/maestros_da_ia`,
3.731 fichas; 429 sobre produto/oferta/preço em 40 vídeos de e-commerce, afiliado,
FBA, dropshipping e estratégia criativa). Cada regra abaixo diz **de quem veio**,
**qual a base** (DEMONSTRADO / AFIRMADO / OPINIÃO — separação que o próprio banco faz)
e **o que já medimos** para aplicá-la. Regra sem dado nosso fica marcada como *falta*.

Objetivo declarado pelo Bryan: o melhor pro cliente, o melhor retorno pra nós, e
escalonagem de vendas. As três pontas puxam pra lados diferentes em alguns
critérios — as tensões estão na seção 4, não escondidas.

---

## 1. O que os maestros dizem sobre escolher produto

### 1.1 Demanda real, não demanda suposta

| Regra | Fonte | Base | O que temos |
|---|---|---|---|
| Ordenar por **número de pedidos**; só entra quem já vende | createaprowebsite (dropshipping), meticsmedia (fornecedor AliExpress) | DEMONSTRADO / AFIRMADO | `vendas` (`lastest_volume`) no Ali. ML não dá vendas: temos **vendedores** (piso 2). Awin: *falta* |
| Piso de volume: **≥ 5.000 pedidos e GMV > 50 k em 30 dias** (TikTok Shop) | loganskimoney | AFIRMADO | Ali: `vendas` total (não é 30 dias). Nosso `CAMPEAO_VOLUME_MIN` já existe |
| **Movers and Shakers**: o que mais subiu no rank de vendas nas últimas 24h — não quem vende muito, quem está **acelerando** | meticsmedia ($100k/mo product, Dropshipping Guide) | AFIRMADO | `_vendas_desde` = crescimento do volume medido por nós (o "+792 vendidos desde 14/09"). É exatamente isso. `garimpo --tendencia` também |
| Google Trends em alta antes de escolher | meticsmedia ×2, Affiliate Tutorial | AFIRMADO | *falta*. Substituto nosso: `busca` do Supabase (o que as pessoas procuram no site) |
| Autocomplete com intenção de compra ("best", "X vs Y", "review") | meticsmedia Affiliate Tutorial | AFIRMADO | *falta*; barato de medir |

### 1.2 Confiança: avaliação e vendedor

| Regra | Fonte | Base | O que temos |
|---|---|---|---|
| Vendedor com **feedback ≥ 90 % (ideal > 95 %)** e produto **≥ 4,5 estrelas** | meticsmedia ×2 | AFIRMADO | `nota` (evaluate_rate) no Ali — o fogo já exige ≥ 95. ML e Awin: *falta* |
| Ler as avaliações **1 estrela** para achar a objeção; 5 vs 3 vs 1 pra achar a linguagem | motioncreativeanalytics ×2 | AFIRMADO | *falta* (a API de afiliado não dá texto de review) |
| Importar só reviews **4+** pra loja | createaprowebsite ×2 | DEMONSTRADO | não importamos review; o "% positivas" cumpre o papel |
| Comece pelo **produto hero**: o que já tem confiança e validação | motion & Varos | OPINIÃO | é a vitrine (2ª posição do ML, fogo) |

### 1.3 Preço e o que rende

| Regra | Fonte | Base | O que temos |
|---|---|---|---|
| Faixa de **impulso: US$ 20–100** (na nossa moeda, ~R$ 30–150 — bate com o teto 150 do Bryan) | meticsmedia Dropshipping Guide, Jungle Scout (19–100) | AFIRMADO / DEMONSTRADO | perfil de canal `min/max`; teto 150 nas externas |
| **Margem** decide, não preço: `(venda − custo)/venda`; alvo ~25 % no FBA | meticsmedia FBA | DEMONSTRADO | nosso "custo" é zero; o análogo é **comissão × preço = ganho por venda** (`ganho_previsto`). Já existe |
| **EPC (ganho por clique)** pra escolher entre ofertas: 100 cliques × conversão × preço | Hormozi (Offers & Pricing) | DEMONSTRADO | *falta o clique por produto*. `resultado --placar` não cruza produto com pedido (e diz isso) |
| Cortar os **20 % piores** por unit economics; concentrar nos de alta margem | Hormozi (Getting Rich) | DEMONSTRADO | dá pra fazer com `ganho × vendas` (`_potencial`) hoje |
| Desligar a oferta de **LTV:CAC baixo** e mover pra de maior TAM | Hormozi | AFIRMADO | sem CAC (tráfego orgânico). O TAM é a categoria: Clovis 5.983 ≠ Exypna 4 |
| Tráfego orgânico aceita **margem menor** (não há custo de anúncio) | meticsmedia | AFIRMADO | é o nosso caso: Kabum a 0–2,3 % não é automaticamente lixo |
| Preço de comparação riscado ("de/por") na página | 6 vídeos de Shopify/Woo | DEMONSTRADO | fazemos, e melhor: contra a **nossa** série, não o "de" do vendedor |

### 1.4 Concorrência e saturação

| Regra | Fonte | Base | O que temos |
|---|---|---|---|
| **Evitar nicho dominado por uma marca** (líder com a maioria da receita) | meticsmedia FBA | OPINIÃO | *falta* medir; nas externas o feed dá `marca` |
| **Evitar saturado** (o liquidificador portátil) | meticsmedia ONE PRODUCT | OPINIÃO | *falta*. Proxy: quantos vendedores no ML (muitos = commodity, ver memória "volume significa o contrário em cada fonte") |
| Reviews ≤ 1.000 = concorrência entrável | Jungle Scout | DEMONSTRADO | *falta* |
| Espionar o que a concorrência anuncia (Meta Ad Library, TikTok Top Ads, lojas Zeke) | pauljlipsky, motion | DEMONSTRADO | *falta*; é pesquisa manual |

### 1.5 O que dá vídeo (o produto tem de ser **mostrável**)

| Regra | Fonte | Base | O que temos |
|---|---|---|---|
| Checar se o produto tem **imagens e vídeos bons pra promover** antes de importar | createaprowebsite | DEMONSTRADO | `rende_video.peneirar_com_ia` (crivo editorial) — só no ML hoje |
| "Dá pra vender isso **criativamente** em rede social?" como pergunta de corte | meticsmedia | AFIRMADO | idem |
| Teste pequeno, escale o vencedor (ROAS > 3 → +10–30 % de orçamento; troque só o gancho dos 3 s) | motion ×4 | AFIRMADO | nosso teste é o **post**: views por produto já estão em `desempenho` (e a memória diz: nota do motor **não** prevê views — 88 deu 1.822, 98 deu 584). O dado existe; falta ligá-lo na vitrine |
| Sazonalidade: lista mensal (abril = jardim, dezembro = presente) e **planilha dos vencedores** pra reaproveitar | pauljlipsky | DEMONSTRADO / AFIRMADO | a série de preços É essa planilha. Falta o carimbo de estação |

### 1.6 Escassez e oferta (o que faz clicar)

| Regra | Fonte | Base | O que temos |
|---|---|---|---|
| Escassez real: **1–2 unidades** | pauljlipsky | AFIRMADO | não temos estoque; nosso análogo honesto é o "última chance" da série (`engine/sinais.py`) |
| Hook → problema → solução → prova social → oferta irresistível | loganskimoney | AFIRMADO | linha de sinais do cartão = prova social; Promo = oferta |
| Oferta que cabe em **uma mensagem de texto** | Hormozi | AFIRMADO | o post de sinal no Telegram |
| Bundle/upsell na página sobe o ticket | motion, Atlas | DEMONSTRADO | `combina` (vai bem com) já existe |

---

## 2. Tradução pra **nossa** régua: a Nota de Vitrine

Tudo acima colapsa em quatro eixos. Cada eixo com o que **já medimos** e o peso
proposto. Nota 0–100; entra na vitrine quem passa o piso; a ordem é a nota.

```
VITRINE = 35·Rende + 30·Confiança + 20·Momento + 15·Mostrável
```

**Rende (35)** — o melhor pra nós. Acima de R$ 150 (faixa de impulso) vale ×0,7.
`ganho_por_venda = preço × comissão`. Normalizado por loja (a régua do Kabum a 2 %
não é a do Ali a 9 %). Fonte: Hormozi (margem, EPC), FBA (margem), meticsmedia
(orgânico aceita margem menor → por isso é 35 e não 50).

**Confiança (30)** — o melhor pro cliente. (Ali: 60 % nota + 40 % volume de vendas — medido em 17/09: sem o volume o topo virava "os mais caros".)
Ali: `nota ≥ 95 %` = cheio; 90–95 = metade; < 90 = zero (meticsmedia: ≥ 90, ideal > 95).
ML: `vendedores ≥ 5` = cheio; 2–4 = metade (piso 2 já é regra do `buscar`).
Awin: **zero por enquanto** — o feed não traz avaliação. É o eixo que a Nike/Clovis
não conseguem pontuar, e é o motivo honesto de elas não abrirem a página.

**Momento (20)** — Movers and Shakers.
`+N vendidos desde dd/mm` (Ali) ou `+N vendedores desde` (ML), e `queda` medida por
nós. Um produto que cai de preço **e** vende mais é o sinal mais forte que o banco
descreve (garimpo: "queda com volume subindo é oportunidade; com volume caindo é
produto morrendo"). Awin pontua aqui a partir do dia 3 da série.

**Mostrável (15)** — dá vídeo.
`rende_video.peneirar_com_ia` (crivo editorial) + **views do post** quando houver
(`desempenho`). Produto que já rendeu um post com views acima da mediana do canal
ganha o eixo inteiro; é o "escale o vencedor" da motion aplicado ao nosso teste real.

**Pisos (fora da vitrine, mas NUNCA fora da série):**
- preço fora do perfil do canal;
- `nota < 90 %` no Ali;
- `vendedores < 2` no ML;
- salto de variante (esgotado) — já existe;
- preço não reconferido em 24 h — já existe.

**Furador de fila:** termo com busca no site (`busca` do Supabase) e produto que
o atende → topo, independente da nota. É a demanda mais real que temos: alguém
digitou.

**Corte de Hormozi:** todo dia, os 20 % piores em `Rende × Momento` saem da
vitrine (não da loja, não da série).

---

## 3. O que isso muda no site, na prática

| Hoje | Com a régua |
|---|---|
| Externa abre pelos **mais baratos** (meia-calça R$ 14,99) | Externa abre por **Rende × Momento**; sem série ainda, por Rende. Meia-calça de 1 % cai pra baixo |
| Fogo = nota ≥ 95, queda ≥ 15, vendas ≥ 1.000, rende ≥ R$ 3 | Fogo = top 6 da Nota de Vitrine com Confiança cheia. Mesma ideia, uma régua só |
| ML na 2ª posição por `vendedores × ganho` | Mesma coisa, agora dentro da nota |
| Kabum: "fica?" pela comissão | Kabum fica **na loja** (dado), pontua baixo em Rende, alto em Mostrável (eletrônico dá vídeo) — a régua responde sem decisão manual |
| Vitrine ignora as views dos posts | Views entram em Mostrável — o que já provou no TikTok sobe no site |

---

## 4. Tensões (o que a régua NÃO resolve sozinha)

1. **Cliente × nós.** O mais barato pro cliente (Ali a R$ 9) rende R$ 0,80. A régua
   dá 35 pra Rende e 30 pra Confiança de propósito: quase empate. Se o Bryan
   quiser "cliente primeiro", inverte-se pra 30/35 — é um número, não uma reforma.
2. **Awin sem confiança.** Nike/Clovis não têm avaliação no feed. Ou aceitamos
   que a marca é a confiança (Nike = nota cheia por decreto), ou elas nunca
   pontuam o eixo. Proposta: **marca conhecida = metade do eixo**; o resto
   fica com quem tem review. Decisão do Bryan.
3. **Momento precisa de dias.** Hoje as externas têm 1 dia de série. A régua
   fica cega nesse eixo até 19/09 — e é certo que fique: momento inventado é o
   "de/por" da loja.
4. **Mostrável é caro.** O crivo por modelo custa cota; 26 k produtos não passam.
   Só passa quem já tem Rende × Confiança acima do piso — o funil vem antes do juiz.
5. **EPC de verdade exige clique por produto.** Nem Ali nem ML nem Awin nos dão
   isso por link sem um tracking por produto. É o dado que transformaria a régua
   de "estimada" em "medida". Fica em PERGUNTAS_ABERTAS.

---

## 5. Ordem de implementação (cada passo com medição)

1. `engine/vitrine.py`: `nota(p) -> (total, eixos)` com os quatro eixos sobre os
   campos que **já existem** (`ganho`, `nota`, `vendedores`, `vendeu`, `queda`).
   Guarda: caso negativo teoremático (Awin sem nota pontua 0 em Confiança).
2. `publicar_bio.produtos_todos` e `produtos_externos` carregam `vitrine` (a nota)
   no cartão; a página ordena por ela quando o filtro é "tudo". Medir: quantos
   cartões mudam de posição no topo; conferir os 8 do topo à mão.
3. Fogo e `marcar_vitrine_ml` passam a ler a nota (uma régua só).
4. Views do `desempenho` entram em Mostrável (cruzamento por `id` do produto
   no registro de publicados).
5. Corte de 20 % diário e furador de fila da `busca`.
6. Marca-como-confiança nas externas — **só depois da decisão do Bryan** (tensão 2).

Nada aqui muda a coleta: a série continua recebendo tudo (ordem de 17/09).

---

## 6. Régua v2 — parâmetros refinados (17/09/2026, 2ª investigação)

Segunda passada no banco: 3.960 fichas com atributo de produto, e a fonte que faltava —
**Ecommerce na Prática (Bruno de Oliveira), 211 vídeos, mercado brasileiro/Mercado Livre**.
O que muda de v1 → v2 é que cada parâmetro abaixo tem **dado medido** (conferido na API em
17/09) e não só intuição. Base entre colchetes.

### 6.1 O que os brasileiros acrescentam (ENP = Ecommerce na Prática)

| Parâmetro | Regra | Fonte | Dado que temos / conferido |
|---|---|---|---|
| **Demanda por categoria** | "Tendências do ML": os 40 termos mais buscados **por categoria e subcategoria** — nunca a tela inicial, que é genérica | ENP ×6 [DEM] | `GET /trends/MLB/{categoria}` responde (ex.: "cadeira gamer", "creatina growth", "bolsa térmica"). Produto cujo nome casa com termo em alta ganha Momento; e os termos viram pauta do garimpo do ML |
| **Curva B** | Produto com muitos anunciantes = guerra de preço e margem zero; preferir "curva B" (menos concorrentes) | ENP [AFI] + memória "muito vendido no ML = commodity" | `vendedores` do ML: ≥ 5 confiança cheia, **> 30 = commodity, ×0,8** |
| **Reputação do vendedor** | "termômetro" do vendedor decide confiança e ranqueamento | ENP ×3 [AFI] | `GET /users/{seller_id}` → `level_id 5_green`, `power_seller_status silver`. **Confiança do ML medida**, não só contagem |
| **Frete grátis** | Embutir frete e anunciar grátis; frete grátis é o que mais converte | ENP ×4 [AFI], meticsmedia | `shipping.free_shipping` no anúncio do ML (true no termômetro). Ali: `ship_to_days`/frete no `product.query` — a conferir |
| **Parcelamento** | "12× de R$ 10" vende mais que "R$ 120" | ENP [AFI] | ML: `installments` (veio null no produto testado; depende do anúncio). Cartão pode mostrar quando houver |
| **Faixa de preço** | Primeiras vendas: R$ 8–50; impulso até ~R$ 150; alto ticket precisa de confiança | ENP [AFI], Jungle Scout, meticsmedia | v1 já tem; v2 escalona: ≤ 150 = 1,0 · 150–500 = 0,85 · 500–1.500 = 0,7 · > 1.500 = fora do site (fica na série) |
| **Recorrência** | Consumíveis (bebida, suplemento, cartucho, fita), desgaste (camiseta, lâmpada), colecionáveis geram recompra | ENP "Produto Recorrente" ×4 [AFI] | Categoria/nome: Exypna (energético), suplemento, ração, lâmpada, filtro. **+0,15 no Rende** (LTV) |
| **Teste de 30 dias** | 10–20 anúncios por 30 dias; **exclui o que não vendeu** | ENP ×3 [AFI] | Awin: clickref por produto (já no ar). Ali/ML: **falta clique por produto** → o site passa a anotar o clique no Supabase (`clique(produto_id)`) — igual à tabela `busca` que já existe |
| **Kit / ticket** | Kits sobem o ticket; sugerir complementar no carrinho | ENP ×8 [AFI], motion | `combina` (vai bem com) já existe; vira "monte o kit" |
| **Gatilhos honestos** | Escassez só real; prova social com número que se confere; "de/por" só verdadeiro | ENP ×5 [AFI] | Selos 3, 4, 5 (já no código) |
| **Exclusões** | Gift card não é produto; "peça/acessório para X" não é X; livro fora | ENP, juiz de pertinência (16/09) | Lista de exclusão por nome/categoria no `awin --guardar` e no garimpo |

### 6.2 A fórmula v2 (mesmos pesos; eixos mais medidos)

```
VITRINE = 35·Rende + 30·Confiança + 20·Momento + 15·Mostrável        (× faixa de preço)

Rende      = ganho/ref_loja · faixa(preço) · (1 + 0,15 se recorrente)
Confiança  = Ali: 0,6·nota + 0,4·volume (v1)
             ML : 0,5·reputação_vendedor (5_green=1 · 4=0,6 · ≤3=0) + 0,3·vendedores(≥5) + 0,2·frete_grátis
                  × 0,8 se vendedores > 30 (commodity)
             Awin: reputação da loja (manual, 60 dias)  |  0 sem dado
Momento    = v1 (queda medida + volume/vendedores subindo)
             + 0,3 se o nome casa com termo em alta da categoria no ML (tendências)
Mostrável  = views do post (quando houver) · imagem · frete grátis (+0,1)
Piso       = v1 + exclusões (gift card, peça/acessório, livro)
Kill       = 30 dias na vitrine sem clique (clickref no Awin; `clique` no site pros demais) → sai da vitrine
```

### 6.3 Lojas externas: os 2 blocos por categoria

- **"achadinhos"**: ≤ R$ 150 · **"maior valor"**: R$ 150–1.500 · acima de 1.500: só série.
- Por loja e por categoria, **top 300 por bloco** pela régua (o site não pesa; Nike inteira seria 4 MB).
- Cada bloco com "ver mais" (já existe na página).
- Enquanto Confiança/Momento das externas forem 0, a ordem é Rende × faixa; **o kill de 30 dias
  e o clickref fazem a curadoria acontecer sozinha** a partir do 1º mês.

### 6.4 Ordem de implementação (cada passo com guarda e medição)

1. `clique` no Supabase (tabela + anotação no clique do cartão) — o dado que falta em Ali/ML.
2. ML: reputação do vendedor + frete grátis na reconferência horária (`fichas_atual` já abre o anúncio).
3. Tendências do ML por categoria no garimpo (pauta) e no Momento (casamento por nome).
4. Faixa escalonada + recorrência + exclusões na régua; teste teoremático.
5. `awin --guardar` com dois tetos e top 300 por bloco/categoria; blocos na página.
6. Kill de 30 dias (lê clickref do relatório Awin e `clique` do Supabase).

---

## 7. Máquina de vendas — o que não estamos vendo (18/09/2026, 3ª investigação)

Terceira passada, agora sobre **conversão e diferencial**, não sobre produto: 15.789 fichas de
venda, 15 temas. Fontes que pesaram: Ecommerce na Prática (Brasil), Hormozi, motion (criativo),
Saraev (copy), Iman Gadzhi. Abaixo, só o que **não fazemos** — ordenado pelo que os mentores mais
repetem e pelo que temos dado para executar.

### 7.1 O que não sabemos que não sabemos (os buracos de medição)

| Buraco | Por que importa | Fonte |
|---|---|---|
| **Não sabemos qual vídeo gerou qual clique.** O link da bio é por canal; o clique no site não carrega o vídeo de origem | motion: "alinhe oferta, audiência e proposta do anúncio ao checkout"; sem isso não há como escalar o criativo vencedor | motion ×4 |
| **Não sabemos o prazo de entrega** de nada (Ali 15–40 dias vs ML 2–5) e é a objeção nº 1 de importado | ENP: frete/prazo é o que mais converte; "responda a pergunta antes dela" | ENP ×6 |
| **Não temos uma lista que seja nossa.** 98,7 % do tráfego é "Para Você" do TikTok; o canal do Telegram é o único ativo próprio | Hormozi: e-mail front-end; ENP: lista de transmissão segmentada por produto | ENP ×12, Hormozi ×3 |
| **Não medimos a velocidade da página** (PageSpeed) — nunca rodou | ENP, createaprowebsite: PSI antes de qualquer campanha | 3 |
| **Não temos prova social nossa** — só a da loja (% positivas). Zero "comprei e chegou" | Hormozi: loop de UGC (cliente → depoimento → anúncio); ENP: depoimento + bônus | 8 |
| **Não lemos as objeções** que já estão nos comentários dos nossos vídeos | Hormozi: "extraia a objeção primária das transcrições e trate em 3–5 linhas"; ENP: FAQ no anúncio | 5 |

### 7.2 Diferenciais que os mentores repetem e que dá para adotar

| # | Diferencial | O que muda no site/anúncio | Dado/infra | Fonte |
|---|---|---|---|---|
| 1 | **Link do vídeo abre o produto do vídeo** (`?p=<id>&v=<video>`): quem veio do vídeo do pulverizador vê o pulverizador em 1º, com o mesmo gancho | topo da página troca pelo produto do vídeo; `clique_produto` ganha `video` | contra-capa já conta por canal; falta o parâmetro | motion, Saraev |
| 2 | **"Frete grátis" e "chega em ~N dias"** no cartão | ML: `free_shipping` já no instantâneo (hoje só na régua); Ali: `ship_to_days` do `product.query` (a medir); Awin: `delivery_time` só Radiale/Exypna | ML pronto; Ali a medir | ENP |
| 3 | **Objeções dos comentários viram 1 linha no cartão** ("é original?" → "loja oficial 8BitDo"; "demora?" → "chega em 12–25 dias") | ler comentários do TikTok dos nossos posts (`desempenho` já lê views) → modelo extrai objeção → linha honesta | cota de modelo pequena (1 post/produto) | Hormozi, ENP |
| 4 | **"N pessoas de olho neste preço"** — o nº real de inscritos no avise-me do produto | escassez REAL (ENP: "nunca inventar escassez"); sobe com o próprio uso | `alertas.jsonl` | ENP ×5 |
| 5 | **Reposição no tempo certo**: consumível (Exypna, whey, ração) ganha "lembrar em 30 dias" no avise-me | recompra sem anúncio; LTV | `alertas.py` + regex de recorrente | ENP "Produto Recorrente" ×4 |
| 6 | **Loop de prova social nossa**: quem clicou recebe (Telegram, 20 dias depois) "chegou? manda a foto" → foto vira "quem comprou" no cartão, com brinde (cupom/achadinho) | única prova que ninguém copia | canal + avise-me já colhem chat_id | Hormozi ×3, ENP ×4 |
| 7 | **3 opções lado a lado na categoria** (barato · o que mais rende · premium) — o premium ancora; o do meio vende | ENP "efeito chamariz"; Hormozi "âncora 10×" — é o argumento a favor do bloco "A partir de R$ 100" | dados já existem; é layout | ENP, Hormozi |
| 8 | **Garantia de conferência**: "preço conferido hoje às 19:55 — se na loja estiver mais caro, me avisa" com botão | reversão de risco possível pra afiliado (não é reembolso, é promessa que cumprimos) | botão → Telegram do bot | Hormozi, Iman |
| 9 | **Achadinho do dia**: 1 produto, 1 história (o vídeo embutido), 1 motivo medido — no topo, todo dia | Hormozi: "um canal, um produto, um avatar"; ENP: "produto estrela" | `desempenho` + série | Hormozi ×3 |
| 10 | **Páginas de intenção**: "melhor balança digital 2026", "X vs Y" geradas da série (comparação real de preço/queda/nota) | tráfego do Google além do TikTok; a série é o conteúdo | índice estático já existe; gerar por categoria | ENP, meticsmedia, ferdycom |
| 11 | **Checklist de copy por cartão** (Saraev): giving · micro-compromisso · prova social · autoridade · rapport · escassez — auditar cada cartão | hoje: giving ✓ (queda medida), social ✓ (%), escassez ✓ (Recorde), autoridade ✗, rapport ✗, micro ✗ | é auditoria + 2 linhas | Saraev |
| 12 | **PageSpeed** medido e travado como guarda (≥ 80 mobile) | cada 1 s a menos converte mais; nunca medimos | PSI API grátis | ENP |

### 7.3 O que os mentores dizem e NÃO cabe aqui (pra não perseguir)
- Cupom/cashback próprio, frete grátis condicional, kit com desconto → são da **loja**, não do afiliado.
- Parcelamento "12×" → a API não expõe; e só numa loja distorce a comparação (decisão de 18/09).
- Tráfego pago → orgânico é a nossa vantagem (margem menor aceita — meticsmedia); primeiro medir o funil.

### 7.4 Ordem sugerida (o que mais aproxima da venda por menos código)
1. **`?p=<id>&v=<vídeo>` na bio + `video` no clique** — fecha o buraco nº 1 e habilita o teste de criativo (motion).
2. **Frete grátis (ML) no cartão** — dado já no instantâneo.
3. **"N de olho" + "lembrar em 30 dias"** no avise-me — reutiliza tudo que existe.
4. **Prazo do Ali** (`ship_to_days`) — medir a API; se der, é a maior objeção resolvida.
5. **Achadinho do dia** com vídeo embutido — 1 layout.
6. **Objeções dos comentários** → linha no cartão — precisa de leitor de comentários.
7. **Loop de prova social** (Telegram 20 dias depois) — precisa do avise-me rodando.
8. **Páginas de intenção** — SEO, resultado em semanas.
