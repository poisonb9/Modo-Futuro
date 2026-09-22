# O cartão da grade frente aos Maestros — 22/09/2026

Pedido do Bryan: *"analise profundamente os cards comuns do site … precisamos fazer com que
esses cards sejam uma máquina de venda … quando criamos não tínhamos o conhecimento que
temos hoje"*.

Consultados: `maestros-da-ia`, `css-frontend`, o **Impeccable** (`pbakaus/impeccable`,
atualizado em 21/09 — `reference/typeset.md`, `layout.md`, `craft-floor.md`) e os irmãos que
já estão no repositório (`MAESTROS_ESTETICA_DO_SITE.md`, de 18/09, e `MAESTROS_HEROI.md`, de
21/09). O cartão foi **medido no ar**, a 430 px, elemento por elemento — não lido do CSS.

---

## 1. O cartão de hoje, medido (430 px · cartão de 190 × 435)

```
foto 1:1 .................. 190 × 190              ✓
chip da loja "Ali" ........  9 px / 600            ✗ abaixo do piso de 11 px
nome ...................... 13,5 px / 600, 3 linhas
"+22 vendidos" ............ 11 px / 500   ┐
"☆ 98%" ................... 12 px / 600   ┘        ✗ dois tamanhos para o MESMO papel
preço ..................... 20 px / 700
"R$" ...................... 12 px / 600
gráfico ................... 14 px de altura
legenda ................... 12,5 px, 2 linhas      ✓ (corrigida hoje)
"avise-me se cair" ........ 12 px / 600, 40 px     ✗ alvo de toque < 44 px
```

## 2. O que o cartão JÁ mostra (e é bom)

Estes sinais já existem no dado e já são desenhados quando há: `caiu N%`, preço riscado
(`de`), fogo, frete grátis, envio (UF), vendedores (ML), `recorde` ("menor preço em N
dias"), `espere — já esteve a R$ X`, `novo`, `também em` (o mesmo produto mais barato em
outra loja) e a prova social da loja (% positivas e vendidos).

⭐ **A base é boa.** O problema não é falta de sinal: é hierarquia, piso mecânico e a
ausência da ação.

## 3. O que falta — em ordem de retorno esperado

| # | Falta | Fonte | Por quê |
|---|---|---|---|
| 1 | **Nenhuma ação visível no cartão** | Analista de Loja Virtual (OPINIÃO); decisão do próprio Bryan em 20/09 na capa | O cartão inteiro é link, mas nada parece clicável. Na capa isso já foi consertado com "Comprar agora" e o Bryan disse o porquê: *"a pessoa não sabe que ela tem que clicar"*. A grade tem 90 cartões e nenhum botão |
| 2 | **"você economiza R$ X"** só existe na capa | mesmo caso acima | A grade mostra `↓13%` e o riscado, mas não o número em reais. Percentual é conta; real é decisão |
| 3 | **Chip da loja a 9 px**, antes do nome | Impeccable `craft-floor` (piso de 11 px para texto funcional) | Já apontado em 18/09 ("vai pro rodapé do cartão") e não foi feito |
| 4 | **"+22 vendidos" 11 px vs "98%" 12 px** | Impeccable `typeset.md`: *"adjacent sizes or weights too close to carry different jobs"* | Mesmo papel (prova da loja), dois tamanhos. Ou é um, ou a diferença precisa de função |
| 5 | **"avise-me" com 40 px** | `craft-floor` (alvo de toque) | É a única ação própria do cartão e é a mais difícil de acertar com o polegar |

## 4. O que o acervo manda NÃO fazer (e nos poupa de errar)

- ⛔ **Urgência e escassez fabricadas** ("últimas unidades", contador). O acervo só as mostra
  em funil de anúncio pago. Aqui seriam mentira: a régua do site é "Promo só com queda
  medida" (16/09).
- ⛔ **Avaliação nossa** (estrelas do site). *"Não usar quando a loja ainda não tiver 20 a 30
  vendas por mês"* (DEMONSTRADO, ajudavitor). Com 0 vendas, nota nossa é invenção. A % que
  mostramos é **da loja**, e o cartão diz de quem é. ✓
- ⛔ **Cartões aninhados** e **sparkline no lugar de conteúdo** (`craft-floor`). Nosso gráfico
  escapa dessa regra porque vem com a legenda que diz o número — ele é conteúdo, não enfeite.
- ⛔ **Reescrever os 148 títulos** — `engine/titulo_vendavel.py` já foi medido e
  desaconselhado (7 de 10 voltaram idênticos), e hoje medimos que só 9 dos 148 são feios.

## 5. A ordem proposta

**Bloco A — mecânico, nenhuma decisão nova** (é aplicar ao cartão o piso que a capa já tem):
chip da loja de 9 → 11 px; "+22 vendidos" e "98%" no mesmo tamanho (12,5 px, o degrau da
escala); "avise-me" com 44 px de altura; ritmo de espaçamento em base 4; números tabulares.

**Bloco B — a máquina de venda** (muda o que o cartão faz, não só como parece):
botão "Comprar agora" no cartão, com o mesmo ouro da capa, e "você economiza R$ X" em verde
quando houver queda. ⚠️ Isso cresce o cartão em ~56 px e a grade fica mais longa — é a troca
a decidir.

**Bloco C — decisão do dono:** chip da loja desce para o rodapé do cartão (§1 da estética de
18/09, ainda não feito) e nome de 13,5 → 14,5 px.

## 6. O que medir

`clique_produto` por origem (`vitrine` × `grade`), antes e depois do Bloco B. ⚠️ Com o
tráfego de hoje, diferença pequena não se distingue de ruído — o que se mede de verdade é
**taxa de clique no cartão**, não venda.
