# -*- coding: utf-8 -*-
"""Canal que existe no TikTok mas NAO no Buffer nao pode publicar nada.

⚠️ POR QUE ESTE TESTE EXISTE.

Em 09/09/2026, na tela "Mudar de conta" do app, apareceram SETE contas de
TikTok. O `canais_registro` tinha CINCO. As duas faltantes
(`achadinhos.instantaneos` e `fatura.chora`) sao a FASE 2 — canais de
achadinho puro, com link de afiliado — e ainda nao existem no Buffer.

Elas foram registradas assim mesmo, para a maquina saber que existem: sem
isso, um export chegando como `Content_fatura.chora.zip` pareceria um canal
novo surgido do nada, e nenhuma guarda saberia o nome.

Mas registrar canal SEM token e' perigoso pelo outro lado. O cabecalho do
`canais_registro.py` conta o que ja' aconteceu: quando o nome nao bate, o
workflow cai no `else` e publica com o token de OUTRO canal, em silencio.

O QUE PRECISA SER PROVADO

  1. os campos do Buffer ficam VAZIOS, nao inventados. Um id plausivel porem
     falso e' pior que nenhum: publica no lugar errado sem dar sinal.
  2. canal sem id do Buffer NAO entra no escopo do motor nem no
     `conferir_postados` — ou seja, nada que publica ou confere o alcanca.
  3. ⚠️ CASO NEGATIVO: os canais de verdade CONTINUAM completos e no escopo.
     Um teste que so' olha os dois novos passaria com o registro inteiro
     zerado — e aí a operacao inteira estaria fora do ar, calada.
  4. o `canonico()` reconhece os nomes novos: e' ele que traduz o que vem do
     export e do manifesto.

Roda com: python teste/teste_canal_sem_buffer.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import canais_registro as cr
from engine import escopo

falhas = 0


def checar(cond, recado):
    global falhas
    if cond:
        print(f"  ok  {recado}")
    else:
        print(f"  FALHOU  {recado}")
        falhas += 1


SEM_BUFFER = ("achadinhos.instantaneos", "fatura.chora")
COM_BUFFER = ("modofuturo", "semanestesia.pod", "atefalhar",
              "truque.importado", "cozinha.importada")

print("1. os dois da FASE 2 estao registrados, e com os campos do Buffer VAZIOS")
for n in SEM_BUFFER:
    c = cr.CANAIS.get(n)
    checar(c is not None, f"{n} esta' no registro")
    if c:
        checar(c.org == "" and c.canal_id == "" and c.env == "",
               f"{n}: org/canal_id/env vazios, nao inventados")
        checar(c.motor is False, f"{n}: motor=False")

print("\n2. e por isso nada que publica os alcanca")
import conferir_postados as cp
for n in SEM_BUFFER:
    checar(n not in escopo.CANAIS_DO_MOTOR, f"{n} fora do escopo do motor")
    checar(n not in cp.CANAIS, f"{n} fora do conferir_postados")

print("\n3. CASO NEGATIVO: os canais de verdade continuam inteiros e no escopo")
# ⚠️ Sem isto, um registro inteiramente zerado passaria no teste 2 — e a
# operacao estaria fora do ar em silencio, com a suite verde.
for n in COM_BUFFER:
    c = cr.CANAIS.get(n)
    checar(c is not None, f"{n} esta' no registro")
    if c:
        checar(bool(c.org and c.canal_id and c.env),
               f"{n}: org, canal_id e env PREENCHIDOS")
checar("modofuturo" in escopo.CANAIS_DO_MOTOR,
       "modofuturo continua no escopo do motor")
checar(len(escopo.CANAIS_DO_MOTOR) == 4,
       f"4 canais no escopo (veio {len(escopo.CANAIS_DO_MOTOR)}) — "
       "cozinha e' motor=False, os dois da fase 2 tambem")

print("\n4. o canonico() traduz os nomes novos (e' ele que le' export e manifesto)")
checar(cr.canonico("fatura.chora") == "fatura.chora", "fatura.chora")
checar(cr.canonico("fatura") == "fatura.chora", "apelido 'fatura'")
checar(cr.canonico("instantaneos") == "achadinhos.instantaneos",
       "apelido 'instantaneos'")
checar(cr.canonico("achadinho.make") == "truque.importado",
       "achadinho.make continua caindo em truque.importado")

print("\n5. e o registro tem SETE contas, que e' o que o app mostra")
checar(len(cr.CANAIS) == 7, f"{len(cr.CANAIS)} contas (esperado 7)")

if falhas:
    print(chr(10) + f"{falhas} FALHA(S)")
    sys.exit(1)
print(chr(10) + "tudo verde")
