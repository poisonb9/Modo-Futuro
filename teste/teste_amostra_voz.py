# -*- coding: utf-8 -*-
"""A amostra clonada e' a do canal certo — e existe antes de gastar runner.

POR QUE EXISTE

Ate' 31/08/2026 a amostra era FIXA na voz do Bryan, em dois lugares que
precisavam concordar e ninguem checava:

    config.py   VOZ_CLONADA_AMOSTRA = vozes/bryan_amostra.wav
    workflow    baixa o file-id do Bryan e grava com esse nome

Isso travava o canal de maquiagem: voz masculina ali contradiz o publico, e o
edge-tts so' tem TRES vozes pt-BR — nenhuma agradou. A irma do Bryan, Bruna
Soares, gravou a amostra (autorizada por ela).

O RISCO QUE ESTE TESTE COBRE

Sao dois nomes que tem de casar: o que o workflow GRAVA em `vozes/` e o que o
`config.py` LE'. Se divergirem, o motor procura um arquivo que nao existe — e
descobre isso depois de baixar o bruto e comecar a cortar, com o runner ja'
gasto. E' a mesma familia de defeito que ja' custou tres runs hoje: a peca
existe, e a ponta que liga uma na outra falta.

⚠️ CASO NEGATIVO: sem `AMOSTRA_VOZ`, tem de continuar a do Bryan. Os quatro
canais que ja' rodam dependem disso, e uma troca silenciosa de voz nao levanta
excecao nenhuma — sai como clipe com a voz errada, publicado.

Roda com: python teste/teste_amostra_voz.py
"""
import importlib
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def amostra(valor):
    """Qual arquivo o config escolhe para um dado AMOSTRA_VOZ."""
    if valor is None:
        os.environ.pop("AMOSTRA_VOZ", None)
    else:
        os.environ["AMOSTRA_VOZ"] = valor
    import config
    importlib.reload(config)
    return Path(config.VOZ_CLONADA_AMOSTRA).name


print(__doc__.splitlines()[0])

# --- 1. o caso NEGATIVO, que protege os canais no ar ---------------------
print("\n[1] sem AMOSTRA_VOZ, continua a voz do Bryan")
checar(amostra(None) == "bryan_amostra.wav", "padrao e' bryan_amostra.wav")
checar(amostra("") == "bryan_amostra.wav", "string vazia tambem cai no padrao")

# --- 2. o caso positivo ---------------------------------------------------
print("\n[2] com AMOSTRA_VOZ, troca de verdade")
checar(amostra("bruna_amostra.wav") == "bruna_amostra.wav",
       "bruna_amostra.wav e' escolhida")
checar(amostra("  bruna_amostra.wav  ") == "bruna_amostra.wav",
       "espaco em volta nao atrapalha")

# --- 3. os DOIS NOMES tem de casar ---------------------------------------
print("\n[3] o nome que o workflow grava == o nome que o config le'")
yml = (RAIZ / ".github" / "workflows" / "cortar_de_bruto.yml").read_text(
    encoding="utf-8")

# nomes que o passo de download pode gravar
gravados = set(re.findall(r'NOME="([a-z_]+)"', yml))
checar(gravados == {"bruna_amostra", "bryan_amostra"},
       f"o workflow grava {sorted(gravados)}")

# nomes que o env manda o config ler
lidos = set(re.findall(r"'([a-z_]+_amostra\.wav)'", yml))
checar(lidos == {"bruna_amostra.wav", "bryan_amostra.wav"},
       f"o env manda ler {sorted(lidos)}")

checar({n + ".wav" for n in gravados} == lidos,
       "os dois conjuntos BATEM — nenhum nome grava sem ser lido")

# --- 3b. o conversor nao pode ter entrada == saida -----------------------
# ⚠️ ISTO NAO E' TEORICO: quebrou o run #192. A amostra da Bruna ja' e' .wav,
# entao baixar com a extensao de ORIGEM e converter pro .wav final produzia
#
#     ffmpeg -i vozes/bruna_amostra.wav ... vozes/bruna_amostra.wav
#
# e o ffmpeg recusa ("Output same as Input - exiting"), exit 234. Com o Bryan
# passava despercebido, porque a origem dele e' .m4a e os nomes diferiam.
#
# ⚠️ O bloco [3] acima comparava os NOMES e passou. Nomes batendo nao provam
# que o COMANDO e' valido — sao perguntas diferentes, e so' a segunda pega
# este defeito. Foi por isso que ele chegou na nuvem.
print("")
print("[3b] o ffmpeg da conversao tem entrada diferente da saida")
import shlex  # noqa: E402

linhas = [l.strip() for l in yml.splitlines() if l.strip().startswith("ffmpeg")]
conv = [l for l in linhas if "-ar 24000" in l]
checar(len(conv) == 1,
       f"ha exatamente um ffmpeg de conversao de amostra (achei {len(conv)})")
if conv:
    partes = shlex.split(conv[0])
    entrada = partes[partes.index("-i") + 1]
    saida = partes[-1]
    checar(entrada != saida, f"entrada {entrada} difere da saida {saida}")
    checar("_amostra_bruta" in entrada,
           "a entrada e' um nome provisorio, nao o nome final")

# --- 4. a chave do disparo e o download concordam ------------------------
print("\n[4] o valor 'bruna' no disparo leva ao arquivo da Bruna")
checar('AMOSTRA" = "bruna"' in yml or '"$AMOSTRA" = "bruna"' in yml,
       "o download ramifica em 'bruna'")
checar("bruna" in yml.split("amostra_voz:")[1][:400],
       "a descricao do input cita 'bruna' (quem dispara descobre o valor)")

# --- 5. a voz alternativa do edge-tts existe de verdade ------------------
print("\n[5] o mapa de vozes nao aponta pra voz inexistente")
vz = (RAIZ / "engine" / "voz.py").read_text(encoding="utf-8")
checar('"pt-BR-ThalitaNeural"' not in vz,
       "pt-BR-ThalitaNeural (que NAO existe) saiu do mapa")
checar("ThalitaMultilingualNeural" in vz,
       "o nome real, ThalitaMultilingualNeural, esta' no mapa")

os.environ.pop("AMOSTRA_VOZ", None)
print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
