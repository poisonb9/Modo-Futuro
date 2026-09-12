-- Contra-capa — o canal passa a ser identificado por CODIGO
-- Rode DEPOIS do TUDO_EM_UM (ou dos tres primeiros). Roda uma vez.
--
-- ⚠️ POR QUE: a pagina publica usa `c1`..`c7` no lugar do nome interno do
-- canal (ordem do Bryan: "use codigos, deixe nosso repo mascarado"). Sem esta
-- migracao o banco recusaria o clique com 409, e o clique se perderia calado —
-- que e' o pior desfecho possivel pra uma contagem.
--
-- ⚠️ E o codigo NAO MUDA quando o canal muda de nome. E' metade do motivo de
-- ele existir: `fatura.chora` e `achadinhos.instantaneos` ainda podem trocar
-- de nome, e o historico de cliques precisa continuar apontando pro mesmo
-- canal quando isso acontecer.

alter table canal add column if not exists codigo text;

update canal set codigo = case nome_buffer
  when 'truque.importado'        then 'c1'
  when 'semanestesia.pod'        then 'c2'
  when 'atefalhar'               then 'c3'
  when 'modofuturo'              then 'c4'
  when 'cozinha.importada'       then 'c5'
  when 'fatura.chora'            then 'c6'
  when 'achadinhos.instantaneos' then 'c7'
end
where codigo is null;

alter table canal alter column codigo set not null;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'canal_codigo_unico') then
    alter table canal add constraint canal_codigo_unico unique (codigo);
  end if;
end $$;

-- ⚠️ A CHAVE SAI PRIMEIRO, DEPOIS AS LINHAS MUDAM. E' o contrario do que eu
-- tinha escrito na primeira versao, e o contrario quebrou de verdade em
-- 12/09/2026:
--
--   ERROR 23503: insert or update on table "clique" violates foreign key
--   constraint "clique_canal_fkey". Key (canal)=(c4) is not present in
--   table "canal".
--
-- O erro NAO foi na criacao da chave nova: foi no UPDATE. Com a chave antiga
-- ainda valendo — a que aponta pra `nome_buffer` — trocar 'modofuturo' por
-- 'c4' ja' viola na hora da escrita, porque 'c4' nao e' um nome_buffer.
--
-- ⚠️ E eu tinha escrito um comentario DEFENDENDO a ordem errada, com um
-- argumento que parecia bom ("se a chave mudasse primeiro, as linhas de teste
-- quebrariam a migracao"). Parecia e nao era: sem chave nenhuma, nao ha' o que
-- violar. Argumento bem escrito nao vira verificacao.
--
-- Nada se perdeu porque o Supabase roda o script inteiro numa transacao: a
-- primeira tentativa desfez tudo sozinha.
alter table clique   drop constraint if exists clique_canal_fkey;
alter table visita   drop constraint if exists visita_canal_fkey;
alter table produto  drop constraint if exists produto_canal_fkey;
alter table link_bio drop constraint if exists link_bio_canal_fkey;

update clique  c set canal = k.codigo from canal k where c.canal = k.nome_buffer;
update visita  v set canal = k.codigo from canal k where v.canal = k.nome_buffer;
update produto p set canal = k.codigo from canal k where p.canal = k.nome_buffer;
update link_bio l set canal = k.codigo from canal k where l.canal = k.nome_buffer;

alter table clique   add constraint clique_canal_fkey
  foreign key (canal) references canal(codigo) on delete cascade;
alter table visita   add constraint visita_canal_fkey
  foreign key (canal) references canal(codigo) on delete cascade;
alter table produto  add constraint produto_canal_fkey
  foreign key (canal) references canal(codigo) on delete set null;
alter table link_bio add constraint link_bio_canal_fkey
  foreign key (canal) references canal(codigo) on delete cascade;

-- O placar passa a cruzar por codigo. Continua mostrando o nome de exibicao,
-- que e' o que a gente le' — mascarar e' pra fora, nao pra dentro.
create or replace view v_placar_por_canal as
select c.codigo,
       c.nome_buffer,
       c.nome_exibicao,
       (select count(*) from visita v where v.canal = c.codigo) as visitas,
       (select count(*) from clique q where q.canal = c.codigo) as cliques,
       (select count(*) from clique q
         where q.canal = c.codigo and q.rotulo ilike '%grupo%')  as cliques_grupo,
       (select count(*) from clique q
         where q.canal = c.codigo and q.tipo = 'produto')        as cliques_produto
from canal c
where c.ativo;

-- ⚠️ A pagina publica NAO pode ler `nome_buffer`: e' justamente o que a
-- mascara esconde. Esta visao e' o que a `anon` enxerga — codigo, nome de
-- exibicao e o @, que ja' sao publicos.
create or replace view v_canal_publico as
select codigo, nome_exibicao, arroba, slug from canal where ativo;

grant select on v_canal_publico to anon;

-- E a leitura direta da tabela `canal` sai do alcance da chave publica.
drop policy if exists canal_le on canal;
