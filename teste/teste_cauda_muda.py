# -*- coding: utf-8 -*-
"""A cauda muda e' aparada — e o CASO NEGATIVO e' quem prova o detector.

Com dublagem, a trilha e' silencio do tamanho do clipe com as frases coladas
por cima: se a fala acaba antes, o fim toca mudo. `engine/cauda.py` decide
ate' onde o video vai.

⚠️ POR QUE O CASO NEGATIVO E' MAIS DA METADE DESTE ARQUIVO. Um "detector" que
manda aparar SEMPRE passa em qualquer teste que so' mostre o caso positivo — e
aparar sempre encurtaria todo clipe do motor em CAUDA_MARGEM_S, inclusive os
que nao tem cauda nenhuma, e derrubaria abaixo de DUR_MIN os que estao no
limite. Sao QUATRO recusas, e cada uma tem um motivo diferente:

    sem dublagem      o audio original toca ate' o fim, nao e' mudo
    sem palavra       nao da' pra saber onde a fala acabou
    cauda pequena     sobra curta le' como fechamento, nao como falha
    piso de dinheiro  DUR_MIN e' o que garante monetizacao

E as recusas NAO sao intuicao: cada uma corresponde a um `return None` escrito
no modulo, e a lista aqui e' a lista de la'.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import cauda  # noqa: E402

falhas = []


def palavras_ate(fim_s: float) -> list[dict]:
    return [{"palavra": "oi", "inicio": 0.0, "fim": 1.0},
            {"palavra": "tchau", "inicio": fim_s - 0.5, "fim": fim_s}]


# ---------------------------------------------------------------- POSITIVO
# clipe de 90s, fala acaba aos 70s -> 20s mudos, apara
u = cauda.duracao_util(90.0, palavras_ate(70.0), True, 65.0)
if u is None:
    falhas.append("20s de cauda muda e nao aparou")
elif abs(u - (70.0 + cauda.CAUDA_MARGEM_S)) > 0.001:
    falhas.append(f"aparou no lugar errado: {u} (esperado "
                  f"{70.0 + cauda.CAUDA_MARGEM_S})")

# o fim da fala e' o MAIOR fim, nao o da ultima da lista (fora de ordem)
fora = [{"palavra": "b", "inicio": 60.0, "fim": 70.0},
        {"palavra": "a", "inicio": 1.0, "fim": 2.0}]
if abs(cauda.fim_da_fala(fora) - 70.0) > 0.001:
    falhas.append("fim_da_fala nao pega o maior fim quando a lista esta' "
                  "fora de ordem")

# ---------------------------------------------------------------- NEGATIVOS
# 1. sem dublagem: o audio original toca ate' o fim
if cauda.duracao_util(90.0, palavras_ate(70.0), False, 65.0) is not None:
    falhas.append("NEGATIVO: aparou um clipe SEM dublagem")

# 2. sem palavra: nao da' pra saber onde a fala acabou
if cauda.duracao_util(90.0, [], True, 65.0) is not None:
    falhas.append("NEGATIVO: aparou sem ter timing de fala")
if cauda.duracao_util(90.0, None, True, 65.0) is not None:
    falhas.append("NEGATIVO: aparou com palavras=None")

# 3. cauda pequena: sobra de meio segundo e' fechamento, nao falha
if cauda.duracao_util(90.0, palavras_ate(89.5), True, 65.0) is not None:
    falhas.append("NEGATIVO: aparou uma cauda de 0,5s")
# e a fronteira exata do limiar tambem NAO apara
if cauda.duracao_util(90.0, palavras_ate(90.0 - cauda.CAUDA_MAX_S),
                      True, 65.0) is not None:
    falhas.append("NEGATIVO: aparou exatamente em CAUDA_MAX_S (o limiar e' "
                  "'maior que', nao 'maior ou igual')")

# 4. o piso de dinheiro manda mais: aparar deixaria abaixo de DUR_MIN
if cauda.duracao_util(70.0, palavras_ate(50.0), True, 65.0) is not None:
    falhas.append("NEGATIVO: aparou pra 50,6s com DUR_MIN=65 — clipe "
                  "desmonetizado pra tirar silencio")
# e o vizinho que passa raspando TEM de aparar, senao a guarda acima esta'
# recusando por outro motivo que nao o piso
if cauda.duracao_util(90.0, palavras_ate(65.0), True, 65.0) is None:
    falhas.append("aparar pra 65,6s (acima do piso) foi recusado — a guarda "
                  "do DUR_MIN esta' larga demais")

# ------------------------------------------------ o modulo nao mente sozinho
if cauda.CAUDA_MAX_S <= cauda.CAUDA_MARGEM_S:
    falhas.append("CAUDA_MAX_S <= CAUDA_MARGEM_S: aparar deixaria uma cauda "
                  "que o proprio limiar consideraria grande")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_cauda_muda: apara acima de {cauda.CAUDA_MAX_S}s, deixa "
      f"{cauda.CAUDA_MARGEM_S}s de respiro, e recusa nos 4 casos negativos")
