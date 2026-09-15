# Para fazer assim que estiver no computador

⚠️ **ATUALIZADO EM 14/09/2026 (noite).** O que mudou nesta sessão está em
[`handoff/HANDOFF_14-09-2026_NOITE.md`](handoff/HANDOFF_14-09-2026_NOITE.md)
— site mãe no ar, catálogo com 66 produtos, e o gargalo agora é **imagem e
vídeo do produto**.

⚠️ **O lembrete `Lembrete_MercadoLivre` pode ser desligado** (corrigido em
15/09): ele cobrava a *inscrição*, que **já estava feita**. O que sobrou no
item 3 é outra coisa — criar as **etiquetas por canal** no painel.

Escrito em 13/09/2026, a pedido do Bryan. **Ordem de cima para baixo: o que
está em cima rende mais, ou piora se esperar.**

Marque com `[x]` o que for fazendo — este arquivo é o combinado.

---

## ✅ 0. O RÓTULO DE IA — JÁ ESTÁ MARCADO (conferido em 14/09/2026)

⚠️ **Este item estava errado.** O grep de 13/09 procurou por `rotulo` e por
isso não achou nada — o campo não se chama assim.

**O que foi medido agora:**

- `agendar_buffer.py:489` manda `metadata.tiktok.isAiGenerated = True` em
  **todo** post, sem condição nenhuma. Está no código desde 25/08/2026.
- `enfileirar()` é a **única** função do motor que cria post — os outros seis
  arquivos que falam com a API do Buffer só **leem**. Não há caminho por fora.
- A regra 3 do cabeçalho do módulo já dizia isso; a interface do Buffer não
  expõe o campo, mas a API expõe.

⭐ Ou seja: **todo clipe que sai pelo motor já nasce rotulado.** O risco de
conta por aqui não existe.

**O que sobra, e é menor:** clipe postado **na mão**, fora do Buffer. Já
aconteceu uma vez (`agendar_buffer.py:370` guarda o rastro: clipe tirado da
fila por ter sido postado sem rótulo). Aí quem marca é você, no app.

⚠️ E vale lembrar o que o handoff de 08/09 mediu: **o rótulo não explica o
corte de alcance de 02/08.** Ele entrou no código e a recuperação não veio
dele — a causa medida foi **duplicata**. Marcar continua sendo obrigação de
plataforma; só não é a alavanca de alcance que a gente achou que fosse.

---
## 🔴 1. Perfil do Awin — É O ÚNICO QUE PIORA ENQUANTO ESPERA

⚠️ **MEDIDO EM 15/09/2026** (`python -m engine.awin`), contra o instantâneo
guardado de 14/09 — em **29 horas** a fila andou muito:

```
             14/09      15/09
JOINED           0          1     ⭐ Nike BR (Sportswear)
PENDING         28         20
REJECTED         1          8
```

⭐ **A NIKE APROVOU.** É o primeiro anunciante da operação inteira, e é
Sportswear — cai no **Até Falhar**. O motor já monta link de Awin
(`engine/awin.py:66`, `link(destino, id_anunciante)`).

⛔ **E a recusa do Carrefour é de OUTRA ESPÉCIE** (e-mail de 15/09):

> **O anunciante não trabalha com afiliado pessoa física.**

⚠️ Isso **não se conserta com página, perfil nem descrição** — é sobre ser
PF. Compare com a da 365Rider (*"o site não complementa a marca"*), que era
defeito nosso e já foi consertado. São duas causas diferentes, e das 8
recusas só essas DUAS têm motivo conhecido.

🔴 **O que decide dinheiro, e ainda não está respondido:** o MEI destrava 6
anunciantes ou 1? Os outros 6 (adidas, Calvin Klein, Motorola, Authentic
Feet, Allianz, Zee Now) têm motivo desconhecido — a API **não** entrega o
porquê, só o e-mail. Encaminhar os e-mails de recusa responde isso antes de
abrir CNPJ com amostra de um.

⛔ **Não reenviar pedido para nenhum dos 8** antes de saber o motivo:
reaplicar com o mesmo perfil recusado queima a relação.

**Onde:** `ui.awin.com` → Conta → Perfil → Visão Geral

⚠️ **MEDIDO EM 14/09/2026** (`python -m engine.awin`, não é estimativa):

```
JOINED      0
PENDING    28
REJECTED    1   <- 365Rider (Sportswear)
SUSPENDED   0
```

⚠️ **A fila começou a ser julgada.** Ontem eram 29 pendentes e **zero**
recusas; hoje a primeira recusa entrou.

⭐ **E o motivo veio no e-mail** (print do Bryan, 14/09) — não foi perfil
incompleto:

> **O site não complementa a marca do anunciante**

⚠️ **Isso aponta pra outra coisa, e mais barata de consertar.** A 365Rider
é *Sportswear*. O único Espaço Promocional cadastrado é `oachadinho`, que é
de achadinhos e beleza. Quem avaliou abriu uma página que não conversa com a
marca dele e recusou — com razão.

⭐ Ou seja: **cadastrar os outros Espaços Promocionais deixou de ser item de
arrumação e virou o conserto da causa medida.** Anunciante de esporte
precisa ver a página do *Até Falhar*; o de beleza, a do *Truque Importado*.
São 28 decisões ainda em aberto olhando pra página errada.

⚠️ A API **não** entrega o motivo — só a relação (`pending`/`rejected`).
O porquê só chega no e-mail do Awin.
⭐ Dá pra reconferir a qualquer momento, sem abrir o painel:

```bash
python -m engine.awin
```
Cole na descrição:

```
Publisher de conteúdo focado em achadinhos e produtos do dia a dia. Opero cinco canais de vídeo curto no TikTok (beleza, cozinha, fitness, achadinhos gerais e promoções) e um canal no Telegram, todos em português para público brasileiro. Cada canal tem uma página própria listando os produtos que aparecem nos vídeos, com preço, loja e link. Publico diariamente. Divulgação por conteúdo e redes sociais — não faço e-mail marketing, display nem search.
```

⭐ A última frase é a que mais pesa: anunciante já se queimou com afiliado de
cupom e de search bidding. Dizer que você **não** faz isso remove a objeção
antes de ela aparecer.

**E no mesmo painel:**
- **A tela só aceita UM site** (conferido na print, 14/09): `Configurações →
  Links de redes sociais` tem Site, Blog, Twitter e Facebook — só isso. Então
  o conserto é o endereço mostrar a operação inteira, e não cadastrar mais
  endereços. Ver [`AWIN_ESPACOS.md`](AWIN_ESPACOS.md).
- `Configurações → dados de pagamento` — ⚠️ sem isso a comissão **acumula e
  não sai**.

---

## 🔴 2. tracking_id por canal no AliExpress — NÃO SE RECUPERA DEPOIS

**Onde:** `portals.aliexpress.com` → Ad Center → Tracking ID → criar um por canal

```
achadinhomake      (truque.importado)
achadinhochef      (cozinha.importada)
instantaneos       (achadinhos.instantaneos)
pagomenos          (fatura.chora)
atefalhar          (atefalhar)
semanestesia       (semanestesia.pod)
modofuturo         (modofuturo)
```

⚠️ **Hoje existe UM só** (`default`) para a operação inteira. Consequência: a
primeira venda vai entrar dizendo *"a operação vendeu"*, não *"o canal Y
vendeu"*. **Venda que entrar antes da troca fica sem canal para sempre** — é
igual ao histórico de preço, não se coleta depois.

⭐ É o que decide **onde investir esforço**: se um canal vende 10x mais que
outro, isso muda quantos clipes cada um recebe por semana.

**Me mandar os nomes.** ✅ **O lado do motor já está pronto** (14/09): a
tabela `TRACKING` em `engine/garimpo.py` espera os nomes **comentada**, e
`buscar()` já pede `tracking_de(canal)`. Descomentar é tudo.

⭐ E é **um lugar só**: o `promotion_link` já vem carimbado com o id que a
busca pediu, então não há segundo ponto pra esquecer.

⚠️ **Ficam comentados de propósito até existirem no Portals.** Id que não
existe devolve link que **abre a página normalmente e não paga** — pior que
não ter. Assim que criar, rode `python teste/fumaca_tracking.py` com os nomes
novos: ele tenta um por um e só o válido passa. Guarda:
`teste/teste_tracking_por_canal.py`.

---

## ✅ 3. Mercado Livre — A INSCRIÇÃO JÁ ESTÁ FEITA (corrigido em 15/09/2026)

⚠️ **Este item estava errado.** Dizia "falta só a inscrição no programa". **A
inscrição está feita**, o painel de afiliado existe e responde, como
BRYANEXPAND.

**MEDIDO em 15/09**, não suposto:

```
MELI_MATT_TOOL     87181766     id de ferramenta de afiliado, ja' no .env
MELI_MATT_WORD     bryanexpand
token da API       200
/trends/MLB        200   bolsa feminina, ofertas, chuveiro, cadeira gamer...
mais_vendidos()    devolve produto com preco e link JA' com a tag
```

⭐ **E a atribuição está PROVADA.** O painel mostra `Cliques 1 · Pedidos 0` nos
últimos 7 dias — é o link que o Bryan abriu em 13/09, montado pelo nosso
motor. O sistema **contou**. O modo de falha mais caro (link que abre a página
e não atribui nada) está descartado por registro do próprio ML.

### ⛔ O QUE O ML NÃO É — e a puxada provou

`mais_vendidos("MLB1246")`, categoria **Beleza**, devolveu:

```
Papel Higienico Folha Tripla    R$ 16,00
Papel Higienico Toque da Seda   R$ 13,89
Protetor Solar FPS 70           R$ 67,97
Perfume Cebolinha Jequiti       R$ 45,90
```

⛔ **Não é fonte de achadinho.** Os mais vendidos dele são a cesta de compras
do país; ele NÃO substitui o AliExpress no garimpo. O que dá de único é (1)
comissão alta em produto escolhido a dedo e (2) `trends/MLB`, que é **pauta**,
não produto.

### ⭐ A comissão é MELHOR do que este documento dizia

Visto no hub em 15/09 — existe faixa de **GANHOS EXTRAS**:

```
Chinelo Kenner        26%    <- quase 4x o AliExpress
Lavadora Lava Jato    16%
Tenis Kappa           16%
Creatina              12%
```

⚠️ Mas são produtos que **o ML escolheu mostrar**. O teto de 26% é real; a
média no nosso público não foi medida.

### ✅ AS ETIQUETAS JÁ FORAM CRIADAS (conferido em 15/09/2026)

Conferido na tela do painel contra `engine/mercadolivre.ETIQUETAS`: as
**cinco** que o motor usa existem, mais a `bryanexpand` de "sem canal".

```
truque.importado          achadinhomake   ✅      fatura.chora   pagomenos   ✅
cozinha.importada         achadinhochef   ✅      atefalhar      atefalhar   ✅
achadinhos.instantaneos   instantaneos    ✅      (sem canal)  bryanexpand   ✅
```

O link sai `?matt_word=<canal>&matt_tool=87181766`. **Nada a fazer no
código.**

⚠️ **Sobraram 4 duplicatas que o motor NUNCA vai usar** —
`achadinhosinstantaneos`, `cozinhaimportada`, `faturachora`,
`truqueimportado`. São o mesmo canal com o outro estilo de nome, e vão ficar
em ZERO para sempre. O risco não é técnico: é ler o relatório daqui a um mês,
ver `faturachora: 0 vendas` e concluir que o canal não vende. ⭐ Apagar as 4
no painel (nenhuma venda passou por elas). ⛔ **Não apagar `bryanexpand`** —
foi ela que registrou o clique de 13/09.

### O que era este item antes — `Administrar etiquetas`

No hub existe a ferramenta **`Administrar etiquetas`**. Ela é o equivalente do
`tracking_id` por canal — **e resolve, pelo lado do ML, o único item
irreversível da lista** (item 2): venda que entrar sem etiqueta fica sem canal
para sempre.

⭐ **O motor já está a um parâmetro de distância.** `com_afiliado()` monta
`?matt_word=<word>&matt_tool=<tool>`, e o `matt_word` é o campo de
rastreamento — hoje fixo em `bryanexpand`. Trocar por `achadinhomake`,
`achadinhochef`, `instantaneos`, `pagomenos`, `atefalhar` separa a venda por
canal.

⚠️ **NÃO inventar o nome da etiqueta antes de criá-la no painel.** Mesma
armadilha do AliExpress: id que não existe devolve link que abre a página e
não paga — **pior que não ter**. Criar primeiro em `Administrar etiquetas`,
depois usar exatamente os nomes criados.

### ⛔ Campanhas de vídeos — FECHADO, exige 10 mil seguidores

Conferido na tela em 15/09 (`/l/afiliados-videos-sem-redes`):

> *"Para participar, você precisa ter 10 mil seguidores."*

E cumprir o requisito **não garante**: depende de avaliação de perfil e
conteúdo, e de vagas vigentes. O maior canal tem 58. É meta, não tarefa.

### ⚠️ O cookie continua sendo a trava real

**24 horas.** Curto para o funil `vídeo → perfil → bio → loja`: a venda de
sábado sobre um clipe de quinta NÃO é nossa. Não se conserta no código — se
conserta na chamada do clipe, que precisa gerar clique **no mesmo dia**.

---

## 🟠 4. Shopee — dados de pagamento ENVIADOS em 15/09/2026

⭐ **O formulário foi enviado.** Ficou dias travado com o botão `Enviar`
apagado, e a causa era um campo obrigatório **vazio escondido atrás do
resumo**: o número da casa tinha sido digitado em **Complemento**, e o campo
**Número** estava em branco. O resumo montava "Al dos Mandarins, 500 - ..."
puxando do complemento, então a linha parecia certa e o formulário não.

> ⭐ **A lição, que vale para além da Shopee:** o resumo de um formulário é
> DERIVADO. Ele pode estar completo com um campo obrigatório vazio — e foi
> exatamente o que aconteceu. Conferir o resumo não é conferir o formulário.

⚠️ Regra da Shopee que derruba o cadastro DEPOIS do envio: nome completo e
nome da mãe **sem acento e sem abreviação** (`Antonia`, não `Antônia`).

🔴 **E APARECEU OUTRA EXIGÊNCIA, fora do painel de afiliados:** assim que os
dados fiscais entraram, a tela passou a pedir *"ative sua conta Maree para
receber a comissão"*. A **Maree é a carteira digital** onde a comissão de
pessoa física cai — sem ela a comissão é calculada, aprovada e não tem para
onde ir.

```
app Shopee -> ícone "Eu" -> Maree -> "Ativar agora"
   código por WhatsApp · dados · PIN · biometria (opcional)
   documento: CNH ou RG EMITIDO NOS ÚLTIMOS 10 ANOS
   validação: até 3 dias úteis
```

⚠️ **Duas armadilhas:** (1) o documento precisa ser dos últimos 10 anos — RG
antigo cai aqui, CNH costuma passar; (2) a Maree tem de ser ativada na MESMA
conta Shopee do afiliado (`bryanarchives@gmail.com`, ID `18331841315`), senão
a comissão vai para a carteira errada.

⭐ Depois de ativa: pagamento automático **todo dia 10** na carteira, mínimo
de **R$ 30** acumulados, e a saída para o banco é PIX pela Maree.

⚠️ **Isto não estava em nenhum handoff** porque só aparece DEPOIS de enviar
os dados fiscais. O item "Shopee" era um só e na verdade são três: dados
fiscais, carteira Maree, e API.

🔴 **O que continua aberto: a API.** O pedido foi um **chamado de suporte**
("Quero ativar a API", ID de afiliado `18331841315`, conta
`bryanarchives@gmail.com`), não um formulário de developer com aprovação
automática — e está sem resposta há dias. Sem App ID + Secret não há
`engine/shopee.py`: a palavra "shopee" aparece no repo em dois lugares e os
dois são texto.

### O que era este item antes

**Onde:** `affiliate.shopee.com.br` → o banner vermelho no topo

⚠️ Sem isso a comissão é calculada e **não sai**, mesmo de link feito na mão.
O pedido de Open API já foi enviado e está em análise — mas **não é ele que
trava dinheiro**; é este banner.

---

## 🟡 5. A arte do Achadinho Chef

`siga_cozinha.importada.png`, no mesmo padrão cromado dos outros.

⭐ Ele **já está na lista** de canais com cascata e é pulado
automaticamente — entra sozinho no dia em que o arquivo existir, sem ninguém
editar código.

⚠️ O canal vira **@achadinho.chef em 26/09**, então a arte já pode nascer com
o nome novo.

---

## 🟡 6. Colar o link da bio nos seis canais que faltam

Só o **Pago menos** tem o link na bio hoje. Os outros seis têm a página no ar
e ninguém chega nela.

```
Achadinho Make            oachadinho.pages.dev
Achadinho Chef            achadinhochef.pages.dev
Achadinhos Instantâneos   achadinhodehoje.pages.dev
Até Falhar                (falta escolher o endereço — 5 reservados)
Sem Anestesia             meulivro.pages.dev  ⚠️ só depois da Kiwify
Modo Futuro               (sem destino hoje — não vale a linha)
```

⚠️ **O Sem Anestesia não deve entrar ainda:** o livro não está à venda e o
cartão da página sai desligado. Prometer na bio o que a página não entrega é
o erro mais caro dos três, porque quem clica é quem mais confiava.

---

## 🟡 7. Endereço do Até Falhar

Cinco reservados: `otreinodehoje` · `treinodefora` · `atefalhar` ·
`achadinhofitness` · `treinoquefunciona`. Escolha um e eu publico.

---

## ⚪ 8. Decisões que só você toma

- **CNPJ / MEI** — já barrou o Magalu e pode barrar o Mercado Livre em outras
  frentes
- **Livro na Kiwify** — destrava o `meulivro.pages.dev` e a linha da bio do
  Sem Anestesia
- **Instagram** — a Meta pediu horas pela conta ser nova; quando liberar,
  criar o app e me mandar App ID + Secret
- **Os @ do Instagram** de cozinha, fatura.chora e atefalhar

---

## O que a máquina faz sozinha enquanto isso

**Todo dia às 11h**, sem você:

```
garimpo por canal     escolhe produto, anota o que escolheu e o ganho previsto
varredura             21 termos largos alimentam o histórico de preço
campeões              acompanha pelo ID quem vende muito
tendência             quem está ACELERANDO e quem apareceu já grande
vigia                 PS5, smartwatch, SSD e mais 7
pedidos + placar      lê vendas reais do AliExpress
commit                nada se perde no runner efêmero
```

E todo clipe novo sai com a cascata **CURTA · COMENTE · SIGA**.

---

## As URLs, para não ter que procurar

```
https://www.tiktok.com/@truque.importado
https://www.tiktok.com/@cozinha.internacional
https://www.tiktok.com/@achadinhos.instantaneos
https://www.tiktok.com/@fatura.chora
https://www.tiktok.com/@atefalhar
https://www.tiktok.com/@semanestesia.pod
https://www.tiktok.com/@modofuturo
https://t.me/achadinhototal
https://oachadinho.pages.dev
https://achadinhochef.pages.dev
https://achadinhodehoje.pages.dev
https://pagomenos.pages.dev
```

---

## 🟡 9. Higgsfield MCP — olhar, não contratar

⚠️ **É pago por crédito**, então isto é "ver se vale", não "ligar".

**O que existe:** o MCP foi registrado no projeto em **06/08/2026** e **nunca
foi autenticado**. Está parado há mais de um ano.

⭐ **O buraco que ele fecharia:** o garimpo acha o produto, mas **não temos
vídeo DO produto**. Hoje o achadinho entra no Telegram e na página como texto
e foto; os clipes são cortes de vídeo de terceiros. O Achadinho Make não tem
imagem do sérum que recomenda.

O fluxo está DEMONSTRADO no acervo dos Maestros (vídeo de 19/05/2026): foto +
descrição do produto → vídeo UGC de 15s em 9x16 → publicar.

⚠️ **Três coisas antes de contratar:**
1. Não sei se o MCP ainda funciona — precisa de sessão nova para autenticar
2. Custo **por vídeo**, diferente do corte, que é grátis
3. Vídeo de IA com produto real **exige rótulo** — ver o item 0
