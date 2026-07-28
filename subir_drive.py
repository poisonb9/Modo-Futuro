"""Sobe os clipes prontos pro Google Drive, organizados por nota nas
subpastas 7/8/9, com a legenda num .txt ao lado (pro iPhone: baixa o vídeo
+ abre o txt e cola no TikTok).

Existe como alternativa ao rascunho via API quando a fila do TikTok trava
(ver sabedoria/SABEDORIA_TIKTOK.md, "REGRA DE OURO").

    python subir_drive.py --pasta-id 1uYzc71yxlYvl-aJeTFf0whDuwDXVoXxU

Reaproveita o client_secrets.json já usado pro YouTube (publicar.py), mas
com escopo Drive e token separado (token_drive.json) — não mistura com o
token.json do YouTube.
"""
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import config
from engine import telegram
from publicar_tiktok import legenda_do_clipe

SCOPES = ["https://www.googleapis.com/auth/drive"]
CLIENT_SECRETS = config.RAIZ / "client_secrets.json"
TOKEN = config.RAIZ / "token_drive.json"
REGISTRO = config.RAIZ / "estado" / "enviados_drive.json"


def _servico():
    from googleapiclient.discovery import build

    # No GitHub Actions (ou qualquer ambiente sem tela pra login manual),
    # usa Service Account via variável de ambiente — nada de OAuth
    # interativo. Local continua exatamente como sempre foi (abaixo).
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        from google.oauth2 import service_account
        info = json.loads(sa_json)
        cred = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return build("drive", "v3", credentials=cred)

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    cred = None
    if TOKEN.exists():
        cred = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            if not CLIENT_SECRETS.exists():
                sys.exit(f"Falta {CLIENT_SECRETS}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            cred = flow.run_local_server(port=0)
        TOKEN.write_text(cred.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=cred)


def _chave(clipe: Path) -> str:
    return f"{clipe.parent.parent.name}/{clipe.name}"


def _enviados() -> set[str]:
    if not REGISTRO.exists():
        return set()
    return set(json.loads(REGISTRO.read_text(encoding="utf-8")))


def _marcar(chave: str):
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    atual = _enviados()
    atual.add(chave)
    REGISTRO.write_text(json.dumps(sorted(atual), ensure_ascii=False, indent=2), encoding="utf-8")


def fila_pendente_drive() -> list[tuple[float, Path]]:
    """Igual à fila do TikTok (mesmo critério de nota/lote ignorado), mas com
    registro PRÓPRIO — subir pro Drive não marca como enviado pro TikTok e
    vice-versa, são filas independentes."""
    ja = _enviados()
    achados = []
    for pj in config.SAIDA.rglob("post.json"):
        clipe = pj.parent
        lote = clipe.parent.parent.name
        if lote in config.LOTES_IGNORADOS:
            continue
        if not (clipe / "short_9x16.mp4").exists():
            continue
        if _chave(clipe) in ja:
            continue
        try:
            nota = float(json.loads(pj.read_text(encoding="utf-8")).get("nota", 0))
        except Exception:
            nota = 0.0
        achados.append((nota, clipe))
    achados.sort(key=lambda x: -x[0])
    return achados


def _pasta_por_nota(nota: float) -> str:
    if nota >= 90:
        return "9"
    if nota >= 80:
        return "8"
    return "7"


def _achar_subpasta(servico, pai_id: str, nome: str) -> str:
    q = (f"'{pai_id}' in parents and name = '{nome}' "
         "and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
    r = servico.files().list(q=q, fields="files(id, name)").execute()
    arquivos = r.get("files", [])
    if not arquivos:
        sys.exit(f"Não achei a subpasta '{nome}' dentro da pasta {pai_id}. "
                  f"Confira se ela existe e se a conta do Google usada no login "
                  f"tem acesso.")
    return arquivos[0]["id"]


def _achar_ou_criar_subpasta(servico, pai_id: str, nome: str) -> str:
    """Igual a _achar_subpasta, mas cria a pasta se não existir — usado pra
    pasta do dia (ex: '26-07') dentro de cada pasta de nota."""
    q = (f"'{pai_id}' in parents and name = '{nome}' "
         "and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
    r = servico.files().list(q=q, fields="files(id, name)").execute()
    arquivos = r.get("files", [])
    if arquivos:
        return arquivos[0]["id"]
    meta = {"name": nome, "mimeType": "application/vnd.google-apps.folder", "parents": [pai_id]}
    nova = servico.files().create(body=meta, fields="id").execute()
    return nova["id"]


def _upload(servico, pasta_id: str, caminho: Path, mimetype: str):
    from googleapiclient.http import MediaFileUpload
    meta = {"name": caminho.name, "parents": [pasta_id]}
    media = MediaFileUpload(str(caminho), mimetype=mimetype, resumable=True)
    servico.files().create(body=meta, media_body=media, fields="id").execute()


def subir(pasta_pai_id: str, avisar_telegram: bool = True):
    fila = fila_pendente_drive()
    if not fila:
        print("Nada pendente pra subir no Drive.")
        return

    print(f"{len(fila)} clipe(s) pra subir.\n")
    servico = _servico()
    pastas_nota = {n: _achar_subpasta(servico, pasta_pai_id, n) for n in ("7", "8", "9")}
    hoje = date.today().strftime("%d-%m")
    pastas_dia = {n: _achar_ou_criar_subpasta(servico, pastas_nota[n], hoje) for n in ("7", "8", "9")}

    enviados = 0
    for nota, clipe in fila:
        video = clipe / "short_9x16.mp4"
        alvo = _pasta_por_nota(nota)
        legenda = legenda_do_clipe(clipe)

        txt = clipe / "_legenda_drive.txt"
        txt.write_text(legenda, encoding="utf-8")

        nome_video = f"nota{int(nota)}_{clipe.name}.mp4"
        nome_txt = f"nota{int(nota)}_{clipe.name}.txt"
        print(f"  [pasta {alvo}/{hoje}] nota {nota:.0f}  {clipe.name}")
        try:
            _upload_renomeado(servico, pastas_dia[alvo], video, nome_video, "video/mp4")
            _upload_renomeado(servico, pastas_dia[alvo], txt, nome_txt, "text/plain")
        finally:
            txt.unlink(missing_ok=True)

        _marcar(_chave(clipe))
        if avisar_telegram:
            telegram.enviar(f"[Drive · pasta {alvo}/{hoje}] {legenda}")
        enviados += 1

    print(f"\n{enviados} clipe(s) enviado(s) pro Drive"
          f"{' (legendas mandadas pro Telegram)' if avisar_telegram else ''}.")


def _upload_renomeado(servico, pasta_id: str, caminho: Path, nome: str, mimetype: str):
    from googleapiclient.http import MediaFileUpload
    meta = {"name": nome, "parents": [pasta_id]}
    media = MediaFileUpload(str(caminho), mimetype=mimetype, resumable=True)
    servico.files().create(body=meta, media_body=media, fields="id").execute()


def main():
    p = argparse.ArgumentParser(description="Sobe os clipes prontos pro Google Drive, por nota")
    p.add_argument("--pasta-id", required=True,
                   help="ID da pasta pai do Drive (a que tem as subpastas 7/8/9)")
    p.add_argument("--sem-telegram", action="store_true",
                   help="não manda as legendas pro Telegram")
    a = p.parse_args()
    subir(a.pasta_id, avisar_telegram=not a.sem_telegram)


if __name__ == "__main__":
    main()
