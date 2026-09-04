"""Mede, SEM AGENDAR NADA, quantos clipes prontos cada canal ainda tem.

POR QUE ESTE ARQUIVO EXISTE

Em 04/09/2026 uma sessao concluiu "a fabrica esta' seca" a partir de UMA
linha do `repor_fila`: "0 ainda nao agendado". A linha era verdadeira e a
conclusao era falsa. O `repor_fila` so' olha o manifesto de um canal quando
ele esta' ABAIXO do piso; naquela hora o modofuturo tinha exatamente o piso,
entao o agendador nunca rodou e o "0" era o valor de quem nao contou. Medido
depois, o mesmo canal tinha 27 clipes prontos e 6 vagas livres.

⚠️ E nao da' pra medir isso da maquina do Bryan: o `.env` local so' tem o
token do modofuturo. Os quatro tokens juntos so' existem nos SECRETS deste
repositorio — por isso a medicao mora num workflow, e nao num script local.

⚠️ ESTE SCRIPT NAO ESCREVE EM LUGAR NENHUM. Ele so' chama o
`agendar_buffer.py --simular`, que e' read-only por construcao. Se um dia
alguem precisar que ele reponha, escreva OUTRO script: a garantia de que este
nao publica e' o que o torna seguro de disparar a qualquer hora.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from repor_fila import LIBERADOS, SO_RELATA

RAIZ = Path(__file__).resolve().parent

# "158 clipe(s) no manifesto, 27 ainda nao agendado(s)" — com ou sem acento,
# porque o agendador imprime acentuado e o runner pode reencodar.
LINHA_ESTOQUE = re.compile(
    r"(\d+)\s+clipe\(s\) no manifesto,\s*(\d+)\s+ainda n[ãa]o agendado")
LINHA_FILA = re.compile(r"fila:\s*(\d+)/(\d+)\s+agendados.*?(\d+)\s+vaga")


def medir(nome: str, cfg: dict) -> dict:
    """Roda o simulador para UM canal. Devolve o que deu pra ler.

    ⚠️ Campo nao lido vira None, nunca 0. Um zero inventado aqui e'
    exatamente o erro que este arquivo existe pra impedir.
    """
    token = (os.environ.get(cfg["env"]) or "").strip()
    if not token:
        return {"canal": nome, "erro": f"sem {cfg['env']}"}

    # CANAL_ESPERADO e' a guarda do proprio agendador: se o token abrir outra
    # conta, ele aborta. Sem isso, um secret trocado mede o canal errado em
    # silencio — aconteceu na medicao local de 04/09.
    env = dict(os.environ, CANAL_ESPERADO=nome, BUFFER_TOKEN=token)
    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", "agendar_buffer.py", "--simular"],
            cwd=RAIZ, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=900)
    except subprocess.TimeoutExpired:
        return {"canal": nome, "erro": "simulador passou de 15 min"}

    saida = (r.stdout or "") + (r.stderr or "")
    if "CANAL ERRADO" in saida:
        return {"canal": nome, "erro": "o token abriu outra conta"}

    est = LINHA_ESTOQUE.search(saida)
    fil = LINHA_FILA.search(saida)
    return {
        "canal": nome,
        "manifesto": int(est.group(1)) if est else None,
        "prontos": int(est.group(2)) if est else None,
        "agendados": int(fil.group(1)) if fil else None,
        "vagas": int(fil.group(3)) if fil else None,
        "erro": None if est else "nao achei a linha de estoque na saida",
    }


def formatar(linhas: list[dict]) -> str:
    out = ["Estoque por canal (medido, sem agendar nada)", ""]
    out.append(f"  {'canal':<24}{'prontos':>8}{'vagas':>7}{'manifesto':>11}")
    for d in linhas:
        if d.get("erro"):
            out.append(f"  {d['canal']:<24}  [!] {d['erro']}")
            continue
        out.append(f"  {d['canal']:<24}{d['prontos']:>8}{d['vagas']:>7}"
                   f"{d['manifesto']:>11}")
    out.append("")
    out.append("prontos = clipe no manifesto que passou por TODAS as guardas "
               "e caberia na fila agora.")
    out.append("⚠️ Nada foi agendado: isto roda o agendador com --simular.")
    return "\n".join(out)


def main() -> None:
    pedidos = [c.strip() for c in (os.environ.get("CANAIS") or "").split(",")
               if c.strip()]
    # SO_RELATA entra tambem: a cozinha tem manifesto proprio, e ver "0" nela
    # com a fila vazia e' informacao, nao ruido.
    todos = {**LIBERADOS, **SO_RELATA}
    linhas = [medir(n, c) for n, c in todos.items()
              if not pedidos or n in pedidos]
    texto = formatar(linhas)
    print(texto)
    Path("relato_estoque.txt").write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
