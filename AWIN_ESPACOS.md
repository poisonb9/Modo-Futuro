# Awin — o que o anunciante vê, e como caber tudo num endereço só

⚠️ **CORRIGIDO EM 14/09/2026, depois da print do Bryan.** A primeira versão
deste arquivo listava dez Espaços Promocionais pra cadastrar. **A tela não
aceita dez.**

---

## O que a tela realmente oferece

`Configurações → Links de redes sociais` tem **quatro campos, e só**:

```
Site                 https://oachadinho.pages.dev
URL do Blog          https://oachadinho.pages.dev
Nome no Twitter      (vazio)
Página do Facebook   (vazio)
```

Não há campo de TikTok, nem de Telegram, nem lugar pra um segundo site.

⚠️ **E a API também não alcança** (medido): `/promotionalspaces`,
`/websites` e `/profile` respondem **404** com o nosso token, que só abre
`programmes` e relatórios.

---

## ⭐ Por isso a saída inverte

Se o anunciante vê **um endereço**, a resposta não é cadastrar mais
endereços — é **esse endereço mostrar a operação inteira**.

Hoje ele abre `oachadinho.pages.dev`, que é a bio do **Truque Importado**:
maquiagem e beleza. Foi exatamente a queixa da 365Rider (*Sportswear*):

> **O site não complementa a marca do anunciante**

⚠️ E **não dá pra encher a bio do Truque Importado de links dos outros
canais.** Ela tem outro trabalho: converter quem chegou de um vídeo de
maquiagem. Duas plateias, dois objetivos — quem paga a conta de misturar é a
conversão de quem veio do vídeo.

### ✅ ATUALIZADO em 15/09 — agora é o SITE MÃE, e os dois campos são usados

⚠️ **A instrução de 14/09 mandava colar a MESMA coisa nos dois campos.** Era
desperdício: a tela tem `Site` e `URL do Blog`, e eles podem apontar para
coisas diferentes.

**Cole assim:**

```
Site           https://achadinhototal.pages.dev
URL do Blog    https://achadinhototal.pages.dev/parceiros
```

⭐ **Por que o site mãe, e não a bio.** Decisão do Bryan em 15/09, e ela
ataca a causa MEDIDA da recusa. A 365Rider (Sportswear) recusou com *"o site
não complementa a marca do anunciante"* — porque abriu `oachadinho`, que é a
bio de um canal de **maquiagem**. O site mãe mostra **cinco áreas numa página
só** (medido em 15/09: Beleza, Casa, Cozinha, Eletrônicos, Fitness), com
preço e histórico. Anunciante de esporte abre e vê Fitness ali dentro.

⭐ **E a ordem dos dois campos não é arbitrária.** A `/parceiros` é
**discurso** — nós dizendo o que fazemos. O catálogo é **prova** — 62
produtos reais com preço acompanhado dia a dia. Quem avalia parceria confia
mais no que vê funcionando, então a prova vai no campo principal e a
explicação fica a um clique.

⚠️ **O site mãe NÃO fala de canal** (decisão do Bryan em 14/09, e está certa
para quem compra). O anunciante só descobre que há cinco TikToks se abrir a
`/parceiros` — que é exatamente por isso que ela continua no segundo campo,
em vez de sumir.

⚠️ **O que eu NÃO sei:** se o Awin reavalia as 28 pendentes quando o perfil
muda, ou se isso só vale para as próximas. Trocar não custa nada e melhora as
próximas de qualquer forma — mas a 365Rider pode estar perdida.

⭐ A rota foi conferida pelo CONTEÚDO, não pelo status: `/parceiros` do site
mãe tem a frase "search bidding", que só existe na página do anunciante.
Conferir por `200` não provaria nada — o Cloudflare devolve a raiz quando o
caminho não existe.

Ela lista os **seis canais** com a categoria de cada um e o setor de
anunciante que combina, como eu trabalho (garimpo diário, preço conferido
contra histórico próprio), o Telegram, e a frase que remove a objeção.

⚠️ **Não é um projeto novo:** a conta do Cloudflare bateu o teto de **10
projetos** (medido em 14/09; 4 dos 10 são endereços reservados do Até
Falhar). Então ela vai como **rota** dentro dos projetos que já existem —
o mesmo endereço serve nos cinco:

```
oachadinho.pages.dev/parceiros       200
achadinhochef.pages.dev/parceiros    200
pagomenos.pages.dev/parceiros        200
achadinhodehoje.pages.dev/parceiros  200
meulivro.pages.dev/parceiros         200
```

⭐ **E ela sobrevive ao próximo deploy.** Upload direto substitui o
diretório inteiro: se a rota não subisse no mesmo deploy da bio, o deploy
seguinte a apagaria em silêncio e o link do perfil viraria 404. Por isso
`publicar_bio.py` sobe as duas juntas e **confere a rota separadamente** —
a raiz estar nova não prova que `/parceiros` subiu.

⚠️ **O nome do dono saiu do rodapé**: o detector de vazamento do próprio
`publicar_bio.py` reprovou a primeira versão. O anunciante já vê o nome na
conta do Awin.
⚠️ **O que eu não sei:** se o Awin reavalia sozinho uma candidatura
pendente quando o perfil muda, ou se só vale pras próximas. As 28 em aberto
é que estão em jogo — a 365Rider pode estar perdida.

---

## Enquanto isso, o que cabe hoje na tela

Os dois campos vazios aceitam alguma coisa:

| campo | o que pôr |
|---|---|
| Nome no Twitter | (não temos — deixar vazio) |
| Página do Facebook | (não temos — deixar vazio) |

⚠️ **Não invente perfil pra preencher campo.** Link que não abre é pior que
campo vazio na tela de quem está decidindo.

---

⭐ Para reconferir o estado das candidaturas, sem abrir o painel:

```bash
python -m engine.awin
```
