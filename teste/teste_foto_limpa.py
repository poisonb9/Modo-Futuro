# -*- coding: utf-8 -*-
"""A escolha da foto do cartao, com as medidas da nuvem injetadas. Sem rede.

Os numeros sao os MEDIDOS no run 35356232292 (18/09/2026), nos produtos que
foram olhados a olho antes. O que protege:
1. ⛔ o teclado: extras com fid 0,32-0,58 (a placa de montagem) NAO entram,
   mesmo com menos texto — fica a principal;
2. ⛔ bolsa/oculos: principal com texto 0,0 nao troca, por melhor que a extra
   pareca (a v1 trocou a bolsa marrom pela preta aqui);
3. luva/ventosa: principal com banner, extra do mesmo produto com menos
   texto -> troca pela de MENOS texto entre as que passam;
4. extra com menos texto mas por menos que a margem -> fica;
5. sem medida (nao medida, ou erro do OCR) -> nao concorre; principal sem
   medida -> principal.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import foto_limpa as fl  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


print("1. ⛔ teclado: placa de montagem (fid < FID_MIN) nao entra")
med = {"p": {"texto": 0.0863, "fid": 1.0},
       "a": {"texto": 0.0749, "fid": 0.322}, "b": {"texto": 0.0132, "fid": 0.3911},
       "c": {"texto": 0.0812, "fid": 0.3843}, "d": {"texto": 0.1342, "fid": 0.5839}}
checar(fl.escolher("p", ["a", "b", "c", "d"], med) == "p", "fica a principal (nenhuma e' o teclado)")
checar(fl.FID_MIN > 0.5839, f"FID_MIN {fl.FID_MIN} acima da placa mais parecida (0,5839)")

print("2. ⛔ principal ja' limpa nao troca (bolsa marrom x preta)")
med = {"p": {"texto": 0.0, "fid": 1.0}, "preta": {"texto": 0.0, "fid": 0.74}}
checar(fl.escolher("p", ["preta"], med) == "p", "texto 0,0 na principal: nada a consertar")

print("3. luva: banner na principal, extra do mesmo produto com menos texto")
med = {"p": {"texto": 0.1431, "fid": 1.0},
       "a": {"texto": 0.0874, "fid": 0.4635}, "b": {"texto": 0.032, "fid": 0.6124},
       "c": {"texto": 0.0, "fid": 0.4333}, "d": {"texto": 0.0353, "fid": 0.6275}}
checar(fl.escolher("p", ["a", "b", "c", "d"], med) == "d",
       "escolhe 'd' (fid 0,63, texto 0,035); 'c' tem 0,0 de texto mas fid 0,43 — nao e' a luva")

print("4. menos texto, mas por menos que a margem -> fica")
med = {"p": {"texto": 0.10, "fid": 1.0}, "a": {"texto": 0.10 - fl.MARGEM_TEXTO + 0.001, "fid": 0.9}}
checar(fl.escolher("p", ["a"], med) == "p", "ruido nao troca a foto")

print("5. falha aberta")
med = {"p": {"texto": 0.2, "fid": 1.0}, "a": {"erro": "Timeout"}, "b": {"texto": 0.0, "fid": 0.9}}
checar(fl.escolher("p", ["a", "b"], med) == "b", "extra com erro nao concorre; a boa entra")
checar(fl.escolher("p", ["a"], med) == "p", "so' extras com erro -> principal")
checar(fl.escolher("x", ["b"], med) == "x", "principal sem medida -> principal")
checar(fl.escolher("p", [], med) == "p", "sem extras -> principal")

print("6. o modulo registra o que NAO funcionou (o caso negativo da v1)")
_fonte = (RAIZ / "engine" / "foto_limpa.py").read_text(encoding="utf-8")
checar("PLACA DE MONTAGEM" in _fonte and "RECORTA" in _fonte,
       "placa do teclado e recorte da dedupe estao escritos")

print()
print("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde")
sys.exit(1 if falhas else 0)
