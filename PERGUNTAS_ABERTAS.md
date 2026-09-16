# Perguntas abertas — o que espera conhecimento novo

⚠️ **Este arquivo existe por ordem do Bryan em 16/09/2026:** *"essa questão da
moeda ainda me intriga, vamos pensar melhor sobre isso depois, anote, está
chegando conhecimento novo e vamos consultar em breve muitas coisas, não deixe
esquecer isso"*.

⭐ **O que ele guarda é diferente do `PARA_FAZER_NO_PC.md`.** Lá estão tarefas
— coisas que alguém executa. Aqui estão **perguntas que ainda não têm resposta
suficiente para virar tarefa**, e que morreriam num handoff se ficassem só
espalhadas em "decisões pendentes".

⛔ **Nada sai daqui por decurso de prazo.** Pergunta que some sem ter sido
respondida vira decisão tomada por omissão — que é exatamente o modo como o
padrão ruim se instala. Sai daqui quando for respondida, e a resposta fica
registrada junto.

---

## 1. 🟡 MOEDA PARA QUEM ACESSA DE FORA DO BRASIL

**Estado:** aberta desde 15/09/2026. Bryan em 16/09: *"ainda me intriga"*.

### Como ela costuma ser formulada, e por que essa formulação é fraca

"Mostrar dólar/euro para quem acessa de fora" soa como um problema de
**exibição** — trocar o símbolo e converter pelo câmbio do dia. Se fosse só
isso, já estaria feito.

### ⚠️ A pergunta de verdade é outra, e é de DINHEIRO

Todo preço do catálogo é pedido à API do AliExpress com três parâmetros fixos
(`engine/vitrine.atualizar_preco` e `engine/garimpo`):

```
target_currency = BRL      target_language = PT      country = BR
```

Ou seja: o preço no site é o preço **para um comprador no Brasil**, com o
frete e o imposto daquele destino embutidos na oferta que a API escolheu.
Converter esse número para dólar mostraria ao visitante de fora **um preço
que ele não vai pagar** — e um preço errado é exatamente a coisa que esta
operação passou duas semanas removendo da página.

### As perguntas que precisam de resposta, em ordem

1. **O link de afiliado paga por uma venda fora do Brasil?** Se não paga, a
   moeda é irrelevante: o visitante de fora não é público, é curioso. Se paga,
   ele é receita que hoje está sendo servida com dado errado.
2. **Quanto desse tráfego existe?** Nunca foi medido. A resposta muda a
   prioridade de "fazer agora" para "não fazer nunca". ⭐ Isto é o mais barato
   de responder e deve vir primeiro — é uma leitura do Supabase, não uma
   decisão.
3. **A API aceita `country` variável sem multiplicar chamada?** O
   `productdetail.get` aceita lote de 50 (medido em 15/09). Se o `country`
   for por chamada e não por produto, servir duas moedas custa o **dobro** da
   coleta horária, não o mesmo.

### ⛔ O que NÃO fazer enquanto ela estiver aberta

Converter o preço BRL por câmbio no navegador. É a solução óbvia, é barata, e
é a única que tem chance de mentir: ela produz um número plausível, redondo e
errado, exatamente como o `target_original_price` que foi banido em 15/09.

---

## 2. 🟡 VÍDEO DO PRODUTO — ADIADO, NÃO DESCARTADO

**Estado:** Bryan em 16/09/2026: *"não vamos usar vídeo por enquanto, mas
vamos precisar sim, por hora vamos esperar"*.

⛔ **O Ken Burns foi RECUSADO** ("não ficou legal"). E a nota alta que ele
tirou não defende nada: era nota de **fidelidade** (0,9888), e fidelidade alta
ali é trivial — é a mesma imagem se movendo.

⚠️ **Não montar `engine/video_produto.py`.** O que existe medido, de 15/09:

```
Ken Burns   1080x1920  5,0s  30fps   0,9888   deriva impossivel (a mesma imagem)
Wan 2.2      480x832   4,1s  16fps   0,9646   ancorado no ultimo quadro
LTX          512x704   1,9s  30fps   0,9277   deriva 10x maior
```

⭐ **O que já se sabe e não se deve perder:** o Wan aceita `last_image`;
mandando o último quadro igual ao primeiro, a deriva se contém sozinha. E o
9:16 não é limite do modelo — a saída segue a **proporção da entrada**.

⚠️ **E a guarda de fidelidade não serve para julgar isto.** Os três passaram,
inclusive o LTX com os pincéis se reorganizando. Para reprovar deriva de
detalhe, a base teria de ser a **amplitude entre quadros**, que ninguém
construiu ainda.

---

## 3. 🟡 ACHADINHO DA MADRUGADA

**Estado:** pedido pelo Bryan como "talvez", em 15/09/2026.

Exige duas coisas que não existem: buscar detalhe na API (a série só guarda
`id`, `preço`, `loja`, `data`) e uma **regra de curadoria** — sem ela,
"achadinho da madrugada" é só o post das 3h da manhã, que não é nada.

⚠️ A pergunta que decide: **o que faz um produto ser de madrugada?** Se a
resposta for "nenhuma característica, é só o horário", o recurso não existe.
