# Awin — o que o anunciante vê, e como caber tudo num endereço só

⚠️ **CORRIGIDO EM 14/09/2026, depois da print do Bryan.** A primeira versão
deste arquivo listava dez Espaços Promocionais pra cadastrar. **A tela não
aceita dez.**

---

## O que a tela realmente oferece

`Configurações → Links de redes sociais` tem **quatro campos, e só**:

```
Site                 https://oachadinho.pages.dev
URL do Blog          https://oachadinho.pages.dev
Nome no Twitter      (vazio)
Página do Facebook   (vazio)
```

Não há campo de TikTok, nem de Telegram, nem lugar pra um segundo site.

⚠️ **E a API também não alcança** (medido): `/promotionalspaces`,
`/websites` e `/profile` respondem **404** com o nosso token, que só abre
`programmes` e relatórios.

---

## ⭐ Por isso a saída inverte

Se o anunciante vê **um endereço**, a resposta não é cadastrar mais
endereços — é **esse endereço mostrar a operação inteira**.

Hoje ele abre `oachadinho.pages.dev`, que é a bio do **Truque Importado**:
maquiagem e beleza. Foi exatamente a queixa da 365Rider (*Sportswear*):

> **O site não complementa a marca do anunciante**

⚠️ E **não dá pra encher a bio do Truque Importado de links dos outros
canais.** Ela tem outro trabalho: converter quem chegou de um vídeo de
maquiagem. Duas plateias, dois objetivos — quem paga a conta de misturar é a
conversão de quem veio do vídeo.

### ✅ ATUALIZADO em 15/09 — agora é o SITE MÃE, e os dois campos são usados

⚠️ **A instrução de 14/09 mandava colar a MESMA coisa nos dois campos.** Era
desperdício: a tela tem `Site` e `URL do Blog`, e eles podem apontar para
coisas diferentes.

**Cole assim:**

```
Site           https://achadinhototal.pages.dev
URL do Blog    https://achadinhototal.pages.dev/parceiros
```

⭐ **Por que o site mãe, e não a bio.** Decisão do Bryan em 15/09, e ela
ataca a causa MEDIDA da recusa. A 365Rider (Sportswear) recusou com *"o site
não complementa a marca do anunciante"* — porque abriu `oachadinho`, que é a
bio de um canal de **maquiagem**. O site mãe mostra **cinco áreas numa página
só** (medido em 15/09: Beleza, Casa, Cozinha, Eletrônicos, Fitness), com
preço e histórico. Anunciante de esporte abre e vê Fitness ali dentro.

⭐ **E a ordem dos dois campos não é arbitrária.** A `/parceiros` é
**discurso** — nós dizendo o que fazemos. O catálogo é **prova** — 62
produtos reais com preço acompanhado dia a dia. Quem avalia parceria confia
mais no que vê funcionando, então a prova vai no campo principal e a
explicação fica a um clique.

⚠️ **O site mãe NÃO fala de canal** (decisão do Bryan em 14/09, e está certa
para quem compra). O anunciante só descobre que há cinco TikToks se abrir a
`/parceiros` — que é exatamente por isso que ela continua no segundo campo,
em vez de sumir.

⚠️ **O que eu NÃO sei:** se o Awin reavalia as 28 pendentes quando o perfil
muda, ou se isso só vale para as próximas. Trocar não custa nada e melhora as
próximas de qualquer forma — mas a 365Rider pode estar perdida.

⭐ A rota foi conferida pelo CONTEÚDO, não pelo status: `/parceiros` do site
mãe tem a frase "search bidding", que só existe na página do anunciante.
Conferir por `200` não provaria nada — o Cloudflare devolve a raiz quando o
caminho não existe.

Ela lista os **seis canais** com a categoria de cada um e o setor de
anunciante que combina, como eu trabalho (garimpo diário, preço conferido
contra histórico próprio), o Telegram, e a frase que remove a objeção.

⚠️ **Não é um projeto novo:** a conta do Cloudflare bateu o teto de **10
projetos** (medido em 14/09; 4 dos 10 são endereços reservados do Até
Falhar). Então ela vai como **rota** dentro dos projetos que já existem —
o mesmo endereço serve nos cinco:

```
oachadinho.pages.dev/parceiros       200
achadinhochef.pages.dev/parceiros    200
pagomenos.pages.dev/parceiros        200
achadinhodehoje.pages.dev/parceiros  200
meulivro.pages.dev/parceiros         200
```

⭐ **E ela sobrevive ao próximo deploy.** Upload direto substitui o
diretório inteiro: se a rota não subisse no mesmo deploy da bio, o deploy
seguinte a apagaria em silêncio e o link do perfil viraria 404. Por isso
`publicar_bio.py` sobe as duas juntas e **confere a rota separadamente** —
a raiz estar nova não prova que `/parceiros` subiu.

⚠️ **O nome do dono saiu do rodapé**: o detector de vazamento do próprio
`publicar_bio.py` reprovou a primeira versão. O anunciante já vê o nome na
conta do Awin.
⚠️ **O que eu não sei:** se o Awin reavalia sozinho uma candidatura
pendente quando o perfil muda, ou se só vale pras próximas. As 28 em aberto
é que estão em jogo — a 365Rider pode estar perdida.

---

## Enquanto isso, o que cabe hoje na tela

Os dois campos vazios aceitam alguma coisa:

| campo | o que pôr |
|---|---|
| Nome no Twitter | (não temos — deixar vazio) |
| Página do Facebook | (não temos — deixar vazio) |

⚠️ **Não invente perfil pra preencher campo.** Link que não abre é pior que
campo vazio na tela de quem está decidindo.

---

⭐ Para reconferir o estado das candidaturas, sem abrir o painel:

```bash
python -m engine.awin
```

---

# A NIKE BR, MEDIDA (16/09/2026)

É o **único** anunciante aprovado. `mid = 17652`, nosso `affid = 3089205`,
`status Active`, `linkStatus online`, `deeplinkEnabled: true`.

## ⭐ O link JÁ FUNCIONA com o token de hoje — não espera a chave de datafeed

`engine.awin.link()` foi testado ponta a ponta contra uma página real da
Nike. O `cread.php` devolveu **302** e pousou em:

```
nike.com.br/tenis-nike-air-force-1?aw_affid=3089205&awc=17652_...&utm_source=Zanox
```

⭐ `aw_affid=3089205` é **nós**, e o `awc=` é o carimbo de clique do Awin. O
`403` que aparece no fim é a proteção antirrobô da Nike recusando um `requests`
do Python — não é falha do link. Um navegador de verdade abre.

## ⛔ O CASO NEGATIVO ACHOU ALGO PIOR QUE "NÃO PAGA"

Rodei o mesmo link **sem** o nosso `awinaffid` esperando que ele não pagasse.
Não é isso que acontece:

```
sem affid  ->  nike.com.br/...?aw_affid=13430&awc=17652_...
```

**O Awin preenche com o afiliado 13430**, que não somos nós. Link malformado
não quebra e não deixa de pagar — ele paga **outra pessoa**, com a página
abrindo normalmente e nada indicando o desvio. É a regra do `tracking_id` do
AliExpress em outra roupa, e aqui ela é ainda mais silenciosa.

## As comissões, e por que "14%" seria uma leitura errada

22 grupos. O que vale para quase tudo é **7,50%**:

```
14,00%   5 grupos, TODOS presos a SKU específico (condição PRODUCT_SKU IN_LIST)
         Dunk · P-6000 · Shox · Court Vision · Air Force 1
 7,50%   os outros 17, incluindo o grupo `Default` (sem condição nenhuma)
         Calçados · Corrida · Treino · Futebol · Roupas · Infantil · Cupom · ...
```

⚠️ **Anunciar "Nike paga 14%" seria falso.** Os 14% dependem do SKU exato estar
numa lista que não temos — e sem a chave de datafeed não há como saber quais
SKUs são. O número que se pode usar para decidir é **7,50%**.

## ⚠️ E "a que custo", antes de "quanto"

```
approvalPercentage   77,54%     <- 1 em cada 4 comissões não é aprovada
validationDays          33
averagePaymentTime      47 dias
conversionRate        3,33%
epc                   1,28      (a unidade do Awin aqui não foi confirmada)
```

**7,50% × 0,7754 = 5,82% efetivo** — *menos* que os 7% nominais do AliExpress.

⭐ **Mas a comissão não é a variável que decide; o TICKET é.** Medido no nosso
catálogo (304 produtos): mediana **R$ 38,79**, média R$ 56,87, maior R$ 253,52.

```
ganho por venda        AliExpress 7,00% da mediana R$ 38,79  =  R$  2,72
                       Nike 7,50% de um tênis R$ 349         =  R$ 26,18
                                              (x aprovação)  =  R$ 20,30
                       Nike 7,50% de um tênis R$ 499         =  R$ 37,42
                                              (x aprovação)  =  R$ 29,02
```

**Uma venda da Nike vale 7 a 11 vendas do catálogo de hoje.** Essa é a razão
para usá-la, e ela sobrevive à aprovação de 77,5% com folga.

⚠️ **O que ainda não sei, e não dá pra medir sem a chave:** se a Nike BR
oferece feed de produto. Sem feed, dá para gerar link de qualquer página do
site (`deeplinkEnabled: true`), mas não dá para garimpar preço e queda como se
faz no AliExpress — e é o acompanhamento de preço que esta operação vende.

---

# COMO PEGAR A CHAVE DE DATAFEED

⛔ **É outra chave.** Confirmado por medição em 16/09/2026 e pela documentação
do Awin: *"The API key for product feeds is different from your Publisher API
key."*

```
Toolbox  ->  Links & Tools  ->  Create-a-Feed
```

A chave aparece dentro da URL de download que a ferramenta monta:

```
https://productdata.awin.com/datafeed/list/apikey/<A CHAVE>
```

⚠️ **A chave vai no CAMINHO da URL, não no cabeçalho.** Medido, e os dois
erros dizem coisas diferentes:

```
Authorization: Bearer <AWIN_TOKEN>      ->  403  "No API key supplied"
/apikey/<AWIN_TOKEN>                    ->  500  "Sorry, we broke something"
```

⭐ O 500 é o que prova que a chave está errada, e não que o endpoint está
quebrado: quando a chave não existe no formato certo, ele responde 403 dizendo
isso. Com uma chave no lugar certo mas inválida, ele estoura.

Guardar no `.env` como `AWIN_DATAFEED_KEY` — **não** sobrescrever o
`AWIN_TOKEN`, que é o que faz o vigia de candidaturas funcionar.

Fontes: [How to access a product data feed](https://success.awin.com/s/article/How-can-I-access-a-Product-Feed?language=en_US) ·
[Downloading feeds using Create-a-Feed](https://developer.awin.com/docs/downloading-feeds-using-create-a-feed) ·
[Product Feed List Download](https://help.awin.com/docs/product-feed-list-download)
