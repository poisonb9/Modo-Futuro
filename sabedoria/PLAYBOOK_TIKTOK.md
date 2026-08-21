# PLAYBOOK TIKTOK — Modo Futuro

> **Este é o documento operacional do canal.** Regras e definições que vamos
> seguir. Se um script, config ou hábito diverge daqui, este arquivo vence —
> a menos que o usuário peça exceção pontual.
>
> Criado em 27/07/2026, destilado de **178 vídeos** de 3 canais brasileiros
> que ensinam TikTok (corpus em `sabedoria-tiktok/destilacao/`), cruzado com
> o que já medimos na prática (`SABEDORIA_TIKTOK.md`).
>
> Substitui o "Roteiro pra destilar" do `SABEDORIA_TIKTOK.md` — as 7
> perguntas estão respondidas na seção 13, com as que continuam abertas
> marcadas honestamente.

---

## 0. Como ler este documento

Cada regra vem com a força da evidência. **Não promova uma regra fraca a
verdade sem teste.** Foi confiar em intuição sobre ritmo que custou o canal
do YouTube.

| Marca | Significado |
|---|---|
| `[OFICIAL]` | Documentação do próprio TikTok. **Vence tudo.** |
| `[PAPER]` | Literatura revisada por pares (via Consensus). |
| `[TESTADO]` | Medimos na nossa conta/API. É fato. |
| `[CONSENSO n]` | n vídeos **distintos** do corpus sustentam. n≥4 é forte. |
| `[FRACO]` | 1 fonte só. Hipótese útil, trate como aposta. |
| `[ABERTO]` | Ninguém responde. Não invente. |
| `[REJEITADO]` | Aparece no corpus mas **não vamos fazer** — motivo junto. |

Hierarquia: `[OFICIAL]` > `[PAPER]` > `[TESTADO]` > `[CONSENSO n]` > `[FRACO]`.
Um estudo controlado vale mais que oito gurus repetindo um ao outro — e a
doc do TikTok vale mais que o estudo, quando a pergunta é sobre a regra da
plataforma. Ver §15 e §16.

**Aviso de viés do corpus (importante):** dos 178 vídeos, ~60 são sobre
TikTok Shop/afiliados (outro modelo de negócio) e boa parte do resto existe
para vender curso. Números de faturamento pessoal ("fiz R$ 15.000 em 7
dias") são propaganda, não dado — foram descartados. O que sobreviveu é
mecânica de plataforma, que é o que interessa.

---

## 1. O mecanismo central (entenda isto antes de qualquer regra)

O TikTok **não paga por visualização**. Paga por **visualização
qualificada**, e o preço dela é variável.

**✅ VERIFICADO NA FONTE OFICIAL em 27/07/2026** (Termos do Creator Rewards
Program + Creator Academy). O corpus de gurus acertou uma parte e errou
outra — a versão correta é esta:

1. **O vídeo precisa ter no mínimo 1 minuto.** `[OFICIAL]`
   Termos legais, ao pé da letra: *"Eligible Videos"* devem ter *"a duration
   of at least 1 minute publicly posted on the Platform"*.
   → Confirma `[CONSENSO 8]`. Nosso `DUR_MIN = 65` está certo.
2. **Uma "qualified view" NÃO exige 50% de retenção.** `[OFICIAL]`
   É a visualização de **5 segundos ou mais**, não marcada como "não tenho
   interesse", excluindo fraude, view paga/promovida/artificial.
   → ❌ **O `[FRACO]` de "~50% de retenção" estava ERRADO.** A barra por
   visualização é MUITO mais baixa do que supúnhamos.
3. O vídeo precisa alcançar **~1.000 visualizações no For You** para começar
   a gerar receita, e **não pode ser Duet nem Stitch**. `[OFICIAL]`
   (vem da central de ajuda/Academy, não dos termos legais — confiança um
   degrau abaixo dos itens 1 e 2)

**Por que essa correção importa muito:** a gente vinha achando que era
preciso segurar metade do vídeo para a view contar. Não é. Isso *afrouxa* a
pressão por clipe curto — e desarma o principal argumento contra a faixa de
65-110s (ver §16.1). Retenção continua importando, mas por outro caminho:
ela alimenta a **distribuição** do algoritmo, não a contagem do pagamento.

E o RPM (US$ por 1.000 visualizações qualificadas) **não é fixo** — escala
com retenção e com um bônus de "conteúdo original e bem editado":

| Situação | RPM Brasil (US$/1k) | Fonte |
|---|---|---|
| Corte de podcast, fundo trocado, edição fraca | **< 0,01** | `[FRACO]` |
| Piso padrão | 0,05 – 0,25 | `[CONSENSO 2]` |
| Operação normal | 0,20 – 0,40 | `[CONSENSO 3]` |
| Bem editado, boa retenção | 0,30 – 0,70 | `[CONSENSO 2]` |
| Retenção alta + público mais velho | ~1,00 | `[FRACO]` |
| Europa (DE/UK/FR) | 0,60 – 0,80 | `[FRACO]` |
| EUA | o mais alto citado | `[FRACO]` |

### As três consequências que governam tudo

**(a) Vídeo abaixo de 60s rende exatamente zero.** Não importa se viraliza.
O corpus cita um vídeo de 9 segundos com **20 milhões de views e
monetização zero**. ✅ **Corrigido em 27/07/2026**: `config.DUR_MIN` foi de
20 para **65** e `DUR_MAX` de 120 para **110**. O lote da Bermuda, feito
antes disso, tinha 6 clipes de notas 83-95 **todos entre 42 e 56s** —
nenhum podia monetizar.

**(b) A diferença entre corte premiado e corte punido é intensidade de
edição, não o fato de ser corte.** O mesmo corpus diz que corte com legenda
animada, zoom no rosto, transições, corte de silêncio e emoji *"o TikTok
aprova e paga bem"*, e que corte de podcast com fundo removido e legenda
simples cai para menos de 1 centavo. Isto é a nossa alavanca principal.

**(c) O algoritmo pontua ações com pesos muito diferentes** — `[FRACO]`,
uma fonte, mas explica o comportamento observado em toda a plataforma:

| Ação | Peso |
|---|---|
| Visualização completa | **4** |
| Compartilhamento | **3** |
| Comentário | 2 (implícito) |
| Curtida | **1** |

Otimize para **terminar o vídeo** e para **compartilhar**. Curtida é ruído.

---

## 2. As cinco regras inegociáveis

Se tudo o mais for esquecido, ficam estas.

1. **Todo clipe publicado tem mais de 60 segundos.** Alvo 70–95s.
   `[OFICIAL]` — confirmado nos termos do Creator Rewards Program.
2. **Todo clipe é cortado do vídeo LONGO original**, nunca do corte já
   editado de outro perfil — o algoritmo detecta e limita reaproveitamento
   de cortador. `[CONSENSO 2]` + já é a nossa prática.
3. **Todo clipe leva no mínimo 3 camadas de edição própria** (ver §5). Corte
   cru com legenda não sustenta RPM. `[CONSENSO 3]`
4. **Nunca rajada.** Máximo 3 posts/dia, espaçados. Foi rajada + mono-tema
   que matou o canal anterior. `[TESTADO]` (o ban) + `[CONSENSO 2]`
5. **Só cortar fonte com permissão confirmada.** Preferir criadores que
   liberam cortes explicitamente. `[CONSENSO 1]` + política nossa.

---

## 3. Em que fase o canal está — e o que muda

O corpus contém um conflito aparente sobre duração que na verdade é
estratégia de fase:

- Vídeo curto (15–30s) → maior taxa de conclusão, cresce seguidor mais
  rápido. `[CONSENSO 2]`
- Vídeo >60s → única forma de receita. `[CONSENSO 8]`

| | Fase 1 — Qualificar | Fase 2 — Faturar |
|---|---|---|
| **Onde estamos** | ← aqui (conta nova, ~0 seg.) | |
| **Meta** | 10.000 seguidores + 100.000 views/30d | RPM e volume |
| **Duração** | 65–95s (ver decisão abaixo) | 70–110s |
| **Prioridade** | gancho e compartilhamento | retenção e originalidade |
| **Volume** | 2–3/dia | 3/dia |

**Requisito de monetização** (Creator Rewards) — `[CONSENSO 8]`:
**10.000 seguidores + 100.000 visualizações somadas nos últimos 30 dias**,
18+, conta **Pessoal ou de Criador** (não Empresarial).
Pagamento cai no **dia 15 do mês seguinte**, via chave **Pix** `[FRACO]`.

Atalhos que existem e são mais perto: **TikTok Shop** a partir de
1.000–2.000 seguidores `[CONSENSO 4]` e **Lives** a partir de 1.000
`[FRACO]`. Não são o nosso modelo hoje, mas registrar que a primeira
receita possível não é a de 10k.

> **Decisão recomendada sobre duração na Fase 1:** ficar em **>60s mesmo
> antes de monetizar**. Motivo: o corpus diz que **um único vídeo de
> 100–200k views costuma entregar os 10.000 seguidores E as 100.000
> visualizações de uma vez** `[FRACO]`. Um vídeo >60s que estoure cumpre a
> meta *e* já nasce elegível; um de 30s que estoure cumpre metade e não
> paga nada. O ganho de conclusão do vídeo curto não compensa perder a
> receita inteira. **Isto é uma decisão sua** — se preferir priorizar
> velocidade de seguidor, a alternativa é 25–35s até 10k e virar a chave
> depois.

---

## 4. Regras de produto — o clipe

### 4.1 Duração
- **Mínimo 65s** (margem de segurança sobre os 60s). `[CONSENSO 8]`
- **Alvo 70–95s.** Acima de ~110s a retenção de 50% fica difícil.
- Se o trecho bom tem 45s, **não publique solto** — ou estenda o recorte
  para pegar mais contexto, ou emende com um segundo trecho do mesmo vídeo.
  Emendar clipes curtos para ultrapassar 1 min é prática explícita do
  corpus. `[CONSENSO 2]`

### 4.2 Gancho — os 3 primeiros segundos
- **3 segundos é o tempo que o usuário leva para decidir ficar ou pular.**
  `[CONSENSO 3]`
- O gancho decide a entrega; sem ele o resto do vídeo não é assistido.
  `[CONSENSO 4]`
- Ganchos que funcionam no corpus: **curiosidade enigmática**, **fato
  impressionante**, **quebra de expectativa**, **figura de autoridade
  aparecendo já no primeiro frame**. `[CONSENSO 3]`
- **Ambição e medo** são os dois motores emocionais que mais geram
  compartilhamento — e compartilhamento vale 3 pontos. `[FRACO]`
- Abrir em **close-up** dá mais impacto que plano aberto. `[FRACO]`

### 4.3 Estrutura interna
- Mantemos **GPC** (Gancho-Progresso-Clímax), já no prompt do Gemini.
- Novidade do corpus: **troque de estímulo a cada ~3s** nos primeiros 12s
  (gancho 0-3s, contexto 3-6s, clímax 6-9s, resolução 9-12s). `[CONSENSO 2]`
- **Nenhuma cena/plano deve durar mais de ~8s sem mudança visual.**
  `[CONSENSO 2]`
- Termine **logo após o pico**, sem despedida — já implementado.

### 4.4 Retenção
- Alvo prático: **≥50% do vídeo assistido** (é o limiar da visualização
  qualificada). `[FRACO]`
- **Cortar silêncios e respirações** ("decupagem") é citado repetidamente
  como o ajuste de maior impacto em ritmo. `[CONSENSO 3]` — **não temos
  isso no motor hoje.** É a melhoria de retenção mais barata disponível.
- **Legenda é obrigatória**: ~40% assiste sem som. `[CONSENSO 4]`

---

## 5. Regras de edição — o que separa corte premiado de corte punido

Esta seção é a alavanca de RPM. **Mínimo 3 destas camadas por clipe.**

| # | Camada | Temos? | Nota |
|---|---|---|---|
| 1 | Legenda karaokê palavra-a-palavra | ✅ Inter Black | máx. ~3 palavras por vez `[CONSENSO 2]` |
| 2 | Corte de silêncios/respiros | ✅ `CORTAR_SILENCIOS` | maior ganho de ritmo `[CONSENSO 3]` — medido no run #9 (28/07): −6,4s em 83,8s, 22 pedaços |
| 3 | Zoom/punch-in dinâmico | ✅ **desde 28/07**: cíclico 1.00→1.10 a cada 6,5s | variar enquadramento a cada 5-8s `[CONSENSO 2]` — antes era 1.00→1.06 monotônico, sutil demais |
| 3b | Reenquadramento seguindo o rosto | ✅ **ressuscitado em 28/07** | estava morto desde a atualização do MediaPipe (`mp.solutions` removido na v1.0): todo clipe saía com crop fixo no centro e só um aviso discreto no log |
| 4 | Transição com efeito sonoro | ❌ | citado como sinal de originalidade `[CONSENSO 2]` |
| 5 | Elemento gráfico sincronizado com a fala | ❌ | ex.: ícone aparece na palavra dita `[FRACO]` |
| 6 | Frase-título fixa no topo | ❌ | e ela deve ser **igual ao título do post** `[FRACO]` |
| 7 | ~~Música de fundo~~ **áudio em tendência** | ❌ | ⚠️ rebaixado em §16.5: experimento pré-registrado não achou efeito de música. Usar só quando casar com o tema; preferir som em alta, que também aciona distribuição |

**Posicionamento de legenda:** manter longe das bordas — a UI do TikTok
(perfil, curtir, comentar, nome) cobre a **direita e a base**. O corpus
recomenda legenda **ligeiramente acima do centro**. `[CONSENSO 2]`
Hoje usamos `LEGENDA_MARGEM_V_FRAC = 0.18` (18% a partir da base), que é
justamente a zona coberta. **Candidato a subir para ~0.30 como padrão.**

**Export:** 1080p, 9:16, e o corpus cita 60fps `[FRACO]`. Nós já usamos o
fps nativo da fonte, o que é mais seguro — manter.

**Áudio em alta:** vincular som/música em tendência na hora de postar
aumenta distribuição. `[CONSENSO 3]` Só dá para fazer **no app**, na
publicação manual — é um passo do checklist, não do motor.

---

## 6. Originalidade — o risco existencial

Aqui o corpus é duro e vale ler com atenção, porque fala diretamente do
nosso formato.

### O que ele afirma
- **"Canais focados puramente em cortes de podcasts de terceiros sofrem
  desmonetização sistemática por falta de originalidade."** `[CONSENSO 3]`
- Republicar vídeo de terceiro **sem alteração** → restrição de alcance ou
  banimento. `[CONSENSO 4]`
- **Corte gerado do vídeo bruto ≠ corte pego de outro cortador.** O
  primeiro é aceito; o segundo é detectado. `[CONSENSO 2]` — **nós fazemos
  o certo**, e isso precisa continuar.
- Usar **trechos curtos e intercalados** em vez de reproduzir bloco longo
  contínuo reduz sinalização. `[FRACO]`
- Preferir fontes que **autorizam cortes explicitamente**. `[FRACO]`

### O que NÃO vamos fazer — `[REJEITADO]`
O corpus está cheio de táticas para *burlar* a detecção de conteúdo
reciclado: espelhar o vídeo, aplicar filtro "Berlim", efeito de ruído
retrô, **remover metadados**, renomear arquivo, **VPN para garimpar vídeo
russo/chinês não indexado**, proxy residencial e navegador antidetect.

Não vamos usar nada disso, por dois motivos — e o primeiro é do próprio
corpus:

1. **Ele diz que não funciona.** Regra marcada risco alto: *"A alteração
   superficial de vídeos alheios não evita as punições do algoritmo por
   conteúdo não original e coloca em risco o status de monetização."*
   Investir em disfarce é gastar esforço no lugar errado.
2. Proxy/antidetect para simular região viola os termos, e **já perdemos um
   canal**. Não é o risco certo a correr.

O caminho que resta é o único que o corpus também endossa: **editar de
verdade**. É a §5.

### Ferramenta oficial que devemos usar
**Guardião Criativo** — IA do próprio TikTok que pré-verifica diretrizes e
originalidade antes de publicar, **2 checagens grátis por dia** `[FRACO]`.
Se existir mesmo, é o oráculo definitivo: para de ser adivinhação.
**Ação: validar no app e, existindo, virar passo obrigatório do checklist
para todo clipe novo de fonte nova.**

---

## 7. Publicação

### 7.1 Volume
- **2–3 posts/dia** é o consenso operacional. `[CONSENSO 6]`
- 3–5/dia aparece como "aceleração" `[CONSENSO 3]`; até 10/dia aparece
  `[FRACO]` — **ignorar**, é exatamente o padrão que nos derrubou.
- **Postar todos os dias**, sem buracos, importa mais que o número.
  `[CONSENSO 5]`
- **Não despejar volume em conta nova** — é lido como automação.
  `[CONSENSO 2]`
- ~~Variar o tema entre os posts do dia~~ — **REVOGADO em 27/07/2026, ver
  §17.4.** Consensus mostrou que isso compete com o loop de reinjeção
  algorítmica. Nova regra: núcleo semântico único e estreito na Fase 1
  (ex.: documentário/entrevista de não-ficção), variando **formato e
  ângulo** dentro dele — não o tema em si.

### 7.2 Horário
Várias fontes independentes, convergindo:

| Faixa | Força |
|---|---|
| **20h–21h** ("horário nobre digital") | mais citada; se for postar 1x/dia, é aqui `[CONSENSO 4]` |
| 8h (primeiro scroll do dia) | `[CONSENSO 3]` |
| 11h–12h | `[CONSENSO 3]` |
| 15h | `[CONSENSO 2]` |
| 18h | `[CONSENSO 2]` |

- **Postar alguns minutos ANTES do pico**, não em cima — o vídeo precisa
  estar processado quando a audiência chega. `[FRACO]`, mas bate com o que
  o `SABEDORIA_YT.md` já dizia.
- Isso é **ponto de partida**. Depois de ~2 semanas com histórico, trocar
  pelo painel do próprio perfil. `[CONSENSO 2]`

**Nosso plano diário:** 2–3 posts — **~8h, ~15h, ~20h30**, mesmo núcleo
semântico, **ângulo e formato diferentes** entre eles (⚠️ dizia "temas
diferentes"; corrigido em 28/07 pela revogação do §7.1/§17.4).

### 7.3 Legenda e hashtags
- **3 a 5 hashtags**, todas **estritamente relevantes**. `[CONSENSO 3]`
- **Hashtag irrelevante prejudica** — confunde a classificação e reduz
  alcance. Não existe "pegar carona". `[CONSENSO 2]`
- Copiar as hashtags de vídeos virais **do mesmo tema** é tática válida.
  `[CONSENSO 2]`
- Colocar dados concretos na legenda (nome, data, evento) ajuda o algoritmo
  a contextualizar. `[FRACO]`
- **CTA pedindo comentário de uma palavra específica** gera volume de
  interação. `[FRACO]` — usar com parcimônia, beira o engajamento
  artificial que o próprio corpus diz ser punido.

### 7.4 Depois de postar
- **Responder e curtir os comentários**, usando palavras-chave do nicho nas
  respostas — aumenta permanência na página e ajuda a classificar o canal
  na bolha certa. `[CONSENSO 3]` Barato e não fazemos.

---

## 8. Saúde da conta

- **Aquecimento** de conta nova: usar o app como humano — assistir, curtir,
  salvar, pesquisar na lupa — **10–30 min/dia por 1–7 dias** antes de
  postar sério. `[CONSENSO 4]`
- **Sinal de conta saudável:** publicação passando de **200 visualizações**.
  `[CONSENSO 2]`
- **Sinal de conta marcada como bot:** views travadas sistematicamente na
  faixa **50–200**. `[CONSENSO 2]`
- **Não repetir sequências mecânicas de interação** (sempre curtir→comentar
  na mesma ordem) — aciona o antifraude. `[FRACO]`
- **Interagir só com conteúdo do nosso nicho e idioma** — o algoritmo usa o
  que você consome para decidir para quem entregar o que você publica.
  `[CONSENSO 2]` Consequência prática: **não usar a conta do canal para
  lazer.**
- Conta em **Pessoal ou Criador**, nunca Empresarial (bloqueia Rewards).
  `[CONSENSO 2]`
- Ativar **verificação em duas etapas**. `[FRACO]`

### O que já sabemos por medição — `[TESTADO]`
Mantido de `SABEDORIA_TIKTOK.md`, continua valendo:
- Limite de **~5 rascunhos pendentes** via API → `spam_risk_too_many_pending_share`.
- **REGRA DE OURO: nunca excluir rascunho vindo da API.** Excluir não
  devolve a vaga; só postar devolve. Vaga excluída fica presa.
- Direct Post exige auditoria (`unaudited_client_can_only_post_to_private_accounts`).
- Por isso a publicação real hoje é **manual pelo LDPlayer**, que não tem
  nenhum desses limites.

---

## 9. Métricas — o que olhar

| Métrica | Alvo | Força |
|---|---|---|
| Retenção média | **≥50%** (limiar da view qualificada) | `[FRACO]` |
| Views por post em conta saudável | >200 nos primeiros posts | `[CONSENSO 2]` |
| Vídeo que resolve a Fase 1 | um único de **100k–200k** views | `[FRACO]` |
| RPM esperado Brasil | 0,20–0,40 US$/1k para projeção | `[CONSENSO 3]` |
| Prazo para julgar a estratégia | **30 dias** sem mudar o método | `[CONSENSO 2]` |

**Não otimizar por curtida.** Vale 1 ponto contra 4 da visualização
completa e 3 do compartilhamento.

**Diagnóstico rápido quando um vídeo morre:**
1. Travou em 50–200 views → suspeita de conta marcada, não de conteúdo.
2. Views normais mas retenção <30% → gancho falhou (3 primeiros segundos).
3. Retenção boa mas zero compartilhamento → falta carga emocional
   (ambição/medo/quebra de expectativa).
4. Tudo bom mas RPM no chão → sinal de "não original": faltou edição (§5).

---

## 10. Erros fatais — lista de proibições

Todos `[CONSENSO ≥1]` com risco alto ou médio no corpus:

1. Publicar vídeo de terceiro sem alteração real.
2. Tentar burlar detecção com edição superficial (espelho, filtro,
   metadados). Não funciona e queima a conta.
3. Rajada de posts, principalmente em conta nova.
4. Hashtag irrelevante para "pegar carona".
5. Logo/marca registrada de terceiro (Rockstar, Take-Two, etc.).
6. Rosto de celebridade em peça promocional sem autorização.
7. Sangue, cadáver, violência explícita, imagem chocante.
8. Conteúdo apelativo/sensacionalista para forçar engajamento (o corpus
   cita desqualificação imediata do programa).
9. Figuras políticas como atalho de crescimento — engaja rápido, restringe
   a conta depois. **Relevante para nós:** "política" apareceu como nicho
   quente no radar; fica **vetado**.
10. Narração 100% IA sem edição complementar → classificado como spam.
11. Dado inventado por IA em vídeo de ciência/tecnologia. **Conferir número
    antes de publicar** — é exatamente o nosso nicho e é como se perde
    credibilidade e, no limite, a conta por desinformação.
12. Repetir a mesma estrutura em todo vídeo → risco de desmonetização por
    falta de diversidade.

---

## 11. O que isto exige do motor (ações concretas)

Ordenado por retorno sobre esforço.

| # | Mudança | Onde | Impacto |
|---|---|---|---|
| 1 | `DUR_MIN` 20 → **65** | `config.py:25` | **Destrava receita.** Hoje produzimos clipes que não podem pagar. |
| 2 | `DUR_MAX` 120 → **110**, alvo 70–95s no prompt | `config.py:32`, `engine/selecao.py` | retenção de 50% mais viável |
| 3 | **Corte de silêncios** (decupagem automática) | `engine/midia.py` novo | maior ganho de ritmo/retenção disponível |
| 4 | Legenda: `LEGENDA_MARGEM_V_FRAC` 0.18 → **0.30** padrão | `engine/legendas.py` | sai de baixo da UI do TikTok |
| 5 | Punch-in periódico (zoom a cada 5–8s) além do Ken Burns | `engine/enquadrar.py` | camada de originalidade + dinamismo |
| 6 | Limitar hashtags a **5** e checar relevância | `main.py`, `publicar_tiktok.py` | evita punição por hashtag solta |
| 7 | Frase-título fixa no topo, igual ao título do post | `engine/legendas.py` | camada de edição + coerência |
| 8 | Rejeitar candidato <65s na seleção | `engine/selecao.py` | impede clipe inelegível de nascer |

**Checklist manual por post** (LDPlayer, não automatizável):
- [ ] Clipe >65s
- [ ] ≥3 camadas de edição
- [ ] Guardião Criativo aprovou (se existir)
- [ ] Som em alta vinculado
- [ ] 3–5 hashtags relevantes
- [ ] Mesmo núcleo semântico, **ângulo/formato diferente** do post anterior
      (⚠️ dizia "tema diferente" — contradizia a revogação do §7.1 e §17.4;
      corrigido em 28/07. Variar o tema compete com o loop de reinjeção)
- [ ] Horário ~8h / ~15h / ~20h30
- [ ] Voltar em 1h para responder comentários

---

## 12. Plano dos próximos 30 dias

**Semana 1 — arrumar o motor.** Itens 1, 2, 4 e 8 da §11 (config + legenda,
tudo barato). Rodar um lote e comparar retenção com os posts atuais.

**Semana 2 — edição de verdade.** Item 3 (corte de silêncios) e 5
(punch-in). Estes dois são o que move o RPM.

**Semanas 3–4 — regime.** 2–3 posts/dia (§7.1), **núcleo semântico único
variando ângulo e formato** — não temas variados (⚠️ dizia "temas variados";
contradizia a revogação do §7.1/§17.4, corrigido em 28/07). Horários fixos,
responder comentários. **Não mudar o método por 30 dias** — sem isso não
há como saber o que funcionou. `[CONSENSO 2]`

**Medir ao fim:** retenção média, views/post, seguidores ganhos, e se algum
vídeo passou de 100k. Só então revisar este playbook.

---

## 13. As 7 perguntas do roteiro antigo — respondidas

| # | Pergunta | Resposta |
|---|---|---|
| 1 | Janela de teste inicial do TikTok | **Parcial — ver §22 (28/07).** Mecanismo resolvido: entrega inicial ~100 usuários, alocada por embedding do conteúdo (não por seguidores), com watch time como sinal dominante. **Números do TikTok seguem `[ABERTO]` e o relatório declara isso como GAP** — os limiares que existem (4.000 views em 2 dias) são do Kuaishou. |
| 2 | Volume seguro por dia | **2–3/dia**, subindo devagar. `[CONSENSO 6]` Resolve a pendência do 3-5/dia. |
| 3 | Horário de pico real (Brasil) | **20h–21h principal**; 8h, 11h, 15h, 18h secundários. `[CONSENSO 4]` Substitui o chute que estava no `PADRAO.md`. |
| 4 | Métricas do painel e alvos | **Parcial.** Temos alvos (§9) mas **não** os nomes exatos das métricas no painel do TikTok. `[ABERTO]` |
| 5 | Duração ideal | **>60s obrigatório, alvo 70–95s.** `[CONSENSO 8]` A mais importante do documento. |
| 6 | Tolerância a conteúdo de terceiros | **Respondida e é séria** (§6): corte do bruto é aceito, corte de cortador não, e corte sem edição real é desmonetizado. |
| 7 | Hashtags | **3–5, estritamente relevantes.** `[CONSENSO 3]` Quantidade resolvida; **acento continua `[ABERTO]`**. |

### Ainda em aberto (não inventar)
- Janela de teste inicial: tamanho e duração.
- Nomes/limiares das métricas no painel do TikTok.
- Hashtag com acento atrapalha? (`#robótica` vs `#robotica`)
- O Guardião Criativo existe mesmo e está disponível na nossa conta?
- Prazo de expiração de rascunho pendente na API.

---

## 14. Procedência

- **Corpus:** 178 vídeos, 1.031 passagens
  (`sabedoria-tiktok/destilacao/tiktok_bruto.json`).
- **Método:** extração de 704 regras acionáveis via Gemini com julgamento de
  aplicabilidade ao nosso caso (`extrair_regras.py` → `regras.jsonl`),
  depois agrupamento local por consenso (`agrupar.py`), depois curadoria
  manual — filtrando venda de curso, TikTok Shop e tática de evasão.
- **Consulta direcionada:** `python buscar.py "<regex>"` imprime as
  passagens originais que sustentam qualquer afirmação daqui. Use quando
  uma regra parecer estranha — **a fonte vence este documento**.
- **Não incluído:** ~60 vídeos de TikTok Shop/afiliado e todo o material de
  proxy/antidetect/conta gringa.

> Ao editar: mantenha a marca de confiança. Se um `[FRACO]` for confirmado
> na prática, promova para `[TESTADO]` e diga como foi medido.

---

## 15. Base científica `[PAPER]` — relatório Consensus, 27/07/2026

50 artigos analisados. **Ressalva de validade externa que vale para tudo
abaixo:** quase toda a evidência vem de *anúncios, TED talks, vídeo
educacional e notícia* — **não de feed de vídeo curto**. O próprio
relatório fecha dizendo que a maior questão em aberto é justamente se
esses efeitos valem em ambiente de feed. Trate como direção forte, não
como lei do TikTok.

### 15.1 Os 3 primeiros segundos: **sim com ressalva**
Medidor: 50% sim · 33% não · 17% misto (N=6). Os momentos iniciais
influenciam muito, mas **não determinam sozinhos** — retenção também
depende de estrutura de cena, dinâmica emocional, narrativa e carga de
compreensão ao longo do vídeo.
- Song et al. 2023: leva **~3s para o espectador captar a informação
  principal de um plano** (2s se a densidade for baixa). É achado
  *perceptual*, não curva de retenção de plataforma.
  **→ Consequência direta: nenhum plano deve durar menos de ~2-3s**, senão
  o espectador não processa. Isso põe um PISO no punch-in.
- Zhang et al. 2026 chama os 3s iniciais de "hooking period" e liga a
  métricas posteriores. Coker et al. 2021: anúncio em forma de HISTÓRIA
  engancha mais que anúncio argumentativo, e enganchar aumenta intenção de
  ver e de compartilhar.

**Mantemos** o peso no gancho, mas sem tratar 3s como interruptor mágico.

### 15.2 Emoção vence utilidade — **evidência forte**
Isto resolve a dúvida que estava aberta sobre o peso de `valor-pratico`.
- Emoção de **alta ativação** aumenta compartilhamento — awe, raiva,
  ansiedade, surpresa; **tristeza (baixa ativação) reduz**
  (Berger & Milkman 2012; Nelson-Field 2013; Yu 2020). *Forte.*
- Apelo emocional **bate** apelo informativo em vídeo (Akpinar & Berger
  2017; Tellis 2019). *Forte.*
- Utilidade prevê algum compartilhamento, mas **menos consistente** que
  emoção. *Moderado.*

**→ `valor-pratico` NÃO deve pesar mais que os marcadores emocionais na
seleção.** Fica como contribuinte, não como driver.

- **Surpresa concentra atenção mais que alegria** (Teixeira et al. 2012), e
  viaja mais longe (Yu 2020, Tellis 2019).
  **→ `emocao_dominante: surpresa` merece peso extra.** (Nosso melhor
  clipe da Bermuda, nota 95, era exatamente surpresa + tabu-quebrado.)

- **Dimensão que nos falta:** compartilhar é ato de **identidade**. Scholz
  et al. 2017 liga o ato a um sinal de valor que integra cognição sobre si
  e sobre o social — não só ativação do conteúdo. Brady et al. 2019: teor
  moral/emocional captura atenção.
  **→ Candidato a nova dimensão na taxonomia: "valor social" — o quanto
  compartilhar isso diz algo bom sobre quem compartilha.**

- **Ressalvas honestas:** Prowten et al. 2024 **falhou em replicar** que
  ativação fisiológica isolada aumente disposição a compartilhar. E as
  emoções discretas mudam por plataforma (no WeChat, ansiedade/amor/
  surpresa ampliam, mas raiva/tristeza/alegria **freiam**).

### 15.3 CONFLITO: clickbait — a literatura contraria nosso padrão
Mukherjee et al. 2022: informação omitida previa compartilhamento num
modelo simples, mas **perdeu significância** ao controlar emoção e
utilidade. Pior: clickbait aciona **percepção de intenção manipulativa e
depreciação da fonte**, e manchetes clickbait foram **compartilhadas menos**
em média.

**O `PADRAO.md` manda "título chamativo/clickbait controlado".** Isso é
preferência sua, registrada, então não mudei nada — mas a literatura diz
que o clickbait cobra em confiança e reduz share. Recomendo migrar de
*curiosidade por omissão* ("o que aconteceu vai te chocar") para
*curiosidade por especificidade* ("a lei que obriga executivos a usar
bermuda") — que foi, aliás, o que a Bermuda já fez naturalmente.

### 15.4 Cortes e ritmo — valida o punch-in de 5-8s
- Cenas curtas e visualmente simples geram mais sincronia atencional;
  **cortes aumentam atenção**; complexidade visual tem efeito negativo
  atrasado (Wals et al. 2026).
- Cortes reduzem frequência de piscada logo após ocorrerem, sinal de
  atenção (Andreu-Sánchez & Martín-Pascual 2021).
- **Números de referência:** edição clássica ≈ **5,9s por plano**; edição
  caótica ≈ **2,4s**.
  **→ Nosso alvo de punch-in a cada 5-8s está bem calibrado.** Com piso de
  ~3s (§15.1). "Mais rápido é sempre melhor" é **falso**.

### 15.5 Corte de silêncios: seguro, com um teto
Era a pergunta que mais me preocupava, porque acabamos de implementar.
- Aprendizado por vídeo tem **custo mínimo de compreensão até 1,5x-2x**;
  cai acima de 2x (Murphy et al. 2021).
- Análise de TED: fala ágil e frases curtas preveem mais engajamento
  (Kim 2024).
- Acima de ~**200 palavras/min** a compreensão cai para ouvinte de nível
  intermediário-baixo (Weinstein-Shr & Griffiths 1992).

**→ O que fazemos é seguro**: removemos ar morto, não aceleramos a fala —
a velocidade de locução em si não muda. Mas ganhamos um **guardrail
mensurável**: temos timestamps por palavra do Groq, então dá pra calcular
o wpm efetivo depois do corte e **avisar se passar de 200**.

### 15.6 Automação: multimodal vence só-texto
- Framework LLM **multimodal** extraiu features do "hooking period" de
  vídeo+áudio+texto e correlacionou com performance real de anúncio
  (Zhang et al. 2026).
- Modelo multimodal de retenção: **-30% de MAE** contra baseline de
  regressão direta, e identificou clusters latentes de ganchos virais
  (Husiev & Vergunova 2026).

**→ Valida a arquitetura que montamos:** triagem barata por transcrição
como pré-filtro (`triar_cortabilidade.py`), e análise **multimodal** cara
(vídeo no Gemini) só no que passou. Não trocar a seleção por texto puro.

### 15.8 → continua na §16 (2ª rodada, evidência de FEED)

### 15.7 O que a literatura NÃO respondeu (continua `[ABERTO]`)
O relatório diz explicitamente que os 50 artigos não trazem resultado
direto sobre: **legenda sem som**, **música de fundo**, narrativa vs
expositiva, suspense e duração de visualização, **features de viralidade
específicas do TikTok**, **horário de postagem**, predição de engajamento
só por transcrição, e **detecção automática de highlights**.

Ou seja: horário de postagem segue sem base — nem no corpus de gurus (2
fontes) nem na literatura. Continua chute calibrado.

---

---

## 16. Segunda rodada Consensus `[PAPER]` — evidência de FEED, 27/07/2026

Esta rodada é mais forte que a §15: N=23 artigos, boa parte **em feed de
vídeo curto de verdade** (TikTok/Reels/Shorts), não em anúncio ou sala de
aula. Onde ela divergir da §15, **ela vence**.

### 16.1 ⚠️ A regra dos 65-110s virou HIPÓTESE, não fato assentado
O relatório é explícito: *"para a regra atual de 65-110s, este corpus não
valida essa faixa como ótima (...) a leitura financeiramente mais segura é
tratar 65-110s como hipótese que agora precisa de teste A/B interno contra
faixas materialmente mais curtas."*

- Vídeo mais curto em geral **melhora conclusão/retenção** (moderado-alto).
- Mas "mais curto é sempre melhor" é cru demais em feed: vídeo mais longo
  às vezes gera **mais comentário e compartilhamento** (Zhang et al. 2022).
- Objetivo baseado em % assistida **enviesa a recomendação para extremos de
  duração**; formulações cientes de duração alinham melhor (Saket 2023).

**Como isso convive com o `DUR_MIN=65`?** Não é contradição — são duas
coisas diferentes:
- ">60s ou receita zero" é **regra de elegibilidade de pagamento**, binária.
- "mais curto retém melhor" é **efeito contínuo de retenção**.
Se a primeira for verdadeira, 65-95s é forçado e a gente otimiza retenção
*dentro* dessa restrição.

**✅ AÇÃO CRÍTICA — FEITA em 27/07/2026. A tensão se dissolveu.**
Fui à documentação oficial (ver §1). Resultado:
- **1 minuto mínimo: CONFIRMADO** nos termos legais. `DUR_MIN = 65` fica.
- **"50% de retenção para a view contar": FALSO.** A definição oficial de
  qualified view é **5 segundos**. Era uma invenção do corpus de gurus.

**O que isso faz com o conflito:** o argumento científico "mais curto retém
melhor" atacava uma restrição que eu supunha existir (segurar metade do
vídeo). Ela não existe. Como a elegibilidade de pagamento é binária em 1
minuto, ficar abaixo disso é receita zero — **65-110s continua sendo a
faixa certa**, e não precisa de A/B contra faixas mais curtas *para fins de
receita*.

**O que continua valendo da crítica:** retenção e conclusão ainda governam
a **distribuição** (o algoritmo premia watch time), e nisso vídeo mais
curto leva vantagem. Ou seja, o A/B que faz sentido não é "65s vs 30s" —
é **dentro da faixa elegível**: 65-75s vs 90-110s. Esse sim vale rodar
quando houver volume de dados.

### 16.2 Benchmarks REAIS de feed (Zannettou et al. 2023) — use estes
Substituem os alvos chutados da §9:

| Métrica no TikTok | Valor real |
|---|---|
| Mediana assistida de um vídeo visto | **82%** |
| Views que chegam ao fim | **45%** |
| Views abandonadas antes de 20% da duração | **24%** |
| Faixa típica de conclusão por usuário | 20-60% |

**Leitura:** 1 em cada 4 espectadores sai antes dos primeiros 20% — é aí
que o gancho se paga. E como só 45% completam, **conclusão não pode ser
lida isolada**; comentário e compartilhamento contam.

### 16.3 Features de feed que realmente preveem engajamento — `Forte`
Dados de campo do TikTok (Xiao et al. 2023, 2024):
- **número de planos** (efeito **não-linear** — existe ponto ótimo, não é
  "mais cortes = melhor"; casa com o piso de ~3s da §15.1)
- **complexidade visual** por pixel (também não-linear)
- **formato vertical** — efeito positivo em **comentários e compartilhamentos**
- **velocidade de fala**
- **brilho do áudio**
- entretenimento, storytelling, força do laço social
Mais: **áudio em tendência**, elementos interativos e adaptação nativa à
plataforma (Fatimah & Nasir 2025). Traços recorrentes do que funciona:
compressão narrativa, densidade multimodal, autenticidade performada,
**endereçamento direto** e edição rápida.

### 16.4 Legenda queimada: mantém, mas o motivo muda
74% sim — porém a evidência boa é de **compreensão**, não de retenção.
- Szarkowska et al. 2024: assistir legendado **sem som** aumentou carga
  cognitiva e **reduziu** compreensão, imersão e prazer *versus* com som.
- Pascale et al. 2025: legenda mudou o padrão de atenção visual mas **não**
  melhorou recall imediato.
- **Legenda profissional supera legenda automática** na compreensão da
  narrativa (Kim et al. 2023).

**→ Mantemos legenda queimada** como camada de acessibilidade/compreensão,
mas **sem contar com ganho de retenção**. E ganha peso a qualidade: a nossa
vem de transcrição automática (Groq) + tradução — revisar erro de legenda
passa a ser item de qualidade, não capricho.

### 16.5 Música de fundo: rebaixada de "camada padrão" para "condicional"
Corrige a §5, item 7.
- Experimento **pré-registrado**: música de fundo **sem efeito consistente**
  em persuasão, engajamento ou recall (Djavaherpour et al. 2026).
- Música **desalinhada distrai**; bem alinhada melhora prazer/foco.
- No TikTok, gênero musical **interage** com tema e sentimento — não é
  ganho uniforme (Zhang et al. 2022).
- Compartilhamento sobe quando a música é **ativante, congruente e em
  tendência** (Nelson & Yu 2026).

**→ Não usar música por padrão.** Usar quando casar com o tema, e preferir
áudio em tendência — que também aciona a distribuição `[CONSENSO 3]`.

### 16.6 Identidade confirmada — nova dimensão na taxonomia
74% sim. Compartilhar reflete **consequências esperadas para si e para a
imagem social**, integradas num sinal de valor. Isso explica por que a
pessoa *transmite* em vez de só reagir. Complementa (não substitui) a
teoria de ativação emocional.

**→ Adicionar `valor_social` à taxonomia do `post.json`**: o quanto
compartilhar isto diz algo bom sobre quem compartilha.

### 16.7 Triagem por transcrição: teto confirmado — é PRÉ-FILTRO, não preditor
Isto calibra o `triar_cortabilidade.py` que acabamos de construir.
- Li et al. 2024: acrescentar transcrição **não melhorou** a previsão de
  engajamento — só 30% dos vídeos tinham transcrição útil, e o espectador
  decide rápido, antes de processar muita fala.
- O que ajudou, em ordem: **features visuais intermediárias** (maior salto)
  > título/descrição > classificação de som de fundo > legendas geradas.

**→ A `triar_cortabilidade.py` está no papel certo**: filtro grosseiro de
relevância semântica e de "tem arco autocontido aqui?". **Não** é preditor
de engajamento e não deve virar um. Se quisermos nota de retenção de
verdade, o caminho é multimodal (visual + áudio), não mais texto.

### 16.8 Mudanças que esta rodada força

| # | Mudança | Onde | Status |
|---|---|---|---|
| 1 | Verificar a regra dos 60s na doc **oficial** do TikTok | — | **fazer primeiro** |
| 2 | Tratar 65-110s como hipótese e montar A/B contra faixa mais curta | `config.py` | depende do 1 |
| 3 | Música: de padrão para condicional | §5 item 7 | ✅ feito |
| 4 | Benchmarks reais de feed | §9 | ✅ feito |
| 5 | `valor_social` na taxonomia | `selecao.py`, `main.py`, `desempenho.py` | ✅ feito 27/07 |
| 6 | Nº de planos e complexidade visual são **não-lineares** — punch-in entre 3s (piso perceptual) e 8s | `engine/enquadrar.py` | a fazer |
| 7 | Qualidade de legenda vira item de revisão | processo | a fazer |
| 8 | Peso emoção > utilidade no prompt de seleção | `engine/selecao.py` | ✅ feito 27/07 |

**Sobre o item 5 (`valor_social`):** entrou como 5ª subnota (0-10), com a
definição de "o quanto compartilhar isto diz algo bom sobre quem
compartilha". Já é gravada no `post.json` e já entra no relatório do
`desempenho.py` — então a partir do próximo lote dá pra medir se ela
prevê alguma coisa de verdade, em vez de acreditar.

**Sobre o item 8:** o prompt de seleção agora diz explicitamente que
emoção de alta ativação bate utilidade prática, que `surpresa` é sinal
premium, e que tristeza/baixa ativação reduz compartilhamento. Antes ele
tratava todas as dimensões como equivalentes.

---

## 17. Terceira rodada Consensus `[PAPER]` — cascata algorítmica vs. retenção isolada, 27/07/2026

Pergunta feita para fechar o buraco que §15/§16 deixaram: as duas rodadas
anteriores explicam o que faz **um vídeo isolado** reter/compartilhar. Nunca
perguntamos o que faz o algoritmo **reinjetar** esse vídeo em ondas
sucessivas — que é o mecanismo real por trás de crescimento exponencial de
conta, e não apenas de um post que performa bem sozinho.

**Achado central:** retenção alta em um vídeo é sinal de qualidade local,
necessário mas **não suficiente** para cascata. Cascata exige que três
mecanismos se reforcem ao mesmo tempo — algoritmo, conteúdo e rede — e o
marcador certo não é watch time isolado, é **reinjeção sucessiva +
compartilhamento + remixabilidade + spillover entre plataformas**
(Qiu et al. 2015; Klug et al. 2021; Goel et al. 2015).

### 17.1 Algoritmo — o "teste contínuo" e a reinjeção
- TikTok expõe até conta pequena no For You como **teste contínuo**, não só
  por seguidor. `[PAPER]` (Guinaudeau et al. 2022)
- A amplificação vira loop direto usuário-algoritmo cedo, por volta de
  **~200 vídeos de navegação no nível do usuário** — e isso **reduz
  diversidade de exploração** ao mesmo tempo que amplifica.
  `[PAPER]` (Baumann et al. 2025)
- Rewatch, like, follow e interação consistente com um tema fazem o sistema
  **voltar a servir conteúdo semelhante** — é reinjeção, não recomendação
  única. `[PAPER]` (Molem et al. 2024)
- Seguidor prévio e volume acumulado de conteúdo aumentam o pool inicial e
  amplificam rodadas seguintes — **efeito Matthew**: quem já cresceu, cresce
  mais fácil. `[PAPER]` (Xue 2024; Li et al. 2026)
  **→ Reforça §7.1 e §12**: postar todo dia sem buraco não é só disciplina,
  é o que constrói o volume acumulado que alimenta o efeito Matthew.
- **Hashtag genérica tipo #fyp/#foryou não tem efeito consistente
  isolado.** `[PAPER]` (Klug et al. 2021) → confirma a regra já adotada em
  §7.3 (só hashtag estritamente relevante).

**→ Ação candidata:** desenhar o final do clipe para puxar **rewatch**
(loop natural, última cena que só faz sentido revendo o gancho), não só
para "terminar bem". Rewatch é um dos sinais que mais alimenta o loop de
reinjeção — hoje o motor otimiza só para conclusão.

### 17.2 Conteúdo — o que o algoritmo consegue reaproveitar
- Narrativa comprimida, multimodalidade densa, autenticidade performada,
  edição rápida, texto na tela, som, endereço direto. `[PAPER]` (Malik et
  al. 2025; Mou 2026) — já é nossa prática (§4, §5).
- **O conteúdo que mais cresce em rede não é o "melhor" informacionalmente
  — é o attention-grabbing, controverso ou de alta excitação**, porque
  puxa discussão e compartilhamento em cadeia. `[PAPER]` (Qiu et al. 2015)
  **→ Isto é uma evidência nova e forte a favor do candidato #1 do lote
  atual** ("1 cientista vs 31 negacionistas" — debate/controvérsia
  estruturada, não política partidária, dentro do nicho de ciência).
  Controvérsia científica ≠ o item 9 vetado do §10 (figura política como
  atalho); a distinção é o alvo do conflito, não a presença de conflito.
- Choque, severidade, humor, surpresa, outrage e emoção forte aparecem
  repetidamente como gatilho de alcance ampliado. `[PAPER]` (O'Donnell et
  al. 2023; Omar et al. 2026; Zhang 2025) — reforça §15.2/§16 (peso
  emoção > utilidade), agora com o adicional de que isso ajuda cascata
  especificamente, não só retenção.
- Hashtags e sons funcionam menos como persuasão humana e mais como
  **índice técnico** que reduz mismatch de distribuição — reforça manter
  hashtag/som **relevante ao tema real**, não como isca. `[PAPER]` (Li et
  al. 2026)

### 17.3 Rede — de resposta individual a propagação social
- Cascata é **atenção convertida em caminhos de propagação com múltiplas
  gerações**, não um broadcast único grande. `[PAPER]` (Goel et al. 2015)
- Compartilhamento, remix, duet, repost e **comentário que atrai pares**
  (secondary creation) prolongam o ciclo de popularidade por **meses**.
  `[PAPER]` (Zhang 2025; Shen 2025; Hontar 2026)
  **→ Reforça §7.4** (responder comentário usando palavra-chave do nicho):
  não é só cosmético, é o que gera a segunda geração de exposição.
- **Spillover cross-platform: publicar o mesmo vídeo viral em plataforma
  adicional aproximadamente DOBRA o crescimento subsequente** na
  plataforma líder, efeito mais forte nas primeiras 6 semanas.
  `[PAPER]` (Krijestorac et al. 2020)
  **→ Ação candidata nova, ainda não decidida**: publicar o mesmo clipe
  também em YouTube Shorts/Instagram Reels pode dobrar o alcance do
  TikTok, não só somar audiência à parte. Isto é diferente da decisão de
  26/07 (vertical vs. horizontal no mesmo TikTok) — é sobre
  multi-plataforma. **Perguntar ao usuário antes de implementar.**
- Follower count e posição de status também moldam potencial de cascata,
  independente da qualidade do vídeo — mais um motivo para não desistir de
  conta nova cedo (o pool cresce com o tempo). `[PAPER]` (Ling et al. 2021)

### 17.4 RESOLVIDO em 27/07/2026 — núcleo semântico fixo, depois diversidade adjacente
Era tensão em aberto: "variar tema entre posts" (§7.1) parecia competir com
o loop de reinjeção que se aprofunda num nicho só (§17.1, ~200 vídeos).
Quarta rodada Consensus (50 papéis, confiança **moderada**) resolveu:

- **Subtema estreito acelera a convergência algorítmica.** Sinal
  consistente ensina o classificador mais rápido "quem deve ver isso";
  sinal disperso amplia exploração e atrasa a reinjeção. `[PAPER]`
  (Baumann et al. 2025; Hu 2025)
- **Mas especialização extrema cobra preço depois**: homogeneização,
  fadiga, teto de crescimento. `[PAPER]` (Tang 2025; Qin 2025)
- **O equilíbrio é sequencial, não simultâneo**: começar estreito pra
  treinar o sistema e provar retenção num cluster claro, **depois**
  expandir pra subtemas adjacentes — não dispersão ampla. Formulação mais
  explícita (fora de vídeo curto, mas usada como referência de proporção):
  **90% do conteúdo nos 2 gêneros preferidos, 10% fora, com 20% de itens
  "impopulares" dentro de cada gênero.** `[PAPER]` (Ping et al. 2024)
- **Para criador**: manter um **"núcleo semântico" constante** e variar
  formato/ângulo/narrativa/profundidade — não trocar de tema sem eixo
  central. `[PAPER]` (Hu 2025; Fatimah & Nasir 2025)

**Ressalva honesta do próprio relatório:** confiança moderada, não máxima
— a literatura quase nunca mede "velocidade de reinjeção de creator
account" diretamente; é inferência a partir de auditoria/simulação de
recomendação, não experimento com creators novos.

**→ Ação concreta — muda §7.1:** "variar tema entre os posts do dia" fica
**revogado como regra geral**. Substituir por: manter o canal dentro de um
**núcleo semântico único e estreito na Fase 1** (ex.: "ciência/tecnologia
com revelação/debate" — não pular pra política, humor, esporte). Variar
**formato e ângulo** dentro desse núcleo (documentário vs. debate vs.
biografia — como já são os 3 candidatos do lote atual: ciência-debate,
ciência-biografia, curiosidade-país; todos ficam dentro de
"documentário/entrevista de não-ficção"). Expandir para subtema adjacente só depois de ter prova de retenção
real no cluster atual (`desempenho.py` com volume suficiente) — **não
existe número de posts validado pela literatura para esse limiar**, ver
correção em §18.1. Não usar "~200" como meta operacional; é limiar de
consumo de espectador, não de publicação de criador.

### 17.5 O que isto muda no motor (ações concretas)

| # | Mudança | Onde | Status |
|---|---|---|---|
| 1 | Desenhar final do clipe para puxar rewatch, não só conclusão | `engine/selecao.py` (prompt) | candidato, a testar |
| 2 | Preferir candidato com controvérsia/debate estruturado (não político) sobre candidato "informativo neutro" quando notas empatarem | seleção de fonte, radar | ✅ aplicado no lote atual (candidato #1) |
| 3 | Publicar mesmo clipe também fora do TikTok (Shorts/Reels) | `publicar.py` / processo | **pedir autorização antes** |
| 4 | Medir se comentário nosso puxa resposta em cadeia (2ª geração) | `desempenho.py` | adicionar quando houver volume |
| 5 | Tensão variar-tema vs. aprofundar-nicho | — | `[ABERTO]`, não decidir sem dado |

**Procedência:** pergunta feita a partir do gap identificado em §15.7/§16.7
(literatura cobria vídeo isolado, não mecanismo de rede/cascata). Relatório
Consensus, 23 fontes, 27/07/2026. PDF em
`C:\Users\T3610\Downloads\Quais_mecanismos_estruturais_do_algoritmo_de_dis.pdf`.

---

## 18. Quinta rodada Consensus `[PAPER]` — núcleo semântico: sinais e limiar de expansão, 27/07/2026

Continuação direta da §17.4: perguntamos os 3 "Open Research Questions" que
o próprio relatório anterior tinha deixado (limiar de posts, efeito da
expansão no alcance/retenção por plataforma, sinais que definem núcleo
semântico). 50 fontes, confiança **moderada a forte** dependendo do ponto.

### 18.1 Não existe número mágico de posts — e isso é confirmado, não só desconhecido
Nenhum estudo do corpus valida um limiar tipo "5 posts" ou "12 posts"
antes de expandir tema. `[PAPER]` (Zhou 2025; Saket et al. 2023) —
força da evidência **fraca** especificamente aqui, e o próprio relatório
marca como `GAP`: quase toda a literatura mede aprendizado algorítmico em
**interações/embeddings**, não em **contagem de upload do criador**.

**→ Correção importante ao que escrevi em §17.4**: a estimativa "~30 dias
/ ~200 publicações" que usei por analogia era extrapolação frouxa (~200 é
limiar de **vídeos consumidos pelo usuário-espectador**, Baumann et al.,
não de posts publicados pelo criador). Não existe conversão validada de
um pro outro. **Manter a decisão qualitativa** (núcleo estreito primeiro,
expandir só com prova de retenção), **descartar o número "~200" como
regra** — não temos base para ele.

### 18.2 O núcleo semântico é multimodal, com hierarquia clara — `Forte`
Nenhuma dimensão isolada define o núcleo; quatro canais compõem o sinal,
com peso relativo diferente: `[PAPER]` (Xiao 2025; Zhao et al. 2025;
Wei et al. 2023)

| Canal | O que o sistema lê | Papel |
|---|---|---|
| Texto | título, legenda, hashtag, OCR de texto na tela | pista explícita de tópico |
| Áudio | música, fala, padrão acústico | retenção e estilo |
| **Visual** | frames, objetos, cena, cor, movimento | **modalidade mais forte em cold-start**, em vários modelos |
| Comportamento | watch time, swipe, pausa, like, follow | desambiguação mais forte, downstream |

**→ Achado que muda prioridade**: sinal visual pesa mais que hashtag em
vários modelos de cold-start. Isso reforça o que já fazíamos (§5, camadas
de edição visual) mas por um motivo novo — não é só "engajamento", é
**classificação de tópico pelo próprio algoritmo**.

### 18.3 Hashtag confirmado como fraco e ruidoso — reforça §17.2
"Hashtags importam só como um canal de texto entre vários, não como
alavanca de controle isolada." Auditorias mostram que hashtags populares
no TikTok frequentemente referenciam **rituais de plataforma** (tipo
#fyp), não semântica de conteúdo real — e crenças comuns sobre benefício
de hashtag **não se sustentam** em predição de virality em estudo de
larga escala. `[PAPER]` (Hagar & Diakopoulos 2023; Chen et al. 2024)
**→ Confirma, pela terceira vez** (§17.1, §16.3, agora aqui): não
investir em otimização de hashtag além de "3-5, relevante ao tema real".

### 18.4 "Adjacente" significa sobreposição de embedding, não só audiência
Expansão é mais segura quando o subtema adjacente preserva **pistas
semânticas sobrepostas em texto, visual E áudio ao mesmo tempo** — não
basta público parecido; os modelos aprendem "o que é comum entre
modalidades" preservando preferência específica de cada uma. `[PAPER]`
(Wei et al. 2023; Yi et al. 2022; Chen et al. 2024)

**→ Ação concreta para o lote atual**: os 3 vídeos escolhidos (debate
científico, biografia, curiosidade de país) compartilham texto/tom
(documentário/entrevista sério, tom investigativo) e formato de edição,
mas **não compartilham necessariamente o mesmo visual** (debate em
estúdio vs. arquivo histórico vs. imagens de viagem). Isso é
"adjacente" no sentido qualitativo, mas ainda não temos como validar
sobreposição de embedding de fato — só dá para medir depois, com dado
real de desempenho.

### 18.5 Tensão preservada, não resolvida: precisão vs. diversidade
Reforço inicial forte melhora eficiência de recomendação, mas reforço
estreito repetido **pode reduzir exploração e promover homogeneidade ou
"cocoon"** — embora personalização mais precisa não piore isso
mecanicamente sempre. `[PAPER]` (Baumann et al. 2025; Li et al. 2022;
Qin 2025) Isto é a mesma tensão do §17.4/§17.5, agora com mais matiz:
não é automático que "estreito = cocoon", depende de quão precisa é a
personalização.

### 18.6 O que isto muda no motor e no processo

| # | Mudança | Onde | Status |
|---|---|---|---|
| 1 | Descartar "~200 posts" como número-alvo de expansão; manter critério qualitativo (retenção provada) | `sabedoria/PLAYBOOK_TIKTOK.md` §17.4 | ✅ corrigido aqui |
| 2 | Priorizar qualidade de sinal visual na seleção/edição, não só hashtag | `engine/selecao.py`, §5 | reforça prática já existente |
| 3 | Não investir mais em otimização de hashtag além do mínimo (3-5, relevante) | processo | ✅ confirmado 3ª vez |
| 4 | Ao expandir tema, checar se texto+visual+áudio têm sobreposição, não só afinidade de público | seleção de fonte no radar | `[ABERTO]` — sem métrica automatizada hoje |

**Lacuna que o próprio relatório reconhece**: quase nenhum estudo testa
diretamente **estratégia de sequenciamento de posts do criador** — é
o oposto do padrão de pesquisa em recomendação, que otimiza embedding de
vídeo/usuário, não decisão editorial de conta nova. **Não teremos essa
resposta de literatura; só de dado próprio (`desempenho.py`) quando
houver volume.**

**Procedência:** continuação de §17.4, mesmas 3 perguntas em aberto do
relatório anterior. Consensus, 50 fontes, 27/07/2026. PDF em
`C:\Users\T3610\Downloads\Em_contas_novas_de_plataformas_de_vdeo_curto_Ti.pdf`.

---

## 19. Sexta rodada Consensus `[PAPER]` — mesmas 3 perguntas, corrida em paralelo, 27/07/2026

Segunda resposta independente às mesmas 3 perguntas do §18 (rodada
paralela, corpus parcialmente diferente). Confirma tudo o que §18 já
tinha (sem limiar numérico validado; núcleo multimodal com peso visual
forte; hashtag insuficiente sozinho) e acrescenta 3 pontos novos.

### 19.1 Hierarquia de sinais de feedback — novo
No TikTok, **seguir o criador** foi o fator mais influente entre os
testados para diferenciar o feed, depois **tempo assistido**, e só depois
**curtida**. `[PAPER]` (Boeker & Urman 2022) E **skip é sinal negativo
particularmente informativo** para separar subinteresses — mais do que
a ausência de like. `[PAPER]` (Pan et al. 2023)
**→ Muda leitura da nossa priorização**: se converter em "seguidor" pesa
mais que like para o algoritmo entender o núcleo da conta, o CTA de
seguir (não só curtir/comentar) merece destaque no clipe/legenda — hoje
não priorizamos isso explicitamente.

### 19.2 ⚠️ Confirmação séria: a plataforma pode não otimizar para conclusão
Em dado observacional de **9,2 milhões de recomendações reais do TikTok**:
tempo gasto e likes subiram ao longo do tempo, mas **atenção não
aumentou**, e a maioria assistiu só **30%-50%** dos vídeos até o fim.
Interpretação dos autores: o TikTok otimiza mais para **tempo de sessão e
like** do que para watch-to-end. `[PAPER]` (Zannettou et al. 2023)

**→ Isto tensiona diretamente o §9 e o §16.2**, que usavam "retenção
≥50%"/"82% mediana assistida" (mesmo autor, Zannettou et al. 2023, dado
diferente) como alvo confiável. Não é contraditório, mas adiciona
matiz: **conclusão pode não ser o que o algoritmo mais recompensa**, então
otimizar só para "terminar o vídeo" pode estar mirando a métrica errada.
Sinal de seguir + tempo assistido (mesmo sem concluir) podem pesar mais
na prática do que o clímax/fechamento do clipe. Não mudar o motor sem
mais evidência, mas **parar de tratar "watch-to-end" como proxy único de
sucesso** ao interpretar `desempenho.py`.

### 19.3 Diferença real entre plataformas — novo, útil se formos multi-plataforma
Relevante para a decisão pendente do §17.3 (spillover cross-platform):

| Plataforma | Força relativa | Implicação pra expansão de tema |
|---|---|---|
| **TikTok** | mais acurácia/serendipidade percebida `[PAPER]` (Roberts & David 2025) | expansão adjacente funciona melhor mantendo coerência **comportamental** forte |
| **Instagram Reels** | ênfase maior em hashtag trending e visibilidade | expansão ajuda alcance mais fácil, mas evidência de retenção é fraca |
| **YouTube Shorts** | integrado à busca/ecossistema YouTube | expansão pode servir de porta de entrada pra conteúdo mais longo (nós não temos "conteúdo mais longo" hoje — canal é só clipe) |

**→ Se a decisão pendente do §17.3 (publicar também fora do TikTok) for
autorizada**, a expectativa correta não é "mesmo resultado em todo
lugar" — Reels tende a favorecer alcance via hashtag mais do que TikTok,
Shorts tende a funcionar como porta de entrada pro ecossistema YouTube
(o que não faz sentido pra nós hoje, já que não publicamos vídeo longo).

**Procedência:** rodada paralela às mesmas 3 perguntas do §18, corpus
diferente (Boeker & Urman 2022; Zannettou et al. 2023; Roberts & David
2025 como âncoras novas). Consensus, 27/07/2026. PDF em
`C:\Users\T3610\Downloads\Pergunta_1_Limiar_de_expanso_Em_contas_novas_d.pdf`.

---

## 20. Sétima rodada Consensus `[PAPER]` — desenho do final do clipe: rewatch vs. follow, 27/07/2026

Primeira pergunta feita no **formato canônico** de Bryan (uma pergunta,
inglês acadêmico, contexto + sub-perguntas + "do not"). Resultado: rewatch
e follow são sinais **diferentes**, com desenhos de final **diferentes** —
não existe "final ideal único".

### 20.1 Rewatch — gap não resolvido, não suspense genérico
- **Final não resolvido aumenta desejo por "mais um episódio" mais que
  final resolvido**, mesmo sem aumentar o prazer da peça em si — mapeia
  melhor pra replay do que pra "gostei". `[PAPER]` (Schibler et al. 2023,
  cliffhanger)
- **Prompt de curiosidade guiado por pergunta** aumenta curiosidade e
  visualização subsequente mais focada/intencional. `[PAPER]` (Tan et al.
  2025)
- **CTA verbal de "se inscreva" sozinho não aumenta inscrição** em estudo
  grande no YouTube (8.500 vídeos) — mas CTA de "curtir" no meio do vídeo
  aumenta curtida. `[PAPER]` (Anderson et al. 2025)
- **Ressalva importante**: gap grande demais frustra; a curva é
  **curvilínea** — quando a informação já é vaga, adicionar concretude
  ajuda a seleção; quando já é concreta, reter um pouco ajuda. `[PAPER]`
  (Quéré & Matias 2025) **→ Para documentário/entrevista, final
  parcialmente resolvido é mais defensável que corte tipo teaser puro.**
- **Loop-back (final que retorna ao início)**: evidência mais fraca (1
  fonte, análise formal não-empírica), mas é hipótese plausível —
  movimento que continua através do corte torna a costura "leve".
  `[FRACO]` (Heorhii 2025)
- **Ressalva ética/qualidade**: assistir de novo faz o comportamento
  parecer **mais ensaiado e menos espontâneo** (9 experimentos). Para
  documentário/entrevista, é trade-off real: final que convida replay
  pode custar um pouco de "candidez" percebida. `[PAPER]` (Donnelly et al.
  2024)

### 20.2 Follow — não é "like mais forte", é sinal de compromisso futuro
Confirma e aprofunda o §19.1: seguir é tratado como sinal de
**preferência de nível de criador e valor futuro esperado**, não
subproduto de watch time. `[PAPER]` (Boeker & Urman 2022; Cai et al.
2023)

| Sinal | O que a evidência sugere | Diferença de like/share |
|---|---|---|
| Seguir | preferência de criador + valor futuro esperado | compromete exposição futura, não só aprovação de 1 item |
| Curtir | aprovação de baixo custo/item único | reação a um clipe só |
| Compartilhar | ação esparsa, distorcida, limiar alto | sinaliza utilidade/valor social excepcional |

- **Endereçamento direto (falar olhando pra câmera) aumenta experiência
  parassocial especificamente** — mais candidato a conversão de "seguir"
  do que a replay. `[PAPER]` (Cohen et al. 2018)
- **Similaridade percebida fortalece vínculo parassocial** em vídeo curto.
  `[PAPER]` (Xie et al. 2025)
- **CTA de inscrição pura não funciona** (mesmo achado do §20.1) —
  lógica de custo-benefício: ação de baixo atrito (curtir) responde a
  prompt, compromisso de alto atrito (seguir) não. `[PAPER]` (Anderson et
  al. 2025)
- **Melhor lógica de follow para canal de não-ficção**: usar o final pra
  sinalizar que existe **mais valor coerente no corpo de trabalho do
  criador** — prompt guiado por pergunta apontando pro próximo
  explicador/clipe aumentou curiosidade e visualização subsequente
  intencional. **Mecanismo é "seguir pela série", não "dá o follow
  agora".** `[PAPER]` (Tan et al. 2025)

### 20.3 Watch time, conclusão, replay e follow são sinais diferentes — não confundir
Tabela do próprio relatório, direto aplicável ao `desempenho.py`:

| Medida | Limitação principal | Implicação pro desenho do final |
|---|---|---|
| Watch time bruto | fortemente confundido por duração | não inferir qualidade do final só por segundos assistidos |
| Conclusão | comparável só dentro da mesma faixa de duração | final resolvido pode aumentar conclusão **sem** aumentar replay |
| Replay | sinal direto de interesse além da duração | melhor proxy de "loopabilidade"/curiosidade não resolvida |
| Follow | preferência persistente de criador | melhor proxy de confiança/valor seriado |

Dado do TikTok (mesma fonte do §19.2): só **45% das views chegam ao
final**, e isso não sobe com o tempo — **conclusão claramente não é o
único alvo do sistema**. `[PAPER]` (Zannettou et al. 2023, confirma §19.2)

### 20.4 O que isto muda no motor (ações concretas)

| # | Mudança | Onde | Status |
|---|---|---|---|
| 1 | Final do clipe: terminar em afirmação/contraste/pergunta não resolvida que a abertura já recontextualiza — não em resolução total | `engine/selecao.py` (prompt), corte do clipe | candidato, a testar no lote atual |
| 2 | Não usar CTA verbal de "segue a gente" — não funciona sozinho | roteiro/edição | ✅ confirma que não vale a pena investir nisso |
| 3 | Se houver fala direta pra câmera na fonte, priorizar manter esse trecho perto do final (parassocial → follow) | seleção de clipe | candidato |
| 4 | Ao medir desempenho, tratar replay e follow como sinais **separados** de watch time/conclusão — não usar só "% assistido" como proxy de sucesso do final | `desempenho.py` | reforça §19.2, ainda a implementar (TikTok não expõe replay count nativamente pro criador — checar se aparece no painel) |
| 5 | Final "parcialmente resolvido" (não teaser puro, não resolução total) para nicho documentário/entrevista | `engine/selecao.py` | candidato |

**Lacuna reconhecida pelo próprio relatório**: quase não há teste causal
direto de edição de final especificamente em vídeo curto de não-ficção —
loop-back, CTA integrado e endereçamento direto no final continuam
**hipóteses informadas por evidência**, não efeitos estabelecidos.

**Procedência:** primeira pergunta no formato canônico (ver
`bfv-consensus-question-pattern.md`), continuação de §19.1. Consensus,
27/07/2026. PDF em
`C:\Users\T3610\Downloads\What_structural_and_editing_features_of_a_short-fo.pdf`.

---

## 21. Oitava rodada Consensus `[PAPER]` — combinar gap não resolvido + endereçamento direto no mesmo final, 27/07/2026

Pergunta de acompanhamento direto do §20: dá pra combinar os dois
mecanismos (rewatch via gap aberto, follow via fala direta pra câmera) no
mesmo final, ou competem? N=17 estudos avaliados, **71% sim / 24% não /
6% misto**.

### 21.1 Resposta: sim, mas em sequência — não simultâneo
Os dois mecanismos **coexistem**, mas evidência favorece **sequenciamento
breve**, não um final único onde os dois competem ao mesmo tempo pela
atenção. `[PAPER]` (síntese do corpus, N=17)

- Final não resolvido **não reduz prazer**, só aumenta desejo de
  continuação — não "estraga" o fechamento por si só. `[PAPER]` (Schibler
  et al. 2023)
- Endereçamento direto tem efeito robusto próprio em experiência
  parassocial, **mesmo com conteúdo informacional controlado** — o
  mecanismo é o próprio formato de olhar+falar, não informação extra.
  `[PAPER]` (Atad & Cohen 2023)
- **Risco de interferência vem de pesquisa de atenção/carga cognitiva**:
  inputs concorrentes redundantes ou irrelevantes prejudicam
  processamento porque o espectador divide atenção limitada entre fluxos
  competindo. `[PAPER]` (Mayer et al. 2001) Ativação emocional aguça
  atenção quando a pista é relevante à tarefa, **atrapalha quando é
  irrelevante**. `[PAPER]` (Zsidó 2023)

**→ Regra prática**: se a fala direta pra câmera funcionar como
**conclusão natural** do gap aberto (parece parte do mesmo raciocínio),
os dois reforçam. Se parecer uma "segunda tarefa" emendada por cima
(ex.: gancho de conteúdo + depois, separadamente, "me segue"), vira
interferência. `[PAPER]` (Heorhii 2025 — CTA deve estar integrado no
frame, não como card de título separado)

### 21.2 Ordem importa: conteúdo não resolvido PRIMEIRO, endereçamento direto DEPOIS (breve)
Evidência favorece **gap de conteúdo → depois um momento breve de
endereçamento direto**, não o inverso. `[PAPER]`

| Sequência | Resultado provável | Base |
|---|---|---|
| **Gap → endereçamento direto (breve)** | preserva curiosidade, depois converte em ação dirigida ao espectador | recomendado |
| Endereçamento direto → gap | traço de curiosidade final mais forte, mas o pedido social explícito perde retenção | efeito de recência: o que vem por último domina a memória imediata |
| Sobreposição total simultânea | maior risco de interferência | split-attention / competição de metas |

Motivo: **efeito de posição serial/recência** — o que fica por último
domina o traço de memória imediata. Se o endereçamento vier primeiro e o
gap por último, o gap "engole" o pedido social. `[PAPER]` (Pieters &
Bijmolt 1997; Boswell & Terry 2005)

### 21.3 Duração do trecho de endereçamento direto — sem número, mas com princípio
**Não há evidência experimental direta** pra duração ideal em clipe de
60-110s. Conclusão mais segura possível: **o trecho de endereçamento
direto deve ser breve o suficiente pra não virar um "segundo final"** —
o próprio olhar direto carrega o efeito, sem precisar de muito material
explicativo extra. `[PAPER]` (inferência de Mayer et al. 2001; Zsidó
2023; Atad & Cohen 2023; Kuang et al. 2023)

### 21.4 O que isto muda no motor (ações concretas)

| # | Mudança | Onde | Status |
|---|---|---|---|
| 1 | Estrutura de final: gap/contraste não resolvido → corte breve de fala direta pra câmera (se existir na fonte) → fim. Nunca o inverso. | `engine/selecao.py` (prompt de seleção/corte) | candidato a testar no lote atual |
| 2 | Endereçamento direto deve ser **integrado** ao raciocínio do gap (soar como conclusão natural), não como CTA separado tipo "segue a gente" plugado depois | edição/seleção de trecho | reforça §20.4 item 2/3 |
| 3 | Manter o trecho de endereçamento direto **curto** — não alongar o clipe só pra caber isso | corte final | princípio, sem número exato |
| 4 | Se a fonte não tiver momento de fala direta pra câmera perto do final, não forçar — não inventar endereçamento sintético | seleção de fonte/trecho | guardrail |

**Maior lacuna reconhecida pelo relatório**: nenhum experimento fatorial
testa diretamente "sobreposição simultânea vs. final micro-sequenciado"
em clipe curto de não-ficção real — a inferência é a mais forte possível
com a evidência disponível, mas ainda não é teste direto.

**Procedência:** continuação direta de §20, segunda pergunta no formato
canônico. Consensus, 27/07/2026, N=17. PDF em
`C:\Users\T3610\Downloads\Can_a_short-form_video_ending_combine_an_unresolve.pdf`.

---

## 22. Nona rodada Consensus `[PAPER]` — cold-start: alocação inicial e sinais de promoção, 28/07/2026

Resolve a **pergunta 1 do §13**, que estava `[ABERTO]` e era chamada de
prioridade 1 no `SABEDORIA_TIKTOK.md` ("governa tudo o resto"). Corpus:
87,1M recuperados, 1,3K elegíveis, **50 incluídos**, 22 buscas.

### 22.1 Tamanho da entrega inicial
- **~100 usuários** na primeira exposição de um vídeo novo. `[PAPER]`
  (Li et al. 2024, Snapchat) — evidência **moderada**, plataforma única.
- No Kuaishou, "cold-start" é definido operacionalmente como vídeo com
  **menos de 4.000 views nas primeiras 24h**; a métrica "Climbing 4k"
  marca a transição de 0 para 4.000 views em **dois dias** como o ponto
  em que sai da coorte inicial. `[PAPER]` (Chen et al. 2024)
- **Para o TikTok, os números são GAP declarado.** O relatório é
  explícito: não existe dado empírico publicado de limiar do TikTok, e
  essa é "a lacuna mais marcante" do corpus. Usar os números do Kuaishou
  como ordem de grandeza, **nunca como limiar nosso**.

### 22.2 Quem recebe o vídeo numa conta nova — o achado que mais importa
Conta **sem grafo social** não recebe audiência por seguidores: o sistema
aloca por **embedding multimodal do próprio conteúdo** (visual, áudio e
texto). `[PAPER]` — evidência **forte**, replicado em estudos
independentes (Chen et al. 2024; Deldjoo et al. 2019; Chen et al. 2025).

Consequência prática direta: **na Fase 1 é o vídeo que define quem o vê,
não a conta.** Isso dá base científica ao núcleo semântico único do §17.4
— embedding consistente entre posts ajuda o sistema a achar o público
certo mais rápido. Também eleva a importância da legenda e das hashtags:
elas são entrada de texto do embedding, não enfeite.

O Kuaishou usa um "coverage mechanism" que garante exposição mínima a
todo vídeo, independente de seguidores, justamente para corrigir o viés
contra conta nova. `[PAPER]` (Chen et al. 2025)

### 22.3 Hierarquia dos sinais
| Sinal | Papel | Força |
|---|---|---|
| **Watch time** | sinal dominante da decisão de promover | `[PAPER]` **forte** |
| NAWP (watch % normalizado por duração) | mais robusto que watch time cru | `[PAPER]` |
| ECR (assistiu além de ~5s) | prevê sustentação de atenção | `[PAPER]` |
| Likes, comentários, shares | secundários; mais esparsos e ruidosos | `[PAPER]` |
| Skip | sinal **negativo**, informa supressão | `[PAPER]` |

- Watch time pesa mais por ser o sinal **mais frequente e menos ruidoso**,
  não por ser conceitualmente superior. `[PAPER]` (Xiao 2025)
- Entre os explícitos, **share é o mais forte** — propaga para a rede de
  outro usuário. `[PAPER]` (Dong et al. 2023)
- **Limiar de 50% de watch time** define "assistido" em sistema de
  produção — mas vem de plataforma de e-commerce com vídeo curto, **não
  do TikTok nem do Kuaishou**. Generalização limitada, o próprio relatório
  ressalva. `[PAPER]` (Dzhoha et al. 2025)

### 22.4 O achado que contraria intuição
Estudo de doação de dados de usuários reais de TikTok: **só 45% das views
chegam ao fim**, e a atenção não cresce ao longo do vídeo — sugerindo que
o algoritmo prioriza **tempo gasto e curtida acima de completude**.
`[PAPER]` (Zannettou et al. 2023)

Isso reforça a regra de duração >60s do §13.5: perseguir taxa de
completude alta é otimizar a métrica errada. Métrica normalizada por
duração (NAWP) alinha melhor com retenção real que completude simples.
`[PAPER]` (Saket et al. 2023)

### 22.5 O que muda no nosso método
| # | Decisão | Onde | Base |
|---|---|---|---|
| 1 | Primeiros ~5s viram prioridade de edição — ECR mede exatamente isso | seleção/render | §22.3 |
| 2 | Manter núcleo semântico estreito na Fase 1 | curadoria | §22.2, confirma §17.4 |
| 3 | Legenda e hashtags são entrada do embedding — relevância estrita, sem carona | `publicar_tiktok.py` | §22.2 |
| 4 | Não perseguir completude; perseguir tempo assistido | métrica de sucesso | §22.4 |
| 5 | Não adotar 4.000 views como limiar nosso — é Kuaishou, não TikTok | `desempenho.py` | §22.1 |

O item 1 dá base ao "choque visual nos primeiros 0.2-0.3s" que o
`SABEDORIA_TIKTOK.md` §3 listava como **não implementado** — agora tem
suporte de paper, não só de guru.

**Maior lacuna reconhecida pelo relatório**: ausência quase total de dado
empírico de limiar para TikTok e YouTube Shorts, apesar de dominarem o
ecossistema. O Kuaishou é a plataforma melhor documentada, e é justamente
a que não usamos. **Não promover número de Kuaishou a fato de TikTok.**

**Procedência:** primeira pergunta do roteiro do `SABEDORIA_TIKTOK.md` §7,
formato canônico (`bfv-consensus-question-pattern.md`). Consensus,
28/07/2026, N=50. PDF em `sabedoria/raw/`.
