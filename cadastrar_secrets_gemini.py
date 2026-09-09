# -*- coding: utf-8 -*-
"""Cadastra chaves GEMINI do `.env` como secrets do repositorio.

    python cadastrar_secrets_gemini.py               # so' as que faltam
    python cadastrar_secrets_gemini.py --todas       # reenvia todas
    python cadastrar_secrets_gemini.py --simular     # nao escreve nada

Irmao do `cadastrar_secrets_nvidia.py`, mesma mecanica: a chave e' cifrada
AQUI, nesta maquina, com a chave publica do repositorio. O GitHub nunca
recebe o valor em claro, e este script nunca imprime uma chave.

⚠️ POR QUE ELE EXISTE (medido em 09/09/2026).

O Gemini e' o gargalo da operacao — a cota diaria esgotou em 8 horas em
07/09. Comparando o `.env` com os secrets do repositorio descobriu-se que as
duas metades divergiram: havia chave na nuvem que nao existia no disco (as
"orfas") e, depois da recuperacao de 09/09, chave no disco que nao existia na
nuvem. Quem corta e' a NUVEM: chave que so' existe no disco nao aumenta cota
nenhuma.

⚠️ TOKEN: usa `github_token.txt` (o de 04/08, que tem escrita) e cai para o
`GITHUB_TOKEN` do `.env` se aquele nao existir. O do `.env` da' 403 em push —
se der 403 aqui tambem, e' o mesmo problema, nao e' o script.

⚠️ E a regra do CREDENCIAIS.md continua valendo, nesta ordem: chave nova entra
no DISCO primeiro, depois na nuvem. As 22 orfas de 08/09 sao a prova do que
acontece quando se faz ao contrario.
"""
import argparse
import base64
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO = "poisonb9/Modo-Futuro"
RAIZ = Path(__file__).resolve().parent


def _token() -> str:
    arq = RAIZ / "github_token.txt"
    if arq.exists():
        t = arq.read_text(encoding="utf-8").strip()
        if t:
            return t
    load_dotenv(RAIZ / ".env")
    t = (os.getenv("GITHUB_TOKEN") or "").strip()
    if not t:
        sys.exit("sem token: nem github_token.txt nem GITHUB_TOKEN no .env")
    return t


def _nomes_do_env() -> list[str]:
    """Os nomes GEMINI_* que existem no `.env`, em ordem numerica."""
    txt = (RAIZ / ".env").read_text(encoding="utf-8", errors="ignore")
    achados = re.findall(r"^(GEMINI_API_KEY(?:_(\d+))?)=", txt, re.M)
    return [n for n, _ in sorted(achados, key=lambda a: int(a[1] or 1))]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--todas", action="store_true",
                   help="reenvia todas, nao so' as que faltam na nuvem")
    p.add_argument("--simular", action="store_true")
    a = p.parse_args()

    load_dotenv(RAIZ / ".env")
    try:
        from nacl import encoding, public
    except ImportError:
        sys.exit("falta a biblioteca: pip install pynacl")

    token = _token()
    h = {"Authorization": f"Bearer {token}",
         "Accept": "application/vnd.github+json"}

    r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets"
                     "?per_page=100", headers=h, timeout=30)
    if r.status_code != 200:
        sys.exit(f"nao consegui listar os secrets: HTTP {r.status_code} — o "
                 f"token precisa de permissao de Secrets (write)")
    ja_na_nuvem = {s["name"] for s in r.json().get("secrets", [])}

    nomes = _nomes_do_env()
    alvo = nomes if a.todas else [n for n in nomes if n not in ja_na_nuvem]
    print(f"{len(nomes)} chave(s) GEMINI no .env · {len(ja_na_nuvem & set(nomes))} "
          f"ja' na nuvem · {len(alvo)} a enviar")
    if not alvo:
        print("nada a fazer.")
        return
    if a.simular:
        print("SIMULADO — nada escrito:", ", ".join(alvo))
        return

    r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
                     headers=h, timeout=30)
    if r.status_code != 200:
        sys.exit(f"nao consegui a chave publica: HTTP {r.status_code}")
    chave = r.json()
    caixa = public.SealedBox(public.PublicKey(chave["key"].encode(),
                                              encoding.Base64Encoder()))
    ok = 0
    for nome in alvo:
        valor = (os.getenv(nome) or "").strip()
        if not valor:
            print(f"  {nome:22} vazio no .env — pulado")
            continue
        cifrado = base64.b64encode(caixa.encrypt(valor.encode())).decode()
        rr = requests.put(
            f"https://api.github.com/repos/{REPO}/actions/secrets/{nome}",
            headers=h, json={"encrypted_value": cifrado,
                             "key_id": chave["key_id"]}, timeout=30)
        if rr.status_code in (201, 204):
            ok += 1
            print(f"  {nome:22} {'criado' if rr.status_code == 201 else 'atualizado'}")
        else:
            print(f"  {nome:22} FALHOU  HTTP {rr.status_code}  {rr.text[:90]}")

    print(f"\n{ok} de {len(alvo)} no ar.")
    print("⚠️ A prova nao e' esta saida: e' um corte rodando sem 'cota esgotada'.")


if __name__ == "__main__":
    main()
