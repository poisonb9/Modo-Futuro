# HANDOFF — 16/09/2026, madrugada (23:33 → 07:19 BRT)

Sessão que **travou sem handoff**: às 07:17 BRT a conta devolveu *"organization
has disabled Claude subscription access"* e as duas últimas mensagens do Bryan
ficaram sem resposta. Este arquivo foi reconstruído a partir do transcrito
(`e4ea99ce…jsonl`) na sessão seguinte, às 07:40 BRT. Anterior:
[`HANDOFF_15-09-2026_PARTE4.md`](HANDOFF_15-09-2026_PARTE4.md).

**9 commits** (00:32 → 02:35 UTC) + **`engine/awin.py` editado e NÃO
commitado** (03:26 UTC).

---

## ESTADO NO FECHAMENTO

```
local           ad5d635 + awin.py sujo (catalogo Awin, +163 linhas)
no ar           achadinhototal.pages.dev   142 produtos   258 KB (210 KB de JSON)
Awin            JOINED 1 (Nike BR mid 17652)   PENDING 20   REJECTED 8
```

---

## 1. ⭐ A NIKE, MEDIDA — e o catálogo Awin já lê os feeds

Detalhe em [`AWIN_ESPACOS.md`](../AWIN_ESPACOS.md) (seção "A NIKE BR, MEDIDA").
O que fecha aqui:

```
feeds da Nike       44669 (29 col, 5.447)  +  93360 (35 col, 5.457)   sobrepostos
deduplicado         por aw_product_id, fica a linha MAIS COMPLETA
ate R$ 150          905 produtos   min R$ 59,98        (~370 KB de card)
ate R$ 250        1.268            mediana geral R$ 449,99
inteira           5.457            max R$ 2.599,99      2,2 MB de JSON
```

⛔ **A chave do feed é OUTRA credencial** (`AWIN_FEED_API_KEY`, 32 hex, dentro
da URL de download do Crie um Feed). O `AWIN_TOKEN` dá 500 lá. **Ela passou
por print e por chat** → regenerar no painel antes de colar no `.env`. O
`catalogo()` foi testado passando a chave só na linha de comando; nada gravado.

⛔ **Link sem `awinaffid` paga OUTRA pessoa** (afiliado 13430), com a página
abrindo normal. Sempre `aw_deep_link`, nunca `merchant_deep_link`.

⚠️ `in_stock` veio 1 em 100% dos 5.457 — campo fixo, não usado como garantia.

⚠️ Status no CSV do feed é `active`, não `joined` (filtrar por joined = zero).

---

## 2. AS DECISÕES DO BRYAN SOBRE A SEÇÃO NIKE

1. **Nike vira categoria própria** no site mãe. Dentro dela: bloco até R$ 250 e
   bloco 250+, com "ver mais".
2. **A com selo do C — padrão para TODO produto:** entra sem histórico com selo
   "novo no catálogo"; gradua para gráfico com 3 leituras (`_serie_curta`
   `minimo=3` já faz a trava; o `todos.html` já tem `novo`/`olho` por `pontos`).
3. ⛔ **"Não quero o site lento."** Carregamento inicial igual ao de hoje; o que
   for além baixa **só quando a pessoa clica**. Medido: cada card Nike = 421 B;
   905 cards = 372 KB, quase dobra a página. Não entra na inicial.
4. **50 cards, mais baratos primeiro** — ⭐ **NO TOPO DA CATEGORIA NIKE**, não
   da página principal (esclarecido às 07:19, última mensagem). Depois os 50
   seguintes mais caros. O feed não tem `vendas`, então o critério é preço.

### ⭐ O template JÁ TEM o mecanismo inteiro (`paginas/todos.html`)

```
TETO_VITRINE = 250      tira da lista principal E divide os dois blocos
SO_NO_SEGMENTO          categoria que só existe atrás do menu (hoje: Calçados)
PASSO_BLOCO = 15        "ver mais" dentro da categoria
novo / olho             selo por pontos < 2 / >= 2
```

O item 4 **resolve o conflito** que eu tinha levantado (50 no topo ×
`SO_NO_SEGMENTO`): Nike **segue a regra do Calçados** — fora do rolar
principal, tudo dentro da categoria. Só falta ligar; não escrever mecanismo.

⚠️ Ainda aberto: `PASSO_BLOCO` é 15 e ele pediu blocos de 50 para a Nike.

---

## 3. ⭐ DUAS ORDENS QUE FICARAM SEM RESPOSTA (07:17 BRT)

**a) Pedido de produto na conversa → o melhor de CADA loja.** Complementa a
memória `modofuturo-pedido-sob-demanda`: se o produto existe em várias lojas,
publico **todos os melhores anúncios por canal**; o cliente escolhe na hora
(Brasil rápido × AliExpress barato, e às vezes ele pode esperar). O que vender
fica; os outros saem do ar depois da venda. **É por isso que a operação
precisa de catálogos brasileiros**, e não só do AliExpress.

**b) "Por que ainda não temos Mercado Livre no site?"** Resposta pelos
registros: inscrição feita, `MELI_MATT_TOOL` no `.env`, 5 etiquetas por canal
criadas, atribuição **provada** (1 clique contado em 15/09). O que faltou foi a
**fonte**: `mais_vendidos` do ML devolve papel higiênico e Elseve — farmácia de
marca, não achadinho — e em 15/09 ficou "ML pede busca dirigida por produto, é
outro trabalho". Ninguém marcou como próximo passo. ⭐ **O item (a) é a busca
dirigida.** ML entra pelo caminho do pedido sob demanda, não pelo garimpo
automático.

---

## 4. ERROS MEUS DESTA SESSÃO

⛔ **Aconselhei pôr `oachadinho.pages.dev/parceiros` no campo Site do Awin**,
contradizendo a decisão registrada de 15/09 (`achadinhototal`). O Bryan clicou
antes de eu ler o `AWIN_ESPACOS.md`. Ele corrigiu às 00:25. **Ler o registro
antes de aconselhar campo que julga candidatura.**

⛔ **Afirmei 325 produtos até R$ 150 e mínimo R$ 89,99** — era um feed só. Com
os dois deduplicados: **905 e R$ 59,98**.

⛔ **Chutei a página em ~60 KB; medido: 258 KB.** Estimativa minha entrou numa
recomendação de desenho antes da medição.

⚠️ **Sessão de 8 h sem handoff intermediário.** Se a conta caísse 1 h antes,
o esclarecimento das 07:19 teria morrido com ela.

---

## 5. ⭐ A ÁREA NIKE FOI LIGADA NA SESSÃO SEGUINTE (16/09, 07:40–08:30 BRT)

```
engine/awin.py          --guardar --teto 150  -> estado/awin_catalogo.json (instantâneo)
                                              + precos_vistos.jsonl, id "awin:<id>" (série)
paginas/publicar_bio.py produtos_externos()   lê o instantâneo (SEM rede), recusa > 24h
                        montar_catalogo()     HTML leva só o ÍNDICE; cartões vão em nike.json
                        publicar_no_ar        nike.json em /todos/ (bios) e na raiz (site mãe)
                        conferir_no_ar        confere o JSON no ar pelo próprio carimbo
paginas/todos.html      EXTERNOS              categoria no menu com contagem; fetch só no clique
                                              passo 50 na lista corrida E nos blocos
.github/workflows/garimpo.yml                 --guardar depois do --vigiar, `|| true`
teste/teste_categoria_externa.py              8 seções, casos negativos teoremáticos
```

**Provado no navegador com dublê de 120 produtos:** abertura pede 0 bytes da
Nike (só o índice no HTML); `/#nike` abre com **50 cartões + "ver mais 50 de
70"**, mais baratos primeiro, selo "novo"; voltar a "todas" → grade sem Nike.

⛔ **Defeito que o dublê expôs:** a Nike inteira (teto 150) fica abaixo de
R$ 250, então a categoria NÃO se divide em dois blocos — cai na lista
corrida, que andava de 90 em 90. O passo 50 tinha de valer nos dois caminhos.

⛔ **Cache do navegador enganou a segunda medição** (mesma URL, HTML velho).
Medir com `?v=N` ou reload forçado.

### O que falta para a Nike aparecer NO AR (nesta ordem)

1. 🔴 **Bryan:** regenerar a chave do feed no painel (a de hoje passou por
   print) e colar como secret `AWIN_FEED_API_KEY` no GitHub **e** no `.env`.
2. Rodar `python -m engine.awin --guardar --teto 150` (ou esperar o garimpo
   das 10h23 UTC) → nasce `estado/awin_catalogo.json`.
3. `python paginas/publicar_bio.py` → publica e confere `nike.json` no ar.

⚠️ Sem o passo 1 nada muda no site — `EXTERNOS = {}` e a página sai idêntica
à de hoje (medido na seção 5 da guarda).
3. 🔴 Awin: 10 anunciantes BR nunca pedidos; Clovis Calçados (8.198 produtos).
   Encaminhar os 6 e-mails de recusa (PF × perfil).
4. 🟠 ML por busca dirigida (item 3b) — ligado ao fluxo sob demanda.
5. Os itens 3–13 da PARTE4 continuam.

---

## 6. AWIN — A RODADA DE PEDIDOS DE 16/09 (manhã BRT)

Bryan pediu ~45 programas com os blocos colados desta sessão (campo Site já
em `achadinhototal`). Medido às 12h UTC:

```
joined    7   Nike · Carraro · Clovis Calçados · Exypna · Lauri Esporte · Leveros · Radiale Pneus
pending  62   inclui Natura, Boticário, Eudora, Avon, MAC, JBL, Stanley, Kabum,
              Centauro, adidas (re-pedido), Loja do Mecânico, Granado/Phebo,
              9 de viagem (Decolar, CVC, Expedia, Azul, GOL, Zupper...)
```

⭐ **6 aprovaram no mesmo dia** — programa pequeno aprova sozinho. Todos os 7
estão em `EXTERNAS` como categoria própria; **nenhum aparece no site até a
`AWIN_FEED_API_KEY` entrar** (secret + `.env`). Loja cujo `merchant_name` do
feed não bater com o mapa cai no aviso "loja SEM MAPA" do publicador.

⚠️ **Viagem é outro motor** (promoção com validade, não produto com série);
endpoint `promotions` deu 500 com o token atual. Não montar antes de aprovar.

**Não estão no Awin BR:** Mercado Livre (programa próprio, já ativo), Growth,
Integralmédica, Max Titanium, Sephora, Época, Tramontina.

Decisão: **aguardar as 62 respostas**; próximo ataque é o **Mercado Livre**
(busca dirigida por produto — o caminho do pedido sob demanda).

---

## 7. MERCADO LIVRE ATACADO + BUSCAS DO SITE (16/09, tarde BRT)

**Decisões do Bryan:** pedido sob demanda no ML publica **sem** anotação de
comissão (regra **A**); Gemini expande termo genérico; **anotar o que as
pessoas buscam no site** e, sem fonte, mostrar no fechamento do dia.

```
engine/mercadolivre.py  buscar(termo)   /products/search + /items em paralelo (4 fios)
                                        menor anuncio (1o NAO e' o mais barato)
                                        dominio majoritario (peca fora), livro fora
                                        2+ vendedores; expandir() via modelo
                        _get            429 espera; 404 e' o UNICO "sem vendedor"
engine/modelo_texto.py  perguntar()     rodizio Gemini->OpenRouter; 403 = chave morta
engine/buscas_site.py   pendentes/atender/fechamento — le' Supabase (PAT), 3 fontes,
                        JUIZ de pertinencia (acessorio nao e' o produto)
supabase/07_busca.sql   tabela `busca`: so' INSERT p/ anon; motor marca `atendida`
paginas/todos.html      anota {termo, resultados, categoria} 900ms apos parar de digitar
```

**Medido:** "macbook" (busca real de um amigo) → antes: capa de teclado como
"atendido"; depois do juiz: **MacBook Air M1 R$ 6.000, Pro M3 R$ 14.000**,
link com etiqueta do canal. "liquidificador" genérico → Mondial 550W R$ 70
(9 vendedores). Site publicado às 17:10 UTC, carimbo `6d22c10ad05c`, 17
endereços conferidos; busca "iphone 15" gravada no banco a partir do site real.

⛔ **Erros meus:** truncamento (`[:80]`, `[:100]`) me fez afirmar "id cortado"
e "5 links idênticos" — os dois falsos. Heredoc comeu `\n` outra vez (4ª).
Martelei o ML com 6 fios em medições seguidas e tomei 429 — e o 429 dentro
do fio virava "sem vendedor" (consertado: só 404 é ausência).

**Falta:** (1) `--atender` roda AQUI (PAT não está nos secrets) — decidir se
vai pra nuvem; (2) `--fechamento` ainda não entra no relato diário
automático; (3) publicar no site o que `--atender` acha ainda é manual (o
pedido sob demanda); (4) OpenRouter zerou as 50/dia em 3 contas hoje.
