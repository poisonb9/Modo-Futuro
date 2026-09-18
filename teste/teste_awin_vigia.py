# -*- coding: utf-8 -*-
"""O vigia do Awin avisa o que MUDOU — e fica quieto na estreia.

⚠️ Nao toca na rede: troca `_instantaneo` por uma leitura de mentira.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import awin  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


awin.ESTADO = Path(tempfile.mkdtemp()) / "awin.json"


def fingir(d):
    awin._instantaneo = lambda: d


print("1. NEGATIVO - a estreia nao avisa nada")
# 28 pendentes viram 28 "novidades" se a linha de base nao existir. Um aviso
# que grita na estreia ensina a ignorar o aviso.
fingir({"Nike BR": "pending", "Carrefour BR": "pending"})
checar(awin.vigiar(avisar=False) == [], "primeira leitura: zero linha")
checar(awin.ESTADO.exists(), "mas gravou a linha de base")

print("")
print("2. NEGATIVO - sem mudanca, sem aviso")
checar(awin.vigiar(avisar=False) == [], "mesma leitura: zero linha")

print("")
print("3. aprovacao aparece, e diz o que fazer com ela")
fingir({"Nike BR": "joined", "Carrefour BR": "pending"})
linhas = awin.vigiar(avisar=False)
checar(len(linhas) == 1, "so' a que mudou entra")
checar("APROVADO" in linhas[0] and "Nike BR" in linhas[0], "diz APROVADO Nike BR")

print("")
print("4. recusa e anunciante novo tambem aparecem")
fingir({"Nike BR": "joined", "Carrefour BR": "rejected", "Hering BR": "pending"})
linhas = awin.vigiar(avisar=False)
checar(any("Carrefour BR: pending -> rejected" in x for x in linhas), "a recusa")
checar(any(x.startswith("NOVO") and "Hering BR" in x for x in linhas), "o novo")
checar(not any("Nike" in x for x in linhas), "e a Nike, que nao mudou, fica fora")

print("")
print("5. NEGATIVO - falha de leitura NAO apaga a linha de base")
# ⚠️ Gravar depois de uma falha zeraria a base, e a proxima rodada acusaria
# mudanca que nunca houve — ruido que parece sinal.
antes = awin.ESTADO.read_text(encoding="utf-8")


def estoura():
    raise RuntimeError("401 sem token")


awin._instantaneo = estoura
try:
    awin.vigiar(avisar=False)
    checar(False, "devia ter estourado")
except RuntimeError:
    checar(True, "a falha sobe, nao e' engolida")
checar(awin.ESTADO.read_text(encoding="utf-8") == antes,
       "e o arquivo ficou intacto")

print("5. ⛔ COMISSOES: resposta PARCIAL da API nao apaga o que ja' se sabia")
# MEDIDO em 18/09/2026: a API devolveu 12 programas e, um minuto depois, 2;
# a versao anterior gravou os 2 por cima dos 12.
import json
awin.COMISSOES_ESTADO = Path(tempfile.mkdtemp()) / "c.json"
awin.comissoes_da_api = lambda: {"Nike BR": 7.5, "Lauri Esporte": 11.0}
awin.guardar_comissoes()
awin.comissoes_da_api = lambda: {"Nike BR": 7.0}
r = awin.guardar_comissoes()
checar(r == {"Nike BR": 7.0, "Lauri Esporte": 11.0}, f"funde: atualiza a Nike, mantem a Lauri ({r})")
checar(json.loads(awin.COMISSOES_ESTADO.read_text(encoding="utf-8")) == r, "e o arquivo tem o fundido")
awin.comissoes_da_api = lambda: {}
checar(awin.guardar_comissoes() == {} and json.loads(awin.COMISSOES_ESTADO.read_text(encoding="utf-8")) == r,
       "resposta vazia: nao grava nada, arquivo intacto")

print("")
print("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde")
sys.exit(1 if falhas else 0)
