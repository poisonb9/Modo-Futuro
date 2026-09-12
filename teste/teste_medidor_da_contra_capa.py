# -*- coding: utf-8 -*-
"""O medidor da contra-capa: conta sem quebrar, e o banco so' aceita o que deve.

⚠️ POR QUE MEDIR AQUI. A API do TikTok esta' fechada pra nos em definitivo
(22/08/2026). Sem esta contagem, a operacao nunca sabe quantos dos que veem um
video chegam ao grupo ou ao produto — e otimizar no escuro foi o que custou os
meses ate' a medicao de 09/09.

⚠️ E POR QUE ELE E' OPCIONAL. Medicao nao pode ser condicao pra pagina abrir.
Com a chave vazia a pagina roda exatamente como antes: nenhuma requisicao,
nenhum erro. Este teste vigia as duas metades — que ele meca, e que a ausencia
dele nao quebre nada.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = (RAIZ / "paginas" / "contra_capa.html").read_text(encoding="utf-8")
ESQUEMA = (RAIZ / "supabase" / "01_esquema.sql").read_text(encoding="utf-8")
POLITICAS = (RAIZ / "supabase" / "02_politicas.sql").read_text(encoding="utf-8")
SEMENTE = (RAIZ / "supabase" / "03_semente.sql").read_text(encoding="utf-8")

falhas = []


def checar(cond, recado):
    print(("  ok  " if cond else "  [x] ") + recado)
    if not cond:
        falhas.append(recado)


print("1. a pagina mede visita e clique")
checar(PAGINA.count('medir("clique"') == 2, "clique de LINK e de PRODUTO")
checar('medir("visita"' in PAGINA, "visita por canal aberto")
checar("keepalive: true" in PAGINA,
       "keepalive — o clique LEVA EMBORA a pessoa, e sem isso o clique que "
       "converteu e' justamente o que se perde")

print("\n2. NEGATIVO — sem chave, a pagina roda como antes")
checar(re.search(r'url:\s*""', PAGINA) is not None, "a chave nasce VAZIA")
checar("if (!SUPABASE.url || !SUPABASE.anon) return;" in PAGINA,
       "sem chave, `medir` volta na hora: zero requisicao")
checar(".catch(function () {" in PAGINA,
       "e falha de rede nao derruba a pagina")

print("\n3. o canal vai no nome do BANCO, nao na chave da pagina")
# ⚠️ A chave da pagina do Achadinho Make e' o @ do TikTok
# (`achadinho.make`), e o `nome_buffer` e' `truque.importado`. Mandar a chave
# da pagina faria a chave estrangeira recusar, e o clique se perderia calado.
checar('banco: "truque.importado"' in PAGINA,
       "achadinho.make -> truque.importado")
checar('banco: "cozinha.importada"' in PAGINA,
       "cozinha.internacional -> cozinha.importada")
checar(PAGINA.count('banco: "') == 7, "os 7 canais tem nome de banco")
checar("canal: CANAIS[atual].banco" in PAGINA, "e e' ele que e' enviado")

print("\n4. o banco so' deixa fazer o que deve")
# ⚠️ Por REGEX, e nao por string exata: o SQL alinha os nomes com espacos
# diferentes pra ficar legivel, e a primeira versao deste teste reprovou
# `produto  enable` so' porque tinha dois espacos. Teste que quebra com
# formatacao ensina a nao formatar.
for tabela in ("canal", "link_bio", "produto", "visita", "clique"):
    checar(re.search(rf"alter table\s+{tabela}\s+enable row level security",
                     POLITICAS) is not None,
           f"RLS ligado em {tabela}")
checar("for insert to anon" in POLITICAS, "anon pode SOMAR visita e clique")
# ⚠️ A metade que importa: anon NAO le' o placar, e nao apaga nada. Com RLS
# ligado, ausencia de politica e' proibicao — entao o teste confere que
# ninguem escreveu uma politica de update/delete "por conveniencia".
checar("for update to anon" not in POLITICAS,
       "NEGATIVO: anon nao tem UPDATE em lugar nenhum")
checar("for delete to anon" not in POLITICAS,
       "NEGATIVO: anon nao tem DELETE em lugar nenhum")
checar("for select to anon using (ativo)" in POLITICAS,
       "e so' le' o que esta' ATIVO — desligar e' reversivel, apagar nao")
checar("select" not in POLITICAS.split("visita_conta")[1].split(";")[0],
       "NEGATIVO: a politica de visita e' so' de INSERT")

print("\n5. o esquema guarda o que a pagina manda")
checar("tipo    text not null check (tipo in ('link','produto'))" in ESQUEMA,
       "clique tem `tipo`")
checar("rotulo  text not null" in ESQUEMA, "e `rotulo`, nao id de botao")
checar("link_id" not in ESQUEMA,
       "NEGATIVO: nao voltou a apontar pra id — a pagina e' estatica e um "
       "clique que depende de consulta e' um clique que se perde")
checar("preco_com_data" in ESQUEMA,
       "preco e' TEXTO e a data e' obrigatoria quando ha' preco")

print("\n6. a semente nao mente sobre o que existe")
checar("false, now()" in SEMENTE,
       "o livro entra DESLIGADO — em 11/09 o Bryan decidiu nao por a' venda")
checar("exemplo.invalido" in SEMENTE,
       "e com link claramente falso, pra ninguem confundir com checkout real")

if falhas:
    print(f"\n{len(falhas)} FALHA(S)")
    sys.exit(1)
print("\ntudo verde")
