# RETOMADA — 23/09/2026, parte 2 (escrito no fim da sessão da tarde/noite)

Continuação da mesma data. O anterior é
[`RETOMADA_23-09-2026.md`](RETOMADA_23-09-2026.md) (escrito no fim de 22/09,
sobre descontos falsos + gráfico + design da capa/cartões).

Esta sessão focou o **console de filtros** (busca + chips + Categoria/Loja)
e a **barra de abas** (Início/Instantâneos/Lojas/Telegram) — refino visual
pedido pelo Bryan em cima de screenshots do celular real, mais alguns bugs
reais que apareceram no caminho.

⛔ **Tudo o que está descrito abaixo está NO AR** em `achadinhototal.com.br`,
confirmado no commit `85563f4`. A árvore está limpa e empurrada nos dois
clones (mesmo fluxo do handoff anterior — ver seção 0 dele, não repito aqui).

---

## 1. 🔴 O BUG REAL: SSR corrompia preço com `$&` no replace

Achado por acaso enquanto eu ajustava o botão "avise-me". O texto do preço
("R$ 101,00", codificado como `R$&nbsp;101,00`) sendo colado como STRING de
substituição num `saida.replace(alvo, novo)` em `ferramentas/ssr/ssr.js` —
JavaScript trata `$&` dentro da string de replacement como "insira aqui o
match", não como texto literal. Resultado: uma `<div id="grade">` fantasma
aparecia NO MEIO do preço, e `id="grade"` ficava duplicado ~17x na página.

**Fix**: `saida.replace(alvo, () => novo)` — replacement como FUNÇÃO nunca
interpreta padrão, o retorno entra literal. Cobre as 5 chamadas de `troca()`
de uma vez (prova, chips, vitrine, grade, vivo_preco/nome/dica/cta).

Teste novo: `teste/teste_ssr_primeira_tela.py`, seção 9 — confirma
`id="grade"` aparece 1x e nenhum `nbsp;` órfão (sem o `&` antes). Comprovado
que falha 2x contra o código antigo antes do fix.

**Bryan viu isso ao vivo mas não conseguiu tirar print** ("aparece muito
rápido quando atualiza a tela") — se acontecer de novo, é esse mesmo padrão.

---

## 2. O console de filtros — treze rodadas até acertar

O Bryan foi corrigindo com fotos do celular real, uma coisa por vez. A lição
grande desta sessão, se você só ler uma coisa: **screenshot zoomado/cortado
engana**; a medição via `getBoundingClientRect()` no DOM real é a única
fonte confiável de "quanto espaço tem aí". Fui atrás de fantasmas 2-3 vezes
porque confiei demais numa foto comprimida antes de medir.

### 2.1 A abas foram reordenadas e uma foi deletada
Ordem final: **Maiores quedas → Mais vendidos → Instantâneos → Achados
novos → Subiram de preço**. "Mais baratos" foi deletada (sem comprador
claro). "Achados novos" agora usa `p.dias` (idade real, calculada no
backend) em vez de um proxy antigo — cabe até 3 dias de vida, mais recente
primeiro. "Subiram de preço" ordena pela DIFERENÇA (preço hoje − menor que
já vimos), menor subida primeiro — não pelo preço absoluto.

### 2.2 A sombra dos chips — a saga
Sequência real do que aconteceu (pra não repetir os erros):
1. Sombra grande (`0 6px 16px -8px`) vazava visualmente nos vizinhos —
   "botões se sobrepondo". Reduzida.
2. Ainda vazava no canto do chip preto. Reduzida de novo, offset simétrico.
3. Ainda sobrava. Zerei toda sombra externa — "apoiado em algo" resolvido,
   mas criou um problema NOVO.
4. Zero sombra = chip "colado"/sem descolamento. Sombra pequena de volta
   (blur 4px).
5. **Bug de cascata real**: a sombra da rodada 4 foi escrita numa regra
   ANTES da regra BASE do `.chip-ordem` no arquivo — a base, mais abaixo,
   vencia a cascata e apagava a sombra. Nunca chegou a aparecer pro Bryan.
   Corrigido: sombra movida pra dentro da regra que realmente decide.
6. Mesmo corrigido, 16-22% de opacidade sobre fundo quase branco é quase
   invisível a olho nu. Dobrado o blur e a opacidade.
7. **Ainda assim**: no tema ESCURO a sombra contrasta e fica ótima; no tema
   CLARO, sombra clara sobre página já branca tem pouquíssimo contraste —
   limite físico de box-shadow sozinho. **Fix definitivo**: borda fina e
   sólida (`1px solid rgba(20,20,30,.12)`) — não depende de contraste de
   luz, sempre desenha uma linha, funciona nos dois temas.

**Se a sombra "desaparecer" de novo**: primeiro suspeite de outra regra
`.chip-ordem { ... }` mais abaixo no arquivo roubando a cascata (Ctrl+F
`.chip-ordem {` e confira quantas ocorrências existem — deveria ser só uma
definindo box-shadow/border).

### 2.3 O "card branco" era o fundo do `.console`
Bryan: "quero ver o fundo entre eles, não esse card branco". O espaço entre
a fila de chips e Categoria/Loja SEMPRE teve o valor de gap certo — o que
parecia "sem espaço" era o `.console.vidro` (fundo compartilhado com TODO
elemento de vidro do site) pintando um painel sólido por cima do espaço
vazio. Fix: `.console.vidro { background-color: ... }` sobrescreve SÓ ali
(não toquei em `.vidro`, que afetaria abas/chips/escolha/busca-caixa/opcoes
também). Primeiro fiz 100% transparente — revelou uma mancha de cor de foto
de produto atrás através do blur ("sombra estranha"). Ajustado pra um
branco/escuro bem leve (55% opacidade) — esconde a mancha sem voltar a ser
card sólido.

### 2.4 Destaque de toque do Safari vazando
Com o console transparente, o retângulo azul de toque nativo do iOS (que
antes ficava escondido pelo fundo sólido) ficou visível atravessando os
chips. Fix: `-webkit-tap-highlight-color: transparent` nos filhos do
console — o `:active` do próprio site já dá o feedback (`scale(.96)`).

### 2.5 Espaçamentos finais
- Gap horizontal entre chips: 10px.
- Gap vertical entre a fila de chips e Categoria/Loja: 12px.
- Padding-top da fila de chips (espaço acima, entre busca e chips): 12px —
  **igualado** ao gap vertical de baixo, por pedido explícito do Bryan
  ("quero os espaçamentos iguais").

### 2.6 Textos
- Legenda "rastreando há X dias" nunca mais fica verde — o verde é só do
  VEREDITO ("menor que eu vi ✓"), não da idade do rastreamento. As duas
  linhas usavam a mesma variável `classe` por engano (herdado de um fix de
  ícone anterior).
- "a R$ X do menor preço" cortava o "a " do início — estourava a borda do
  card empilhado. Agora começa direto em "R$".
- "você economiza R$ X" → "economiza R$ X" (sem "você") SÓ na grade (card
  estreito, 139px úteis) — quebrava em 2 linhas no pior caso medido
  ("R$ 153,93"). A capa (300px+) nunca teve o problema e continua "você".
- Legenda do convite ("O achadinho aparece lá primeiro... antes do vídeo
  sair") prometia uma vantagem de TEMPO que não existe — Telegram e vídeo
  saem JUNTOS. Trocada por "Receba as melhores ofertas no seu celular" /
  "Sem precisar abrir o site: cada queda de preço boa que eu encontro cai
  direto no seu Telegram" — honesta.
- Botão "Entrar no Achadinho Total" ganhou o ícone de avião de papel (mesmo
  path SVG da aba "Telegram") — o texto "entrar" sozinho não dizia PARA
  ONDE.

### 2.7 Selo de loja no menu "Loja"
Reserva de 18/09 nunca desenhada: a cor da loja "fica no seletor Loja", mas
ninguém tinha implementado. Adicionado: SIMBOLOS oficial (logo real) quando
existe, senão sigla colorida (mesmo `LOJAS{}` que o cartão usa). Lojas sem
marca cadastrada (Kabum, Arno, Lauri, Shark Ninja, Exypna) ganharam selo
CINZA SÓLIDO (`#5b5566`, texto branco) — o primeiro tentativa (translúcido)
ficava "apagada" ao lado das coloridas.

---

## 3. O brilho iridescente da barra de abas — CUIDADO, revertido

O Bryan pediu pra deixar o brilho/halo do shader (`espelho()`, WebGL) mais
evidente na barra de abas (`#abas`), igual já é nos chips/console. Aumentei
a amplitude da lente (`ligar(el, raio, ampl)` — terceiro parâmetro que EU
adicionei nesta sessão, só afeta o elemento passado) de 7 (padrão) pra 11,
depois pra 16.

**Revertido pro padrão (7) no fim da sessão**: ao trocar de aba (Início →
Instantâneos), a View Transitions API mistura o snapshot antigo com o novo
por ~0,26s, e com a lente forte esse instante de mistura piscava como uma
"sombra estranha do nada". Não consegui confirmar visualmente NENHUMA
dessas mudanças de amplitude — **este ambiente de teste automatizado não
renderiza WebGL** (nenhum `canvas.espelho` aparece em nenhum elemento,
mesmo os que funcionam de verdade no aparelho do Bryan; `prefers-reduced-
motion: reduce` também vem `true` por padrão aqui).

**Se o Bryan pedir de novo pra aumentar esse brilho**: o parâmetro existe
(`ligar(document.getElementById("abas"), -1, N)`, ~linha 5450 de
`todos.html`), mas teste com cautela e OBSERVE a troca de aba antes de
declarar sucesso — o efeito colateral só aparece durante a transição, não
no estado parado.

---

## 4. Armadilha de encoding que voltou a aparecer

O texto "a R$ X do menor preço" (seção 2.6) tem o MESMO padrão de bytes que
já causou dor de cabeça antes nesta sessão: `\xc2\xa0\xc2\xb7` (nbsp + middle
dot reais, UTF-8) em volta do "·". O Edit tool não bate por string exata
nesse trecho — funciona: ler o arquivo em `rb`, achar os bytes exatos com
`.find()`, substituir com `.replace()` em bytes, escrever de volta em `wb`.
Não tente Edit normal nessa região do arquivo (por volta da função que monta
`veredito`, ~linha 3030-3040).

---

## 5. Falso-negativo de publicação — aconteceu 3x nesta sessão

Padrão recorrente: `publicar_bio.py --subir` reporta `NAO ESTA' NO AR` mas
o conteúdo JÁ está lá (propagação de CDN, hash mudou entre o push e a
verificação). **Não pânico, não anuncie falha** — confirme com:
```bash
curl -s "https://achadinhototal.com.br/paginas/todos.html" | grep -c "TEXTO_QUE_VOCE_ACABOU_DE_ADICIONAR"
```
Se aparecer, o conteúdo está no ar mesmo que o script tenha reclamado — só
rode `--subir` de novo pra fechar o diário com o hash certo.

⚠️ **Os comentários JS/CSS são removidos na publicação** (minificação).
Procurar por texto de comentário (`RODADA 9`, `BLOCO A`) no HTML publicado
SEMPRE dá 0 — isso é normal, não é sinal de deploy velho. Procure pela
REGRA/VALOR real (ex: `rgba(20,20,30,.12)`), não pelo comentário.

⚠️ **Race condition real**: se você editar o arquivo ENQUANTO um
`--subir` anterior ainda está esperando o lock de outro processo (o vigia
automático publica sozinho a cada 10 min), o conteúdo publicado pode ficar
com um snapshot de ANTES da sua edição, mesmo que o diário mostre o hash
git certo (o diário só regista o HEAD no momento em que o script terminou,
não o que foi de fato lido pro upload). Se suspeitar disso, sempre confirme
com curl + grep pelo texto/regra específica.

---

## 6. Estado final — o que está pendente

Nada quebrado, nada pendente tecnicamente. O Bryan estava em modo de
refino visual fila-por-fila no celular real; é plausível que ele volte com
mais um ou dois ajustes finos (a sessão teve 13 rodadas só no console de
filtros — ele está olhando com atenção). Se voltar:
1. **Meça antes de mudar** — `getBoundingClientRect()` via
   `mcp__Claude_Browser__javascript_tool`, nunca confie só no screenshot
   comprimido do celular dele.
2. **Teste os dois temas** (claro e escuro) — pelo menos duas vezes nesta
   sessão um fix funcionou num tema e não no outro.
3. **`resize_window` com `preset: "mobile"`** antes de screenshot — sem
   isso a página renderiza em largura de desktop e a medição não bate com
   o celular real dele.
4. Se for mexer no `#console` ou `#abas` de novo: são os elementos com
   `class="vidro"` + `ligar()` do shader WebGL — o Bryan é MUITO cauteloso
   com esse sistema (pediu checkpoint antes de eu tocar nele:
   `checkpoint-antes-menu-chips-23-09-2026`). Qualquer mudança aí, avise
   explicitamente que está tocando no vidro/shader antes de fazer.

Nada do YouTube/mentores research (Wholesale Ted, Biaheza, etc — pedido
antigo, nunca retomado) foi tocado nesta sessão.
