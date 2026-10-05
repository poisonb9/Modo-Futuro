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
