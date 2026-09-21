# Awin — o estado real, 21/09/2026

> ⚠️ **Este arquivo foi reescrito em 21/09/2026.** A versão anterior dizia que
> a Nike era o **único** anunciante aprovado, ensinava a **pegar** a chave de
> datafeed, e mandava cadastrar `achadinhototal.pages.dev`. As três coisas
> estavam vencidas. O que elas ensinavam continua abaixo, na parte que ainda
> vale — mas os números eram de 16/09 e a operação andou.

---

## O QUE ESTÁ FEITO ✅

**O perfil foi preenchido pelo Bryan em 21/09.** Era o item mais urgente da
fila havia três dias:

```
Site           https://achadinhototal.com.br
URL do Blog    https://achadinhototal.com.br/parceiros
```

⭐ **O domínio próprio, e não o `pages.dev`.** O `achadinhototal.com.br` está
no ar desde 17/09. Conferido em 21/09 **pelo conteúdo, não pelo status**:
`/parceiros` devolve 8.015 bytes contendo a frase `search bidding`, que só
existe na página do anunciante. Conferir por `200` não provaria nada — o
Cloudflare devolve a raiz quando o caminho não existe.

⭐ **A ordem dos dois campos não é arbitrária.** O catálogo é **prova** (62
produtos com preço acompanhado dia a dia); a `/parceiros` é **discurso**. Quem
avalia parceria confia mais no que vê funcionando, então a prova vai no campo
principal e a explicação fica a um clique.

⚠️ Twitter e Facebook ficam **vazios**. Link que não abre é pior que campo
vazio na tela de quem está decidindo.

**A chave de datafeed já está no `.env`**, como `AWIN_FEED_API_KEY` (não
`AWIN_DATAFEED_KEY`, como a versão antiga deste arquivo dizia). Ela funciona:
`estado/awin_catalogo.json` de 21/09 tem **3.063 produtos de 11 lojas**.

---

## OS NÚMEROS DE HOJE, MEDIDOS

`python -m engine.awin`, 21/09/2026:

```
JOINED      14
PENDING     37
REJECTED    23
SUSPENDED    0
```

⛔ **A versão anterior deste arquivo dizia "a Nike BR é o ÚNICO aprovado".**
São 14, e entre eles está o AliExpress, que é a base do catálogo:

```
Aliexpress BR & LATAM   Kabum BR        Nike BR          Lacoste BR
Shark-Ninja BR          Arno BR         Carraro BR       Clóvis Calçados BR
Lauri Esporte           Leveros BR      Exypna           Radiale Pneus
Drogaria Venancio BR    Camilovers BR
```

O que já chega ao site, do `awin_catalogo.json`:

```
Aliexpress 614 · Clóvis 611 · Kabum 610 · Nike 460 · Lauri 308
Carraro 305 · Arno 116 · Radiale 20 · Shark-Ninja 10 · Exypna 5 · Leveros 4
```

---

## ⛔ POR QUE AS 23 RECUSAS — A CAUSA, DITA PELO BRYAN

**Elas não trabalham com pessoa física.** Bryan confirmou em 21/09.

⚠️ **Isto derruba a teoria que sustentava este arquivo inteiro.** A versão
anterior partia da recusa da 365Rider (*Sportswear*), cujo texto foi:

> O site não complementa a marca do anunciante

…e concluía que a saída era o perfil apontar para o site mãe, que mostra cinco
áreas em vez da bio de um canal de maquiagem. **Essa conclusão continua certa
e já foi executada** — mas ela explica *uma* recusa, não as 23. A causa
dominante é cadastral, e **nenhuma mudança de site a resolve**.

⭐ **O que muda na prática:** parar de ler as recusas como veredito sobre a
qualidade do site. Das 23, a única com sinal aproveitável sobre a vitrine é a
365Rider. As outras 22 são porta fechada por CNPJ, e insistir nelas é gasto de
atenção onde não há decisão nossa a tomar.

⛔ **E NÃO DÁ PARA SABER ANTES.** O painel da Awin **não mostra** se o
anunciante aceita pessoa física (Bryan conferiu, 21/09). Não há campo, filtro
nem coluna: descobrir custa **uma candidatura e uma recusa**, uma por vez.

⭐ **A consequência prática, que é o que interessa:** as **37 pendentes são um
teto, não uma previsão**. Se a proporção das 23 recusas se repetir entre elas, o
número real de aprovações possíveis é bem menor — e nenhum trabalho nosso move
esse número. É a diferença entre uma frente onde dá para melhorar o resultado e
uma fila onde só dá para esperar.

⚠️ Por isso, ao decidir quanto tempo a Awin merece, a conta honesta usa os
**14 aprovados de hoje** — que já incluem o AliExpress, a Kabum e a Nike — e
não os 51 (14 + 37) que a soma sugere.

---

## O QUE A TELA OFERECE, E O QUE A API NÃO ALCANÇA

`Configurações → Links de redes sociais` tem **quatro campos, e só**: Site,
URL do Blog, Nome no Twitter, Página do Facebook. Não há campo de TikTok, nem
de Telegram, nem lugar para um segundo site.

⚠️ **A primeira versão deste arquivo listava dez Espaços Promocionais para
cadastrar. A tela não aceita dez.**

⚠️ **E a API também não alcança** (medido): `/promotionalspaces`, `/websites`
e `/profile` respondem **404** com o nosso token, que só abre `programmes` e
relatórios. Não adianta automatizar o preenchimento — é tela, na mão.

## ⚠️ A ROTA `/parceiros` SOBREVIVE AO PRÓXIMO DEPLOY — E ISSO NÃO É DE GRAÇA

O Pages é **upload direto, e ele substitui o diretório inteiro**. Se a rota
não subisse no mesmo deploy da bio, o deploy seguinte a apagaria **em
silêncio** e o link do perfil da Awin viraria 404 — com a raiz do site no ar,
nova, sem nada indicando o estrago.

⭐ Por isso `publicar_bio.py` sobe as duas **juntas** e **confere a rota
separadamente**: a raiz estar nova não prova que `/parceiros` subiu. A
conferência é pelo **conteúdo** (a frase `search bidding`), nunca pelo `200`.

⚠️ **Não é um projeto novo no Cloudflare:** a conta bateu o teto de **10
projetos** (medido em 14/09). A `/parceiros` vai como **rota** dentro dos
projetos que já existem, e o mesmo endereço serve nos cinco.

⚠️ **O nome do dono saiu do rodapé**: o detector de vazamento do próprio
`publicar_bio.py` reprovou a primeira versão. O anunciante já vê o nome na
conta da Awin.

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

# COMO A CHAVE DE DATAFEED FOI PEGA

> ✅ **Já está no `.env` como `AWIN_FEED_API_KEY`** desde 16/09, e o
> `awin_catalogo.json` prova que funciona (3.063 produtos). Fica aqui
> porque a chave vence e o caminho de volta não é óbvio.

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
