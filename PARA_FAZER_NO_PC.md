# Para fazer assim que estiver no computador

Escrito em 13/09/2026, a pedido do Bryan. **Ordem de cima para baixo: o que
está em cima rende mais, ou piora se esperar.**

Marque com `[x]` o que for fazendo — este arquivo é o combinado.

---

## 🔴 1. Perfil do Awin — É O ÚNICO QUE PIORA ENQUANTO ESPERA

**Onde:** `ui.awin.com` → Conta → Perfil → Visão Geral

⚠️ **Por que agora:** as **29 candidaturas estão sendo avaliadas neste
momento**, e o alerta *"Seu perfil está incompleto"* aparece na tela de quem
decide. Preencher depois **não desfaz uma recusa**.

Cole na descrição:

```
Publisher de conteúdo focado em achadinhos e produtos do dia a dia. Opero cinco canais de vídeo curto no TikTok (beleza, cozinha, fitness, achadinhos gerais e promoções) e um canal no Telegram, todos em português para público brasileiro. Cada canal tem uma página própria listando os produtos que aparecem nos vídeos, com preço, loja e link. Publico diariamente. Divulgação por conteúdo e redes sociais — não faço e-mail marketing, display nem search.
```

⭐ A última frase é a que mais pesa: anunciante já se queimou com afiliado de
cupom e de search bidding. Dizer que você **não** faz isso remove a objeção
antes de ela aparecer.

**E no mesmo painel:**
- `Perfil → Espaços Promocionais` — hoje só existe `oachadinho`. Adicione os
  outros (lista no fim deste arquivo).
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

**Me mandar os nomes** — a troca do lado do motor é uma linha por canal.

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
