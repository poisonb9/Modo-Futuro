# RETOMADA — 24/09/2026, parte 3 (galeria, rolagem, bios, preços vivos, avise-me)

Anteriores: [`RETOMADA_24-09-2026_BALOES_PARTE2.md`](RETOMADA_24-09-2026_BALOES_PARTE2.md)
e [`RETOMADA_24-09-2026_BALOES.md`](RETOMADA_24-09-2026_BALOES.md).
Continuam ABERTOS de antes: os 2 bugs da barra de abas (`RETOMADA_23-09-2026_PARTE3.md`)
e os 2 testes vermelhos antigos (`teste_categoria_externa`, `teste_legenda_uma_linha`).

## 0. ⛔ PRIMEIRA COISA DA PRÓXIMA SESSÃO — conferir no ar

Às 09:20, 09:30 e 09:37 o vigia FALHOU: o detector de vazamento barrou
("NAO PUBLIQUEI. Sobrou coisa interna: 'Bryan' (nome do dono)"). Causa: eu
escrevi `/* ... (Bryan) */` DENTRO da linha `@media` do travamento de tema
nas 4 páginas, onde a limpeza de comentários não alcança. Consertado em
`0d889ab` e publicação disparada às 09:42 — **NÃO CONFIRMADA no fechamento.**

Prova de que está no ar (tudo tem de dar ≥ 1):
```
curl -s https://achadinhototal.com.br/ | grep -c coracao-convite
curl -s https://oachadinho.pages.dev/ | grep -c varal-bio
curl -s -o /dev/null -w '%{http_code}' https://achadinhototal.com.br/galerias.json   # 200
```
Se falhar: `estado/publicar_ao_mudar.log` e rodar `python -X utf8 paginas/publicar_bio.py`
SEM `--subir` — ele imprime a lista do detector (o log do vigia só mostra a 1ª linha).

⚠️ LIÇÃO: comentário com nome do dono só em comentário NORMAL (linha própria),
nunca colado em seletor/@media. Antes de publicar, rodar o publicador sem `--subir`.

## 1. O que foi feito nesta parte (commits `9124972` → `0d889ab`)

1. **Galeria do destaque no PC (≥1024)** — foto grande quadrada + grade 2×2 de
   4 extras, tudo `contain` sobre branco (nada esticado). Clique na miniatura
   troca a grande (View Transition). Dados: `precos_agora.json` já guardava
   `imagens` do Ali (164/168 produtos, 157 com 5) e ninguém usava.
   Publicador: `montar_galerias()` → `galerias.json` ao lado (61 KB, só o PC
   baixa, depois da carga). Filtro: foto JULGADA colagem/nota<5 sai; não
   julgada entra depois das boas; mínimo 3. Miniatura `_350x350.jpg` (30 KB).
   Liga por MutationObserver no `#vitrine` (a 1ª tela vem do SSR, `montar`
   não roda nela). Foto grande tem classe `vgal-grande` (NÃO `vfoto`: o
   `teste_primeira_tela_cabe` acusou disputa de cascata — consertado).
   ⏳ Só 53 das 809 extras estão julgadas; rodar `foto_julga.medir` nelas
   (gasta cota Gemini) melhora o filtro. Mercado Livre manda `pictures` e só
   guardamos a 1ª — etapa 2 da galeria.
2. **Balões que sobem com a rolagem no PC (≥1440)** — laranja pela direita
   (15%→60% da página), "%" pela esquerda (55%→100%, sai no topo no fim).
   Premium: deriva lateral ±10 px (4,9 s) + balanço ±5° (3,7 s) no `<img>`
   pelo relógio, subida no `<span>` pela rolagem, escala .92→1.04.
   Fallback JS (Safari sem `animation-timeline`): `--prog`.
3. **Celular: duas estrelas ao lado do PREÇO da linha viva**, soltando na
   rolagem (120→520 px; fallback `--solta2`). O Bryan hesitou ("apertado")
   e depois pediu para ver no ar — AVALIAR com ele.
4. **Inauguração nas BIOS** (`contra_capa.html`): varal INAUGURAÇÃO sobre o
   brasão (letras `_p`, vida própria), laranja + laço à esquerda, balão do
   canal + cupom à direita; topo +30 px. Conferido na prévia (Make, Chef).
5. **SÓ FUNDO BRANCO** (ordem do Bryan): contra_capa, nao_achei, privacidade,
   quem_somos travadas no claro (`TRAVADO-SEMPRE-CLARO`), como o todos.html.
   Memória: `modofuturo-so-fundo-branco`.
6. **Corações** (`inaug_coracao.webp`, recorte do PNG transparente do Bryan):
   um de cada lado do bloco "Receba as melhores ofertas", 78 px, PC ≥1440.
7. **Preços vivos**: cada caractere de `.item .preco` e `.cap-preco` vira
   `<span class="dg">` (script `tremularPrecos`, MutationObserver) com dois
   movimentos independentes sorteados (0,3–0,6 px; 0,5–1°). A `.vivo-preco`
   (digitada letra a letra) respira inteira. Com reduced-motion nada é partido.
8. **Avise-me vira link terciário**: sem caixa/vidro, texto cinza da largura
   dele com sublinhado pontilhado, 44 px de toque mantidos (acervo: Maestros
   secundário cinza + alvo ≥44 px iOS; Impeccable "everything else tertiary").
   Medido 118×44 px. NÃO VISTO em captura (o painel de prévia fica branco
   depois de rolar no PC — confirmado por `elementFromPoint` que nada cobre).

9. **"Comprar agora" flutua** (`.item .cta`, `.cap-cta`, `.vivo-cta`): dois
   movimentos independentes, 0,7 px e 0,25°, cartões defasados (nth-child),
   em `translate`/`rotate` para não brigar com o `transform` do toque.

## 2. Pendências com o Bryan

- **Dois balões exclusivos para a subida do PC** (no lugar do laranja e do %):
  proposta aceita para ele gerar — CAIXA DE ENCOMENDA dourada com laço
  vermelho (direita) + EMOJI 😍 dourado (esquerda): "chegada + reação", o
  formato que o acervo mais aponta como viral (unboxing). Prompts no chat
  de 24/09 (e o do brasão / moeda R$ como alternativas).
- **Balões para vídeos do TikTok** (lista: quantos, quais, quando) — ainda não veio.
- **Black Friday**: 4 balões guardados com ele (memória `modofuturo-black-friday-baloes-campanha`).
- Ele não confirmou se gostou de: galeria do PC, estrelas do celular, preços vivos, avise-me novo.

## 3. Armadilhas desta parte

- Detector de vazamento (acima). O vigia loga só "NAO PUBLIQUEI" — o motivo
  sai rodando o publicador sem `--subir`.
- Painel de prévia: `prefers-reduced-motion` LIGADO (animação não aparece;
  para testar, injetar a regra sem a media, ou trocar `dgReduz` por false numa
  cópia) e captura em branco depois de rolar no PC.
- Prévia com dados reais: `montar_catalogo()` escrito em `%TEMP%\prev\` (a
  cópia crua do todos.html vem sem produtos).
- Edição sempre em BYTES com contagem de CRLF (scripts em `ferramentas/baloes/`).

## 4. Ferramentas novas em `ferramentas/baloes/`

`galeria.py`, `subida_pc.py`, `estrelas_vivo.py`, `bio_inauguracao.py`
(receitas; os caminhos de entrada de `%TEMP%` não sobrevivem).
