# -*- coding: utf-8 -*-
"""Cadastra as chaves NVIDIA como secrets do repositorio.

    python cadastrar_secrets_nvidia.py

Le' do `.env` local e escreve em Settings > Secrets and variables > Actions.
As chaves sao cifradas aqui, na sua maquina, antes de subir — o GitHub nunca
recebe o valor em claro.

⚠️ POR QUE ISTO E' NECESSARIO. A reserva de traducao (Nemotron) existe no
codigo desde 02/09/2026, mas caiu no primeiro run real com "Nenhuma chave
NVIDIA_API_KEY encontrada": o workflow passa as variaveis, e os secrets nao
existiam. Secret ausente vira string vazia e o rodizio ignora vazio — entao a
reserva fica inerte EM SILENCIO, sem erro nenhum.

Depois de rodar, a prova de que funcionou e' esta linha no log de um corte
que tenha esgotado o Gemini:

    [reserva] Gemini sem cota — traduzido pelo Nemotron Ultra
"""
import base64
import os
import sys

import requests
from dotenv import load_dotenv

REPO = "poisonb9/Modo-Futuro"
NOMES = ["NVIDIA_API_KEY"] + [f"NVIDIA_API_KEY_{i}" for i in range(2, 6)]


def main() -> None:
    load_dotenv(".env")
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("falta GITHUB_TOKEN no .env")
    try:
        from nacl import encoding, public
    except ImportError:
        sys.exit("falta a biblioteca: pip install pynacl")

    h = {"Authorization": f"Bearer {token}",
         "Accept": "application/vnd.github+json"}
    r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
                     headers=h, timeout=30)
    if r.status_code != 200:
        sys.exit(f"nao consegui a chave publica do repo: HTTP {r.status_code} "
                 f"— o GITHUB_TOKEN precisa de permissao de Secrets (write)")
    chave = r.json()
    pk = public.PublicKey(chave["key"].encode(), encoding.Base64Encoder())
    caixa = public.SealedBox(pk)

    ok = 0
    for nome in NOMES:
        valor = (os.getenv(nome) or "").strip()
        if not valor:
            print(f"  {nome:20} ausente no .env — pulado")
            continue
        cifrado = base64.b64encode(caixa.encrypt(valor.encode())).decode()
        rr = requests.put(
            f"https://api.github.com/repos/{REPO}/actions/secrets/{nome}",
            headers=h, json={"encrypted_value": cifrado,
                             "key_id": chave["key_id"]}, timeout=30)
        # 201 = criado, 204 = atualizado
        if rr.status_code in (201, 204):
            ok += 1
            print(f"  {nome:20} {'criado' if rr.status_code == 201 else 'atualizado'}")
        else:
            print(f"  {nome:20} FALHOU  HTTP {rr.status_code}  {rr.text[:90]}")

    print(f"\n{ok} de {len(NOMES)} secrets no ar.")
    if ok:
        print("A reserva de traducao so' entra quando o Gemini esgotar. "
              "A prova e' a linha '[reserva] ... Nemotron Ultra' no log do corte.")


if __name__ == "__main__":
    main()
