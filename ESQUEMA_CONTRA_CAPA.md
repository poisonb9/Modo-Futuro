# Esquema da contra-capa (Supabase) — PROPOSTA, 12/09/2026

Levantado a pedido do Bryan. **Nada foi criado**: não há conta, projeto nem
credencial. Isto é para ele ler e decidir antes de existir qualquer coisa.

O que a página precisa fazer está na `FASE2.md` §2.6: por canal, uma página
com vários links (um "para mais conteúdo como esse", um do grupo de
achadinhos com nome viral, outros) e **dois produtos** para compra imediata,
sempre os últimos filtrados e postados.

---

## 1. As cinco decisões que o esquema toma, e por quê

**1.1 Preço é TEXTO, com a data ao lado.** `preco_texto` + `preco_em`. Número
envelhece calado: a página diria "R$ 39,90" para sempre enquanto a loja já
mudou. É a mesma regra que o `engine/produto.py` já aplica no manifesto, e ela
existe para os dois lugares não divergirem.

**1.2 Link só `http(s)`, com CHECK no banco.** `javascript:` e `intent://` não
são link torto — são vetor de ataque numa página que a gente publica. Falha
FECHADA: o banco recusa a linha, não a página na hora de renderizar.

**1.3 Canal desconhecido não entra.** Chave estrangeira para `canal`. É a mesma
regra do `canais_registro.canonico()`, que devolve `None` em vez de chutar —
chutar canal foi a causa medida de oito clipes irem para o canal errado.

**1.4 Produto AUSENTE é estado normal, não erro.** Hoje NENHUM clipe tem
produto (o radar depende da aprovação do AliExpress). A página nasce sabendo
renderizar sem o bloco.

**1.5 Clique não guarda dado pessoal.** Sem IP, sem user-agent, sem
identificador. Só carimbo de tempo, canal e alvo. Responde "qual canal traz
gente", que é a pergunta, e não cria um dossiê de ninguém.

---

## 2. Tabelas

```sql
-- Projeção de engine/canais_registro.py. A FONTE continua sendo o código:
-- aqui é cópia de leitura, e quem diverge é esta tabela, nunca o motor.
create table canal (
  nome_buffer    text primary key,           -- 'modofuturo', 'truque.importado'
  arroba         text not null,              -- '@modofuturo'
  nome_exibicao  text not null,              -- 'Modo Futuro'
  slug           text unique not null,       -- o que vai na URL da bio
  ativo          boolean not null default true
);

-- Os botões da página, por canal e em ordem.
create table link_bio (
  id       bigint generated always as identity primary key,
  canal    text not null references canal(nome_buffer),
  rotulo   text not null,                    -- o nome VIRAL, não o literal
  url      text not null check (url ~ '^https?://'),
  tipo     text not null check (tipo in ('conteudo','grupo','produto','outro')),
  ordem    int  not null default 100,
  ativo    boolean not null default true
);

-- Produto de afiliado. Espelha o campo `produto` do manifesto.
create table produto (
  id            bigint generated always as identity primary key,
  canal         text references canal(nome_buffer),  -- NULL = serve a todos
  nome          text not null,
  preco_texto   text not null default '',
  preco_em      date,                        -- a data do PREÇO, não de hoje
  link          text not null check (link ~ '^https?://'),
  imagem_url    text check (imagem_url is null or imagem_url ~ '^https?://'),
  sha_clipe     text,                        -- qual clipe promoveu (rastro)
  publicado_em  timestamptz,                 -- quando o clipe foi ao ar
  ativo         boolean not null default true,
  criado_em     timestamptz not null default now(),
  constraint preco_com_data check (preco_texto = '' or preco_em is not null)
);

-- Só carimbo, canal e alvo. Nada que identifique pessoa.
create table visita (
  id       bigint generated always as identity primary key,
  quando   timestamptz not null default now(),
  canal    text not null references canal(nome_buffer)
);

create table clique (
  id         bigint generated always as identity primary key,
  quando     timestamptz not null default now(),
  canal      text not null references canal(nome_buffer),
  link_id    bigint references link_bio(id),
  produto_id bigint references produto(id),
  constraint um_alvo_so check (
    (link_id is not null and produto_id is null) or
    (link_id is null and produto_id is not null))
);

create index on clique (canal, quando);
create index on visita (canal, quando);
create index on produto (canal, publicado_em desc) where ativo;
```

### A leitura que a página faz

```sql
-- Os DOIS últimos produtos do canal, já filtrados e publicados.
create view v_produtos_da_bio as
select p.*, row_number() over (partition by p.canal
                               order by p.publicado_em desc nulls last) as pos
from produto p
where p.ativo and p.publicado_em is not null;
-- a página pede `pos <= 2`
```

---

## 3. Permissões (RLS) — o ponto que decide se isto é seguro

⚠️ **A chave anônima do Supabase é pública por natureza.** Ela vai dentro do
HTML da página, e qualquer visitante pode lê-la. O que protege não é escondê-la
— é a política de acesso.

    canal, link_bio, produto     SELECT apenas, e só onde `ativo`
    visita, clique               INSERT apenas
    tudo                         UPDATE e DELETE: NEGADOS para o anônimo

Escrever produto e link é trabalho do motor, com a chave de serviço, que NUNCA
vai para a página — ela mora nos secrets, como as outras.

⚠️ **E a consequência disso, dita na cara:** quem achar a chave anônima pode
inflar a contagem de cliques. Não há como impedir numa página estática sem
servidor. Portanto **o número de cliques é direcional, não auditado** — serve
para comparar canais entre si, não para fechar conta com ninguém.

---

## 4. O que este esquema resolve das pendências da FASE2

**Resolve a decisão que expira (§2.5).** Estava assim: "um convite de WhatsApp
por canal, ou um só? Depois que o link estiver na bio não dá para separar a
origem". ⚠️ **Com a contra-capa, a pergunta muda de lugar** — a página já
separa por canal antes de mandar para o WhatsApp, então um convite só passa a
servir. A medição vem do `clique`, não do convite.

**Resolve "quem conta o clique" (§2.6, item 3).** A API do TikTok está fechada
para nós em definitivo; esta contagem é nossa e não depende deles.

**NÃO resolve o bloqueio real.** Nada escreve `produto` hoje — o cano está
pronto da ponta a ponta e não há torneira, porque o radar de produto espera a
aprovação do AliExpress. **Os links sobem já; o bloco de produtos fica vazio
até o primeiro clipe de afiliado.** O esquema nasce sabendo disso.

---

## 5. O que eu NÃO faria

- ⛔ **Migrar o estado do motor para cá agora.** Ele funciona e acabou de ganhar
  um teste que vigia a classe inteira de defeito. Contra-capa é frente nova e
  não tem caminho crítico para quebrar — é por isso que ela vai primeiro.
- ⛔ **Pôr o convite do WhatsApp no repositório.** Ele é público, e commit fica
  no histórico para sempre. O convite entra pela tabela `link_bio`, escrito
  pela chave de serviço.
- ⛔ **Depender do banco no caminho de publicar.** Se o Supabase estiver fora, a
  página mostra menos coisa. Postar não pode parar por causa disso.
