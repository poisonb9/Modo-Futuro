---
name: contra-capa
description: Monta ou adapta a contra-capa — a página de link na bio de um canal do Modo Futuro, com botões agrupados, os dois últimos produtos e o estado vazio. Use sempre que o assunto for página de bio, linktree, link na bio, landing de canal, "a página do @canal", adaptar a contra-capa para outro canal, ou quando um canal novo nascer e precisar de destino para o link do perfil — mesmo que a pessoa não diga a palavra "contra-capa".
---

# Contra-capa: a página de link na bio, uma por canal

A contra-capa é o único lugar onde a operação fala com quem veio de um vídeo.
O TikTok dá **um** link por perfil; a contra-capa transforma esse um em vários
destinos e, quando houver produto de afiliado, em venda.

O arquivo de referência é `paginas/contra_capa.html`. Ele já roda, tem os
cinco canais dentro, e é de onde se parte — **não comece uma página do zero.**

## O que muda de canal para canal, e o que nunca muda

Adaptar é preencher uma ficha, não redesenhar. A estrutura é a mesma porque
ela é o que já funciona; o que muda é o conteúdo e o acento.

```
MUDA     acento, inicial do avatar, nome, arroba, promessa,
         3 vantagens, grupos de botões, produtos
NÃO MUDA a moldura (sombra dura, cartão, coluna de 440px),
         as fontes, a ordem dos blocos, as regras abaixo
```

Por que a moldura não muda: o leitor chega pelo vídeo e cai numa página; se
cada canal parecer um site diferente, a rede de canais não existe aos olhos
dele. A identidade de cada canal entra pelo **acento**, que é uma variável só.

## A ficha de um canal

Preencha isto antes de escrever qualquer linha, e busque o que já existe em
vez de inventar:

| campo | onde achar |
|---|---|
| `nome`, `arroba` | `engine/canais_registro.py` — é a fonte única |
| `acento` | escolha uma cor que o canal já usa; se não houver, proponha |
| `promessa` | a bio do próprio perfil no TikTok, se já estiver escrita |
| `vantagens` | 3 linhas: o que a pessoa ganha, não o que o canal faz |
| `grupos` | veja a ordem canônica abaixo |
| `produtos` | do manifesto, campo `produto`; vazio é normal |

## A ordem dos grupos, e por que ela é essa

1. **"Chegou por um vídeo e quer mais?"** → o próprio canal. Quem clicou no
   link já gostou de alguma coisa; o caminho mais curto para retenção é mais
   do mesmo.
2. **O grupo de WhatsApp**, com a frase que diz o que ele entrega ("é no
   grupo que o achadinho aparece primeiro"). É o destino do funil.
3. **Os outros canais da casa**, quando fizer sentido temático. Público de
   maquiagem atravessa para cozinha; público de chip não atravessa para
   treino — não force.

Cada grupo leva **uma frase guiando**, nunca um botão solto. A frase é o que
transforma uma lista de links numa recomendação.

## Como escrever o rótulo do botão — isto vem de medição nossa

⭐ **O rótulo MOSTRA a coisa; não pergunta e não promete explicação.**

Foi medido nos vídeos e está no `sabedoria/PLAYBOOK_TIKTOK.md` §23.9: entre
18 posts, título-PERGUNTA converteu **0 de 4**, e título que AFIRMA converteu
7 de 14. É a calibragem mais bem apoiada que a operação tem, e não há razão
para o botão de uma página obedecer a uma lógica diferente do título de um
vídeo — é a mesma pessoa decidindo se clica.

```
✅ "Grupo dos Achadinhos — promoção antes de todo mundo"
❌ "Quer saber das promoções?"
✅ "Mais achadinhos como esse"
❌ "Clique aqui"
```

## As cinco regras que não são gosto

Estas vieram de defeito medido ou de decisão do Bryan. Mudar qualquer uma
exige falar com ele antes.

**1. Bloco de produto vazio é estado NORMAL, não erro.** Hoje nenhum clipe
carrega produto — o radar espera a aprovação do AliExpress. A página tem de
nascer bonita sem produto, e o texto do vazio explica o que vai aparecer ali.
Uma página que só fica boa cheia é uma página que hoje está quebrada.

**2. Link que não existe não vira `<a>` morto.** Vira cartão desligado, com o
marcador "falta o link". Link quebrado numa página publicada custa a
confiança de quem clicou; ausência declarada, não.

**3. Foto de produto é a do VENDEDOR, nunca gerada.** Quem compra precisa ver
o que vai receber. Imagem inventada de produto de afiliado é o caminho curto
para devolução e reclamação — e o acervo dos maestros da IA chega na mesma
conclusão por outro caminho: o passo demonstrado é "acesse o site oficial,
copie a imagem e a descrição do produto".

**4. Preço é TEXTO com a data colada.** `R$ 39,90` + `preço visto em 12/09`.
Número sem data envelhece calado e a página passa a mentir sozinha. É a mesma
regra do `engine/produto.py`, e as duas existem para não divergirem.

**5. ⛔ Nenhum convite de WhatsApp no repositório.** Ele é PÚBLICO e commit
fica no histórico para sempre — trocar o convite depois não apaga o antigo. Os
convites moram em `BACKUP_SISTEMA\SEGREDOS_NAO_SUBIR\CONVITES_WHATSAPP.md` e
entram pela tabela `link_bio`, com a chave de serviço. Na página, use a
constante `FALTA`.

## A miniatura: use o que o motor já produz

Cada clipe gera `capa.jpg` (`render.capa`) — o frame real do vídeo, já com o
corte vertical. O `publicar_release` sobe essa capa para a release e põe a URL
em `capa_url` no manifesto.

Isso resolve a miniatura sem gerar imagem nenhuma: a foto do botão é o vídeo
que a pessoa acabou de ver. Quando não houver `capa_url`, o mosaico do acento
com emoji aparece no lugar — é o mesmo desenho, sem buraco.

## Os dados, e por que estão embutidos

`CANAIS` é um objeto no próprio HTML. É de propósito: a página funciona hoje
sem conta, sem credencial e sem banco. O esquema do Supabase
(`ESQUEMA_CONTRA_CAPA.md`) devolve **esta mesma estrutura** — quando o banco
existir, troca-se a origem dos dados e o desenho não muda.

Quando adaptar para um canal novo, acrescente uma chave em `CANAIS` e pronto.
A aba de prévia aparece sozinha.

## Antes de entregar

- [ ] abriu a página e trocou entre TODOS os canais, não só o novo
- [ ] viu o estado **com** e **sem** produto (o interruptor no fim faz isso)
- [ ] nenhum convite real de WhatsApp no arquivo
- [ ] cada grupo tem a frase guiando
- [ ] nenhum rótulo em forma de pergunta
- [ ] tema claro e escuro (a página segue o do aparelho)
- [ ] `git add paginas/contra_capa.html` e commit

## O que ainda é decisão do Bryan

Não decida sozinho, pergunte: o **nome viral** de cada grupo, os convites, e
**onde hospedar**. O repositório `times-report` já tem Pages no ar — mas ele
guarda o `.txt` de verificação de domínio do TikTok na raiz, e mexer ali é
proibido. Repo novo é o caminho limpo.
