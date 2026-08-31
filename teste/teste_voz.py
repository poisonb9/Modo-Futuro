# -*- coding: utf-8 -*-
"""Teste da escolha de voz por canal e da guarda que a protege.

OS CASOS NEGATIVOS SAO A METADE QUE IMPORTA

Uma guarda que so' RECUSA reprova em producao: se ela derrubasse o disparo
normal, nenhum dos quatro canais publicaria. E uma que so' ACEITA nao e'
guarda — era o estado ate' 30/08/2026, quando VOZ_CANAL simplesmente nao
existia e a voz clonada vencia calada.

Entao cada regra e' verificada dos dois lados:

  positivo  pedir voz feminina COM clonagem ligada        -> DERRUBA
  negativo  disparo de sempre, sem VOZ_CANAL              -> nao derruba
            pedir voz feminina COM clonagem desligada     -> nao derruba
            VOZ_CLONADA=0 sozinho (sem VOZ_CANAL)         -> nao derruba

E o mais importante deles: **sem VOZ_CANAL, tudo tem que sair exatamente como
antes da mudanca.** Se este arquivo passar mas o padrao mudar, os quatro
canais existentes trocam de voz sem ninguem pedir.

Roda com: python teste/teste_voz.py
"""
import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import voz

falhas = 0


def ambiente(**kv):
    for k in ("VOZ_CANAL", "VOZ_CLONADA"):
        os.environ.pop(k, None)
    for k, v in kv.items():
        if v is not None:
            os.environ[k] = v


def caso(nome, esperado_derruba, voz_esperada=None, clone_esperado=None, **env):
    global falhas
    ambiente(**env)
    antes = falhas
    derrubou, recado = False, ""
    try:
        voz.conferir()
    except RuntimeError as e:
        derrubou, recado = True, str(e)

    if derrubou != esperado_derruba:
        virou = "derrubou" if derrubou else "seguiu"
        queria = "derrubar" if esperado_derruba else "seguir"
        print(f"  FALHOU {nome}: {virou}, mas era pra {queria}")
        falhas += 1
        return

    if derrubou:
        # Derrubar sem dizer o conserto e' quase tao ruim quanto nao derrubar.
        for pedaco in ("VOZ_CLONADA=0", "silencio"):
            if pedaco.lower() not in recado.lower():
                print(f"  FALHOU {nome}: o recado nao menciona {pedaco!r}")
                falhas += 1
    else:
        if voz_esperada is not None and voz.escolhida() != voz_esperada:
            print(f"  FALHOU {nome}: voz {voz.escolhida()!r}, "
                  f"esperada {voz_esperada!r}")
            falhas += 1
        if clone_esperado is not None and voz.clonada_ativa() != clone_esperado:
            print(f"  FALHOU {nome}: clonada_ativa={voz.clonada_ativa()}, "
                  f"esperado {clone_esperado}")
            falhas += 1

    if falhas == antes:
        marca = "derruba" if derrubou else " segue "
        print(f"  ok  [{marca}]  {nome}")


# ---------------------------------------------------------------- POSITIVO
# A combinacao que produziria a voz do Bryan num canal de maquiagem.
caso("feminina pedida COM clonagem ligada", True, VOZ_CANAL="feminina")
caso("nome completo do edge-tts, clonagem ligada", True,
     VOZ_CANAL="pt-BR-ThalitaMultilingualNeural")

# ---------------------------------------------------------------- NEGATIVOS
# O disparo de sempre. Este e' o caso que protege os quatro canais que ja'
# existem: NADA pode mudar pra eles.
caso("disparo de sempre (nada no ambiente)", False,
     voz_esperada="pt-BR-AntonioNeural", clone_esperado=True)

caso("feminina COM clonagem desligada", False,
     voz_esperada="pt-BR-FranciscaNeural", clone_esperado=False,
     VOZ_CANAL="feminina", VOZ_CLONADA="0")

caso("thalita por apelido, clonagem desligada", False,
     voz_esperada="pt-BR-ThalitaMultilingualNeural", clone_esperado=False,
     VOZ_CANAL="thalita", VOZ_CLONADA="0")

caso("nome completo do edge-tts, clonagem desligada", False,
     voz_esperada="pt-BR-FranciscaNeural", clone_esperado=False,
     VOZ_CANAL="pt-BR-FranciscaNeural", VOZ_CLONADA="false")

caso("VOZ_CLONADA=0 sozinho", False,
     voz_esperada="pt-BR-AntonioNeural", clone_esperado=False,
     VOZ_CLONADA="0")

caso("VOZ_CANAL vazio conta como nao pedido", False,
     voz_esperada="pt-BR-AntonioNeural", clone_esperado=True,
     VOZ_CANAL="   ")

# --------------------------------------------- o modulo que de fato dubla
# `dublagem.VOZ_PADRAO` e' o valor que o `main.py` acaba usando: ele chama
# gerar_trilha SEM passar `voz`. Testar so' o voz.py deixaria de fora
# justamente o fio que liga a escolha ao audio.
ambiente(VOZ_CANAL="feminina", VOZ_CLONADA="0")
import engine.dublagem as dub
importlib.reload(dub)
if dub.VOZ_PADRAO != "pt-BR-FranciscaNeural":
    print(f"  FALHOU dublagem: VOZ_PADRAO={dub.VOZ_PADRAO!r}")
    falhas += 1
else:
    print("  ok  [ segue ]  dublagem.VOZ_PADRAO segue a VOZ_CANAL")

ambiente()
importlib.reload(dub)
if dub.VOZ_PADRAO != "pt-BR-AntonioNeural":
    print(f"  FALHOU dublagem: sem VOZ_CANAL virou {dub.VOZ_PADRAO!r}")
    falhas += 1
else:
    print("  ok  [ segue ]  sem VOZ_CANAL, dublagem volta ao masculino")


# ─────────────────────────────────────────────────────────────────────────
# ⚠️ A GUARDA QUE FALTAVA — e por que este teste passou com o mapa errado.
#
# Ate' 31/08/2026 o mapa apontava `thalita` para `pt-BR-ThalitaNeural`, um
# nome que NAO EXISTE no catalogo do edge-tts (so' ha' tres vozes pt-BR:
# Antonio, Francisca e ThalitaMultilingual). O teste passava porque ele
# comparava o mapa com uma constante escrita no proprio teste — os dois
# concordavam, e os dois estavam errados.
#
# Comparar o codigo com uma copia da mesma suposicao nao verifica nada. O que
# verifica e' perguntar ao edge-tts quais vozes existem de verdade.
#
# O catalogo vem da rede. Sem rede o teste AVISA e segue: falha de rede nao
# pode reprovar uma suite que roda offline o tempo todo.
print()
print("[extra] as vozes do mapa existem no catalogo do edge-tts?")
try:
    import asyncio
    import edge_tts
    from engine import voz as vozmod

    reais = {v["ShortName"] for v in asyncio.run(edge_tts.list_voices())}
except Exception as e:
    print(f"  aviso  catalogo indisponivel ({str(e)[:50]}) — checagem pulada")
else:
    for apelido, nome in sorted(vozmod.VOZES.items()):
        if nome in reais:
            print(f"  ok     {apelido:<12} -> {nome}")
        else:
            print(f"  FALHOU {apelido:<12} -> {nome} NAO EXISTE no edge-tts")
            falhas += 1
    ptbr = sorted(v for v in reais if v.startswith("pt-BR"))
    print(f"  (o catalogo pt-BR tem {len(ptbr)}: {', '.join(ptbr)})")

if falhas:
    print(chr(10) + f"{falhas} FALHA(S)")
    sys.exit(1)
print(chr(10) + "tudo verde")
