-- 18/09/2026: de onde a pessoa veio (bio.<canal>, telegram, video.<id>).
alter table clique_produto add column if not exists de text check (char_length(de) <= 40);
notify pgrst, 'reload schema';
