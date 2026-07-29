"""Vigia a pasta RAW do Drive e dispara o corte na nuvem pra cada vídeo
novo que aparecer — fecha o ciclo sem ninguém precisar apertar nada.

    python vigia_raw.py              # fica rodando, checa a cada 5 min
    python vigia_raw.py --uma-vez    # checa uma vez e sai (pra Agendador)
    python vigia_raw.py --listar     # só mostra o que RAW tem e o que já foi

O que ele considera "novo": arquivo de vídeo em RAW cujo ID não está em
estado/raw_vistos.json. O nome não entra na conta — renomear no Drive não
faz reprocessar, e dois arquivos de mesmo nome não se confundem.

Por que ele mexe em permissão: a Service Account do GitHub Actions não
enxerga arquivo subido por login OAuth pessoal, nem dentro de pasta
compartilhada (404 "File not found", visto em 28/07/2026). Vídeo que você
arrastou pro Drive na mão cai nesse caso, então o vigia abre leitura por
link antes de disparar — mesma coisa que o enviar_bruto_drive.py já faz.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

RAIZ = Path(__file__).resolve().parent
REGISTRO = RAIZ / "estado" / "raw_vistos.json"
CLIENT_SECRETS = RAIZ / "client_secrets.json"
TOKEN = RAIZ / "token_drive.json"

PASTA_RAW = "1gUK_okgnHg-V1MDyM90ffnFe4dqIYV2g"
# Onde os clipes prontos aterrissam: dentro de 'A POSTAR' nasce a pasta do
# dia (ex: 28-07). Apontar pra raiz 'tiktok' faria a pasta do dia aparecer
# ao lado de RAW, misturando entrada com saída.
PASTA_DRIVE = "1k8fh9qZPxEkr64IK1TIpucdSstVDxDFO"  # A POSTAR
REPO = "poisonb9/Modo-Futuro"
WORKFLOW = "cortar_de_bruto.yml"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

INTERVALO_S = 300

# Voltou pra 8 em 29/07/2026, depois que o Bryan aprovou a rodada de prova
# ("rodou liso, legenda boa, tudo certo"). Ficou em "1" durante o teste das
# cinco mudanças de qualidade — fonte 1080p, tracking em rampa, legenda a
# 30%, punch-in cíclico e volume -14 LUFS.
QTD_CLIPES = "8"
IDIOMA = "pt"

SCOPES = ["https://www.googleapis.com/auth/drive"]
EXTS = {".mp4", ".mkv", ".mov", ".webm", ".m4v"}


# ------------------------------------------------------------------ drive

def servico():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

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


def _filhos(drive, pasta_id: str) -> list[dict]:
    """Itens diretos de uma pasta, paginando até o fim."""
    itens, pagina = [], None
    while True:
        r = drive.files().list(
            q=f"'{pasta_id}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,size,mimeType,modifiedTime)",
            orderBy="modifiedTime", pageToken=pagina, pageSize=100,
        ).execute()
        itens.extend(r.get("files", []))
        pagina = r.get("nextPageToken")
        if not pagina:
            return itens


def videos_em_raw(drive, profundidade_max: int = 3) -> list[dict]:
    """Vídeos na RAW, **inclusive dentro de subpastas**.

    Antes só olhava os filhos diretos e pulava pasta. Em 28/07/2026 o Bryan
    subiu os vídeos em `RAW/2026-07-28/` e o vigia não enxergava nada —
    reportava "nada novo" indefinidamente, sem erro nenhum, que é o pior
    tipo de falha: silenciosa.

    Desce até `profundidade_max` níveis. O teto existe porque cada pasta
    custa uma chamada de API: sem ele, uma árvore grande (ou um atalho
    circular do Drive) viraria enxurrada de requisições.
    """
    achados: list[dict] = []
    vistos: set[str] = set()
    fila = [(PASTA_RAW, "")]          # (id da pasta, caminho legível)

    for _ in range(profundidade_max):
        if not fila:
            break
        proxima: list[tuple[str, str]] = []
        for pasta_id, caminho in fila:
            if pasta_id in vistos:    # atalho circular não trava o vigia
                continue
            vistos.add(pasta_id)
            for f in _filhos(drive, pasta_id):
                if f["mimeType"].endswith("folder"):
                    proxima.append((f["id"], f"{caminho}{f['name']}/"))
                elif Path(f["name"]).suffix.lower() in EXTS:
                    f["caminho"] = caminho    # ex.: "2026-07-28/", só pro log
                    achados.append(f)
        fila = proxima

    return achados


def liberar_leitura(drive, file_id: str):
    """Abre leitura por link pra Service Account do Actions conseguir baixar.
    Se já estiver liberado, o Drive só devolve a permissão existente."""
    try:
        drive.permissions().create(
            fileId=file_id, body={"type": "anyone", "role": "reader"}).execute()
    except Exception as e:
        print(f"   [!] não consegui abrir leitura ({e}); o corte pode dar 404")


# --------------------------------------------------------------- registro

def ler_registro() -> dict:
    if not REGISTRO.exists():
        return {}
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[!] {REGISTRO.name} ilegível, tratando tudo como novo.")
        return {}


def marcar(file_id: str, dados: dict):
    reg = ler_registro()
    reg[file_id] = dados
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRO.with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(REGISTRO)


# ----------------------------------------------------------------- github

def disparar(file_id: str, nome: str):
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "Falta GITHUB_TOKEN no .env — sem ele não dá pra disparar o corte. "
            "Crie um PAT com Actions: Read and write, Contents: Read and write."
        )
    r = requests.post(
        f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}",
                 "Accept": "application/vnd.github+json"},
        json={"ref": "main", "inputs": {
            "drive_file_id": file_id, "nome_arquivo": nome,
            "qtd": QTD_CLIPES, "idioma": IDIOMA, "pasta_drive": PASTA_DRIVE,
        }},
        timeout=30,
    )
    if r.status_code != 204:
        raise RuntimeError(f"disparo falhou: {r.status_code} {r.text[:300]}")


# ------------------------------------------------------------------ ciclo

def uma_passada(drive) -> int:
    reg = ler_registro()
    novos = [v for v in videos_em_raw(drive) if v["id"] not in reg]
    if not novos:
        return 0
    print(f"{len(novos)} vídeo(s) novo(s) em RAW:")
    for v in novos:
        tam = int(v.get("size", 0)) / 2**30
        print(f"  - {v.get('caminho', '')}{v['name']} ({tam:.2f} GB)")
        try:
            liberar_leitura(drive, v["id"])
            disparar(v["id"], v["name"])
        except Exception as e:
            # Não marca: na próxima passada ele tenta de novo.
            print(f"   [!] falhou, fica pra próxima passada: {e}")
            continue
        marcar(v["id"], {"nome": v["name"], "tamanho": v.get("size"),
                         "quando": time.strftime("%Y-%m-%d %H:%M:%S")})
        print("   corte disparado na nuvem.")
    return len(novos)


def main():
    p = argparse.ArgumentParser(description="Vigia a pasta RAW do Drive")
    p.add_argument("--uma-vez", action="store_true", help="checa uma vez e sai")
    p.add_argument("--listar", action="store_true", help="só mostra o estado atual")
    p.add_argument("--intervalo", type=int, default=INTERVALO_S)
    a = p.parse_args()

    drive = servico()

    if a.listar:
        reg = ler_registro()
        vids = videos_em_raw(drive)
        print(f"RAW tem {len(vids)} vídeo(s):")
        for v in vids:
            marca = "já processado" if v["id"] in reg else "NOVO"
            print(f"  [{marca}] {v['name']}")
        return

    if a.uma_vez:
        n = uma_passada(drive)
        print("Nada novo." if not n else f"{n} disparado(s).")
        return

    print(f"Vigiando RAW a cada {a.intervalo}s. Ctrl+C pra parar.")
    while True:
        try:
            if not uma_passada(drive):
                print(f"[{time.strftime('%H:%M:%S')}] nada novo.")
        except KeyboardInterrupt:
            print("\nParei.")
            return
        except Exception as e:
            # Rede caiu, token expirou, Drive fora do ar: espera e insiste.
            print(f"[!] passada falhou ({e}); tento de novo no próximo ciclo.")
        time.sleep(a.intervalo)


if __name__ == "__main__":
    main()
