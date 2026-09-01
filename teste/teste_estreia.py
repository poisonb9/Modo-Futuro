# -*- coding: utf-8 -*-
"""Canal em estreia nao recebe agendamento — e destrava sozinho no prazo.

⚠️ ESTE TESTE EXISTE PORQUE EU CONSERTEI A INSTANCIA TRES VEZES. Em
31/08/2026 os runs #191, #196, #202 e #216 enfileiraram sozinhos em canal de
estreia, e a cada vez eu apaguei o post e segui. Apagar depois nao e'
conserto: o run seguinte repoe.

⚠️ CASO NEGATIVO 1: canal que NAO esta' em estreia tem de passar. Uma guarda
que recusa todo mundo passaria no caso de cima e pararia a operacao inteira.

⚠️ CASO NEGATIVO 2: passado o prazo, o proprio canal em estreia volta a
passar. Sem isso a trava seria eterna e dependeria de alguem lembrar de
destravar — trocar um esquecimento por outro.
"""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import estreia  # noqa: E402

falhas = []
durante = datetime.date(2026, 9, 1)
depois = datetime.date(2026, 9, 2)

# ⚠️ Em 01/09/2026 o Bryan liberou o @truque.importado e o @semanestesia.pod
# pro automatico. So' o @atefalhar continua na lista — e o teste tem de
# confirmar que os liberados PASSAM, senao a liberacao nao valeu de nada.
for canal in ("truque.importado", "semanestesia.pod"):
    if estreia.em_estreia(canal, durante):
        falhas.append(f"{canal} foi LIBERADO pelo Bryan e continua travado")

for canal in ("atefalhar",):
    if not estreia.em_estreia(canal, durante):
        falhas.append(f"{canal} deveria estar travado em 01/09")
    # NEGATIVO 2 — o prazo acaba e o canal volta sozinho
    if estreia.em_estreia(canal, depois):
        falhas.append(f"{canal} continuou travado depois do prazo (02/09)")

# NEGATIVO 1 — canal fora da estreia nunca e' travado
for canal in ("modofuturo", "cozinha.internacional", ""):
    if estreia.em_estreia(canal, durante):
        falhas.append(f"{canal!r} foi travado sem estar em estreia")

# o @ na frente nao pode enganar a guarda
if not estreia.em_estreia("@atefalhar", durante):
    falhas.append("o @ na frente do nome furou a guarda")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print("[ok] teste_estreia: travado no prazo, livre depois, e so' quem deve")
