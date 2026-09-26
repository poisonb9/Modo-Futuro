# -*- coding: utf-8 -*-
"""modelo_texto.perguntar sem chave de reserva devolve None, nao explode.

POR QUE EXISTE

26/09/2026: 5 previas de referencia em paralelo secaram as chaves do Gemini;
`keys.openrouter()` LEVANTA quando nao ha' chave, e o A/B do titulo
(engine/ab_titulo.py) derrubou 2 clipes inteiros depois da dublagem pronta
("NENHUM clipe sobreviveu"). O contrato do modulo e' devolver None.

  [1] Gemini sem cota + sem chave OpenRouter -> None (sem excecao)
  [2] o A/B do titulo segue com o titulo original (grupo B_falhou)

Roda com: python teste/teste_modelo_texto_sem_reserva.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import ab_titulo, keys, modelo_texto  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


class _Seca:
    def __len__(self):
        return 2

    def proxima(self):
        return "chave"

    def queimar(self, c):
        pass


class _Resp:
    status_code = 429


def _sem_reserva():
    raise RuntimeError("Nenhuma chave OPENROUTER_API_KEY encontrada.")


keys.gemini, keys.openrouter = (lambda: _Seca()), _sem_reserva
modelo_texto.requests.post = lambda *a, **k: _Resp()

print("[1] sem cota e sem reserva")
try:
    r = modelo_texto.perguntar("oi")
    checar(r is None, "devolve None")
except Exception as e:
    checar(False, f"levantou {type(e).__name__}: {e}")

print("\n[2] o A/B do titulo nao derruba o clipe")
ab_titulo.LIGADO = True
c = {"titulo": "Wonhee conta a historia de terror que viveu", "inicio_s": 0}
achado = None
for fonte in ("a", "b", "c", "d", "e", "f"):
    if ab_titulo.grupo(fonte, 0) == "B":
        achado = fonte
        break
try:
    tela = ab_titulo.aplicar(c, achado or "a")
    checar(tela == c["titulo"], "titulo original na tela")
except Exception as e:
    checar(False, f"levantou {type(e).__name__}: {e}")

print(f"\n{'FALHOU: ' + str(len(falhas)) if falhas else 'tudo verde'}")
sys.exit(1 if falhas else 0)
