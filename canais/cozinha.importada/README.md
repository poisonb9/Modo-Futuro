# Cozinha Internacional — `@cozinha.internacional`

Receitas do mundo, dubladas em portugues, **com as medidas convertidas**.

⚠️ O nome no Buffer e' `cozinha.importada`, diferente do @ do TikTok. **O valor
de `canal` segue o BUFFER**, porque e' com ele que a guarda compara.

## Receita de disparo

| parametro | valor |
|---|---|
| `canal` | `cozinha.importada` |
| `idioma` | o da fonte (`en` na maioria) |
| `dublar` | `true` |
| `fala_literal` | **`false`** |
| `voice_over` | **`false`** |

## A conversao E' o produto

Fahrenheit para Celsius, xicara para ml, libra para grama. Um canal de receita
em portugues que nao converte medida nao resolve o problema de ninguem.

Por isso **fonte muda nao serve**, e a regra e' mais dura aqui que nos outros:
sem narracao nao ha' o que converter. Os tres maiores canais de comida do radar
foram descartados por serem silenciosos — "nada pra transcrever, traduzir ou
dublar".

### As armadilhas da conversao, todas medidas

Cinco rodadas ate' fechar, em 29 e 30/08/2026:

| o que falhava | por que |
|---|---|
| `a pound of`, `half a cup` | a regra exigia digito, e fala nao usa digito |
| `425 degrees` | a regra exigia o `F` |
| `at 420` | numero pelado, sem nem "degrees" |
| 1/3 de xicara dava 72 ml | arredondava a fracao ANTES de multiplicar (era 80) |
| "um terco de 240 ml" | `one third of a cup` nao casava, e o "a cup" do fim casava sozinho |

Provado no mesmo material que falhava: **455 g**, **180°C**, **255 g**,
**220°C**.

## ⚠️ O radar por hype seleciona o material ERRADO

Busca aberta por sobremesa devolve culinaria em miniatura e video de reacao —
muita view, **zero narracao e zero medida**.

O run #12 provou: a "AMAZING Dessert Compilation" do Preppy Kitchen rendeu
clipes com **4,3s de narracao em 91s de video**. Formato *satisfying*: imagem e
musica.

Aposta melhor: **Chef Jean-Pierre e Joshua Weissman**, que falam sem parar.

A guarda de clipe mudo (`engine/fala.py`, densidade < 0,5 palavra/s) pega isso,
mas prevenir na FONTE e' muito mais barato que descartar depois de duas horas
de corte.

## Guardas proprias deste canal

| guarda | pega |
|---|---|
| `engine/abertura.py` | corte que abre preso na receita anterior: "a mesma", "terminamos", "nossos", ordinal, palavra solta |
| idem, encerramento | "se inscreva" + "nosso podcast" + ... (piso de 2 marcas) |

O padrao por tras das duas: **regra no prompt nao basta.** Os 6 cortes orfaos
sairam de prompts que ja' proibiam aquilo. Prompt pede, guarda mede.
