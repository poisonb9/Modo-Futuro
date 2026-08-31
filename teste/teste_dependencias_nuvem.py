# -*- coding: utf-8 -*-
"""Toda dependencia que o motor IMPORTA esta' declarada pro runner?

POR QUE EXISTE — o defeito reincidiu TRES vezes em 24 horas

  30/08  `voz.py` aprendeu a ler `VOZ_CANAL`, com teste verde... e o
         `cortar_de_bruto.yml` nao passava a variavel. Peca pronta,
         inalcancavel.
  31/08  `selecao.py` aprendeu a ler `SELECAO_MODO`, com teste verde... e o
         workflow nao tinha o input. Mesma coisa.
  31/08  o run #190 morreu em 14 min: `edge-tts` nunca esteve no
         `requirements.txt`. Ate' ali todo canal usava a voz clonada, entao a
         nuvem NUNCA tinha tido como dublar pelo edge-tts — o caminho existia
         no codigo e nao existia no runner.

Os tres sao a MESMA classe: a peca funciona na maquina do Bryan, o teste
passa, e a ponta que liga ela ao ambiente de verdade esta' faltando. Nenhum
dos tres levanta excecao no teste local, porque na maquina local a
dependencia esta' la'.

⚠️ Erro que reincide vira GUARDA, nao nota de handoff. Isto e' a guarda.

O QUE ELE CONFERE

Os dois caminhos de dublagem, que sao o lugar onde isso doeu: cada um tem uma
dependencia de terceiro, e ela tem de estar declarada no `requirements.txt`
— nao basta estar instalada aqui.

E confere que cada guarda `_exige_*` verifica O QUE O CODIGO USA. O guarda do
edge-tts procurava o executavel no PATH (`shutil.which`) enquanto o codigo faz
`import edge_tts`. Um guarda que confere a coisa errada conta a historia
errada justamente na hora em que alguem le' o log pra entender a falha.

Roda com: python teste/teste_dependencias_nuvem.py
"""
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


def declarados() -> set[str]:
    """Nomes de pacote do requirements.txt, normalizados."""
    txt = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    nomes = set()
    for linha in txt.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        nome = re.split(r"[<>=!\[;]", linha)[0].strip().lower()
        if nome:
            nomes.add(nome.replace("_", "-"))
    return nomes


print(__doc__.splitlines()[0])
pacotes = declarados()
print(f"\n{len(pacotes)} pacote(s) declarado(s) no requirements.txt")

# --- 1. os dois caminhos de dublagem --------------------------------------
print("\n[1] cada caminho de voz tem sua dependencia DECLARADA")
CAMINHOS = [
    ("edge-tts", "engine/dublagem.py", "voz do canal (feminina/masculina)"),
    ("chatterbox-tts", "engine/voz_clonada.py", "voz clonada do Bryan"),
]
for pacote, arquivo, oque in CAMINHOS:
    presente = pacote in pacotes
    if pacote == "chatterbox-tts" and not presente:
        # o Chatterbox e' instalado por passo proprio do workflow, nao pelo
        # requirements — entao a declaracao dele vive no yml.
        yml = (RAIZ / ".github" / "workflows" / "cortar_de_bruto.yml"
               ).read_text(encoding="utf-8")
        presente = "chatterbox" in yml.lower()
        oque += " (declarado no workflow, nao no requirements)"
    checar(presente, f"{pacote}: {oque}")

# --- 2. o guarda confere o que o codigo usa -------------------------------
print("\n[2] cada guarda verifica a dependencia que o codigo REALMENTE usa")
# ⚠️ Pela ARVORE, nao por busca de texto. A primeira versao deste teste
# procurava a string `shutil.which("edge-tts")` no arquivo e reprovou por
# encontra-la... dentro da docstring que EXPLICA por que ela saiu. Detector
# que le' prosa como se fosse codigo acusa o proprio comentario.
import ast  # noqa: E402
dub_src = (RAIZ / "engine" / "dublagem.py").read_text(encoding="utf-8")
arvore = ast.parse(dub_src)


def chama_which_edge(no) -> bool:
    return (isinstance(no, ast.Call)
            and getattr(no.func, "attr", "") == "which"
            and getattr(getattr(no.func, "value", None), "id", "") == "shutil"
            and any(isinstance(a, ast.Constant) and "edge" in str(a.value)
                    for a in no.args))


def chama_find_spec_edge(no) -> bool:
    return (isinstance(no, ast.Call)
            and getattr(no.func, "attr", "") == "find_spec"
            and any(isinstance(a, ast.Constant) and a.value == "edge_tts"
                    for a in no.args))


nos = list(ast.walk(arvore))
usa_import = any(isinstance(n, ast.Import)
                 and any(a.name == "edge_tts" for a in n.names) for n in nos)
guarda_import = any(chama_find_spec_edge(n) for n in nos)
guarda_path = any(chama_which_edge(n) for n in nos)
checar(usa_import, "dublagem.py sintetiza com `import edge_tts` (a biblioteca)")
checar(guarda_import,
       "o guarda confere o import da biblioteca (find_spec)")
checar(not guarda_path,
       "o guarda NAO confere o executavel no PATH (coisa que o codigo nao usa)")

# --- 3. a dependencia importa mesmo, aqui ---------------------------------
print("\n[3] a biblioteca importa nesta maquina")
import importlib.util  # noqa: E402
for mod, pacote in (("edge_tts", "edge-tts"),):
    ok = importlib.util.find_spec(mod) is not None
    if ok:
        checar(True, f"{mod} importavel")
    else:
        # nao e' falha do repo: pode ser um ambiente local sem o pacote.
        # O que importa pro runner e' a declaracao, ja' conferida em [1].
        print(f"  aviso  {mod} nao instalado AQUI — o runner instala pelo "
              f"requirements ({pacote} declarado: {pacote in pacotes})")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
