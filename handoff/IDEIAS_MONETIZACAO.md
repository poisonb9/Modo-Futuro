# Ideias de monetização — anotadas, não decididas

> Aberto em 22/08/2026. Nada aqui foi testado. É lista de hipóteses com o
> raciocínio junto, pra não se perder entre sessões.

## 1. Afiliado do TikTok Shop

**A pergunta do Bryan:** dá pra usar o nosso pipeline pra gerar conteúdo de
produto pra vender como afiliado?

**O que já temos sobre isso:** 124 das 178 transcrições em
`sabedoria/tiktok gold` citam TikTok Shop ou afiliado. O método que elas
descrevem (ex.: "O Nicho mais FÁCIL Para VENDER RÁPIDO no Tiktok SHOP",
filliperocha, 23/02/2026) é: print do produto como fundo, tela verde, rosto no
canto, 20-25 segundos, **20+ vídeos por dia**, gravados em lote em ~30 min.

**Por que o pipeline atual NÃO serve direto:**

- Ele custa ~2h30 de runner pra render 5 clipes. Conteúdo de afiliado vive de
  volume descartável, não de acabamento.
- Ele parte de vídeo longo que já existe. Pra vender um produto, o vídeo tem
  que mostrar **aquele** produto — e não existe documentário sobre o item que
  está em promoção hoje. Recortar review de terceiros pra vender por cima é
  caminho curto pra strike de direito autoral.

**Onde parece haver encaixe real, em ordem de aposta:**

1. **Produto colado no núcleo que já existe.** O canal fala de robôs, IA e
   alta tecnologia; o Shop vende gadget. Clipe sobre robô humanoide que
   termina apontando pra um robô de brinquedo, fone tradutor, mini drone. O
   conteúdo segue sendo nosso, o produto é desfecho e não assunto — não é
   troca de nicho.
2. **Reaproveitar as PEÇAS, não o pipeline.** O que serve é a **voz clonada** e
   a **legenda karaokê**, não o `main.py` inteiro. Roteiro curto de ~25s
   escrito por LLM, narrado com a voz do Bryan, sobre um print do produto:
   `gerar_narracao_padrao.py` já faz quase isso, e roda em minutos.
3. **Canal separado**, pra não estragar o sinal semântico que o algoritmo já
   aprendeu no `@modofuturo`. O PLAYBOOK inteiro é construído sobre manter o
   núcleo consistente.

**⚠️ Ressalva forte:** o conselho de "20+ vídeos/dia" do corpus contradiz o
`[CONSENSO 6]` do PLAYBOOK (2-3 posts/dia) e foi **uma rajada de 8-10 vídeos
que fez o canal do YouTube ser banido por spam em 26/07/2026**. Esse material
é `[FRACO]` — criador vendendo o próprio treinamento, não evidência medida.

**Teste pequeno proposto (não executado):** 3 clipes com desfecho de produto
no canal atual, medindo se a retenção cai.

---

## 2. Repostar vídeo de terceiro trocando o "quadro"

**A ideia do Bryan (22/08):** viu alguém que baixava vídeo de outro perfil do
TikTok — vídeo com fundo e uma legenda tipo um quadro — trocava o quadro pelo
dele e repostava no próprio perfil.

**Status: anotado, com ressalva séria. Não avaliado a fundo.**

O que precisa ser encarado antes de tentar:

- **Conteúdo não original** é uma categoria específica de penalização do
  TikTok, separada de strike formal — o mesmo tipo de coisa que suspeitamos no
  corte de alcance de 02/08 e que só foi entendido quando apareceu o rótulo de
  IA. Trocar o overlay não torna o vídeo original: o material de baixo
  continua sendo de outra pessoa.
- **O canal do YouTube já foi banido uma vez** (26/07/2026). Uma segunda perda
  de conta custa mais que qualquer ganho desse método.
- Se for testar, que seja em **conta separada**, nunca no `@modofuturo`.

Não é conselho pra fazer nem pra não fazer — é o custo, escrito antes da
decisão.

---

## 3. Agendamento em fila grande (a pergunta ferramenta)

Bryan quer alternativa gratuita ao Buffer com fila de ~100 vídeos.

**A armadilha, descoberta em 22/08:** qualquer ferramenta que publica no
TikTok precisa de um app **aprovado** pela TikTok for Developers. Auto-hospedar
um agendador de código aberto (Postiz, Mixpost) significa usar credencial
própria — e o nosso app foi **recusado** exatamente nesse ponto (ver
`handoff_22-08-2026.md`). Então "de graça e self-hosted" provavelmente esbarra
no mesmo muro que já batemos.

O caminho sem esse problema é o **agendador nativo do próprio TikTok Studio**,
que não passa por API de terceiro. Limites de quantidade e de antecedência
precisam ser verificados — não confirmados nesta sessão.

---

## 4. Automacao de postagem — pesquisado em 25/08/2026, GUARDADO a pedido do Bryan

### O que foi descoberto

**Buffer** (o que ele usa hoje):
- API disponivel pra todo cliente; conta gratuita gera **1 chave**.
- **Nao aceita upload de arquivo.** Sem endpoint de upload — voce hospeda e
  passa URL publica no campo de midia.
- **Nao expoe os campos de divulgacao do TikTok**, nem na API nem na
  interface manual (Bryan confirmou que nao consegue marcar nem na mao).
  Consta no roadmap deles como pedido, nao implementado.

**Blotato** — a que bate item por item:
- **Ja passou pela auditoria do TikTok** (app aprovado; o muro que derrubou o
  nosso app nao se aplica).
- Suporta `isAiGenerated`, o booleano de divulgacao do TikTok.
- Tem **servidor MCP** — daria pra eu postar direto, sem OAuth e sem tocar em
  credencial do Bryan.
- **Paga. Preco nao verificado.**

**Ayrshare**: API unificada madura, TikTok incluso, rotulo de IA confirmado
so' no Instagram. Tambem paga.

**Detalhe tecnico:** a API do TikTok tem tres booleanos de divulgacao —
`isBrandedContent`, `isYourBrand`, `isAiGenerated`. Quem implementa direito
expoe os tres.

**Hospedagem esta' resolvida:** GitHub Releases aceita 2 GiB por arquivo, sem
limite de tamanho total nem de banda, ate' 1.000 arquivos por release. A ~40 MB
por clipe sao ~40 GB numa release so'. Nao precisa apagar nada.

### Por que ficou guardado

O Bryan posta 2-3 por dia na mao e esta' funcionando (o canal foi de ~200 pra
1.822 views num video). **Automacao de postagem resolve trabalho repetitivo,
nao o gargalo medido** — que e' retencao e conversao em seguidor (10
seguidores para 284 curtidas). Revisitar quando o volume manual virar o
limite de verdade.

---

## 5. Onde o tempo do run realmente vai — MEDIDO em 25/08/2026

Bryan achou os runs lentos e perguntou se disparar um por conta de Gemini
aceleraria. **Nao aceleraria.** Medicao do run 32826317446 (qtd=5, 71,6 min):

| etapa | tempo |
|---|---|
| escolha dos momentos (Gemini) | ~0 |
| transcricao (Groq) | ~0 |
| traducao/narracao (Gemini) | ~0 |
| **dublagem, voz clonada (Chatterbox, CPU)** | **10-12 min POR CLIPE** |
| renderizacao + upload + resto | poucos min |

Cinco clipes = ~55 dos 64 min do passo `Cortar`. **O gargalo e' o TTS em CPU,
nao a IA.** As 14 chaves de Gemini do workflow ja' sao um pool rotativo — nao
existe "uma conta por run", qualquer run usa qualquer chave.

### Por que NAO paralelizamos (decisao do Bryan, 25/08)

A forma obvia — 1 clipe por run, N runs em paralelo via `--recorte` — **perde
qualidade**: `--recorte` pula a checagem de congelamento DE PROPOSITO (o
codigo diz isso explicitamente), porque foi feito pro caso em que o Bryan
escolhe o trecho na mao. Usar isso pra orquestrar faria todo clipe nascer sem
o filtro que descartou os tres brutos de palestra em agosto.

Da' pra consertar (flag distinguindo "recorte do Gemini" de "recorte manual"),
mas o ganho e' de relogio, nao do tempo dele: os 71 min rodam sozinhos na
nuvem. E o motor ja' produz mais rapido do que ele posta (19 brutos na fila,
~6 posts/dia). Alem disso paralelismo reabre a corrida de numeracao de 30/07,
que gerou dois clipes com o mesmo numero.

**Revisitar so' se a cadencia subir muito** (ex.: 12 posts/dia). Ai fazer COM
a correcao do congelamento junto.

**Dublar sempre**: Bryan confirmou em 25/08 que dubla TODOS os videos, e' o
padrao do canal. Cortar `--dublar` pra ganhar tempo esta' fora de questao.
