# RETOMADA -- 21/09/2026, o grafico de GANHO

Clone canonico: `ATUALIZADA/clip_engine` (repo `poisonb9/Modo-Futuro`, branch
`main`). HEAD ao escrever: **b8a265a** "precos: instantaneo do catalogo".

## ESTADO: ha' trabalho NAO COMMITADO na arvore

Nada disto esta' no git. Sobrevive a reinicio (esta' em disco), mas e' a
primeira coisa a resolver.

    paginas/publicar_bio.py   +81/-2   piso da foto 9, corte medido, backspace
    paginas/todos.html        +34      brilho do foguinho, grafico colado na economia
    estado/fotos_julgadas.json         cache 69 -> 138 de 148
    (DIARIO, radar, estado/* -- rotina das tarefas agendadas)

### 1. Piso da nota da foto: 7 -> 9, MEDIDO

O 7 era chute meu, tirado de uma afericao de SEIS fotos. Com 138 julgadas:

    nota 10 ... 18 limpas / 0 sujas     piso  7 ... 32 sujas de 77 (42%)
    nota  9 ... 20 limpas / 2 sujas     piso  8 ... 11 de 56 (20%)
    nota  8 ...  7 limpas / 9 sujas     piso  9 ...  2 de 40 ( 5%)
    nota <=7 .. 0 limpas / 61 sujas     piso 10 ...  0 de 18 ( 0%)

"Limpa" = sem colagem, sem texto queimado, fundo limpo, produto inteiro.
**Abaixo de 8 nao existe uma unica foto limpa.** Era o piso 7 a porta por
onde a colagem de 4 cenas entrou na capa.

9 e nao 10: o 10 descarta 27 das 45 limpas para ganhar 2 sujas a menos.

MEDIDO no catalogo de hoje: **2 candidatos a capa com piso 7, 8, 9 E 10** --
as duas fotos que chegam ao fim da regua tiram 10. Apertar nao custa nada hoje.

CORRECAO do que eu disse antes: a distribuicao **nao e' bimodal**. Com 69
julgadas eu afirmei que era e que havia um "vale" no 7. Com 138 ele sumiu --
era tamanho de amostra.

### 2. O `` que virou 0x08 -- JA' ESTAVA NO HEAD

Em `externalizar_motor`, o `(?![^>]*src=)` tinha um byte 0x08 (backspace)
no lugar do ``. Efeito: a lookahead nunca casava, ou seja a funcao **nao
pulava scripts com `src`**. Hoje inofensivo (corpo vazio, escolha e' por
tamanho), mas passou por commit e por suite verde.

ARMADILHA NOVA, e ela e' cruel: `sed -n '2353p'` imprimiu a linha e o
TERMINAL executou o backspace, apagando o caractere anterior na tela. A linha
parecia consertada e nao estava. So' `open(...,'rb')` diz a verdade.
Consertado por troca de BYTES, com caso positivo e negativo provados
(pula `<script src=...>`, pega `<script>` inline).

### 3. Vitrine: brilho e proximidade

- foguinho com brilho sutil (dois halos fracos, SEM animacao -- brilho que
  pulsa vira alarme);
- o grafico saiu de 16 px para **6 px** da linha verde "voce economiza", na
  mesma coluna (left 34 nos dois, medido a 430 px claro). Ele e' a PROVA da
  economia, nao um terceiro assunto.

## O PROXIMO BLOCO, ja' escrito e NAO APLICADO

Pedido do Bryan: *"eu quero ele de cabeca pra baixo para mostrar que a queda
e' positiva em favor do nosso cliente"*, e depois *"economia mas do preco
inicial para o preco mais em conta agora"*.

DECISAO: **nao inverter o eixo do preco** (isso e' o grafico invertido
classico, linha subindo enquanto o preco cai, sem nada dizendo -- a familia
do "a pagina passa a mentir sozinha"). Em vez disso troca-se O QUE e'
plotado: a linha passa a ser ECONOMIA (`riscado - preco` de cada dia),
ancorada no ZERO.

    preco     11,79 11,99 11,89  19,73 19,61 11,89   desce no fim
    economia   7,94  7,74  7,84   0,00  0,12  7,84   SOBE no fim

A linha termina exatamente no R$ 7,84 verde que esta' logo acima dela.

O patch esta' pronto no scratchpad da sessao:
`.../scratchpad/patch_grafico_ganho.py` -- 6 ancoras, todas com `assert`.
Se o scratchpad sumir: a mudanca e' em `grafico(p)` em `paginas/todos.html`
(modo `p.ganhoRef`, base zero, `vals` trocado antes do `pts`, o `<title>` e a
classe `.ganho` acompanhando) e uma linha no chamador da capa setando
`v1.ganhoRef = (vA > 0 && vA > vB) ? vA : 0` -- `vA` ja' existe ali, e' o
mesmo numero do "voce economiza". NAO calcular a referencia duas vezes.

## SUITE

- suite22: **121 passou, 0 falhou** -- mas eu editei `publicar_bio.py` NO MEIO
  dela. Nao vale para o piso 9 nem para o backspace.
- suite23 (limpa) estava disparando quando o Bryan pediu o handoff.
- Lancador: `bash scratchpad/rodar_suite.sh <saida>` -- sao SCRIPTS, nao
  pytest. `python -m pytest teste` devolve "no tests ran" e EXIT 0: falso
  verde, eu cai nele hoje.

## DECIDIDO NESTA SESSAO

- **19,73 era preco de verdade** (Bryan conferiu no anuncio: hoje esta'
  11,89). A serie esta' honesta, o "economiza R$ 7,84" e o "40%" sao
  verdadeiros, e o `serie_limpa` fica como esta' (o 1,8x derrubou o 27,54,
  que era ruido, e preservou o 19,73, que era preco).
- **Sem pastas no Drive.** Bryan: "nao vou jogar foto para editar pelo drive".
  O roteador e' o Actions que ja' existe (`poisonb9/visao-fotos`), que puxa do
  CDN. O que faltara' no dia do motor de edicao e' ONDE hospedar o pixel novo
  (candidato: o Pages do proprio site).
- **Serie horaria gravando**: 7 carimbos hoje, 166 produtos, em
  `estado/precos_horas.jsonl` (gitignorado, rotativo 10 dias). Ela so' passa a
  alimentar o grafico quando cobrir 2 dias -- limiar em `_serie_curta`
  (`len(horas) >= 8 and len(dias) >= 2`).

## FILA, na ordem

1. rodar a suite LIMPA e so' entao commitar tudo acima;
2. aplicar `patch_grafico_ganho.py`, conferir a 430 px CLARO (nao 380 escuro
   -- o cartao tem aspect-ratio fixo e a proporcao muda com a largura), suite,
   commit, publicar;
3. guarda de bytes de controle no carimbador -- o 0x08 apareceu DUAS vezes
   no projeto; erro que reincide vira guarda, nao nota;
4. **AWIN** -- parada o dia inteiro, e e' a unica frente que mexe em dinheiro
   novo;
5. `melhor_foto()` esta' escrita em `engine/foto_julga.py` e NAO ligada: hoje
   foto ruim DESQUALIFICA o produto em vez de trocar por uma extra boa;
6. faltam 10 de 148 fotos por julgar;
7. divergencia do clone `Modo-Futuro` (baseado em hashes que o rebase do
   vigia reescreveu);
8. backup antes de reorganizar pastas (as tarefas agendadas usam caminho fixo).

## FALHA ABERTA, dita de proposito

`foto_julga.serve_de_capa` falha ABERTO: foto sem julgamento PASSA. E' de
proposito -- a guarda nao pode esvaziar a capa quando a API esta' fora -- mas
com o piso em 9 ela e' a unica porta que sobrou.
