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
