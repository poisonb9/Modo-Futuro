# -*- coding: utf-8 -*-
"""Sobe uma pasta de imagens de referencia para o Drive (subpasta com a data).

    python ferramentas/guardar_referencias.py <pasta>
Destino: pasta do Drive em REF_PASTA, na conta REF_CONTA (padrao labzirkonart).
Nome repetido nao sobe de novo. Falha aberta: erro aqui nao derruba o run.
"""
import mimetypes, os, sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import contas_drive as cd  # noqa: E402
import enviar_bruto_drive as eb  # noqa: E402
from googleapiclient.http import MediaFileUpload  # noqa: E402

pasta = Path(sys.argv[1])
destino_raiz = os.environ.get("REF_PASTA", "")
if not destino_raiz:
    sys.exit("REF_PASTA vazio — nada guardado")
try:
    s = cd.servico(cd.conta_por_nome(os.environ.get("REF_CONTA", "labzirkonart")))
    dest = eb._achar_ou_criar_subpasta(s, destino_raiz, f"coleta {date.today():%Y-%m-%d}")
    ja = {x["name"] for x in s.files().list(q=f"'{dest}' in parents and trashed=false",
                                             fields="files(name)", pageSize=1000).execute()["files"]}
    n = 0
    for p in sorted(pasta.iterdir()):
        if p.name in ja or not p.is_file():
            continue
        s.files().create(body={"name": p.name, "parents": [dest]},
                         media_body=MediaFileUpload(str(p), mimetype=mimetypes.guess_type(p.name)[0] or "image/jpeg"),
                         fields="id").execute()
        n += 1
    print(f"{n} imagem(ns) guardada(s) no Drive")
except Exception as e:  # noqa: BLE001
    print(f"[!] nao guardou no Drive: {type(e).__name__}")
