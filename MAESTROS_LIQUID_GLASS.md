# Liquid Glass no Achadinho Total — a autópsia (19/09/2026)

Fonte: skill `liquid-glass` (11.872 itens, 1.128 vídeos, 12 fontes) lida
inteira pela ferramenta do projeto; 553 itens são de web/CSS/SVG, o resto é
shader (three.js/WebGL), Framer, Spline, After Effects. Este arquivo é o que
SOBRA depois de passar tudo pelo nosso caso: site estático, 98% do público
no **iPhone/Safari** vindo do TikTok, fundo claro, ouro como cor de marca.

## 1. A decisão que manda em todas as outras: Safari

- "Evite usar o componente liquid glass em páginas que serão abertas no
  Safari, pois o efeito não será renderizado corretamente" (Fundo, DEM).
  O que não renderiza é a **refração por SVG** (`feDisplacementMap` /
  `feTurbulence` via `filter: url(#…)` sobre backdrop): só Chrome. Firefox
  também não. Logo: **refração SVG está fora**. Nada de "vidro que distorce
  o que está atrás".
- O que o Safari faz bem, e é o que a Apple mesma faz no iOS 26 em CSS-land:
  `backdrop-filter: blur() saturate()` com `-webkit-` (e `!important` quando
  a especificidade briga — item DEM do iPhone Safari), sombras internas
  brancas como especular, borda em gradiente de 3 paradas, camada de
  "frost" atrás do texto.
- Refração de verdade só com WebGL (Yuri Artiukh, 3.199 itens) — custo alto,
  máquina do visitante, bateria. Não para uma vitrine de R$ 13.

## 2. O material (receita fechada, Safari-safe)

| camada | valor | de onde |
|---|---|---|
| fundo do vidro | `rgba(255,255,255,.55)` claro / `rgba(30,28,36,.6)` escuro — sem cor de fundo o blur não aparece (DEM) | Fundo, LiquidGlass |
| desfoque | `backdrop-filter: blur(24px) saturate(160%)` + `-webkit-` | Fundo (10–25px, saturate 150–200%) |
| especular de topo | `inset 0 4px 8px rgba(255,255,255,.7)` (mais fino em elementos pequenos: `inset 0 1px 0 #fff`) | Fundo DEM |
| brilho de cantos | `inset -1px -1px 1px -1px rgba(255,255,255,.7)` + `inset 1px 1px 1px -1px rgba(255,255,255,.7)` | Fundo DEM |
| borda curva de luz | stroke 1px em gradiente de 3 paradas brancas: 5% / opaco / 5%, direção baixo-esq → cima-dir | Fundo DEM (o "highlight band que sugere vidro curvo") |
| sombra externa | `0 12px 40px rgba(60,45,10,.14)` (tingida de ouro, nunca preto puro) | Fundo + Impeccable |
| frost para texto | camada extra `rgba(255,255,255,.35)` atrás de texto pequeno | WWDC + Fundo |
| Clear × Tinted | Clear só sobre luz forte; por padrão **Tinted** (a Apple recuou no 26.1 por legibilidade) | Fundo (26.1), Apple |
| contraste | texto normal ≥ 4.5:1, ícone/borda ≥ 3:1 sobre o vidro | W3C WAI, LiquidGlass |
| movimento | `prefers-reduced-motion` respeitado; `translate3d` nas animações | W3C, Fundo |
| Firefox | sem backdrop: fallback sólido `@supports not (backdrop-filter: blur(1px))` | Fundo |

Regra de ouro tirada da lista: **vidro precisa de luz atrás**. Sobre branco
chapado o material some. Por isso o fundo da página deixa de ser chapado:
duas luzes douradas fixas e suaves (gradientes, não imagem) — é o que o
vidro "refrata".

## 3. O que isso muda no site (por partes, nesta ordem)

1. **Fundo + tokens do material** (`--vidro-*`), aplicados ao console.
2. **Barra de abas inferior em vidro** (a metáfora do iOS 26: Início ·
   Quedas · Lojas · Telegram). É o que faz "parecer app".
3. **Vitrine**: o primeiro produto (topo #1) vira um cartão grande com a
   placa de preço em vidro sobre a foto — o que a pessoa vê "logo de cara".
4. **Cartões**: foto num poço branco (produto precisa de branco), rodapé em
   vidro tingido; chips e botão "avise-me" com o mesmo material.
5. Menus (Categoria/Loja) como folhas de vidro que sobem de baixo (sheet).

## 4. O que fica de fora, e por quê

- Refração SVG / dispersão cromática: Safari. (Se um dia for só Chrome, o
  filtro é `feImage` PNG + `feDisplacementMap` R/G, DEM.)
- WebGL: custo × ganho numa vitrine de produto barato.
- Vidro em cima de foto de produto: a foto é o produto; o vidro só na placa
  de preço, e tingido.
