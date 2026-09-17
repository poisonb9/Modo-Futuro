-- Clique POR PRODUTO no site mae — o dado que Ali e ML nao dao.
-- Rode com: python supabase/rodar_sql.py supabase/08_clique_produto.sql
--
-- ⭐ POR QUE EXISTE (regua v2, 17/09/2026, CRITERIOS_DA_VITRINE.md §6):
-- o Ecommerce na Pratica manda "testar 30 dias e excluir o que nao vendeu";
-- Hormozi manda escolher pelo ganho POR CLIQUE. O Awin devolve clique por
-- clickref; AliExpress e Mercado Livre so' contam por canal. Entao o proprio
-- site anota o clique no cartao — e' o EPC medido pra TODAS as lojas, e e'
-- o que alimenta o "kill de 30 dias sem clique".
--
-- ⚠️ O MESMO CONTRATO DE `visita`, `clique` E `busca`: carimbo, id do
-- produto, loja e onde clicou. Sem IP, sem user-agent, sem identificador.
-- Responde "qual produto as pessoas querem", nao "quem".
create table if not exists clique_produto (
  id       bigint generated always as identity primary key,
  quando   timestamptz not null default now(),
  produto  text not null check (char_length(produto) between 1 and 64),
  loja     text check (char_length(loja) <= 40),
  -- 'cartao' (o link principal), 'irmao' (o mesmo produto em outra loja),
  -- 'topo' (a linha viva), 'avise' (o botao avise-me)
  origem   text not null check (origem in ('cartao','irmao','topo','avise'))
);

create index if not exists clique_produto_quando on clique_produto (quando desc);
create index if not exists clique_produto_produto on clique_produto (produto, quando desc);

alter table clique_produto enable row level security;

-- ⚠️ SO' INSERT, nunca SELECT — quem le' e' o motor com a chave de servico.
drop policy if exists clique_produto_conta on clique_produto;
create policy clique_produto_conta on clique_produto
  for insert to anon with check (true);
