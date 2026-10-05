-- 15 · CATALOGO DE BUSCA (05/10/2026)
--
-- Dono: "quando a pessoa fizer a busca, se nao tivermos na loja o produto,
-- cadastrar ele instantaneamente buscando dentro do nosso acervo e ja'
-- entregando esse produto pra ela ali".
--
-- O feed INTEIRO das lojas (Awin ~76 mil + vitrine do ML) mora aqui, nao no
-- site (seria 30 MB de JSON) nem no disco da VPS. A pagina chama a funcao
-- `buscar_catalogo(q)` com a chave PUBLICA; a funcao so' LE e so' devolve o
-- que ja' e' publico (nome, preco, foto, link de afiliado). Quem ESCREVE e'
-- a VPS com a chave mestra (ferramentas/catalogo_busca.py), 1x por dia.

create extension if not exists unaccent;
create extension if not exists pg_trgm;

create table if not exists catalogo_busca (
  id           text primary key,          -- "awin:123" | "MLB123"
  nome         text not null,
  loja         text not null,
  categoria    text,
  preco        numeric(12,2) not null,
  imagem       text,
  link         text not null,
  atualizado   timestamptz not null default now(),
  busca        tsvector
);

-- unaccent nao e' IMMUTABLE; o wrapper permite indexar
create or replace function f_unaccent(text) returns text
  language sql immutable parallel safe as $$ select public.unaccent('public.unaccent', $1) $$;

create index if not exists catalogo_busca_tsv on catalogo_busca using gin (busca);
create index if not exists catalogo_busca_trgm on catalogo_busca using gin (f_unaccent(lower(nome)) gin_trgm_ops);

create or replace function catalogo_busca_tsv() returns trigger language plpgsql as $$
begin
  new.busca := to_tsvector('portuguese', f_unaccent(coalesce(new.nome,'') || ' ' || coalesce(new.categoria,'') || ' ' || coalesce(new.loja,'')));
  return new;
end $$;
drop trigger if exists catalogo_busca_tsv on catalogo_busca;
create trigger catalogo_busca_tsv before insert or update on catalogo_busca
  for each row execute function catalogo_busca_tsv();

-- RLS ligado e SEM politica de leitura direta: a chave publica so' alcanca a
-- funcao abaixo (security definer), que limita a 24 linhas e so' o que e' fresco.
alter table catalogo_busca enable row level security;

create or replace function buscar_catalogo(q text)
returns table (id text, nome text, loja text, categoria text, preco numeric, imagem text, link text)
language sql stable security definer set search_path = public as $$
  with t as (select f_unaccent(lower(trim(coalesce(q,'')))) as s)
  select c.id, c.nome, c.loja, c.categoria, c.preco, c.imagem, c.link
  from catalogo_busca c, t
  where length(t.s) >= 2
    and c.atualizado > now() - interval '3 days'
    and (c.busca @@ plainto_tsquery('portuguese', t.s)
         or f_unaccent(lower(c.nome)) like '%' || t.s || '%'
         or f_unaccent(lower(c.nome)) % t.s)
  order by (f_unaccent(lower(c.nome)) like t.s || '%') desc,
           ts_rank(c.busca, plainto_tsquery('portuguese', t.s)) desc,
           similarity(f_unaccent(lower(c.nome)), t.s) desc,
           c.preco asc
  limit 24
$$;
grant execute on function buscar_catalogo(text) to anon, authenticated;revoke all on function buscar_catalogo(text) from public;
