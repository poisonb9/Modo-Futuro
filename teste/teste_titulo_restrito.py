# -*- coding: utf-8 -*-
"""A guarda do titulo restrito: limpar pode, inventar nao.

O Bryan pediu titulo "extremamente vendavel" pelo Gemini e, depois de eu
expor o risco, escolheu a REESCRITA RESTRITA. Este teste e' o que faz
"restrita" valer alguma coisa: sem ele, a restricao seria apenas uma frase
simpatica dentro do prompt — e prompt nao e' garantia, e' pedido.

⛔ O CASO NEGATIVO E' O CORACAO. Um detector que so' aprova o certo nao prova
nada: ele passaria igual se aceitasse tudo. Aqui cada invencao plausivel que
um modelo faria — material, superlativo, medida, publico — tem de ser
RECUSADA por nome.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from engine import titulo_vendavel as tv  # noqa: E402

FALHAS = 0


def checar(ok, msg):
    global FALHAS
    print(("  ok   " if ok else "  [x]  ") + msg)
    if not ok:
        FALHAS += 1


ORIGEM = "Limpa vidro carro com cabo longo e escova"

print("1. POSITIVO: limpeza legitima passa")
for novo, porque in [
    ("Limpa-vidros de carro com cabo longo", "cortou e reordenou"),
    ("Escova limpa vidro de carro", "trocou a ordem"),
    ("Limpa vidro carro com cabo longo", "so' cortou"),
]:
    ok, motivo = tv.so_reordena(ORIGEM, novo)
    checar(ok, f"{porque}: {novo!r} ({motivo})")

print()
print("2. NEGATIVO: toda invencao plausivel de um modelo e' RECUSADA")
# ⚠️ Estas nao sao invencoes imaginarias: sao exatamente o que um modelo
# escreve quando se pede "titulo vendavel" — material, superlativo, medida,
# publico e uso que ninguem verificou.
for novo, oquefoi in [
    ("Limpa-vidros profissional com cabo longo", "superlativo 'profissional'"),
    ("Limpa vidro carro com cabo telescopico", "atributo 'telescopico'"),
    ("Limpa vidro com escova de microfibra", "material 'microfibra'"),
    ("Limpa vidro carro cabo 90cm com escova", "medida '90cm'"),
    ("Limpa vidro ideal para motoristas", "publico 'motoristas'"),
    ("Kit limpa vidro carro com cabo e escova", "substantivo 'kit'"),
]:
    ok, motivo = tv.so_reordena(ORIGEM, novo)
    checar(not ok, f"recusa {oquefoi} ({motivo})")

print()
print("3. NEGATIVO: os limites de forma")
for novo, oquefoi in [
    ("", "vazio"),
    ("   ", "so' espaco"),
    ("Limpa vidro de carro com cabo longo e escova de limpeza para vidro",
     "mais longo que a origem"),
]:
    ok, motivo = tv.so_reordena(ORIGEM, novo)
    checar(not ok, f"recusa {oquefoi} ({motivo})")

print()
print("4. PLURAL E GENERO NAO SAO INVENCAO")
# ⚠️ Sem esta tolerancia a guarda reprovaria limpeza legitima e ninguem
# usaria a ferramenta: "escovas" nao e' palavra nova, e' a mesma palavra.
for novo, oquefoi in [
    ("Limpa-vidros de carro com escovas", "plural 'escovas'"),
    ("Limpa vidro do carro com cabo longo", "contracao 'do'"),
]:
    ok, motivo = tv.so_reordena(ORIGEM, novo)
    checar(ok, f"aceita {oquefoi} ({motivo})")

print()
print("5. A PALAVRA CURTA EXIGE IGUALDADE")
# ⚠️ Com raiz de 4 letras, palavra de 3 casaria com quase tudo: "kit" nao
# pode entrar so' porque existe "carro". Abaixo de 4 letras, e' igualdade.
ok, motivo = tv.so_reordena("Suporte de celular para carro", "Suporte de cel para carro")
checar(not ok, f"recusa 'cel', que nao esta' na origem ({motivo})")

print()
print("tudo verde" if not FALHAS else f"{FALHAS} FALHA(S)")
sys.exit(1 if FALHAS else 0)
