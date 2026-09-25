-- Pedido de SAIR dos avisos por e-mail (link "Nao quero mais receber").
-- Rode com: python supabase/rodar_sql.py supabase/11_saida_email.sql
--
-- ⭐ POR QUE EXISTE (25/09/2026): o aviso de queda sai pela API transacional
-- do Brevo, onde a etiqueta {{ unsubscribe }} NAO funciona (so' em campanha).
-- Sem saida que funcione, e-mail automatico nao pode ligar (LGPD).
--
-- A pagina /sair grava aqui {email, assinatura}. A rotina de envio (maquina
-- local, com a chave mestra) confere a assinatura — HMAC do e-mail com um
-- segredo que so' ela tem — e so' entao marca `contato.saiu_em`. Sem a
-- assinatura certa, ninguem tira outra pessoa da lista.
create table if not exists saida_email (
  id          bigint generated always as identity primary key,
  quando      timestamptz not null default now(),
  email       text not null check (char_length(email) between 6 and 120),
  assinatura  text not null check (char_length(assinatura) between 16 and 128),
  tratado_em  timestamptz
);

alter table saida_email enable row level security;

-- SO' INSERT, nunca SELECT — igual a `contato`.
drop policy if exists saida_pede on saida_email;
create policy saida_pede on saida_email
  for insert to anon with check (tratado_em is null);
