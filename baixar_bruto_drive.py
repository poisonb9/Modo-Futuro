"""Baixa um arquivo do Drive pelo ID — usado pelo workflow do GitHub
Actions no fluxo híbrido (download local, resto na nuvem).

    python baixar_bruto_drive.py --file-id XXXX --destino fonte.mp4

Usa Service Account (GOOGLE_SERVICE_ACCOUNT_JSON), igual ao subir_drive.py.
"""
import argparse
import json
import os
import sys


def _servico():
    from googleapiclient.discovery import build

    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        sys.exit("Falta GOOGLE_SERVICE_ACCOUNT_JSON no ambiente.")
    from google.oauth2 import service_account
    info = json.loads(sa_json)
    scopes = ["https://www.googleapis.com/auth/drive"]
    cred = service_account.Credentials.from_service_account_info(info, scopes=scopes)
    return build("drive", "v3", credentials=cred)


def baixar(file_id: str, destino: str):
    from googleapiclient.http import MediaIoBaseDownload

    servico = _servico()
    req = servico.files().get_media(fileId=file_id)
    with open(destino, "wb") as f:
        downloader = MediaIoBaseDownload(f, req)
        concluido = False
        while not concluido:
            status, concluido = downloader.next_chunk()
            if status:
                print(f"  {int(status.progress() * 100)}%")
    print(f"Baixado: {destino}")


def main():
    p = argparse.ArgumentParser(description="Baixa arquivo do Drive pelo ID")
    p.add_argument("--file-id", required=True)
    p.add_argument("--destino", required=True)
    a = p.parse_args()
    baixar(a.file_id, a.destino)


if __name__ == "__main__":
    main()
