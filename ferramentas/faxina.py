# -*- coding: utf-8 -*-
"""Faxina do disco do motor: o que é descartável e ocupa espaço.

    python -X utf8 ferramentas/faxina.py            so' MOSTRA (padrao)
    python -X utf8 ferramentas/faxina.py --apagar   apaga o que foi mostrado

## POR QUE EXISTE

Pedido do dono em 26/09/2026, ao subir o download para 1440p: "temos que ser
organizados para nao deixar lixo no pc, os arquivos sao grandes". Medido no
mesmo dia: `enviar_bruto_drive.enviar` tinha um `apagar_local` que ninguem
lia, e o `processar_lista` nunca apagava — toda copia enviada ao Drive ficava
no disco (882 MB de um so' bruto em trabalho/brutos).

Desde entao o envio apaga a copia depois de CONFERIR o tamanho no Drive. Esta
faxina pega o que sobra: download interrompido, bruto que nao chegou a subir,
intermediario de corte local, pasta de teste.

## REGRAS (idade = ultima modificacao)

| o que                               | sai depois de |
|-------------------------------------|---------------|
| download interrompido (*.part/.ytdl) | sempre        |
| trabalho/ intermediarios (fora brutos) | 1 dia       |
| trabalho/brutos/                    | 3 dias (o corte roda da copia no Drive) |
| saida/teste_*                        | 7 dias        |

⛔ NUNCA toca em `_privado/`, `estado/`, codigo, nem fora do motor.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIA = 86400


def _tam(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def _idade_dias(p: Path) -> float:
    return (time.time() - p.stat().st_mtime) / DIA


def candidatos(raiz: Path = RAIZ, dias_brutos: float = 3, dias_trabalho: float = 1,
               dias_teste: float = 7) -> list[tuple[str, Path, int]]:
    """[(categoria, caminho, bytes)] do que pode sair."""
    out = []
    trab = raiz / "trabalho"
    if trab.exists():
        for f in trab.rglob("*"):
            if f.is_file() and f.suffix in (".part", ".ytdl"):
                out.append(("download interrompido", f, _tam(f)))
        for item in trab.iterdir():
            if item.name == "brutos":
                continue
            if _idade_dias(item) >= dias_trabalho:
                out.append(("intermediario de corte", item, _tam(item)))
        brutos = trab / "brutos"
        if brutos.exists():
            for f in brutos.iterdir():
                if f.is_file() and f.suffix not in (".part", ".ytdl") \
                        and _idade_dias(f) >= dias_brutos:
                    out.append(("bruto antigo", f, _tam(f)))
    saida = raiz / "saida"
    if saida.exists():
        for d in saida.glob("teste_*"):
            if _idade_dias(d) >= dias_teste:
                out.append(("pasta de teste", d, _tam(d)))
    # nada fora do motor, nunca _privado/estado (defesa extra). ⚠️ Os DOIS
    # lados resolvidos: no Windows o mesmo caminho aparece curto (ADMINI~1) e
    # longo (Administrator), e comparar um de cada recusava tudo.
    r = raiz.resolve()
    return [(c, p, t) for c, p, t in out
            if r in p.resolve().parents
            and not {"_privado", "estado"} & set(p.resolve().relative_to(r).parts)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apagar", action="store_true")
    ap.add_argument("--dias-brutos", type=float, default=3)
    a = ap.parse_args()
    lista = candidatos(dias_brutos=a.dias_brutos)
    if not lista:
        print("Nada a limpar.")
        return
    total = 0
    for cat, p, t in sorted(lista, key=lambda x: -x[2]):
        total += t
        print(f"  {t / 1e6:9.1f} MB  {cat:24}  {p.resolve().relative_to(RAIZ.resolve())}")
    print(f"  {total / 1e6:9.1f} MB  TOTAL")
    if not a.apagar:
        print("\n(so' mostrei. Para apagar: --apagar)")
        return
    for _, p, _ in lista:
        (shutil.rmtree if p.is_dir() else Path.unlink)(p)
    print(f"\nApagado: {total / 1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
