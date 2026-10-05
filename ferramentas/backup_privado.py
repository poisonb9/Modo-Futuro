"""Cópia semanal do que SÓ existe no PC (não vai pro GitHub, repo é público).

⭐ 05/10/2026 (dono: "tudo o que está no github tem cópia no projeto?" -> o
contrário não tinha: _privado, .env e tokens morriam junto com o PC).

Entra: documentos de `_privado/` (md, json, txt, py, csv, html — sem áudio/vídeo,
que são 1,9 GB e já vivem no Drive), `.env*`, `token*.json`, `*token*.txt`,
`client_secrets*.json`, `credentials.json`.
Sai: um .zip em Drive reserva > pasta BACKUP_PRIVADO, nome com a data; guarda os
8 mais novos (2 meses). Roda toda segunda 09:00 pela tarefa do Windows
`clip_engine_backup_privado` (ferramentas/backup_privado_agendado.ps1).

⚠️ O zip tem segredos: a pasta no Drive é PRIVADA da conta reserva (nunca compartilhar).

Uso: python ferramentas/backup_privado.py [--simular]
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
DOCS = {".md", ".json", ".txt", ".py", ".csv", ".html", ".ps1", ".bat"}
SEGREDOS = (".env*", "token*.json", "*token*.txt", "client_secrets*.json", "credentials.json")
PASTA = "BACKUP_PRIVADO"
GUARDAR = 8


def montar() -> tuple[bytes, int]:
    buf = io.BytesIO()
    n = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in (RAIZ / "_privado").rglob("*"):
            if f.is_file() and f.suffix.lower() in DOCS and f.stat().st_size < 20_000_000:
                z.write(f, f.relative_to(RAIZ)); n += 1
        for padrao in SEGREDOS:
            for f in RAIZ.glob(padrao):
                if f.is_file():
                    z.write(f, f.relative_to(RAIZ)); n += 1
    return buf.getvalue(), n


def subir(dados: bytes, nome: str) -> str:
    from googleapiclient.http import MediaIoBaseUpload
    import contas_drive as cd
    conta = cd.conta_por_nome("reserva")
    sv = cd.servico(conta)
    q = f"name='{PASTA}' and '{conta['raiz']}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    achou = sv.files().list(q=q, fields="files(id)").execute().get("files") or []
    pasta = achou[0]["id"] if achou else sv.files().create(body={
        "name": PASTA, "parents": [conta["raiz"]], "mimeType": "application/vnd.google-apps.folder"},
        fields="id").execute()["id"]
    arq = sv.files().create(body={"name": nome, "parents": [pasta]},
                            media_body=MediaIoBaseUpload(io.BytesIO(dados), "application/zip"),
                            fields="id,webViewLink").execute()
    velhos = sv.files().list(q=f"'{pasta}' in parents and trashed=false", orderBy="createdTime desc",
                             fields="files(id,name)").execute().get("files") or []
    for v in velhos[GUARDAR:]:
        sv.files().update(fileId=v["id"], body={"trashed": True}).execute()   # lixeira, não apaga de vez
    return arq.get("webViewLink", "")


def main() -> None:
    a = argparse.ArgumentParser(); a.add_argument("--simular", action="store_true"); a = a.parse_args()
    dados, n = montar()
    nome = f"backup_privado_{dt.date.today():%Y-%m-%d}.zip"
    print(f"{nome}: {n} arquivos, {len(dados) / 1e6:.1f} MB")
    if not a.simular:
        print("drive:", subir(dados, nome))


if __name__ == "__main__":
    main()
