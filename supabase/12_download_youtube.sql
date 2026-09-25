-- LIVRO DE DOWNLOADS DO YOUTUBE — compartilhado por TODAS as maquinas.
-- Rode com: python supabase/rodar_sql.py supabase/12_download_youtube.sql
--
-- ⭐ POR QUE EXISTE (dono, 25/09/2026): "pelo menos 20 minutos de intervalo
-- para qualquer video que precise ser baixado, nunca em cadeia, nesse
-- projeto ou em outros". A sentinela (engine/sentinela_youtube.py) guarda o
-- disco de UMA maquina; o runner da nuvem nasce limpo e nao sabia do que
-- tinha sido baixado antes — em 25/09 sairam 3 downloads seguidos assim.
-- Aqui fica o carimbo de cada download de VIDEO, de onde vier.
--
-- Nao ha' dado pessoal: so' hora, origem (maquina/runner) e um rotulo curto.
create table if not exists download_youtube (
  id      bigint generated always as identity primary key,
  quando  timestamptz not null default now(),
  onde    text not null check (char_length(onde) <= 60),
  rotulo  text check (rotulo is null or char_length(rotulo) <= 120)
);
create index if not exists download_youtube_quando on download_youtube (quando desc);
alter table download_youtube enable row level security;

drop policy if exists download_anota on download_youtube;
create policy download_anota on download_youtube for insert to anon with check (true);
drop policy if exists download_consulta on download_youtube;
create policy download_consulta on download_youtube for select to anon using (true);
