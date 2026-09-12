-- Contra-capa — tabelas
-- Cole no SQL Editor do Supabase e rode UMA vez. Depois rode o 02_politicas.
--
-- Desenho e justificativa: ESQUEMA_CONTRA_CAPA.md, na raiz do repositorio.
-- Aqui vai o que muda o banco; la' vai o porque de cada decisao.

-- ---------------------------------------------------------------- canal
-- Projecao de engine/canais_registro.py. A FONTE continua sendo o codigo:
-- esta tabela e' copia de leitura, e quem diverge e' ela, nunca o motor.
create table if not exists canal (
  nome_buffer    text primary key,
  arroba         text not null,
  nome_exibicao  text not null,
  slug           text unique not null,
  ativo          boolean not null default true
);

-- ---------------------------------------------------------------- link_bio
-- Os botoes da pagina, por canal e em ordem.
create table if not exists link_bio (
  id       bigint generated always as identity primary key,
  canal    text not null references canal(nome_buffer) on delete cascade,
  rotulo   text not null,
  url      text not null check (url ~ '^https?://'),
  tipo     text not null check (tipo in ('conteudo','grupo','produto','outro')),
  ordem    int  not null default 100,
  ativo    boolean not null default true
);

-- ---------------------------------------------------------------- produto
-- Espelha o campo `produto` do manifesto do motor.
--
-- ⚠️ `preco_texto` e' TEXTO com `preco_em` ao lado, e o CHECK obriga a data
-- quando ha' preco. Numero sem data envelhece calado e a pagina passa a
-- mentir sozinha — a mesma regra do engine/produto.py, escrita nos dois
-- lugares de proposito pra nao divergirem.
create table if not exists produto (
  id            bigint generated always as identity primary key,
  canal         text references canal(nome_buffer) on delete set null,
  nome          text not null,
  preco_texto   text not null default '',
  preco_em      date,
  link          text not null check (link ~ '^https?://'),
  imagem_url    text check (imagem_url is null or imagem_url ~ '^https?://'),
  sha_clipe     text,
  publicado_em  timestamptz,
  ativo         boolean not null default true,
  criado_em     timestamptz not null default now(),
  constraint preco_com_data check (preco_texto = '' or preco_em is not null)
);

-- ------------------------------------------------------- visita e clique
-- ⚠️ SO' CARIMBO, CANAL E ALVO. Sem IP, sem user-agent, sem identificador.
-- Responde "qual canal traz gente", que e' a pergunta, e nao cria dossie de
-- ninguem.
create table if not exists visita (
  id     bigint generated always as identity primary key,
  quando timestamptz not null default now(),
  canal  text not null references canal(nome_buffer) on delete cascade
);

-- ⚠️ O CLIQUE GUARDA O ROTULO, NAO O ID DO BOTAO.
--
-- A primeira versao apontava pra `link_bio(id)`. Parecia mais correto e era
-- pior: a pagina e' ESTATICA e sabe o texto do botao, nao o id — pra mandar
-- id ela teria de consultar o banco ANTES de cada clique, e um clique que
-- depende de uma consulta e' um clique que se perde quando a rede falha.
--
-- O rotulo e' o mesmo texto que a semente grava em `link_bio`, entao cruzar
-- os dois continua possivel. E se o texto do botao mudar, o historico guarda
-- o que estava escrito NA EPOCA — que e' o que se quer saber ao comparar.
create table if not exists clique (
  id      bigint generated always as identity primary key,
  quando  timestamptz not null default now(),
  canal   text not null references canal(nome_buffer) on delete cascade,
  tipo    text not null check (tipo in ('link','produto')),
  rotulo  text not null
);

create index if not exists clique_canal_quando on clique (canal, quando);
create index if not exists visita_canal_quando on visita (canal, quando);
create index if not exists produto_do_canal on produto (canal, publicado_em desc)
  where ativo;

-- ---------------------------------------------------------------- leitura
-- Os DOIS ultimos produtos de cada canal, ja' publicados. A pagina pede
-- `pos <= 2`.
create or replace view v_produtos_da_bio as
select p.*,
       row_number() over (partition by p.canal
                          order by p.publicado_em desc nulls last) as pos
from produto p
where p.ativo and p.publicado_em is not null;

-- O placar que responde a pergunta de negocio: qual canal traz gente.
create or replace view v_placar_por_canal as
select c.nome_buffer,
       c.nome_exibicao,
       (select count(*) from visita v where v.canal = c.nome_buffer) as visitas,
       (select count(*) from clique q where q.canal = c.nome_buffer) as cliques,
       (select count(*) from clique q
         where q.canal = c.nome_buffer
           and q.rotulo ilike '%grupo%')                             as cliques_grupo,
       (select count(*) from clique q
         where q.canal = c.nome_buffer and q.tipo = 'produto')       as cliques_produto
from canal c
where c.ativo;
