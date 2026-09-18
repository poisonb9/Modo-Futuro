# Auditoria: o site frente aos Maestros — 18/09/2026

Pedido do Bryan: "análise completa do site frente à skill; como elevar a uma máquina de
vendas absoluta; o que está acontecendo que não estamos vendo". A resposta começa por
**medir o funil**, porque os mentores (Hormozi, ENP, motion) são unânimes: antes de
otimizar a página, saiba quantos entram e quantos saem em cada degrau.

## 1. O funil, medido em 18/09 (últimos 7 dias, dados nossos)

```
TikTok (5 canais, ~11 posts/dia)     views: DESCONHECIDO desde 29/08
                                       (a série de views lê 0 do Buffer há 3 semanas —
                                        "zero do Buffer não é zero", memória de 26/08)
   ↓ toque no link da bio
Bio dos canais (contra-capa)          193 visitas em 7 dias  (~27/dia; c1 = 91, c7 = 40, c6 = 30)
   ↓ toque em produto ou "entrar na casa"
                                       15 cliques em 7 dias   (10 produto, 5 link)  ≈ 8 %
Site mãe (achadinhototal.com.br)      cliques em produto: ~2 reais desde 17/09 (medição nova)
                                       buscas: 5 em 7 dias
Telegram (@achadinhototal)             2 membros
Loja (Ali / ML / Awin)                 0 vendas
```

**O diagnóstico que os números dão, sem opinião:** o site é uma loja pronta numa rua
onde passam ~27 pessoas por dia, e a rua (TikTok) não está medida há 3 semanas. Otimizar
conversão em 27 visitas/dia é medir ruído: com 2 % de conversão seriam 0,5 vendas/dia
**no melhor caso**. A alavanca não está na página; está antes dela e depois dela.

## 2. Estágio por estágio, contra os mentores

### 2.1 Topo: o vídeo não vende o produto (o buraco que não estava na lista)
- Os posts do TikTok são **clipes de conteúdo** (cortes de vídeos alheios); o produto
  aparece na bio, não no vídeo. `publicados.json`: 431 posts, **0 com produto, 0 com URL**.
- motion (×4, DEMONSTRADO): "alinhe oferta, audiência e proposta do anúncio ao checkout".
  Hoje o "anúncio" é um clipe sobre disciplina ou receita; o "checkout" é uma balança digital.
  A congruência é zero por construção.
- loganskimoney/ENP: hook → problema → **produto resolvendo** → prova → oferta. O nosso
  hook existe (clipe), o produto não está no vídeo.
- Bryan adiou o vídeo de produto em 16/09 (Ken Burns recusado). **É a decisão que trava a
  máquina inteira**: sem vídeo de produto não há congruência, não há teste de criativo
  (qual vídeo vende), não há objeção lida, não há prova social em loop.
- **O que se pode fazer sem vídeo**: o clipe leva ao produto do dia pelo `?p=` na bio
  (feito em 18/09) — o mínimo de congruência: quem clica na bio vê primeiro o produto que
  o texto do post citou.

### 2.2 A bio converte 8 % — e isso é bom
- 15 cliques / 193 visitas. ENP considera 1 % ruim e 3–5 % bom em loja; a bio está acima
  porque quem chega já quis clicar. Não é aqui o problema.

### 2.3 A medição de alcance morreu em 29/08
- `serie_views`: 10.487 leituras "confiáveis", mas **views > 0 só até 29/08**. Desde então
  o Buffer devolve 0 e a série grava 0 como se fosse leitura. Memória de 26/08 já dizia:
  "Zero do Buffer não é zero". Três semanas sem saber se um vídeo deu 100 ou 10.000 views.
- Sem alcance não há CTR da bio (cliques ÷ views), que é **o número que decide o que
  postar** (motion: escale o criativo pelo dado).

### 2.4 A lista: 2 pessoas
- Hormozi: "quem não tem lista aluga a audiência"; ENP ×12: lista de transmissão.
- O Telegram é o único ativo próprio e tem 2 membros. O "avise-me" (18/09) é a primeira
  porta de entrada com motivo (a pessoa ganha algo: o aviso). O post de sinal no canal
  (2/dia) fala pra 2 pessoas.
- A bio manda pro Telegram como 2ª opção ("é no canal que aparece primeiro") — sem um
  motivo concreto medido ("R$ 2.543 de queda já entregue", "12 recordes esta semana").

### 2.5 O site em si (onde estamos bem, e o que sobra)
| Critério | Estado | Fonte |
|---|---|---|
| Prova social honesta (% positivas, vendas medidas, vendedores) | ✓ | ENP, meticsmedia |
| Preço conferido + "de" medido (não o da loja) | ✓ — único no mercado | Hormozi (giving) |
| Selos da série (espere, recorde, a loja diz, irmão em outra loja) | ✓ no código; 3 esperam dias de série | — |
| Régua de vitrine 35/30/20/15 + 5+5 no topo | ✓ | Hormozi, ENP |
| Dois blocos 99,99 / 100+ com "ver mais" | ✓ | ENP |
| Velocidade mobile | 72 (era 48) — TBT 550 ms sobra | ENP |
| SEO técnico (canonical, sitemap, índice estático) | ✓ — 0 páginas indexadas ainda (site tem 1 dia) | — |
| Frete grátis / prazo | ML ✓; Ali e Awin não têm dado | ENP |
| Objeções respondidas no cartão | ✗ (sem comentários lidos) | Hormozi, ENP |
| Prova social **nossa** ("comprei, chegou") | ✗ | Hormozi UGC loop |
| Autoridade / quem somos com rosto | quem_somos.html existe; sem rosto, sem história | ENP ×8 |
| Checklist de copy por cartão (Saraev) | giving ✓ social ✓ escassez ✓ · autoridade ✗ rapport ✗ micro ✗ | Saraev |
| Kill de 30 dias e clique por produto | ✓ (nasce em 17/10) | ENP, Hormozi |

## 3. O que está nos atrapalhando (em ordem de estrago)

1. **O produto não está no vídeo.** Tudo o que os mentores chamam de "máquina" (criativo
   → página congruente → prova → recompra) começa no vídeo do produto. Adiado = máquina
   sem motor. Não é um vídeo bonito que falta; é **um vídeo por produto do topo, 15 s,
   fato medido + preço + "link na bio"** — o formato que a ENP e a motion descrevem.
2. **Cegos de alcance desde 29/08.** Sem views não há CTR, sem CTR não há "escale o
   vencedor". Consertar a leitura do Buffer (ou anotar views à mão 1×/semana) vem antes
   de qualquer teste.
3. **Lista de 2.** Cada visita que não deixa um jeito de voltar é perdida. O avise-me e o
   canal precisam de um motivo dito com número, na bio e no cartão.
4. **Dispersão.** 5 canais + 9 lojas + 2.400 produtos externos com 27 visitas/dia.
   Hormozi: "um canal, um produto, um avatar até R$ 100 mil/mês". A régua já escolhe os
   10; o **achadinho do dia** (1 produto, 1 vídeo, 1 motivo) é a forma de foco que cabe.
5. **Nenhuma venda atribuída jamais** — e quando vier, não saberemos de onde (Ali:
   tracking por canal; Awin: clickref por produto desde 17/09 — o único que responde).

## 4. O plano que os números pedem (não o que a página pede)

| # | Ação | Mede o quê | Quem |
|---|---|---|---|
| 1 | Consertar a leitura de views (Buffer) ou anotar à mão semanalmente | alcance → CTR da bio | eu (leitura) / Bryan (se manual) |
| 2 | **Vídeo de produto 15 s** para os 10 do topo, 1/dia, com o fato medido e `?p=` na bio | qual produto/gancho clica (clique_produto + `de`) | decisão do Bryan (adiado em 16/09) |
| 3 | Motivo com número para o Telegram na bio e no cartão ("R$ 3.420 de queda entregue · avise-me") | membros/dia | eu |
| 4 | Achadinho do dia no topo (produto do vídeo do dia) | cliques do dia | eu, depois do 2 |
| 5 | Quem somos com rosto e história (ENP ×8) | confiança (medir por clique/visita) | Bryan grava 1 vídeo; eu monto |
| 6 | Objeções: enquanto não há comentários, usar as **perguntas do ML** (`/questions` da API é pública) do produto irmão | linha honesta no cartão | eu (medir a API) |
| 7 | Reclame Aqui das 10 lojas (manual) | Confiança das externas | Bryan |
| 8 | Páginas de intenção (SEO) | visitas do Google em 30–60 dias | eu |

**A pergunta que decide tudo é a 2.** O resto é polimento de uma loja onde não passa gente.

---

## 5. Crítica sem alisar (18/09, a pedido: "não me alise")

Cada ponto: o que está errado, o que o banco diz, o que fazer. Ordenado por estrago.

### 5.1 O preço que mostramos pode não ser o preço que a pessoa paga (Ali)
- A fumaça de 18/09 devolveu `tax_rate: 0.00` e `target_sale_price` em BRL **sem
  imposto**. No Brasil, importado do Ali paga 20 % de importação + ICMS no checkout
  (Remessa Conforme). Se a página do Ali no Brasil mostra R$ 74,60 e o checkout cobra
  ~R$ 100, o nosso "preço conferido hoje às 19:55" é falso em 30–40 % — **a exata
  mentira que a regra dos 24 h existe pra evitar**, só que estrutural.
- ENP: "cliente encontra outro número na loja = perdeu a confiança pra sempre".
- **Fazer:** Bryan confere 1 produto no celular (site vs checkout). Se divergir: (a)
  mostrar "R$ 74,60 + impostos no checkout" ou aplicar a alíquota conhecida com o
  rótulo "estimado com impostos"; (b) medir a diferença real em 5 produtos antes de
  escolher. Não pode ficar como está.

### 5.2 A máquina inteira sem motor: nenhum vídeo é sobre produto
- 431 posts, 0 sobre produto. O tráfego é de clipes de conteúdo; o produto é rodapé
  de bio. motion/ENP/loganskimoney: o vídeo É a oferta. A decisão de 16/09 (Ken Burns
  recusado, vídeo adiado) transformou o site numa loja sem vitrine na rua.
- **Fazer:** 1 vídeo de produto por dia, 15 s, formato fixo: fato medido (queda,
  recorde, vendas) + preço + "link na bio", `?p=` apontando pro produto. Sem produção
  bonita: a motion diz que o hook de 3 s decide, não a edição. É a única decisão que
  muda o resultado; o resto é polimento.

### 5.3 Cegos de alcance há 3 semanas — e postando 11/dia mesmo assim
- Views = 0 no Buffer desde 29/08 e ninguém parou. Postar sem medir é exatamente o
  que a memória de 26/08 ("zero do Buffer não é zero") já tinha diagnosticado — e
  virou rotina. Última medição real: mediana **169 views** por post, top 1.826.
  Com 169 views e CTR de bio de 1–2 %, cada post vale 2–3 visitas. 11 posts/dia = 27
  visitas/dia — **fecha com o número medido**. Não há mistério: o volume é esse.
- **Fazer:** consertar a leitura (ou anotar à mão 1×/semana) ANTES de qualquer teste
  de criativo. Sem views não existe "escale o vencedor".

### 5.4 Dispersão: 5 canais, 9 lojas, 2.400 produtos, 8 motores — para 27 visitas/dia
- Hormozi: "um canal, um produto, um avatar até R$ 100 mil/mês". Nós: 5 marcas
  (Make, Chef, Total, de Hoje, Pago menos, Até Falhar, Sem Anestesia), 9 lojas
  externas das quais **Carraro (móvel de R$ 4 k), Leveros (ar-condicionado), Radiale
  (pneu)** não têm nada a ver com "achadinho", e Kabum paga 1,15 %. Cada loja entrou
  porque foi aprovada, não porque cabe. Cada canal dilui a lista, o Telegram, a
  atenção.
- **Fazer:** cortar lojas por FIT, não por aprovação (Carraro/Leveros/Radiale fora
  do site; ficam na série). Escolher UM canal-motor para o vídeo de produto (o de
  maior visita na bio: c1) e provar 1 venda/dia por 15 dias (ENP) antes de replicar.

### 5.5 Otimizando a página antes de validar a demanda
- Selos, régua, blocos, Recorde, clickref, kill de 30 dias: 20 commits de conversão
  em 48 h para uma loja com 27 visitas/dia e **nenhuma venda jamais**. ENP: "venda 1
  por dia por 15 dias, depois construa". Estamos construindo a catedral antes da
  primeira missa. Nada disso é errado — é **cedo**, e o custo é o tempo que não foi
  pro vídeo.
- **Fazer:** congelar features de página até a 1ª venda. Só medição e tráfego.

### 5.6 Atribuição de venda: zero, por construção
- Ali: sem `tracking_id` por canal no Portals (o placar diz isso). ML: `matt_word`
  por canal, ok. Awin: clickref por produto desde 17/09. Quando a primeira venda
  vier do Ali (a loja principal), **não saberemos nem o canal**. Hormozi: LTV:CAC por
  canal é a única bússola.
- **Fazer:** criar os tracking_ids por canal no Portals do Ali (é clique do Bryan) e
  passar pelo `garimpo.tracking_de`, que já existe esperando.

### 5.7 A lista é de 2 e a bio mente a promessa
- "É no canal que o achadinho aparece PRIMEIRO" — para 2 pessoas. A promessa está
  certa e ninguém sabe. A bio manda ao Telegram sem motivo com número.
- **Fazer:** o botão vira "R$ 3.420 de queda já entregue — receba a próxima antes"
  (número vivo do multômetro, atualizado na publicação); no cartão, o avise-me é a
  porta. Meta medível: membros/dia.

### 5.8 Sem rosto, sem história, sem garantia
- ENP ×8: "Sobre nós com rosto e história" é o que tira o medo de loja nova; Hormozi:
  reversão de risco. Temos "quem somos" sem rosto e nenhuma promessa que custe algo.
- **Fazer:** Bryan grava 40 s no celular ("eu garimpo, eu confiro o preço toda hora,
  se estiver mais caro na loja me avisa"). A "garantia de conferência" (§7.2 #8) é a
  reversão de risco possível pro afiliado.

### 5.9 A operação depende de mão
- Publicação diária travada em S4U desde 16/09: 3 publicações à mão em 24 h. O
  dia que ninguém publicar, a página envelhece e a trava de 24 h esvazia a vitrine —
  por desenho. Ponto único de falha, e é a gente.
- **Fazer:** resolver o wrangler em S4U (item 1 do handoff, ainda intocado) ou mover
  a publicação pra nuvem (o CF token já está lá; falta só o segredo do modelo pros nomes).

### 5.10 Coisas estranhas que ninguém questionou
- **Nome do bot do "avise-me": `bryan_fxv_fila_bot`.** O cliente vê isso. Bot novo
  custa 1 minuto.
- **Vitrine "Achadinho" abre com 8BitDo de R$ 140 e organizador de R$ 144** para um
  público que veio de clipe de academia/maquiagem. A régua está certa pelos
  números e errada pelo avatar — porque não existe avatar: 5 públicos, 1 vitrine.
- **Quatro documentos de regra** (CRITERIOS, REGRAS, AUDITORIA, PARA_FAZER) em 24 h.
  Sinal de operação que pensa mais do que vende. Eu incluído.

### 5.11 Onde estamos genuinamente à frente (para não jogar fora)
- A série de preços em 3 lojas com 37 k pontos é um ativo que nenhum afiliado
  brasileiro pequeno tem; os selos que nascem dela (espere, recorde, "a loja diz",
  irmão em outra loja) são honestos e inéditos. O clique por produto e o clickref
  são a medição que os mentores mandam ter. A régua com dials explícitos é rara.
  **O problema não é o que construímos; é a ordem.**

## 6. A ordem certa, segundo os números e os mentores

1. **Confirmar o imposto do Ali** (Bryan, 2 min). Se divergir, corrigir o preço exibido
   antes de qualquer vídeo — vídeo mandando gente pra um preço falso queima o canal.
2. **Ligar a medição de views** (leitura do Buffer ou manual semanal).
3. **Tracking_id do Ali por canal** (Portals, Bryan) — pra primeira venda ter dono.
4. **Vídeo de produto, 1/dia, num canal só**, com `?p=` na bio. Meta: 1 venda/dia por
   15 dias (ENP). Medir por clique_produto + `de`.
5. **Lista com motivo**: botão do Telegram com número vivo; avise-me como porta.
6. **Cortar lojas sem fit** (Carraro, Leveros, Radiale) e congelar features da página.
7. Só então: subdomínios, SEO de intenção, quem somos com rosto, copy por cartão.
