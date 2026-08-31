# Truque Importado — `@truque.importado`

Maquiagem de fora, em portugues. **Quinto canal**, nome decidido pelo Bryan em
30/08/2026.

## ESTADO

A receita foi escrita ANTES de criar a conta, de proposito — foi a falta disso
que custou dois runs de 6h no Sem Anestesia.

- [x] `@truque.importado` estava livre — **conta criada em 31/08/2026**
- [x] radar de fontes (`radar.py` — escrito, **ainda nao rodou**)
- [x] 5a conta do Buffer criada e canal conectado (31/08/2026)
- [x] secret `BUFFER_TOKEN_TRUQUEIMPORTADO` gravado (HTTP 201)
- [ ] publicar a bio
- [ ] logo em SVG
- [ ] pasta do Drive para brutos e cortes

✅ **O canal esta' pronto pra receber corte.** O nome no Buffer e'
`truque.importado`, identico ao valor de `canal` no disparo, entao a guarda
`CANAL_ESPERADO` casa.

⚠️ Na primeira tentativa a conta do Buffer existia mas com ZERO canais
conectados, e o secret **nao** foi gravado — de proposito. Secret do Actions e'
so' de ESCRITA: token errado gravado ali so' apareceria como run abortando la'
na frente. Conferir o destino real antes de gravar e' o mesmo principio da
guarda de canal.

## Receita de disparo

| parametro | valor | por que |
|---|---|---|
| `canal` | `truque.importado` | identico ao nome no Buffer, senao a guarda aborta |
| `idioma` | o da fonte | PT ganha sempre que existir equivalente (ver abaixo) |
| `dublar` | `true` | |
| `fala_literal` | **`false`** | narracao de contexto, como o @modofuturo |
| `voice_over` | **`false`** | |
| `voz_canal` | **`feminina`** | `pt-BR-FranciscaNeural` |
| `voz_clonada` | **`false`** | ⚠️ obrigatorio junto com `voz_canal` |
| `recorte` | use em fonte longa | teto de 6h do Actions |
| `SELECAO_MODO` | **`procedimento`** | ⚠️ obrigatorio — ver abaixo |

### ⚠️ A voz e' a decisao que define este canal

Voz masculina em canal de maquiagem contradiz o publico. E' o mesmo tipo de
erro que fez o Cozinha descartar fonte muda: a peca nao combina com o produto.

**`VOZ_CLONADA_ATIVA` VENCE.** O `main.py` so' cai no edge-tts quando ela e'
falsa. Pedir voz feminina sem desligar a clonagem produziria um clipe com a
voz do Bryan **em silencio** — por isso o motor RECUSA a combinacao no import
do config, antes de baixar bruto. Ver `engine/voz.py`.

### ⚠️ A REGRA QUE NAO TEM EXCECAO: o passo tem de estar INTEIRO

Ordem do Bryan, 31/08/2026, sobre os cortes deste canal:

> "Maquiagem no meio, ou deixar ela nao terminar a maquiagem, ou comecar no
> meio de outra maquiagem, faltar partes — essas coisas sao inadmissiveis."

**O motor fazia exatamente isso, e nao por acaso.** O unico criterio de corte
que existia ate' entao e' RETORICO: o corte fecha quando a IDEIA se resolve.
Ele manda, com todas as letras:

    "Termine logo apos o pico (frase mais forte), de forma ABRUPTA"

Num canal de fala isso e' tensao e segura a retencao. Num canal de
PROCEDIMENTO e' um video quebrado. Nao era um ajuste fino — era o criterio
mandando o oposto do que este canal precisa.

Por isso `SELECAO_MODO=procedimento` e' **obrigatorio no disparo**. Ele troca
o criterio por um que exige:

| | |
|---|---|
| comeco limpo | comeca quando ela PEGA o produto, nunca com a aplicacao pela metade |
| meio inteiro | passar, espalhar e corrigir estao os tres dentro do corte |
| fim resolvido | termina com a etapa CONCLUIDA e visivel |

E manda **DESCARTAR o video** se nenhuma etapa inteira couber na duracao —
melhor devolver menos cortes do que um passo pela metade.

⚠️ Sem a variavel, o disparo cai no criterio retorico e volta a cortar no
meio. **Falha ABERTA de proposito**: valor desconhecido nao derruba o run,
cai no antigo. O contrario travaria os quatro canais que ja' rodam por causa
de um typo no disparo do quinto — mas significa que ESQUECER a variavel nao
da' erro, da' corte ruim. Confira no disparo.

`teste/teste_selecao_modo.py` prova que sem a variavel o prompt fica **byte a
byte identico** ao de antes (comparado contra o git HEAD). Esse e' o caso
negativo que protege os quatro canais no ar: mudanca de prompt nao levanta
excecao e nao aparece em log — ela sai como corte pior, semanas depois.

### Por que narracao, e nao fala literal

O produto aqui e' **o passo**, nao a pessoa. Ninguem precisa da voz original da
maquiadora; precisa de saber onde ela pos o produto. Isso e' o oposto do Sem
Anestesia e do Ate Falhar, onde a fala **e'** o argumento.

Vantagem colateral, medida: a receita literal + voice over + voz clonada
estourou o teto de 6h duas vezes em 30/08/2026. A narracao de contexto fez
**5 clipes em 2h01** no run #185. Este canal nasce pela receita que cabe.

### Fonte em portugues ganha

Fonte ja' em PT pula traducao e dublagem inteiras: **83 min contra 255** no
passo do corte, e zero cota de Gemini. O audio original fica intacto.

⚠️ Em maquiagem isso tem um risco que os outros canais nao tem: se a fonte PT
for de uma criadora brasileira, o canal deixa de ser "de fora, em portugues" e
vira agregador de conteudo nacional. **Fonte PT so' quando for dublagem ou
legendagem de material estrangeiro.**

## Identidade

| | |
|---|---|
| nome de exibicao | **Truque Importado** |
| @ | `truque.importado` (16/24 caracteres, formato valido) |
| nome no Buffer | `truque.importado` |

### Bio  —  sugerida, 68/80 unidades UTF-16 (medido)

    💄 O passo que ela pula no video.
    🌍 Maquiagem de fora, em portugues

Por que esta: nao repete "truque", que agora e' o NOME, e nomeia o gargalo
medido do projeto — **retencao**. "O passo que ela pula" e' promessa de
assistir ate' o fim, e o dado de 30/08 diz que a audiencia sai em 0:02.

Alternativas medidas, todas dentro do teto:

| | unid. |
|---|---|
| 💄 O truque que ela usou, em portugues. / 🌍 Maquiagem de fora, sem enrolacao | 75 |
| 💄 A tecnica que ela usou, passo a passo. / 🌍 Maquiagem de fora, em portugues | 76 |
| 💄 Maquiagem de fora, explicada em portugues. / 🌍 O passo que ninguem mostra | 75 |

⚠️ Emoji conta mais de um caractere. Uma bio do Cozinha ja' estourou em 85 sem
ninguem notar.

### Por que "Truque Importado", e nao "Base Importada"

`Base Importada` foi a primeira proposta e esta' **descartada**. Dois defeitos:
repetir o sobrenome de *Cozinha Importada* fazia o canal ler como sub-marca
dela, nao como irmao; e "Base" sozinha e' ambigua (base de dados, base de
apoio). "Truque" e' a palavra que a espectadora usa, e o nome vira a propria
promessa do canal.

### Logo — ainda nao feita

⚠️ **Nao usar modelo de difusao (Cloudflare/FLUX).** Ele e' ruim em marca
geometrica limpa. Serviu pra personagem porque personagem tolera imperfeicao;
marca nao tolera. O caminho e' SVG.

A restricao que manda no desenho: o avatar aparece a **~50 px** no feed. Um
traco so', grosso, contraste maximo.
