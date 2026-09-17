# -*- coding: utf-8 -*-
"""Os selos "Espere" e "Recorde" nascem da NOSSA serie — e so' dela. Sem rede.

## POR QUE EXISTE (17/09/2026)

Bryan aprovou dois selos que a loja nunca da': "espere: ja' esteve a R$ 34
ha' 6 dias" (manda NAO comprar) e "Recorde: menor em N dias" (o produto
ADQUIRE o selo no dia em que bate o minimo da serie com >= 14 dias).

⭐ Casos teorematicos: (1) recorde com 14 dias e hoje = minimo; (2) ⛔ NEGATIVO
13 dias NAO e' recorde (e' estreia), e hoje acima do minimo NAO e' recorde;
(3) empate ate' 0,5% conta ("nunca esteve mais barato"); (4) "espere" leva
`ha` (dias desde o minimo) e some quando o produto esta' no minimo.
"""
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
import publicar_bio as pb  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


def serie(pontos):
    raiz = Path(tempfile.mkdtemp())
    (raiz / "estado").mkdir()
    (raiz / "estado" / "precos_vistos.jsonl").write_text(
        "\n".join(json.dumps({"id": 1, "preco": v, "quando": (date.today() - timedelta(days=d)).isoformat()})
                  for d, v in pontos), encoding="utf-8")
    pb.RAIZ = raiz
    pb._MEMO_HOJE.clear()
    return pb._precos_por_dia()


raiz_real = pb.RAIZ
d = {"id": 1, "preco": "R$ 30,00"}
try:
    print("1. RECORDE: 14 dias de serie, hoje e' o minimo")
    por_dia = serie([(14, 30.0), (7, 28.0), (0, 25.0)])
    checar(pb._recorde(por_dia, d) == {"dias": 14}, f"recorde com 14 dias: {pb._recorde(por_dia, d)}")
    checar(pb._ja_esteve(por_dia, d) == {}, "no minimo NAO ha' 'espere'")

    print()
    print("2. ⛔ NEGATIVO: 13 dias NAO e' recorde; hoje acima do minimo NAO e' recorde")
    por_dia = serie([(13, 30.0), (7, 28.0), (0, 25.0)])
    checar(pb._recorde(por_dia, d) == {}, "13 dias = estreia, sem selo")
    por_dia = serie([(20, 30.0), (6, 22.0), (0, 25.0)])
    checar(pb._recorde(por_dia, d) == {}, "hoje 25 > minimo 22: sem recorde")

    print()
    print("3. EMPATE ATE' 0,5% CONTA COMO RECORDE")
    por_dia = serie([(20, 30.0), (10, 25.0), (0, 25.10)])
    checar(pb._recorde(por_dia, d) == {"dias": 20}, "25,10 contra minimo 25,00 (0,4%) = recorde")
    por_dia = serie([(20, 30.0), (10, 25.0), (0, 25.20)])
    checar(pb._recorde(por_dia, d) == {}, "25,20 (0,8%) ja' nao e'")

    print()
    print("4. ESPERE: leva `ha` (dias desde o minimo)")
    por_dia = serie([(20, 30.0), (6, 22.0), (0, 25.0)])
    je = pb._ja_esteve(por_dia, d)
    checar(je.get("preco") == "R$ 22,00" and je.get("ha") == 6, f"ja_esteve = {je}")
finally:
    pb.RAIZ = raiz_real
    pb._MEMO_HOJE.clear()

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
