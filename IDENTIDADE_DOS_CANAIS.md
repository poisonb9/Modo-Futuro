# Identidade dos canais — brasão, acento e nome

Quem manda no **nome técnico** é `engine/canais_registro.py`. Este arquivo
cuida do resto: qual brasão é de qual canal, que cor cada um usa na
contra-capa, e **quais nomes ainda podem mudar**.

Conferido em 12/09/2026 contra a tela "Mudar de conta" do TikTok — a lista de
contas do próprio aplicativo, que é a única fonte que não depende de memória.

## A tabela

| canal (nome_buffer) | arroba no TikTok | brasão | acento | nome |
|---|---|---|---|---|
| `truque.importado` | `@achadinho.make` | lábios vermelhos sobre ouro | `#E0157F` | firme |
| `semanestesia.pod` | `@semanestesia.pod` | letra **A** cromada, corte vermelho | `#D92B2B` | firme |
| `atefalhar` | `@atefalhar` | halter cromado sobre ouro | `#E36414` | firme |
| `modofuturo` | `@modofuturo` | **MF** cromado sobre PRATA | `#1B5BFF` | firme |
| `cozinha.importada` | `@cozinha.internacional` | chapéu de chef cromado | `#1F8A5F` | ⚠️ vira `@achadinho.chef` em 26/09 |
| `fatura.chora` | `@fatura.chora` | carrinho de compras cromado | `#C1841A` | ⚠️ **pode mudar** |
| `achadinhos.instantaneos` | `@achadinhos.instantaneos` | lupa cromada sobre ouro | `#7A3FF2` | ⚠️ **pode mudar** |

⚠️ **Os dois últimos são os canais abertos mais recentemente, e o Bryan avisou
em 12/09/2026 que o nome deles ainda está sujeito a alteração.** Antes de
imprimir esses nomes em qualquer lugar que custe caro desfazer — arte, bio,
convite de grupo, domínio — confirme com ele. Dentro do código, trocar o nome
é barato; num convite de WhatsApp que já circulou, não é.

## A arte

```
paginas/avatares/<canal>.png              320px, para quando houver hospedagem
dentro de paginas/contra_capa.html        WebP de 160px em data URI, ~11 KB cada
BACKUP_SISTEMA\ARTE_CANAIS\brasoes_originais\    os arquivos em ALTA (1254px)
BACKUP_SISTEMA\ARTE_CANAIS\referencia_linkfly\   as prints que geraram o desenho
```

⚠️ **O original fica FORA do repositório, de propósito.** São ~2 MB por
brasão; o repo é público e não ganha nada carregando 20 MB de arte que a
página não usa — ela usa o WebP de 11 KB. O original importa no dia em que
alguém precisar gerar outro tamanho, e para isso o backup basta.

⚠️ **Por que o brasão vai EMBUTIDO na página.** Ela tem de funcionar como
arquivo solto — sem servidor, sem CDN e sem caminho relativo para quebrar. O
PNG de 320px fica no repositório para o dia em que houver hospedagem de
verdade; o WebP embutido é o que faz a página abrir em qualquer lugar hoje.

⚠️ **Falta UM brasão: `cozinha.importada`** (chapéu de chef sobre ouro, visível
na tela do TikTok). Enquanto não chegar, esse canal mostra o monograma sobre o
acento — o círculo tem o mesmo tamanho, então a página não muda de forma
quando a arte aparecer.

⚠️ **O `modofuturo` veio diferente dos outros, e por isso teve tratamento
diferente.** Ele chegou como FOTO: a moeda apoiada num balcão de mármore, com
um laboratório desfocado atrás. O cenário foi descartado por ordem do Bryan
("apenas o círculo") e a moeda saiu com **máscara circular e fundo
transparente** — não com corte quadrado. Corte quadrado deixaria o mármore
aparecendo nas quinas de qualquer container menos redondo que o avatar, e o
mesmo arquivo ainda vai virar miniatura de 44 px.

## O padrão visual dos brasões

Todos seguem a mesma família, e isso não é acaso — é o que faz a rede de
canais parecer uma rede:

- disco de **ouro escovado** com aro de **cromo** polido
- símbolo em cromo, em relevo, com reflexo alto
- fundo preto, que a máscara redonda do avatar recorta
- exceção proposital: o `modofuturo` é **prata sobre prata**, não ouro — é o
  canal de tecnologia, e a ausência do dourado o separa dos de compra

## Onde cada nome aparece, se mudar

Um canal batizado em vários lugares é o molde de erro que já custou caro aqui
(ver `FASE2.md` §1.2). Se um nome mudar, os pontos são:

1. `engine/canais_registro.py` — a fonte; o `nome_buffer` e os apelidos
2. `paginas/contra_capa.html` — chave em `CANAIS`, `nome`, `inicial`, link
3. `paginas/avatares/<canal>.png` — o arquivo do brasão
4. este arquivo
5. a bio do perfil no TikTok e o convite do grupo — fora do repositório

⚠️ O `nome_buffer` **não** muda quando o @ do TikTok muda: são coisas
diferentes, e foi confundi-las que fez a cozinha ter dois nomes em oito
arquivos.
