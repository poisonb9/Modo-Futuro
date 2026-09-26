# -*- coding: utf-8 -*-
"""Clipes de 30-45 s nos canais curtos; Sem Anestesia e cozinha seguem longos.

POR QUE EXISTE

26/09/2026, dono: "vamos em videos de 30-45s para esse canal e outros tirando
o sem anestesia e o de cozinha". A faixa sai do canal do corte
(CANAL_ESPERADO). O risco que este teste guarda e' o contrario do pedido: o
Sem Anestesia ou a cozinha encurtarem calados, ou o prompt dos longos mudar
uma virgula.
"""
import importlib
import os
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

falhas = []


def checar(ok, msg):
    print(("  ok    " if ok else "  FALHA ") + msg)
    if not ok:
        falhas.append(msg)


def carregar(canal):
    if canal is None:
        os.environ.pop("CANAL_ESPERADO", None)
    else:
        os.environ["CANAL_ESPERADO"] = canal
    os.environ.pop("SELECAO_MODO", None)
    import config
    importlib.reload(config)
    from engine import selecao
    importlib.reload(selecao)
    return config, selecao


print("[1] faixa por canal")
for canal, esperado in [("modofuturo", (30, 45)), ("truque.importado", (30, 45)),
                        ("atefalhar", (30, 45)), ("semanestesia.pod", (65, 110)),
                        ("cozinha.importada", (65, 110)),
                        ("cozinha.internacional", (65, 110)),   # apelido antigo
                        (None, (65, 110)), ("canal-que-nao-existe", (65, 110))]:
    c, _ = carregar(canal)
    checar((c.DUR_MIN, c.DUR_MAX) == esperado, f"{canal}: {c.DUR_MIN}-{c.DUR_MAX}s")

print("\n[2] o prompt dos longos e' o de antes, byte a byte")
c, s = carregar("semanestesia.pod")
novo = s.PROMPT.format(tipo="vídeo", n=5, criterio=s._criterio(),
                       dmin=c.DUR_MIN, dmax=c.DUR_MAX,
                       regra_duracao=s._regra_duracao(c.DUR_MIN, c.DUR_MAX))
try:
    antes = subprocess.run(["git", "show", "HEAD:engine/selecao.py"], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           check=True).stdout
except Exception as e:
    print(f"  aviso  git indisponivel ({str(e)[:40]})")
else:
    if "{regra_duracao}" in antes:
        print("  aviso  HEAD ja' tem a regra por canal; prova nao se aplica")
    else:
        i = antes.index('PROMPT = """')
        j = antes.index('"""', i + 12) + 3
        ns = {}
        exec(compile(antes[i:j], "antes", "exec"), ns)
        velho = ns["PROMPT"].format(tipo="vídeo", n=5, criterio=s._criterio(),
                                    dmin=c.DUR_MIN, dmax=c.DUR_MAX)
        checar(velho == novo, "prompt longo IDENTICO ao do git HEAD")

print("\n[3] o prompt curto nao fala de minimo de dinheiro")
c, s = carregar("modofuturo")
regra = s._regra_duracao(c.DUR_MIN, c.DUR_MAX)
checar("só paga" not in regra and "35-45s" in regra, "regra curta: 35-45s, sem piso de 60s")
checar("{" not in s.PROMPT.format(tipo="vídeo", n=5, criterio="", dmin=30, dmax=45,
                                  regra_duracao=regra).split("REGRAS DURAS")[1][:600],
       "nenhum placeholder sobrou nas regras")

carregar(None)
print("\ntudo verde" if not falhas else f"\n{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
