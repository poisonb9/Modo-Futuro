"""Compara a QUALIDADE DA SELEÇÃO entre modelos do Gemini.

Existe porque a cota gratuita é de 20 requisições/dia POR MODELO: quando o
principal esgota, o motor cai pro reserva (`config.GEMINI_MODELOS_RESERVA`).
Antes de confiar num reserva é preciso provar que ele não piora o corte.

    python teste/comparar_modelos.py --url "https://youtu.be/..." \
        --modelos gemini-3.6-flash gemini-3.5-flash gemini-3-flash-preview

    # comparar contra um lote já produzido (referência de 3.6-flash)
    python teste/comparar_modelos.py --url "..." --ref "saida/2026-07-26_2346/fonte"

Baixa a fonte UMA vez e reaproveita entre os modelos. Cada modelo custa 1
requisição da cota dele.
"""
import argparse
import io
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import config                      # noqa: E402
from engine import midia, selecao  # noqa: E402

TAXONOMIA = ["tipo_conteudo", "emocao_dominante", "dinamica",
             "marcador_viral", "arquetipo"]
SUBNOTAS = ["forca_gancho", "compartilhabilidade", "independencia",
            "intensidade_emocional"]


def carregar_ref(pasta: Path) -> list[dict]:
    """Lê os post.json de um lote já produzido, pra servir de referência."""
    out = []
    for p in sorted(pasta.glob("*/post.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def sobreposicao(a: dict, b: dict) -> float:
    """Quanto do clipe MAIS CURTO está contido no outro (0 a 1).

    Divide pela duração MENOR de propósito. A pergunta é "achou o mesmo
    momento?", não "escolheu o mesmo recorte". Um candidato de 120s que
    engloba inteiro um clipe de 46s da referência achou o momento — usar a
    duração maior daria 38% e reprovaria um acerto (foi o que aconteceu na
    1ª rodada deste teste e quase virou conclusão errada)."""
    ini = max(a["inicio_s"], b["inicio_s"])
    fim = min(a["fim_s"], b["fim_s"])
    if fim <= ini:
        return 0.0
    menor = min(a["fim_s"] - a["inicio_s"], b["fim_s"] - b["inicio_s"])
    return (fim - ini) / menor if menor > 0 else 0.0


def concordancia(clipes: list[dict], ref: list[dict]) -> tuple[int, float]:
    """Quantos clipes da referência foram reencontrados (sobreposição >50%)."""
    achou, somas = 0, []
    for r in ref:
        melhor = max((sobreposicao(c, r) for c in clipes), default=0.0)
        somas.append(melhor)
        if melhor > 0.5:
            achou += 1
    return achou, (statistics.mean(somas) if somas else 0.0)


def resumo(nome: str, clipes: list[dict], ref: list[dict] | None):
    notas = [c.get("nota", 0) for c in clipes]
    durs = [c.get("duracao_s") or (c["fim_s"] - c["inicio_s"]) for c in clipes]
    cheio_tax = sum(1 for c in clipes if all(c.get(k) for k in TAXONOMIA))
    cheio_sub = sum(1 for c in clipes if all(c.get(k) is not None for k in SUBNOTAS))
    curtos = sum(1 for d in durs if d < 60)

    print(f"\n--- {nome} ---")
    print(f"  clipes:            {len(clipes)}")
    if notas:
        print(f"  nota   min/med/max: {min(notas)} / {statistics.mean(notas):.1f} / {max(notas)}")
    if durs:
        print(f"  duração min/med/max: {min(durs):.0f}s / {statistics.mean(durs):.0f}s / {max(durs):.0f}s")
        print(f"  abaixo de 60s:     {curtos}/{len(durs)}  (não monetizam)")
    print(f"  taxonomia completa: {cheio_tax}/{len(clipes)}")
    print(f"  subnotas completas: {cheio_sub}/{len(clipes)}")
    if ref:
        achou, media = concordancia(clipes, ref)
        print(f"  reencontrou da ref: {achou}/{len(ref)} clipes (sobrep. média {media:.0%})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="URL do vídeo de teste")
    ap.add_argument("--arquivo", help="usa um .mp4 local em vez de baixar")
    ap.add_argument("--modelos", nargs="+", required=True)
    ap.add_argument("--qtd", type=int, default=6)
    ap.add_argument("--ref", help="pasta de um lote já produzido, como referência")
    ap.add_argument("--saida", default="teste/comparacao_modelos.json")
    a = ap.parse_args()

    if a.arquivo:
        fonte = Path(a.arquivo)
    elif a.url:
        # pasta própria: `midia.baixar` apaga fonte.* do destino, e não
        # queremos que isso atrapalhe um main.py rodando em paralelo
        print(f"baixando {a.url} ...")
        fonte = midia.baixar(a.url, config.TRABALHO / "teste_modelos")
    else:
        sys.exit("informe --url ou --arquivo")

    dur = midia.duracao(fonte)
    print(f"fonte: {fonte.name}  {midia.mb(fonte):.0f} MB  {dur/60:.1f} min")

    ref = carregar_ref(Path(a.ref)) if a.ref else None
    if ref:
        resumo(f"REFERÊNCIA ({a.ref})", ref, None)

    resultados = {}
    original = config.GEMINI_MODELO
    reserva_original = config.GEMINI_MODELOS_RESERVA
    try:
        for m in a.modelos:
            print(f"\n>>> rodando seleção com {m} ...")
            # trava no modelo do teste: sem cascata, senão mede outro modelo
            config.GEMINI_MODELO = m
            config.GEMINI_MODELOS_RESERVA = []
            try:
                clipes = selecao.escolher(fonte, dur, True, a.qtd)
            except Exception as e:                       # noqa: BLE001
                print(f"  [x] {m} falhou: {str(e)[:200]}")
                continue
            resultados[m] = clipes
            resumo(m, clipes, ref)
    finally:
        config.GEMINI_MODELO = original
        config.GEMINI_MODELOS_RESERVA = reserva_original

    Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.saida).write_text(
        json.dumps({"fonte": str(fonte), "ref": a.ref, "resultados": resultados},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsalvo em {a.saida}")

    if len(resultados) > 1:
        print("\n=== títulos lado a lado ===")
        for m, cs in resultados.items():
            print(f"\n{m}:")
            for c in sorted(cs, key=lambda x: -x.get("nota", 0)):
                d = c.get("duracao_s") or (c["fim_s"] - c["inicio_s"])
                print(f"  [{c.get('nota','?')}] {d:>5.0f}s  {str(c.get('titulo',''))[:64]}")


if __name__ == "__main__":
    main()
