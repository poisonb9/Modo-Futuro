-- Contra-capa: esquema + politicas + semente. Rode UMA vez, inteiro.
-- A versao comentada esta' em clip_engine/supabase/ no repositorio.

create table if not exists canal (
  nome_buffer    text primary key,
  arroba         text not null,
  nome_exibicao  text not null,
  slug           text unique not null,
  ativo          boolean not null default true
);

create table if not exists link_bio (
  id       bigint generated always as identity primary key,
  canal    text not null references canal(nome_buffer) on delete cascade,
  rotulo   text not null,
  url      text not null check (url ~ '^https?://'),
  tipo     text not null check (tipo in ('conteudo','grupo','produto','outro')),
  ordem    int  not null default 100,
  ativo    boolean not null default true
);

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

create table if not exists visita (
  id     bigint generated always as identity primary key,
  quando timestamptz not null default now(),
  canal  text not null references canal(nome_buffer) on delete cascade
);

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

create or replace view v_produtos_da_bio as
select p.*,
       row_number() over (partition by p.canal
                          order by p.publicado_em desc nulls last) as pos
from produto p
where p.ativo and p.publicado_em is not null;

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

alter table canal    enable row level security;
alter table link_bio enable row level security;
alter table produto  enable row level security;
alter table visita   enable row level security;
alter table clique   enable row level security;

drop policy if exists canal_le on canal;
create policy canal_le on canal
  for select to anon using (ativo);

drop policy if exists link_le on link_bio;
create policy link_le on link_bio
  for select to anon using (ativo);

drop policy if exists produto_le on produto;
create policy produto_le on produto
  for select to anon using (ativo);

drop policy if exists visita_conta on visita;
create policy visita_conta on visita
  for insert to anon with check (true);

drop policy if exists clique_conta on clique;
create policy clique_conta on clique
  for insert to anon with check (true);

insert into canal (nome_buffer, arroba, nome_exibicao, slug, ativo) values
  ('truque.importado',        '@achadinho.make',          'Achadinho Make',          'achadinho-make',          true),
  ('semanestesia.pod',        '@semanestesia.pod',        'Sem Anestesia',           'sem-anestesia',           true),
  ('atefalhar',               '@atefalhar',               'Até Falhar',              'ate-falhar',              true),
  ('modofuturo',              '@modofuturo',              'Modo Futuro',             'modo-futuro',             true),
  ('cozinha.importada',       '@cozinha.internacional',   'Achadinho Chef',          'achadinho-chef',          true),
  ('fatura.chora',            '@fatura.chora',            'Fatura Chora',            'fatura-chora',            true),
  ('achadinhos.instantaneos', '@achadinhos.instantaneos', 'Achadinhos Instantâneos', 'achadinhos-instantaneos', true)
on conflict (nome_buffer) do update
  set arroba = excluded.arroba,
      nome_exibicao = excluded.nome_exibicao,
      slug = excluded.slug,
      ativo = excluded.ativo;

delete from link_bio where rotulo in (
  'Mais achadinhos como esse',
  'Grupo dos Achadinhos — promoção antes de todo mundo',
  'Achadinho Chef — cozinha de fora, ingrediente daqui',
  'Achadinho Total — tudo que sobra de bom',
  'Mais cortes como esse',
  'Mais treinos como esse',
  'Mais vídeos como esse',
  'Mais receitas como essa',
  'Grupo do Achadinho Chef',
  'Mais economias como essa',
  'Achadinho Total — o grupo'
);

insert into link_bio (canal, rotulo, url, tipo, ordem) values
  ('truque.importado', 'Mais achadinhos como esse',
   'https://www.tiktok.com/@achadinho.make', 'conteudo', 10),
  ('truque.importado', 'Grupo dos Achadinhos — promoção antes de todo mundo',
   'https://chat.whatsapp.com/KESO09AHGBD7UOPwxiMHpw?s=cl&p=i&mlu=4', 'grupo', 20),
  ('truque.importado', 'Achadinho Chef — cozinha de fora, ingrediente daqui',
   'https://www.tiktok.com/@cozinha.internacional', 'outro', 30),
  ('truque.importado', 'Achadinho Total — tudo que sobra de bom',
   'https://chat.whatsapp.com/FKoIqqfqWbj0Kxe6wS3Zkx?s=cl&p=i&mlu=4', 'grupo', 40),

  ('semanestesia.pod', 'Mais cortes como esse',
   'https://www.tiktok.com/@semanestesia.pod', 'conteudo', 10),

  ('atefalhar', 'Mais treinos como esse',
   'https://www.tiktok.com/@atefalhar', 'conteudo', 10),
  ('modofuturo', 'Mais vídeos como esse',
   'https://www.tiktok.com/@modofuturo', 'conteudo', 10),

  ('cozinha.importada', 'Mais receitas como essa',
   'https://www.tiktok.com/@cozinha.internacional', 'conteudo', 10),
  ('cozinha.importada', 'Grupo do Achadinho Chef',
   'https://chat.whatsapp.com/EH690bUwbt74FYrW3OEbxu?s=cl&p=i&mlu=4', 'grupo', 20),

  ('fatura.chora', 'Mais economias como essa',
   'https://www.tiktok.com/@fatura.chora', 'conteudo', 10),
  ('fatura.chora', 'Achadinho Total — o grupo',
   'https://chat.whatsapp.com/FKoIqqfqWbj0Kxe6wS3Zkx?s=cl&p=i&mlu=4', 'grupo', 20),

  ('achadinhos.instantaneos', 'Mais achadinhos como esse',
   'https://www.tiktok.com/@achadinhos.instantaneos', 'conteudo', 10),
  ('achadinhos.instantaneos', 'Achadinho Total — o grupo',
   'https://chat.whatsapp.com/FKoIqqfqWbj0Kxe6wS3Zkx?s=cl&p=i&mlu=4', 'grupo', 20);

insert into produto (canal, nome, preco_texto, preco_em, link, ativo, publicado_em)
select 'semanestesia.pod',
       'A culpa não é sua — e é exatamente isso que está te prendendo',
       'R$ 37', date '2026-09-12',
       'https://exemplo.invalido/trocar-pelo-checkout-da-kiwify',
       false, now()
where not exists (
  select 1 from produto
   where canal = 'semanestesia.pod'
     and nome like 'A culpa não é sua%');
