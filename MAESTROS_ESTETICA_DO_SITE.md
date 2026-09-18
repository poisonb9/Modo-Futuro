# Avaliação estética do site frente aos Maestros — 18/09/2026

Pedido do Bryan (18/09, 13:10): *"o sino de emoticon por algo mais premium… alguma coisa na
apresentação da caixa de produto… simples mas ainda mais bonito. Consulte a fundo o que os
mentores falam sobre isso."* Terceira consulta do dia à skill `maestros-da-ia` (63.970
fichas), desta vez só sobre **forma**: 314 fichas de design/UI (233 DEMONSTRADO ·
69 AFIRMADO · 12 OPINIÃO), mais os vídeos inteiros de crítica de interface — YC "Design
for Startups" (Garry Tan), YC "Critiquing Startup Mobile Apps" e "Critiquing AI Startup
Websites", "How to Fix AI Slop with Claude Design", "Top 10 Claude Code Frontend Design
Skills", Analista de Loja Virtual EP.6–7. O cartão foi olhado no iPhone do Bryan (print de
13:07) e no código (`paginas/todos.html`, CSS das linhas 419–590).

Irmão de `MAESTROS_DESIGN_DO_SITE.md` (o que a página *diz*); este é sobre o que ela *parece*.

---

## 1. Os princípios que o acervo repete — e o que eles dizem do nosso cartão

| Princípio | Fonte | Base | No nosso cartão |
|---|---|---|---|
| **Ícones e emojis monocromáticos, na cor da paleta** — emoji renderiza diferente em cada aparelho | NICK_SARAEV (apps com Claude); AILABS ("remova todas as cores e emojis"); YC mobile ("emojis pouco claros") | DEMONSTRADO ×2, OPINIÃO | O 🔔 é o único emoji da tela. Nós mesmos já tiramos o 🔥 por isso em 16/09 ("saiu grande e solto") — a estrela e a chama já são SVG na cor do texto. O sino é o que sobrou |
| **Teste do olho meio fechado**: o elemento de maior peso tem de ser o que importa | YC Garry Tan | OPINIÃO | Passa no preço (Archivo Black 17,5px) ✓. Mas em volta dele há 5 coisas do mesmo cinza e do mesmo tamanho (conferido às, nota, espere, sino, radar) — ruído de peso igual |
| **Remover ornamento que não carrega significado** (linhas, bordas, dois-pontos) | YC Garry Tan | OPINIÃO | A linha do gráfico quando é reta é ornamento; o ponto verde pulsando "no radar há 2 dias" é telemetria nossa, não decisão de compra |
| **Uma fonte de exibição só; corpo 16–18px; evitar Inter** | TristenOBrien (AI slop) | DEMONSTRADO | Temos TRÊS famílias no mesmo cartão: Archivo Black (preço), Poppins (nome), JetBrains Mono (tudo o mais, a 10px). Mono a 10px em 5 linhas = cara de terminal, não de vitrine |
| **Página neutra; cor forte só em ponto de foco; sem gradiente** | TristenOBrien | DEMONSTRADO | Paleta é boa (ouro da lupa, sem roxo) ✓. Mas o cartão carrega 3 acentos: ouro (caiu), verde (novo/nota/pulso), vermelho (chip "Ali"). O chip vermelho ao lado do título lê como aviso de erro |
| **Espaçamento em múltiplos de 8; nada apertado** | TristenOBrien | DEMONSTRADO | Corpo do cartão: 11/12/7px. Perto, não é |
| **Texto secundário com contraste baixo → escurecer** | YC mobile | OPINIÃO | `--fraco` a 10px no claro (#6f6b7d sobre #fff) fica no limite; no escuro (#a5a1b4) melhor |
| **Alvo de toque ≥ 60px; ação principal com cor, secundárias neutras** | YC mobile | OPINIÃO ×2 | O "avise-me" tem ~22px de altura e fonte 10px: difícil de tocar no polegar. E é a ÚNICA ação do cartão além de abrir a loja |
| **Suavizar aparecer/sumir (fade/slide)** | YC mobile | OPINIÃO | Temos no hover/active ✓ |
| **Tipografia moderna e legível** como item nº 1 da estética de loja | Analista EP.6 | OPINIÃO | Poppins e Archivo Black são escolha com intenção ✓ — o problema não é a fonte, é quantas |
| **Elemento de assinatura + risco estético justificável** | Claude Code skills (18/09 do acervo) | DEMONSTRADO | A lupa dourada e o "Eu garimpo" são a assinatura ✓. O risco estético hoje é o mono — e ele está do lado errado (na telemetria, não no preço) |
| **Quadro de inspiração com 4–5 sites e as impressões** antes de pedir mudança | TristenOBrien | DEMONSTRADO | Não temos. Sugestão de referência (o próprio acervo cita): Amaro (fotos grandes + avaliações), Stripe (Skill UI), "Jack Dorsey: clean, elegant, interactions" |

O que o acervo **não** sustenta: glass-morphism, brilhos, gradiente no herói, animação
cinematográfica (fichas de vibe coding de SaaS — DEMONSTRADO em outro produto). Vitrine de
R$ 20 pede o oposto: menos.

## 2. O cartão de hoje, linha a linha (print de 13:07, mobile)

```
[foto 1:1]                      ✓ boa; selo "caiu" em ouro só quando há queda ✓
Nome do produto (Poppins 13)    ✓
[Ali] chip vermelho              ✗ 3º acento; lê como erro; vai pro rodapé do cartão
preço conferido hoje às 12:06   ✗ telemetria (MAESTROS_DESIGN §3.5); vira `title`
☆ 97%                           ✓ mas 10,5px mono — merece 12px
R$ 211,71 (Archivo Black)       ✓ o dono da hierarquia
espere · já esteve a R$ 207,51  ~ certo existir; mono 10px o esconde
[🔔 avise-me quando cair]        ✗ emoji + 22px de alto + 10px mono
────────•  (gráfico)             ✗ ornamento quando reto; some no cartão, fica no ?p=
● no radar há 4 dias             ✗ telemetria nossa
(vazio)                          ✗ o Cortador tem um buraco entre nome e preço: o preço é
                                   empurrado pro fundo (`margin-top:auto`) e o cartão vizinho
                                   mais alto abre o vão
```

## 3. O cartão proposto — "simples, mas mais bonito"

Sete coisas, todas subtração ou troca; nenhuma feature nova:

1. **Sino em SVG monocromático** (traço 1,5px, cor `--fraco`, 16px), como a estrela e a
   chama já são. Zero emoji na tela.
2. **"avise-me" vira botão de verdade**: largura total do cartão, 40px de altura, borda
   1px `--linha`, cantos 10px, Poppins 600 12px, ícone + "avise-me se cair". Neutro (é ação
   secundária; a primária é tocar o cartão). No card com `espere`, é ele que resolve o
   "não compre" — o texto vira "avise-me se voltar a R$ 207".
3. **Uma fonte de corpo**: Poppins em toda frase (nome, espere, avise-me, rodapé). Mono
   fica **só para números tabulares** — preço riscado, %, data — que é onde mono tem
   função. Tamanhos: frases 12px, números 11px, nada abaixo de 11.
4. **Um acento por cartão**: ouro para "caiu"; verde só na nota quando há fogo; o chip da
   loja vira **neutro** (cinza, ou o símbolo oficial de `simbolos_lojas/` sem borda) e desce
   para a linha do rodapé. ⚠️ Tensão com a decisão de 16/09 ("selo de canto na cor da loja"):
   a cor da loja pode ficar no **símbolo**, não numa borda vermelha ao lado do título.
5. **Sai do cartão, vai pro `?p=`**: "preço conferido hoje às 12:06" (vira `title` do preço),
   "no radar há N dias", e a linha do gráfico quando não há queda ≥ 5%. O cartão diz o que
   decide compra; o resto está a um toque.
6. **Sem vão**: nome → nota/loja → preço → estado → botão, em fluxo; o botão é que gruda no
   fundo (`margin-top:auto` nele, não no preço). Cartões vizinhos ficam com a mesma altura
   pela grade, mas o vazio some entre nome e preço.
7. **Ritmo de 8**: corpo 12px/16px, gaps 8px, foto com cantos 12px por dentro.

Em texto, o cartão vira:

```
[foto]  caiu 43%
Nome do produto em duas linhas
★ 98%  ·  [símbolo da loja]
R$ 211,71   R$ 367,92
espere — já esteve a R$ 207 há 4 dias        (só quando existe)
[ 🛎 avise-me se voltar a R$ 207 ]           (botão 40px, neutro)
```

## 4. Fora do cartão (o que o mesmo acervo aponta, para depois)

- Herói: os números agora falam do visitante ✓ (18/09). O "Eu garimpo. / Você paga menos."
  passa no squint ✓.
- Rodapé: ícones das redes no rodapé (Analista EP.6–7) — falta o @ dos canais.
- Busca "mais proeminente" (YC mobile) — a nossa já é ✓.
- Quadro de inspiração: 4–5 referências com impressões antes da próxima rodada visual
  (Amaro, Stripe, um catálogo minimalista, um app de preço tipo Zoom/Buscapé no que NÃO fazer).

## 5. Ordem que eu proporia

Bloco A (uma tarde, só CSS/markup, sem risco): 1 + 2 + 3 + 7.
Bloco B (decisão do Bryan por causa da tensão do 16/09): 4 + 5 + 6.
Medir depois: cliques no "avise-me" antes/depois (Supabase `clique_produto.origem='avise'`),
que é a única métrica que o cartão gera hoje.
