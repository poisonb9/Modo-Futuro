# Para fazer assim que estiver no computador

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
- `Perfil → Espaços Promocionais` — hoje só existe `oachadinho`, e foi ele
  que causou a recusa medida. **Os dez espaços estão prontos pra colar em
  [`AWIN_ESPACOS.md`](AWIN_ESPACOS.md)**, com tipo, endereço e descrição.
  ⚠️ A API não alcança isto (404 medido em 14/09) — é tela.
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

## 🟠 3. Afiliados do Mercado Livre — 16% parados

**Onde:** `www.mercadolivre.com.br/l/afiliados-home` (logado como BRYANEXPAND)

⚠️ Não é `/afiliados` — esse joga para o login sem explicar. O endereço certo
é `/l/afiliados-home`.

⭐ **16% de comissão contra 7% do AliExpress**, pagamento na conta Mercado
Pago que você já tem, entrega em **2 dias** em vez de 3 semanas. O app da API
já funciona; falta só a inscrição no programa.

⚠️ **O cookie é de 24h** — curto para o funil `vídeo → perfil → bio → loja`.
A chamada do clipe precisa gerar clique **no mesmo dia**.

⚠️ E existe **pagamento por visualização** (até R$ 30 mil) a partir de **10
mil seguidores** no TikTok ou Instagram. O maior canal tem 58. É receita que
não depende de ninguém comprar nada — e agora tem um número concreto de meta.

---

## 🟠 4. Shopee — dados de pagamento e fiscais

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
https://www.tiktok.com/@cozinha.importada
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
