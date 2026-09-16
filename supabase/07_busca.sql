-- Busca no site mae — o que as pessoas PROCURAM e nao acham.
-- Rode com: python supabase/rodar_sql.py supabase/07_busca.sql
--
-- ⭐ POR QUE EXISTE (ordem do Bryan em 16/09/2026): "meu amigo entrou no
-- site e pesquisou por macbook e nao tinha nada, eu queria que nos de alguma
-- forma soubessemos disso e o proximo radar ja viesse com o item; e se nao
-- tiver fonte, que isso me seja mostrado no fechamento do dia".
--
-- ⚠️ O MESMO CONTRATO DE `visita` E `clique`: so' carimbo, termo, contagem e
-- categoria. Sem IP, sem user-agent, sem identificador. Responde "o que
-- falta na prateleira", que e' a pergunta, e nao cria dossie de ninguem.
--
-- ⚠️ E O TERMO E' TEXTO DIGITADO POR ESTRANHO. Fica limitado a 80 chars no
-- banco (nao so' na pagina) e NUNCA vai pra tela sem escapar — quem le' e'
-- o motor e o relatorio, nao a pagina.
create table if not exists busca (
  id         bigint generated always as identity primary key,
  quando     timestamptz not null default now(),
  termo      text not null check (char_length(termo) between 2 and 80),
  resultados integer not null check (resultados >= 0),
  categoria  text,                       -- filtro ativo na hora, se havia
  -- ⭐ O QUE O MOTOR FEZ COM ELA. NULL = ainda nao olhou. Preenchido pelo
  -- garimpo com a chave de servico, nunca pela pagina.
  atendida   text check (atendida in ('publicada','sem_fonte','ignorada')),
  atendida_em timestamptz,
  nota       text                        -- ex.: "ML: 5 achados" / "nenhuma fonte"
);

create index if not exists busca_quando on busca (quando desc);
create index if not exists busca_pendente on busca (atendida) where atendida is null;

alter table busca enable row level security;

-- ⚠️ SO' INSERT, nunca SELECT — igual ao clique. O visitante pode dizer o
-- que procurou; nao pode ler o que os outros procuraram.
drop policy if exists busca_conta on busca;
create policy busca_conta on busca
  for insert to anon with check (true);
