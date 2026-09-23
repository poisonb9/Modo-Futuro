# RETOMADA — 23/09/2026, parte 3 (fim de sessão, /clear pedido)

Continuação da mesma data. O anterior é
[`RETOMADA_23-09-2026_PARTE2.md`](RETOMADA_23-09-2026_PARTE2.md) (console de
filtros, bug do SSR `$&`, shader). Esta sessão começou a partir de dois prints
do celular real do Bryan e foi até travar o tema sempre-claro.

Commit no ar: **`7bf9146`**, confirmado com `curl` (não só a saída do
publicador). Árvore limpa, empurrada nos dois clones.

⛔ **Dois bugs ficaram ABERTOS.** O Bryan viu ao vivo no celular dele que
persistem mesmo depois do fix, decidiu não continuar investigando agora
("vamos deixar") — ver seção 3. NÃO declare os dois resolvidos na próxima
sessão só porque o código parece certo; eles já pareceram certos aqui e
continuaram aparecendo pra ele.

---

## 1. O que foi CONFERTIDO resolvido (commit `7bf9146`)

### 1.1 "Comprar agora" cortado no card da capa
Bug real: `.cap-linha` (preço + riscado + botão, todos numa linha sem quebra)
estourava o container em telas estreitas quando havia riscado (desconto).
MEDIDO a 375px no card real: preço 99px + riscado 68,6px + gap 16px + botão
176,8px = 360,4px contra 307px de container — 53px pra fora.

**Fix**: `.cap-linha` ganhou `flex-wrap: wrap`; o botão agora cai pra própria
linha (ainda `margin-left:auto`, fica encostado na borda direita) em vez de
vazar pra fora do cartão. Confirmado com `getBoundingClientRect()` ao vivo em
produção: `overflow: 0`.

### 1.2 Tema sempre-claro travado
Pedido do Bryan: tema escuro pode estar atrapalhando venda. Travado SEM
apagar nada — reversível.

- Os 14 blocos `@media (prefers-color-scheme: dark)` (CSS) e o
  `<meta name="theme-color" media="...">` ganharam uma condição impossível
  anexada: `and (prefers-color-scheme: light)` — nunca casa, mas o bloco
  original continua inteiro, marcado com o comentário `TRAVADO-SEMPRE-CLARO
  23-09`.
- Os 2 pontos de JS que leem `matchMedia("(prefers-color-scheme: dark)")`
  (o shader do vidro, `.com-gl` e `.com-espelho`) ganharam `&& false` no
  final da expressão — mesmo princípio, mesmo marcador.
- **Reverter**: procurar `TRAVADO-SEMPRE-CLARO` no arquivo e tirar o texto
  extra de cada ocorrência (15 no CSS/meta, 4 no JS).
- Confirmado com `curl` contando as 15 condições impossíveis no ar.

⚠️ **Cuidado ao tocar em qualquer `@media (prefers-color-scheme: dark)` ou
`matchMedia` novo**: se alguém adicionar um bloco de tema escuro sem saber
disso, ele não vai ser travado automaticamente — precisa repetir o padrão.

---

## 2. Investigação que foi ENGANOSA — não repetir

Cheguei a propor consertar `motor.js` (trocar `src="motor.js"` relativo por
`/motor.js` absoluto) porque `achadinhototal.com.br/paginas/todos.html`
devolvia `Refused to execute script ... MIME type ('text/html')`.

**Era falso alarme.** `/paginas/todos.html` não é um endereço real — é
fallback do Cloudflare Pages pra QUALQUER caminho inexistente (testei com
`/caminho-que-nao-existe-xyz123`: mesmo md5 byte a byte da home). Ninguém
chega lá por link nenhum (bio, TikTok, Telegram). O `motor.js` de verdade,
na raiz, funciona.

Se eu TIVESSE aplicado o fix (`/motor.js` absoluto em todo lugar), teria
**quebrado os 5 sites de bio** (oachadinho, achadinhochef, pagomenos,
achadinhodehoje, meulivro) — confirmado com `curl`: neles o `motor.js` real
só existe em `/todos/motor.js`, não na raiz (arquitetura diferente do site
mãe, documentada em `publicar_bio.py` ~linha 2672, decisão de 21/09
"REDIRECIONAR, E NAO ESPELHAR"). **Não mexer em `MOTOR_ARQUIVO` sem
testar os 6 projetos, não só o site mãe.**

---

## 3. Os dois bugs ABERTOS — reproduzidos só no celular real do Bryan

Ambos na barra flutuante inferior (`#abas`, `Início`/`Instantâneos`/
`Lojas`/`Telegram`). Eu apliquei fix pros dois, medi no ambiente de teste
(browser automatizado) e bateu certo — mas o Bryan viu ao vivo que
continuam. **Não reproduzi nenhum dos dois no meu ambiente**, então o que
seguiu abaixo é o que já foi DESCARTADO como causa, não o diagnóstico final.

### 3.1 Sombra quadrada atrás de "Início" e "Instantâneos" ao pressionar
Print mostrou um retângulo/sombra nos CANTOS da pílula redonda ao tocar.

**O que já tentei** (commit `7bf9146`): apliquei
`-webkit-tap-highlight-color: transparent` em `.abas a`, o mesmo fix que já
resolveu esse exato padrão no `.console` na sessão anterior (rodada 8,
21/09). Não resolveu — Bryan viu de novo depois do deploy confirmado no ar.

**Hipóteses NÃO testadas ainda**:
- Pode não ser mais o tap-highlight nativo (esse já foi desligado). Pode ser
  a `.pilula` (indicador deslizante, `position:absolute`, `border-radius:
  999px`, transição de `left`/`width` em 0,34s) desenhando um frame
  quadrado durante a própria transição/repaint em Safari iOS — o
  `border-radius` às vezes "atrasa" um frame em relação ao `width` durante
  animação no WebKit.
- Pode ser um navegador/WebView específico (Bryan usa TikTok in-app browser
  às vezes, que é WebView do app, não Safari/Chrome puro) que ignora
  `-webkit-tap-highlight-color`.
- **Próximo passo sugerido**: perguntar ao Bryan qual navegador exatamente
  (Safari, Chrome, ou dentro do app do TikTok/Telegram) — isso decide se o
  problema é CSS ou comportamento nativo do WebView que CSS não alcança.

### 3.2 O botão/pílula ainda invade a palavra "Instantâneos"
Print mostrou o fundo branco arredondado mais estreito que a palavra,
"cortando" visualmente.

**O que já tentei** (commit `7bf9146`): troquei o texto solto por
`<span class="aba-rotulo">` com `align-self:stretch` + `text-overflow:
ellipsis` (mesmo padrão de `.item .eco`/`.leg-loja-txt`), pra nunca deixar
o texto vazar sem pelo menos truncar com reticência.

**Medido AO VIVO em produção** (não só localmente): cliquei em
"Instantâneos" de verdade na raiz do site (JS rodando), medi com
`getBoundingClientRect()`:
```
aWidth: 77.75px   spanWidth: 77.75px   pilWidth: 77.75px   pilLeft == aLeft
```
Os três batem exatos — nenhum overflow, nenhum mismatch, no ambiente de
teste. Mesmo assim o Bryan reportou "ainda tá bugado" depois.

**Hipóteses NÃO testadas ainda**:
- Fonte real (Poppins, Google Fonts) pode não ter carregado a tempo no
  celular dele e caiu pro fallback do sistema — que pode ser mais largo pra
  "Instantâneos" (com acento) do que o Poppins mede aqui.
- Pode ser tamanho de fonte do sistema aumentado (acessibilidade) no
  telefone dele — `font: 600 10.5px/1` é um valor FIXO em px, não usa
  `rem`, então não deveria escalar com preferência do usuário, mas vale
  confirmar.
- Cache do Safari/PWA: se ele não deu reload forçado, pode estar vendo uma
  versão de ANTES do commit `7bf9146` (o `Cache-Control` do HTML é
  `max-age=0, must-revalidate`, então isso seria estranho, mas telefone com
  app instalado como PWA pode manter um Service Worker antigo — não
  verificado se este site tem Service Worker).

**Próximo passo sugerido**: pedir um screen recording (não print) do toque
na aba, e perguntar se ele deu reload forçado (puxar pra baixo / fechar e
reabrir o app) antes do print mais recente.

---

## 4. Estado final

Nada quebrado além dos dois itens da seção 3, que já eram assim antes desta
sessão (não é regressão do que mudei — o texto "Instantâneos" e o ícone de
raio são novos de hoje mesmo, trocados de "Quedas" na sessão da tarde,
então o bug pode ser tão novo quanto o rótulo). Árvore limpa, tudo commitado
e publicado, conferido com `curl`.

Se o Bryan voltar com mais um print dos dois bugs da seção 3: comece
perguntando navegador/app e se recarregou, ANTES de mexer em CSS de novo —
já foi medido que a implementação bate no ambiente de teste, então repetir
a mesma medição não vai achar nada novo.
