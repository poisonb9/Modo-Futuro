-- Contato de quem pediu alerta de queda — e-mail e/ou telefone.
-- Rode com: python supabase/rodar_sql.py supabase/10_contato.sql
--
-- ⭐ POR QUE EXISTE (aprovado pelo Bryan em 24/09/2026): o "avise-me" so'
-- falava com o Telegram; quem nao usa Telegram ia embora sem deixar caminho.
--
-- ⚠️ E' DADO PESSOAL (LGPD). Diferente de `busca`/`clique`, aqui HA'
-- identificador — por isso: so' com consentimento marcado (consentimento_em
-- obrigatorio), saida registrada (saiu_em) em vez de sumir, e a copia local
-- mora em `_privado/` (fora do git). Nunca vai pra pagina nem pro repositorio.
create table if not exists contato (
  id              bigint generated always as identity primary key,
  quando          timestamptz not null default now(),
  email           text check (email is null or (char_length(email) between 6 and 120
                                                and email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$')),
  telefone        text check (telefone is null or telefone ~ '^\+?[0-9]{10,15}$'),
  origem          text not null check (origem in ('site','bot')),
  produto         text check (produto is null or char_length(produto) <= 200),
  consentimento_em timestamptz not null,
  saiu_em         timestamptz,
  check (email is not null or telefone is not null)
);

create index if not exists contato_quando on contato (quando desc);
create index if not exists contato_ativo on contato (email) where saiu_em is null;

alter table contato enable row level security;

-- ⚠️ SO' INSERT, nunca SELECT — igual a `busca`. O visitante deixa o proprio
-- contato; nao le' o de ninguem. E nao escolhe saiu_em (entra ativo).
drop policy if exists contato_deixa on contato;
create policy contato_deixa on contato
  for insert to anon with check (saiu_em is null);
