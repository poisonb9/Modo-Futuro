# HANDOFF — 14/09/2026, tarde e noite

Sessão longa, quase toda em **página e catálogo**. A operação ganhou um
**site mãe** e o gargalo mudou de novo: saiu de "não temos produto" e virou
**"o produto não tem imagem boa nem vídeo"**.

---

## 🚨 AS ARMADILHAS QUE ME PEGARAM

### 1. `target="_blank"` era o defeito maior da página — e ficou dias invisível

O Bryan reportou que **nada clicava** no iPhone: nem cartão, nem a linha do
topo, nem "toque para ver na loja". Eu tinha "provado" que funcionava com
`preventDefault` no teste — que é justamente o que esconde o problema.

O navegador disse a causa quando cliquei de verdade:

> *the page tried to open a new tab and the pane **BLOCKED it***

Abrir aba nova é tratado como **pop-up**, e o bloqueador do Safari vem ligado
de fábrica. **O link sempre funcionou — a aba é que não abria.**

> ⭐ Teste que usa `preventDefault` prova que o listener roda, **não** que o
> link abre. Para provar navegação, tem de navegar.

### 2. `200` não é prova de que a rota existe

`/todos` respondia **200** e servia a **bio**: o Cloudflare Pages devolve a
página raiz com 200 quando o caminho não existe. Eu dei por publicado e o
deploy nem tinha acontecido.

> ⭐ A prova de rota é **uma marca que só aquela rota tem**. Status nunca.

### 3. Um passo que não publica estava segurando a publicação

O `git push` para o repo `bio` (que é **arquivo**, não publica nada) abortava
com `check=True` **antes** do deploy. O catálogo ficou fora do ar por causa
de um passo irrelevante para o visitante.

> ⭐ Ordem de prioridade: primeiro o visitante, depois o arquivo.

### 4. `403` não queimava a chave no anel do Gemini

Só `429` queimava. Com 28 chaves, uma rodada inteira morreu em
`PERMISSION_DENIED` enquanto **minutos antes** outras chaves do mesmo anel
respondiam 200. E o cache só gravava no fim, então essa rodada jogou fora
tudo o que já tinha custado cota.

### 5. `\n` em heredoc — de novo

Escrevi `\n` dentro de um f-string via heredoc e virou quebra de linha real →
`SyntaxError`. **Está na memória permanente e me pegou mesmo assim.**

---

## O QUE FICOU NO AR

### O site mãe — **https://achadinhototal.pages.dev**

A raiz **é o catálogo**, com a lupa e sem canal na frente. Criado apagando o
reservado `treinodefora` (0 deploys, conferido antes) — a conta do Cloudflare
bate o teto de **10 projetos**.

⚠️ Nome tomado na Cloudflare **não dá erro**: ela cria com sufixo aleatório.
Só o `subdomain` da resposta prova. O nosso saiu limpo.

| endereço | raiz | `/todos` | `/parceiros` |
|---|---|---|---|
| `achadinhototal` | **catálogo** | — | sim |
| os 5 de canal | bio do canal | catálogo | sim |

### O catálogo

```
66 produtos · 64 com nome curto · 60 com combinação julgada
filtros: Tudo · Caiu de preço · Achados novos · Sendo acompanhados · Mais baratos
chips por ÁREA (Beleza, Cozinha, Eletrônicos, Casa, Fitness)
```

⚠️ **O site mãe não fala de canal.** Decisão do Bryan: quem abre a casa da
operação não precisa saber que há cinco TikToks por trás — é estrutura nossa,
não informação de quem compra.

### A copy, medida contra checklist

Veio do acervo dos Maestros (Nick Saraev, DEMONSTRADO):
`giving · micro commitment · social proof · authority · rapport · scarcity`.

⚠️ **Divergi do acervo em uma:** a ficha demonstra escassez fabricada (timer
de 90s, "só restam 150 cópias"). Numa página cujo único diferencial é o preço
ser **verificável**, isso queima o que sustenta tudo. A nossa escassez é real:
o preço muda, e o que está ali é o de hoje.

### O upsell

Aparece no **`pageshow`** — quando a pessoa **volta** da loja. Não intercepta
o clique: o caminho da compra continua com **um** clique.

⚠️ `pageshow` e não `load`: voltando pelo botão "voltar" o Safari restaura do
bfcache e `load` **não dispara**.

Quem julga o que combina é o **Gemini** (`engine/combina.py`), em cache por id.
A regra de palavras (Jaccard ≤ 0,25) ficou como reserva.

### O garimpo ampliado

```
termos    27 → 97        por canal  5 → 8
ordem     _potencial = ganho por venda × volume na loja
```

⚠️ **Ampliar a busca não é baixar o filtro**: `serve()` continua igual.

### Nomes de produto para gente

`engine/nome_produto.py` — Gemini primeiro, OpenRouter como reserva, e a
**regra que sustenta tudo**: todo número do nome novo tem de existir no
original. Nome que não passa é descartado e cai no corte do título.

---

## 🔴 O QUE ESTÁ ABERTO — em ordem

### 1. A imagem do produto (o Bryan não gostou do FLUX)

**MEDIDO:** o Cloudflare Workers AI funciona com o `CF_API_TOKEN` que já temos:

```
@cf/black-forest-labs/flux-1-schnell            200
@cf/bytedance/stable-diffusion-xl-lightning     200
@cf/stabilityai/stable-diffusion-xl-base-1.0    200
```

⚠️ E o Gemini de imagem **não** é falta de cota: `gemini-2.5-flash-image`
devolve **403 PERMISSION_DENIED** ("your project has been denied access"), e
`gemini-3-pro-image` dá 429 em 8 chaves seguidas.

**O que o Bryan pediu, e eu ainda NÃO fiz:** *"não quero criar uma imagem
nova, quero pegar a imagem do anúncio e deixar ela premium e dentro do nosso
contexto, às vezes escrever nelas"*. Isso é **img2img**, não geração do zero —
testar `stable-diffusion-xl` com imagem de referência.

⚠️ E a razão de fazer assim é a certa: imagem inventada é **ilustração**, não o
produto. Um sérum genérico bonito no lugar da foto real entrega outra coisa.

### 2. Vídeo de produto — o AliExpress NÃO serve

**MEDIDO em 14/09:** apenas **1 de 40** produtos (2%) tem `product_video_url`.
A ideia de usar o vídeo do vendedor morreu na medição.

⚠️ E **vídeo do YouTube também não serve** — ver o item 3: para 83% do
catálogo não há como verificar que é o mesmo produto.

⭐ **O caminho que sobra é o motor que já existe:** `main.py` monta 9:16 com
legenda no timing do áudio, narração com voz clonada e a cascata CTA. Falta a
matéria-prima visual — foto + movimento de câmera resolve, sem IA generativa e
sem pagar nada.

### 3. ⛔ VÍDEO DO YOUTUBE PARA O PRODUTO — **decidido: NÃO**

O Bryan levantou a ideia e ele mesmo pôs o limite: *"não posso correr o
risco de pôr vídeo do produto errado, é preferível nem ter"*.

**MEDIDO em 14/09/2026, nos 66 produtos do catálogo:**

```
11 têm marca/modelo identificável   (Lenovo GM2, KZ EDX PRO, TP300...)
55 são genéricos                    "Organizador de maquiagem giratório 360°"
```

⚠️ **Para 83% do catálogo a verificação é impossível.** "Organizador
giratório 360°" existe em centenas de versões quase idênticas, de dezenas de
lojistas. Um vídeo do YouTube mostraria *um* organizador, não **o** que a
pessoa vai receber — e ela descobre quando abre a caixa.

⚠️ **E o segundo problema é pior que o primeiro:** vídeo de terceiro em post
comercial. O canal já tomou corte de alcance por integridade/autenticidade em
02/08 e ainda está reconstruindo.

⭐ **A alternativa é melhor, não é consolo.** A foto do anúncio é, por
definição, do produto certo: vem do mesmo lojista, do mesmo link que a pessoa
vai abrir. É o mesmo raciocínio do preço — *o desconto é NOSSO, medido contra
o que nós vimos*. Aqui: **a imagem é a do produto que vai chegar**.

⭐ E a mesma imagem tratada serve ao cartão **e** ao vídeo: um trabalho, dois
lugares.

### 4. Radar de canais no YouTube (pedido, não feito)

O Bryan pediu para procurar canais que ensinem o que estamos fazendo — vitrine
de afiliado, UGC, conversão. O acervo dos Maestros cobre **produção**; sobre
**vender por canal próprio** ele tem 4 fichas e todas são sobre configurar bot.

### 5. O que continua travando dinheiro (de sempre)

- **`tracking_id` por canal** — a tabela está pronta e comentada em
  `engine/garimpo.py`; falta criar os ids no Portals e rodar
  `teste/fumaca_tracking.py`
- **Awin** — 28 pendentes, 1 recusa. Motivo medido: *"o site não complementa a
  marca do anunciante"*. O `/parceiros` existe para resolver isso
- **Mercado Livre** — 16% contra 7%. ⏰ **Lembrete agendado para 20:00 de
  14/09** (`Lembrete_MercadoLivre`, Telegram)
- **Shopee** — dados de pagamento no banner vermelho

---

## Estado medido no fechamento

```
37 commits hoje · local e remoto no mesmo ponto
catálogo: 66 produtos no ar
guardas verdes: teste_garimpo, teste_resultado, teste_nome_produto,
                teste_vitrine_produtos_reais, teste_medidor_da_contra_capa,
                teste_nomes_definidos, teste_workflows_completos
```

⚠️ Sujos que **não** devem ser commitados (mudam sozinhos, tarefa agendada):
`radar_modofuturo.json`, `estado/baixados_em_intervalos.json`,
`estado/videos_trabalhados.json`, `relato_*.txt`,
`paginas/avatares/logo_app_aliexpress_100.png`
