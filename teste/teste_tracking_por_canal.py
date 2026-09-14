# -*- coding: utf-8 -*-
"""O tracking_id sai do CANAL, e canal sem id cai no que PAGA.

⚠️ O erro que esta guarda impede nao aparece em log nenhum: link com
tracking_id invalido ABRE A PAGINA NORMALMENTE e nao paga. A venda acontece
e ninguem ve' que ela se perdeu.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import garimpo  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


print("1. o canal escolhe o tracking_id")
garimpo.TRACKING = {"cozinha.importada": "achadinhochef"}
checar(garimpo.tracking_de("cozinha.importada") == "achadinhochef",
       "canal com id usa o id dele")

print("")
print("2. NEGATIVO - canal SEM id nao inventa nome")
# ⚠️ O jeito obvio de errar aqui seria derivar o id do nome do canal
# ("cozinha.importada" -> "cozinhaimportada"). Isso gera link que nao paga.
for canal in ("truque.importado", "atefalhar", "canal.que.nao.existe", ""):
    checar(garimpo.tracking_de(canal) == "default",
           f"{canal or '(vazio)'} cai no default")

print("")
print("3. NEGATIVO - id so' entra depois de MEDIDO")
# ⚠️ Os nomes propostos estao COMENTADOS ate' existirem no Portals e
# passarem no teste/fumaca_tracking.py. Ligar antes e' pior que nao ligar.
garimpo.TRACKING = {}
fonte = Path("engine/garimpo.py").read_text(encoding="utf-8")
checar(garimpo.tracking_de("truque.importado") == "default",
       "com a tabela vazia, tudo cai no unico id medido")
checar("fumaca_tracking" in fonte,
       "o codigo aponta pra onde se prova um id novo")

print("")
print("4. o conserto nao pode voltar atras")
# ⚠️ `buscar` e' o UNICO lugar que importa: o promotion_link ja' vem
# carimbado com o id que ela pediu.
i = fonte.index("def buscar(")
corpo = fonte[i:fonte.index("def ", i + 10)]
checar("tracking_de(canal)" in corpo, "buscar() pede o id do canal")
checar('tracking_id="default"' not in corpo,
       "e nao tem mais o id fixo escrito na mao")

print("")
print("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde")
sys.exit(1 if falhas else 0)
