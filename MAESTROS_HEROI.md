# O herói frente aos Maestros — 21/09/2026

Pedido do Bryan (21/09, madrugada): *"é o principal da vitrine, o cliente abre e chega e tá
esse anúncio sem graça, precisamos fazer com que ele deseje comprar, deseje clicar. Consulte
o +acervo e descubra o ouro."*

Consultados: `maestros-da-ia` (147.597 fichas), `css-frontend` (Kevin Powell, 5.608 itens) e
os dois irmãos que já estão no repo — `MAESTROS_ESTETICA_DO_SITE.md` (o que a página parece)
e `MAESTROS_DESIGN_DO_SITE.md` (o que ela diz). O cartão foi olhado no print do Bryan e no
código (`paginas/todos.html`, `montar()` do herói, e o CSS `.vitrine`).

---

## ⭐ O OURO, EM UMA FRASE

**O herói é o único cartão do site que nunca passou pela régua dos Maestros — e ele viola
quatro decisões que o próprio Bryan já aprovou.** A auditoria de 18/09 mediu o cartão da
GRADE e o consertou (cartão v2, blocos A+B). O herói-foto nasceu em 21/09, três dias depois,
e herdou nada daquilo. O que faz desejar comprar já existe, medido e aprovado, **um
componente ao lado**.

## 1. O teste do olho meio fechado (Garry Tan, YC) — o herói reprova

Apertando os olhos no print, a ordem de peso é:

```
1º  a foto (jato de água, alto contraste)
2º  "R$ 60,31"           ✓ certo, é o dono da hierarquia
3º  "AliExpress"          ✗ branco sobre vidro escuro, canto superior, alvo do olhar
4º  o nome, apagado       ✗ o que explica o produto é o mais fraco
```

**O terceiro elemento de maior peso da tela é o nome do fornecedor** — a coisa menos
persuasiva do cartão. §1 da estética já tinha mandado o chip da loja ser **neutro** e descer
para o rodapé do cartão; o herói o promoveu a destaque.

## 2. O que o herói mostra × o que a grade mostra

| sinal (todos já medidos e no dado) | cartão da grade | herói |
|---|---|---|
| ★ % de avaliações positivas (`nota`) | ✅ | ❌ |
| `+792 vendidos desde 14/09` (`vendeu`) | ✅ | ❌ |
| recorde — `menor preço em N dias` (`recorde`) | ✅ | ❌ |
| `espere — já esteve a R$ X` (`ja_esteve`) | ✅ | ❌ |
| frete grátis / envio / reputação | ✅ | ❌ |
| 5 selos, fogo, `de olho` | ✅ | ❌ |
| `caiu N%` | só ≥5% | só ≥5% |
| nome + preço + loja | ✅ | ✅ |

O herói diz **nome, preço e fornecedor**. Nenhum dos três decide uma compra. E o anúncio do
print não tem `antes` nem queda ≥5%, então o cartão inteiro se reduziu a duas linhas.

⛔ Isto é uma **regressão contra decisão do dono**: em 18/09 ele próprio trocou "Sendo
acompanhados" (telemetria) por "Mais vendidos" (prova social, *Movers and Shakers*). O herói
não tem prova social nenhuma.

## 3. O nome é de catálogo, não de desejo

"Suporte telescópico pulverizador jardim" descreve a **peça**. O acervo (dropshipping com
Claude, DEMONSTRADO) diz o contrário: a copy sai do **problema ou do estado de ânimo de quem
compra** — *"pergunte quais problemas esse tipo de cliente tem"*. E `engine/titulo_vendavel.py`
existe, está pronto e está **desaconselhado** (7 de 10 voltaram idênticos) — o que reforça que
a resposta não é reescrever 148 títulos, e sim **acrescentar uma linha de benefício** acima do
nome, só no herói, que é UM produto por publicação.

## 4. A placa — Kevin Powell, DEMONSTRADO

A placa verde-oliva é cor **tirada da própria foto**: um terceiro acento que não carrega
significado (§1 da estética: *um acento por cartão*). O acervo do Kevin Powell resolve texto
sobre foto com **escurecimento semi-opaco atrás do texto**, não com uma chapa colorida:

```
background: rgba(0,0,0,.5); color: white
```
> *"let's give this a background of RGBA, black, point five, and a color of white"*
> DEMONSTRADO · *Using CSS Position Absolute* · https://youtu.be/lUaw-AA9HnA?t=403

E, do mesmo acervo, a versão de acessibilidade: *"um fundo escuro ou levemente opaco logo
atrás do texto, como as legendas costumam aparecer"* (AFIRMADO, Ashlee Boyer,
https://youtu.be/qr0ujkLLgmE?t=491).

## 5. ⚠️ A tensão que eu não vou esconder

`MAESTROS_ESTETICA_DO_SITE.md` §1, palavra por palavra:

> O que o acervo **não** sustenta: glass-morphism, brilhos, gradiente no herói, animação
> cinematográfica (...). Vitrine de R$ 20 pede o oposto: **menos**.

O herói de hoje é vidro, tem brilho e tem gradiente. **Isso não quer dizer desfazer o Liquid
Glass** — ele foi decisão separada do Bryan (19/09), e a barra Clear tem contraste medido
(6,42 contra 4,5 exigidos). Quer dizer que **o vidro não pode ser o argumento de venda**: ele
é o recipiente. O acervo é unânime em que o que vende é o sinal, não o acabamento — e o
acabamento nós já temos.

## 6. O herói proposto — nenhuma feature nova, só o que já está no dado

```
[foto grande, sangrando]                    caiu 43%   (quando houver)
┌ escurecimento subindo da base ────────────────────────┐
│ Rega o jardim inteiro sem você segurar a mangueira    │  ← benefício, 1 linha
│ Suporte telescópico pulverizador jardim               │  ← nome, menor e mais fraco
│ ★ 97%  ·  +312 vendidos desde 02/09  ·  menor em 21d  │  ← a linha de sinais da grade
│ R$ 60,31          R$ 89,90                            │
└───────────────────────── [símbolo da loja, neutro] ───┘
```

1. **A linha de sinais da grade entra no herói.** Mesma régua, mesmo dado, zero invenção.
   É o item de maior retorno e o mais barato.
2. **A placa vira escurecimento**, não cor tirada da foto. Um acento por cartão.
3. **O chip da loja vira neutro e desce** — o símbolo de `simbolos_lojas/`, sem borda, no
   rodapé. Cumpre o §1 da estética, que o herói pulou.
4. **Uma linha de benefício** acima do nome; o nome de catálogo desce de peso.
5. **Ritmo de 8** e uma fonte de corpo (Poppins), mono só em número — as mesmas regras 3 e 7
   do cartão v2.

## 7. Ordem, e o que medir

- **Bloco A** (só markup/CSS, nenhuma decisão nova — é aplicar ao herói o que já foi aprovado
  para a grade): 1 + 2 + 3 + 5.
- **Bloco B** (decisão do Bryan, porque é texto novo e não sai do dado): 4, a linha de
  benefício — de onde ela vem, quem escreve, e se passa pelo detector de vazamento.
- **Medir**: `clique_produto.origem='vitrine'` antes e depois. Hoje são 193 visitas em 7 dias
  e 0 vendas; o herói é o primeiro cartão que a pessoa vê, então é onde a agulha se move
  primeiro. ⚠️ Com 193 visitas, diferença pequena não se distingue de ruído — o que se pode
  medir de verdade é **taxa de clique no herói**, não venda.

## 8. O que o acervo manda NAO fazer (e nos poupa de errar)

- ⛔ **Sistema de avaliacoes proprio**: *"nao usar quando a loja estiver comecando do
  zero e ainda nao tiver pelo menos umas 20 a 30 vendas por mes"* (DEMONSTRADO,
  ajudavitor). Com 0 vendas medidas, avaliacao NOSSA seria invencao. O que propomos e'
  diferente e sobrevive a esta guarda: a % positiva e' **da loja**, medida pelo garimpo
  (`evaluate_rate`), e o site diz de quem ela e'.
- ⛔ **Urgencia e escassez fabricadas** (contador, "ultimas unidades"): o acervo so' as
  mostra em funil de anuncio pago, nunca como sinal medido. Aqui seriam mentira, e a
  regua do site e' "Promo so' com queda medida" (16/09).
- ⛔ **Reescrever os 148 titulos**: `engine/titulo_vendavel.py` ja' foi medido e
  desaconselhado (7 de 10 voltaram identicos). O heroi e' UM produto por publicacao --
  uma linha de beneficio ali custa quase nada e nao mexe no catalogo.
