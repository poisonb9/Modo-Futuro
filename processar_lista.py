"""Baixa uma lista de vídeos em sequência, sobe cada um bruto pro
Drive, e dispara o corte na nuvem (GitHub Actions) pra cada um —
tudo automático depois de colar a lista.

Uso:
    1. Coloque uma URL por linha em lista_videos.txt (nesta pasta)
    2. python processar_lista.py

Precisa de:
    - GITHUB_TOKEN no .env (Personal Access Token com permissão
      Actions: Read and write, Contents: Read and write)
    - yt-dlp, e o resto das dependências do clip_engine já instaladas
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

RAIZ = Path(__file__).resolve().parent
LISTA = RAIZ / "lista_videos.txt"
PASTA_DRIVE = "1uYzc71yxlYvl-aJeTFf0whDuwDXVoXxU"
REPO = "poisonb9/Modo-Futuro"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def _roda(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
        raise RuntimeError(f"falhou: {' '.join(cmd[:3])}...")
    return r.stdout


def baixar(url: str, destino: Path):
    destino.parent.mkdir(parents=True, exist_ok=True)
    _roda([
        "yt-dlp", "-f", "bv*[height<=480]+ba/b[height<=480]/b",
        "--extractor-args", "youtube:player_client=android",
        "--merge-output-format", "mp4",
        "-o", str(destino), url,
    ])


def subir_bruto(arquivo: Path) -> str:
    saida = _roda([sys.executable, "-X", "utf8", "enviar_bruto_drive.py",
                    "--arquivo", str(arquivo), "--pasta-id", PASTA_DRIVE])
    for linha in saida.splitlines():
        if linha.startswith("DRIVE_FILE_ID="):
            return linha.split("=", 1)[1].strip()
    raise RuntimeError("não achei o DRIVE_FILE_ID na saída")


def disparar_corte(file_id: str, nome_arquivo: str, idioma: str = "pt"):
    if not GITHUB_TOKEN:
        print("   [!] Falta GITHUB_TOKEN no .env — não disparei o corte automaticamente."
              " Rode manualmente no GitHub Actions (workflow cortar_de_bruto.yml).")
        return
    r = requests.post(
        f"https://api.github.com/repos/{REPO}/actions/workflows/cortar_de_bruto.yml/dispatches",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}",
                 "Accept": "application/vnd.github+json"},
        json={"ref": "main", "inputs": {
            "drive_file_id": file_id, "nome_arquivo": nome_arquivo,
            "qtd": "8", "idioma": idioma, "pasta_drive": PASTA_DRIVE,
        }},
    )
    if r.status_code != 204:
        print(f"   [!] falha ao disparar: {r.status_code} {r.text}")
    else:
        print("   corte disparado na nuvem.")


def main():
    if not LISTA.exists():
        LISTA.write_text("# uma URL do YouTube por linha\n", encoding="utf-8")
        sys.exit(f"Criei {LISTA} — cole as URLs (uma por linha) e rode de novo.")

    urls = [l.strip() for l in LISTA.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]
    if not urls:
        sys.exit(f"{LISTA} está vazio — cole as URLs primeiro.")

    print(f"{len(urls)} vídeo(s) na lista.\n")
    for i, url in enumerate(urls, 1):
        print(f"\n=== [{i}/{len(urls)}] {url} ===")
        nome = f"video_{i}.mp4"
        destino = RAIZ / "trabalho" / "lista" / nome
        try:
            baixar(url, destino)
            file_id = subir_bruto(destino)
            disparar_corte(file_id, nome)
        except Exception as e:
            print(f"   [!] falhou, pulando pro próximo: {e}")
            continue
        time.sleep(2)

    print("\nLista processada. Acompanhe o progresso no Telegram.")


if __name__ == "__main__":
    main()
