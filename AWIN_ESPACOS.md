# Awin — Espaços Promocionais, prontos para colar

`ui.awin.com` → **Conta → Perfil → Espaços Promocionais** → *Adicionar*.

⚠️ **MEDIDO EM 14/09/2026:** a Publisher API **não** alcança isto. Os
caminhos `/promotionalspaces`, `/websites` e `/profile` respondem **404** com
o nosso token — ele só abre `programmes` e relatórios. Não há como eu
cadastrar por você; é tela.

---

## Por que isto virou prioridade

A recusa da **365Rider** (14/09) veio com motivo no e-mail:

> **O site não complementa a marca do anunciante**

Ela é *Sportswear*. O único espaço cadastrado é `oachadinho`, que é de
achadinhos e beleza. **As outras 28 candidaturas estão sendo julgadas agora
olhando para essa mesma página.**

⭐ A leitura: não é que o publisher seja fraco — é que o avaliador de esporte
abriu uma vitrine de maquiagem. Cada anunciante precisa ver o canal que
combina com ele.

---

## Os espaços, um por um

| espaço | tipo | endereço | para quais anunciantes |
|---|---|---|---|
| Truque Importado | Site | `oachadinho.pages.dev` | beleza, saúde |
| Truque Importado (TikTok) | Rede social | `tiktok.com/@truque.importado` | beleza |
| Achadinho Chef | Site | `achadinhochef.pages.dev` | cozinha, casa, eletro |
| Achadinho Chef (TikTok) | Rede social | `tiktok.com/@cozinha.importada` | cozinha |
| Achadinhos Instantâneos | Site | `achadinhodehoje.pages.dev` | loja de departamento |
| Achadinhos Instantâneos (TikTok) | Rede social | `tiktok.com/@achadinhos.instantaneos` | geral |
| Pago menos | Site | `pagomenos.pages.dev` | promoções, departamento |
| Pago menos (TikTok) | Rede social | `tiktok.com/@fatura.chora` | promoções |
| **Até Falhar** | Rede social | `tiktok.com/@atefalhar` | **esporte, fitness** |
| Achadinho Total (Telegram) | Rede social | `t.me/achadinhototal` | geral |

⚠️ **O Até Falhar entra só como TikTok** — a página dele não existe (o
endereço ainda não foi escolhido, item 7). E é **justamente a categoria da
recusa**: enquanto não houver espaço de esporte, todo anunciante de
Sportswear vai continuar abrindo a página de beleza.

⚠️ **O Sem Anestesia fica de fora**, pelo mesmo motivo de sempre: o livro não
está à venda e a página entrega um cartão desligado.

⚠️ **Modo Futuro também fica de fora** — não tem destino hoje.

---

## A descrição, se ele pedir uma por espaço

Troque só as duas palavras entre colchetes:

```
Canal de vídeo curto sobre [beleza] em português, para público brasileiro. Publico diariamente produtos que uso e mostro em vídeo, e cada produto vai para uma página própria com preço, loja e link. Divulgação por conteúdo e redes sociais — não faço e-mail marketing, display nem search.
```

⭐ A última frase é a mesma do perfil, e pelo mesmo motivo: anunciante já se
queimou com afiliado de cupom e de search bidding. Dizer que você **não** faz
isso remove a objeção antes de ela aparecer.

---

## ⚠️ Uma coisa que eu não sei

Não sei se o Awin deixa **recandidatar** num programa recusado, nem se
corrigir os espaços faz o avaliador olhar de novo sozinho. A 365Rider pode
estar perdida. As 28 em aberto é que estão em jogo — por isso a pressa.

⭐ Para reconferir o estado a qualquer momento, sem abrir o painel:

```bash
python -m engine.awin
```
