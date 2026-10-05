# -*- coding: utf-8 -*-
"""Mede cada clipe pronto com PySceneDetect e auto-editor — SO' MEDE.

05/10/2026 (dono: "PySceneDetect parece muito interessante, instala em nuvem;
auto-editor tambem"). Os dois rodam no workflow de corte, DEPOIS do main.py,
e nao alteram nenhum clipe:

  cenas_por_min   PySceneDetect (ContentDetector): quantos cortes de cena o
                  clipe tem por minuto — o "ritmo" visual.
  silencio_pct    auto-editor (--export json, limiar de audio): que fracao do
                  clipe seria tirada como pausa morta.

⚠️ POR QUE SO' MEDIR: o motor ja' tem `midia.cortar_silencios` (a mesma ideia
do auto-editor) e ele NAO e' chamado em lugar nenhum — cortar pausa depois da
dublagem desalinha voz e imagem. Ligar no escuro seria trocar retencao por
lip-sync quebrado. Quando `ferramentas/views_tiktok.py` tiver views de uma
semana redonda, cruza-se views x cenas_por_min x silencio_pct e decide-se com
dado se vale cortar mais ou ter mais cenas.

    python -X utf8 ferramentas/medir_clipes.py saida/        # grava estado/medidas_clipes.jsonl
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "estado" / "medidas_clipes.jsonl"


def duracao(v: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                        "default=nw=1:nk=1", str(v)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def cenas(v: Path) -> int | None:
    try:
        from scenedetect import ContentDetector, detect
        return len(detect(str(v), ContentDetector(threshold=27.0)))
    except Exception as e:  # noqa: BLE001 — medir nunca derruba o corte
        print(f"  [!] scenedetect {v.name}: {type(e).__name__} {str(e)[:60]}")
        return None


def silencio(v: Path, dur: float) -> float | None:
    try:
        # auto-editor 29: `--stats` imprime "diff: -0:00:03.00 (-90) -15.03%"
        # (o --export json saiu). Medido em 05/10 num clipe de oferta: 15%.
        r = subprocess.run(["auto-editor", str(v), "--edit", "audio:threshold=4%", "--stats"],
                           capture_output=True, text=True, timeout=300)
        import re
        m = re.search(r"diff:.*?(-?[\d.]+)%", r.stdout + r.stderr)
        return round(abs(float(m.group(1))) / 100, 3) if m else None
    except Exception as e:  # noqa: BLE001
        print(f"  [!] auto-editor {v.name}: {type(e).__name__} {str(e)[:60]}")
        return None


def main() -> None:
    pasta = Path(sys.argv[1] if len(sys.argv) > 1 else "saida")
    clipes = sorted(p for p in pasta.rglob("*.mp4") if "diagnostico" not in p.parts)
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with SAIDA.open("a", encoding="utf-8") as f:
        for v in clipes:
            dur = duracao(v)
            n = cenas(v)
            s = silencio(v, dur)
            linha = {"medido_em": agora, "clipe": str(v.relative_to(pasta)), "duracao": round(dur, 2),
                     "cenas": n, "cenas_por_min": round(n / dur * 60, 1) if n is not None and dur else None,
                     "silencio_pct": s}
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            print(f"  {v.name[:50]:50} {dur:6.1f}s  cenas/min {linha['cenas_por_min']}  silencio {s}")
    print(f"medir_clipes: {len(clipes)} clipe(s) -> {SAIDA.name}")


if __name__ == "__main__":
    main()
