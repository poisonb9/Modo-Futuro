# Regras de operação do Achadinho Total — o que roda, quando, e como conferir

**Este é o arquivo que se abre quando a pergunta é "a gente não esquece de X?"**
Cada regra tem: quem executa (nuvem / máquina local / Bryan), quando, o comando, e como
saber se rodou. Decisões numéricas estão na seção 3 — mudar um número é mudar aqui e no
código citado. Atualizado em 18/09/2026.

## 1. O que roda sozinho (e como conferir)

| Rotina | Quando | Onde | Como conferir |
|---|---|---|---|
| **Garimpo** (Ali por canal, ML por termo, varredura, Awin catálogo + comissões, tendências ML, nomes curtos, sinais → Telegram) | diário 10:23 UTC | nuvem `garimpo.yml` | `gh run list --workflow=garimpo.yml`; commit "garimpo: precos vistos" |
| **Reconferência de preço** (Ali + ML: preço, vendedores, frete, termômetro) + **alertas** (avise-me: colher /start, avisar quedas, lembrar reposição) | 24×/dia | nuvem `precos.yml` | commit "precos: instantaneo do catalogo"; `estado/alertas*.json` |
| **Velocidade** (Lighthouse mobile, piso 70) | segundas 12:37 UTC | nuvem `velocidade.yml` | run vermelho = abaixo do piso; artefato `lighthouse` com o JSON |
| **Publicação diária** (pull → nomes → buscas do site `--rotina --enviar` → publica e confere 26 endereços) | 11:30 UTC | máquina local, tarefa `AchadinhoTotal_Publicar_Diario` (S4U) | `estado/publicar_diario.log` ⚠️ **trava no wrangler em S4U desde 16/09** — publicar à mão: `python -X utf8 paginas/publicar_bio.py --subir` |
| Vitrine (posts do canal), fila, desempenho (views) | ver `.github/workflows/` | nuvem | ⚠️ views leem 0 do Buffer desde 29/08 (AUDITORIA §2.3) |

## 2. O que só o Bryan faz (e a cadência)

| Tarefa | Cadência | Onde |
|---|---|---|
| Reclame Aqui: nota das 10 lojas → me passar → `estado/reputacao_lojas.json` | mensal (validade 60 dias na régua) | navegador dele (o site bloqueia leitura automática) |
| Search Console: sitemap `sitemap.xml` enviado; olhar "Páginas" indexadas | 1× agora; depois mensal | search.google.com/search-console |
| Cloudflare: DNS (CNAME dos canais), Redirect Rule "WWW to root", secrets — **checklist em `PARA_FAZER_NO_CLOUDFLARE.md`** | quando houver mudança | dash.cloudflare.com (meu token é só de Pages) |
| Símbolos oficiais das lojas → `paginas/simbolos_lojas/<Loja>.png` | 1× | kits de afiliado |
| Awin: aprovar/pedir programas; conferir `AWIN_TOKEN` nos secrets (a nuvem lê comissões da reserva sem ele) | quinzenal | ui.awin.com |
| Decisão do vídeo de produto (AUDITORIA §3.1) | pendente desde 16/09 | — |

## 3. As decisões numéricas (o painel de dials)

| Dial | Valor | Onde no código | Decidido |
|---|---|---|---|
| Régua de vitrine | 35 Rende · 30 Confiança · 20 Momento · 15 Mostrável | `engine/regua_vitrine.py` PESOS | 17/09 |
| Faixa de preço (Rende) | ≤150 ×1 · ≤500 ×0,85 · ≤1.500 ×0,7 · acima = fora do site | `FAIXAS` | 17/09 |
| Divisão dos blocos (loja e categoria) | R$ 99,99 | `todos.html` TETO_BLOCO; `garimpo.yml --teto 99.99` | 17/09 |
| Bloco "maior valor" | até R$ 1.500, 300 por bloco/loja, rodízio categoria × terço de preço | `awin.py` TETO_ALTO, POR_BLOCO | 17/09 |
| Topo da vitrine | 5 até R$ 99,90 (ganho ≥ R$ 3) + 5 livres, intercalados | `publicar_bio.py` marcar_topo | 17/09 |
| Fogo | nota ≥ 95, queda ≥ 15, vendas ≥ 1.000, rende ≥ R$ 3, teto 6 | `publicar_bio.py` FOGO_* | 16/09 |
| Pisos | nota Ali < 90; ML < 2 vendedores; excluídos (gift card, pontos, crédito, livro) | `regua_vitrine.py` piso | 17/09 |
| Kill | 30 dias na vitrine com 0 cliques (só com cliques medidos) | `KILL_DIAS` | 17/09 |
| Recorde | menor da série com ≥ 14 dias; empate 0,5 % | `publicar_bio.py` RECORDE_DIAS_MIN | 17/09 |
| "A loja diz" | "de" da loja > maior visto ×1,02, ≥ 3 dias | `DE_INFLADO_*` | 17/09 |
| "N de olho" | aparece a partir de 2 | `todos.html` | 18/09 |
| Reposição | lembrete aos 30 dias (consumível) | `alertas.py` REPOR_DIAS | 18/09 |
| Velocidade | piso 70 mobile | `velocidade.yml` PISO | 18/09 |
| Trava de preço | 24 h sem reconferir = fora do site | `produtos_todos` limite | 15/09 |
| Instantâneo Awin | > 24 h = loja fora | `produtos_externos` | 16/09 |

## 4. Revisões com data marcada

| O quê | Quando | Por quê |
|---|---|---|
| **Teste 5+5**: cliques dos ≤ 99,90 vs livres → decide o teto do topo | **17/10/2026** | `python -m engine.cliques --dias 30` |
| Primeiro **kill** possível | 17/10 | 30 dias de série + cliques |
| Primeiro **Recorde** possível | ~26/09 | 14 dias de série |
| Selo "a loja diz" nasce | 19/09 | 3 dias de série nas externas |
| Reclame Aqui vence | 60 dias após cada leitura | `REPUTACAO_VALIDADE_DIAS` |

## 5. Como ler o que está acontecendo (comandos)

```
python -m engine.cliques --dias 7            cliques por produto no site
python -m engine.buscas_site --fechamento     o que procuraram e não acharam
python -m engine.tendencias_ml --pauta        termos em alta sem produto
python -m engine.alertas                      inscrições do avise-me
python -m engine.resultado --placar           vendas (0 até haver)
python -X utf8 paginas/publicar_bio.py        gera sem subir (mede topo/pisos/pares)
gh workflow run velocidade.yml                Lighthouse agora
```

Documentos irmãos: `CRITERIOS_DA_VITRINE.md` (por que cada regra), `AUDITORIA_MAQUINA_DE_VENDAS.md`
(o funil medido e o que trava), `handoff/RETOMADA_*.md` (estado da sessão).
