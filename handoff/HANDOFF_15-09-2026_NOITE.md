# HANDOFF — 15/09/2026, tarde e noite

Continuação do handoff da manhã (`HANDOFF_15-09-2026.md`, que cobre imagem,
vídeo e o radar de canais). Esta parte foi quase toda **página**, e o achado
mais importante do dia não foi nenhum recurso novo: foi descobrir que **dez
produtos anunciavam desconto que não existia**.

**20 commits hoje.**

---

## 🔴 O DEFEITO MAIS GRAVE — a queda era FALSA, e os campeões estavam nela

### Como apareceu

O Bryan pediu um **gráfico** da série de preços. Fui olhar a série ponto a
ponto só para saber se dava para desenhar a linha. Encontrei isto:

```
Conjunto de pincéis, 14/09:   12,56 · 25,08 · 12,80 · 12,57
```

Quatro leituras **no mesmo dia**, uma o dobro das outras. Não é o preço
mudando quatro vezes: são **anúncios diferentes** (variante, kit maior, outro
vendedor) gravados sob o mesmo `id`.

### A prova

`desconto_honesto()` fazia `maior = max(antes)` sobre todos os pontos. O 25,08
virava "o maior preço que nós vimos" e a página anunciava **queda de 49%**. O
espalhamento do dia batia quase **1:1** com a queda publicada:

```
52% de espalhamento -> 51,9% de "queda"   Termômetro TP300
50%                 -> 49,0%              Conjunto de pincéis
46%                 -> 44,7%              20 organizadores
34%                 -> 34,0%              Fone Lenovo GM2 Pro
32%                 -> 32,1%              Carregador 120W
```

⛔ **Os dois últimos eram os CAMPEÕES que abriam o catálogo**, colocados lá
poucas horas antes. A vitrine anunciava desconto inexistente — o oposto exato
do que a página promete.

### O conserto, em dois lugares

1. **`engine/garimpo.historico()`** — cada DIA vira um valor só, e o valor é o
   **MENOR** do dia. Menor e não média: entre duas variantes, a barata é a
   conservadora, porque puxa a queda para baixo.
2. **`paginas/publicar_bio.produtos_todos()`** — a queda passa a ser
   **recalculada** da série consolidada, não lida do registro. Sem isso o que
   já estava gravado continuaria mentindo até o produto sair do catálogo.

```
Carregador 120W       32,1%  ->  0,0%
Fone Lenovo GM2 Pro   34,0%  ->  0,0%
Termômetro TP300      51,9%  ->  0,0%
Conjunto de pincéis   49,0%  ->  4,2%
com queda >= 5%:         36  ->  26
```

⚠️ O catálogo ficou **menos atraente**, e esse é o ponto.

> ⭐ **A lição que vale mais que o conserto:** o número estava lá, plausível,
> num campo certo, há dias. Nenhum teste pegaria. Quem revelou foi a tentativa
> de **DESENHAR** o dado. Gráfico não é enfeite — é auditoria.

---

## 🚨 AS OUTRAS ARMADILHAS

### 1. Li o CÓDIGO e não o CORPO — três vezes no mesmo dia

```
Gemini   429 -> eu disse "cota do dia, volta amanhã"
              a mensagem dizia `limit: 0` — o modelo NAO existe no free tier
YouTube  429 -> eu disse "as chaves acabaram"
              era limite POR MINUTO; as 5 seguem vivas, basta espaçar 2,5 s
YouTube  429 -> repeti o mesmo erro horas depois
```

> ⭐ A regra que sobrou: **nunca classificar erro HTTP sem imprimir
> `r.text`.** Registrar como armadilha não bastou — precisou virar regra.

### 2. `200` mentiu duas vezes, e de formas diferentes

- **Pollinations**: aceita `?image=<url>`, responde 200, devolve **uma imagem
  de pessoa desconhecida** sem relação com o produto. Não é image-to-image.
- **`/icone.png`**: respondeu 200 servindo **128 KB de `text/html`** — o
  Cloudflare devolve a raiz quando o caminho não existe. Só o `content-type`
  pegou.

### 3. Anunciei "publicado" com deploy que não rodou — duas vezes

Uma por esquecer a flag `--subir` (o output dizia `[sem --subir] nada foi
empurrado` e eu não li). Outra porque o comando encadeado morreu antes do
`publicar_bio.py`. Nas duas, só a conferência baixando a página pegou.

⭐ **Por isso agora publico em comando separado**, nunca encadeado ao commit.

### 4. A guarda de publicação deu ALARME FALSO — e a culpa foi minha

Ela procurava a frase `"Achados novos"`. Troquei o rótulo do filtro para
minúscula e ela passou a gritar **"NÃO ESTÁ NO AR"** com a página nova
publicada e correta.

⛔ **Marca escrita à mão envelhece sozinha.** E guarda com alarme falso é pior
que guarda nenhuma: na vez em que ela acertar, ninguém acredita.

⭐ Agora a marca é o **sha do próprio HTML**, posto como `<meta name="v">`.
Não fica obsoleta, e prova mais: não que "alguma versão nova" subiu, e sim que
subiu **exatamente esta**. E o carimbo vem **antes** do publish — carimbar
depois reprovaria sempre.

### 5. E eu quase reportei um defeito que não existia

Procurei o carimbo da **bio** na página do **catálogo** — HTMLs diferentes,
carimbos diferentes — e disse "não está no ar". Estava.

> ⚠️ Verificação mal construída erra dos **dois** lados: aprovando o que não
> presta e reprovando o que está certo.

### 6. Consertei um arquivo e esqueci o irmão — três vezes

O conserto do texto vazando existia em `todos.html` desde 14/09 e não tinha
sido aplicado em `contra_capa.html`. Depois disso passei a conferir o par
sempre — e foi assim que descobri que a bio **não** tinha o defeito dos chips.

### 7. Quebrei a sintaxe do publicador com uma edição malfeita

Colei um bloco de texto **depois** do fechamento do docstring. O arquivo ficou
inválido; nada tinha sido commitado, e a checagem com `ast.parse` pegou na
hora. ⭐ Rodar `ast.parse` depois de toda edição estrutural em `.py` virou
hábito no resto da sessão.

---

## O QUE FICOU DE PÉ NA PÁGINA

### Nove defeitos vistos no iPhone, todos no ar

| defeito | causa |
|---|---|
| nome do atalho cortado | falta `apple-mobile-web-app-title` |
| ícone virou letra "A" | falta `apple-touch-icon` **e** o arquivo |
| texto vazando do cartão | `nowrap` SEM `overflow: hidden` |
| bolinha verde comida | o conserto acima cortava o `box-shadow` do pulso |
| produtos repetidos | dedupe por `id` não pega dois lojistas |
| chip não acendia | `montarChips()` não limpava antes de remontar |
| rodapé amador | duas frases longas de explicação |
| menu escondia opções | fila única com rolagem horizontal |
| queda falsa | ver a seção do topo |

### `engine/duplicata.py` — um cartão por produto

⛔ **O nome não resolve**, e isso é medido: `"pincéis" x "esponjas"`
(DIFERENTES) dá jaccard **0,50**, e `"Espelho de vaidade" x "Espelho de
Maquiagem"` (O MESMO) dá **0,45**. O par que não pode ser unido pontua mais
alto que o que precisa.

⭐ Quem decide é a **foto**, com o embedding da guarda de fidelidade. Limiar
**0,93** — mais apertado que o 0,85 da guarda, porque o custo do erro é
assimétrico: fundir dois produtos diferentes **tira um achado do catálogo** e
o comprador nunca sabe que ele existiu.

Resultado: **66 -> 62**. Saíram o Espelho de R$ 53,71, o Ralador de R$ 105,49,
o Fone KZ de R$ 32,09 e o Kit Tesla de R$ 40,89 — em todos ficou o **mais
barato**.

### O menu de filtros — QUATRO tentativas

```
1. chips com rolagem horizontal   escondia metade das opções
2. chips quebrando em linhas      cinco linhas, produtos fora da tela
3. <select> nativo                uma linha, mas a roda do iPhone
4. menu próprio sobreposto        uma linha E a cara da página
```

⭐ A regra que amarra todas, e que a 2 violou: **o filtro é acessório, o
produto é o principal.** A versão "mais completa" foi a pior.

O menu final: rótulo fixo + valor (`Preço: tudo`), ícone SVG (não emoji),
contagem por opção, ponto dourado na escolhida, fecha ao tocar fora / Esc.

### O catálogo abre pelos CAMPEÕES

Era por **data** — o melhor produto podia estar em 40º lugar. Agora por
`ganho x vendas`, com **90 cartões** por vez e "ver mais".

⭐ **Não dividir em páginas foi medida, não opinião:**

```
custo real     1,45 KB por produto
 300 produtos -> 0,46 MB      600 -> 0,89 MB      1000 -> 1,45 MB
```

Só perto de 600 peças o peso incomoda no 4G. Dividir custaria o **instantâneo**
da busca e do filtro, que é a premissa do Bryan.

⚠️ E `ganho x vendas` **NÃO é conversão nossa**: `vendas` é o que o mercado
comprou na loja. Vira medição de verdade com o `tracking_id` por canal.

---

## MERCADO LIVRE — a inscrição já estava feita

⚠️ O `PARA_FAZER_NO_PC` mandava fazer o que **já estava pronto** — mesmo
defeito do item 0, que cobrava o rótulo de IA já presente desde agosto.

⭐ **Atribuição PROVADA**: o painel mostra `Cliques 1` nos últimos 7 dias — o
link que o Bryan abriu em 13/09, montado pelo nosso motor. O sistema contou.

### O que mudou no motor

- **etiqueta por canal** no `matt_word`, com os nomes CONFERIDOS na tela
  (`achadinhomake`, `achadinhochef`, `instantaneos`, `pagomenos`, `atefalhar`)
  — os mesmos previstos para o AliExpress, de propósito
- **filtro de subcategoria**: `Higiene Pessoal` e `Farmácia` eram a causa do
  papel higiênico em "Beleza". Agora vêm pincéis, base, corretivo
- **comissão anotada com prazo** (14 dias): a API **não** dá comissão (ficha
  sem campo, 4 rotas em 404) e o painel **não exporta**

⭐ A comissão chega a **26%** (GANHOS EXTRAS), não 16%.
⛔ Campanhas de vídeos: exige **10 mil seguidores**. Fechado.

---

## AWIN — passa a apontar para o SITE MÃE

```
Site           https://achadinhototal.pages.dev
URL do Blog    https://achadinhototal.pages.dev/parceiros
```

⭐ Ataca a causa medida da recusa da 365Rider (*"o site não complementa a
marca do anunciante"*): o cadastro apontava para a bio de um canal de
**maquiagem**. O site mãe mostra **cinco categorias** numa página só.

⭐ E a ordem não é arbitrária: a `/parceiros` é **discurso**; o catálogo é
**prova**. A prova vai no campo principal.

---

## 🔴 O QUE CONTINUA ABERTO

1. ⛔ **`tracking_id` por canal no Portals** — o ÚNICO irreversível. Venda que
   entrar antes fica sem canal **para sempre**. E é ele que transforma o
   `ganho x vendas` em conversão medida.
   Criar em `portals.aliexpress.com` -> Ad Center -> Tracking ID, rodar
   `python teste/fumaca_tracking.py`, e só então descomentar `TRACKING`.
2. **O gráfico da série** — adiado com motivo: a série tem 3 dias (12 a 14/09)
   e 3 pontos viram uma linha que **parece inventada**. Em 2-3 semanas fica
   bom. O acervo dos Maestros **não tem nada** sobre visualização de dados.
3. **`engine/video_produto.py`** e **`engine/imagem_premium.py`** — o motor de
   imagem/vídeo segue no scratchpad (ver o handoff da manhã)
4. **Terceira perna do ModelScope** em `nome_produto.py` e `combina.py`
5. **Awin** (28 pendentes), **Shopee** (dados de pagamento)
6. **Arte do Achadinho Chef**, **endereço do Até Falhar**, **links de bio**

⚠️ Sujos que **não** devem ser commitados: `radar_modofuturo.json`,
`estado/baixados_em_intervalos.json`, `estado/videos_trabalhados.json`,
`relato_*.txt`, `paginas/avatares/logo_app_aliexpress_100.png`
