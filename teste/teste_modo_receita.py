# -*- coding: utf-8 -*-
"""Modo receita: a cozinha agora é deste motor (26/09/2026, decisão do dono).

POR QUE EXISTE

Em 03/09/2026 oito receitas foram cortadas neste motor e publicadas com °F,
xícara e polegada, porque a conversão de medida só existia no motor da
cozinha (`pipeline`). O dono decidiu trazer a cozinha para cá; a conversão
veio junto. Este teste garante que ela está LIGADA em todo o caminho:

  [1] seleção: `SELECAO_MODO=receita` usa o critério de receita e o teto 180 s;
      os outros modos não mudam
  [2] tradução: a medida é convertida ANTES de ir ao Gemini
  [3] voz: "240 g" é DITO "gramas" no modo receita; NEGATIVO: fora dele, "5g"
      (chips) não vira grama
  [4] conferência: compara com a forma falada da unidade
  [5] cozinha SEMPRE em modo receita (main força), guardas de abertura
      ligadas, receita escrita na legenda e no post.json
  [6] o vigia dispara a cozinha em modo receita com a voz da Bruna

Roda com: python teste/teste_modo_receita.py
"""
import asyncio
import os
import sys
import types
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("GEMINI_API_KEY", "x-para-o-teste")

import config  # noqa: E402
from engine import selecao, traducao, conferencia, legenda_post  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def modo(m):
    if m is None:
        os.environ.pop("SELECAO_MODO", None)
    else:
        os.environ["SELECAO_MODO"] = m


print(__doc__.splitlines()[0])

print("\n[1] seleção")
modo("receita")
checar("CORTE DE RECEITA" in selecao._criterio() and "PRATO PRONTO" in selecao._criterio(),
       "receita usa o critério de receita")
checar(config.modo_receita(), "config.modo_receita() liga")
modo("procedimento")
checar("PROCEDIMENTO" in selecao._criterio() and not config.modo_receita(), "procedimento intacto")
modo(None)
checar("GPC" in selecao._criterio() and not config.modo_receita(), "retórico intacto (sem modo)")
src_sel = (RAIZ / "engine" / "selecao.py").read_text(encoding="utf-8")
checar(src_sel.count('in ("procedimento", "receita")') == 2, "teto de 180 s vale para receita (2 lugares)")

print("\n[2] tradução converte antes do Gemini")
enviado = {}


class Resp:
    status_code = 200

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}

    def raise_for_status(self):
        pass


def post_falso(url, json=None, **kw):
    enviado["texto"] = str(json)
    return Resp()


traducao.requests.post = post_falso
traducao.keys.gemini = lambda: types.SimpleNamespace(proxima=lambda: "k", __len__=lambda s: 1)


class Rot:
    def proxima(self):
        return "k"

    def __len__(self):
        return 1


traducao.keys.gemini = lambda: Rot()
modo("receita")
try:
    traducao._traduzir_texto("Add 1 cup of flour, bake at 350 F.")
except Exception as e:
    print(f"       (resposta falsa: {type(e).__name__})")
checar("120 g" in enviado.get("texto", "") and "180°C" in enviado.get("texto", ""),
       "o Gemini recebe 120 g e 180°C")
checar("1 cup" not in enviado.get("texto", ""), "e não recebe 'cup'")
modo(None)
enviado.clear()
try:
    traducao._traduzir_texto("Add 1 cup of flour.")
except Exception:
    pass
checar("1 cup" in enviado.get("texto", ""), "NEGATIVO: fora do modo receita, nada é convertido")

print("\n[3] voz (edge-tts)")
from engine import dublagem  # noqa: E402
falado = {}


class ComFalso:
    def __init__(self, texto, voice=None, **kw):
        falado["t"] = texto

    async def save(self, destino):
        pass


sys.modules["edge_tts"] = types.SimpleNamespace(Communicate=ComFalso)
modo("receita")
asyncio.run(dublagem._sintetizar("Use 240 g de farinha", Path("x.mp3"), "v"))
checar("gramas" in falado["t"], f"receita: diz 'gramas' ({falado['t']!r})")
modo(None)
# "5G" (rede) como o canal de chips escreve. ⚠️ "5g" minúsculo já virava
# "gramas" ANTES do modo receita, pela regra de unidade do numeros.py.
asyncio.run(dublagem._sintetizar("A rede 5G e o chip de 3 nm", Path("x.mp3"), "v"))
checar("grama" not in falado["t"], f"chips: '5G' não vira grama ({falado['t']!r})")
asyncio.run(dublagem._sintetizar("Espere 20 min", Path("x.mp3"), "v"))
checar("20 min" in falado["t"] or "vinte min" in falado["t"],
       f"NEGATIVO: fora da receita o conversoes.para_fala não roda ({falado['t']!r})")
src_vc = (RAIZ / "engine" / "voz_clonada.py").read_text(encoding="utf-8")
checar("conversoes.para_fala(texto)" in src_vc and "config.modo_receita()" in src_vc,
       "a voz A (Chatterbox) também expande unidade no modo receita")

print("\n[4] conferência")
modo("receita")
checar(any("gramas" in f for f in conferencia.formas_faladas("Use 240 g de farinha")),
       "compara com 'gramas'")
modo(None)

print("\n[5] main e legenda")
src_main = (RAIZ / "main.py").read_text(encoding="utf-8")
checar('os.environ["SELECAO_MODO"] = "receita"' in src_main
       and '== "cozinha.importada"' in src_main, "cozinha sempre em modo receita")
checar("abertura.orfa, abertura.so_encerramento" in src_main, "guardas de abertura ligadas")
checar('"receita_texto",' in src_main, "receita_texto vai pro post.json")
leg = legenda_post.montar({"titulo": "T", "descricao": "D", "receita_texto": "R", "tags": ["x"]})
checar(leg.index("D") < leg.index("R") < leg.index("#x"), "legenda: descrição, receita, hashtags")
from engine import canais_registro as cr  # noqa: E402
checar("cozinha.importada" in cr.do_motor(), "a cozinha é deste motor")

print("\n[6] disparo")
src_vig = (RAIZ / "vigia_raw.py").read_text(encoding="utf-8")
checar('"cozinha.importada": {"selecao_modo": "receita", "amostra_voz": "bruna"}' in src_vig,
       "vigia: cozinha em receita, voz da Bruna")
src_ag = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")
checar('== "cozinha.importada"' in src_ag and "refeicao.casar(fila, horarios)" in src_ag,
       "agendador: receita na hora da refeição, só na cozinha")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
