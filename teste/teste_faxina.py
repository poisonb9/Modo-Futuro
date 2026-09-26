# -*- coding: utf-8 -*-
"""Guarda da faxina (ferramentas/faxina.py) e da cópia local apagada no envio.

POR QUE EXISTE

26/09/2026, ao subir o download para 1440p (dono: "não deixar lixo no pc").
O `apagar_local` do envio ao Drive existia e ninguém lia; o processar_lista
nunca apagava.

  [1] a faxina acha cada categoria pela idade certa
  [2] NEGATIVO: arquivo novo, _privado e estado nunca entram
  [3] o envio apaga a cópia SÓ depois de conferir o tamanho no Drive,
      e o processar_lista só apaga depois das três etapas

Roda com: python teste/teste_faxina.py
"""
import os
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "ferramentas"))

import faxina  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def criar(p: Path, dias: float, tam: int = 10):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x" * tam)
    t = time.time() - dias * 86400
    os.utime(p, (t, t))
    return p


print(__doc__.splitlines()[0])
R = Path(tempfile.mkdtemp())
velho_bruto = criar(R / "trabalho/brutos/a.mp4", 4, 1000)
novo_bruto = criar(R / "trabalho/brutos/b.mp4", 1)
parcial = criar(R / "trabalho/brutos/c.mp4.part", 0)
dub = criar(R / "trabalho/dub_01.wav", 2)
dub_novo = criar(R / "trabalho/clip_02.flac", 0.2)
teste_velho = criar(R / "saida/teste_camada/x.mp4", 9)
os.utime(R / "saida/teste_camada", (time.time() - 9 * 86400,) * 2)
privado = criar(R / "_privado/previas/y.mp4", 30)
estado = criar(R / "estado/z.json", 30)

achados = {p.resolve(): c for c, p, _ in faxina.candidatos(R)}
print(f"       {sorted((c, p.name) for p, c in achados.items())}")

print("\n[1] cada categoria pela idade")
checar(achados.get(velho_bruto.resolve()) == "bruto antigo", "bruto de 4 dias sai")
checar(achados.get(parcial.resolve()) == "download interrompido", ".part sai sempre")
checar(achados.get(dub.resolve()) == "intermediario de corte", "intermediário de 2 dias sai")
checar(achados.get((R / "saida/teste_camada").resolve()) == "pasta de teste", "teste de 9 dias sai")

print("\n[2] NEGATIVO: o que fica")
for p, nome in ((novo_bruto, "bruto de 1 dia"), (dub_novo, "intermediário recente"),
                (privado, "_privado"), (estado, "estado")):
    checar(p.resolve() not in achados, f"{nome} fica")

print("\n[3] o envio e o processar_lista")
env = (RAIZ / "enviar_bruto_drive.py").read_text(encoding="utf-8")
checar("if apagar_local:" in env and "no_drive == local" in env,
       "enviar apaga só com tamanho conferido no Drive")
checar("apagar_local=not a.manter_local" in env, "linha de comando apaga por padrão")
pl = (RAIZ / "processar_lista.py").read_text(encoding="utf-8")
checar('"--manter-local"' in pl, "processar_lista pede pra manter no envio...")
checar(pl.index("marcar(vid") < pl.index("destino.unlink(missing_ok=True)"),
       "...e apaga ele mesmo DEPOIS de marcar as três etapas")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
