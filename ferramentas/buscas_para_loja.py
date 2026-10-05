# -*- coding: utf-8 -*-
"""O que as pessoas BUSCAM no site vira produto VISÍVEL na loja.

⭐ 05/10/2026 (dono): "sempre que forem pesquisar, os produtos entram pra dentro
da loja como produtos visíveis dentro do site" + "o primeiro a buscar é o
Mercado Livre".

Ciclo (de hora em hora, tarefa do Windows — o SUPABASE_PAT só existe aqui):
  1. lê os termos buscados nos últimos 7 dias (tabela `busca`, todos, com ou sem
     resultado), mais buscados primeiro;
  2. para cada termo novo ou com mais de 24 h, `mercadolivre.buscar` (link do
     anúncio, régua anti-isca);
  3. grava `estado/ml_busca.json` no formato da vitrine; o publicador junta com
     `ml_vitrine.json` (categoria "Mercado Livre"), e o publicador automático
     sobe o site quando o arquivo muda.

    python -X utf8 ferramentas/buscas_para_loja.py          # roda
    python -X utf8 ferramentas/buscas_para_loja.py --ver    # só mostra os termos
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAIZ / ".env")
from engine import buscas_site, mercadolivre  # noqa: E402

SAIDA = RAIZ / "estado" / "ml_busca.json"
MAX_TERMOS = 40          # por rodada
POR_TERMO = 6
REBUSCA_H = 24
GUARDA_DIAS = 14         # produto de busca fica na loja 14 dias


def termos(dias: int = 7) -> list[dict]:
    return buscas_site._sql(
        "select lower(trim(termo)) as termo, count(*) as vezes, max(quando) as ultima "
        "from busca where quando > now() - make_interval(days => " + str(int(dias)) + ") "
        "  and nota is distinct from 'TESTE' and length(trim(termo)) >= 3 "
        "group by 1 order by vezes desc, ultima desc")


def _num(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v or "").replace("R$", "").strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def main() -> None:
    agora = datetime.now(timezone.utc)
    try:
        atual = json.loads(SAIDA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        atual = {"quando": "", "termos": {}, "produtos": []}
    feitos = atual.get("termos", {})
    lista = termos()
    if "--ver" in sys.argv:
        for t in lista[:MAX_TERMOS]:
            print(t["vezes"], t["termo"], "(ja' buscado em " + feitos.get(t["termo"], "-") + ")")
        return
    prods = {p["id"]: p for p in atual.get("produtos", [])
             if p.get("visto", "") > (agora - timedelta(days=GUARDA_DIAS)).isoformat()}
    n_termos = 0
    for t in lista:
        termo = t["termo"]
        if feitos.get(termo, "") > (agora - timedelta(hours=REBUSCA_H)).isoformat():
            continue
        if n_termos >= MAX_TERMOS:
            break
        n_termos += 1
        try:
            achados = mercadolivre.buscar(termo, quantos=POR_TERMO)
        except Exception as e:  # noqa: BLE001 — um termo nao derruba os outros
            print(f"  [!] {termo}: {str(e)[:70]}")
            continue
        feitos[termo] = agora.isoformat()
        for x in achados:
            pid = str(x.get("_id") or "")
            preco = float(x.get("preco_num") or _num(x.get("preco")))
            if not pid or preco <= 0 or not x.get("link"):
                continue
            prods[pid] = {
                "id": pid, "nome": (x.get("nome") or "").strip(), "preco": preco,
                "imagem": x.get("imagem") or "", "link": x["link"], "loja": "Mercado Livre",
                "categoria": "", "categoria_ml": x.get("categoria_ml") or "",
                "comissao": float(x.get("comissao") or 0), "marca": "", "de_loja": 0.0,
                "origem": "mercadolivre", "busca": termo, "visto": agora.isoformat(),
            }
        print(f"  {termo!r} ({t['vezes']}x): +{len(achados)}")
        time.sleep(0.5)
    novo = {"quando": agora.isoformat(), "termos": feitos, "produtos": list(prods.values())}
    if novo["produtos"] == atual.get("produtos"):
        print("nada novo")
        return
    SAIDA.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(prods)} produto(s) de busca na loja ({n_termos} termo(s) consultados)")
    # sobe pro repo: o publicador automatico olha o origin/main
    subprocess.run(["git", "add", "-f", str(SAIDA)], cwd=RAIZ)
    subprocess.run(["git", "commit", "-q", "-m", "busca -> loja: produtos do ML pelos termos buscados"], cwd=RAIZ)
    subprocess.run(["git", "pull", "-q", "--rebase", "--autostash"], cwd=RAIZ)
    subprocess.run(["git", "push", "-q"], cwd=RAIZ)


if __name__ == "__main__":
    main()
