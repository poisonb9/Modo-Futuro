# HANDOFF — 15/09/2026, parte 4 (a noite, entrando na madrugada de 16/09)

Quarta sessão do mesmo dia. As três anteriores estão em
[`HANDOFF_15-09-2026.md`](HANDOFF_15-09-2026.md),
[`HANDOFF_15-09-2026_NOITE.md`](HANDOFF_15-09-2026_NOITE.md) e
[`HANDOFF_15-09-2026_PARTE3.md`](HANDOFF_15-09-2026_PARTE3.md).

**16 commits.** O canal do Telegram saiu do papel e **o item irreversível
fechou**. E o achado mais caro da sessão não foi um recurso: foi descobrir que
**o site anunciava preço que não existia mais**, em 14 de 14 conferidos.

---

## ESTADO NO FECHAMENTO

```
local e remoto   834f67f    0 a 0
no ar            achadinhototal.pages.dev   carimbo 6e5bbddfffa2   147 produtos
canal            t.me/achadinhototal        4 produtos postados
instantaneo      estado/precos_agora.json   153 produtos
```

⚠️ **Sujos que NÃO se commita:** `radar_modofuturo.json`,
`estado/baixados_em_intervalos.json`, `estado/videos_trabalhados.json`,
`relato_*.txt`, `paginas/avatares/logo_app_aliexpress_100.png`

---

## 1. 🔴 O `tracking_id` POR CANAL — FECHADO

O único item irreversível da lista morreu. O Bryan criou os ids no Portals e
deixou quatro de reserva. **Provado antes de ligar**, com
`teste/fumaca_tracking.py`:

```
default        VALIDO      achadinho   402 TrackingId input parameter error
achadinhomake  VALIDO      bryan       402
achadinhochef  VALIDO      tiktok      402
instantaneos   VALIDO
pagomenos      VALIDO
atefalhar      VALIDO
modofuturo     VALIDO
achadinhototal VALIDO
```

⭐ **Os três recusados é que fazem a prova valer** — um `link.generate` que
aceitasse qualquer string passaria com nota dez. Ficam na lista para sempre.

⛔ **`semanestesia.pod` continua comentado**: esse id NÃO existe no painel (os
dez foram conferidos na tela). Escrevê-lo devolveria link que abre a página e
não paga. Ele cai no `default`, que é o lado seguro.

⚠️ **A partir da próxima rodada do garimpo (10h23 UTC) a venda tem canal.** O
que entrou antes fica sem, para sempre.

---

## 2. 🔴 O SITE ANUNCIAVA PREÇO QUE NÃO EXISTE MAIS

Conferido contra a API do AliExpress, em produtos **que estavam no ar**:

```
na pagina R$  20,11   ultima leitura nossa R$   9,35   API 9.35
na pagina R$  65,87                        R$  51,99   API 51.99
na pagina R$ 142,10                        R$ 107,89   API 107.89
na pagina R$  88,88                        R$  22,69   API 22.73
                    14 de 14 diferentes, sempre PRA CIMA
```

⭐ **E o preço certo JÁ ESTAVA no nosso banco.** O garimpo reconfere todo dia e
grava em `precos_vistos.jsonl`; a trava de honestidade da página consulta essa
mesma série e aprova com razão — e aí a página imprimia o número velho da linha
histórica do `produtos_publicados.jsonl`, que é append-only e guarda o preço
**do dia da captura**. O conserto não custou uma chamada de API.

⚠️ **O erro estava do lado "seguro"** (anunciávamos mais caro), por isso ninguém
reclamaria: o comprador chega e acha mais barato. Mas ele apaga o que a operação
vende — a QUEDA anunciada ficava menor que a real. **Erro a nosso desfavor
também não se confere sozinho.**

### As três mudanças, nos TRÊS lugares que montam preço

1. o preço sai de `_precos_por_dia()`, a MESMA fonte do gráfico e da queda
2. janela de 48h → **24h** (decisão do Bryan: "48 é muito")
3. ⛔ a trava passa a **falhar FECHADA**. Era `if visto_em and visto_em <
   limite` — produto SEM leitura nenhuma passava direto. A guarda barrava quem
   tinha data velha e deixava entrar quem não tinha data.

Custo medido das duas últimas: **158 → 152 produtos**.

---

## 3. ⭐ RECONFERÊNCIA DE HORA EM HORA (`engine/precos.py`)

Ordem do Bryan. Dá para fazer porque o `productdetail.get` **aceita lote**:

```
  1 id  ->   1 devolvido  1,9 s
 50 ids ->  50            3,2 s
100 ids ->  50            3,3 s   ⛔ cortou pela metade, code=200, sem erro
```

Catálogo inteiro (154) em **4 chamadas e ~13 s**. ~96 chamadas/dia contra as
centenas que o garimpo já gasta sem bater teto.

⚠️ **Teto diário: não sei, e não achei onde consultar.** O que está medido é o
custo relativo.

`.github/workflows/precos.yml` — **24 crons, um por hora, minutos todos
diferentes e nenhum no minuto cheio** (pedido do Bryan; o cron do GitHub não
sorteia). Duas horas foram escolhidas: **10h56** depois do garimpo, **12h06**
antes do post da manhã.

### ⛔ O defeito que eu mesmo escrevi e a primeira rodada expôs

O relato dizia "153 reconferidos" e o arquivo saía com **104**. A causa era um
`except (KeyError, TypeError): prods = []` meu: **chamada que falhou** virava
"este lote não tem produto", indistinguível de "estes produtos saíram do ar".
São coisas opostas — produto fora do ar é informação, chamada falhada é
ausência de informação. Agora levanta com o corpo junto, e há 2 s entre lotes.

⚠️ **Dois arquivos, papéis separados:** `precos_vistos.jsonl` é a SÉRIE (um
ponto por dia, de onde saem o "de" riscado e o gráfico); `precos_agora.json` é
o INSTANTÂNEO (de onde sai o preço exibido). A série consolida pelo MENOR do
dia — certo para não inflar queda, errado para exibir.

---

## 4. O CANAL DO TELEGRAM ESTÁ VIVO

### `engine/cartaz.py` — a imagem 9x16 do produto

⛔ **O selo de queda não recebe número pronto.** Recebe os dois preços e deriva.
Imagem salva viaja e não se recalcula depois.

⛔ **A fonte vem do repo** (Poppins-Bold). O rascunho pedia `segoeuib.ttf` ao
Windows com `load_default()` de reserva: na nuvem a reserva entra sozinha e o
cartaz sai com fonte bitmap minúscula **sem levantar erro**.

⭐ **Brilho cobre a peça inteira** (escolha do Bryan entre três medidas, ficou a
do meio: cantos em 47/56, eram 13/23). Guarda nova mede cantos **e** contraste
WCAG do nome, preço e preço riscado (11,0 / 9,3 / **4,98**:1, piso 4,5).

### `engine/vitrine.py` — cadência e encanamento

```
python -m engine.vitrine --quantos 3
09:17 · 15:23 · 20:13 (BRT), 90 s entre posts
```

⛔ **O link vai no BOTÃO.** Medido: link de afiliado tem **1.065 caracteres** e
o limite de legenda de foto é 1.024 — **272 de 277 posts** sairiam partidos em
duas bolhas. Com botão a legenda cai para 111 chars.

⛔ **A fila ia repostar o mesmo produto até 27 vezes.** 302 linhas com link,
**154 ids**: o garimpo regenera o link a cada rodada e a chave do "já postado"
era o link. Agora a identidade é o `id`, com a FOTO de reserva. Fila: 273 → 152.

⛔ **`produto.normalizar` era o único lugar que descartava o campo `imagem`** —
por isso o canal postou texto puro desde que existe. Defeito silencioso.

⛔ **Falha ABERTA no cartaz** (ao contrário da regra): foto que não baixa não
leva o post junto. Mas o post **nunca** sai sem link.

---

## 5. 🚨 OS ERROS MEUS DESTA SESSÃO

⛔ **O teste escrevia no estado de PRODUÇÃO.** `vitrine.postar` chama
`resultado.anotar_publicado`, que grava em `produtos_publicados.jsonl` — o
arquivo que alimenta o site E a fila. Eu redirecionei UM registro e parei aí.
Oito rodadas enfiaram **41 linhas de dublê** no catálogo. Não havia sinal
nenhum: o `postar` engole a exceção do registro de propósito. **Redirecionar um
registro e concluir que o teste está isolado é a armadilha — procurar sempre o
SEGUNDO lugar que escreve.**

⛔ **Guarda com alarme falso, duas vezes.** A da fonte reprovou por causa da
PRÓPRIA docstring que explica por que a Segoe é proibida (agora lê o código
pelo `ast`). Mesma família do `teste_vitrine_teto` de 15/09.

⛔ **Heredoc comeu `\n` TRÊS vezes** e o replace não casou em silêncio. Duas
vezes o `assert` pegou; uma passou e eu só vi depois. **Arquivo com escape vai
pela ferramenta de edição, nunca por heredoc.**

⛔ **`git add` de arquivo ignorado é recusado e o `&&` curto-circuita.** O
commit não aconteceu e eu quase segui em frente — peguei porque imprimi o log.

⛔ **Datei quatro comentários como 16/09 sendo 15/09.**

⛔ **Commitei com um vermelho na lista** (`teste_vitrine_produtos_reais`) porque
o loop não derruba o `&&`. Era defeito do dublê, não do motor — mas eu só
descobri depois de commitar.

⛔ **O dublê da API não interceptava nada.** Trocar `sys.modules` não pega
`from . import aliexpress`, que lê o atributo do pacote. O teste chamava a API
DE VERDADE e passava porque o preço real batia. **As guardas de falha é que
denunciaram.**

⛔ **Afirmei uma causa errada para o travamento do RDP** (`fPromptForPassword`)
— ela **já estava em 0**. Escrevi o valor que já existia.

---

## 6. ⚠️ A VPS — o problema que interrompeu a sessão

O Bryan reconectou e a tela ficou em **"Please wait"**. Medido:

```
maquina    CPU 7%   uptime 9h47m   disco 22 GB livres
memoria    1,0 GB livre de 10,0 GB      <- apertado, mas SEM evento de pressao
sessao     Active, explorer vivo desde 14:29, tudo Responding
7 dias     197 desconexoes (id 40, reason code 5), 78 reconexoes, 3 logons
```

⭐ **O link cai ~28 vezes por dia.** A sessão é sempre a mesma; só o link morre.

**O que foi tentado, na ordem:** matar o `LogonUI` (respawna), `tscon 1
/dest:console` (limpa o bloqueio, mas volta na reconexão), `tsdiscon` limpo.
Nada resolveu.

⭐ **A pista mais concreta, e não chegou a ser testada:** `DisableCAD = 0` — a
máquina exige **Ctrl+Alt+Del** antes de mostrar o campo de senha, e dentro do
RDP isso é **Ctrl+Alt+End**. A tela estática pode ser exatamente isso.

✅ Descartados por medição: limite de inatividade, protetor de tela com senha,
política de sessão, credential provider de terceiro (os 20 são da Microsoft),
`TermService`/`SessionEnv`/`UmRdpService` todos Running.

⚠️ `C:\Users\Administrator\Desktop\DESTRAVAR_SESSAO.bat` faz o `tscon` num
clique. E `BACKUP_RDP_fPromptForPassword.reg` é cópia da chave (não há o que
reverter — o valor não mudou).

⚠️ **Nada disso afeta a operação:** garimpo, vitrine e preços rodam na nuvem.

---

## 7. 🔴 O QUE CONTINUA ABERTO

1. 🔴 **AWIN — não andou nada.** `JOINED 1 · PENDING 20 · REJECTED 8`, igual a
   ontem. E **os dois campos nunca foram colados** (`Site` = raiz, `URL do
   Blog` = `/parceiros`): os 20 pendentes estão sendo julgados olhando a bio de
   maquiagem, que foi a causa medida da recusa da 365Rider. **Pegar a chave de
   datafeed na mesma visita** — o `AWIN_TOKEN` responde 500 em
   `productdata.awin.com/datafeed/list`, é outra chave.
2. 🔴 **Awin: encaminhar os 6 e-mails de recusa** — responde se o MEI destrava
   6 anunciantes ou 1, antes de abrir CNPJ.
3. 🟠 **Shopee:** ⭐ **Maree ATIVADA** (15/09). Falta só a **API** — chamado de
   suporte sem resposta há dias.
4. ⚠️ **A guarda de publicação conta certo e cala o nome.** Disse `publicado: 6
   projetos` e `confirmado em 5` — e não diz QUAL não confirmou.
5. **A varredura lidera a fila.** Os primeiros da fila são ferramenta, carro e
   jardim (sem canal, sem linha de origem). Bryan ainda não decidiu: deixar,
   mandar pro fim, ou intercalar (recomendado 2 de canal + 1 de varredura).
6. **O nome do produto aparece duas vezes** no post (cartaz + legenda).
7. **Achadinho da madrugada** — pedido como "talvez". Exige buscar detalhe na
   API (a série só tem id/preço/loja/data) e uma regra de curadoria.
8. **As 4 etiquetas duplicadas no ML**, para apagar no painel.
9. **`engine/video_produto.py`** — ⛔ **o Ken Burns foi RECUSADO pelo Bryan**
   ("não ficou legal"). O handoff da manhã dizia "Ken Burns de padrão": aquela
   nota era de FIDELIDADE (0,9888), e fidelidade alta ali é trivial — é a mesma
   imagem se movendo. **Vídeo não está decidido; não montar motor.**
10. **`engine/imagem_premium.py`** virou `engine/cartaz.py` — item fechado.
11. **Terceira perna do ModelScope** em `nome_produto.py` e `combina.py`.
12. **Arte do Achadinho Chef**, **endereço do Até Falhar**, **links de bio**.
13. **Moeda para quem acessa de fora do Brasil** — decisão pendente.

---

## 8. REGRAS QUE ESTA SESSÃO ACRESCENTOU

⛔ **Registro histórico não é preço de hoje.** `produtos_publicados.jsonl` é
append-only: o `preco` é o do dia da captura. Quem exibe preço lê a série.

⛔ **Chamada que falhou ≠ resultado vazio.** Foi isso que apagou 49 preços em
silêncio.

⛔ **Identidade de produto é o `id`, com a FOTO de reserva — nunca o link.** O
link de afiliado é regerado a cada rodada.

⛔ **Teste que exercita caminho de produção tem MAIS de um registro para
redirecionar.**

⛔ **`git check-ignore -v` mente com regra de negação** (sai 0 casando com o
`!`). A prova é `git add --dry-run`.

⭐ **Guarda que conta sem nomear é guarda que será ignorada** ("confirmado em 5"
sem dizer qual dos 6 faltou).
