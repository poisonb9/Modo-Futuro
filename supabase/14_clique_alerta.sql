-- 30/09/2026 — o botao "avise-me no Telegram" da contra-capa manda clique com
-- tipo 'alerta', e o CHECK so' aceitava 'link'/'produto': todo clique desses era
-- RECUSADO e se perdia calado (teste_medidor_da_contra_capa acusava). So' AMPLIA.
alter table clique drop constraint if exists clique_tipo_check;
alter table clique add constraint clique_tipo_check
  check (tipo in ('link','produto','alerta'));
