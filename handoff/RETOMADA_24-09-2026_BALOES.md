# RETOMADA — 24/09/2026, balões da inauguração

O anterior é [`RETOMADA_23-09-2026_PARTE3.md`](RETOMADA_23-09-2026_PARTE3.md)
(os dois bugs da barra de abas continuam ABERTOS, não mexi neles).

## 1. Site — commit `c148b88` (empurrado 24/09 ~01:03)

- **Balões** no header (`paginas/todos.html`, bloco "baloes da inauguracao"):
  festa à esquerda (laranja "INAUGURAÇÃO", laço, estrela, etiqueta, sacola,
  lupa), canais à direita (Make, Chef, Instantâneos, Sem Anestesia, Pago
  Menos, Modo Futuro). Celular: 3+3 em arco no brasão. ≥760: 6+6 dos lados
  do título. ≥1400: nas margens ao lado da vitrine. Enfeite puro: absolute,
  aria-hidden, sem toque, parado em reduced-motion.
- Imagens: `paginas/baloes/*.webp` (12, ~20–40 KB). Sobem pelo `_por_icone`
  do `publicar_bio.py`, nos DOIS diretórios do deploy, em `/baloes/`.
  Originais e recortes: `Desktop\inauguracao\` e `\recortados\`.
- Consertos do PC: 4:3 de celular baixo pegava notebook (foto 708 px → 354);
  word-spacing da legenda com teto de 6 px (chegava a 65 px); chips
  `safe center` ≥1024; busca digitando exemplos no placeholder (para no foco,
  reduced-motion e SSR).
- ⛔ **PUBLICAÇÃO NÃO CONFIRMADA no /clear (01:47).** O vigia pegou a
  mudança às 01:10 (python PID 9672, `publicar_bio.py --subir`) e às 01:47
  ainda estava na etapa `wrangler pages deploy` — a anterior levou ~10 min,
  esta passou de 35. **PRIMEIRA COISA da próxima sessão:** conferir no ar.
  Prova: `curl` na raiz achando `inaug_laranja`, e
  `/baloes/inaug_laranja.webp` respondendo `image/webp` (não `text/html`).
  Se não estiver: ler `estado/publicar_ao_mudar.log` e ver se o deploy
  travou (processo node do wrangler parado) antes de republicar à mão —
  e respeitar a trava (uma publicação por vez).
- Testes do site: 17/19 verdes. Os 2 vermelhos são ANTERIORES a esta mudança:
  `teste_legenda_uma_linha` (exige 12,5 px; código usa 11 desde 22/09) e
  `teste_categoria_externa` (campo `subiu` a mais no cartão). Não consertados.

⛔ **3 commits LOCAIS NÃO EMPURRADOS** (`95e7aed`, `db2e9ff` e o deste
handoff). O push foi recusado: o radar da nuvem empurrou `a43629f` antes, e a
árvore tem mudanças de estado das tarefas agendadas, então não rebaseei no
meio da publicação do vigia. Próxima sessão: esperar o vigia terminar,
`git stash -u` → `git pull --rebase` → `git stash pop` → `git push`.
(`c148b88`, o dos balões, JÁ está no GitHub.)

## 1b. Backup e documentação (commit `db2e9ff`)

- `publicar_ao_mudar_agendado.ps1`: depois de TODA publicação conferida roda
  `ferramentas/backup_do_ar.py` → sobrescreve `site_no_ar/` (uma cópia só,
  ~4 MB, NÃO versionada a cada vez — o Bryan pediu para não acumular). Log:
  "backup do ar atualizado" ou "BACKUP FALHOU".
- `backup_do_ar.py` agora baixa os 12 balões e reprova imagem que volta como
  `text/html` (o Pages dá 200 com HTML para caminho inexistente).
  ⚠️ Ainda não rodou de verdade — a 1ª execução é na próxima publicação OK.
- **`Documents\SITE_ACHADINHO_TOTAL_LEIA_PRIMEIRO.md`**: conta Cloudflare
  (**bryanaw21212@gmail.com**, plano Free, medido pela API), projetos Pages e
  domínios, como publica, backup, troca de PC, decisões em vigor.
- ⭐ Ordem permanente: toda menção a **mudar de computador** abre com o aviso
  de copiar `clip_engine` INTEIRO com o `.env` (está na memória).

## 1c. Conversas sem ação

- Armazenamento com API barato: recomendei **Cloudflare R2** (sem taxa de
  download, mesma conta) para o que o site/vídeos servem, **Backblaze B2**
  para backup grande. Preços de memória — não conferidos. Nada criado.
- Mentores de vendas/tráfego: lista entregue no chat (Savannah Sanchez,
  Hormozi, Pedro Sobral `@Pedro.Sobral`, Natanael Oliveira...). Destilação
  não iniciada; lembrar a regra de um canal por vez, sem cookie.

## 2. PENDENTE — balões subindo para os vídeos do TikTok

Pedido do Bryan (24/09): "máscara" de balões sem fundo, subindo na tela, para
entrar em determinado momento dos vídeos.

⏳ **O Bryan está preparando as imagens e vai mandar: QUANTOS balões, QUAIS e
EM QUE MOMENTO (horário) do vídeo entram.** Não comece sem essa lista.

Plano combinado (ainda não feito):
- Sem IA de vídeo (o Kling deformou os balões): movimento por código a partir
  dos recortes — cada balão com posição, velocidade, atraso e balanço
  próprios; menores mais lentos (profundidade). 1080×1920, 3–4 s.
- Entrega em dois formatos: MP4 com fundo verde chapado (CapCut → Recorte →
  Chroma) e `.mov` com transparência de verdade (CapCut PC, Premiere). O editor
  do próprio TikTok não aceita transparência.
- Renderizar NA NUVEM (máquina local não processa nada).
