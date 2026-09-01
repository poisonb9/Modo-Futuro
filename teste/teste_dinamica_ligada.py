# -*- coding: utf-8 -*-
"""A dinamica esta' LIGADA na sintese — e falha ABERTA quando nao da'.

Pedido do Bryan em 01/09/2026: aplicar em TODOS os videos que vierem.

⚠️ O CASO NEGATIVO E' O QUE PROTEGE A OPERACAO. Se a medicao falhar (fonte
ausente, ffmpeg mudo, segmento sem tempo), a dublagem TEM de sair assim mesmo.
Uma dublagem sem dinamica e' pior; uma dublagem que nao sai por causa de uma
medicao e' muito pior — e seria uma regressao causada por um recurso de
acabamento.

⚠️ E o parametro de enfase e' descoberto EM EXECUCAO. O Chatterbox nao roda na
maquina do Bryan, entao a assinatura nao pode ser suposta: passar um argumento
que a versao instalada nao conhece derrubaria toda sintese com TypeError,
depois do run ja' ter pago corte e transcricao.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import voz_clonada as v  # noqa: E402

falhas = []


class ModeloComEnfase:
    def generate(self, texto, audio_prompt_path=None, language_id=None,
                 exaggeration=0.5):
        return None


class ModeloSemEnfase:
    def generate(self, texto, audio_prompt_path=None, language_id=None):
        return None


# 1. modelo que ACEITA -> o parametro vai
if v._enfase_aceita(ModeloComEnfase(), 0.7) != {"exaggeration": 0.7}:
    falhas.append("o modelo aceita enfase e ela nao foi passada")

# 2. NEGATIVO: modelo que NAO aceita -> nada vai (senao TypeError em producao)
if v._enfase_aceita(ModeloSemEnfase(), 0.7) != {}:
    falhas.append("passou 'exaggeration' a um modelo que nao aceita — quebraria tudo")

# 3. NEGATIVO: sem medida, nada vai
if v._enfase_aceita(ModeloComEnfase(), None) != {}:
    falhas.append("sem medida deveria usar o padrao do modelo")

# 4. as janelas cobrem o intervalo falado, e sao aproximacao proporcional
seg = [{"inicio": 10.0, "fim": 40.0, "texto": "x"}]
jan = v._janelas_das_frases(seg, ["curta", "uma frase bem mais comprida"])
if len(jan) != 2:
    falhas.append(f"janelas: esperava 2, veio {len(jan)}")
elif not (abs(jan[0][0] - 10.0) < 1e-6 and abs(jan[-1][1] - 40.0) < 1e-6):
    falhas.append(f"as janelas nao cobrem o intervalo falado: {jan}")
elif (jan[0][1] - jan[0][0]) >= (jan[1][1] - jan[1][0]):
    falhas.append("a frase mais longa nao recebeu janela maior")

# 5. NEGATIVO: segmento sem tempo nao pode explodir — devolve vazio
if v._janelas_das_frases([{"texto": "sem tempo"}], ["a"]) != []:
    falhas.append("segmento sem tempo deveria devolver vazio, nao estourar")
if v._janelas_das_frases([], []) != []:
    falhas.append("entrada vazia deveria devolver vazio")

# 6. o teto/piso de pausa existe e e' curto — pausa longa mata retencao
if not (0.05 <= v._PAUSA_MIN_S < v._PAUSA_MAX_S <= 1.0):
    falhas.append(f"limites de pausa fora do razoavel: "
                  f"{v._PAUSA_MIN_S}-{v._PAUSA_MAX_S}")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print("[ok] teste_dinamica_ligada: enfase so' quando o modelo aceita, "
      "janelas proporcionais, e falha aberta sem medida")
