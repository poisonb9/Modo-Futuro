# -*- coding: utf-8 -*-
"""Entre as fotos de um anuncio, qual e' a que NAO e' banner — e E' o produto.

## O PROBLEMA (MAESTROS_DESIGN_DO_SITE.md, defeito 1, 18/09/2026)

A foto principal do AliExpress e' a que o lojista escolhe pra competir na
busca: "22 colors available~", "STRONG MAGNETIC FORCE", caixa com selo.
Num cartao escuro e limpo isso e' o banner que os Maestros mandam tirar da
pagina de produto (Analista de Loja Virtual EP.2). O `precos.py` guarda as
outras fotos do anuncio (`imagens`); este modulo escolhe.

## ⛔ O QUE NAO FUNCIONOU, medido no mesmo dia

1. O vetor da dedupe (`fidelidade._vetor`) RECORTA o produto antes de
   embutir: o texto do banner fica fora do recorte, e a balanca "Simple but
   not simplistic" saiu como a mais limpa.
2. Embedding da imagem INTEIRA contra a frase "foto limpa": olhado em 18
   produtos, 3 de 8 trocas PIORES — escolheu a PLACA DE MONTAGEM no lugar do
   teclado, a bolsa PRETA no lugar da marrom, uma foto com texto "One-handed
   operation". A nota media "parece foto de produto" e nao "e' ESTE produto
   sem texto". Reprovou no caso negativo; ficou desligado.

## ⭐ O QUE MEDE AGORA — duas medidas, na NUVEM

Ordem do Bryan (18/09): nada instalado na maquina; OCR no GitHub da conta
parada. `bryanaw2121-sketch/pipeline/.github/workflows/fotos_ocr.yml` roda
EasyOCR + CLIP e devolve, por foto:

    texto  fracao da area coberta por letras (0-1)
    fid    cosseno CLIP contra a foto PRINCIPAL do mesmo anuncio

Sem segredo: a lista vai por input do dispatch, o resultado volta por
artifact (`gh run download`) e fica em `estado/fotos_ocr.json` (versionado:
os dois clones e a nuvem leem o mesmo).

## A REGRA, calibrada nos 18 produtos vistos a olho (run 35356232292)

Troca a principal por uma extra SO' se:
  - a principal tem texto (`texto` > TEXTO_PRINCIPAL_MIN) — bolsa e oculos
    tinham 0,0 e nao havia o que trocar (era onde a v1 errava);
  - a extra e' O MESMO produto: `fid` >= FID_MIN. Medido: as fotos da placa
    de montagem do teclado ficam em 0,32-0,58; fotos boas do mesmo produto,
    0,61-0,92. ⚠️ Margem FINA (0,584 x 0,62): por isso o piso e' 0,62 e nao
    0,60, e uma foto boa da luva (0,61) fica de fora — errar pra ficar com a
    principal e' o erro barato;
  - a extra tem menos texto por MARGEM_TEXTO (senao e' ruido trocando foto a
    cada publicacao).
Entre as que passam, a de MENOS texto. Resultado nos 18: troca luva,
carregador e ventosa (as tres que o olho aprovou); mantem teclado, tesla,
fone, balanca "Simple" (sem extra melhor) e todas as que ja' eram limpas.

⚠️ Falha ABERTA: foto sem medida (nao medida ainda, erro no OCR) nao
concorre; principal sem medida fica. Foto pior e' feia; cartao sem foto e'
quebrado.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MEDIDAS = RAIZ / "estado" / "fotos_ocr.json"

REPO_OCR = "bryanaw2121-sketch/pipeline"
WORKFLOW_OCR = "fotos_ocr.yml"
PREFIXO = "https://ae-pic-a1.aliexpress-media.com/kf/"

TEXTO_PRINCIPAL_MIN = 0.05
FID_MIN = 0.62
MARGEM_TEXTO = 0.03


def medidas() -> dict:
    if not MEDIDAS.exists():
        return {}
    try:
        return json.loads(MEDIDAS.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def _boa(m: dict | None) -> bool:
    return bool(m) and "erro" not in m and m.get("texto") is not None


def escolher(principal: str, extras: list[str], med: dict | None = None) -> str:
    """A foto do cartao. Ver a regra no cabecalho."""
    if not extras:
        return principal
    med = medidas() if med is None else med
    mp = med.get(principal)
    if not _boa(mp) or mp["texto"] <= TEXTO_PRINCIPAL_MIN:
        return principal
    melhor, melhor_texto = principal, mp["texto"]
    for u in extras:
        m = med.get(u)
        if not _boa(m) or (m.get("fid") or 0) < FID_MIN:
            continue
        if m["texto"] <= mp["texto"] - MARGEM_TEXTO and m["texto"] < melhor_texto:
            melhor, melhor_texto = u, m["texto"]
    return melhor


def _fotos_do_catalogo() -> dict[str, list[str]]:
    """{id: [principal, extras...]} do instantaneo + registro; so' as URLs
    com o PREFIXO (o input do dispatch e' um sufixo por foto)."""
    from . import precos
    agora = precos.ler_instantaneo()
    arq = RAIZ / "estado" / "produtos_publicados.jsonl"
    principal: dict[str, str] = {}
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(linha)
            except ValueError:
                continue
            if d.get("id") and d.get("imagem"):
                principal.setdefault(str(d["id"]), d["imagem"])
    saida = {}
    for pid, v in agora.items():
        p = principal.get(pid)
        ex = v.get("imagens") or []
        if not p or not ex:
            continue
        urls = [p] + [u for u in ex if u != p]
        if all(u.startswith(PREFIXO) for u in urls):
            saida[pid] = urls
    return saida


def pendentes() -> dict[str, list[str]]:
    """Os anuncios com alguma foto ainda sem medida."""
    med = medidas()
    return {pid: urls for pid, urls in _fotos_do_catalogo().items()
            if any(u not in med for u in urls)}


def medir(esperar: bool = True, timeout_min: int = 90) -> int:
    """Dispara o OCR na nuvem pros pendentes, espera, baixa e grava.
    Devolve quantas fotos entraram. Sem pendentes, nao dispara nada."""
    pend = pendentes()
    if not pend:
        print("fotos: nada pendente de medir")
        return 0
    lista = {pid: [u[len(PREFIXO):] for u in urls] for pid, urls in pend.items()}
    corpo = json.dumps(lista, separators=(",", ":"))
    # ⚠️ o input do dispatch tem teto (~64 KB): em lotes de 120 anuncios
    ids = list(lista)
    entrou = 0
    shell = (sys.platform == "win32")
    for i in range(0, len(ids), 120):
        parte = {k: lista[k] for k in ids[i:i + 120]}
        corpo = json.dumps(parte, separators=(",", ":"))
        antes = time.time()
        subprocess.run(["gh", "workflow", "run", WORKFLOW_OCR, "-R", REPO_OCR,
                        "-f", f"prefixo={PREFIXO}", "-f", f"lista={corpo}"],
                       check=True, capture_output=True, shell=shell)
        print(f"fotos: disparado lote {i // 120 + 1} ({len(parte)} anuncios, "
              f"{sum(len(v) for v in parte.values())} fotos)")
        if not esperar:
            continue
        time.sleep(20)
        run_id = _run_mais_novo(antes)
        if not run_id:
            print("fotos: [!] nao achei o run disparado")
            continue
        fim = time.time() + timeout_min * 60
        while time.time() < fim:
            st = subprocess.run(["gh", "run", "view", run_id, "-R", REPO_OCR,
                                 "--json", "status,conclusion", "-q",
                                 '"\\(.status) \\(.conclusion)"'],
                                capture_output=True, text=True, shell=shell).stdout.strip()
            if st.startswith("completed"):
                break
            time.sleep(45)
        else:
            print(f"fotos: [!] run {run_id} nao terminou em {timeout_min} min")
            continue
        if "success" not in st:
            print(f"fotos: [!] run {run_id}: {st}")
            continue
        entrou += _baixar_e_gravar(run_id)
    return entrou


def _run_mais_novo(desde: float) -> str:
    shell = (sys.platform == "win32")
    r = subprocess.run(["gh", "run", "list", "-R", REPO_OCR, "-w", WORKFLOW_OCR,
                        "-L", "3", "--json", "databaseId,createdAt"],
                       capture_output=True, text=True, shell=shell)
    try:
        runs = json.loads(r.stdout or "[]")
    except ValueError:
        return ""
    from datetime import datetime, timezone
    for x in runs:
        t = datetime.fromisoformat(x["createdAt"].replace("Z", "+00:00")).timestamp()
        if t >= desde - 60:
            return str(x["databaseId"])
    return ""


def _baixar_e_gravar(run_id: str) -> int:
    import shutil
    import tempfile
    shell = (sys.platform == "win32")
    pasta = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["gh", "run", "download", run_id, "-R", REPO_OCR,
                        "-n", "fotos_ocr", "-D", str(pasta)],
                       check=True, capture_output=True, shell=shell)
        novo = json.loads((pasta / "fotos_ocr.json").read_text(encoding="utf-8"))
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
    med = medidas()
    # ⚠️ erro de OCR nao apaga medida boa anterior; e medida boa nova substitui
    n = 0
    for u, m in novo.items():
        if "erro" in m and _boa(med.get(u)):
            continue
        med[u] = m
        n += 1
    MEDIDAS.parent.mkdir(parents=True, exist_ok=True)
    MEDIDAS.write_text(json.dumps(med, ensure_ascii=False, separators=(",", ":")),
                       encoding="utf-8")
    print(f"fotos: {n} medida(s) gravadas em {MEDIDAS.name} (total {len(med)})")
    return n


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--medir", action="store_true", help="dispara o OCR na nuvem e grava")
    p.add_argument("--pendentes", action="store_true", help="so' conta o que falta")
    a = p.parse_args()
    if a.pendentes or not a.medir:
        pend = pendentes()
        print(f"{len(pend)} anuncio(s) com foto sem medida, "
              f"{sum(len(v) for v in pend.values())} fotos")
        return
    medir()


if __name__ == "__main__":
    main()
