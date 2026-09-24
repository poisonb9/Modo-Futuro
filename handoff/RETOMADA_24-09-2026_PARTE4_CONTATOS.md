# RETOMADA — 24/09/2026, parte 4 (e-mail Brevo, captação de contato, bot, balões por bloco)

Anteriores do dia: `RETOMADA_24-09-2026_BALOES.md`, `_PARTE2.md`, `_PARTE3.md`.
Continuam ABERTOS de antes: 2 bugs da barra de abas (`RETOMADA_23-09-2026_PARTE3.md`),
2 testes vermelhos antigos (`teste_categoria_externa`, `teste_legenda_uma_linha`).

## 0. ⛔ PRIMEIRA COISA — conferir no ar

Às 11:10 foi disparada a publicação de `591487b` (arte do e-mail + publicador
subindo `.png`). Às 11:14 ela ainda rodava. Prova:
```
curl -s -o /dev/null -w '%{content_type}' https://achadinhototal.com.br/baloes/email_inauguracao.png   # image/png
curl -s https://achadinhototal.com.br/ | grep -c balao-bloco      # >=1 (já estava no ar às 10:40)
```
Se falhar: `estado/publicar_ao_mudar.log`; o motivo do detector de vazamento só
aparece rodando `python -X utf8 paginas/publicar_bio.py` SEM `--subir`.
Depois de a arte estar no ar: mandar o TESTE do e-mail de inauguração
(`python ferramentas/email_inauguracao.py --teste bryanarchives@gmail.com`) —
o Bryan JÁ AUTORIZOU testes para esse endereço.

## 1. Feito nesta parte (commits `7f38862` → `591487b`)

- **Balões por bloco no PC (≥1440)**: substituem os 2 fixos. Script
  `baloesPorBloco` espalha um balão a cada 1,4 tela da grade (#grade não tem
  blocos no DOM), **lado alternado** (só o 1º sorteado), altura sorteada com
  folga que nunca deixa 2 visíveis juntos (vão ≥ 1 tela + 220 px — medido:
  1.341–1.445 px com tela de 1.000), tipos em ciclo `inaug_laranja`,
  `inaug_porcento`, `inaug_estrela`. Sobem com `animation-timeline: view()`,
  aparecem em 5% e somem em 95% da passagem; deriva/balanço premium pelo relógio.
  Margem medida no JS (a grade tem **944 px**, não 1180). Ferramenta:
  `ferramentas/baloes/baloes_por_bloco.py`.
  ⏳ Quando o Bryan mandar a CAIXA DE ENCOMENDA e o EMOJI 😍 (prompts no chat
  de 24/09), entram em `BALOES_BLOCO`.
- **Preço do topo (hero) balança por caractere**: `fecharPreco` chama
  `window.__partirPreco` (o preço entra inteiro; só o nome é digitado).
- **"Comprar agora" flutua** (commit anterior, já no ar).
- **E-mail (Brevo) configurado de ponta a ponta:**
  - conta "Achadinho Total", plano free 300/dia;
  - domínio `achadinhototal.com.br` **autenticado e com marca** (subdomínio `em`);
  - DNS na Cloudflare: TXT `brevo-code`, CNAME `brevo1._domainkey`,
    `brevo2._domainkey`, `em`, `r.em`, `img.em` (DNS only); **SPF editado**
    de `v=spf1 -all` para `v=spf1 include:spf.brevo.com ~all`; **DMARC editado**
    de `p=reject` para `p=none; rua=mailto:rua@dmarc.brevo.com` (endurecer depois);
  - remetente `ofertas@achadinhototal.com.br` ativo;
  - `BREVO_API_KEY` no `.env` (o Bryan colou no chat — sugerido trocar a chave
    depois); bloqueio de IP para chaves API DESATIVADO (a nuvem muda de IP);
  - teste enviado 11:02 para bryanarchives@gmail.com (201). **Não confirmado
    onde caiu** (caixa/promoções/spam) — perguntar e pedir "Mostrar original"
    (SPF/DKIM/DMARC PASS).
  - Pendente: MX `.` (null MX) — domínio não recebe e-mail. Ligar **Email
    Routing** da Cloudflare (`ofertas@` → Gmail do Bryan).
- **E-mail de inauguração**: `ferramentas/email_inauguracao.py` (prévia em
  `_privado/email_inauguracao.html`). Arte `paginas/baloes/email_inauguracao.png`
  (1200×450, varal arqueado + brasão + balões). Top 3 quedas do dia com foto
  que passa em `foto_julga.serve_de_capa` (a Luz LED da colagem foi barrada).
  UTM `utm_source=email&utm_medium=inauguracao`. ⛔ Envio para LISTA não existe
  ainda (não há lista).
- **Publicador sobe `.png` de `/baloes/`** (antes só `.webp`).
- **`_privado/` no .gitignore** — contato de pessoa nunca no repositório (LGPD).

## 2. PENDENTE — captação de contato (aprovado pelo Bryan: itens 1 e 2)

**Com o Bryan:**
1. Criar o bot no @BotFather: nome `Achadinho Total`, username
   `AchadinhoTotalBot` (ou variações). Colar no `.env`:
   `TELEGRAM_BOT_ALERTA=` e `TELEGRAM_BOT_ALERTA_USERNAME=`. Acabamento:
   `/setuserpic` (logo), `/setdescription`, `/setabouttext`, `/setcommands`
   (start, alertas, contato, parar) — textos no chat de 24/09.
   Motivo: hoje o "avise-me" usa `@bryan_fxv_fila_bot` (bot da operação, nome
   do dono exposto, briga de getUpdates com `bot_telegram.py`).

**Comigo (5, 6, 7 não dependem do token — começar por eles):**
5. Tabela `contato` no Supabase (`supabase/10_contato.sql`, rodar com
   `python supabase/rodar_sql.py`): e-mail, telefone, origem (site/bot),
   produto do alerta, consentimento_em, saiu_em. RLS: anon só INSERT (padrão
   de `07_busca.sql`). Cópia local: script que baixa para
   `_privado/contatos.jsonl` (chave `SUPABASE_PAT`), rodado pela tarefa diária.
6. Site: toque no "avise-me" abre, dentro do cartão, "Telegram · 1 toque" +
   campo de e-mail + caixa de consentimento (desenho aprovado no chat).
7. `paginas/privacidade.html`: o que guardamos, para quê, como sair.
2–4. Com o token: secret na nuvem, trocar o @ no site; no bot (engine/alertas.py,
   colhe DE HORA EM HORA — não é tempo real) oferecer `request_contact` e
   "informar e-mail" após o alerta; comandos /alertas /contato /parar;
   gravar em Supabase. Depois: alertas também por e-mail via Brevo.

## 3. Outras pendências com o Bryan

- Caixa de encomenda + emoji 😍 (balões exclusivos da rolagem).
- Balões para vídeos do TikTok (lista ainda não veio).
- Black Friday: 4 balões guardados (memória `modofuturo-black-friday-baloes-campanha`).
- Ele ainda não disse o que achou de: galeria do PC, estrelas do celular,
  preços vivos, avise-me novo, balões por bloco.

## 4. Armadilhas desta parte

- Brevo: bloqueio de IP liga sozinho para chaves API → 401 "unrecognised IP";
  desativar em Segurança → IPs autorizados. A API da Cloudflare do Brevo recusa
  User-Agent padrão do urllib (erro 1010): mandar `user-agent`.
- DNS antigo do domínio tinha SPF `-all` + DMARC `reject` (proteção de domínio
  sem e-mail) — tinham de ser EDITADOS, não duplicados.
- Consultar DNS público: `curl "https://cloudflare-dns.com/dns-query?name=X&type=TXT" -H "accept: application/dns-json"`.


## 5. ATUALIZAÇÃO 12:05 UTC (depois do 1º handoff da parte 4)

**Estado no fechamento:** commit `3f61372` enviado e publicação disparada às
12:01 — NÃO CONFIRMADA. Prova: `curl -s https://achadinhototal.com.br/ | grep -c "var minimo = innerHeight + 240"` ≥ 1.

Feito:
- **Convite no celular** (`ce34964`, NO AR 11:41): caixa 46 px mais estreita de
  cada lado, um CORAÇÃO de cada lado (`inaug_coracao_p.webp`, 34 px), texto
  enxuto: "As quedas de preço no seu celular" + "Cada queda boa que eu encontro
  cai direto no seu Telegram."; botão em 1 linha (12,5 px).
- **Balões por bloco — conserto** (`3f61372`): MEDIDO no ar, a grade tem só 3
  fileiras (1.727 px, topo em ~1.261) numa página de ~3.520 → só cabia 1
  balão. Agora o trecho vai do topo da grade até o fim da página (−380 px de
  rodapé), vão mínimo = 1 tela + 240 px, sobra dividida por igual, sorteio só
  dentro da sobra. Prévia 1920×1000: 2 balões (1.695 e 3.162, lados alternados).
- **E-mail de inauguração** (`ferramentas/email_inauguracao.py`):
  - caixas dos 3 produtos com a MESMA altura no celular (borda na célula,
    preço/queda `nowrap`, nome ≤ 40 chars) — medido 225 px as três;
  - citação assinada **"— Fundador do Achadinho Total"** (o Bryan escolheu; NÃO
    usar o nome dele);
  - **produto linka DIRETO ao link de afiliado** (ordem permanente, memória
    `modofuturo-email-link-direto-afiliado`); capa e botão levam ao site com UTM.
- **Brevo segurou envios**: de 08:36 a ~08:50 (Brasília) os envios ficaram só em
  "requests" — era aviso de IP desta VPS no painel do Brevo; o Bryan liberou.
  Enviados para o Lucas (lucasmarianocomunicacao@gmail.com) sem querer: até
  3–4 cópias de teste (o "pro Lucas não" chegou depois do envio). ⛔ Regra:
  antes de QUALQUER envio, dizer para quem vai e esperar confirmação.
- Último teste: 11:52 UTC só para bryanarchives@gmail.com, assinatura Fundador.

Pendente (novo):
- **Foto do remetente no Gmail**: criar conta Google com
  `ofertas@achadinhototal.com.br` e pôr a imagem do Bryan (ele tem a imagem;
  conferir recorte em círculo de 40 px). EXIGE antes o **Email Routing** da
  Cloudflare (ofertas@ → Gmail), porque o domínio tem MX nulo. BIMI descartado
  (VMC ~US$ 1.000/ano + marca registrada).
- Perguntar ao Bryan se os e-mails de teste chegaram na caixa principal, em
  Promoções ou no Spam, e pedir "Mostrar original" (SPF/DKIM/DMARC).
