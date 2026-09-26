# -*- coding: utf-8 -*-
"""Os 3 clipes de REFERENCIA: toda mudanca refeita no MESMO trecho.

POR QUE EXISTE (26/09/2026, combinado com o dono no plano da dublagem)

Cada teste ate' aqui usou um video diferente, entao "ficou melhor?" nunca
tinha comparacao justa. Agora ha' 3 clipes fixos: make (voz da Bruna),
Sem Anestesia (voice-over) e chips. Toda mudanca de voz, legenda,
enquadramento ou som e' refeita NELES, e o dono compara lado a lado antes
de ligar para todos.

- Config: `_privado/referencia/clipes.json` (tem IDs do Drive; o repo e'
  publico, por isso fica no _privado). Fontes COPIADAS na pasta
  REFERENCIA_FONTES do Drive: a limpeza de bruto nunca as apaga.
- Toda rodada e' PREVIA (`previa=true`): nao sobe pro Drive de postagem,
  nao vai pro Buffer, nao publica nada.

Uso:
    python ferramentas/referencia.py disparar     # dispara os 3 no Actions
    python ferramentas/referencia.py status       # como estao as runs
    python ferramentas/referencia.py baixar       # baixa, renomeia, sobe pro Drive
    python ferramentas/referencia.py congelar     # grava o trecho escolhido no json

Leia-me completo: `_privado/referencia/LEIA-ME.md`.
"""
import argparse
import datetime
import glob
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
PASTA = RAIZ / "_privado" / "referencia"
CONFIG = PASTA / "clipes.json"
RODADAS = PASTA / "rodadas"
WORKFLOW = "cortar_de_bruto.yml"


def _config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:2])}: {r.stderr.strip()[:300]}")
    return r.stdout


def campos(cfg: dict, clipe: dict) -> list[str]:
    """Os -f do `gh workflow run` de UM clipe de referencia. Exposto pro teste."""
    f = {
        "drive_file_id": clipe["drive_file_id"],
        "nome_arquivo": clipe["nome_arquivo"],
        "qtd": "1",
        "idioma": clipe.get("idioma", "en"),
        "estilo_legenda": "3",
        "pasta_drive": cfg["pasta_drive"],
        "conta": cfg.get("conta", "reserva"),
        "conta_saida": cfg.get("conta", "reserva"),
        "dublar": "true",
        "canal": clipe["canal"],
        "voz_clonada": "true",
        "amostra_voz": clipe.get("amostra_voz", ""),
        "selecao_modo": clipe.get("selecao_modo", ""),
        "voice_over": clipe.get("voice_over", "false"),
        "fala_literal": clipe.get("fala_literal", "false"),
        "fundo_original": clipe.get("fundo_original", "false"),
        "previa": "true",                 # ⛔ SEMPRE previa: nada e' publicado
    }
    if clipe.get("recorte"):
        f["recorte"] = clipe["recorte"]
    return [x for k, v in f.items() for x in ("-f", f"{k}={v}")]


def _ultima_rodada() -> Path | None:
    arqs = sorted(RODADAS.glob("*.json"))
    return arqs[-1] if arqs else None


def disparar(motivo: str) -> None:
    cfg = _config()
    RODADAS.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    rodada = {"carimbo": carimbo, "motivo": motivo, "commit": _gh(
        "api", "repos/{owner}/{repo}/commits/main", "--jq", ".sha").strip()[:7],
              "runs": {}}
    for clipe in cfg["clipes"]:
        antes = time.time()
        _gh("workflow", "run", WORKFLOW, *campos(cfg, clipe))
        run_id = None
        for _ in range(12):                    # a run leva alguns s pra aparecer
            time.sleep(5)
            lst = json.loads(_gh("run", "list", "--workflow", WORKFLOW, "-L", "5",
                                 "--json", "databaseId,createdAt,event"))
            novos = [r for r in lst if r["event"] == "workflow_dispatch"
                     and datetime.datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
                     .timestamp() >= antes - 5
                     and r["databaseId"] not in rodada["runs"].values()]
            if novos:
                run_id = novos[0]["databaseId"]
                break
        rodada["runs"][clipe["nome"]] = run_id
        print(f"  {clipe['nome']:13s} run {run_id}  "
              f"({'trecho fixo ' + clipe['recorte'] if clipe.get('recorte') else 'o motor escolhe o trecho'})")
    arq = RODADAS / f"{carimbo}.json"
    arq.write_text(json.dumps(rodada, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"rodada salva em {arq.relative_to(RAIZ)}")


def status() -> None:
    arq = _ultima_rodada()
    if not arq:
        print("nenhuma rodada ainda")
        return
    rodada = json.loads(arq.read_text(encoding="utf-8"))
    print(f"rodada {rodada['carimbo']} ({rodada.get('motivo', '')}), commit {rodada.get('commit')}")
    for nome, rid in rodada["runs"].items():
        s = json.loads(_gh("run", "view", str(rid), "--json", "status,conclusion"))
        print(f"  {nome:13s} {rid}  {s['status']} {s['conclusion']}")


def baixar() -> None:
    import contas_drive
    from googleapiclient.http import MediaFileUpload
    cfg = _config()
    arq = _ultima_rodada()
    rodada = json.loads(arq.read_text(encoding="utf-8"))
    destino = PASTA / "saidas" / rodada["carimbo"]
    destino.mkdir(parents=True, exist_ok=True)
    d = contas_drive.servico(contas_drive.conta_por_nome(cfg.get("conta", "reserva")))
    nome_pasta = f"REFERENCIA {rodada['carimbo']}"
    pasta = d.files().create(body={"name": nome_pasta, "parents": [cfg["pasta_drive"]],
                                   "mimeType": "application/vnd.google-apps.folder"},
                             fields="id,webViewLink").execute()
    for nome, rid in rodada["runs"].items():
        tmp = Path(tempfile.mkdtemp())
        try:
            _gh("run", "download", str(rid), "-n", "previa-clipes", "-D", str(tmp))
        except RuntimeError as e:
            print(f"  {nome}: sem artefato ({e})")
            continue
        for plat, padrao in (("tiktok", "short_9x16.mp4"), ("reels", "short_9x16_reels.mp4")):
            achados = sorted(glob.glob(str(tmp / "**" / padrao), recursive=True))
            if not achados:
                continue
            final = destino / f"REF_{nome}_{plat}_{rodada['carimbo']}.mp4"
            shutil.copy(achados[0], final)
            d.files().create(body={"name": final.name, "parents": [pasta["id"]]},
                             media_body=MediaFileUpload(str(final), mimetype="video/mp4",
                                                        resumable=True)).execute()
            print(f"  {final.name}")
        posts = sorted(glob.glob(str(tmp / "**" / "post.json"), recursive=True))
        if posts:
            shutil.copy(posts[0], destino / f"post_{nome}.json")
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"local: {destino.relative_to(RAIZ)}")
    print(f"Drive: {pasta['webViewLink']}")


def trecho_do_post(post: dict) -> str | None:
    """'INICIO-FIM' do clipe escolhido pelo motor. Exposto pro teste."""
    a, b = post.get("inicio_s"), post.get("fim_s")
    return f"{float(a):.1f}-{float(b):.1f}" if a is not None and b is not None else None


def congelar() -> None:
    cfg = _config()
    arq = _ultima_rodada()
    rodada = json.loads(arq.read_text(encoding="utf-8"))
    saidas = PASTA / "saidas" / rodada["carimbo"]
    mudou = False
    for clipe in cfg["clipes"]:
        if clipe.get("recorte"):
            continue
        post = saidas / f"post_{clipe['nome']}.json"
        if not post.exists():
            print(f"  {clipe['nome']}: rode `baixar` antes")
            continue
        t = trecho_do_post(json.loads(post.read_text(encoding="utf-8")))
        if t:
            clipe["recorte"] = t
            mudou = True
            print(f"  {clipe['nome']}: trecho congelado em {t}")
    if mudou:
        CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="clipes de referencia")
    ap.add_argument("acao", choices=["disparar", "status", "baixar", "congelar"])
    ap.add_argument("--motivo", default="", help="o que esta rodada testa")
    a = ap.parse_args()
    {"disparar": lambda: disparar(a.motivo), "status": status,
     "baixar": baixar, "congelar": congelar}[a.acao]()
