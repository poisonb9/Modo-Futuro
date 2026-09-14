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

### A proposta: uma página só pra anunciante

Um endereço novo (ex.: `quemsomos.pages.dev`), que o campo **Site** do Awin
aponta, com:

- os **cinco canais** e o que cada um cobre — beleza, cozinha, fitness,
  achadinhos gerais, promoções — cada um com link pro TikTok
- o **Telegram** e quantas pessoas recebem
- a **cadência** (publico todo dia) e de onde vem o produto
- a frase que remove a objeção: **não faço e-mail marketing, display nem
  search**

⭐ Aí o avaliador de esporte abre e vê o **Até Falhar** na tela, em vez de
procurar batom. E as bios dos canais continuam fazendo o trabalho delas.

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
