# -*- coding: utf-8 -*-
"""A voz de producao e' a D (edge-tts + troca de timbre), com falha aberta p/ A.

POR QUE EXISTE

26/09/2026: o dono ouviu a previa (run 36207479880) e decidiu "D para os
dois" — Bryan e Bruna. A D nao pode derrubar um clipe: sem o conversor de
timbre, sem rede pro edge, ou idioma que nao e' portugues, a frase sai na A.

Nem o edge nem o Chatterbox rodam aqui: os dois viram falsos que registram
quem foi chamado e com que voz.

  [1] padrao e' D; amostra da Bruna -> Thalita, do Bryan -> Antonio
  [2] edge falhando numa frase -> essa frase sai na A
  [3] VC indisponivel -> A, e nao tenta carregar de novo na frase seguinte
  [4] idioma que nao e' pt -> A direto
  [5] VOZ_MOTOR=A -> A; e motor="A" explicito -> A
  [6] a refeita da conferencia (motor "D-") fica na D, 10% mais lenta

Roda com: python teste/teste_voz_motor_d.py
"""
import importlib
import os
import sys
import tempfile
import types
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


chamadas = []


class VCFalso:
    sr = 24000
    cargas = 0

    @classmethod
    def from_pretrained(cls, device="cpu"):
        cls.cargas += 1
        if os.environ.get("_VC_QUEBRADO"):
            raise ImportError("sem chatterbox.vc")
        return cls()

    def generate(self, audio, target_voice_path):
        chamadas.append(("vc", Path(target_voice_path).name))
        return "wav"


# modulos falsos: chatterbox.vc e torchaudio (nao instalados aqui)
sys.modules["chatterbox"] = types.ModuleType("chatterbox")
sys.modules["chatterbox.vc"] = types.SimpleNamespace(ChatterboxVC=VCFalso)
sys.modules["torchaudio"] = types.SimpleNamespace(
    save=lambda caminho, wav, sr: Path(caminho).write_bytes(b"RIFF"))


def carregar(motor_env=None):
    if motor_env is None:
        os.environ.pop("VOZ_MOTOR", None)
    else:
        os.environ["VOZ_MOTOR"] = motor_env
    from engine import voz_clonada, dublagem
    v = importlib.reload(voz_clonada)
    v._bypass_watermarker = lambda: None
    VCFalso.cargas = 0

    def edge_falso(texto, destino, voz, velocidade=None):
        if "QUEBRA" in texto:
            raise ConnectionError("sem rede")
        chamadas.append(("edge", voz) if velocidade is None else ("edge", voz, velocidade))
        Path(destino).write_bytes(b"mp3")
        return destino
    dublagem._falar = edge_falso

    class ModeloA:
        sr = 24000

        def generate(self, texto, audio_prompt_path, language_id, **kw):
            chamadas.append(("A", Path(audio_prompt_path).name))
            return "wav"
    v._carregar_modelo = lambda: ModeloA()
    return v


tmp = Path(tempfile.mkdtemp())
bruna, bryan = tmp / "bruna_amostra.wav", tmp / "bryan_amostra.wav"
for a in (bruna, bryan):
    a.write_bytes(b"x")

print("\n[1] padrao D, voz do edge pelo dono da amostra")
v = carregar()
checar(v.VOZ_MOTOR == "D", "motor padrao e' D")
chamadas.clear()
v._falar("Olha esse truque.", tmp / "f1.wav", bruna, "pt")
checar(chamadas == [("edge", v.EDGE_FEMININA), ("vc", "bruna_amostra.wav")],
       f"Bruna: Thalita + timbre dela ({chamadas})")
chamadas.clear()
v._falar("Essa maquina custa caro.", tmp / "f2.wav", bryan, "pt")
checar(chamadas == [("edge", v.EDGE_MASCULINA), ("vc", "bryan_amostra.wav")],
       f"Bryan: Antonio + timbre dele ({chamadas})")
checar((tmp / "f2.wav").exists(), "wav gravado no destino")

print("\n[2] edge falha numa frase -> essa frase vai pra A")
chamadas.clear()
v._falar("QUEBRA aqui.", tmp / "f3.wav", bryan, "pt")
checar(chamadas == [("A", "bryan_amostra.wav")], f"caiu na A ({chamadas})")
chamadas.clear()
v._falar("Proxima frase.", tmp / "f4.wav", bryan, "pt")
checar(chamadas[0][0] == "edge", "a frase seguinte volta pra D")

print("\n[3] VC indisponivel -> A, carregado so' uma vez")
os.environ["_VC_QUEBRADO"] = "1"
v = carregar()
chamadas.clear()
v._falar("Um.", tmp / "g1.wav", bruna, "pt")
v._falar("Dois.", tmp / "g2.wav", bruna, "pt")
checar([c[0] for c in chamadas] == ["A", "A"], f"as duas na A ({chamadas})")
checar(VCFalso.cargas == 1, f"tentou carregar o VC 1 vez ({VCFalso.cargas})")
os.environ.pop("_VC_QUEBRADO")

print("\n[4] idioma nao-portugues -> A")
v = carregar()
chamadas.clear()
v._falar("Hello there.", tmp / "h1.wav", bryan, "en")
checar(chamadas == [("A", "bryan_amostra.wav")], f"ingles na A ({chamadas})")

print("\n[5] VOZ_MOTOR=A e motor='A' explicito")
v = carregar("A")
chamadas.clear()
v._falar("Frase.", tmp / "i1.wav", bryan, "pt")
checar(chamadas == [("A", "bryan_amostra.wav")], "env VOZ_MOTOR=A usa a A")
v = carregar()
chamadas.clear()
v._falar("Frase.", tmp / "i2.wav", bryan, "pt", motor="A")
checar(chamadas == [("A", "bryan_amostra.wav")], "motor='A' explicito usa a A")
fonte = (RAIZ / "engine" / "voz_clonada.py").read_text(encoding="utf-8")
checar('motor="D-" if VOZ_MOTOR == "D" else "A")' in fonte,
       "a refeita da conferencia pede a D lenta (e a A fora da D)")

print("\n[6] refeita na D: mesma voz, leitura mais lenta")
chamadas.clear()
v._falar("Frase.", tmp / "j1.wav", bruna, "pt", motor="D-")
checar(chamadas == [("edge", v.EDGE_FEMININA, v.REFEITA_VELOCIDADE), ("vc", "bruna_amostra.wav")],
       f"edge com {v.REFEITA_VELOCIDADE} + timbre da Bruna ({chamadas})")

os.environ.pop("VOZ_MOTOR", None)
print()
if falhas:
    print(f"FALHOU: {len(falhas)}")
    sys.exit(1)
print("TUDO OK")
