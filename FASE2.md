# FASE 2 — canais de achadinhos (TikTok + Instagram, afiliados)

Escrito em 04/09/2026, depois da revisao dos cinco canais atuais.

O QUE E' A FASE 2, nas palavras do Bryan: dois canais de achadinhos, um no
TikTok e um no Instagram, publicando video de produto com link de afiliado;
uma pagina na bio com esses produtos; e um grupo de WhatsApp onde entram
esses e outros produtos. A intencao declarada e' VENDER, nao alcance.

⚠️ Este documento separa TRES coisas que se confundem facil: (1) defeito atual
que a fase 2 transforma em risco, (2) o que a fase 2 precisa e NAO existe
aqui, (3) o que ja' esta' pronto e serve. Cada item diz qual e'.

---

## 1. O QUE MUDA DE TAMANHO PORQUE A FASE 2 EXISTE

Tres achados da revisao eram "latentes" enquanto os canais eram cinco e todos
de video longo cortado. Com canal NOVO entrando, dois deles saiam da gaveta.

⚠️ **ATUALIZADO 09/09/2026: os tres estao fechados.** A secao fica porque ela
conta POR QUE cada um precisava ser consertado antes do canal novo — e o canal
novo chegou em 09/09. Nao ha' acao pendente aqui; se voce esta' procurando
trabalho, va' pra §2.

### 1.1 O default `or "modofuturo"` — ✅ RESOLVIDO 04/09/2026

**Era** `agendar_buffer.py`:

    (v.get("canal") or "modofuturo").strip().lower() == canal_deste_run

Clipe sem `canal` no manifesto era tratado como modofuturo — foi este default
que mandou oito clipes de podcast pro canal de chips, e QUATRO chegaram a ser
agendados.

**Hoje** o agendador resolve pelo registro e ausencia e' RECUSA:

    c = canais_registro.canonico(v.get("canal"))
    return bool(c) and c == canal_deste_run

`canonico` devolve None pra desconhecido, nunca um palpite.
`teste/teste_canais_registro.py` guarda os dois lados: a linha literal
`or "modofuturo"` nao pode voltar ao agendador (o defeito ERA uma grafia), e
o caso negativo exige que canal desconhecido, vazio e None devolvam None —
sem ele, um resolvedor que sempre devolve algo passaria e reproduziria o
defeito.

### 1.2 Dois nomes para o mesmo canal — ✅ RESOLVIDO 04/09/2026

A cozinha se chama `cozinha.importada` em quatro lugares e
`cozinha.internacional` em quatro outros. O nome real no Buffer e'
`cozinha.importada` (medido: e' o que passa pela guarda CANAL_ESPERADO).

O caminho do estrago, hoje bloqueado por acidente: o vigia mapeia a pasta
`DOCES/` para `cozinha.internacional`; os workflows escolhem o token do Buffer
comparando com `cozinha.importada`; nao bate; cai no `else`; e o token que sai
e' o do **modofuturo**. So' nao acontece porque o `engine/escopo.py` barra a
cozinha antes — duas guardas independentes, e nenhuma sabe da outra.

⚠️ Para a fase 2 isto era um MOLDE de erro, nao um caso isolado: cada canal
novo era batizado em pelo menos seis arquivos, e nada conferia que os seis
concordavam.

**O conserto:** `engine/canais_registro.py` e' a fonte UNICA. O nome real do
Buffer e' o canonico (`cozinha.importada`) e `cozinha.internacional` entrou
como APELIDO, junto com o `@` do TikTok — os dois resolvem pro mesmo canal em
vez de competir. `teste/teste_canais_registro.py` reprova divergencia: compara
as tabelas que `conferir_postados`, `escolher_impulsionar`, `painel_filas`,
`registrar_desempenho` e `repor_fila` publicam, e acusa quando duas discordam.

⚠️ O que continua valendo da licao: canal novo se cadastra NUM lugar so'. Foi
assim que os dois canais novos de 09/09 entraram (§2.5).

### 1.3 O mecanismo de estreia volta a valer  (ja' pronto, so' usar)

`engine/estreia.py` esta' com `ESTREIA_ATE` VAZIO desde 01/09 — os tres canais
que estavam la' venceram o prazo. ⚠️ A `PIPELINE.md` §5 ficou tres dias
dizendo o contrario e **ja' foi corrigida em 04/09**; a tabela vazia e' o
estado certo, nao um esquecimento.

O Bryan ja' pediu, para os canais anteriores, postar os DOIS primeiros videos
na mao: houve estreia automatica que flopou. Os dois canais de achadinhos
entram em `ESTREIA_ATE` com data ANTES do primeiro corte, nao depois.

---

## 2. O QUE A FASE 2 PRECISA E NAO EXISTE AQUI

⚠️ Nada disto e' conserto. E' construcao, e cada linha e' uma decisao do
Bryan que eu nao vou tomar sozinho.

### 2.1 Instagram nunca passou por este motor

Todo o caminho de publicacao e' TikTok, e nao por acaso — esta' no codigo:

    metadata: {"tiktok": {"isAiGenerated": True, "title": ...}}
    canais filtrados por service == TikTok
    LIMITE_FILA, SLOTS_SP, MAX_POR_DIA calibrados na cadencia do TikTok

O Buffer publica no Instagram, entao o caminho existe — mas o campo de
metadados e' outro, o formato aceito e' outro (Reels tem regra propria), e a
guarda `CANAL_ESPERADO` compara nome de canal do Buffer sem olhar servico:
**hoje um canal do Instagram com o mesmo nome passaria pela guarda.**

### 2.2 Link de afiliado nao existe no manifesto  — ✅ RESOLVIDO 09/09/2026

**DECISAO: vai no MANIFESTO, como campo aninhado `produto`.**

O argumento contra era "o manifesto ja' e' lido por seis scripts". O que
decidiu nao foi quantos leem, foi a frase abaixo, desta propria secao: o preco
tem de sair do MESMO lugar que a legenda usa. A legenda e' montada a partir do
manifesto; registro separado criaria duas fontes para o mesmo preco, e duas
fontes divergem. E' o mesmo raciocinio que ja' pos `sha`, `fonte_id` e
`depende_de_anterior` la' dentro.

Aninhado num campo so' (`produto`) e AUSENTE nos cinco canais de hoje —
ausente quer dizer "este clipe nao e' de afiliado", diferente de vazio. Os
seis leitores atuais pegam chaves nomeadas; chave nova nao quebra nenhum.

    engine/produto.py                    valida e normaliza, num lugar so'
    publicar_release.py                  carrega pro manifesto
    teste/teste_produto_no_manifesto.py  guarda, com caso negativo

⚠️ PRECO E' TEXTO, com `preco_em`. Numero envelhece calado: o clipe diria
"R$ 39,90" pra sempre enquanto a loja ja' mudou.

⚠️ LINK SO' http(s), falha FECHADA. `javascript:` e `intent://` nao sao link
torto — sao vetor de ataque numa pagina que a gente publica.

E `produto.linha_da_lista()` devolve a linha pronta pro grupo do WhatsApp,
que e' a unica coisa que este repo pode entregar ao grupo hoje (§2.5).

---

### 2.3 A fonte do video muda de natureza

Os cinco canais atuais cortam video longo de terceiro. Achadinho e' video
CURTO de produto — e o motor inteiro (selecao do Gemini, ancoragem, DUR_MIN
de 65s por monetizacao) foi calibrado para o primeiro caso.

⚠️ `DUR_MIN = 65` e' regra de DINHEIRO no TikTok, nao estetica. Para venda por
afiliado o incentivo e' outro, e manter 65s por inercia pode ser errado. Isto
e' decisao do Bryan, com numero na mao, nao palpite meu.

### 2.4 Divulgacao obrigatoria de afiliado

Conteudo pago/afiliado tem regra propria de divulgacao no TikTok e no
Instagram, e ela e' SEPARADA do rotulo de IA que ja' marcamos
(`isAiGenerated`). Um video de achadinho com voz clonada precisa dos DOIS.

⚠️ Nao medi as regras atuais das duas plataformas. Antes de publicar o
primeiro, alguem tem de ler a politica vigente — a de afiliado muda mais que
a de IA.

### 2.5 O grupo de WhatsApp esta' fora de tudo

Nao ha' integracao, nao ha' credencial, nao ha' script. E' frente nova
inteira, e a unica coisa que este repositorio pode oferecer de imediato e' a
LISTA (qual produto, qual link, qual clipe) — publicar no grupo e' outro
problema.

#### ⚠️ ATUALIZADO EM 09/09/2026 — os dois canais existem, e o grupo foi decidido

**As duas contas ja' foram criadas no TikTok**, e este repositorio nao sabia:
a tela "Mudar de conta" do app mostra SETE contas e o `canais_registro` tinha
CINCO. As faltantes:

    @achadinhos.instantaneos   0 posts · 0 seguidores · sem bio
    @fatura.chora              (icone de carrinho)

Agora estao registradas em `engine/canais_registro.py`, com `motor=False` e
com os campos do Buffer **VAZIOS** — elas nao existem no Buffer e nao ha'
token. `teste/teste_canal_sem_buffer.py` guarda isso: quando ganharem token,
o teste acusa, e e' o lembrete de preencher os tres campos no mesmo commit.

**Decisao do Bryan em 09/09:** os canais Achadinho apontam para o **grupo de
WhatsApp**. Isso muda a ordem da §4 — o 2.5 deixa de ser "por ultimo porque
nao bloqueia ninguem" e vira o **destino** do funil. Continua sem bloquear
codigo (criar o grupo e' acao manual dele), mas o que este repo precisa
entregar fica mais claro: **a LISTA**, no formato que o grupo le'.

⚠️ E fica um risco novo, que so' existe porque os canais Achadinho agora sao
DOIS (`make` e `chef`) mais os dois puros: se todos apontarem para o MESMO
grupo, nao havera' como saber qual canal traz gente. **A medicao mais barata
e' um link de convite por canal** — mesmo grupo, convites diferentes. Decidir
isso ANTES de por o link na bio; depois, nao ha' como separar.

⚠️ O defeito da §1.1 (`or "modofuturo"`) seria o risco destes dois canais
novos: clipe de afiliado sem `canal` no manifesto iria pro canal de chips.
**Ele ja' estava consertado antes de eles existirem** — o agendador recusa em
vez de chutar. E' o unico item desta secao que nao precisa de acao.

---

## 3. O QUE JA' SERVE, SEM MUDANCA

  - o vigia do RAW: pasta nova -> canal novo, so' acrescentar ao
    `MAPA_PASTA_CANAL` (e ele RECUSA pasta que nao conhece, que e' o certo);
  - `engine/escopo.py`: os canais novos entram em `CANAIS_DO_MOTOR`, senao o
    motor recusa — e recusar por engano e' barato, o contrario nao;
  - a fila de cortes, o encadeamento e o cron: nao sabem de canal, so' de item;
  - `publicar_release.py` + manifesto: guardam clipe de qualquer canal;
  - `medir_estoque.py` (novo, 04/09): mede canal novo no dia em que ele nascer,
    sem agendar nada;
  - as guardas de duplicata por sha256 e por trecho: sao por conteudo, nao por
    canal, entao valem de graca nos canais novos.

---

## 4. ORDEM PROPOSTA (a discutir, nao decidida)

⚠️ Isto e' proposta. A ordem real e' do Bryan.

  1. ~~**1.1 e 1.2 primeiro**~~ — ✅ FEITOS em 04/09/2026, e a ordem se
     provou certa: os dois canais novos apareceram em 09/09 e encontraram o
     agendador ja' recusando ausencia de canal.
  2. **Os dois consertos ja' autorizados** (o `recorte` de 20 min e a sonda de
     cota antes do download) — o primeiro reacende 15 janelas do
     @semanestesia, o segundo para de queimar runner.
  3. **2.1 (Instagram)** — decidir se o Buffer serve, e ensinar a guarda a
     olhar o SERVICO alem do nome.
  4. **2.2 (produto/link no manifesto)** — e' o que a pagina da bio e o grupo
     vao ler; define o formato de tudo depois.
  5. **2.3 e 2.4** — duracao e divulgacao, com numero e politica medidos.
  6. **2.5 (WhatsApp)** — por ultimo, porque nao bloqueia nenhum dos outros.

⚠️ E uma coisa que NAO entra nesta lista: o @truque.importado tem 1 clipe
pronto e fila de +25h (medido 04/09). Ele seca antes de qualquer item acima
ficar pronto, e a saida e' video novo no RAW — nao e' trabalho de codigo.
