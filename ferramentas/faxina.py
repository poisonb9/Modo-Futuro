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
| trabalho/brutos/                    | 3 dias E so' se o Drive tiver igual |
| ~/Downloads/abastecer/*.mp4 (orfao) | 1 dia E so' se o Drive tiver igual |
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
BAIXADOS = Path.home() / "Downloads" / "abastecer"   # o mesmo do abastecer_loop


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
    # ⭐ 07/10/2026: o JDownloader do abastecer_loop deixa .mp4 ORFAO quando o
    # vídeo não está nos `pendentes` (JD caiu na hora do addLinks, ou baixou de
    # novo um link já enviado). O loop nunca sobe nem apaga esses: achados
    # 2 parados (565 MB) com o disco em 1,8 GB livres.
    for f in (BAIXADOS.rglob("*.mp4") if raiz == RAIZ and BAIXADOS.exists() else []):
        if _idade_dias(f) >= 1:
            out.append(("mp4 orfao do JDownloader", f, _tam(f)))
    saida = raiz / "saida"
    if saida.exists():
        for d in saida.glob("teste_*"):
            if _idade_dias(d) >= dias_teste:
                out.append(("pasta de teste", d, _tam(d)))
    # nada fora do motor, nunca _privado/estado (defesa extra). ⚠️ Os DOIS
    # lados resolvidos: no Windows o mesmo caminho aparece curto (ADMINI~1) e
    # longo (Administrator), e comparar um de cada recusava tudo.
    r = raiz.resolve()
    b = BAIXADOS.resolve()
    return [(c, p, t) for c, p, t in out
            if b in p.resolve().parents or (r in p.resolve().parents
            and not {"_privado", "estado"} & set(p.resolve().relative_to(r).parts))]


def no_drive(f: Path, contas: list | None = None) -> str | None:
    """Conta onde existe um arquivo com o MESMO nome e o MESMO tamanho em
    bytes, ou None. Regra do dono: só apaga do PC o que está no Drive."""
    sys.path.insert(0, str(RAIZ))
    import contas_drive as cd
    nome = f.name.replace("\\", "\\\\").replace("'", "\\'")
    try:
        tam = f.stat().st_size
    except FileNotFoundError:      # outro processo já subiu e apagou
        return None
    for c in contas or cd.CONTAS:
        try:
            r = cd.servico(c).files().list(
                q=f"name='{nome}' and trashed=false", fields="files(size)").execute()
        except Exception:
            continue
        if any(int(x.get("size", -1)) == tam for x in r.get("files", [])):
            return c["nome"]
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apagar", action="store_true")
    ap.add_argument("--dias-brutos", type=float, default=3)
    a = ap.parse_args()
    lista = []
    for cat, p, t in candidatos(dias_brutos=a.dias_brutos):
        # ⭐ 07/10/2026: bruto/orfao só sai se o Drive tiver a cópia inteira.
        # Antes saía pela idade: 16 brutos de trabalho/brutos (3,4 GB) NUNCA
        # tinham subido (baixar_em_intervalos não sobe, de propósito).
        if cat in ("bruto antigo", "mp4 orfao do JDownloader"):
            if not no_drive(p):
                print(f"  [mantido: NAO esta' no Drive] {p.name[:70]}")
                continue
        lista.append((cat, p, t))
    if not lista:
        print("Nada a limpar.")
        return
    total = 0
    for cat, p, t in sorted(lista, key=lambda x: -x[2]):
        total += t
        print(f"  {t / 1e6:9.1f} MB  {cat:24}  {p.name if BAIXADOS.resolve() in p.resolve().parents else p.resolve().relative_to(RAIZ.resolve())}")
    print(f"  {total / 1e6:9.1f} MB  TOTAL")
    if not a.apagar:
        print("\n(so' mostrei. Para apagar: --apagar)")
        return
    for _, p, _ in lista:
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        else:
            p.unlink(missing_ok=True)
    print(f"\nApagado: {total / 1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
