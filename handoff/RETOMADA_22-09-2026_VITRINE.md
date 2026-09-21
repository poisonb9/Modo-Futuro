# RETOMADA — a vitrine, do herói ao cartão campeão (21/09/2026, dia inteiro)

Substitui `RETOMADA_22-09-2026_CAPA.md`, que cobria só até a régua da capa.
O antecessor da madrugada é `RETOMADA_22-09-2026.md`.

---

## ONDE ESTAMOS, EM UMA FRASE

O cartão que abre a vitrine deixou de ser "o primeiro da lista" e passou a
ser **escolhido por uma régua que mede número E foto**, com gráfico, foguinho,
economia em reais e o que só nós temos. Tudo o que está descrito abaixo está
**no ar** em `achadinhototal.com.br`.

---

## 1. A RÉGUA DA CAPA (`marcar_capa`, em `paginas/publicar_bio.py`)

```
preço ≤ R$ 99          nota da loja ≥ 95%        queda ≥ 15%
vendas ≥ 1.000         série ≥ 5 pontos          ganho ≥ 6% do preço
foto: sem colagem, sem texto queimado, nota ≥ 7
```

### ⭐ A medida que destravou tudo

O piso que barrava **não era a queda — era o ganho**, e ele estava errado de
forma: absoluto numa faixa onde tem de ser proporcional.

```
entre os 120 produtos vivos de até R$ 99:
  passam em nota + queda + vendas ......... 14
  desses, passam no ganho >= R$ 3 .......... 1   <- a trava
  afrouxar a QUEDA de 15% para 5% .......... 1   <- NÃO era a queda
```

R$ 1,45 num produto de R$ 6,36 é **22,8%**; R$ 3 num de R$ 150 é **2%**. O
piso absoluto matava os melhores baratos *por serem baratos* — os 14 barrados
tinham 62 mil a 113 mil vendas e quedas de 46% a 69%.

⚠️ Isto **não abandona** a regra de 17/09 (*"não podemos postar só porque é
barato e não lucrar"*): muda a **unidade**, de reais para proporção.

---

## 2. ⭐ O JULGAMENTO DE FOTO POR VISÃO (`engine/foto_julga.py`)

### Por que existe

A régua acertou todos os números e escolheu uma **colagem de 4 cenas com
texto queimado**. Nenhuma medida nossa pegava:

```
OCR  mede TEXTO ........ esta foto: 0,0356 — ABAIXO da mediana de 0,0568
CLIP mede SEMELHANÇA ... contra a principal, e esta É a principal
```

Os dois são **proxies**. O modelo de visão pergunta a coisa em si.

### A aferição, com o caso negativo

`gemini-3.6-flash`, temperatura 0, 6 fotos: **uma** acusação de colagem (a
certa, nota 3) e as outras cinco **graduadas** (9, 8, 6, 6, 5). Não é
detector que acusa tudo.

### ⛔ O `gemini-3.1-flash-lite` foi TESTADO E REPROVADO

10× mais rápido (4/4 em 8,5 s contra 1/4 em 97 s) e **erra**: acusou colagem
onde não havia, deu nota 9 onde o 3.6 deu 5, e não respondeu na colagem.
Concordou em 4 de 7. **Não trocar por velocidade.**

### ⛔ `gemini-2.5-flash` MORREU

404: *"no longer available to new users, use models/gemini-3.6-flash"*.
**Conferir se outro lugar do projeto ainda o chama.**

### ⭐ O que fazer quando a foto é ruim: ESCOLHER, não editar

MEDIDO: **160 dos 165** produtos guardam fotos extras, mediana de 5. A capa
da colagem tinha 5, e a colagem era só UMA delas.

⛔ E editar está fora por medida do próprio projeto: `engine/fidelidade.py`
registra que o inpainting **refez o produto com menos detalhe** e ainda tirou
**0,9786** — acima de qualquer limiar útil. A guarda NÃO pega degradação.
`melhor_foto()` já está escrita para promover a melhor extra julgada, e
**ainda não está ligada na régua**.

---

## 3. O CARTÃO, DEPOIS DO ACERVO (Bloco 1)

```
🔥↓57%  ☆98%
[foto limpa, 4:3, produto inteiro]
R$ 11,89  R$ 27,54            [ Comprar agora → ]
você economiza R$ 15,65
▔▔▔╱╲▔▔ rastreando há 8 dias · menor que eu vi ✓
98% positivas · 52.454 vendas na loja · AliExpress
```

- **Proximidade** (Kevin Powell, DEMONSTRADO): 6 px dentro do grupo, 16 px
  entre grupos. Existiam três grupos e nenhum se lia. Custo em altura: zero.
- **A economia em reais** abaixo do preço — mais concreta que a porcentagem,
  e é NOSSA (sai de `antes`, não do "de/por" do vendedor).
- **Elevação em duas camadas** — 1 px de borda + uma larga e fraca.
- **Nome do produto fora** (como o AliExpress faz na vitrine de ofertas).

---

## ⛔ OS CINCO DEFEITOS REAIS ACHADOS (todos medidos, todos consertados)

1. **A série era `int` e o instantâneo era `str`.** `_visto_em` normalizava
   para texto e nunca casava — **metade da guarda de 24 h estava MORTA em
   produção**. Dois testes vermelhos desde 20/09 eram isto falando.

2. **O gráfico contradizia o preço.** A série parava ONTEM em R$ 24,63 e o
   cartão anunciava R$ 9,48 de hoje: a linha SUBIA num produto que caiu 62%.
   `antes: 17 de 18 candidatos` → `depois: 0 de 135`.

3. **Um `\b` virou caractere de BACKSPACE** numa regex (`/\x08promo\x08/`).
   Invisível no `sed`, no navegador, e **o `node --check` APROVA**. Só
   apareceu porque o chip continuava na tela.

4. **`emReais`/`moeda`/`milhar` presas dentro de `animarVivo`** — o cartão da
   capa usaria `emReais` e estouraria `ReferenceError` NO NAVEGADOR,
   derrubando a vitrine inteira. Promovidas ao escopo do motor.

5. **`from engine import foto_julga` no topo do módulo** derrubava o
   `teste_guarda_confirma_nomeando`. `regua_vitrine` já era importada dentro
   da função pelo mesmo motivo — eu quebrei o padrão e a suíte pegou.

---

## ⛔ OS ERROS DE MÉTODO — leia isto antes de publicar qualquer coisa

### Publiquei TRÊS vezes algo que o dono reprovou na tela dele

Sempre a mesma causa: conferi num painel de **380 px NO ESCURO**. O iPhone
dele é **430 px NO CLARO** e mais alto. O cartão tem `aspect-ratio` fixo,
então **cada largura muda a PROPORÇÃO entre placa e foto** — que era
justamente o que quebrava.

⭐ **Conferir no ar só vale na largura e no tema de quem olha.** Prototipar
no navegador antes de publicar custa minutos.

### Repeti o mesmo fato em dois lugares, três vezes

O chip "Promo 62% OFF" ao lado do selo "↓62%"; o carimbo "nunca esteve tão
barato" acima de "menor que eu vi ✓"; a economia no botão E no riscado.
**Regra que ficou: com gráfico, quem fala é o gráfico.**

### Afirmei duas coisas sem medir, e as duas estavam erradas

- *"o lote parou"* — o processo estava vivo, eu olhei o cache por 45 s. Havia
  **DOIS lotes rodando em paralelo**, queimando as mesmas chaves em dobro.
- *"a cota acabou"* — testei as 28 chaves de uma vez: **14 eram 503** (fila do
  Google, que passa) e só **5 eram 429**. A cota explicava 5 de 28.

⭐ Medida indireta não vira afirmação.

---

## 🟠 O QUE FICA PARA O BRYAN

1. **⭐ MOVER O JULGAMENTO PARA A NUVEM.** Ele roda LOCAL e morre junto com a
   sessão — por isso o lote nunca passa de ~60 de 148. O OCR já resolve isso
   do jeito certo: `bryanaw2121-sketch/pipeline/.github/workflows/fotos_ocr.yml`,
   com a lista por dispatch e o resultado por artifact. Fazer o mesmo com o
   `foto_julga` é o maior ganho pendente. Por enquanto, retomar com:
   ```
   python -X utf8 -m engine.foto_julga
   ```

2. **`CAPA_FOTO_NOTA_MIN = 7` ainda é chute.** Distribuição com 60 de 148:
   ```
   10 ▓▓▓▓▓▓▓▓▓▓▓ 11    9 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 14    8 ▓▓▓▓▓▓ 6    7 ▓▓▓▓▓▓▓▓ 8
    6 ▓▓▓▓ 4            5 ▓▓▓▓▓▓ 6            4 ▓▓▓▓▓ 5     3 ▓▓▓▓▓ 5   2 ▓ 1
   ```
   É **bimodal** — um grupo em 9-10 e outro em 3-5, com vale no meio. O piso 7
   cai no vale, o que sustenta o chute. Fixar depois das 148:
   `python -X utf8 -m engine.foto_julga --distribuicao`

3. **Ligar o `melhor_foto()`**: hoje a régua REPROVA o produto de foto ruim.
   Com ele ligado, ela **troca a foto** pela melhor extra e o produto fica.

4. **Bloco 2 (escala tipográfica)** e **Bloco 3 (gráfico com corpo + resposta
   ao toque no botão)** — combinados e não iniciados.

5. **Awin** — continua o mais urgente da fila, e não foi tocado em nenhum
   momento hoje.

6. **Os dois clones** divergiram mais: o rebase do vigia reescreveu os hashes
   que o `Modo-Futuro` tinha como base.
