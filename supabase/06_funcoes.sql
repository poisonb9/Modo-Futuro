-- ===================================================================
-- VERSAO 1  ·  12/09/2026 13:10  ·  rode DEPOIS do 05
-- ===================================================================
-- Contra-capa — duas funcoes estreitas, chamaveis pela chave publica
--
-- ⚠️ POR QUE ISTO EXISTE. Pedido do Bryan em 12/09/2026: "voce tem como fazer
-- isso no SQL? eu nao posso ficar entrando no pc". A chave publica nao apaga
-- nada e nao le' o placar — e' assim que tem de ser. Isto NAO afrouxa essa
-- regra: cria duas portas estreitas, cada uma fazendo UMA coisa escrita aqui.
--
-- ⚠️ O RACIOCINIO DE SEGURANCA, porque `security definer` merece explicacao:
-- estas funcoes rodam com a permissao de quem as criou, entao elas passam por
-- cima do RLS — de proposito. O que as torna seguras nao e' quem chama: e' o
-- fato de NAO RECEBEREM o que apagar nem o que ler. O alcance esta' congelado
-- no corpo delas. Uma funcao que recebesse a condicao como texto seria uma
-- porta aberta com outro nome.

-- ------------------------------------------------------------- limpar teste
-- Apaga SO' o que foi escrito como teste. O criterio esta' no corpo e nao
-- entra por parametro: `rotulo` que comeca com 'TESTE'.
--
-- ⚠️ A visita nao tem rotulo, entao ela so' pode ser apagada por DATA — e por
-- isso a funcao recebe um limite de tempo em vez de apagar tudo. Chamar com
-- uma data no passado nao apaga visita nova; chamar sem querer nao leva o
-- historico junto.
create or replace function limpar_testes(ate timestamptz)
returns table (cliques_apagados bigint, visitas_apagadas bigint)
language plpgsql
security definer
set search_path = public
as $$
declare c bigint; v bigint;
begin
  delete from clique where rotulo like 'TESTE%' and quando <= ate;
  get diagnostics c = row_count;
  delete from visita where quando <= ate;
  get diagnostics v = row_count;
  return query select c, v;
end $$;

revoke all on function limpar_testes(timestamptz) from public;
grant execute on function limpar_testes(timestamptz) to anon;

-- ------------------------------------------------------------------ placar
-- Devolve o placar SEM o `nome_buffer` — a mascara continua valendo, e quem
-- le' de fora ve' codigo e nome de exibicao, que ja' sao publicos.
--
-- ⚠️ E' leitura, nao escrita: o pior que alguem com a chave publica faz aqui
-- e' saber quantos cliques cada canal teve. Vale a pena pra eu poder conferir
-- de longe, e por isso o `nome_buffer` fica de fora.
create or replace function placar()
returns table (codigo text, canal text, visitas bigint, cliques bigint,
               cliques_grupo bigint, cliques_produto bigint)
language sql
security definer
set search_path = public
as $$
  select c.codigo,
         c.nome_exibicao,
         (select count(*) from visita v where v.canal = c.codigo),
         (select count(*) from clique q where q.canal = c.codigo),
         (select count(*) from clique q
           where q.canal = c.codigo and q.rotulo ilike '%grupo%'),
         (select count(*) from clique q
           where q.canal = c.codigo and q.tipo = 'produto')
  from canal c
  where c.ativo
  order by c.codigo;
$$;

revoke all on function placar() from public;
grant execute on function placar() to anon;
