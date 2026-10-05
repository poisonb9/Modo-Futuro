# PLANO DOS CANAIS — 05/10/2026 (primeira leitura de views)

> Fonte: `estado/views_tiktok.jsonl` (ferramentas/views_tiktok.py — link pelo Buffer, views pela página pública).
> 169 vídeos lidos, últimos 21 dias. ⚠️ Amostra pequena e semana NÃO redonda (falhas de postagem): conclusões
> abaixo são de DIREÇÃO, não de decimal. Reavaliar após 7 dias redondos.

## O que os dados dizem

| canal | vídeos | views totais | mediana | melhor | leitura |
|---|---|---|---|---|---|
| **Make** | 66 | **237.452** | 568 | **92.300** | **83% de TODAS as views**. Distribuição de hit: 7 de 66 passaram de 5 mil |
| **Camarim** | 6 | 8.419 | **1.260** | 2.241 | maior mediana com só 6 posts e 4 seguidores — formato bastidor funciona |
| Modo Futuro | 24 | 11.448 | 531 | 1.242 | platô |
| Sem Anestesia | 21 | 7.326 | 316 | 649 | os 3 melhores são a SÉRIE "Goggins sem filtro #1-3" |
| Achadinho Chef | 18 | 6.467 | 358 | 572 | vídeos de 70 s |
| Até Falhar (Geração 2000) | 22 | 6.405 | 213 | 583 | melhores: Coragem, o Cão Covarde (curiosidade) |
| Pago Menos / Instantâneos / Achei pra Você | 12 | ~1.400 | 80–166 | 310 | **0% de engajamento**, 0 seguidores: o formato cartão de 20 s não segura |

Achados medidos:
- **Make: nome de idol no título** → mediana 612 vs 432 sem (+42%). Mas o maior hit (92 mil) NÃO tem idol: é um gancho de identificação ("Quando você quer fazer uma maquiagem marcante mas tem medo…"). O 2º (46 mil) junta os dois: idol + segredo ("O segredo por trás dos lábios de JIWOO").
- Horário: 13h levemente melhor (1,13× a mediana do canal), 16h pior (0,87×) — diferença pequena, pode ser ruído.
- Duração: sem efeito visível entre 30–45 s e 60 s+.
- Engajamento mediano do Make: 3,3%.

## Plano

### 1. Escalar o que funciona (Make e Camarim)
- **Nunca deixar o Make sem fila** (o dia parado custou o embalo). Feito hoje: radar 13→48 candidatos, fila de corte revezando, regra da lacuna, vigia de postagem.
- **Fórmula de título do Make**: idol + segredo/curiosidade + identificação ("o segredo de X", "quando você quer… mas…"). Aplicar no gerador de título.
- **Estudar os 7 hits do Make** (> 5 mil) e repetir o formato — adaptando, nunca copiando (acervo F04669).
- **Camarim**: mesma esteira do Make, com mais volume de fonte (radar com min_views 100 mil).

### 2. Monetizar onde está a audiência
- O dinheiro está nos canais de oferta, mas a audiência está no Make. **Produtos de beleza (Oceane, ML Beleza, AliExpress beleza) na bio do Make** — "o produto da técnica que você viu". É o caminho mais curto de view para clique.

### 3. Testar formato nos canais em platô (um teste por canal, 7 dias)
- Sem Anestesia: **séries numeradas** (a série Goggins foi o melhor).
- Até Falhar: **personagem âncora** em curiosidade (Coragem rendeu) — feito hoje: menos dark, mais curiosidade.
- Chef: **versão curta (< 45 s)** contra a atual de 70 s.
- Modo Futuro: título com número/escala ("1.000 vezes", "do tamanho de um prédio") — os dois melhores usam isso.

### 4. Repensar os canais de oferta
- 20 s de cartão parado = 0% de engajamento. Precisam de **demonstração real do produto** (vídeo do vendedor/demo — `demo_local.py` existe) ou de serem absorvidos pelos canais com audiência (ver item 2). Decidir após a semana redonda.

### 5. Medir de novo em 7 dias
- `views_tiktok.yml` lê 2×/dia; `medir_clipes.py` grava cenas/min e % de pausa de cada corte novo → cruzar com views.
- Conhecimento a adquirir para avaliar: algoritmo do TikTok (janela das primeiras horas), monetização de fandom K-pop, estatística com amostra pequena.
