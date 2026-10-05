# BLACK FRIDAY DE VERDADE — 27/11/2026 (plano mestre)

> Dono (05/10): "vamos fazer black friday de verdade, acompanhar os produtos, com maestria, com tudo o que temos, balões novos".
> Base: acervo marketing-e-oferta (54 fichas de BF + 112 de urgência/escassez/prova) + nossos ativos medidos hoje.

## O que já temos (medido 05/10)
| ativo | número |
|---|---|
| produtos com preço acompanhado | **~128 mil ids** desde 12/09 (`estado/precos_vistos.jsonl`), ~75 dias de histórico na BF |
| catálogo da busca | 69.734 produtos, 17 lojas |
| cupons | 112 ativos, atualizados **de hora em hora** (`cupons.yml`) |
| alerta por produto | bot do Telegram `alerta_<id>` + e-mail "me avise" (já existem nos cartões) |
| busca "não achou? eu rastreio" | e-mail → `engine/buscas_site.py` |
| vídeo de oferta automático | `ferramentas/video_oferta.py` (com "Comenta QUERO") |
| medição | PostHog (busca → clique → loja) + Supabase |
| balões | gerador grátis (Cloudflare flux) — **6 balões BF preto+ouro prontos** (`paginas/baloes/bf_*.webp`) |
| lembretes | `lembretes.yml` → Telegram do dono |

## A ideia central: o "Detector de Black Fraude"
Para cada produto, o veredito vem do histórico, não da loja:
- 🟢 **BF DE VERDADE** — menor preço dos últimos 60 dias (e abaixo da referência de outubro).
- 🟡 **IGUAL AO DE SEMPRE** — "desconto" que já existia em outubro.
- 🔴 **MAQUIADA** — subiu ≥15% nos 30 dias antes e "caiu" de volta.
Acervo: prova social e razão concreta da urgência convencem mais que urgência falsa ("remover urgência falsa da copy").
A nossa urgência é REAL: o histórico mostra quando o preço volta a subir.

## Fases (acervo: pré / BF / pós, objetivos distintos)
### Fase 0 — agora → 26/10 (construção)
1. `engine/veredito_bf.py`: calcula 🟢🟡🔴 por produto com a série (ref. = mediana de 01–25/10). Testar já em quedas de hoje.
2. Selo do veredito nos cartões da loja (só aparece em novembro; em outubro, testar escondido com `?bf=1`).
3. Balões BF no varal da loja e na `/blackfriday` (trocam automaticamente em 01/11, voltam em 01/12).
4. Ensaio geral no **11.11** (AliExpress).

### Fase 1 — 01/11 → 20/11: captura (lista quente)
5. `/blackfriday`: contagem regressiva real + **"Minha lista da Black Friday"**: a pessoa marca produtos (♥) e recebe
   no Telegram/e-mail **só se cair de verdade (🟢)**. Reaproveita o alerta por produto que já existe.
6. Conteúdo diário nos canais de oferta: **"Já subiu antes da Black Friday"** (🔴 com print do gráfico) — conteúdo que
   ninguém mais tem, gerado sozinho pelo `video_oferta.py`.
7. Banner no topo do site com a data (acervo: top banner com prazo até meia-noite).

### Fase 2 — 21/11 → 27/11: a semana
8. `/blackfriday` vira vitrine **só de 🟢**, por categoria, + cupons (hora em hora), re-checada de hora em hora.
9. Telegram/canais: "top 10 quedas reais do dia" 2x/dia. E-mail 1x/dia para a lista (**só com OK do dono**).
10. Desconto já no link (acervo: sem exigir código converte mais) — priorizar cupons sem código / link com desconto.

### Fase 3 — 28/11 → 12/12: Cyber Monday, 12.12, Natal
11. Kabum/tecnologia na Cyber Monday; vitrine de presentes; relatório PostHog para 2027.

## Marcos no calendário (lembretes no Telegram)
27/10 congelar referência + `/blackfriday` pronta · 01/11 abrir lista · 11/11 ensaio · 21/11 vitrine · 27/11 BF · 30/11 Cyber.

## Depende de / riscos
- Shopee sem resposta (PENDENCIAS). E-mail só com OK. WhatsApp bloqueado pela API.
- Série grava só MUDANÇA de preço: "menor em 60 dias" precisa saber que o produto foi VISTO no período, não só que mudou.
  Conferir cobertura antes de exibir selo (produto sem leitura recente → sem selo, nunca selo inventado).
