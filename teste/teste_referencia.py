# -*- coding: utf-8 -*-
"""Clipes de referência (ferramentas/referencia.py): sempre prévia, campos válidos.

POR QUE EXISTE

26/09/2026: os 3 clipes fixos (make, Sem Anestesia, chips) em que toda
mudança é refeita. Disparar errado aqui PUBLICARIA um clipe de teste, então:

  [1] todo disparo leva previa=true (nada vai pro Drive de postagem/Buffer)
  [2] todo campo mandado existe nos inputs do cortar_de_bruto.yml
  [3] recorte só vai quando está fixado; vazio = o motor escolhe
  [4] voice-over exige fala_literal (o motor recusa a combinação errada)
  [5] congelar lê o trecho do post.json
  [6] a config real (se existir nesta máquina) tem os 4 e nada publicável

Roda com: python teste/teste_referencia.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "ferramentas"))

import yaml  # noqa: E402
import referencia  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def pares(lst):
    return dict(x.split("=", 1) for x in lst[1::2])


print(__doc__.splitlines()[0])
cfg = {"pasta_drive": "P", "conta": "reserva", "clipes": []}
fixo = {"nome": "make", "drive_file_id": "A", "nome_arquivo": "a.mp4", "canal": "truque.importado",
        "amostra_voz": "bruna", "recorte": "10.0-95.0", "fundo_original": "true"}
livre = {"nome": "chips", "drive_file_id": "B", "nome_arquivo": "b.mp4", "canal": "modofuturo"}
vo = {"nome": "sa", "drive_file_id": "C", "nome_arquivo": "c.mp4", "canal": "semanestesia.pod",
      "voice_over": "true", "fala_literal": "true"}

print("\n[1] sempre prévia")
for c in (fixo, livre, vo):
    checar(pares(referencia.campos(cfg, c)).get("previa") == "true", f"{c['nome']}: previa=true")

print("\n[2] campos existem no workflow")
w = yaml.safe_load((RAIZ / ".github/workflows/cortar_de_bruto.yml").read_text(encoding="utf-8"))
inputs = set((w.get(True) or w.get("on"))["workflow_dispatch"]["inputs"])
for c in (fixo, livre, vo):
    sobra = set(pares(referencia.campos(cfg, c))) - inputs
    checar(not sobra, f"{c['nome']}: nenhum campo desconhecido ({sobra or 'ok'})")

print("\n[3] recorte")
checar(pares(referencia.campos(cfg, fixo)).get("recorte") == "10.0-95.0", "fixo vai")
checar("recorte" not in pares(referencia.campos(cfg, livre)), "vazio não vai")

print("\n[4] voice-over com fala literal")
p = pares(referencia.campos(cfg, vo))
checar(p["voice_over"] == "true" and p["fala_literal"] == "true", "Sem Anestesia coerente")

print("\n[5] congelar")
checar(referencia.trecho_do_post({"inicio_s": 12.345, "fim_s": 98.7}) == "12.3-98.7", "12.3-98.7")
checar(referencia.trecho_do_post({}) is None, "sem tempos = None")

print("\n[6] config real")
if referencia.CONFIG.exists():
    real = json.loads(referencia.CONFIG.read_text(encoding="utf-8"))
    fixos = [c["nome"] for c in real["clipes"] if not c.get("voz_original_db")]
    checar(sorted(fixos) == ["chips", "cozinha", "make", "semanestesia"],
           "os 4 clipes (cozinha entrou em 26/09 com o modo receita)")
    # variante A/B da voz original baixa: SO' no make (dono, 26/09: "chips nao")
    var = [c for c in real["clipes"] if c.get("voz_original_db")]
    checar(all(c["canal"] == "truque.importado" for c in var),
           "voz original por baixo so' em variante do make")
    for c in var:
        checar(pares(referencia.campos(real, c)).get("voz_original_db") == c["voz_original_db"],
               f"{c['nome']}: a variante chega ao workflow")
    coz = [c for c in real["clipes"] if c["nome"] == "cozinha"]
    checar(bool(coz) and coz[0]["selecao_modo"] == "receita" and coz[0]["amostra_voz"] == "bruna",
           "cozinha em modo receita, voz da Bruna")
    for c in real["clipes"]:
        pr = pares(referencia.campos(real, c))
        checar(pr["previa"] == "true" and not (pr["voice_over"] == "true" and pr["fala_literal"] != "true"),
               f"{c['nome']}: prévia e coerente")
else:
    print("       (pulado: config só existe na máquina do dono)")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
