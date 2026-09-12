# Supabase da contra-capa — o que você faz, o que eu faço

## O que é seu (eu não faço, por regra)

1. **Criar a conta e o projeto** no supabase.com. Eu não crio conta nem entro
   com senha em lugar nenhum.
2. No projeto criado, abrir o **SQL Editor** e rodar os três arquivos **nesta
   ordem**, um de cada vez:

   ```
   01_esquema.sql     as tabelas e as duas leituras
   02_politicas.sql   quem pode o quê  ← é esta que decide se é seguro
   03_semente.sql     os 7 canais e os botões que já existem
   ```

3. Me mandar **duas coisas**, e só elas:
   - a **URL do projeto** (`https://xxxx.supabase.co`)
   - a chave **`anon`** (aparece como *anon* ou *publishable* em
     Settings → API)

⛔ **Não me mande a `service_role`.** Ela ignora todas as políticas e não tem
o que fazer na página. Se um dia o motor precisar escrever no banco, ela entra
como secret do GitHub, como as outras.

## O que é meu

Preencher `SUPABASE` no `paginas/contra_capa.html` com as duas e republicar. A
página já mede visita e clique — hoje, com a chave vazia, ela simplesmente não
envia nada.

## Por que a chave `anon` pode ficar no HTML

Porque ela é pública por natureza: ela vai dentro da página, e qualquer
visitante lê. O que protege o banco não é escondê-la — é o
`02_politicas.sql`, que só deixa ela:

    LER      canal, link_bio e produto, e só o que está `ativo`
    SOMAR    uma visita, um clique
    nada     de UPDATE, nada de DELETE, e NÃO lê o placar

⚠️ Quantas pessoas clicaram é informação de negócio. O visitante pode somar ao
placar e não pode vê-lo.

## O que isto NÃO garante, dito na cara

Quem achar a chave `anon` pode **inflar a contagem de cliques**. Não há como
impedir numa página estática sem servidor. Portanto o número é **direcional,
não auditado**: serve para comparar canais entre si — que é a pergunta que a
gente tem — e não para fechar conta com ninguém.

## O que perguntar ao banco depois

```sql
select * from v_placar_por_canal;
```

Devolve, por canal: visitas, cliques, cliques em grupo e cliques em produto.
É a resposta para "qual canal traz gente", que hoje ninguém sabe.

⚠️ E o número só começa a valer **depois** que a chamada no fim do clipe
estiver rodando há alguns dias — antes disso ninguém está sendo convidado a
chegar lá.

---

## Conferido no ar — 12/09/2026

Rodado contra o projeto de verdade, com a chave pública, depois que o Bryan
executou o SQL:

```
7 canais            ok
13 botoes           ok   (7 conteudo, 5 grupo, 1 outro)
livro invisivel     ok   (inativo, e a politica so' mostra ativo)
POST clique         201  funciona
POST visita         201  funciona
canal inventado     409  o BANCO recusa pela chave estrangeira
DELETE de canal     bloqueado
PATCH de botao      bloqueado
SELECT no placar    bloqueado (volta vazio)
```

⚠️ **O `204` do DELETE quase me enganou, e vale pra quem repetir isto.** No
PostgREST, `204` quer dizer "requisição válida, zero linhas afetadas" — não
"apagou". Parar no código de status teria me feito relatar o oposto do que
aconteceu. **A prova é o efeito:** reler a tabela depois e ver que os 7 canais
continuam lá e que nenhuma URL virou outra coisa.

⚠️ **Duas linhas de teste ficaram** (um clique rotulado `TESTE DE LIGACAO
12-09 (pode apagar)` e uma visita do `modofuturo`). A chave pública não apaga
— e é assim que tem de ser. Saem pelo Table Editor quando alguém quiser.

⚠️ **A contagem NÃO funciona na prévia do artifact.** Aquele ambiente bloqueia
requisição para qualquer outro domínio, então o clique lá não conta. Ela só
passa a valer quando a página estiver hospedada de verdade.
