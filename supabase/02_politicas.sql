-- Contra-capa — quem pode o que (RLS)
-- Rode DEPOIS do 01_esquema.sql, no mesmo SQL Editor.
--
-- ⚠️ ISTO E' A PARTE QUE DECIDE SE A COISA E' SEGURA, e nao a chave.
--
-- A chave `anon` do Supabase e' PUBLICA por natureza: ela vai dentro do HTML,
-- e qualquer visitante le'. O que protege nao e' esconde-la — e' o que ela
-- pode fazer. Sem as politicas abaixo, `anon` com RLS desligado consegue
-- APAGAR as tabelas inteiras.

-- Liga o RLS. Com ele ligado e SEM politica, ninguem passa — falha FECHADA,
-- que e' o lado certo pra errar.
alter table canal    enable row level security;
alter table link_bio enable row level security;
alter table produto  enable row level security;
alter table visita   enable row level security;
alter table clique   enable row level security;

-- ------------------------------------------------------------- ler
-- So' SELECT, e so' o que esta' ativo. Linha desativada some da pagina sem
-- precisar ser apagada — desligar e' reversivel, apagar nao.
drop policy if exists canal_le on canal;
create policy canal_le on canal
  for select to anon using (ativo);

drop policy if exists link_le on link_bio;
create policy link_le on link_bio
  for select to anon using (ativo);

drop policy if exists produto_le on produto;
create policy produto_le on produto
  for select to anon using (ativo);

-- ------------------------------------------------------------- contar
-- ⚠️ SO' INSERT, nunca SELECT. O visitante pode somar ao placar e NAO pode
-- ler o placar: quantas pessoas clicaram e' informacao de negocio, e nao tem
-- por que estar aberta a quem abre a pagina.
--
-- A conferencia da origem fica por conta da chave estrangeira: canal que nao
-- existe na tabela `canal` e' recusado pelo banco, e nao pela boa vontade de
-- quem chama.
drop policy if exists visita_conta on visita;
create policy visita_conta on visita
  for insert to anon with check (true);

drop policy if exists clique_conta on clique;
create policy clique_conta on clique
  for insert to anon with check (true);

-- ------------------------------------------------------------- o que fica de fora
-- UPDATE e DELETE: nenhuma politica para `anon`, em nenhuma tabela. Com RLS
-- ligado, ausencia de politica e' proibicao.
--
-- Escrever produto e link e' trabalho do motor, com a chave de SERVICO, que
-- ignora RLS e NUNCA vai para a pagina — ela mora nos secrets, como as outras.

-- ⚠️ O QUE ISTO NAO IMPEDE, dito na cara pra nao virar surpresa: quem achar a
-- chave anon pode inflar a contagem de cliques, e nao ha' como impedir numa
-- pagina estatica sem servidor. Portanto o numero e' DIRECIONAL, nao
-- auditado: serve pra comparar canais entre si, nao pra fechar conta com
-- ninguem. Se um dia virar dinheiro, a contagem migra pra uma funcao com
-- limite por IP — que e' outro projeto.
