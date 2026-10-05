# REGISTRO 05/10/2026 (D) — o que foi feito DE FATO e por quê

> Diário de correções desta sessão (depois do handoff C). Cada item: sintoma → causa → correção → como conferir.
> Objetivo: não repetir os mesmos problemas.

## 1. Sem Anestesia 10 h sem postar (6 clipes prontos barrados)
- **Sintoma:** corte de 03:46 gerou 6 clipes; agendador disse "0 ainda não agendado(s)".
- **Causa:** `_chave_texto` em `agendar_buffer.py` cortava tudo depois do `#` (achando que era hashtag).
  Título de série "Protocolo #47: ..." virava `protocolo` = igual a todo Protocolo já postado → "já publicado".
  Afetava toda série com `#N` (Protocolo, Goggins sem filtro, Seu cérebro desiste antes).
- **Correção:** só sai hashtag de verdade (`#palavra`); `#47` fica. Commit "agendador: '#47' de serie...".
- **Efeito colateral tratado:** `estado/publicados.json` tinha chaves no formato velho (todos os Protocolo colapsados em `protocolo`).
  Refeito o histórico inteiro do Buffer: `desempenho.yml` ganhou entrada `paginas` (rodado com 60) e `historico.py` lê `HIST_PAGINAS`.
- **Resultado:** 10 clipes na fila (1º às 06:54 BRT), 41 esperando vaga.
- **Pendência:** numeração repetida na fila ("Protocolo #14" duas vezes) — a renumeração do repor_fila não olha a fila.

## 2. Diagnóstico do agendador ficou visível
- `agendar_buffer.py` agora imprime `recusados por motivo: {...}` (quarentena, trecho_usado, texto_publicado, etc.).
- Novo workflow `agendar_simular.yml` (canal + secret) roda `--simular` na nuvem: **use isto primeiro quando um canal parar**.

## 3. Make e Chef parados (~1 dia)
- **Make:** os clipes livres foram recusados porque o título não batia com a fala (recusa correta). Radar das 06:28 não aprovou nenhum vídeo (chaves Gemini esgotadas no meio da avaliação). Tinha 1 na fila (09:48).
- **Gargalo geral:** `vigia_raw.py` só deixava **1 corte por vez** (~2,5 h cada; ~17 min de dublagem por clipe) → 23 brutos esperando.
  **Correção (OK do dono):** `MAX_SIMULTANEOS = 3`; `corte_em_andamento()` agora conta runs. Continua 1 disparo por passada (10 min).
- **Chef sem reposição:** `abastecer_loop.estoque_drive()` contava como estoque TODO .mp4 da pasta, inclusive brutos já cortados
  (9 do Chef). Ficava acima do piso 3 e nunca buscava receita nova.
  **Correção:** ignora ids que estão em `estado/raw_vistos.json`. Estoque medido depois: Chef 0, Make 0 → reposição volta a rodar.

## 4. Site (achadinhototal.com.br)
- **PostHog** (UE, sem cookie, `persistence: memory`) em todas as páginas via `_com_posthog` em `paginas/publicar_bio.py`
  (entra no `_carimbar`, só no `--subir`). Conferido no ar: `/` e `/parceiros/` com `posthog.init` (`/todos/` redireciona para `/`).
- **Menu Loja ilegível no PC:** `.opcoes` era vidro a 26% sem limite de altura. Agora no desktop: fundo branco, sombra, `max-height` com rolagem.
- **Mercado Livre vazio ao escolher a loja:** o chip padrão "Maiores quedas" filtrava; ML quase não tem queda → 0 achadinhos.
  Agora com LOJA escolhida o chip só ordena (mesma regra que já valia para a busca).

## 5. Armadilhas novas (não repetir)
- Rodar `publicar_bio.py` com saída em pipe no Windows quebra por cp1252: usar `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`.
- PostHog/carimbo só existem no `--subir`; a geração sem `--subir` não mostra o snippet (não é erro).
- Mudar a função de chave de dedup exige refazer `estado/publicados.json` (chaves gravadas no formato antigo).

## 6. Anotado para depois
- ManyChat (Instagram do achadinho já conectado): Claude monta pelo Chrome a automação QUERO → DM, **depois do TikTok redondo**.

## 7. Telegram do dono estava MUDO (achado em 05/10 ~07:15 BRT)
- **Sintoma:** log do corte: `Telegram falhou: 401 Unauthorized`.
- **Causa:** `TELEGRAM_BOT_TOKEN` (de 28/07) foi revogado. Vigia de postagem e avisos de corte não chegavam.
- **Correção:** secrets `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` agora = AchadinhoTotalBot + chat do dono. Testado: `telegram: 200`.
- **Aberto:** o `.env` local ainda tem o token morto (ver PENDENCIAS_ABERTAS).

## 8. Lembretes que não deixam esquecer
- `estado/calendario_promocoes.json` (forçado no git: `estado/` é ignorado) + `ferramentas/lembretes.py` + `lembretes.yml` (08:00 BRT).
- Datas: avisa 14/7/5/3/2/1/0 dias antes. Pendências: `handoff/PENDENCIAS_ABERTAS.md` toda segunda (ou `-f pendencias=1`). Testado: chegou.

## 9. PostHog ponta a ponta
- Eventos: `produto_clique` (produto, loja, origem), `busca` (termo, resultados), `telegram_clique`; `?eu=1` desliga (opt-out).
- Mesmo ponto que já gravava no Supabase (`anotarClique`, `anotarBusca`).

## 10. Cupons — fonte encontrada
- Awin `POST /publisher/{id}/promotions` (filtro joined/active/BR) devolve cupom + validade das NOSSAS lojas (testado: 50+, ex. Kabum STREAMER10).
- AliExpress: API de afiliado já integrada (`engine/aliexpress.py`) tem promoções; a conferir.

## 11. Página /cupons (pedido do dono)
- `engine/cupons.py`: Awin promotions → `/cupons/` (109 ativos, 53 com código, 17 lojas). Filtro por loja, botão "copiar" código,
  "vence hoje/amanhã" em vermelho, link `urlTracking` (nosso id). Sem API → usa `estado/cupons.json` (último bom).
- Gerada em toda publicação (`_por_privacidade` em `publicar_bio.py`), com PostHog: `cupom_copiado`, `cupom_clique`, `cupom_filtro`.
- Aba "Cupons" na barra de baixo da loja.
- Próximo: cupons do AliExpress (API já integrada) e card "cupom do dia" no Telegram.

## 12. Resposta a "automatizar DM/interação no TikTok"
- Acervo: F62331 — **evitar bots de mensagem no TikTok** (limite de contatos, risco de bloqueio). Caminho oficial: **ManyChat × TikTok**
  (o painel do dono já mostra o banner "TikTok × Manychat"): comentário com palavra-chave → DM automática, pela API oficial.
- Acervo F27194: responder comentário com VÍDEO (função "Responder com vídeo") converte — pode virar formato semi-automático.

## 13. Cupons de hora em hora + AliExpress (no ar, conferido)
- `cupons.yml` (GitHub, minuto 17 de toda hora) grava `estado/cupons.json`; /cupons lê o JSON do repo público ao abrir
  (raw.githubusercontent, CORS `*` conferido). Dados embutidos = fallback. Custo zero (APIs grátis, sem IA).
- AliExpress: `hotproduct.query` → `promo_code_info` (cupom de loja). Os cupons gerais do Ali (BRCD3..8) vêm pelo Awin.
- Armadilha: API do Ali estoura o timeout de 20 s às vezes → `engine/cupons.py` sobe para 90 s.
- Conferido no ar: 111 cupons embutidos, PostHog presente. Navegador interno não abre o domínio (recusado) — conferido por curl.

## 14. Black Friday
- Plano mestre: handoff/CAMPANHA_BLACK_FRIDAY_2026.md ("Detector de Black Fraude": 🟢 real / 🟡 igual / 🔴 maquiada).
- 6 balões preto+ouro gerados (`paginas/baloes/bf_*.webp`, Cloudflare flux grátis); prévia em handoff/baloes_bf_prototipo.jpg.

## 15. Preço do Mercado Livre diferente no site e na loja (print do dono: JBL 174,90 × 188,53)
- **Causa:** `mais_vendidos` (vitrine) e a busca pegavam o preço de um vendedor e linkavam a FICHA `/p/{id}`, que abre na buy box
  (loja oficial, mais cara). O conserto `link_do_anuncio` de 18/09 só valia para livros.
- **Correção:** `vencedor_confiavel()` = menor preço novo, ignorando anúncio isolado (>40% abaixo do 2º — régua do dono; testado 20%,
  e mediana cortava demais) + link do ANÚNCIO (`produto.mercadolivre.com.br/MLB-<item>`). Vitrine refeita: 423 itens, 0 com `/p/`.
- **Resta:** vitrine do ML é 1x/dia — preço pode mudar no meio do dia. Avaliar 2–3x/dia.

## 16. /cupons premium
- HTML separado em `engine/cupons_pagina.html` (o gerador só injeta os dados). Herói preto/ouro, cupom-ticket com picote,
  título longo recolhido ("ver regras completas"), código quebra linha (bug do "copiar" vazando), filtros fixos no topo,
  balões BF no herói + balões que aparecem/somem na rolagem em telas ≥1300 px (mesma mecânica da loja).

## 17. Mercado Livre na loja: hora em hora, prioridade, busca rápida, busca → loja
- `ml_vitrine.yml` de hora em hora (rodada ~4 min, sem 429) + `ml_vitrine.json`/`ml_busca.json` na lista do publicador automático (10 min).
- **Prioridade:** `promover_ofertas_ml` (publicar_bio) põe até 4 ofertas "muito boas" do ML no topo da 1ª página:
  queda REAL ≥15% (3+ dias de série) ou desconto da loja 25–60% (acima de 60% o "de" costuma ser inflado). Vitrine guarda `de_loja` (original_price).
- **Busca sem delay:** antes as lojas baixavam UMA POR VEZ com tela de espera. Agora: com termo, todas em paralelo, ML na frente e
  primeiro na lista; pré-carrega ao TOCAR na busca e o ML na ociosidade; sem cartão repetido.
- **Busca → loja:** `ferramentas/buscas_para_loja.py`: `--termos` (VPS, SUPABASE_PAT) grava `estado/termos_buscados.json`;
  `--ml` (nuvem, no ml_vitrine.yml) busca no ML e grava `estado/ml_busca.json`, que entra na loja 14 dias. Testado: "whey" → 6 produtos.
- **Armadilha:** a API do ML NÃO responde da VPS (timeout) — tudo de ML roda na nuvem.
- **Falta:** agendar `--termos` de hora em hora na VPS (tarefa do Windows).

## 18. Top 10 do Mercado Livre por nicho + bios
- `engine/top10.py` + `engine/top10_pagina.html` → `/top10/` e `/top10/<academia|eletronicos|beleza|saude|casa|cozinha|infantil|pet>/`.
  Ordem = mais vendidos do próprio ML (`/highlights`), sem nome repetido, preço com data/hora, selo "⚡ Oferta de hoje",
  "por que está aqui", JSON-LD ItemList (Google), canonical, PostHog `top10_clique`. Gerado em toda publicação.
- Bios: grupo "Os mais vendidos do Mercado Livre, com o preço de hoje" (3º grupo) em 8 canais, cada um no seu nicho.
  Armadilha: inserir por texto quebrou (grupo sem vírgula, canal com 1 grupo) → inserção por contagem de colchetes.
- **Cookie de 24 h:** conta a partir do CLIQUE; link não expira, nada a renovar. Por isso o selo "oferta de hoje" + aviso "compre hoje".

## 19. Selos (ChatGPT) e regra do remédio
- 4 selos do dono: originais em `midia/selos_originais/` (com LEIA.md), web em `paginas/baloes/selo_{oferta_de_hoje,compre_hoje,mais_vendido,bf_de_verdade}{,_p}.webp`.
  No Top 10: 1º lugar = "Mais vendido", demais = "Oferta de hoje", aviso = "Compre hoje". BF guardado para a campanha.
- Prompts dos selos: pílula preta (ou dourada) com borda dourada, texto exato, fundo transparente, 3:1.
- **Remédio fora da loja** (`engine/ml_vitrine.py`, `REMEDIO`): Bravecto/Simparic/NexGard/Defenza estavam na vitrine Pet. Suplemento continua.
- Top 10 sem cesta básica (papel higiênico abria "Beleza"; lava-roupas, papel toalha, lenço umedecido...).

## 20. Remédio sem competir + botão/pódio/moldura
- Dono revisou: remédio PODE ficar, mas não compete. `ml_vitrine` marca `remedio: True`; publicador põe no FIM do bloco ML;
  fora do Top 10, das ofertas no topo; na página (todos.html) sempre no fim, inclusive na busca.
- Botão de compra `.btn-ouro` em CÓDIGO (visual dos selos) no Top 10 e cupons — imagem como botão foi descartada
  (ilegível em tela pequena, sem texto para leitor de tela/Google, troca de texto exige arte nova).
  Celular: largura do cartão, quebra em 2 linhas (medido: 0 botões cortados em 375 px).
- Pódio 1/2/3 ouro/prata/bronze e moldura EM VOLTA da foto (nunca por cima — a foto é a do vendedor).

## 21. Botões: família + cor de cada loja (opção A do dono)
- Família de 9 botões (prévia: paginas/previa_botoes.html; imagens do ChatGPT em midia/botoes_originais + botoes_web).
- Loja principal (todos.html, `CTA_LOJA`): o CTA de cada cartão tem a COR DA LOJA e o nome ("Ver na Nike"):
  ML amarelo, Ali vermelho, Nike preto, Kabum laranja/azul, Drogal azul, Clovis vermelho-escuro, Oceane rosa,
  Soldiers verde/ouro, Lauri azul, Guess preto/vermelho, Stanley verde, Arno vermelho; fora do mapa = ouro da casa.
  Prévia comparando hoje × A × B: paginas/previa_botoes_lojas.html. Loja nova aprovada: acrescentar em `CTA_LOJA`.

## 22. Acervo — pipeline PARTE 1 (OK do dono 05/10 tarde; parte 2 quando a destilação inteira acabar)
- Destilação no momento: Russell 98/158; faltam Natanael 331, Hormozi 132, Ladeira 54, Jordan 54, Income 25, Ben Heath 14
  (~670 vídeos a ~34/h ≈ 20 h — o "~8 h" do handoff E estava errado). Russell rende pouco (vlog Funnel Hacker TV → 0 fichas).
- Etapa 6 feita: `maestros_da_ia/gerar_skill.py` (comando do SKILL.md) → 24.283 fichas (+2.672), 3.465 vídeos.
  Backup da skill anterior em %TEMP%/claude/skill_mkt_antes_20261005. A skill em ~/.claude/skills é link para skills_de_trabalho.
- Etapa 7 em andamento: `embutir_acervo.py --fonte marketing --modelo voyage-3.5 --aplicar --esperar-cota` (incremental: só as ~2.672 novas),
  log `ia mind/_embutir_voyage_marketing_20261005.log`. Depois: rerank-2.5 e aferir_busca.

## 23. Botões das lojas recebidos (ChatGPT)
- Guess, Nike, Stanley, Drogal, Lauri, Soldiers → `midia/botoes_originais/botao_ver_na_<loja>.png`, recorte alpha>60 em `midia/botoes_web/` (.png + .webp 600 px), LEIA.md atualizado.
  Faltam: Clovis, Oceane, Arno (prompt do Arno reenviado ao dono).
- Etapa 7 FEITA: 2.672 vetores novos em 16 s, conferência 24.283 × 24.283 OK.
- Etapa 8 (`medir_reranker.py --modelo rerank-2.5 --topn 250`): top-5 16 → 31 com rerank (+15); 1 pergunta não medida (fatia perdida por RemoteDisconnected).
- Etapa 9 (`aferir_busca.py --rotulo parte1_20261005`): 18/58 (31%).
  ⚠️ O banco de aferição só tem perguntas de LIVROS e MENTORES — nenhuma de marketing. A busca de marketing segue SEM aferição própria → pendência.

## 24. Cartão com queda e sem procedência (massageador do Ali, "caiu 30%")
- **Sintoma:** selo "caiu 30%" sem gráfico e sem "rastreando há N dias".
- **Causa:** 2 leituras (178,99 → 125,99). `grafico()` exige 3 pontos e a linha de idade só existe dentro do gráfico.
- **Correção:** `todos.html`: sem gráfico + queda ≥5% + 2 leituras → linha "rastreando há N dias · N leituras". Varredura: era o único caso.
- **Conferir:** prévia local mostrou "rastreando há 4 dias · 2 leituras". Vai ao ar na próxima publicação.

## 25. Destilação: Gemini flash + Nemotron, 3 vídeos juntos
- Dono pediu Nemotron junto com Gemini em paralelo. `destilar_canais_em_ordem_20260924.py`: `--gemini-em-dez 5 --videos-juntos 3`
  (backup `.antes_do_paralelo_20261005`). Escada Gemini = só flash 3.8→3.5. Reiniciado 17:12. Não há pipeline de destilação na nuvem (só PC).

## 26. +acervo unificado e aferição no assunto certo (não-trade)
- **Sintoma:** `+acervo` injetava as 4 SKILL.md (~18 KB); o Claude Code corta contexto de hook grande para uma prévia de 2 KB →
  só o maestros-da-ia era visto; marketing/CSS/Liquid Glass sumiam em silêncio.
- **Correção:** `~/.claude/hooks/trio_do_acervo.py` (backup `.antes_unificado_20261005`): `+acervo` agora entrega um bloco de 1,3 KB com a
  busca semântica UNIFICADA (`buscar_semantico.py --acervo marketing --acervo maestros --acervo css --acervo liquid_glass`, 190.431 fichas,
  Voyage 3.5 + rerank-2.5, ~35 s). `+livros` (trade) inalterado.
- **Aferição:** o banco só tinha trade. Novo par `acervo_geral` (4 índices) em `aferir_busca.py`; 30 perguntas M01–M30 parafraseadas,
  alvo literal de ficha real (marketing/maestros/css). `medir_reranker.py` ganhou `--par` (saída `rerank_rerank-2.5_n250_acervo_geral.json`).
- **Bug achado no aferidor:** `normalizar()` deixava espaço duplo onde havia pontuação → alvo que atravessasse vírgula/parêntese NUNCA casava
  (5 dos 30 deram 0). Corrigido (split/join). ⚠️ Notas antigas de trade podem ter sido SUBESTIMADAS por isso — remedir antes de comparar.

## 27. Balões de cupom na loja (pedido do dono) + botão Arno
- Imagens do ChatGPT: originais em `midia/baloes_cupom_originais/`; web em `paginas/baloes/cupom_{a,b,clique_aqui,ver_cupons}.webp` (recorte alpha>60).
- `todos.html`: PC (≥1100 px) = 2 conjuntos ao lado da linha viva (cupom grande + "clique aqui" pendurado na fita), flutuando,
  brilho dourado pulsando, selo vermelho "112 hoje" lido ao vivo do `estado/cupons.json` (raw GitHub). Celular/tablet = pílula
  "VER CUPONS" fixa acima da barra de abas, entra após 3 s, some ao rolar para baixo. PostHog `cupom_balao_clique` (origem).
  `prefers-reduced-motion` desliga animação. Backup: %TEMP%/claude/todos_antes_baloes_cupom.html.
- Conferido na prévia local: 1700 px (posição dos quadrados vermelhos do print) e 375 px (pílula sem cobrir a barra). Vai ao ar na próxima publicação.
- Botão Arno recebido → `botao_ver_na_arno` (originais + web). Faltam Clovis e Oceane.
- Dono: o da esquerda ficou melhor → os DOIS lados usam `cupom_a.webp`.

## 28. ⛔ Publicador automático "engoliu" o trabalho local (05/10 ~18:25)
- **Sintoma:** `todos.html` voltou à versão do commit (sumiram balões de cupom e o conserto do massageador); REGISTRO, radares, mídia nova também.
- **Causa:** `publicar_ao_mudar_agendado.ps1` faz `git stash -u` → `git pull --rebase` → `git stash pop`. O pop falhou (conflito com arquivo
  atualizado na nuvem, ex. `estado/cupons.json`) e TUDO ficou preso em `stash@{0}` em silêncio.
- **Correção:** `git stash apply stash@{0}` (sem apagar o stash) + `git checkout stash@{0} --` dos 3 arquivos que eu tinha mexido depois.
  Conferido: balões, linha "leituras" e itens 22–27 de volta. Stash mantido como segurança. Cópia em %TEMP%/claude/todos_com_baloes_cupom.html.
- **Pendente:** o publicador precisa AVISAR (Telegram) quando o pop falha, em vez de deixar o trabalho no stash.

## 29. Reranker medido no acervo NÃO-trade (30 perguntas M01–M30)
- Só embedding (Voyage 3.5): 17/30 no top-5 (57%). Com rerank-2.5 (top-250): **21/30 (70%)**, ganho +4. 1 URLError na rodada (M28/M29).
- Comparar só com esta mesma lista. Arquivo: `ia mind/_afericao/rerank_rerank-2.5_n250_acervo_geral.json`.

## 30. +livros no mesmo molde do +acervo
- `+livros` injetava a SKILL.md de trade (16 KB) → cortada em prévia de 2 KB. Agora: bloco de ~1,4 KB com a busca unificada nos 7 índices
  de trade (livros_estrategia/metodo/texto, mentores_estrategia/nao_fazer/visao, falas_mentores = 300.543 itens, rerank-2.5, ~50 s).
  Testado: "quando não entrar num rompimento" → regras de mentores com link do minuto. `/mentores-de-trade` continua funcionando.
  Tamanhos: +livros 1,4 KB · +acervo +livros 2,3 KB (ambos abaixo do corte).
- Dono: atalho de trade renomeado para `+trade` (`+livros` segue como apelido; os dois juntos entram uma vez só).

## 31. Site que vende — diagnóstico e plano (documento-mestre: handoff/PLANO_SITE_VENDAS_2026.md)
- Medido: 45 cliques/30 dias; sitemap com 2 endereços; vitrine 145/148 AliExpress. Plano de 6 frentes aprovado pelo dono.
- **Sitemap completo:** `publicar_bio.py` agora lista /, /cupons/, /top10/ + 8 nichos, /parceiros, /privacidade (11). `TOP10_NICHOS_MAPA`.
- **ML na vitrine:** `misturar_ml_na_vitrine()` — 8 mais vendidos do ML intercalados (topo 2.5, 4.5, …), máx. 2 por área
  (1ª versão trouxe 5 tênis de 8), sem remédio, sem nome repetido. Testado: tênis, whey, kit Wella, Galaxy A17, modeladora, microfone.

## 32. Lista VIP de cupons + /cupons/<loja>/ + aviso de cupom novo
- `engine/cupons_pagina.html`: título/descrição/canonical/og/BreadcrumbList por página; bloco VIP preto/ouro ("Receba os cupons da
  <loja> antes de todo mundo"): Telegram (`t.me/AchadinhoTotalBot?start=alerta_cupons-<slug>`, troca com o filtro) + e-mail
  (Supabase `contato`, origem `cupons`, produto `cupons:<slug>`), honeypot, consentimento; números do herói passam a ser da loja filtrada;
  rodapé "Cupons por loja" com links reais (rastreáveis pelo Google). `grupo()` junta "Aliexpress" (Awin) e "AliExpress" (Ali).
- `engine/cupons.py`: `lojas()`, `slug()`, `pagina_html(slug, bot)`. Página só para loja com cupom ATIVO (sem página vazia).
- `paginas/publicar_bio.py`: gera /cupons/<slug>/ e põe no sitemap (`_slugs_cupons()`).
- `engine/alertas.py`: `/start alerta_cupons-<slug>` com confirmação própria; `avisar_cupons()` manda DM do cupom novo para quem assinou
  a loja (ou "todas"); 1ª rodada só marca o que já existe (`estado/cupons_avisados.json`).
- **Achado:** `cupons.yml` (cron :17) nunca rodou por agendamento → JSON parado desde 10:43. Cupons agora no `precos.yml` (hora em hora).
- Conferido na prévia: Kabum/Arno em 1400 px e 375 px; link do Telegram correto; 35 cupons da Arno; 14 links internos.
- Balões de cupom subidos (top 300→180 px) para o "clique aqui" não cobrir o anúncio; /cupons e /top10 sem barra → 301 (Search Console).

## 33. Search Console + arrumação dos balões
- Search Console: propriedade de Domínio JÁ existia e verificada. /cupons/ testada ao vivo = disponível, indexação SOLICITADA
  (o 404 da 1ª tentativa foi o instante da publicação). Sitemap reenviado (`https://achadinhototal.com.br/sitemap.xml` — em propriedade
  Domínio precisa do endereço INTEIRO; "sitemap.xml" sozinho dá "endereço inválido"). No ar: 27 endereços.
- Balões (pedido do dono, "muito embolado"): saíram %, etiqueta (o "de cupom") e chapéu de chef; estrelas em destaque no alto
  (`.estrela-centro` top 18px, 124px, ao lado do "INAUGURAÇÃO"); cupons de desconto mantidos no lugar. Backup %TEMP%/claude/todos_antes_estrelas.html.

## 34. Balões premium no PC (dono: "ainda não gostei", pediu organizado/premium, pode tirar)
- Acervo (+acervo): página que converte = poucos elementos e o olho guiado até a oferta e o botão. Respiro e hierarquia.
- `todos.html`: no PC ficam SÓ 2 balões por lado, numa coluna no meio da margem, só ouro e vermelho, cores cruzadas:
  presente (ouro) / laço (vermelho) | boca (vermelho) / lupa (ouro). Saem do PC: sacola roxa, carrinho, A, $, MF (prata).
  Tela média (760–1399 px): 1 balão por lado (o 2º batia nos cupons). Celular inalterado. Estrelas no alto e cupons mantidos.
  Classe `.balao.pc`; regras com prefixo `.baloes` (as de 1400 px vinham depois no arquivo e ganhavam).
- Backup: %TEMP%/claude/todos_antes_baloes_premium.html. Conferido na prévia em 1912, 1100 e 375 px.
- Dono: "ficou vazio" → 3 por lado no PC (≥1400 px), em xadrez ouro/vermelho: presente/laço/sacola dourada | boca/lupa/coração
  (linhas de 235 px, a partir de top 30 px). Tela média segue com 1 por lado; celular inalterado.

## 35. SEO: as 6 frentes do "+acervo o que não estamos fazendo" (dono aprovou as 6)
- Acervo: site novo ranqueia com páginas de UMA busca de baixa concorrência e alta intenção, resposta direta 2–3 frases + tabela,
  palavra-chave no título/H1, sitemap + Search Console, links internos e de fora.
- **Código:** `engine/paginas_produto.py` (novo), `paginas/publicar_bio.py` (gera /p/ e /melhores/ em `montar_catalogo`,
  `pg` nos cartões, índice estático → /p/, sitemap com lastmod real, IndexNow pós-deploy, chave .txt), `paginas/todos.html`
  (título/descrição com palavras-chave, link "ver histórico de preço →" no cartão, rodapé com links), `ferramentas/relatorio_seo.py`
  + workflow `relatorio_seo.yml` (segunda 08:30).
- **Bug pego na prévia:** preço de hoje fora da série → "menor R$ 30,99" com hoje R$ 30,49. Corrigido: hoje entra na série.
- **Bug pego no teste:** ids do Ali são `int` na série e `str` no cartão → só 3 páginas. Normalizado para str → 141.
- 1ª geração: 141 /p/ + 11 listas /melhores/ (Eletrônicos, Academia, Casa, Cozinha, Beleza, Carro, Achadinhos). Teste do relatório: 27 URLs, 25/25 = 200.
- Pendente do dono: segredo GSC_CREDENCIAIS, Bing (importar do GSC), Pinterest. Passo a passo no PLANO seção 5.
