# RETOMADA — a CAPA da vitrine (21/09/2026, manhã e tarde)

Continuação de `RETOMADA_22-09-2026.md`. Aquele fechou a madrugada do herói;
este é o dia inteiro em cima do **cartão que abre a vitrine**.

---

## ⭐ O QUE MUDOU DE CONCEITO

O herói deixou de ser **o primeiro da lista** e passou a ser **escolhido por
uma régua própria** — a `marcar_capa` em `paginas/publicar_bio.py`.

O pedido do Bryan foi: *"tem que ser um produto top que esteja vendendo muito
muito e que nos dê um bom lucro e que seja elegível para estar na capa"*, com
foguinho e gráfico.

### A medida que destravou tudo

O piso que barrava a capa **não era a queda — era o ganho**, e ele estava
errado de forma: absoluto numa faixa onde deveria ser proporcional.

```
entre os 120 produtos vivos de até R$ 99:
  passam em nota + queda + vendas ......... 14
  desses, passam no ganho >= R$ 3 .......... 1   <- a trava
  afrouxar a QUEDA de 15% para 5% .......... 1   <- NÃO era a queda
```

R$ 1,45 num produto de R$ 6,36 é **22,8%** do preço; R$ 3 num de R$ 150 é 2%.
O piso absoluto matava os melhores baratos **por serem baratos**. Virou
`CAPA_GANHO_PCT_MIN = 6.0`.

⚠️ Isto **não abandona** a regra de 17/09 (*"não podemos postar só porque é
barato e não lucrar"*): muda a unidade, de reais para proporção. O ganho
absoluto cai para ~R$ 1,50 e só se paga no volume — que estes produtos têm
(62 mil a 113 mil vendas).

---

## OS DEFEITOS REAIS ACHADOS (medidos, consertados)

### 1. A série era int e o instantâneo era str — metade da guarda de 24h morta

`estado/precos_vistos.jsonl` grava `"id": 1005007542604477` (int);
`estado/precos_agora.json` grava `"1005007096727922"` (str). `_visto_em`
normalizava para texto e nunca casava com a série. **A metade "último ponto
da série" devolvia "" em toda chamada** — o `_todos` inteiro dependia só do
instantâneo horário. É o "amanhecer com 1 produto" que o próprio comentário
da função descreve; o reparo de 19/09 mascarou o defeito em vez de corrigi-lo.

Dois testes vermelhos desde 20/09 eram isto falando, não dublê velho.

### 2. O gráfico contradizia o preço

```
série do produto da capa:  ... 09-19 R$ 9,48 | 09-20 R$ 24,63   (ontem)
preço exibido:                 R$ 9,48                           (instantâneo de hoje)
```

O cartão dizia "caiu 62%, R$ 9,48" e a linha **subia** até o fim. Os dois
estavam certos: o preço caiu mesmo de ontem para hoje, e a série só ia até
ontem porque é consolidada por DIA. Errado era desenhar um sem o outro.

```
antes: 17 de 18 candidatos anunciavam preço ≠ da última leitura
depois:  0 de 135
```

Conserto em `_serie_curta`: se o instantâneo tem preço e o último ponto é de
outro dia, o instantâneo **vira o ponto de hoje**.

### 3. ⛔ Um `\b` virou caractere de BACKSPACE dentro de uma regex

Meu filtro saiu como `/\x08promo\x08/`. **Invisível no `sed`, no navegador, e
o `node --check` APROVA** — é sintaxe válida. Só apareceu porque o chip
continuava na tela. Agora eu varro caracteres de controle a cada patch:

```python
sum(d.count(bytes([c])) for c in range(32) if c not in (9, 10, 13))
```

### 4. `emReais` / `moeda` / `milhar` estavam presas dentro de `animarVivo`

O cartão da capa precisou de `emReais` e o código ficava perfeito e estourava
`ReferenceError` NO NAVEGADOR — derrubando a vitrine inteira. Promovidas ao
escopo do motor, na mesma doutrina de `linhaDeSinais`: uma régua só.

---

## ⭐ O JULGAMENTO DE FOTO POR VISÃO — `engine/foto_julga.py`

### Por que existe

A régua acertou todos os números e escolheu uma **colagem de 4 cenas com
texto queimado**. Nenhuma medida nossa pegava:

```
OCR  mede TEXTO ........ esta foto: 0,0356, ABAIXO da mediana de 0,0568
CLIP mede SEMELHANÇA ... contra a principal — e esta É a principal
```

Os dois são **proxies**. O modelo de visão pergunta a coisa em si.

### A aferição (o caso negativo, que é o que importa)

`gemini-3.6-flash`, temperatura 0, 6 fotos:

```
Organizador de panelas .... colagem=não quadros=1 texto=não nota 9
Pulverizador de jardim .... colagem=não quadros=1 texto=não nota 8
Bolsa tática .............. colagem=não quadros=1 texto=SIM nota 6
Fita organizadora ......... colagem=não quadros=1 texto=não nota 6
Carregador GaN ............ colagem=não quadros=1 texto=SIM nota 5
Luz LED (a capa do dia) ... colagem=SIM quadros=4 texto=SIM nota 3
```

Uma acusação em seis, e as outras cinco **graduadas**. Não é detector que
acusa tudo.

### ⛔ O `gemini-3.1-flash-lite` foi TESTADO E REPROVADO

Ele é 10× mais rápido (4/4 em 8,5 s contra 1/4 em 97 s do 3.6) e **erra**:

```
foto ...200.png    lite: colagem=SIM    3.6: colagem=não   <- falso positivo
foto ...9x.png     lite: nota 9         3.6: nota 5
foto ...7E.png     lite: nota 10        3.6: nota 8
a colagem da capa  lite: não respondeu  3.6: colagem=sim, nota 3
```

Concordou em 4 de 7 e **acusou colagem onde não havia** — o erro que reprova
foto boa em silêncio. **Não trocar por velocidade.**

### ⛔ `gemini-2.5-flash` MORREU

404: *"no longer available to new users. Please update your code to use
models/gemini-3.6-flash"*. **Conferir se algum outro lugar do projeto ainda
chama o 2.5.**

### ⚠️ A disponibilidade é instável

Para o 3.6 responder uma vez foram precisas CINCO chaves (dois `503 high
demand`, um `403`, um `429`). Por isso: rodízio de `engine.keys`, `queimar()`
em 429/403, e **grava o cache a cada resposta**.

### ⭐ EDITAR A FOTO ESTÁ FORA — escolher, não editar

MEDIDO: **160 dos 165** produtos do instantâneo guardam fotos extras, mediana
de **5 por produto**. A capa daquele dia tinha 5, e a colagem era só UMA.

E editar quebraria a fidelidade: `engine/fidelidade.py` registra que o
inpainting **refez o produto com menos detalhe** e ainda tirou **0,9786** —
acima de qualquer limiar útil. A guarda NÃO pega degradação. Redesenhar o
produto quebraria a ordem de 15/09 sem nada ficar vermelho.

`melhor_foto()` já está escrita para promover a melhor extra julgada.

---

## ⛔ O ERRO DE MÉTODO QUE SE REPETIU O DIA INTEIRO

**Publiquei três vezes uma coisa que o Bryan reprovou na tela dele.** Sempre
a mesma causa: conferi num painel de **380 px no escuro** e chamei de
conferido. O iPhone dele é **430 px no claro**, mais alto — e o cartão do
herói tem `aspect-ratio` fixo, então **cada largura muda a PROPORÇÃO entre
placa e foto**, que era justamente o que quebrava.

E duas vezes eu **repeti o mesmo fato em dois lugares** do cartão: o chip
"Promo 62% OFF" ao lado do selo "↓ 62%", e o carimbo "nunca esteve tão
barato" logo acima da escala "menor que eu vi ✓". Regra que ficou:
**com gráfico, quem fala é o gráfico.**

⭐ **Conferir no ar só vale na largura e no tema de quem olha.** E prototipar
no navegador ANTES de publicar custa minutos; publicar errado custa a manhã
dele.

---

## O QUE ESTÁ NO REPO E NÃO FOI PUBLICADO

Tudo abaixo está commitado e **nada foi ao ar** nesta leva:

- `marcar_capa` + `CAPA_*` + `_menor` (o menor preço rastreado)
- o cartão da capa (preço + riscado + botão, gráfico com escala, prova da loja)
- `engine/foto_julga.py` e o piso de foto na régua (falha ABERTA)

⚠️ O último estado NO AR é o de ~09:30: nome e preço fora da foto, cartão em
coluna. Tudo depois disso está só no repo.

---

## 🟠 O QUE FICOU PARA O BRYAN

1. **O lote de julgamento das 148 fotos** parou no meio (18 julgadas,
   2 colagens). Retomar com:
   ```
   python -X utf8 -m engine.foto_julga
   ```
   Ele continua de onde parou — o cache grava a cada resposta. ~45 s por
   foto por causa dos `503`; ~1h40 para o resto.

2. **O piso da nota da foto** está em `CAPA_FOTO_NOTA_MIN = 7`, chutado a
   partir de 6 fotos. **Decidir depois de ver a distribuição das 148**:
   ```
   python -X utf8 -m engine.foto_julga --distribuicao
   ```

3. **Publicar.** Nada desta leva está no ar.

4. **Awin** — continua sendo o mais urgente da fila, e não foi tocado hoje.

5. **Os dois clones divergentes** — o `Modo-Futuro` está com base em commits
   que o rebase do vigia reescreveu. Ficou pior que ontem.
