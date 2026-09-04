# HANDOFF — 03/09/2026, parte 2 (sessao de MEDICAO)

⚠️ **Esta sessao nao mudou UMA LINHA do repo.** Nao houve conserto, nao houve
suite, nao houve commit de codigo. So' medicao. O unico arquivo novo e' este.
Se voce esta' procurando "o que ela fez", a resposta honesta e': confirmou que
o motor anda sozinho, e achou UMA coisa nova (secao 3).

Leia antes: `PIPELINE.md` (mapa) e `handoff/HANDOFF_03-09-2026.md` (caf1980).
Este arquivo e' um adendo aquele, nao um substituto.

---

## 1. ESTADO MEDIDO AS 22:26 UTC (o handoff anterior mediu 21:36)

    @truque.importado        9  (+48h)      @modofuturo   8  (+45h)
    @atefalhar               8  (+45h)      @semanestesia 4  (+21h)
    @cozinha.internacional   3  (+16h)  <- menor folga, e NAO e' deste motor
    TOTAL 32 posts agendados — nenhum canal vazio
    fonte: `python painel_filas.py`

    fila de cortes, lida da NUVEM (nao a foto local):
      17 pendente · 16 pronto · 1 disparado · 1 sem_fonte   (total 35)
      pendentes: semanestesia.pod 14 · atefalhar 3
    fonte: contents API de fila_cortes.json em poisonb9/Modo-Futuro

⚠️ O `fila_cortes.json` LOCAL dizia 18/14/2/1 — divergente, porque e' a foto do
ultimo commit. Isso e' o esperado (PIPELINE secao 6), nao e' defeito. Meça pela
API, sempre.

**Comparado com o handoff anterior: prontas subiram de 14 para 16.** O motor
produziu sem monitor nenhum, so' com cron + encadeamento — exatamente como a
secao 5 daquele handoff previu. Nao foi preciso reacender nada.

    vigia do RAW  vivo, ultima passada 22:12 (LENTO: 311s)
    corte em voo  1, despachado 21:50, ainda in_progress as 22:26 (36 min)
    cortar_fila   schedule 21:49 ok · workflow_run 20:48 e 20:40 ok

---

## 2. AS TRES FALHAS DE HOJE, E POR QUE NAO SAO DEFEITO

Runs de `cortar_de_bruto` que terminaram em failure: 18:12, 20:33, 20:41.
Os dois ultimos sao os dois videos de gluteos que o vigia despachou do RAW.

Todos morreram no MESMO passo, com a MESMA linha:

    [reserva] Gemini sem cota -> traduzido pelo Nemotron Ultra
    RuntimeError: Gemini falhou em escolha de clipes:
                  todas as chaves esgotadas em ['gemini-3.6-flash']

E' cota, nao codigo. A cota da nuvem vira 07:00 UTC.

⚠️ **A sonda LOCAL deu `3/5 vivas` as 22:24 e isso NAO desmente o de cima.**
Sao pools diferentes: 15 chaves no `.env` local, 27 nos secrets da nuvem. Quem
esgotou foi a da nuvem. Nao repita o erro da secao 7 do handoff anterior —
nao dei, e nao de', veredito de dia inteiro a partir de uma foto.

---

## 3. ⚠️ O ACHADO NOVO: A SELECAO NAO TEM RESERVA, A TRADUCAO TEM

Medido, lendo o codigo depois de ler o log:

    engine/traducao.py     TEM caminho de reserva -> Nemotron -> quarentena
    engine/selecao.py:473  `_pedir(..., "escolha de clipes", ...)`
                           NAO tem reserva. Sem Gemini, levanta e mata o run.

**A consequencia tem preco.** No run 33803772922 o vigia baixou 0,11 GB,
o motor traduziu (ja' caindo na reserva, as 20:46:52) e so' as 20:48:42 morreu
na selecao. Ou seja: **o run paga o download e a traducao inteira e so' entao
descobre que nao tem como escolher.** Tres runs de hoje morreram assim.

⚠️ **NAO CONSERTEI, E DE PROPOSITO.** Dar reserva a selecao muda *quais clipes
sao escolhidos pra publicar*, e o proprio `engine/traducao.py` (linhas ~266-282)
argumenta que o Nemotron e' reserva CARA de proposito, com quarentena, e nao
alternativa barata. Isso e' decisao do Bryan, nao guarda de manutencao.

Se ele mandar mexer, as duas opcoes honestas sao:
  (a) reserva na selecao + quarentena, igual a traducao (muda o que publica);
  (b) sondar a cota ANTES do download, e abortar barato (nao muda o que
      publica, so' para de queimar runner) — o mais conservador dos dois.

---

## 4. OS 5 PENDENTES DO BRYAN: NENHUM ANDOU

Continuam iguais aos da secao 6 do handoff de caf1980. Nenhum e' executavel
por mim:

  1. Write a `poisonb9` em `bryanaw2121-sketch/pipeline`, OU aplicar
     `scratchpad/conserto_fahrenheit.patch` com `git am`. Pronto, testado 18/18.
  2. Regenerar `GEMINI_API_KEY_2` (403 em todas as medicoes).
  3. Esvaziar a lixeira da conta principal (~2,7 GB).
  4. Video novo no RAW nas pastas `MODO FUTURO` e `Truque Importado`.
  5. Decidir sobre o clipe do cookie com "220°C Fahrenheit" (publicado, 173 views).

⚠️ **O item 1 e o item que mais aperta, e a medicao mostra porque:** ele
conserta a COZINHA, que e' justamente o canal de MENOR folga (+16h) e o unico
que este motor nao repoe. Os outros quatro canais tem 21h a 48h.

⚠️ **O item 4 esta' confirmado pela medicao, nao suposto:** os 17 pendentes sao
so' de semanestesia (14) e atefalhar (3). `modofuturo` e `truque.importado` tem
ZERO fonte pendente — vivem do estoque de 16 prontas. Quando acabar, param.

---

## 5. O QUE CONTINUA RODANDO SOZINHO (nada disto e' monitor meu)

    cron cortar_fila   */30, best-effort (1,8h a 4,8h medidos em 02/09)
    encadeamento       cada corte que termina dispara o cortar_fila
    vigia do RAW       10 em 10 min, 1 por passada
    desempenho.yml     de hora em hora

⚠️ Esta sessao nao deixou monitor nenhum. Nao ha' nada pra morrer com ela.

---

## 6. ARMADILHAS QUE ESTA SESSAO PAGOU (pequenas, mas custam minuto)

  - `clip_engine` NAO esta' em Documents. Mora em
    `Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine`.
  - Ler log do Actions no Windows quebra com `UnicodeEncodeError` (cp1252) se
    voce imprimir direto. Use `PYTHONIOENCODING=utf-8` e salve em arquivo antes.
  - O zip do log tem `0_cortar.txt` na raiz — filtrar o namelist por "Cortar"
    (maiusculo) devolve lista vazia.
  - Suite: `timeout 90` no laco, nunca 60 (herdado, nao remedido nesta sessao).

---

# ADENDO — 04/09/2026 18:15 UTC. ⚠️ LEIA ISTO PRIMEIRO.

A maquina ficou ~20h fora entre a secao 1 e este adendo. **Tudo acima esta'
velho.** E o que aconteceu nessas 20h contradiz a minha propria secao 2.

## O QUE EU ESCREVI ERRADO ACIMA

Escrevi "as falhas sao COTA, nao codigo". **Estava errado a partir das 23:41
de 03/09.** As falhas de ontem de tarde eram cota, sim. As de hoje sao OUTRO
defeito, e eu so' vi porque medi de novo em vez de herdar.

⚠️ A prova de que nao e' cota: **o lote das 07:00:24 UTC foi disparado NO
RESET da cota e falhou igual.**

## O DEFEITO: JANELA DE `recorte` DE 20 MIN ESTOURA O LIMITE DO GROQ

Do log (run 33895553257, e identico no 33846768614):

    [3/5] recorte manual 4692.0s->5892.0s (pula selecao do Gemini)
    [4/5] clipe 1/1 -> nota 92
          Groq transcrevendo (36.8 MB)...
       [!] clipe 1 perdido: clip_01.flac tem 36.8 MB, acima do limite de 25 MB
    [x] NENHUM clipe sobreviveu -> o run falha.

O caminho do `recorte` **pula a selecao do Gemini** e trata a janela INTEIRA
como um clipe so'. Toda janela tem 1200s = 20 min, o FLAC sai com 36-39 MB, e
o teto de upload do Groq e' 25 MB. **Nunca vai passar. Nao e' intermitente.**

⚠️ **Isto e' regressao do conserto de ontem** — `d485c51 "a fila aprende
recorte"`. O recurso entrou e nenhuma janela consegue transcrever.

## O ALCANCE, MEDIDO NA NUVEM (nao estimado)

    itens com `recorte`: 15 — TODOS de @semanestesia.pod
      3 desistido (ja' queimaram 3 tentativas cada) · 3 disparado · 9 pendente
      janelas vistas: 300-1500 · 1952-3152 · 3604-4804  (todas 1200s)

    itens sem `recorte`: 20 — 16 pronto · 1 sem_fonte · 3 pendente (atefalhar)
      ⚠️ estes estao SAOS. O defeito e' so' do caminho do recorte.

    fila agora: 16 pronto · 12 pendente · 3 disparado · 3 desistido · 1 sem_fonte

## O PRECO JA' PAGO, E O QUE AINDA VAI QUEIMAR

**12 runs seguidos falharam** desde 03/09 23:41, em lotes de 3
(23:41 · 07:00 · 12:02 · 16:30), cada um rodando 50-60 min antes de morrer.
Isso e' **~11 horas de runner ja' gastas, com zero clipe produzido.**

⚠️ **E nao parou.** Sobram 12 itens de recorte vivos x 3 tentativas =
ate' **36 runs** e ~33h de runner, todos com desfecho conhecido: falha.
A cada ~4h um lote novo dispara sozinho.

## O QUE EU NAO FIZ, E POR QUE

Nao consertei e nao mexi na fila. As duas saidas mudam coisa que e' decisao
do Bryan:

  (a) **partir a janela** em clipes curtos antes do Groq — resolve de vez, mas
      muda O QUE SE PUBLICA no @semanestesia (hoje a janela e' o clipe);
  (b) **so' estancar**: marcar os 12 itens de recorte como nao-pendente ate'
      (a) existir. Nao muda publicacao, so' para de queimar runner.

⚠️ Nao dispare corte na mao pra "testar" — o lote seguinte vem sozinho.

## ESTADO DOS POSTS: NAO MEDIDO NESTE ADENDO

⚠️ A secao 1 diz "32 posts, nenhum canal vazio" as 03/09 22:26. **Isso tem 20h
e NAO vale mais.** Rode `python painel_filas.py` antes de afirmar qualquer
coisa sobre folga de canal. @semanestesia estava com a menor folga entre os
canais deste motor (+21h) e e' exatamente o canal que parou de produzir.

---

# ADENDO 2 — 04/09 18:30 UTC. FEITO O (b), E O ESTOQUE ACABOU.

## O QUE EU FIZ (commit 19ed9eb, na nuvem)

Opcao (b), estancar. Os 12 itens de `recorte` ainda vivos (3 disparado +
9 pendente) foram marcados:

    "estado": "desistido"                         <- terminal, o motor honra
    "pausado_por": "groq_25mb_recorte_1200s"      <- pra opcao (a) achar
    "pausado_em": "2026-09-04"

Escolhi `desistido` porque **ja' e' terminal no codigo**: `cortar_fila.py:548`
so' despacha `pendente`, e nada revive `desistido`. **Zero mudanca de codigo,
logo zero risco de regressao.** Suite 49/49 (timeout 90).

Conferido item a item: 35 itens antes e depois, **nenhum campo perdido**, os
19 `run_id` preservados, `teto_em_voo` intacto. Nuvem confirma:

    16 pronto · 3 pendente · 15 desistido · 1 sem_fonte

Os 3 pendentes que sobraram sao de @atefalhar, sem `recorte` — caminho sao.

⚠️ **Pra reviver na opcao (a):** os exatos 12 sao os que tem `pausado_por ==
"groq_25mb_recorte_1200s"`. Os outros 3 `desistido` NAO sao meus — o motor
desistiu deles sozinho, pelo mesmo defeito, antes de eu chegar.

## ⚠️ O ACHADO MAIOR: A FABRICA ESTA' SECA

Medido as 18:30 com `painel_filas.py` — e comparar com a secao 1 (20h antes)
e' o susto:

                        03/09 22:26      04/09 18:30
    @modofuturo              8 (+45h)         5 (+25h)
    @truque.importado        9 (+48h)         6 (+28h)
    @atefalhar               8 (+45h)         5 (+25h)
    @semanestesia.pod        4 (+21h)         1 (+1h)   <- acaba em 1 HORA
    @cozinha.internacional   3 (+16h)         0 VAZIA   <- ja' acabou
    TOTAL                   32               17

**Consumiu 15 posts e repos ZERO.** E o log do `repor_fila` de hoje diz porque:

    148 clipe(s) no manifesto, 0 ainda nao agendado(s)
    0 clipe(s) enfileirado(s); 0 esperando a proxima vaga

⚠️ **Nao ha' estoque.** O catalogo inteiro ja' esta' agendado. A reposicao
diaria nao tem de onde tirar, e ela nao corta (PIPELINE secao 5). Os 16
`pronto` da fila de cortes tambem nao sao sobra — ja' foram agendados.

⚠️ E o `PIPELINE.md` esta' DESATUALIZADO na secao 5: ele diz que truque,
atefalhar e semanestesia ficam fora da reposicao por serem estreia. **Nao
ficam mais** — `engine/estreia.py` tem `ESTREIA_ATE` vazio desde 01/09. Nao
e' essa a causa da fila vazia; a causa e' que nao ha' clipe.

## ENTAO AS TRES SAIDAS SAO, E TODAS SAO DECISAO DO BRYAN

  1. **Video novo no RAW** em `MODO FUTURO` e `Truque Importado` — era o item 4
     dos pendentes, e agora e' A TRAVA, nao um lembrete. Sem fonte nova, esses
     dois canais nao tem como produzir NADA.
  2. **A opcao (a)** — partir a janela de 20 min em clipes curtos antes do
     Groq. E' o unico caminho que reacende o @semanestesia (15 janelas presas).
  3. **O item 1 dos pendentes** (Write no repo `pipeline`, ou aplicar o patch)
     — e' o unico caminho pro @cozinha, que ja' esta' VAZIO. Este motor nao
     serve aquele canal, por desenho.

⚠️ Estancar NAO produziu clipe nenhum. So' parou de queimar runner. A fila de
posts continua drenando enquanto nenhuma das tres acima acontecer.
