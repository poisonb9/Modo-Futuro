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
