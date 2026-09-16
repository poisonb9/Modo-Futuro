# HANDOFF — 16/09/2026, madrugada (23:33 → 07:19 BRT)

Sessão que **travou sem handoff**: às 07:17 BRT a conta devolveu *"organization
has disabled Claude subscription access"* e as duas últimas mensagens do Bryan
ficaram sem resposta. Este arquivo foi reconstruído a partir do transcrito
(`e4ea99ce…jsonl`) na sessão seguinte, às 07:40 BRT. Anterior:
[`HANDOFF_15-09-2026_PARTE4.md`](HANDOFF_15-09-2026_PARTE4.md).

**9 commits** (00:32 → 02:35 UTC) + **`engine/awin.py` editado e NÃO
commitado** (03:26 UTC).

---

## ESTADO NO FECHAMENTO

```
local           ad5d635 + awin.py sujo (catalogo Awin, +163 linhas)
no ar           achadinhototal.pages.dev   142 produtos   258 KB (210 KB de JSON)
Awin            JOINED 1 (Nike BR mid 17652)   PENDING 20   REJECTED 8
```

---

## 1. ⭐ A NIKE, MEDIDA — e o catálogo Awin já lê os feeds

Detalhe em [`AWIN_ESPACOS.md`](../AWIN_ESPACOS.md) (seção "A NIKE BR, MEDIDA").
O que fecha aqui:

```
feeds da Nike       44669 (29 col, 5.447)  +  93360 (35 col, 5.457)   sobrepostos
deduplicado         por aw_product_id, fica a linha MAIS COMPLETA
ate R$ 150          905 produtos   min R$ 59,98        (~370 KB de card)
ate R$ 250        1.268            mediana geral R$ 449,99
inteira           5.457            max R$ 2.599,99      2,2 MB de JSON
```

⛔ **A chave do feed é OUTRA credencial** (`AWIN_FEED_API_KEY`, 32 hex, dentro
da URL de download do Crie um Feed). O `AWIN_TOKEN` dá 500 lá. **Ela passou
por print e por chat** → regenerar no painel antes de colar no `.env`. O
`catalogo()` foi testado passando a chave só na linha de comando; nada gravado.

⛔ **Link sem `awinaffid` paga OUTRA pessoa** (afiliado 13430), com a página
abrindo normal. Sempre `aw_deep_link`, nunca `merchant_deep_link`.

⚠️ `in_stock` veio 1 em 100% dos 5.457 — campo fixo, não usado como garantia.

⚠️ Status no CSV do feed é `active`, não `joined` (filtrar por joined = zero).

---

## 2. AS DECISÕES DO BRYAN SOBRE A SEÇÃO NIKE

1. **Nike vira categoria própria** no site mãe. Dentro dela: bloco até R$ 250 e
   bloco 250+, com "ver mais".
2. **A com selo do C — padrão para TODO produto:** entra sem histórico com selo
   "novo no catálogo"; gradua para gráfico com 3 leituras (`_serie_curta`
   `minimo=3` já faz a trava; o `todos.html` já tem `novo`/`olho` por `pontos`).
3. ⛔ **"Não quero o site lento."** Carregamento inicial igual ao de hoje; o que
   for além baixa **só quando a pessoa clica**. Medido: cada card Nike = 421 B;
   905 cards = 372 KB, quase dobra a página. Não entra na inicial.
4. **50 cards, mais baratos primeiro** — ⭐ **NO TOPO DA CATEGORIA NIKE**, não
   da página principal (esclarecido às 07:19, última mensagem). Depois os 50
   seguintes mais caros. O feed não tem `vendas`, então o critério é preço.

### ⭐ O template JÁ TEM o mecanismo inteiro (`paginas/todos.html`)

```
TETO_VITRINE = 250      tira da lista principal E divide os dois blocos
SO_NO_SEGMENTO          categoria que só existe atrás do menu (hoje: Calçados)
PASSO_BLOCO = 15        "ver mais" dentro da categoria
novo / olho             selo por pontos < 2 / >= 2
```

O item 4 **resolve o conflito** que eu tinha levantado (50 no topo ×
`SO_NO_SEGMENTO`): Nike **segue a regra do Calçados** — fora do rolar
principal, tudo dentro da categoria. Só falta ligar; não escrever mecanismo.

⚠️ Ainda aberto: `PASSO_BLOCO` é 15 e ele pediu blocos de 50 para a Nike.

---

## 3. ⭐ DUAS ORDENS QUE FICARAM SEM RESPOSTA (07:17 BRT)

**a) Pedido de produto na conversa → o melhor de CADA loja.** Complementa a
memória `modofuturo-pedido-sob-demanda`: se o produto existe em várias lojas,
publico **todos os melhores anúncios por canal**; o cliente escolhe na hora
(Brasil rápido × AliExpress barato, e às vezes ele pode esperar). O que vender
fica; os outros saem do ar depois da venda. **É por isso que a operação
precisa de catálogos brasileiros**, e não só do AliExpress.

**b) "Por que ainda não temos Mercado Livre no site?"** Resposta pelos
registros: inscrição feita, `MELI_MATT_TOOL` no `.env`, 5 etiquetas por canal
criadas, atribuição **provada** (1 clique contado em 15/09). O que faltou foi a
**fonte**: `mais_vendidos` do ML devolve papel higiênico e Elseve — farmácia de
marca, não achadinho — e em 15/09 ficou "ML pede busca dirigida por produto, é
outro trabalho". Ninguém marcou como próximo passo. ⭐ **O item (a) é a busca
dirigida.** ML entra pelo caminho do pedido sob demanda, não pelo garimpo
automático.

---

## 4. ERROS MEUS DESTA SESSÃO

⛔ **Aconselhei pôr `oachadinho.pages.dev/parceiros` no campo Site do Awin**,
contradizendo a decisão registrada de 15/09 (`achadinhototal`). O Bryan clicou
antes de eu ler o `AWIN_ESPACOS.md`. Ele corrigiu às 00:25. **Ler o registro
antes de aconselhar campo que julga candidatura.**

⛔ **Afirmei 325 produtos até R$ 150 e mínimo R$ 89,99** — era um feed só. Com
os dois deduplicados: **905 e R$ 59,98**.

⛔ **Chutei a página em ~60 KB; medido: 258 KB.** Estimativa minha entrou numa
recomendação de desenho antes da medição.

⚠️ **Sessão de 8 h sem handoff intermediário.** Se a conta caísse 1 h antes,
o esclarecimento das 07:19 teria morrido com ela.

---

## 5. O QUE CONTINUA ABERTO

1. 🔴 `AWIN_FEED_API_KEY` regenerada no `.env` (a exposta não vale).
2. 🔴 Ligar a área Nike (item 2) — mecanismo pronto, faltam `canal="Nike"`,
   `SO_NO_SEGMENTO += "Nike"`, `origem: awin` no `produtos_todos()`, `PASSO_BLOCO`
   50 para a Nike, e a Nike no `guardar_preco()` desde a 1ª rodada.
3. 🔴 Awin: 10 anunciantes BR nunca pedidos; Clovis Calçados (8.198 produtos).
   Encaminhar os 6 e-mails de recusa (PF × perfil).
4. 🟠 ML por busca dirigida (item 3b) — ligado ao fluxo sob demanda.
5. Os itens 3–13 da PARTE4 continuam.
