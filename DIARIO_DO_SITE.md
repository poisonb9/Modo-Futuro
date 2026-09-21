# Diário do site — achadinhototal.com.br

Uma entrada por publicação **confirmada no ar**, escrita pelo próprio
publicador a partir do commit (assunto = o quê; primeiro parágrafo do
corpo = o porquê). Mais novo primeiro.

---

## 21/09/2026 01:25 — `7fd35ee`

**O quê:** Heroi: capturar a classe herdada antes da PRIMEIRA limpeza da vitrine

**Por quê:** MEDIDO no ar com MutationObserver: o cartao era remontado sem classe e so' 17 ms depois recebia `fundo-cena`. Um quadro -- mas a heranca existia justamente para nao ter nem isso.

Carimbo no ar: `8ecd4297f42d` · 25 endereço(s) conferidos · HTML 109 KB

---

## 21/09/2026 01:20 — `833abe7`

**O quê:** Heroi: `decode()` numa <img> solta pode nunca responder (e a heranca lia tarde)

**Por quê:** 1. `img.decode()` NUNCA CUMPRE NEM REJEITA numa <img> que ainda esta' fora do documento -- e e' exatamente essa que o construtor cria. MEDIDO: os logs mostraram "quandoDer" e depois NADA; `medir()` nunca foi chamada e o cartao ficou sem classe, em silencio. No ar isso nao aparecia porque la' o cartao vem do SSR, ja' anexado -- por isso a cena passava e o estudio, que so' eu testo local, nao. Agora `decode()` e' ATALHO COM PRAZO (120 ms): se nao responder, mede-se assim mesmo. Quem garante e' a repeticao, nao a promessa.

Carimbo no ar: `80ae9b5c9b7a` · 25 endereço(s) conferidos · HTML 109 KB

---

## 21/09/2026 01:17 — `b45a93b`

**O quê:** Heroi: `decode()` numa <img> solta pode nunca responder (e a heranca lia tarde)

**Por quê:** 1. `img.decode()` NUNCA CUMPRE NEM REJEITA numa <img> que ainda esta' fora do documento -- e e' exatamente essa que o construtor cria. MEDIDO: os logs mostraram "quandoDer" e depois NADA; `medir()` nunca foi chamada e o cartao ficou sem classe, em silencio. No ar isso nao aparecia porque la' o cartao vem do SSR, ja' anexado -- por isso a cena passava e o estudio, que so' eu testo local, nao. Agora `decode()` e' ATALHO COM PRAZO (120 ms): se nao responder, mede-se assim mesmo. Quem garante e' a repeticao, nao a promessa.

Carimbo no ar: `bd1335386b05` · 25 endereço(s) conferidos · HTML 109 KB

---

## 21/09/2026 01:10 — `4fcc823`

**O quê:** Barra do heroi em Clear, e o fundo medido na PUBLICACAO (mata o flash)

**Por quê:** 1) "deixar um pouco transparente mas chamando a atencao para o nome e principalmente o preco"

Carimbo no ar: `458a36f4aa8b` · 25 endereço(s) conferidos · HTML 109 KB

---

## 20/09/2026 23:00 — `2ac75ad`

**O quê:** Nome do produto no teto da faixa: 18px e peso 500

**Por quê:** "Voce acha que aumentamos ainda um pouco mais o texto que esta sendo digitado?" — sim, e o acervo da' a regua: corpo 16-18px (MAESTROS_ESTETICA, DEMONSTRADO). 16,5 -> 18px, que e' o TETO. Acima disso o nome passa a disputar tamanho com o preco.

Carimbo no ar: `f9d10e09208b` · 25 endereço(s) conferidos · HTML 107 KB

---

## 20/09/2026 22:46 — `0275d1f`

**O quê:** Nome maior e a caixa que cabe; e a guarda do titulo restrito

**Por quê:** 1) ⛔ O ATROPELO QUE ELE FOTOGRAFOU. Com o nome em duas linhas, a segunda sumia atras do preco ("Carregador de carro USB / C carregamento rapido"). Mesma classe de erro de horas atras, cometida por mim DE NOVO: cresci o preco de 26 para 34px de altura e NAO cresci a caixa de altura fixa que o contem. Com `justify-content: center`, o que nao cabe vaza pelos dois lados. 134 -> 152, somando a mao: nome 42 + preco 34 + dica 15 + botao 26 mais vaos e padding. Altura fixa continua de proposito (a linha nao pode pular quando o nome muda de tamanho) — mas altura fixa OBRIGA a somar a mao toda vez qu...

Carimbo no ar: `927a54668c32` · 25 endereço(s) conferidos · HTML 107 KB

---

## 20/09/2026 22:33 — `56f6975`

**O quê:** precos: instantaneo do catalogo

Carimbo no ar: `a0a5771b908c` · 25 endereço(s) conferidos · HTML 106 KB

---

## 20/09/2026 22:21 — `e5af22b`

**O quê:** O preco vira o dono da linha; e a caixa do CTA finalmente acende

**Por quê:** 1) "DE QUE MANEIRA APRESENTAR O NOME E O VALOR PARA O CLIENTE QUERER MUITO COMPRAR?" O acervo do projeto responde com o TESTE DO OLHO MEIO FECHADO (YC, Garry Tan): o elemento de maior peso tem de ser o que importa. MEDIDO no heroi, havia TRES familias — Archivo Black no titulo, Poppins no nome, JetBrains Mono no preco — e o acervo e' DEMONSTRADO nisso: "uma fonte de exibicao so'". O preco era o UNICO ainda em mono: vitrine e cartoes migraram para Poppins em 19/09 e o heroi ficou para tras. Estava escrito no handoff como item 1 da minha lista desde as 01:30 e nunca foi feito. preco mono 22px...

Carimbo no ar: `79ada51843b6` · 25 endereço(s) conferidos · HTML 106 KB

---

## 20/09/2026 22:17 — `e5af22b`

**O quê:** O preco vira o dono da linha; e a caixa do CTA finalmente acende

**Por quê:** 1) "DE QUE MANEIRA APRESENTAR O NOME E O VALOR PARA O CLIENTE QUERER MUITO COMPRAR?" O acervo do projeto responde com o TESTE DO OLHO MEIO FECHADO (YC, Garry Tan): o elemento de maior peso tem de ser o que importa. MEDIDO no heroi, havia TRES familias — Archivo Black no titulo, Poppins no nome, JetBrains Mono no preco — e o acervo e' DEMONSTRADO nisso: "uma fonte de exibicao so'". O preco era o UNICO ainda em mono: vitrine e cartoes migraram para Poppins em 19/09 e o heroi ficou para tras. Estava escrito no handoff como item 1 da minha lista desde as 01:30 e nunca foi feito. preco mono 22px...

Carimbo no ar: `8828a0a4041e` · 25 endereço(s) conferidos · HTML 105 KB

---

## 20/09/2026 21:59 — `52589c2`

**O quê:** A caixa do CTA acende com a luz; barra alinhada com a busca

**Por quê:** 1) A CAIXA, NAO O FIO. Ele viu a borda enchendo pelo perimetro e disse: "isso e' legal mas nao e' bem o que eu queria ... quando a luz aparece e comeca a encher, a caixa que envolve comprar agora comeca a acender, comeca a ter cor e vai chegando a cor ate' o auge e depois apaga tudo". Agora o que anima e' o PREENCHIMENTO, no mesmo compasso do clarao. ⚠️ O TEXTO NAO DEPENDE DESSA COR: e' --tinta sobre a pagina branca, 18:1 mesmo com a caixa completamente apagada. A cor e' evento; leitura nao pode ser evento. ⚠️ `background-color`, nao o atalho `background`, senao a animacao apagaria tambem q...

Carimbo no ar: `a9dc01030951` · 25 endereço(s) conferidos · HTML 105 KB

---

## 20/09/2026 21:39 — `bff3685`

**O quê:** Borda do CTA enche com a luz; e a primeira tela para de cortar o produto

**Por quê:** 1) A BORDA QUE ENCHE. "o botao vai acendendo o contorno dele conforme a luz que vem por tras enche ele, e no fim ele fica ligado igual esta' agora; depois some e reinicia no proximo preco". Barra de progresso circular: `conic-gradient` com parada dura que anda pelo perimetro, com o angulo registrado por `@property` para poder interpolar (sem registrar, a variavel e' texto e o contorno pularia de 0 para 360). `from -90deg` comeca no topo, que e' onde o olho espera. Mesma duracao e curva do clarao, senao a borda corre por fora da luz que deveria estar enchendo ela. `both` deixa acesa no fim;...

Carimbo no ar: `9ee29ec2d74d` · 25 endereço(s) conferidos · HTML 105 KB

---

## 20/09/2026 21:15 — `0d4fedd`

**O quê:** vitrine: o que ja' foi ao canal

Carimbo no ar: `d5e9ec089495` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 21:05 — `5fa16ff`

**O quê:** A forma: tres ladrilhos no lugar da lajota fatiada

**Por quê:** Ideia do Bryan, do dock do iOS 26 que ele mandou: "inves dos icones deles verdes podemos por nossas informacoes". Era a ultima peca da ideia dele que faltava construir.

Carimbo no ar: `d5e9ec089495` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 21:01 — `5fa16ff`

**O quê:** A forma: tres ladrilhos no lugar da lajota fatiada

**Por quê:** Ideia do Bryan, do dock do iOS 26 que ele mandou: "inves dos icones deles verdes podemos por nossas informacoes". Era a ultima peca da ideia dele que faltava construir.

Carimbo no ar: `a7e77e363759` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 20:43 — `76343c4`

**O quê:** Cabecalhos de seguranca: os tres faceis, CSP de conteudo fica para depois

**Por quê:** Autorizado pelo Bryan depois de eu explicar cada um em portugues claro. Hoje o Pages nao manda NENHUM dos quatro (conferido no ar).

Carimbo no ar: `7b1747b39101` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 20:40 — `b5ef17c`

**O quê:** Vigia: marca relida depois do pull, e rc=2 e' fila, nao falha

**Por quê:** A marca era gravada com o hash lido ANTES do `git pull` — entre uma coisa e outra cabe um push, e ai' publicava-se o estado novo gravando a marca do velho: o ciclo seguinte repetia um deploy identico. Nao era incorrecao (o sistema se conserta em 10 min), era deploy jogado fora. Agora a marca vem de HEAD depois do pull: casa com o byte que subiu.

Carimbo no ar: `6bc979fed2e4` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 20:25 — `35dec4f`

**O quê:** Diario: entrada de 1c47c12 (segunda linha viva no ar)

Carimbo no ar: `a53c67b1279e` · 25 endereço(s) conferidos · HTML 104 KB

---

## 20/09/2026 20:15 — `39c5292`

**O quê:** Diario: entradas de 546da81 (RLS) e 1c47c12 (segunda linha viva)

Carimbo no ar: `bc9c27d3b8e6` · 25 endereço(s) conferidos · HTML 104 KB

---

## 20/09/2026 20:10 — `39c5292`

**O quê:** Diario: entradas de 546da81 (RLS) e 1c47c12 (segunda linha viva)

Carimbo no ar: `f1df9005bc36` · 25 endereço(s) conferidos · HTML 104 KB

---

## 20/09/2026 19:03 — `ee686fa`

**O quê:** Diario: entradas de d82b7c9 (trava) e f11a21c (CTA discreto)

Carimbo no ar: `2216e7c79d61` · 25 endereço(s) conferidos · HTML 104 KB

---

## 20/09/2026 18:51 — `f11a21c`

**O quê:** CTA: a discreta vira o padrao; o andaime fica ate' ele fechar

**Por quê:** Bryan: "por hora gostei do discreto" e, logo depois, "mas to' na duvida, vamos definir mais tarde?". Entao a discreta vai para o ar — e' a que ele prefere hoje — e as outras CONTINUAM testaveis, agora com o caminho de volta incluido:

Carimbo no ar: `80b1ec53f13a` · 25 endereço(s) conferidos · HTML 104 KB

---

## 20/09/2026 18:42 — `d82b7c9`

**O quê:** Uma publicacao por vez: trava contra o vigia que publica sozinho

**Por quê:** 18:1x eu disparei `publicar_bio.py --subir` a mao 18:20 a tarefa `AchadinhoTotal_Publicar_Ao_Mudar` disparou SOZINHA 18:2x minha verificacao acusou "NAO ESTA' NO AR em: pagomenos/todos, achadinhodehoje/todos, meulivro/todos"

Carimbo no ar: `29cb0a66819b` · 25 endereço(s) conferidos · HTML 104 KB

---

## 20/09/2026 18:35 — `d82b7c9`

**O quê:** Uma publicacao por vez: trava contra o vigia que publica sozinho

**Por quê:** 18:1x eu disparei `publicar_bio.py --subir` a mao 18:20 a tarefa `AchadinhoTotal_Publicar_Ao_Mudar` disparou SOZINHA 18:2x minha verificacao acusou "NAO ESTA' NO AR em: pagomenos/todos, achadinhodehoje/todos, meulivro/todos"

Carimbo no ar: `5d3b42b4c9df` · 25 endereço(s) conferidos · HTML 104 KB

---

## 20/09/2026 18:13 — `63dee00`

**O quê:** Diario: entrada de 28555be (pilula da aba mais sutil)

Carimbo no ar: `4fb71df5bb06` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 18:05 — `28555be`

**O quê:** Pilula da aba mais sutil: menos tinta e muito menos sombra

**Por quê:** MEDIDO ANTES DE BAIXAR, e a medicao mudou onde eu ia mexer: no CLARO o preenchimento quase nao afeta a legibilidade — de 72% para 36% a razao vai de 18,04 para 17,93, ou seja 0,11 de diferenca. A barra ja' e' quase branca, entao branco sobre branco nao muda a luminancia. Quem da' presenca a' pilula nao e' a tinta: e' a SOMBRA.

Carimbo no ar: `3713b1a3a7a4` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 17:54 — `59962b7`

**O quê:** Aba ativa: fica a "clara", andaime removido, e tres regras viram uma

**Por quê:** Bryan escolheu entre as quatro testadas no aparelho: "a clara". As outras duas variantes e o seletor `?aba=` saem do codigo — era andaime declarado, nao podia virar entulho.

Carimbo no ar: `6b6d7622e63f` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 17:24 — `e183b71`

**O quê:** Diario: entrada de 1c4bc6c (tres variantes da aba ativa)

Carimbo no ar: `73073d008326` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 17:20 — `1c4bc6c`

**O quê:** Tres variantes da aba ativa, testaveis pelo endereco

**Por quê:** Bryan (20/09): "a pilula no inicio ta' muito evidente, tem como chamar menos atencao? Nao sei? Vamos testar".

Carimbo no ar: `7716e7f68efe` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 17:03 — `c7ea7ee`

**O quê:** precos: instantaneo do catalogo

Carimbo no ar: `2bc1c798d499` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 16:23 — `c655a12`

**O quê:** vitrine: o que ja' foi ao canal

Carimbo no ar: `fe11cd36490a` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 16:12 — `95d2902`

**O quê:** Diario: entrada de 005afe6 (CTA sai com o preco; pilula da aba solida)

Carimbo no ar: `abe22868e922` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 16:04 — `005afe6`

**O quê:** CTA some junto com o preco; e a pilula da aba volta a ser solida

**Por quê:** 1) "QUERO QUE ESSE BOTAO APARECA SO' QUANDO O PRECO NO FINAL APARECE, ELE ESTA' FICANDO CONSTANTEMENTE APARECENDO". Eu limpava o preco na troca de produto (`aPreco.innerHTML = ""`) e esquecia o CTA: ele sobrava da rodada anterior durante a digitacao do nome seguinte — um botao de comprar sem preco nenhum na tela, que e' o oposto do que ele existe para fazer. No print dele da' para ver o vao: nome em cima, nada no meio, pilula embaixo. Agora sai junto e volta junto.

Carimbo no ar: `6d81a2d72f32` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 14:57 — `a452d0e`

**O quê:** precos: instantaneo do catalogo

Carimbo no ar: `1fa0297bba60` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 14:44 — `5423834`

**O quê:** Produto principal no lugar do mostrador; mostrador vai para o fim

**Por quê:** Ordem do Bryan (20/09), com desenho em cima do print: o produto principal assume o lugar do mostrador, e o mostrador desce para depois do botao do Telegram.

Carimbo no ar: `93e26b515f64` · 25 endereço(s) conferidos · HTML 103 KB

---

## 20/09/2026 12:25 — `551fc37`

**O quê:** CTA "Comprar agora" com a economia medida, luz sobre o preco, diario do site

**Por quê:** 1) "QUERIA QUE APARECESSE ALGO COMO COMPRAR AGORA ... QUE ESTIMULASSE A PESSOA A COMPRAR", e depois o porque: "o preco mostra mas a pessoa nao sabe que ela tem que clicar pra ir pro produto" ("toque aqui" ele ja' tinha recusado: "feio tambem"). O problema e' AFFORDANCE: a linha viva sempre foi um link e nunca pareceu um.

Carimbo no ar: `af88cfa90b9e` · 25 endereço(s) conferidos · HTML 103 KB

---

