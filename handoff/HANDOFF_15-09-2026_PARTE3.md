# HANDOFF — 15/09/2026, parte 3 (depois do /clear e do reinício)

Terceira sessão do mesmo dia. As duas anteriores estão em
[`HANDOFF_15-09-2026.md`](HANDOFF_15-09-2026.md) (imagem, vídeo, provedores,
radar) e [`HANDOFF_15-09-2026_NOITE.md`](HANDOFF_15-09-2026_NOITE.md) (a queda
falsa e as 7 armadilhas).

**9 commits.** O catálogo saiu de **63 para 149 produtos**, ganhou **101
gráficos de preço**, e dois defeitos do motor foram encontrados — os dois por
acidente, como o desconto falso de ontem.

---

## O QUE ESTÁ NO AR AGORA

```
achadinhototal.pages.dev   carimbo 5adedcf056b8   149 produtos   8 categorias
                           101 gráficos de série · 2 produtos acima de R$ 250
5 bios                     carimbo 2558efab9503
```

⚠️ **O navegador serve a versão em cache.** Na primeira conferência ele me deu
13 em "Casa" — número do catálogo velho — enquanto o `curl` trazia 34. Conferir
**sempre pelo `curl` e pelo carimbo**, nunca pelo que a aba mostra.

---

## 1. ⭐ O GRÁFICO DA SÉRIE — publicado, e a escala é a decisão inteira

O desenho que revelou o desconto falso virou parte do cartão, no catálogo e na
bio. **41 de 63 produtos desenham** hoje (eram 15 antes do garimpo rodar).

⛔ **O eixo NÃO se ajusta ao mínimo e máximo da série, e isso é contra-intuitivo.**
Sparkline auto-ajustada transforma oscilação de 1,6% numa montanha: o Carregador
120W (36,59 · 36,59 · 37,19) sairia com a mesma cara dramática da Lanterna, que
caiu 12,2% de verdade. Seria a mentira de ontem outra vez — **tinta inflada no
lugar de número inflado**.

⭐ Por isso o eixo tem **piso de 10% do preço**: quem não se mexeu sai quase
reto, quem caiu ocupa a altura toda. Conferido na tela, nos dois casos e nos
dois temas.

⛔ **Mínimo de TRÊS dias.** Com dois pontos o desenho é um *segmento*: sempre
sobe ou sempre desce, com a mesma inclinação convincente, tenha o preço oscilado
0,5% ou 40%. Desenhar isso seria inventar com tinta o que `_queda_real` se
recusa a inventar com número.

⭐ **Uma leitura só para o desenho e para a queda.** `_precos_por_dia()` foi
extraída de `_serie_de_precos()` sem mudar a conta — provado id a id (2.241
iguais) e com o catálogo idêntico campo a campo. Se o desenho consolidasse por
conta própria, poderia mostrar uma linha que a queda não confirma: ferramenta de
auditoria com caminho próprio audita a si mesma, não o dado.

Custo medido: **+4,4 KB de código por página** (uma vez só) e **14,6 bytes por
produto**. O cartão já custa 1,45 KB cada.

Guarda: `teste/teste_grafico_serie.py`, com o caso negativo que importa (seis
leituras de anúncios diferentes em três dias não podem virar pico) **e prova de
sensibilidade** — o mesmo predicado roda contra a série sem consolidação e tem
de reprovar.

---

## 2. ⛔ O GARIMPO NÃO RODAVA — e era o cron no minuto cheio

Descoberto ao investigar por que a série parava em 14/09.

```
cron '0 11'        duas execuções agendadas em toda a história do workflow
13/09  disparou 14:45   (3h45 de atraso)
14/09  disparou 16:43   (5h43 de atraso)
15/09  NÃO RODOU        (medido às 14:57 UTC)
```

⛔ E **não era a plataforma**: no mesmo dia a fila rodou às 11:55 e o desempenho
de hora em hora. O minuto cheio é o mais disputado do GitHub.

⭐ Trocado para `'23 10'` e a rodada de hoje disparada na mão. Resultado
imediato, e é ele que mostra o tamanho do estrago:

```
série ganhou 15/09 com 2.042 leituras
gráficos                    15 → 41
cartões com selo "caiu" e SEM gráfico     21 → 0
```

⚠️ **O segundo número é o que importa.** Havia 21 cartões dizendo "caiu 18%" sem
nenhuma linha sustentando — o selo afirmava com 2 leituras e o desenho se
recusava a desenhar com 2. A incoerência sumiu sozinha quando a série ganhou
mais um dia. **Dia sem rodada é dia que não entra na série, e não se coleta
depois.**

---

## 3. 🚨 O ERRO DE MEDIÇÃO QUE ME PEGOU DUAS VEZES NO MESMO DIA

**O `id` sai da página como TEXTO e mora na série como INTEIRO.**

Primeira vez: cruzei os dois direto e concluí que **"os 62 produtos do catálogo
não existem na série de preços"** — defeito gravíssimo, e falso. Cruzando como
texto: 62 de 62. A página sempre esteve certa; quem errou foi a medição.

Segunda vez, horas depois: `len(pd.get(str(i), {}))` numa tabela de chaves
inteiras devolveu **"0 dias de série" em 125 de 125**. Com a chave crua: 86 dos
125 já desenhariam gráfico no primeiro dia.

> ⚠️ Nos dois casos o número era **plausível e catastrófico** — e erro que
> assusta é o que menos se questiona. Está salvo na memória permanente como
> `modofuturo-id-do-catalogo-e-texto`.

E uma terceira, da mesma família: li `124` como "124 produtos sobreviveram ao
dedupe" quando era **código de saída do `timeout`**. Campo errado, valor
plausível.

---

## 4. ⛔ DOIS DEFEITOS DO MOTOR, achados por acidente

### 4a. `rende_video` cortava produto no MEIO DA PALAVRA

O corte era `termo in titulo`, substring solta. MEDIDO sobre 111 candidatos
reais: **7 dos 8 cortes eram falsos**, todos por "ração" (de animal):

```
"Caixa de som bluetooth, vibração"   ->  vib(ração)
"Clipes de Liberação Rápida"         ->  libe(ração)
"Luzes de tira led ... decoração"    ->  deco(ração)
"Lanterna com liberação rápida"      ->  libe(ração)
```

⛔ Isso vinha **apagando produto em silêncio** desde sempre: o cartão só não
aparecia. E o pior — a guarda certa existia **duas linhas abaixo**, na lista de
marcas, com o comentário que descreve exatamente este defeito: *"filtro que casa
demais reprova o que deveria passar, e isso é invisível — o produto só some"*.
A proteção existia para as marcas e não para a reposição.

⭐ O conserto é **prefixo** (`\btermo`), e não `\btermo\b`: ancorando nos dois
lados, "fralda" deixaria de casar com "fraldas" e o filtro erraria para o outro
lado. Guarda nova com os dois lados — 6 falsos positivos têm de passar, 5 casos
verdadeiros (mais um no plural) têm de continuar sendo cortados.

⚠️ **Como apareceu:** a peneira caiu na lista de palavras porque as chaves do
OpenRouter estavam sem cota. A rede funcionou como projetada — e foi ela que
revelou o defeito.

### 4b. `duplicata` perdia 18 minutos de rede

O cache de vetores só era gravado no fim. Uma rodada de 124 produtos levou
**18,6 minutos**, a tentativa anterior morreu num `timeout` de 15 e perdeu os
122 vetores já buscados. Agora grava a cada 10.

---

## 5. O CATÁLOGO TRIPLICOU — 87 produtos da varredura

O motor **já tinha visto** muito mais do que publicou. O funil, todo medido:

```
2.259  produtos que o motor já viu (varredura larga, desde 12/09)
   67  já publicados alguma vez
1.293  nunca publicados que passam no filtro básico (nota 90+, 300+ vendas, R$ 10-250)
  125  desses com potencial (ganho x vendas) ACIMA da mediana do catálogo
  124  resgatados pelo productdetail.get (1 id não existe mais)
  111  após dedupe pela FOTO (13 fundidos; fica sempre o mais barato)
  110  após o corte editorial
   87  após teto de 4 por categoria
```

⭐ **O teto por categoria foi o que resolveu de verdade.** A peneira editorial
julga UM título por vez, então ela não vê que há seis organizadores de cabo
diferentes na lista — cada um, sozinho, é legítimo. **Seis soluções para o mesmo
problema não são seis achados.** "Acessórios para celulares" caiu de 15 para 4.

⚠️ E o dedupe pela foto provavelmente está **certo** em não fundir esses seis:
velcro, silicone, fita e braçadeira são produtos distintos. O limiar 0,93 é
apertado de propósito, porque fundir dois diferentes apaga um achado.

### ⚠️ A varredura não respeita os nossos canais

Ela trouxe **26 peças de carro, jardim e ferramenta**, que nenhum dos cinco
canais cobre. Em vez de enfiá-las em "Casa" (fazendo a categoria mentir sobre o
que tem dentro), entraram três pseudo-canais com área própria: **Carro, Jardim,
Ferramentas**.

⚠️ Não há bio de carro nem de jardim — esses 26 vivem no catálogo do site mãe e
em vitrine nenhuma. Decisão do Bryan: um dia podem ser redirecionados a um canal.

```
Eletrônicos 41 · Casa 34 · Fitness 21 · Carro 18
Beleza 15 · Cozinha 12 · Jardim 4 · Ferramentas 4
```

⭐ `onde: "varredura"` e não `"garimpo"`: o registro fica honesto sobre o fato de
que ninguém escolheu estes a dedo.

⚠️ **Consequência aceita pelo Bryan:** como são os mais novos, os 12 itens da
seção "No Achadinho Total" — que aparece nas CINCO bios — são hoje todos da
varredura. Os do garimpo de hoje de manhã saíram de lá.

---

## 6. A VITRINE GANHOU TETO — preparando o calçado de marca

A Nike aprovou no Awin (seção 8), e isso obrigava uma decisão antes de o
primeiro tênis entrar.

⛔ **O problema é automático:** a lista abre ordenada por `ganho x vendas`. Um
tênis rende ~R$ 37 por venda contra ~R$ 2 de um achadinho — então o primeiro par
assumiria a frente sozinho e empurraria todo achadinho para baixo. **Ninguém
teria decidido isso.**

```
teto R$ 250        tira da lista padrão QUALQUER produto acima disso
SO_NO_SEGMENTO     a categoria Calçados inteira só existe atrás do menu,
                   cara ou barata
```

O teto saiu de medição: mediana do catálogo R$ 30,99, maior R$ 231,99. R$ 250
pega todo tênis de marca (R$ 400-700) e não escondia **nenhum** achadinho que já
estava rodando. R$ 150 tiraria o Projetor de R$ 231,99, que tem queda medida e
rende vídeo — efeito colateral, não objetivo.

⭐ **O mesmo número divide os dois blocos dentro da categoria**, 15 por bloco com
"ver mais" próprio, e o **barato vem primeiro**. Um número, dois usos.

⭐ **Os títulos são factuais** — "Até R$ 250" e "Acima de R$ 250". "Premium /
Básico" foi recusado pelo Bryan com o argumento certo, o mesmo que derrubou "De
marca": rótulo de status só existe por contraste, e "básico" carimbaria 62 dos 63
itens do catálogo. O nome da seção também mudou por isso — **"Calçados"**, um
tipo de coisa, e não um nível.

⭐ **Navegar é passivo, buscar é intenção.** Quem escolheu a categoria ou digitou
"nike" vê tudo; o recorte existe só para quem rola a página sem pedir nada. E a
busca passou a casar também com a **categoria** — antes, digitar "calçados"
devolvia vazio, porque os nomes são "Tênis Nike Air Force 1".

⚠️ **TRÊS lugares aplicam o recorte**, e não um: a grade, o **cartão do topo**
(que pesca "os 8 que mais caíram" e traria o tênis sozinho para a primeira tela)
e a **contagem do seletor** (que diria "tudo 67" sobre uma grade de 63).

### ⭐ A categoria ganhou ENDEREÇO

`/#calcados`, `/#fitness`, `/#eletronicos` abrem já filtrados. Antes havia UMA
url para o catálogo inteiro e não dava para mandar ninguém direto a uma
prateleira — nem pela bio, nem pela descrição do vídeo.

⛔ **O valor da url nunca é escrito na página.** Ele é só COMPARADO com as
categorias existentes; o que não casar abre o catálogo normal. Endereço que vira
texto na tela (`innerHTML`) é porta de injeção.

⚠️ E isso **não esconde nada de ninguém**: os produtos já estão todos no fonte
da página. Tirar da lista principal é decisão **editorial**, não segredo — por
isso endereço "criptografado" não protegeria nada e só quebraria o link que se
dita num vídeo.

Guarda: `teste/teste_vitrine_teto.py`. Provada nos dois sentidos — abrindo um
furo no recorte do cartão do topo ela reprova.

---

## 7. O REGISTRO DAS QUEDAS FALSAS FOI REESCRITO

`estado/produtos_publicados.jsonl` ainda guardava as quedas calculadas pelo
histórico antigo. A página recalcula, então o ar estava certo; quem lesse o
arquivo direto via número que não existe.

**23 dos 170 registros mudaram, TODOS para baixo** — nenhum subiu, que é o
esperado, porque o defeito só inflava:

```
51,9% -> 0,0%   Termômetro TP300        34,0% -> 0,0%  Fone Lenovo GM2 Pro
49,0% -> 4,2%   Conjunto de pincéis     32,1% -> 0,0%  Carregador 120W
```

⭐ Reescrito pelas **mesmas funções do publicador**, não por conta paralela:
conta paralela seria um segundo lugar para divergir. Conferido campo a campo —
só `queda` difere, ordem de campos igual, sem escape unicode novo, newline final
igual, e o `git diff --numstat` bate 23/23 por fora.

---

## 8. AWIN — a Nike aprovou, e a recusa do Carrefour é de outra espécie

Em **29 horas** a fila andou muito (contra o instantâneo guardado de 14/09):

```
             14/09      15/09
JOINED           0          1     ⭐ Nike BR (Sportswear)
PENDING         28         20
REJECTED         1          8
```

⭐ **A Nike é a primeira aprovação da operação.** Conferido na resposta crua da
API, não no nosso resumo: `membershipStatus: "Joined"`, `status: Active`,
`linkStatus: online`, `deeplinkEnabled: true`, e o `clickThroughUrl` já vem com
o PID 3089205 — **o mesmo PID que aparece no e-mail de recusa do Carrefour**, o
que confirma que é a conta certa.

```
comissão     7,5% base  ·  14% em cinco linhas de SKU
             Dunk · Air Force 1 · Court Vision · Shox · P-6000
KPIs da rede EPC R$ 1,28/clique · conversão 3,33% · aprovação 77,5%
             validação 33 dias · pagamento ~47 dias
```

⚠️ **Esses KPIs são da rede inteira, não nossos.** São afiliados de review de
tênis e comparador de preço, cujo visitante já está decidindo comprar Nike. Não
dá para assumir 3,33% para nós.

⚠️ **A janela de cookie a API não entrega** — não está em nenhum dos três
endpoints. Só no perfil do programa, dentro do painel. É justamente o número que
mais nos machuca hoje (AliExpress tem 24h).

### ⛔ A recusa do Carrefour não se conserta com página

> **"O anunciante não trabalha com afiliado pessoa física."**

Compare com a da 365Rider (*"o site não complementa a marca"*), que era defeito
nosso e já foi consertado. **São duas causas diferentes, e das 8 recusas só
essas duas têm motivo conhecido.**

🔴 **A pergunta que decide dinheiro e continua aberta:** o MEI destrava 6
anunciantes ou 1? Os outros 6 (adidas, Calvin Klein, Motorola, Authentic Feet,
Allianz, Zee Now) têm motivo desconhecido — a API não entrega o porquê, só o
e-mail. **Encaminhar os e-mails de recusa responde isso antes de abrir CNPJ com
amostra de um.**

⛔ Não reenviar pedido para nenhum dos 8 antes de saber o motivo.

---

## 9. MERCADO LIVRE — etiquetas prontas, e o `mais_vendidos` NÃO vale

⭐ **As cinco etiquetas existem**, conferidas na tela do painel contra
`engine/mercadolivre.ETIQUETAS`:

```
truque.importado  achadinhomake   ✅     fatura.chora  pagomenos  ✅
cozinha.importada achadinhochef   ✅     atefalhar     atefalhar  ✅
achadinhos.inst.  instantaneos    ✅     (sem canal) bryanexpand  ✅
```

O link sai `?matt_word=<canal>&matt_tool=87181766`. **Nada a fazer no código.**

⚠️ Sobraram **4 duplicatas** que o motor nunca vai usar —
`achadinhosinstantaneos`, `cozinhaimportada`, `faturachora`, `truqueimportado`.
Vão ficar em ZERO para sempre, e o risco não é técnico: é ler o relatório daqui
a um mês, ver `faturachora: 0 vendas` e concluir que o canal não vende. ⭐ Apagar
as 4 (nenhuma venda passou por elas). ⛔ **Não apagar `bryanexpand`.**

### ⛔ `do_mercado_livre()` existe e nunca foi chamada — e está certo assim

Medido: `engine/garimpo.py:891` tem a função pronta, com faixa de preço por
canal, etiqueta e peneira editorial. **Zero chamadas no motor inteiro**, e 170
de 170 produtos publicados são AliExpress.

Testei sem publicar. A peneira matou papel higiênico e fralda como devia, mas o
que **sobrou** foi Cicaplast, CeraVe, Elseve, perfume da Turma da Mônica.
**Farmácia de marca, não achadinho** — ninguém descobre o Elseve num vídeo.

⭐ O que vale no ML é a faixa de **GANHOS EXTRAS** (até 26%, quase 4x o
AliExpress), e isso pede **busca dirigida por produto**, não lista de mais
vendidos. É outro trabalho.

---

## 10. SHOPEE — o item era um e na verdade são TRÊS

### ⭐ 1. Dados fiscais: ENVIADOS às 12:43, "Avaliação Pendente"

Ficaram dias travados com o botão `Enviar` apagado. A causa era um obrigatório
**vazio escondido atrás do resumo**: o número da casa tinha sido digitado em
**Complemento**, e o campo **Número** estava em branco. O resumo montava "Al dos
Mandarins, 500 - ..." puxando do complemento, então a linha parecia certa.

> ⭐ **A lição, que vale além da Shopee:** resumo de formulário é **derivado**.
> Ele pode estar completo com um campo obrigatório vazio. Conferir o resumo não
> é conferir o formulário — mesma família do "200 não prova nada".

⚠️ Regra que derruba o cadastro DEPOIS do envio: nome completo e nome da mãe
**sem acento e sem abreviação**.

### 🔴 2. Carteira Maree: FALTA, e é ela que recebe

Apareceu só depois do envio dos dados fiscais. Ativa-se **no app**, não no
painel:

```
app Shopee -> ícone "Eu" -> Maree -> "Ativar agora"
   código por WhatsApp · PIN · documento dos ÚLTIMOS 10 ANOS (CNH costuma passar)
   validação até 3 dias úteis
pagamento automático todo dia 10 · mínimo R$ 30 · saída por PIX
```

⚠️ Tem de ser a **mesma conta Shopee do afiliado** (`bryanarchives@gmail.com`,
ID `18331841315`), senão a comissão vai para a carteira errada.

### 🔴 3. API: chamado de suporte, sem resposta há dias

Não é formulário de developer com aprovação automática. **Sem App ID + Secret
não há `engine/shopee.py`** — a palavra "shopee" aparece no repo em dois lugares
e os dois são texto. Texto de cobrança pronto no chat da sessão.

---

## 11. DECISÕES DO BRYAN NESTA SESSÃO

```
gráfico da série         fazer agora e PUBLICAR
registro das quedas      reescrever, com cópia antes
cron do garimpo          trocar e disparar a rodada de hoje
seção de calçados        nome "Calçados" (não "De marca": marginalizava o resto)
teto de vitrine          R$ 250, por preço (não por fonte)
regra B                  a categoria Calçados inteira fora da lista padrão
blocos                   "Até R$ 250" / "Acima de R$ 250", barato PRIMEIRO
os 87 da varredura       publicar TODOS, criando categorias novas
                         e deixar entrar nas bios
```

---

## 12. 🔴 O QUE CONTINUA ABERTO

1. ⛔ **`tracking_id` por canal no Portals** — o ÚNICO irreversível. Venda que
   entrar antes fica sem canal **para sempre**. Os cinco nomes são os mesmos já
   criados no ML, de propósito.
2. 🔴 **Awin, hoje à noite:** colar `Site` = raiz e `URL do Blog` = `/parceiros`
   (nunca foi colado — ver `PARA_FAZER_NO_PC.md` item 1), **e** pegar a **chave
   de datafeed** na mesma visita. O `AWIN_TOKEN` atual responde **500** em
   `productdata.awin.com/datafeed/list`: são chaves diferentes. Sem ela, a seção
   de calçados é curadoria manual, um link por vez.
3. 🟠 **Shopee:** ativar a Maree; cobrar o chamado da API.
4. 🟠 **Awin:** encaminhar os 6 e-mails de recusa para classificar PF × perfil.
5. **A moeda para quem está fora do Brasil.** A mãe do Bryan abriu de Portugal:
   a página mostra R$ e o AliExpress mostrou €. ⛔ **Converter seria inventar um
   preço** — o valor para PT é outro (frete, imposto, às vezes outro vendedor),
   não é câmbio. Três caminhos: não fazer nada / ⭐ avisar quem está fora
   (detectável pelo fuso do navegador, sem dado pessoal) / catálogo por país.
   **Decisão pendente.**
6. **A caixa de estatística conta o acervo inteiro** e a linha de baixo conta a
   lista na tela. Com o recorte ligado isso aparece mais ("149 achadinhos de pé"
   sobre uma grade de 147). Não é defeito novo, mas incomoda mais agora.
7. **As 4 etiquetas duplicadas no ML**, para apagar no painel.
8. `engine/video_produto.py` e `engine/imagem_premium.py` continuam no
   scratchpad (handoff da manhã).
9. **Terceira perna do ModelScope** em `nome_produto.py` e `combina.py`.
10. **Arte do Achadinho Chef**, **endereço do Até Falhar**, **links de bio**.

---

## 13. REGRAS QUE ESTA SESSÃO CONFIRMOU OU ACRESCENTOU

⛔ **O `id` do catálogo é TEXTO e o da série é INTEIRO.** Cruzar direto dá "0 de
62" e parece defeito gravíssimo. Aconteceu duas vezes hoje.

⛔ **Número plausível vindo do campo errado** — `124` era código de saída do
`timeout`, não contagem. Mesma família do desconto falso.

⛔ **Guarda com alarme falso é pior que guarda nenhuma.** A primeira versão do
`teste_vitrine_teto` reprovava por causa de um "R$ 250" escrito dentro de um
**comentário**. Corrigida para olhar só o código.

⛔ **`git add` de arquivo ignorado é recusado, e o `&&` curto-circuita em
silêncio** — o commit do conserto do `duplicata` não aconteceu na primeira
tentativa e eu quase segui em frente.

⭐ **Detector precisa de prova de sensibilidade, não só de caso negativo.** A
guarda do teto foi validada abrindo um furo de propósito no recorte do cartão do
topo: ela reprovou, e só então voltou ao verde.

⚠️ **O `garimpo.yml` diz que esta máquina não alcança os gateways do AliExpress**
(timeout de TLS, medido em 12/09). **Hoje ela alcança**: `productdetail.get`
respondeu em 2,3 s daqui. Ou era outro endpoint, ou mudou — o comentário está
desatualizado.

⚠️ **`engine/aliexpress.py` e `engine/garimpo.py` não chamam `load_dotenv()`**.
Funcionam na nuvem, que injeta as variáveis, e estouram `SemCredencial` numa
chamada local direta. Carregar o `.env` na mão antes de testar.
