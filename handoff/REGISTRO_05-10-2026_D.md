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
