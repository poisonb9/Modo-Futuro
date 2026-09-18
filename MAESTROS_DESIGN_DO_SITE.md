# O site frente aos Maestros — design, premium e vendabilidade (18/09/2026)

Segunda consulta ao banco **Maestros da IA** sobre o site, feita em 18/09/2026 em duas
rodadas no mesmo dia. A primeira leu o acervo com **46.183 fichas** e devolveu 98 fichas
úteis — quase todas de funil de infoproduto americano. Bryan atualizou a skill; a segunda
rodada leu **63.970 fichas** e o mesmo filtro devolveu **1.387** (637 DEMONSTRADO ·
699 AFIRMADO · 57 OPINIÃO). A diferença é o bloco de e-commerce brasileiro que entrou:
mayaraprado 469, ecommercenapratica 280, ecommercefree 247, ajudavitor 135,
vendedoresml 65, shopeebrasil 44.

⭐ A série **"Analista de Loja Virtual" EP.2–8 (ecommercenapratica)** é o exercício que o
Bryan pediu, feito em lojas reais por quem audita loja por ofício. Tudo OPINIÃO — e o
banco marca OPINIÃO por honestidade, não por desprezo.

⚠️ Metade das fichas novas é ferramenta (Elementor, Hostinger, Google Ads, clonar página
do produtor). Descartadas. Ficou o princípio, com procedência.

O site foi OLHADO no ar (375px) antes de escrever, não deduzido do código. O primeiro
documento desta família é `CRITERIOS_DA_VITRINE.md` (o que sobe pra loja); este é sobre
**como a página vende** o que subiu. O funil medido está em `AUDITORIA_MAQUINA_DE_VENDAS.md`.

---

## 1. Diagnóstico antes de design — o acervo concorda com a decisão 5

| Regra | Fonte | Base |
|---|---|---|
| CTR alto e conversão baixa → a página; CTR baixo → o criativo/tráfego | motioncreativeanalytics | AFIRMADO |
| CTR de saída × clique-para-compra diz onde está o vazamento | motioncreativeanalytics | AFIRMADO |
| Régua: page-view → add-to-cart **≥ ~9%**; abaixo, mexer na página ou na oferta | IMAN_GADZHI | DEMONSTRADO |

Nosso funil (18/09, 7 dias): 193 visitas na bio → 15 no site (8%) → ~2 cliques pra loja.
**O vazamento maior é ANTES do site** (92% param na bio, que nem tem link clicável).
Com 15 visitas nenhum redesenho é mensurável. É a "catedral antes da missa" (decisão 5)
dita por outra boca. A régua de 9% só serve quando houver tráfego pra medir.

## 2. O que o acervo NOVO diz — e o que muda no site

| Ficha | Fonte | Base | No site hoje → o que fazer |
|---|---|---|---|
| **Kit de credibilidade mínimo**: layout profissional, redes ativas linkadas, "Sobre", política de privacidade (LGPD), CNPJ visível, avaliações | ecommercenapratica ("3 maiores erros") | DEMONSTRADO | Temos layout e "contém links de afiliado". **Faltam**: link pros @ do TikTok, "Sobre" (foto é "depois", mas 3 linhas sem foto já contam), política de privacidade (o Supabase registra clique → LGPD pede aviso) |
| **Prazo de entrega invisível é objeção nº 1** | Analista EP.8 | OPINIÃO | 134 dos 139 itens são Ali e o card não diz *quando chega*. "Chega em 10–20 dias" / "envio do Brasil" decide compra no Ali |
| **Priorizar fornecedores brasileiros no Ali** (converte mais) | ecommercefree (teste de 30 dias) | OPINIÃO | A régua v2 não pontua origem do envio. Dial "envio do Brasil" na régua + selo no card |
| **Importar avaliações REAIS do marketplace** pra dentro da página, só as com foto | ajudavitor ×2, ecommercenapratica | DEMONSTRADO | 1 frase de avaliação real por produto. A ferramenta deles é app de loja (Lily, BK Reviews); o nosso caminho é a API do Ali — **a conferir se devolve review** |
| **Avaliações presentes mas sem destaque → bloco destacado** | Analista EP.5 | OPINIÃO | Nosso "☆ 98%" é um número pequeno no canto do card |
| **Banner na página de produto distrai → remover** | Analista EP.2 | OPINIÃO | A foto do seller ("22 colors available~", "STRONG MAGNETIC FORCE", "HTMCK") É um banner |
| **Home só com logo → produtos em destaque** | Analista EP.3 | OPINIÃO | Topo = logo grande + slogan + 1 produto. Poderia ser o produto |
| **Descrição curta não transmite uso → gif/vídeo de uso; ≥ 3 fotos + vídeo** | Analista EP.4; "Product Ads" do ML | OPINIÃO | Card tem 1 foto, zero uso. Vídeo é "depois" (decisão do Bryan, 18/09) |
| **Proposta de valor no topo responde "por que comprar com você?"** | createaprowebsite (Golden Rule) | OPINIÃO | "Eu garimpo. Você paga menos." responde. Mas a promessa real — *preço vigiado, desconto medido contra o preço que nós vimos* — está só na meta description |
| **Dizer o que o produto NÃO serve** ("só corta alface") constrói confiança e aumenta ganho | ecommercefree ×2 | OPINIÃO | Sem par no acervo antigo. Campo "não serve pra" por produto é diferenciação que vitrine de afiliado não tem. Casa com o selo "espere" |
| **Link de afiliado camuflado no próprio domínio** (evita bloqueio em WhatsApp/Telegram) | mayaraprado | DEMONSTRADO | Já temos `?p=` — falta ele ser o link que vai pro Telegram e pro vídeo, não a URL crua do Ali |
| Manutenção no anúncio (título, foto, ficha) reativa o algoritmo do ML | ecommercefree (curso ML) | DEMONSTRADO | Não é nosso (somos afiliado), mas explica por que preço/link do ML muda embaixo de nós |
| Mesmo criativo do anúncio na página de destino; alinhar oferta do vídeo → landing → PDP | motioncreativeanalytics | DEMONSTRADO / AFIRMADO | Quem vem do vídeo cai num catálogo de 139 com herói aleatório. Quando a bio aceitar link, o link é `?p=<produto do vídeo>`, nunca a raiz |
| Página-ponte entre vídeo e link de afiliado | MAKE_MONEY_MATT ×2 | AFIRMADO | Tocar no card = sai do site direto pro Ali, na mesma aba. `target=_blank` no mínimo; `?p=` como ponte de 1 produto é o desenho certo |
| Ler as avaliações do AliExpress pra achar benefícios e objeções antes da copy | meticsmedia | DEMONSTRADO | Uma linha de benefício por produto, vinda das avaliações, não da cabeça |
| Prova social = voz de cliente, 2–3 citações; perto do CTA | meticsmedia; createaprowebsite | DEMONSTRADO / OPINIÃO | Zero texto humano no site. "3.349.185 vendas destes na loja" é número sem rosto |

## 3. O que está no ar e não está legal — com correção

1. **Foto do seller** (EP.2 + Product Ads). O nº 1 pro "premium": fundo escuro elegante
   + banner de seller chinês = contradição visual. Correção: escolher a imagem mais limpa
   entre as da API do Ali e/ou recortar com o Space do HF já provado (alpha medido).
2. **Nenhuma resposta a "quando chega?"** (EP.8). Correção: prazo no card, do campo de
   envio da API do Ali; origem do envio entra na régua.
3. **Duplicatas visíveis**: dois "Organizador de maquiagem giratório 360°" (R$ 30,19 e
   24,88), duas "Balança digital de café" (R$ 51,99 e 52,49). Pro visitante é defeito.
   Correção: agrupar por identidade (hash) e mostrar o mais barato como principal.
4. **Confiança institucional zero**: sem "Sobre", sem privacidade, sem @ do canal.
   Correção: rodapé com 3 links (Sobre em 3 linhas, Privacidade, @ dos canais) — sem foto,
   sem cobrar a foto.
5. **Telemetria no card**: "no radar há 5 dias", "preço conferido 17/09", "+67 vendidos
   desde 14/09" em monoespaçada. É a nossa telemetria vazando pra tela. Correção: fica o
   que decide compra ("caiu 43%", "menor preço em 30 dias"); o resto some ou vai pro `?p=`.
6. **"Espere" sem saída**: honesto, e fica — mas "já esteve a R$ 96,79 há 3 dias" diz "não
   compre" sem dizer "faça isto". Correção: "avise-me" vira o CTA cheio DESSE card, com o
   texto "avise-me se voltar a R$ 96".
7. **Números do herói falam de nós, não dele**: "R$ 3.602,77 de garimpo já entregue",
   "139 achadinhos de pé". Correção: 1 número que ele entende ("34 baixaram de preço esta
   semana").
8. **Mesma aba pro Ali** — o visitante nunca volta. Correção: `target=_blank`.
   ⚠️ Na sessão de 18/09 o link resolveu pra `de.aliexpress.com` + captcha — é o IP do
   navegador da máquina; conferir no celular que o `pt.` abre limpo.

## 4. O que o acervo sugere e NÃO se recomenda aqui

Pop-up de saída com desconto (3 OPINIÕES) — não temos desconto pra dar. Newsletter com
bônus. "33 banners de produtos na home". Gatilhos "últimas horas" no título. Timer de 90s,
"só 150 cópias", chatbot no site (IMAN/LIAM/GenSpark — DEMONSTRADO em infoproduto, não em
vitrine de R$ 20). Clonar página do produtor. Tudo contradiz a estrela-de-traço-sem-"4.9"
(16/09) e a régua de sinais medidos (17/09).

## 5. A ordem, respeitando "só defeito até a 1ª venda" (decisão 5)

Defeito: **3 duplicatas · 8 aba · 4 privacidade** (LGPD é obrigação, não feature).
Feature que se defende mesmo congelado, porque é objeção e não enfeite: **2 prazo de
entrega** e **1 imagem limpa**. O resto espera a venda.

Antes de 2 e da frase-de-avaliação: **conferir na API do Ali se ela devolve prazo de envio,
origem e review** — decide se é 1 tarde ou 1 semana. Ordem acordada com o Bryan em 18/09:
API primeiro, depois os três defeitos, em loop.

## 6. Como a consulta foi feita (pra repetir)

`referencias/por_resultado.md` da skill `maestros-da-ia`, parse de uma ficha por bloco
`- situação / Saída / Passo / _base · ferramenta · data · vídeo_`. Pontuação por palavra
(página de venda/produto 4, prova social 4, afiliado 3, prazo/urgência 3, ML/Shopee/Ali 3,
avaliação 2, confiança 2, …) e corte em **≥ 7**. Depois agrupamento por tema (imagem,
título, avaliação, afiliado, preço, confiança, urgência, mobile, landing, vídeo, marketplace)
e leitura das OPINIÕES inteiras — são só 57 e são as que carregam princípio.
