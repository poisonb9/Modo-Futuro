-- Contra-capa — a semente: os 7 canais e os botoes que ja' existem
-- Rode DEPOIS do 02_politicas.sql. Pode rodar de novo sem estragar nada
-- (tudo e' upsert).
--
-- ⚠️ A FONTE DOS NOMES E' `engine/canais_registro.py`, e o brasao/acento estao
-- no `IDENTIDADE_DOS_CANAIS.md`. Se um nome mudar la', muda aqui tambem — a
-- lista dos cinco lugares esta' naquele arquivo.
--
-- ⚠️ `fatura.chora` e `achadinhos.instantaneos` ainda podem trocar de NOME
-- (aviso do Bryan em 12/09/2026). O `nome_buffer` e' a chave primaria: se o
-- nome mudar, e' um UPDATE aqui e nas linhas que apontam pra ele.

insert into canal (nome_buffer, arroba, nome_exibicao, slug, ativo) values
  ('truque.importado',        '@achadinho.make',          'Achadinho Make',          'achadinho-make',          true),
  ('semanestesia.pod',        '@semanestesia.pod',        'Sem Anestesia',           'sem-anestesia',           true),
  ('atefalhar',               '@atefalhar',               'Até Falhar',              'ate-falhar',              true),
  ('modofuturo',              '@modofuturo',              'Modo Futuro',             'modo-futuro',             true),
  ('cozinha.importada',       '@cozinha.internacional',   'Achadinho Chef',          'achadinho-chef',          true),
  ('fatura.chora',            '@fatura.chora',            'Fatura Chora',            'fatura-chora',            true),
  ('achadinhos.instantaneos', '@achadinhos.instantaneos', 'Achadinhos Instantâneos', 'achadinhos-instantaneos', true)
on conflict (nome_buffer) do update
  set arroba = excluded.arroba,
      nome_exibicao = excluded.nome_exibicao,
      slug = excluded.slug,
      ativo = excluded.ativo;

-- ---------------------------------------------------------------- botoes
-- ⚠️ Limpa antes de semear pra rodar duas vezes nao duplicar botao. So' as
-- linhas desta semente: se alguem acrescentar um botao pela mao, ele some
-- aqui — entao acrescente NA SEMENTE, nao direto na tabela.
delete from link_bio where rotulo in (
  'Mais achadinhos como esse',
  'Grupo dos Achadinhos — promoção antes de todo mundo',
  'Achadinho Chef — cozinha de fora, ingrediente daqui',
  'Achadinho Total — tudo que sobra de bom',
  'Mais cortes como esse',
  'Mais treinos como esse',
  'Mais vídeos como esse',
  'Mais receitas como essa',
  'Grupo do Achadinho Chef',
  'Mais economias como essa',
  'Achadinho Total — o grupo'
);

insert into link_bio (canal, rotulo, url, tipo, ordem) values
  -- Achadinho Make
  ('truque.importado', 'Mais achadinhos como esse',
   'https://www.tiktok.com/@achadinho.make', 'conteudo', 10),
  ('truque.importado', 'Grupo dos Achadinhos — promoção antes de todo mundo',
   'https://chat.whatsapp.com/KESO09AHGBD7UOPwxiMHpw?s=cl&p=i&mlu=4', 'grupo', 20),
  ('truque.importado', 'Achadinho Chef — cozinha de fora, ingrediente daqui',
   'https://www.tiktok.com/@cozinha.internacional', 'outro', 30),
  ('truque.importado', 'Achadinho Total — tudo que sobra de bom',
   'https://chat.whatsapp.com/FKoIqqfqWbj0Kxe6wS3Zkx?s=cl&p=i&mlu=4', 'grupo', 40),

  -- Sem Anestesia (o livro entra como PRODUTO, nao como link)
  ('semanestesia.pod', 'Mais cortes como esse',
   'https://www.tiktok.com/@semanestesia.pod', 'conteudo', 10),

  -- Ate Falhar e Modo Futuro: so' conteudo. Nao tem grupo nem produto, e
  -- convidar pra pagina que nao entrega gasta a frase (ver engine/chamada.py).
  ('atefalhar', 'Mais treinos como esse',
   'https://www.tiktok.com/@atefalhar', 'conteudo', 10),
  ('modofuturo', 'Mais vídeos como esse',
   'https://www.tiktok.com/@modofuturo', 'conteudo', 10),

  -- Achadinho Chef
  ('cozinha.importada', 'Mais receitas como essa',
   'https://www.tiktok.com/@cozinha.internacional', 'conteudo', 10),
  ('cozinha.importada', 'Grupo do Achadinho Chef',
   'https://chat.whatsapp.com/EH690bUwbt74FYrW3OEbxu?s=cl&p=i&mlu=4', 'grupo', 20),

  -- Fatura Chora
  ('fatura.chora', 'Mais economias como essa',
   'https://www.tiktok.com/@fatura.chora', 'conteudo', 10),
  ('fatura.chora', 'Achadinho Total — o grupo',
   'https://chat.whatsapp.com/FKoIqqfqWbj0Kxe6wS3Zkx?s=cl&p=i&mlu=4', 'grupo', 20),

  -- Achadinhos Instantaneos
  ('achadinhos.instantaneos', 'Mais achadinhos como esse',
   'https://www.tiktok.com/@achadinhos.instantaneos', 'conteudo', 10),
  ('achadinhos.instantaneos', 'Achadinho Total — o grupo',
   'https://chat.whatsapp.com/FKoIqqfqWbj0Kxe6wS3Zkx?s=cl&p=i&mlu=4', 'grupo', 20);

-- ---------------------------------------------------------------- o livro
-- ⚠️ ENTRA COM `ativo = false`. Em 11/09/2026 o Bryan decidiu NAO por a'
-- venda ainda: o produto nao esta' cadastrado na Kiwify e o link abaixo e'
-- PLACEHOLDER. A pagina so' mostra o que esta' ativo, entao ele fica invisivel
-- ate' alguem trocar o link pelo checkout de verdade e virar `ativo = true`.
--
-- Deixar a linha pronta e desligada e' melhor que nao ter linha: no dia da
-- estreia sao dois campos, e nao uma tabela nova.
insert into produto (canal, nome, preco_texto, preco_em, link, ativo, publicado_em)
select 'semanestesia.pod',
       'A culpa não é sua — e é exatamente isso que está te prendendo',
       'R$ 37', date '2026-09-12',
       'https://exemplo.invalido/trocar-pelo-checkout-da-kiwify',
       false, now()
where not exists (
  select 1 from produto
   where canal = 'semanestesia.pod'
     and nome like 'A culpa não é sua%');
