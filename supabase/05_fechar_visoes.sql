-- ===================================================================
-- VERSAO 1  ·  12/09/2026 12:50  ·  rode DEPOIS do 04 (VERSAO 3)
-- ===================================================================
-- Contra-capa — fechar as visoes para a chave publica
--
-- ⚠️ O DEFEITO, MEDIDO em 12/09/2026 logo depois do 04 passar:
--
--   GET /rest/v1/v_placar_por_canal  ->  HTTP 200
--   [{"codigo":"c1","nome_buffer":"truque.importado", ... "cliques":2}, ...]
--
-- A chave PUBLICA estava lendo o placar inteiro — inclusive o `nome_buffer`,
-- que e' exatamente o que a mascara da pagina existe pra esconder, e a
-- contagem de cliques, que e' informacao de negocio.
--
-- ⚠️ POR QUE AS POLITICAS NAO PEGARAM: elas estavam certas. Sao DUAS coisas
-- que se somaram, e nenhuma e' bug do que a gente escreveu:
--
--   1. no Postgres, uma VIEW roda com a permissao de quem a CRIOU, nao de
--      quem a le'. Ela passa por cima do RLS das tabelas de baixo — o RLS do
--      `clique` continua valendo pra quem consulta o `clique`, e nao vale pra
--      quem consulta uma visao que consulta o `clique`;
--
--   2. o Supabase concede `select` para `anon` em tudo que nasce no schema
--      `public`. Visao nova ja' nasce legivel.
--
-- ⚠️ E E' POR ISSO QUE `revoke` SOZINHO NAO BASTA: ele conserta esta visao, e
-- a proxima que alguem criar nasce aberta de novo. O conserto da CLASSE e'
-- `security_invoker`, que faz a visao respeitar o RLS de quem esta' lendo.

-- ------------------------------------------------------------- o placar
-- E' leitura NOSSA. Ninguem de fora tem o que fazer com ela.
revoke select on v_placar_por_canal from anon;
revoke select on v_placar_por_canal from authenticated;

-- E mesmo que alguem conceda de novo por engano, a visao passa a respeitar o
-- RLS de quem le': sem politica de select em `clique`, `visita` e `canal`,
-- nao sobra linha.
alter view v_placar_por_canal set (security_invoker = on);

-- ------------------------------------------------------ produtos da bio
-- Esta a pagina PRECISA ler. Com `security_invoker`, ela passa a obedecer a
-- politica `produto_le` (so' o que esta' ativo) em vez de ignora-la — mais
-- correto do que estava, e o resultado visivel e' o mesmo.
alter view v_produtos_da_bio set (security_invoker = on);

-- ------------------------------------------------------- canal publico
-- ⚠️ ESTA FICA COMO ESTA', e e' de proposito. Ela e' a janela curada: mostra
-- codigo, nome de exibicao, @ e slug — tudo ja' publico — e NAO mostra o
-- `nome_buffer`. Como a tabela `canal` nao tem mais politica de select, por
-- `security_invoker` ela devolveria vazio e a pagina perderia os nomes.
--
-- E' o unico lugar do desenho em que "a visao ve' mais que quem le'" e' o
-- comportamento desejado: ela existe justamente pra filtrar o que sai.
grant select on v_canal_publico to anon;
