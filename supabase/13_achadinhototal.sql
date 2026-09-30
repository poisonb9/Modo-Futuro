-- 30/09/2026 — @achadinhototal entra na contra-capa como c8.
-- Autorizado pelo dono no chat ("Pode fazer o supabase"). Sem esta linha o
-- banco recusa (chave estrangeira) todo clique/visita da pagina dele.
-- Pode rodar de novo (upsert). O codigo NAO muda se o nome mudar.
insert into canal (nome_buffer, arroba, nome_exibicao, slug, ativo, codigo) values
  ('achadinhototal', '@achadinhototal', 'Achadinho Total', 'achadinho-total', true, 'c8')
on conflict (nome_buffer) do update
  set arroba = excluded.arroba, nome_exibicao = excluded.nome_exibicao,
      slug = excluded.slug, ativo = excluded.ativo, codigo = excluded.codigo;
