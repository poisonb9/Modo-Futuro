# A página

Uma página, vários canais. Cada canal tem o seu endereço:

```
.../             abre o primeiro
.../?c=c1        abre um canal especifico
```

## O arquivo

É **um** arquivo: `index.html`. Sem build, sem dependência, sem `npm install`.
Abre direto no navegador, inclusive offline.

Dentro dele, em ordem:

| bloco | o que é |
|---|---|
| `<style>` | o visual inteiro. Cores vêm de variáveis no `:root` |
| `SUPABASE` | endereço e chave pública da contagem de visita e clique |
| `medir()` | envia a contagem. Com a chave vazia, não envia nada |
| `BRASOES` | o avatar de cada canal, embutido como imagem |
| `CAPA_LIVRO` | a capa do produto, embutida do mesmo jeito |
| `CANAIS` | **o conteúdo**: nome, cor, frases, botões e produtos |
| `desenhar()` | monta a tela a partir do `CANAIS` |

## Para mudar alguma coisa

Quase tudo o que se quer mudar está em `CANAIS`. Cada canal tem:

```js
banco:     o codigo do canal na contagem — NAO invente, nao mude
nome:      o que aparece grande no topo
arroba:    o @ que aparece embaixo do nome
acento:    a cor do canal, em hexadecimal
promessa:  a frase abaixo do @
vantagens: as tres linhas com emoji
grupos:    os botoes, em grupos, cada um com a frase que o apresenta
produtos:  ate' dois; lista vazia mostra o aviso de "ainda nao tem"
```

⚠️ **Botão sem link ainda não pronto usa a constante `FALTA`.** Ele aparece
apagado e escrito "falta o link", em vez de virar um link morto. Link quebrado
numa página publicada é pior que ausência declarada.

⚠️ **`banco` é um código de propósito.** Ele não muda quando o canal muda de
nome — é para isso que ele existe. A tabela que diz qual código é qual canal
não está aqui.

## O que NÃO fazer

- ⛔ Não pôr chave de serviço de banco nesta página. A que está aqui é a
  pública, e o que protege os dados são as regras do lado do banco.
- ⛔ Não apagar a linha `medir()` de um botão: é ela que responde qual canal
  traz gente, e sem ela não há como saber.
- ⛔ Não trocar o `banco` de um canal para "arrumar" o nome.

## Esta página é gerada

Ela sai de um arquivo de origem, por um script. Editar aqui funciona até a
próxima geração, que sobrescreve. Se a mudança é para valer, ela tem de entrar
na origem.
