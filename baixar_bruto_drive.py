"""Baixa um arquivo do Drive pelo ID — usado pelo workflow do GitHub
Actions no fluxo híbrido (download local, resto na nuvem).

    python baixar_bruto_drive.py --file-id XXXX --destino fonte.mp4

Usa Service Account (GOOGLE_SERVICE_ACCOUNT_JSON), igual ao subir_drive.py.
"""
import argparse
import json
import os
import sys


def _servico(conta: str = "principal"):
    """Cliente do Drive para a conta indicada.

    O bruto vive na conta onde foi subido, e o vídeo inteiro é processado
    nela — então quem dispara o corte informa qual é. OAuth primeiro: a
    Service Account lê, mas não escreve (não tem cota de armazenamento), e
    manter as duas etapas na mesma credencial evita surpresa.
    """
    from googleapiclient.discovery import build

    try:
        import contas_drive
        return contas_drive.servico(contas_drive.conta_por_nome(conta))
    except Exception as e:
        # Sem o contas_drive (ou conta desconhecida) cai no caminho antigo,
        # pra não quebrar quem chamar sem passar --conta.
        print(f"[aviso] seleção de conta indisponível ({e}); usando fallback.")

    oauth = os.getenv("GOOGLE_OAUTH_TOKEN_JSON")
    if oauth:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        cred = Credentials.from_authorized_user_info(
            json.loads(oauth), ["https://www.googleapis.com/auth/drive"])
        if not cred.valid and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        return build("drive", "v3", credentials=cred)

    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        sys.exit("Falta GOOGLE_OAUTH_TOKEN_JSON ou GOOGLE_SERVICE_ACCOUNT_JSON.")
    from google.oauth2 import service_account
    info = json.loads(sa_json)
    scopes = ["https://www.googleapis.com/auth/drive"]
    cred = service_account.Credentials.from_service_account_info(info, scopes=scopes)
    return build("drive", "v3", credentials=cred)


def baixar(file_id: str, destino: str, conta: str = "principal"):
    from googleapiclient.http import MediaIoBaseDownload

    servico = _servico(conta)

    # NOME ORIGINAL DO ARQUIVO NO DRIVE, guardado ao lado do video.
    #
    # O destino aqui e' sempre `fonte.mp4` — o nome que o Bryan deu ao subir
    # se perde no download, e com ele a unica pista de QUAL video do YouTube
    # isto e'. O `yt-dlp` batiza o arquivo com o titulo do video, entao o nome
    # E' o titulo.
    #
    # Em 01/09/2026 o Bryan pediu os episodios anteriores de um corte que
    # comecava no "dia 3". O clipe existia, o canal existia, e nao havia como
    # saber que video era: cheguei nele por horario de run e nome de arquivo,
    # o que e' inferencia minha, nao dado do sistema.
    #
    # Falha ABERTA: se a consulta do nome nao vier, o download segue. Perder a
    # origem incomoda; perder o corte, nao.
    try:
        meta = servico.files().get(fileId=file_id, fields="name").execute()
        from pathlib import Path as _P
        _P(destino).with_suffix(".origem.txt").write_text(
            meta.get("name", ""), encoding="utf-8")
        print(f"  nome no Drive: {meta.get('name','')[:70]}")
    except Exception as e:
        print(f"  [aviso] nome do arquivo indisponivel ({str(e)[:50]})")

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
    p.add_argument("--conta", default="principal",
                   help="conta do Drive onde o bruto está (ver contas_drive.py)")
    a = p.parse_args()
    baixar(a.file_id, a.destino, a.conta)


if __name__ == "__main__":
    main()
