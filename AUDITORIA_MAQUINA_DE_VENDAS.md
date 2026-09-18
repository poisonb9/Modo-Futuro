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
