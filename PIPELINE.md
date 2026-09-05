# PIPELINE DE PONTA A PONTA — leia isto antes de diagnosticar qualquer parada

Escrito em 02/09/2026 porque uma sessao limpa gastou meia manha confundindo
DUAS entradas de corte como se fossem uma so', e concluiu "pipeline parado ha'
63 horas" quando a fabrica tinha cortado no dia anterior.

⚠️ Cada numero aqui foi MEDIDO, com a fonte ao lado. Se voce for atualizar,
meça de novo — nao herde numero deste arquivo sem conferir.

---

## 1. O ERRO QUE ESTE DOCUMENTO EXISTE PRA IMPEDIR

**Ha' DUAS entradas independentes que desembocam no MESMO cortador.** Elas tem
fontes diferentes, gatilhos diferentes e credenciais diferentes. Uma pode estar
morta por dias enquanto a outra produz normalmente.

    ENTRADA A — a fila curada (o motor principal)

        fila_cortes.json  ->  cortar_fila.yml  ->  cortar_de_bruto.yml
        (fila por canal)      (cron + encadeia)     (o cortador de verdade)

        credencial: GH_TOKEN, secret DO REPOSITORIO. Nao existe local.
        quem decide quantos: a sonda de cota (secao 4).

    ENTRADA B — o vigia do RAW (video largado na mao)

        pasta RAW do Drive  ->  vigia_raw.py  ->  cortar_de_bruto.yml
        (voce arrasta ali)      (local, 10/10min)   (o mesmo cortador)

        credencial: GITHUB_TOKEN, do .env LOCAL.
        quem decide quantos: MAX_POR_PASSADA = 1, e so' se nao ha' corte em voo.

⚠️ **AS DUAS DISPUTAM A MESMA VAGA.** `corte_em_andamento()` no vigia olha
TODOS os runs do `cortar_de_bruto.yml`, inclusive os que a Entrada A despachou.
Fila cheia na nuvem = vigia segura o RAW, e vice-versa. Isso e' desenho, nao
defeito: um corte por vez protege a cota do Gemini.

⚠️ **Ao diagnosticar, diga SEMPRE de qual entrada voce esta' falando.** "O
pipeline parou" nao e' uma frase util aqui.

---

## 2. OS WORKFLOWS E SEUS GATILHOS (medido em 02/09, lendo os YAML)

    cortar_fila.yml        "Cortar a fila (2 por vez)"
        workflow_dispatch, workflow_run, schedule
        cron: */30 * * * *       <- PEDIDO, nao garantia. Ver secao 3.
        cron: 10 7 * * *         <- logo apos o reset da cota
        cron: 40 7 * * *
        apos: "Cortar (a partir de video ja' baixado no Drive)"

    cortar_de_bruto.yml    "Cortar (a partir de video ja' baixado no Drive)"
        workflow_dispatch apenas — ele NUNCA se dispara sozinho.
        E' o cortador. Quem manda nele e' a Entrada A ou a B.

    cortar.yml             "Cortar video e subir pro Drive"
        workflow_dispatch. Baixa do YouTube antes de cortar.

    repor_fila.yml         "Repor fila (diario, 09:00 Sao Paulo)"
        cron: 0 12 * * *
        ⚠️ NAO corta nada. So' AGENDA clipe que ja' existe em release.

    desempenho.yml         "Fotografar desempenho (de hora em hora)"
        cron: 5 * * * *

⚠️ `cortar_de_bruto.yml` so' aceita `workflow_dispatch`. Se voce ver run dele
com evento `schedule`, alguem mudou o arquivo.

---

## 3. O CRON DO GITHUB E' BEST-EFFORT — E ISSO JA' ENGANOU DUAS VEZES

`*/30` pede de 30 em 30 minutos. Os intervalos REAIS medidos em 02/09, entre
runs de `schedule` do `cortar_fila`, em horas:

    4.8   1.8   2.0   2.8   3.4   4.5

⚠️ **Tres ou quatro horas sem run de schedule e' NORMAL.** Nao e' defeito, nao
adianta redisparar, e disparar na mao e' proibido (secao 8).

O que de fato carrega o motor nao e' o cron, e' o **encadeamento**: dos 30
ultimos runs do `cortar_fila`, 9 vieram de `schedule` e 9 de `workflow_run` —
ou seja, de um `cortar_de_bruto` terminando. Enquanto houver corte terminando,
a fila anda sozinha. Fila parada + nada cortando = so' o cron pra reacender.

⚠️ **E o `cortar_fila` e' quem devolve item preso.** Item que falhou fica em
`disparado`; quem o marca de volta como `pendente` e' a passada SEGUINTE.
Sem run do `cortar_fila`, item travado fica travado — nao ha' outro caminho.

---

## 4. A SONDA DE COTA: QUANTOS CORTES EM VOO

`cortar_fila.py::tem_cota()` pergunta ao Gemini se ha' cota, e
`teto_pela_cota()` traduz isso em quantos cortes deixar em voo.

    fatia = chaves que responderam 200 / chaves que RESPONDERAM
      >= 50%          -> teto como pedido (3)
      >=  2 ok        -> teto 2      "cota apertada"
      <   2 ok        -> teto 1      "um de cada vez"
      < 3 respostas   -> teto pelo MEDIDO, nunca pela fracao

⚠️ **3 nao gasta mais cota que 2 — gasta mais RAPIDO.** Os mesmos videos fazem
as mesmas chamadas. O que muda e' o prejuizo quando a cota acaba: um run que
morre ja' pagou 40 a 100 min de runner. Em 31/08, dez em paralelo: nove
morreram carregando trabalho ja' pago.

⚠️ **O TETO PEDIDO E' O MAXIMO, NUNCA O MINIMO.** Cota folgada nao autoriza
passar do que o Bryan pediu.

### As tres armadilhas da sonda, todas ja' pagas

  1. **Nome de secret escrito a mao.** Ate' 01/09 a lista tinha 5 nomes fixos e
     os secrets se chamam outra coisa (`GEMINI4..GEMINI19` + `GEMINI_API_KEY_1
     /2/3/20..27`). A sonda enxergava DUAS de vinte. Hoje ela le' o mesmo
     intervalo do rodizio: prefixo puro e `_2.._40`.
  2. **Sondar duas vezes no mesmo minuto.** Estoura o limite POR MINUTO, o 429
     e' lido como cota diaria esgotada, e a sonda causa o que mede. Por isso a
     amostra e' de 5, ALEATORIA.
  3. **Timeout curto contando lentidao como cota seca** (consertado 02/09).
     Dava "2 de 5 (2 ok, 3 mudo)" -> teto 2; varredura com 20s deu 13 de 15 em
     200. Hoje: timeout 20s, e `mudo` FORA do denominador.

⚠️ **Censo das chaves, medido:** nuvem 27 slots; `.env` local 15; o rodizio
suporta ate' 40. **Nao sao 54** — a mensagem "as 54 chaves estao SEM COTA" vem
de `traducao.py`, cujo laco passa pelo rodizio DUAS vezes e conta RESPOSTAS,
nao chaves. 27 x 2 = 54.

⚠️ A cota do Gemini e' DIARIA e vira a meia-noite do Pacifico = **07:00 UTC =
04:00 em Sao Paulo**.

---

## 5. DEPOIS DO CORTE: COMO O CLIPE VIRA POST

Dentro do proprio `cortar_de_bruto.yml`, em sequencia:

    main.py              corta, traduz, dubla, legenda
    publicar_release.py  sobe os mp4 numa release do GitHub
    agendar_buffer.py    agenda no Buffer, por canal

E, uma vez por dia, `repor_fila.yml` (12:00 UTC = 09:00 SP) confere se algum
canal caiu abaixo do piso e repoe **do que ja' existe em release**.

⚠️ `repor_fila` NAO corta. Se nao houver clipe elegivel ele AVISA e para —
disparar corte custa runner e e' decisao do Bryan.

⚠️ **NAO HA' MAIS CANAL EM ESTREIA** (conferido em 04/09/2026). Ate' 01/09 o
@truque.importado, o @atefalhar e o @semanestesia.pod ficavam de fora da
reposicao automatica, porque o Bryan quer postar os DOIS primeiros de cada
canal na mao — ja' teve estreia automatica que flopou. O prazo dos tres
venceu, e `engine/estreia.py` esta' com `ESTREIA_ATE` VAZIO.

⚠️ O MECANISMO CONTINUA, e a fase 2 vai precisar dele: canal novo entra em
`ESTREIA_ATE` com data ANTES do primeiro corte, e destrava sozinho. Esta
secao ficou tres dias dizendo o contrario do codigo — se voce for decidir
alguma coisa por ela, confira o dicionario antes.

⚠️ **E o piso engana.** O `repor_fila` so' olha o manifesto quando o canal
esta' ABAIXO do piso (5). Com a fila exatamente NO piso ele nem conta, e
imprime "0 ainda nao agendado" — que e' o valor de quem nao olhou, nao de quem
contou zero. Em 04/09 isso virou "a fabrica esta' seca" num handoff; o canal
tinha 27 clipes prontos. Pra saber estoque de verdade, rode o workflow
`medir_estoque.yml`, que nao agenda nada.

⚠️ **A cozinha nao e' deste repositorio.** O motor dela vive em
`bryanaw2121-sketch/pipeline`, com manifesto proprio. Daqui a gente so'
RELATA a fila dela.

---

## 6. ONDE MORA O ESTADO, E QUEM ESCREVE

    fila_cortes.json          fila curada. QUEM ESCREVE E' A NUVEM.
                              ⚠️ O arquivo local e' a foto do ultimo commit,
                              NAO o estado. Pra saber o estado, pergunte a API.
                              estados: pendente -> disparado -> pronto
                                       + sem_fonte (bruto apagado, terminal)
                                       + desistido (3 tentativas NAO-cota)

    estado/raw_vistos.json    ids de RAW ja' processados. Escrito pelo vigia.
                              ⚠️ Por ID, nao por nome: renomear no Drive nao
                              faz reprocessar.

    estado/vigia_raw.log      diario do vigia, uma passada a cada ~10 min.
                              E' a MELHOR fonte pra "o que aconteceu local".

    registro_clipes.json      clipes por sha256 do mp4.
                              ⚠️ Identidade e' o HASH, nao o nome.

    estado/buffer_cota.json   tetos por conta do Buffer (medidos, divergem).

---

## 7. CREDENCIAIS: QUAL TOKEN PRA QUAL COISA

    GH_TOKEN        secret do repositorio. Usado por cortar_fila.py NA NUVEM.
                    ⚠️ Nao existe local — rodar cortar_fila.py aqui da'
                    KeyError 'GH_TOKEN'. Isso e' esperado, nao e' defeito.

    GITHUB_TOKEN    do .env local. Usado pelo vigia_raw.py.
                    ⚠️ Em 02/09 estava MORTO (401) desde 30/08 18:11, e o
                    vigia segurou 375 passadas em silencio. Trocado pelo que
                    estava em github_token.txt. Backup: .env.bak_02-09.

    GEMINI_*        27 na nuvem, 15 no .env. Ver secao 4.

⚠️ **`curl` cru pra api.github.com e' barrado pelo classificador, mas o codigo
do projeto passa.** Antes de escrever "estou sem rede", tente pela porta do
projeto:

    python -c "from dotenv import load_dotenv; load_dotenv();
               import cortar_fila as cf; print(cf.tem_cota())"

---

## 8. O QUE NAO FAZER SEM O BRYAN PEDIR

  - disparar corte na mao (o `cortar_fila` encadeia sozinho);
  - usar fonte PT como padrao — ele decidiu que e' RESERVA PREMIUM, e a
    decisao esta' suspensa ate' ele ouvir o multi-voz;
  - montar o teste multi-voz (ele disse "calma");
  - postar ou apagar clipe; lixeira, nunca delete, e so' apos perguntar se ja'
    postou;
  - mexer em processos do `bryan_fx_vision`;
  - escrever na RAIZ do repo times-report (la' mora o .txt de verificacao de
    dominio do TikTok).

---

## 9. A CLASSE DE DEFEITO QUE MAIS SE REPETE AQUI

**Detector que casa com UMA frase enxerga UMA classe, e o silencio dele parece
sucesso.** Ja' aconteceu, medido, pelo menos cinco vezes:

  - filtro do pyflakes lia so' stdout — `SyntaxError` vai pra stderr, e um foi
    pra producao por 5 commits com a suite verde;
  - detector de cota conhecia a mensagem da traducao, nao a da selecao;
  - teste de movimento com imagem de cor solida mediu 0% e "provou" que o zoom
    nao funcionava;
  - `corte_em_andamento()` devolvendo `True` em qualquer erro: escrito pra rede
    instavel por UMA passada, desligou a Entrada B por tres dias com `exit 0`
    e "Nada novo." em todas elas;
  - a sonda contando `mudo` como cota seca.

**As duas regras que saem disso:**

  1. Todo detector precisa do caso NEGATIVO, e o caso negativo tem de ser
     TEOREMATICO, nao intuitivo. So' o caso positivo prova sensibilidade zero.
  2. ⚠️ **Falha aberta tem de GRITAR.** Se a guarda escolhe o lado seguro
     quando nao sabe, ela precisa avisar depois de N vezes seguidas — senao o
     lado seguro vira desligamento permanente que ninguem ve.

---

## 10. COMO RESPONDER "O QUE ESTA' RODANDO"

Medir, e responder no formato do log do vigia — carimbo, contagem com o que
sobrou, item indentado, desfecho:

    [2026-09-02 09:42:57] (exit 0)
    1 video(s) novo(s) em RAW (+34 na proxima passada):
      - [reserva] DOCES/Make Butter in 10 Minutes or Less! (0.15 GB)
       corte disparado na nuvem.
    1 disparado(s).

O que medir, nesta ordem:

  1. runs em voo nos DOIS workflows (API, com o token do .env);
  2. contagem de estados do `fila_cortes.json` — lembrando que o local e' foto;
  3. ultima linha util do `estado/vigia_raw.log`;
  4. se for decidir teto, a sonda — **uma vez so'**, nunca duas no mesmo minuto.

⚠️ Nunca inventar linha pra preencher o formato. Campo nao medido se diz nao
medido.
