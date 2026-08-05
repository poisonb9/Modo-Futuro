# Handoff — 05/08/2026 (parte 2)

> Continuação de `handoff_05-08-2026.md` (parte 1, sessão da madrugada).
> Onde houver conflito, **este manda**. Sessão: fechou o teste de ponta-a-
> ponta da voz clonada que a parte 1 tinha deixado pendente, e depois de
> 5 iterações guiadas pelo Bryan ouvindo cada resultado, chegou no que ele
> aprovou como **padrão universal de corte daqui em diante**: dublagem +
> narração + legenda sincronizada + estilo 2.

---

# PARTE A — Bug do idioma: dublagem estava sendo pulada silenciosamente

O primeiro run desta sessão (`--dublar true`, `--idioma pt` no padrão do
workflow) terminou com sucesso, legenda ótima, gancho ótimo — mas **sem
dublagem nenhuma**, áudio original em inglês.

Causa, achada lendo `main.py:206`:
```python
precisa_traduzir = (traduzir or dublar) and idioma != "pt" and ps
```
O vídeo fonte ("Rise of the Humanoids") é em **inglês**, mas o disparo
usou `idioma=pt` (padrão do `cortar_de_bruto.yml`). Como `idioma == "pt"`,
o código concluiu que não havia nada pra traduzir e pulou o bloco de
dublagem inteiro, mesmo com `--dublar` ativo — sem erro, sem aviso.

**Não é bug de código, foi disparo errado** (`idioma` tem que ser o
idioma FALADO NO VÍDEO FONTE, não o idioma de saída — a dublagem sempre
sai em pt-BR fixo, ver `IDIOMA_PADRAO` em `engine/voz_clonada.py`).
**Lição pra próximos disparos: sempre confirmar o idioma do vídeo fonte
antes de disparar com `--dublar`.**

---

# PARTE B — `--recorte` no workflow: refazer um clipe específico

Bryan pediu pra reprocessar só o clipe 002 (já visto sem dublagem) pra
comparar. `main.py` já tinha `--recorte INICIO-FIM` (pula seleção do
Gemini, corta o trecho exato), mas o `cortar_de_bruto.yml` não expunha
esse input. Adicionado (commit `1f675ed`). Uso:
```
recorte: "1409.7-1502.4"
```
Útil pra qualquer teste futuro que precise refazer um trecho exato sem
gastar Gemini escolhendo de novo.

Também: o bruto se limpa (vai pra lixeira do Drive) no fim de todo run
bem-sucedido. Pra reusar sem rebaixar do YouTube, restaura da lixeira:
```python
from limpar_bruto_drive import _servico
s = _servico('principal')
s.files().update(fileId=FILE_ID, body={'trashed': False}).execute()
```
(recuperável por até 30 dias da limpeza)

---

# PARTE C — 5 iterações até a dublagem ficar aprovada

Todas testadas no mesmo trecho (clipe 002, `1409.7-1502.4`, fonte "Rise
of the Humanoids") pra isolar cada mudança. Bryan ouviu cada versão.

## C.1 — Tradução literal por janela de 4s (estado anterior, parte 1)
Cada janela de ~4s da transcrição original era traduzida **isoladamente**.
Como a fala original tem entrevistador perguntando / entrevistado
respondendo / cacoetes ("ok ok", repetição), a voz clonada (uma pessoa
só) saía **"interpretando os dois lados do diálogo"** — Bryan: "ficou
estranho a minha voz dublando as duas pessoas".

**Fix**: `engine/traducao.py` ganhou `PROMPT_NARRACAO` + `narrar=True` em
`traduzir_segmentos` — em vez de traduzir cada janela isolada, reescreve
o trecho INTEIRO de uma vez como narração de um narrador contando o que
aconteceu (não dublando as falas dos personagens). Ajustado 2x até o
prompt pedir explicitamente "narrador RELATANDO os fatos", não só "narrador
único" (commits `4b9677b`, `b3eb1b9`).

## C.2 — Síntese picada por janela de 4s (causava pausas erradas)
Cada janela de texto virava um TTS separado, esticado/comprimido pra
caber na janela original. Corte de texto por tempo não respeita
pontuação → pausa de início/fim de CADA pedaço caía no meio da frase,
não na vírgula. Bryan: "tem pausa fora de vírgula".

## C.3 — Tentativa 1 do fix: síntese inteira numa tacada só (RUIM)
Juntei todo o texto reescrito e mandei pro Chatterbox de uma vez.
**Piorou**: o modelo não aguenta bem textos contínuos de ~90s (ele é
calibrado pra frases curtas, ~154s pra sintetizar 24 palavras — ver
comentário em `engine/voz_clonada.py`). Bryan: "a voz está arrastando de
tão lenta... a dicção ficou prejudicada".

## C.4 — Tentativa 2 do fix: frase por frase (APROVADO)
Divide o texto reescrito por pontuação de fim de frase (`. ! ?`), gera
um TTS curto por frase (regime bom do modelo), concatena com uma pausa
curta fixa (0.15s) entre frases, e só então aplica UM `atempo` suave no
áudio inteiro pro tamanho do clipe — não mais um atempo por pedaço.
Commit `94e967d`. Bryan: **"Ficou muito bom!! A voz tá excelente a
dublagem tá ótima"**.

## C.5 — Legenda "correndo" (último ajuste)
Com a dublagem mudando de arquitetura (pausa fixa entre frases + atempo
único no fim), a legenda continuava usando o timing do VÍDEO FONTE — que
não bate mais com o ritmo real do áudio dublado. Bryan: "achei que a
legenda correu um pouco".

**Fix**: `voz_clonada.gerar_trilha` agora devolve também `timing` — o
tempo real de início/fim de cada frase no áudio FINAL (contando pausa
entre frases e a escala do atempo aplicado). `main.py` reconstrói a
legenda (`ps`) a partir desse timing quando `--dublar` com voz clonada,
em vez do timing antigo baseado no vídeo original.
`traducao._redistribuir` virou pública (`redistribuir_palavras`) pra ser
reaproveitada por `voz_clonada.py`. Commit `6f566d3`.

**Resultado final, testado no mesmo clipe 002**: Bryan — **"FICOU BOM
DEMAIS!!! Parabéns!!"**

---

# PARTE D — Padrão universal de corte, a partir de agora

Bryan pediu explicitamente pra isso virar o **padrão universal de cortes
daqui em diante**, não só um teste isolado. O que isso significa na
prática:

1. **`--dublar true`** sempre que fizer sentido pro vídeo (voz clonada,
   Chatterbox) — já é o default do `cortar_de_bruto.yml`.
2. **`--estilo-legenda 2`** agora é o **default** do workflow (commit
   `a10c24a`), porque foi o estilo usado em todos os testes aprovados.
3. **`--idioma` tem que ser o idioma FALADO no vídeo fonte**, sempre
   conferido antes de disparar — nunca deixar no "pt" padrão sem checar
   (ver Parte A, foi o que quebrou a primeira tentativa desta sessão).
4. O comportamento de narração + síntese por frase + legenda sincronizada
   já está embutido no código (`engine/traducao.py`,
   `engine/voz_clonada.py`, `main.py`) — roda automaticamente sempre que
   `--dublar` é usado, não precisa lembrar de nenhuma flag extra além do
   `--idioma` correto.

**Não coberto por essa validação**: o workflow `cortar.yml` (corte direto
de uma URL do YouTube, sem passar por bruto no Drive) **não tem** os
inputs `--dublar` nem `--estilo-legenda` — ainda está no formato antigo,
sem dublagem nenhuma. Se algum dia for usado de novo (hoje o fluxo real é
sempre baixar bruto primeiro, depois `cortar_de_bruto.yml`), precisa
receber os mesmos inputs antes de virar "padrão universal" de verdade lá
também. Não fiz essa atualização porque não é o workflow em uso.

---

# PARTE E — Commits desta sessão (nessa ordem)

1. `1f675ed` — adiciona `--recorte` no `cortar_de_bruto.yml`
2. `4b9677b` — narração de 1 narrador em vez de tradução literal por janela
3. `b3eb1b9` — ajusta prompt: narrador RELATA os fatos, não dubla as falas
4. `43d23a7` — dublagem em síntese única (tentativa que **não** deu certo)
5. `94e967d` — dublagem frase por frase + pausa fixa + atempo único (BOA)
6. `6f566d3` — legenda segue timing real do áudio dublado
7. `a10c24a` — `estilo_legenda=2` vira default do workflow

Todos já em `main` no GitHub (push feito com o token de escrita salvo em
`clip_engine/github_token.txt`).

---

# PARTE F — Estado da fila de redo (retomando da parte 1)

Ainda não mexi na fila de redo (032, 038, 041, 042, 045, 046) durante
esta sessão — o foco foi validar e fechar o padrão de dublagem primeiro,
como Bryan pediu. Agora que o padrão está aprovado, os próximos passos
são os da parte 1, sem mudança:

- **032/038**: fonte já identificada ("Rise of the Humanoids",
  `7I-KWkV0JUM`), mas o bruto está de novo **na lixeira do Drive**
  (`drive_file_id=1kEK3iIGRt-UfN4qt1g-hkd8x-4si94ef`, limpo pelo último
  run bem-sucedido desta sessão). Restaurar da lixeira (ver Parte B)
  antes de reusar, em vez de rebaixar do YouTube.
- **041/042/045/046**: fonte ainda não identificada — usar
  `estado/videos_trabalhados.json` ou os `.srt` da pasta `raw/`.
- **047-060 e anteriores a 032**: Bryan ainda não confirmou, não mexer.
- Bryan pediu pra ir de 3 em 3, checando cada lote antes do próximo —
  agora com o padrão de dublagem validado, dá pra aplicar isso na leva
  real de redo.

**Pasta de teste** (`redo_04-08_teste`,
`1XfycKTuyFa2ofTZvnp_kR-hEAL6fO-Za`) acumulou vários clipes 002 de teste
(um por iteração desta sessão) — não são pra postar, são só as tentativas
até chegar na boa. Pode limpar quando quiser, não é urgente.

---

# PARTE G.1 — Ajuste de gênero na narração (achado logo depois da aprovação)

No mesmo clipe de teste, a visitante era mulher mas a narração se referia
a ela como "ele" o tempo todo. Causa: o inglês (fala original) muitas
vezes não deixa o gênero explícito ("you", nome sem pista clara), e a IA
generalizava pro masculino por padrão ao reescrever em português.

**Fix**: `PROMPT_NARRACAO` (`engine/traducao.py`) agora pede
explicitamente pra prestar atenção em qualquer pista de gênero no texto
original (nome, "she"/"her", forma de tratamento) e manter o
pronome/concordância CONSISTENTE do início ao fim; se não houver
nenhuma pista, prefere repetir o papel da pessoa ("a convidada", "o
entrevistado") em vez de chutar. Commit `e3dfed3`. **Ainda não testado
de ponta a ponta** — validar no próximo redo real (não custa conferir no
primeiro vídeo da leva 032/038).

---

# PARTE G — Sem mudança (herdado da parte 1, ainda válido)

- **Shadowban**: TikTok Studio não mostra violação formal. Causa do corte
  de alcance (2/8) ainda sem explicação confirmada.
- **Imagem IA de ponta a ponta** (`engine/imagem_ia.py`, Pollinations
  realista): ainda pendente, não testado nesta sessão.
- **Cartoon**: descartado definitivamente, não retomar.
- **Token do GitHub** (com escrita): `clip_engine/github_token.txt`,
  nunca pedir de novo.
- **`estado/videos_trabalhados.json`**: registro mestre, rastreado no
  git, rodar `--sincronizar` depois de lotes de redo.
- **Nunca tocar em processos do `bryan_fx_vision`.**

---

## 📋 RODAPÉ PARA COLAR NA SESSÃO NOVA (depois do /clear)

```
Projeto Modo Futuro (@modofuturo). Retomando depois de /clear.

ORDEM DE LEITURA:
1. handoff/handoff_05-08-2026.md (parte 1 — teste ponta-a-ponta, bugs de
   infra corrigidos, lista de redo definida)
2. handoff/handoff_05-08-2026_parte2.md (ESTE — padrão de dublagem
   fechado e APROVADO pelo Bryan, estado mais recente)

PADRÃO UNIVERSAL DE CORTE — fechado e aprovado nesta sessão, não mexer
sem necessidade real:
- --dublar true (voz clonada, Chatterbox) sempre que fizer sentido
- --estilo-legenda 2 (já é o default do cortar_de_bruto.yml)
- --idioma tem que ser o idioma FALADO NO VÍDEO FONTE (nunca deixar "pt"
  sem conferir — foi o que quebrou o primeiro disparo desta sessão)
- Dublagem = narração (o narrador CONTA o que aconteceu com base no que
  os personagens disseram, não dubla as falas deles literalmente)
- Síntese de voz é FRASE POR FRASE (não janela de tempo, não tudo numa
  tacada só — as duas alternativas foram testadas e reprovadas)
- Legenda segue o timing REAL do áudio dublado, não o do vídeo fonte
- Gênero da pessoa descrita: a narração tem que pegar pistas de gênero
  do texto original e manter consistente (achado LOGO DEPOIS da
  aprovação, commit e3dfed3, AINDA NÃO TESTADO de ponta a ponta — vale
  conferir no primeiro vídeo real que rodar)
Tudo isso já está no código (engine/traducao.py, engine/voz_clonada.py,
main.py) — roda sozinho sempre que --dublar é usado com --idioma certo.

PRIMEIRA COISA A FAZER — retomar a fila de redo (parte 1, Parte F desta):
vídeos 032, 038, 041, 042, 045, 046 da pasta a_postar/02-08 v2/parte 02
(Drive conta principal), de 3 em 3. 032/038: fonte é "Rise of the
Humanoids" (7I-KWkV0JUM), bruto na LIXEIRA do Drive
(drive_file_id=1kEK3iIGRt-UfN4qt1g-hkd8x-4si94ef) — restaurar antes de
usar (files().update(body={'trashed': False})), não rebaixar do
YouTube. 041/042/045/046: fonte ainda não identificada, usar
estado/videos_trabalhados.json ou .srt em raw/. NÃO mexer em 047-060 nem
anteriores a 032 sem Bryan confirmar de novo.

PENDENTE — vídeo com imagem IA de ponta a ponta: ainda não foi feito
(engine/imagem_ia.py, Pollinations realista). Cartoon descartado
definitivamente, não retomar.

SHADOWBAN: TikTok Studio não mostra violação formal. Causa do corte de
alcance (2/8) continua sem explicação — não é hipótese principal a menos
que surja dado novo.

INFRA: token do GitHub (com escrita) em clip_engine/github_token.txt,
nunca pedir de novo. cortar.yml (fluxo direto de URL, sem bruto no
Drive) NÃO tem --dublar/--estilo-legenda — está desatualizado em relação
ao padrão novo, só mexer nele se for voltar a usar esse fluxo. Pasta de
teste redo_04-08_teste tem várias tentativas do clipe 002 acumuladas,
pode limpar quando quiser. NUNCA tocar em processos do bryan_fx_vision.

NÃO AFIRME NADA SEM MEDIR. Quadro de progresso em texto a cada ação,
separando medido de estimado.
```
