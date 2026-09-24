# RETOMADA — 24/09/2026, parte 5 (balões, capa, card do WhatsApp, marca, bot)

Anterior: `RETOMADA_24-09-2026_PARTE4_CONTATOS.md` (a seção 2 dele — captação de
contato — continua sendo o próximo trabalho grande).

## 0. ⛔ PRIMEIRA COISA

0. ⛔ ORDEM DO DONO (fim da parte 5): **antes de publicar QUALQUER coisa pelo
   bot/canal do Telegram, rever com ele o PADRÃO DAS PUBLICAÇÕES** (formato da
   mensagem, foto, preço, link, frequência). Nada vai ao Telegram antes disso.
   ⚠️ A troca do link do avise-me para o bot novo entra sozinha na próxima
   publicação automática do site (o publicador lê o `.env`); isso NÃO posta
   nada no Telegram — só muda para onde o botão leva.

1. Publicar e conferir o **bot novo no "avise-me"**: `.env` já tem
   `TELEGRAM_BOT_ALERTA` + `TELEGRAM_BOT_ALERTA_USERNAME=AchadinhoTotalBot`, e o
   secret `TELEGRAM_BOT_ALERTA` foi gravado no GitHub (23:36 UTC). A próxima
   publicação troca o link do avise-me. Prova:
   `curl -s https://achadinhototal.com.br/motor.js | grep -o 'BOT_ALERTA = "[^"]*"'` → `AchadinhoTotalBot`.
   Depois: conferir que `precos.yml` colhe no bot novo (engine/alertas.py).
2. ⚠️ O dono colou o token do bot NO CHAT — sugerido `/revoke` no BotFather e
   trocar no `.env` e no secret (`gh secret set TELEGRAM_BOT_ALERTA`).
3. O site NÃO mostra o @ do bot (só no link). Dono pediu: se algum texto citar
   o bot, escrever "Achadinho Total", nunca "@AchadinhoTotalBot".
   ⚠️ `@AchadinhoTotal` é o CANAL (t.me/achadinhototal), não o bot.

## 1. Feito nesta parte (tudo no ar e conferido)

- **Balões da rolagem (PC ≥1440)**: FIXOS na margem, um aceso por vez pelo
  meio da tela, apagam fora da grade. Ordem: `inaug_seta_lado` (sempre à
  ESQUERDA, aponta p/ produtos) → `inaug_apaixonado` → `inaug_sacola_dourada`.
  Topo (hero): laranja virou `inaug_presente`. Recorte de fundo branco:
  `ferramentas/baloes/recorte_branco.py` (preserva a fita branca).
  Originais renomeados em `Desktop\inauguracao\` (inaug_*.png; seta_baixo guardada p/ campanha).
- **Bio**: laranja → presente (`contra_capa.html`).
- **Estrela sem verde** (`.nota.em-fogo` saiu).
- **Capa**: rodízio de 3 h (`CAPA_RODIZIO_S`, janela no marcador do vigia
  `publicar_ao_mudar_agendado.ps1`) entre régua da capa + foguinho com foto
  boa; os outros do rodízio abrem a grade. HOJE ninguém passa no piso da foto
  (4 foguinhos reprovados) → reserva. **Capa fixada à mão**: `estado/capa_fixa.json`
  (SSD Netac até 2026-09-25T15:14 UTC; arquivo é git-ignored, só local).
- **Card do WhatsApp**: `og:image` = `og_logo.png` (só a logo no branco,
  padrão Apple/Microsoft — `ferramentas/og_logo.py`). Guardados p/ campanha:
  `og_oferta.py` (produto no pedestal + preço na etiqueta), `og_buque_texto.py`,
  `fitas_buque.py`, `og_inauguracao.py`; cenas em `Desktop\inauguracao\og_*`.
- **Marca**: "Eu garimpo" → **"Eu procuro. Você paga menos."** em todo lugar
  (topo, bios, e-mail, og). og:description pela dor do cliente. Quem Somos:
  "Busca diária e constante". meta description na voz "eu".
- **Ícone do iPhone** com fundo BRANCO (`gerar_icones.py`, href `?v=branco`;
  quem já salvou precisa apagar e re-adicionar).
- **Convite (Telegram)**: borda dourada em gradiente, sombra em camadas, selo
  "grátis · no Telegram", anel dourado no botão.
- **E-mail**: Email Routing Cloudflare `ofertas@` → `achados.contato01@gmail.com`
  (dono não quer o pessoal); SPF único brevo+cloudflare; conta Google do
  ofertas@ criada com foto. Teste de inauguração entregue a bryanarchives (11:38 BRT).

## 2. Pendente

- **Captação de contato** (PARTE4 §2): `supabase/10_contato.sql` ESCRITO e NÃO
  rodado; script `_privado/contatos.jsonl`; avise-me com e-mail + consentimento;
  revisar `paginas/privacidade.html`. Mostrar ao dono antes de publicar.
- Bot: comandos /alertas /contato /parar e `request_contact` em engine/alertas.py.
- Balão novo p/ vídeos do TikTok (lista não veio); Black Friday (memória).
- `stash@{0}` redundante no clip_engine (conferido: nada perdido) — apagar só se o dono quiser.

## 3. Armadilhas desta parte

- Comentário com o NOME do dono no JS → detector de vazamento barra a publicação.
- `git stash -u` falha com `site_no_ar/baloes/` não rastreado → usar
  `git pull --rebase --autostash`.
- O painel do navegador do app não pinta (screenshot branco, rAF parado):
  testar lógica com `dispatchEvent(new Event('scroll'))` e JS, não com print.
- Prévia de link: WhatsApp guarda por URL — imagem nova = nome de arquivo novo.
- Brevo: envio p/ endereço que deu hard bounce fica BLOQUEADO → `DELETE /v3/smtp/blockedContacts/{email}`.
- ⛔ Nunca enviar e-mail sem dizer para quem e esperar confirmação.
