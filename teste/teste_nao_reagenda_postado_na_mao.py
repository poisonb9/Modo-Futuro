# -*- coding: utf-8 -*-
"""O que foi postado NA MAO nao pode voltar pra fila.

⚠️ ACONTECEU EM 01/09/2026, com quatro videos. Ao abrir a fila dos canais
novos, o agendador enfileirou material que JA' ESTAVA NO AR — o Bryan tinha
postado a mao, e postagem manual nao passa pelo Buffer:

    A verdade doida sobre o motivo do seu fracasso     41 views
    Como fazer base e contorno em creme perfeito      607 views
    Truque de contorno em po para esculpir             32 views
    O CHECKLIST PERFEITO para escolher exercicios      24 views

⚠️ POR QUE A DEDUP NAO VIU. Ela compara contra o que o BUFFER conhece
(agendados + enviados). Nada disso passou pelo Buffer. A guarda tinha de
consultar o REGISTRO, que guarda as tres origens: buffer, mao e print.

⚠️ CASO NEGATIVO: clipe que NUNCA foi postado tem de passar. Uma guarda que
recusa tudo o que encontra no registro pararia a operacao — o registro
cataloga TODO clipe que sai do pipeline, postado ou nao.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import registro_clipes as reg  # noqa: E402

reg.ARQUIVO = Path(tempfile.mkdtemp()) / "r.json"
falhas = []

# um postado NA MAO, e um que so' saiu do pipeline
reg.registrar_historico(titulo="Como fazer base e contorno em creme perfeito",
                        canal="truque.importado", origem="mao",
                        postado_em="2026-09-01T11:00:00Z")
reg.registrar_historico(titulo="Truque Infalivel para Cilios Postiços",
                        canal="truque.importado")


def cabe(entrada: dict) -> bool:
    """A guarda como esta' no agendar_buffer, na parte do registro."""
    ch = reg.sha_por_titulo(str(entrada.get("titulo") or ""))
    return not (ch and reg.ja_postado(ch))


# 1. POSITIVO — o postado na mao e' recusado
if cabe({"titulo": "Como fazer base e contorno em creme perfeito"}):
    falhas.append("reagendaria um video ja' postado NA MAO")
# e o titulo do Buffer vem com maiusculas/acentos diferentes
if cabe({"titulo": "COMO FAZER BASE E CONTORNO EM CREME PERFEITO"}):
    falhas.append("a diferenca de caixa furou a guarda")

# 2. NEGATIVO — clipe catalogado e NAO postado tem de passar
if not cabe({"titulo": "Truque Infalivel para Cilios Postiços"}):
    falhas.append("recusou um clipe que nunca foi postado")
# 3. NEGATIVO — clipe desconhecido tem de passar
if not cabe({"titulo": "Um clipe totalmente novo"}):
    falhas.append("recusou um clipe que nem esta' no registro")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print("[ok] teste_nao_reagenda_postado_na_mao: recusa o que foi ao ar, "
      "deixa passar o que nao foi")
