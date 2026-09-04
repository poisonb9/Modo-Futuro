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
de video longo cortado. Com canal NOVO entrando, dois deles saem da gaveta.

### 1.1 ⚠️ O default `or "modofuturo"` vira risco ATIVO  (defeito atual)

`agendar_buffer.py:535`

    (v.get("canal") or "modofuturo").strip().lower() == canal_deste_run

Clipe sem `canal` no manifesto e' tratado como modofuturo. Medido em
04/09/2026: os 161 clipes do manifesto TEM canal, entao hoje isto nao dispara.

⚠️ Mas foi exatamente este default que mandou oito clipes de podcast pro canal
de chips, e canal NOVO e' precisamente o caminho por onde entra clipe com
campo faltando — codigo novo, pipeline nova, campo esquecido.

O conserto e' o que o `canal_da_pasta` do vigia ja' faz: devolver None e
RECUSAR, em vez de chutar. Recusar custa um clipe nao agendado; chutar custa
um produto de afiliado publicado no canal de tecnologia.

### 1.2 ⚠️ Dois nomes para o mesmo canal  (defeito atual)

A cozinha se chama `cozinha.importada` em quatro lugares e
`cozinha.internacional` em quatro outros. O nome real no Buffer e'
`cozinha.importada` (medido: e' o que passa pela guarda CANAL_ESPERADO).

O caminho do estrago, hoje bloqueado por acidente: o vigia mapeia a pasta
`DOCES/` para `cozinha.internacional`; os workflows escolhem o token do Buffer
comparando com `cozinha.importada`; nao bate; cai no `else`; e o token que sai
e' o do **modofuturo**. So' nao acontece porque o `engine/escopo.py` barra a
cozinha antes — duas guardas independentes, e nenhuma sabe da outra.

⚠️ Para a fase 2 isto e' um MOLDE de erro, nao um caso isolado: cada canal
novo e' batizado em pelo menos seis arquivos, e nada confere que os seis
concordam. Antes de criar os dois canais de achadinhos, o nome do canal
precisa ter UMA fonte, e um teste que reprove divergencia.

### 1.3 O mecanismo de estreia volta a valer  (ja' pronto, so' usar)

`engine/estreia.py` esta' VAZIO desde 01/09 e o `PIPELINE.md` secao 5 ainda
diz o contrario — a doc esta' velha, o codigo esta' certo.

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

### 2.2 Link de afiliado nao existe no manifesto

O clipe hoje carrega titulo, descricao, tags, gancho, notas. Nao carrega
produto, preco, nem link. A pagina da bio e o grupo do WhatsApp precisam
LER isso de algum lugar, e esse lugar tem de ser o mesmo que a legenda usa —
senao o video diz um preco e a pagina diz outro.

⚠️ Decisao pendente: o produto vira campo do manifesto, ou vira um registro
proprio ao lado dele? O manifesto ja' e' lido por seis scripts.

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

  1. **1.1 e 1.2 primeiro** — sao os dois defeitos que canal novo transforma
     em publicacao no canal errado. Consertar ANTES de existir canal novo
     custa um dia; consertar depois custa um video de afiliado no canal de
     chips.
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
