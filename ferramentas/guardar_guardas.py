# -*- coding: utf-8 -*-
"""Grava as guardas do corte (registro_clipes.json, estado/trechos_usados.json)
no repo SEM perder para quem escreveu ao mesmo tempo.

    python ferramentas/guardar_guardas.py registro_clipes.json estado/trechos_usados.json

Por que existe: em 28/09/2026 o corte do Coragem enfileirou os 5 clipes e
morreu no passo "Guardar as guardas" — `git pull --rebase` deu CONFLITO no
registro_clipes.json (outro run gravou no mesmo minuto) e o push nunca
aconteceu. Resultado: registro e trechos usados do Coragem perdidos.

Os dois arquivos sao dicionarios que so' CRESCEM (chave = clipe / trecho),
entao o conflito tem resposta certa: a uniao. Guardo a minha versao, volto
para o main de agora, somo as chaves (a minha vence na mesma folha) e tento
de novo — ate' 6 vezes, com espera aleatoria para dois runs nao baterem de novo.
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
import time
from pathlib import Path


def somar(deles, meu):
    if isinstance(deles, dict) and isinstance(meu, dict):
        out = dict(deles)
        for k, v in meu.items():
            out[k] = somar(deles[k], v) if k in deles else v
        return out
    return meu


def git(*a, ok=False) -> bool:
    r = subprocess.run(["git", *a])
    if r.returncode and not ok:
        raise SystemExit(f"git {' '.join(a)} falhou ({r.returncode})")
    return r.returncode == 0


def main(alvos: list[str]) -> None:
    meus = {}
    for f in alvos:
        p = Path(f)
        if p.exists():
            meus[f] = json.loads(p.read_text(encoding="utf-8"))
    if not meus:
        print("[!] nenhuma guarda escreveu nada — nada a guardar")
        return
    for tentativa in range(1, 7):
        git("fetch", "-q", "origin", "main")
        git("reset", "-q", "--hard", "origin/main")
        for f, meu in meus.items():
            p = Path(f)
            deles = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(somar(deles, meu), ensure_ascii=False, indent=1),
                         encoding="utf-8")
        git("add", *meus)
        if git("diff", "--cached", "--quiet", ok=True):
            print("guardas inalteradas")
            return
        git("commit", "-q", "-m", "guardas: trecho enfileirado e registro de clipe")
        if git("push", "-q", "origin", "HEAD:main", ok=True):
            print(f"guardas gravadas (tentativa {tentativa})")
            return
        espera = random.uniform(5, 20) * tentativa
        print(f"  push recusado (alguem gravou antes) — somo de novo em {espera:.0f}s")
        time.sleep(espera)
    raise SystemExit("guardas NAO gravadas depois de 6 tentativas")


if __name__ == "__main__":
    main(sys.argv[1:])
