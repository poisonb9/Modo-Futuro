# RETOMADA — 24/09/2026, balões da inauguração

O anterior é [`RETOMADA_23-09-2026_PARTE3.md`](RETOMADA_23-09-2026_PARTE3.md)
(os dois bugs da barra de abas continuam ABERTOS, não mexi neles).

## 1. Site — commit `c148b88` (empurrado 24/09 ~01:03)

- **Balões** no header (`paginas/todos.html`, bloco "baloes da inauguracao"):
  festa à esquerda (laranja "INAUGURAÇÃO", laço, estrela, etiqueta, sacola,
  lupa), canais à direita (Make, Chef, Instantâneos, Sem Anestesia, Pago
  Menos, Modo Futuro). Celular: 3+3 em arco no brasão. ≥760: 6+6 dos lados
  do título. ≥1400: nas margens ao lado da vitrine. Enfeite puro: absolute,
  aria-hidden, sem toque, parado em reduced-motion.
- Imagens: `paginas/baloes/*.webp` (12, ~20–40 KB). Sobem pelo `_por_icone`
  do `publicar_bio.py`, nos DOIS diretórios do deploy, em `/baloes/`.
  Originais e recortes: `Desktop\inauguracao\` e `\recortados\`.
- Consertos do PC: 4:3 de celular baixo pegava notebook (foto 708 px → 354);
  word-spacing da legenda com teto de 6 px (chegava a 65 px); chips
  `safe center` ≥1024; busca digitando exemplos no placeholder (para no foco,
  reduced-motion e SSR).
- ⚠️ **Publicação NÃO confirmada quando escrevi isto.** O vigia pegou a
  mudança às 01:10 e ainda gerava às 01:22. Prova de que está no ar:
  `curl` na raiz achando `inaug_laranja`, e `/baloes/inaug_laranja.webp`
  respondendo `image/webp` (não `text/html`).
- Testes do site: 17/19 verdes. Os 2 vermelhos são ANTERIORES a esta mudança:
  `teste_legenda_uma_linha` (exige 12,5 px; código usa 11 desde 22/09) e
  `teste_categoria_externa` (campo `subiu` a mais no cartão). Não consertados.

## 2. PENDENTE — balões subindo para os vídeos do TikTok

Pedido do Bryan (24/09): "máscara" de balões sem fundo, subindo na tela, para
entrar em determinado momento dos vídeos.

⏳ **O Bryan está preparando as imagens e vai mandar: QUANTOS balões, QUAIS e
EM QUE MOMENTO (horário) do vídeo entram.** Não comece sem essa lista.

Plano combinado (ainda não feito):
- Sem IA de vídeo (o Kling deformou os balões): movimento por código a partir
  dos recortes — cada balão com posição, velocidade, atraso e balanço
  próprios; menores mais lentos (profundidade). 1080×1920, 3–4 s.
- Entrega em dois formatos: MP4 com fundo verde chapado (CapCut → Recorte →
  Chroma) e `.mov` com transparência de verdade (CapCut PC, Premiere). O editor
  do próprio TikTok não aceita transparência.
- Renderizar NA NUVEM (máquina local não processa nada).
