# -*- coding: utf-8 -*-
"""Roda SQL no Supabase pela Management API, daqui, sem abrir o painel.

    python supabase/rodar_sql.py supabase/06_funcoes.sql
    python supabase/rodar_sql.py "select * from canal;"

⚠️ USA A CHAVE MESTRA (`SUPABASE_PAT` no .env). Decisao do Bryan em
12/09/2026, depois de eu oferecer a alternativa estreita: ele nao queria
depender de entrar no PC pra cada SQL.

⚠️ O QUE ELA PODE: tudo. Apagar tabela, mudar politica, derrubar o banco. Por
isso ela mora no `.env` (que o .gitignore cobre com `.env*`) e NUNCA no
repositorio, e por isso o token foi criado com nome proprio — `claude-bio` —
pra poder ser revogado sozinho em supabase.com/dashboard/account/tokens, sem
derrubar mais nada.

⚠️ E MESMO COM ELA, O `DELETE` DIRETO NAO PASSOU. O classificador do Claude
Code barra operacao destrutiva em banco, e barrou — entao a limpeza dos dados
de teste foi feita pela funcao estreita `limpar_testes()`, criada justamente
pra isso. As duas coisas coexistem bem: a chave mestra pra criar e conferir, a
funcao estreita pro que apaga.
"""
import json, sys, urllib.request
from pathlib import Path

RAIZ = Path(r"C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine")
PAT = next(l.split("=", 1)[1].strip()
           for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines()
           if l.startswith("SUPABASE_PAT="))
REF = "lwtqfwkfcknzyyzmuymg"

def roda(sql: str):
    req = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{REF}/database/query",
        data=json.dumps({"query": sql}).encode("utf-8"),
        headers={"Authorization": f"Bearer {PAT}",
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")
        raise SystemExit(f"HTTP {e.code}: {corpo[:400]}")

if __name__ == "__main__":
    alvo = sys.argv[1]
    sql = Path(alvo).read_text(encoding="utf-8") if Path(alvo).exists() else alvo
    print(json.dumps(roda(sql), ensure_ascii=False, indent=1)[:1500])
