# Sabedoria — TikTok (documento SEMENTE, a completar)

> Criado em 26/07/2026. **Este arquivo ainda não é destilado de fontes de
> TikTok** — é uma semente montada de duas origens, marcadas abaixo:
>
> - `[YT→TT]` = vem de `SABEDORIA_YT.md` (cursos de YouTube). É **hipótese
>   transferida**, não fato verificado no TikTok. Tratar como suspeita a
>   confirmar, não como regra.
> - `[TESTADO]` = aprendido na prática nesta sessão, mexendo na API e na
>   conta de verdade. Isso é fato.
> - `[ABERTO]` = pergunta que nenhuma das duas origens responde. É o que o
>   usuário vai destilar.
>
> Regra ao editar: **não promova um `[YT→TT]` pra fato sem fonte de TikTok.**
> Foi confiar em intuição sobre ritmo de postagem que custou o canal do
> YouTube.

## Contexto: por que este arquivo existe

O canal de YouTube "Fatos na Língua" foi banido em 26/07/2026 por "Spam,
práticas enganosas e golpes", depois de uma rajada de ~8-10 vídeos em poucas
horas, todos do mesmo tema. A operação migrou pro TikTok (@cortes.na.lngua)
e o objetivo agora é **não repetir o erro por falta de conhecimento da
plataforma**.

---

## 1. Horário de postagem

### `[YT→TT]` Horário importa mais que frequência
Fonte: `SABEDORIA_YT.md:633` — *"A frequência de postagem de shorts não é o
fator determinante para o sucesso; o horário de postagem é mais importante."*

### `[YT→TT]` Não existe horário universal — é por conta
Fonte: `SABEDORIA_YT.md:634-638`. O melhor horário muda de canal pra canal e
se descobre no gráfico de atividade do próprio público. No caso do autor
citado, ~6h da manhã.
**Implicação prática:** nas primeiras semanas, variar horário de propósito
pra gerar dado, depois ler o painel do TikTok.

### `[YT→TT]` Postar 30-60 min ANTES do pico, não no pico
Fonte: `SABEDORIA_YT.md:734`. A ideia é o vídeo já estar em circulação
quando a audiência chega, não entrar no ar junto com ela. É o detalhe mais
acionável que a sabedoria de YouTube oferece sobre timing.

### `[YT→TT]` As primeiras 2-3 horas decidem o alcance
Fonte: `SABEDORIA_YT.md:735` e `:486-490`. No YouTube o vídeo é entregue
primeiro pra uma "bolha" de 300-2000 pessoas entre 30min e 3h após o post;
retenção, rewatch, engajamento e saídas nessa janela definem se escala pra
bolha seguinte.

### `[ABERTO]` Qual é a janela real do TikTok?
O TikTok tem um mecanismo análogo de teste inicial, mas os números
(tamanho da primeira entrega, duração da janela, limiares de retenção) são
diferentes e não temos fonte. **Destilar isso é prioridade 1** — é o que
governa tudo o resto.

### `[ABERTO]` Horários de pico no Brasil, com fonte
Os horários que estão hoje no `PADRAO.md` (manhã 6-9h, almoço 12-14h, noite
19-23h) são **chute genérico**, não vêm de fonte nenhuma. Substituir por
dado real assim que houver.

---

## 2. Ritmo e volume

### `[TESTADO]` O TikTok TEM limite de rascunhos pendentes — e chama de spam
Descoberto em 26/07/2026 às 09:11, na prática. Depois de mandar **5**
rascunhos pro inbox sem postar nenhum, o 6º foi recusado:

```
400 {"error":{"code":"spam_risk_too_many_pending_share",
              "message":"spam_risk_too_many_pending_share"}}
```

Três coisas importantes aqui:
1. **O limite existe e é baixo** — bateu em ~5-6 pendentes. Não sabemos o
   número exato nem se conta por janela de tempo. `[ABERTO]`
2. **A plataforma nomeia isso como `spam_risk`.** Não é limite técnico de
   armazenamento, é controle antispam explícito. O TikTok está dizendo qual
   comportamento ele considera suspeito.
3. **Funciona como freio natural de ritmo.** Só dá pra mandar mais depois de
   postar/limpar os pendentes — o que impede rajada por acidente.

**Implicação prática:** mandar rascunho em lote grande não funciona. O fluxo
saudável é mandar poucos, postar, e só então mandar mais.

### `[TESTADO]` Diagnóstico completo dos bloqueios (26/07/2026 ~21:27)
Três endpoints medidos na mesma sessão, com o mesmo token:

| endpoint | resultado |
|---|---|
| `post/publish/creator_info/query/` | **200 OK** |
| `post/publish/video/init/` (Direct Post) | **403** `unaudited_client_can_only_post_to_private_accounts` |
| `post/publish/inbox/video/init/` (rascunho) | **400** `spam_risk_too_many_pending_share` |

São **dois bloqueios independentes**, não o mesmo problema:
- Direct Post: barrado por **auditoria do app**. Não é limite de uso — não
  adianta esperar.
- Inbox: barrado por **contador de "pending share"**. É limite de uso.

`creator_info` é o melhor diagnóstico disponível: devolve o perfil e, útil,
`privacy_level_options` — que **inclui `PUBLIC_TO_EVERYONE`**. Ou seja, a
conta permite post público; quem barra o público é a falta de auditoria do
app, não a conta. Use esse endpoint antes de culpar token/conta.

### `[TESTADO]` REGRA DE OURO: nunca EXCLUA um rascunho — POSTE ou deixe expirar
Confirmado por medição em 26/07/2026 ~21:35, e é a coisa mais importante
deste documento sobre operação diária.

O usuário excluiu no app os 5 rascunhos pendentes pra "abrir vaga". Depois
disso, consultamos `post/publish/status/fetch/` com os 5 `publish_id`
originais. **Todos os 5 continuaram devolvendo `SEND_TO_USER_INBOX`.**

Ou seja: pra a API, o rascunho excluído **continua pendente**. O contador de
"pending share" só é liberado quando o vídeo é **realmente postado** — não
quando é apagado. E como o rascunho apagado não existe mais no app, não há
como postá-lo pra devolver a vaga: **a vaga fica presa**.

Consequências práticas:
- **Nunca excluir rascunho vindo da API.** Poste, mesmo que depois apague o
  post. Excluir o rascunho queima uma das ~5 vagas de forma (aparentemente)
  irrecuperável.
- Se as vagas travarem, sobra esperar expirar (o TikTok expira upload
  pendente depois de alguns dias — prazo exato `[ABERTO]`) ou postar pelo
  app com o arquivo na mão.
- `status/fetch/` com o `publish_id` é o jeito de saber se uma vaga está
  ocupada. Vale registrar os `publish_id` de cada envio (o
  `_publicados_tiktok.json` já faz isso).

### `[TESTADO]` Excluir os rascunhos NÃO libera na hora
Testado em 26/07/2026 ~21:00. O usuário excluiu os rascunhos pendentes no app
e o envio seguinte **continuou** recusado com o mesmo
`spam_risk_too_many_pending_share`.

Conclusão: **não é uma contagem simples de "quantos estão pendentes agora"**.
As hipóteses (nenhuma confirmada, `[ABERTO]`):
- é limite por janela de tempo (X envios por hora/dia), não por fila;
- o contador de "pending share" não zera quando o rascunho é excluído, só
  quando é postado de verdade;
- tentativas repetidas em sequência curta agravam o bloqueio (nós tentamos
  várias vezes em poucos minutos investigando o erro — pode ter piorado).

**Como agir até saber:** não insistir em rajada de tentativas — isso é
justamente o comportamento que o nome do erro denuncia. Esperar (ordem de
dezenas de minutos a horas) e tentar uma vez. Se for urgente, transferir os
`.mp4` na mão pro celular e postar pelo app, que não tem limite nenhum.

### `[ABERTO]` — AINDA EM ABERTO: qual o volume seguro de POSTS por dia?
O achado acima é sobre **rascunhos pendentes**, não sobre posts publicados.
São coisas diferentes e não devem ser confundidas.

O usuário escolheu **3-5 posts/dia**. A sabedoria de YouTube não responde
isso, e foi exatamente esse padrão (volume + mono-tema em conta nova) que
derrubou o canal anterior. O erro de `spam_risk` acima é um sinal de que a
plataforma é sensível a volume, mas **não é prova** sobre posts. Até ter
fonte, as mitigações acordadas são:
- variar o tema entre os posts (requisito, não sugestão);
- espaçar ao longo do dia, não em rajada.

### `[YT→TT]` Consistência bate perfeição
Fonte: `SABEDORIA_YT.md:939-940` — o algoritmo é "motor de frequência";
canais começam a ser recomendados ao chegar consistentemente em 10-20
vídeos. Não precisa de qualidade perfeita no começo, precisa de regularidade.

### `[YT→TT]` Mono-tema limita escala
Fonte: `SABEDORIA_YT.md:504` — tema muito específico limita o alcance
máximo; pra escalar além da bolha inicial o assunto precisa ser abrangente.
Reforça a decisão de variar tema.

---

## 3. Estrutura do vídeo

### `[YT→TT]` GPC — Gancho, Progresso, Clímax
Fonte: `SABEDORIA_YT.md:620-628`. Gancho nos primeiros segundos introduzindo
o tópico e deixando dúvida; progresso cumprindo a promessa; clímax
entregando exatamente o que foi prometido e fechando.
**Já implementado** no prompt do Gemini (`engine/selecao.py`).

### `[YT→TT]` Erros que travam o vídeo
Fonte: `SABEDORIA_YT.md:528-543`. Tela preta no fim, silêncio no início,
começar com logo, falar devagar, legenda ruim, visual "normal demais".
Terminar abruptamente (sem despedida) gera vontade de replay.
**Já implementado**: prompt proíbe despedida/CTA no clímax; e há checagem de
frame congelado nas duas bordas do clipe (`midia.pular_congelamento_inicial`
e `pular_congelamento_final`).

### `[YT→TT]` Choque visual nos primeiros 0.2-0.3s
Fonte: `SABEDORIA_YT.md:533-534`. **Não implementado** — hoje o corte começa
onde o Gemini escolheu, sem garantia de impacto visual no primeiro frame.
Candidato a melhoria se a retenção inicial vier baixa.

### `[ABERTO]` Duração ideal no TikTok
Hoje usamos 20-60s (`config.DUR_MIN`/`DUR_MAX`), herdado do limite de
Shorts. O TikTok aceita bem mais e a duração ótima pode ser outra.

---

## 4. Métricas a acompanhar

### `[YT→TT]` Números-alvo do YouTube Shorts
Fonte: `SABEDORIA_YT.md:518-532`. Servem de referência mental, **os nomes e
limiares do TikTok são outros**:
- VTR (assistiu até o fim): ideal >65%
- HCR (retenção nos 2 primeiros segundos): ideal >70%
- RPR (rewatch): ideal 15-25%
- CTR do perfil: >3% (ideal 3-8%)
- Taxa de inscrição: 1-2% das views

### `[ABERTO]` Equivalentes reais no painel do TikTok
Quais métricas o TikTok expõe, como se chamam, e qual valor é "bom".

---

## 5. Como a nossa integração funciona `[TESTADO]`

Tudo aqui foi verificado na prática nesta sessão.

### Conta e app
- Conta: **@cortes.na.lngua** (`open_id: -0000_YB1DLuMSTj42p1ws0ghm3Iaj49rxsm`)
- App Sandbox "Times Report", client key `sbaw1hzszvdhcxf0jw` (no `.env`)
- App de produção "Bryan Fatos" existe mas **não é auditado** e não foi
  submetido. Auditoria exigiria um **vídeo demo** gravado; **não** exige
  domínio verificado — no painel, "Verify domains" vale só pro método
  `pull_by_url`, e nós usamos `push_by_file`. Decisão de 26/07/2026:
  ficar no rascunho, sem auditar

### Direct Post não funciona sem auditoria
Erro exato: `403 unaudited_client_can_only_post_to_private_accounts`. App
não auditado só posta em conta **privada** — inútil, já que a conta precisa
ser pública pra crescer.

### O fluxo que funciona: rascunho no inbox
`publicar_tiktok.py --pasta "..."` manda pro inbox
(`post/publish/inbox/video/init/`). Status vira `SEND_TO_USER_INBOX`. O vídeo
chega como **notificação na Caixa de entrada do app**, NÃO em "Rascunhos" do
perfil (rascunhos do perfil são só os criados no próprio celular — isso
confunde). O usuário toca na notificação, cola a legenda e posta.
**Consequência:** o horário do post é 100% manual — não existe agendamento
de rascunho via API. Toda estratégia de timing depende do usuário.

### Pegadinha do OAuth (custou tempo)
O PKCE do TikTok **foge do padrão OAuth**: o `code_challenge` é o SHA256 em
**HEX**, não base64url. Com base64url o navegador diz "autorizado" e só a
troca do código falha (`Code verifier or code challenge is invalid`) —
parece que deu certo mas não gera token.

### Formato: só vertical
Decidido em 26/07/2026. O `main.py` não gera mais `fullscreen_16x9.mp4` por
padrão (`--com-horizontal` religa). TikTok é vertical-first.

### `[ABERTO]` Hashtags com acento
As tags que o Gemini gera saem acentuadas (`#robôhumanoide`,
`#robótica`). Não sabemos se acento prejudica descoberta no TikTok. Se
prejudicar, é ajuste de uma linha em `publicar_tiktok.py` (normalizar antes
de montar a legenda).

---

## 6. O que NÃO transfere do YouTube

A maior parte de `SABEDORIA_YT.md` é sobre um modelo de negócio diferente
(criar canal dark do zero com IA: avatares, InVideo, Suno, thumbnail no
Canva, nichos de música/futebol/infantil). **Nada disso se aplica** — nosso
motor corta vídeo real já existente. Ignorar essas seções ao destilar.

Também não transfere:
- Thumbnail / teste A/B de capa (TikTok usa frame do vídeo, lógica outra)
- Requisitos de monetização (YPP: 1000 inscritos + 4000h — TikTok tem regras
  próprias) `[ABERTO]`
- RPM: `SABEDORIA_YT.md` aponta RPM 4-8x maior em inglês. Vale no TikTok?
  `[ABERTO]` — e é relevante, porque já está decidido abrir um segundo canal
  100% em inglês depois.

---

## 7. Roteiro pra destilar (prioridade)

1. **Janela de teste inicial do TikTok** — tamanho da primeira entrega,
   duração, o que ele mede. Governa tudo.
2. **Volume seguro por dia em conta nova** — a pergunta que ficou aberta na
   decisão de 3-5/dia.
3. **Horário de pico real** (Brasil) e se a regra "30-60min antes do pico"
   vale lá.
4. **Métricas do painel**: nomes e valores-alvo.
5. **Duração ideal** de vídeo.
6. **Política de conteúdo reutilizado/cortes de terceiros** no TikTok —
   quão tolerante é de verdade.
7. Hashtags: quantidade ideal, acento, mistura de amplas + nicho.
