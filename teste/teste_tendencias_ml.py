# -*- coding: utf-8 -*-
"""Tendencias do ML: so' termo ESPECIFICO casa, e casa inteiro. Sem rede.

## POR QUE EXISTE (regua v2, 17/09/2026)

Medido: palavra solta ("cabo", "controle", "chaveiro") casava com 15-27
produtos a toa. A regra e' teorematica: (1) so' 2+ palavras conta;
(2) o termo casa INTEIRO e com borda de palavra ("pato" nao e' "sapato");
(3) acento e caixa nao importam; (4) Momento +0,3 com `em_alta`, e so' com ele.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import tendencias_ml as tm, regua_vitrine as rv  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


L = ["balanca digital", "cabo", "controle", "caixa organizadora", "pato", "adaptador vga para hdmi"]
print("1. SO' 2+ PALAVRAS")
checar(tm.em_alta("Cabo Tipo C 240W", L) == "", "'cabo' (palavra solta) nao casa")
checar(tm.em_alta("Controle 8BitDo Ultimate", L) == "", "'controle' nao casa")
checar(tm.em_alta("Balança Digital de café", L) == "balanca digital", "'balanca digital' casa (sem acento, sem caixa)")

print()
print("2. INTEIRO E COM BORDA")
checar(tm.em_alta("Sapato social", ["pato"]) == "", "⛔ 'pato' nao casa com 'sapato' (e nem conta: 1 palavra)")
checar(tm.em_alta("Caixa organizadora de 2 camadas", L) == "caixa organizadora", "termo inteiro dentro do nome")
checar(tm.em_alta("Caixa de som organizadora", L) == "", "palavras separadas nao casam")

print()
print("3. MOMENTO +0,3 SO' COM em_alta")
checar(rv.momento({"queda": 0.0}) == 0.0, "sem nada = 0")
checar(abs(rv.momento({"queda": 0.0, "em_alta": "balanca digital"}) - 0.3) < 1e-9, "em alta = 0,3")
checar(rv.momento({"queda": 20.0, "vendeu": [800, "14/09"], "em_alta": "x y"}) == 1.0, "teto 1,0")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
