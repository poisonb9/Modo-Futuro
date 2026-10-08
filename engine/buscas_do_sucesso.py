# -*- coding: utf-8 -*-
"""Buscas extras para o radar de cada canal, tiradas do que MAIS PERFORMOU nele.

08/10/2026 (dono: "amplia o radar com base nos dados dos canais ... seja
estrategico" +acervo). O acervo e' unanime: achado o tema/formato que trouxe
alcance, DOBRAR A APOSTA nele (maestros: "Produzir mais conteudo semelhante";
"redobre os recursos naquele tema, criando conteudo de acompanhamento com
novos angulos"; "procure videos outliers ... e reproduza dentro do seu nicho").

Como:
  1. Ultimo retrato de cada post em `desempenho.jsonl` (o GitHub grava todo
     dia; views do Buffer vem null, entao a nota e' ALCANCE + 20 x CURTIDA).
  2. Os 8 melhores dos ultimos 30 dias (fora as ultimas 24 h, ainda sem numero).
  3. Nemotron (NVIDIA) transforma os titulos em 8 buscas em INGLES de video
     longo no YouTube (fonte para corte), dentro do tema do canal.
  4. ⛔ TRAVA DE TEMA: so' fica a busca que contem um termo do TEMA do radar.
     O radar ainda aplica TEMA/NUCLEO/VETO nos resultados -- isto so' evita
     gastar cota de busca do YouTube em termo que o radar vai descartar.
  5. Grava `canais/<canal>/buscas_extras.json`; o radar soma a BUSCAS.

    python -X utf8 engine/buscas_do_sucesso.py --canal modofuturo
    python -X utf8 engine/buscas_do_sucesso.py --todos [--so-ler]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESEMPENHO = RAIZ / "desempenho.jsonl"
URL_NV = "https://integrate.api.nvidia.com/v1/chat/completions"
MODELO = "nvidia/nemotron-3-super-120b-a12b"
MAX_BUSCAS = 8

PEDIDO = """Voce escolhe FONTES (videos longos do YouTube, 5-20 min) para cortes de TikTok.
Canal: {tema}
Estes foram os cortes de MAIOR alcance e curtida do canal no ultimo mes:
{titulos}
O que eles tem em comum (assunto, pessoas, programas, angulo) e' o que o publico quer.
⚠️ As fontes ATUAIS ja' se esgotaram: o radar ja' usa estas buscas e tudo que elas trazem ja' foi visto:
{atuais}
Escreva {n} buscas do YouTube que achem videos-fonte NOVOS no MESMO assunto campeao, mas vindos de
OUTROS criadores, canais, programas, revistas ou entrevistas (e pessoas vizinhas das campeas).
Nada fora do tema do canal. Ingles de preferencia; idioma original do assunto vale (ex.: coreano).
Responda SO' um array JSON de strings, sem explicar."""


def _ultimos() -> dict[str, dict]:
    ult: dict[str, dict] = {}
    with DESEMPENHO.open(encoding="utf-8") as f:
        for linha in f:
            try:
                d = json.loads(linha)
            except Exception:
                continue
            if d["post_id"] not in ult or d["lido_em"] > ult[d["post_id"]]["lido_em"]:
                ult[d["post_id"]] = d
    return ult


def nota(p: dict) -> float:
    return (p.get("reach") or 0) + 20 * (p.get("curtidas") or 0)


def campeoes(canal: str, n: int = 8, dias: int = 30) -> tuple[list[dict], dict]:
    """Os n melhores posts do canal e um resumo (mediana) para comparar."""
    agora = datetime.now(timezone.utc)
    ps = []
    for d in _ultimos().values():
        if d.get("canal") != canal:
            continue
        try:
            pub = datetime.fromisoformat(d["publicado_em"].replace("Z", "+00:00"))
        except Exception:
            continue
        if timedelta(days=1) <= agora - pub <= timedelta(days=dias):
            ps.append(d)
    ps.sort(key=lambda p: -nota(p))
    resumo = {"posts": len(ps),
              "alcance_mediano": statistics.median([p.get("reach") or 0 for p in ps]) if ps else 0,
              "curtidas_medianas": statistics.median([p.get("curtidas") or 0 for p in ps]) if ps else 0}
    return ps[:n], resumo


def _radar(canal: str):
    sys.path.insert(0, str(RAIZ))
    import abastecer_loop as al
    p = RAIZ / al.CANAIS[canal]["radar"]
    spec = importlib.util.spec_from_file_location("radar_" + canal.replace(".", "_"), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, p, al.CANAIS[canal]["tema"]


def _nemotron(texto: str) -> str | None:
    base = "NVIDIA_API_KEY"
    ks = ([os.environ[base]] if os.environ.get(base) else []) + [
        os.environ[k] for k in sorted(os.environ) if re.fullmatch(base + r"_\d+", k)]
    corpo = json.dumps({"model": MODELO, "temperature": 0.3, "max_tokens": 3000,
                        "messages": [{"role": "user", "content": texto}]}).encode()
    for t in range(max(1, len(ks)) * 2):
        if not ks:
            return None
        req = urllib.request.Request(URL_NV, data=corpo, headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + ks[t % len(ks)]})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                txt = json.load(r)["choices"][0]["message"]["content"] or ""
            return re.sub(r"(?s)<think>.*?</think>", "", txt).strip()
        except Exception:
            time.sleep(3)
    return None


def gerar(canal: str, gravar: bool = True) -> dict:
    radar, arq, tema = _radar(canal)
    termos_tema = [t.lower() for t in getattr(radar, "TEMA", [])]
    top, resumo = campeoes(canal, n=40)
    # ⛔ campeao FORA do tema atual nao enviesa (atefalhar ainda tem Goggins/academia
    # de antes de virar Geracao 2000; um deles gerou "David Goggins cartoon ...").
    import unicodedata
    def _sem_acento(x: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFD", x.lower()) if unicodedata.category(c) != "Mn")
    veto = [v.lower() for v in getattr(radar, "VETO", [])] + ["goggins", "academia", "treino"]         if canal == "atefalhar" else [v.lower() for v in getattr(radar, "VETO", [])]
    # (o TEMA do radar e' em ingles e o titulo do post em portugues: so' o veto
    #  serve aqui; a trava de tema age nas BUSCAS geradas, mais abaixo)
    top = [p for p in top if not any(v in _sem_acento(p["titulo"]) for v in veto)]
    top = top[:8]
    if len(top) < 3:
        return {"canal": canal, "erro": f"so' {len(top)} campeoes dentro do tema — nao enviesei nada"}
    titulos = "\n".join(f"- {p['titulo'][:110]} (alcance {p.get('reach') or 0}, curtidas {p.get('curtidas') or 0})"
                        for p in top)
    atuais = "; ".join(getattr(radar, "BUSCAS", [])[:40])
    txt = _nemotron(PEDIDO.format(tema=tema, titulos=titulos, atuais=atuais, n=MAX_BUSCAS + 4))
    if not txt:
        return {"canal": canal, "erro": "Nemotron nao respondeu"}
    try:
        i, j = txt.find("["), txt.rfind("]")
        cand = [str(b).strip() for b in json.loads(txt[i:j + 1])]
    except Exception:
        return {"canal": canal, "erro": "resposta sem JSON: " + txt[:100]}
    ja = {b.lower() for b in getattr(radar, "BUSCAS", [])}
    buscas, fora = [], []
    for b in cand:
        bl = b.lower()
        if bl in ja or b in buscas:
            continue
        # ⛔ trava de tema (termo curto como "fab" casa com "fabulous": exige palavra)
        if termos_tema and not any(re.search(r"\b" + re.escape(t) + r"\b", bl) for t in termos_tema):
            fora.append(b)
            continue
        buscas.append(b)
    saida = {"canal": canal, "gerado_em": datetime.now().isoformat(timespec="minutes"),
             "nota": "alcance + 20 x curtida, 30 dias", "resumo": resumo,
             "campeoes": [p["titulo"][:90] for p in top],
             "buscas": buscas[:MAX_BUSCAS], "descartadas_fora_do_tema": fora}
    if gravar:
        (arq.parent / "buscas_extras.json").write_text(
            json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    return saida


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--so-ler", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, str(RAIZ))
    import abastecer_loop as al
    for c in (list(al.CANAIS) if a.todos else [a.canal]):
        r = gerar(c, gravar=not a.so_ler)
        print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
