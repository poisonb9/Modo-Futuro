# -*- coding: utf-8 -*-
"""Plano de virada, itens 1-5 (26/09/2026): o 1o segundo do @modofuturo.

POR QUE EXISTE

MEDIDO: 55 de 92 clipes do canal abriam a voz com "Ele explicou que..." e 5 de
8 perdedores abriam a imagem no mesmo estudio de podcast. As frases dos casos
abaixo sao TRANSCRICOES REAIS desses clipes. O teste guarda tres coisas:
  - o detector pega as aberturas fracas reais e NAO pega as boas;
  - so' o modofuturo muda (make, Sem Anestesia e cozinha intactos);
  - o item 5 NAO descarta clipe (dono: "nao generalize, podemos perder muitos
    bons videos") — so' marca e reordena.
"""
import os
import pathlib
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

falhas = []


def checar(ok, msg):
    print(("  ok    " if ok else "  FALHA ") + msg)
    if not ok:
        falhas.append(msg)


from engine import traducao as t, guia_voz, abertura_visual, selecao  # noqa: E402

print("[1] aberturas fracas REAIS sao pegas")
for frase in ["Ele explicou que a máquina é uma das mais caras do mundo.",
              "O convidado ressaltou que, embora o",
              "Ao ser questionado sobre o papel dos semicondutores na geopolítica,",
              "Além disso, eles também não projetam as ferramentas que usam.",
              "A analista explicou que o CHIPS Act envolve apenas",
              "Ele começou abordando os avanços na tecnologia.",
              "Ele fez questão de esclarecer que em quatro anos"]:
    checar(t.abertura_fraca(frase) is not None, f"fraca: {frase[:45]}")

print("\n[2] NEGATIVO: aberturas boas passam")
for frase in ["Existe apenas um tipo de máquina no mundo capaz de construir isso.",
              "Os preços da memória DRAM subiram mais de 80%.",
              "O chip considerado o menor do mundo tem 2 nanômetros.",
              "Uma máquina de 180 toneladas decide qual país tem celular."]:
    checar(t.abertura_fraca(frase) is None, f"boa: {frase[:45]}")

print("\n[3] corte mecanico so' quando a frase fica inteira")
checar(t.tirar_atribuicao("Ele explicou que a máquina pesa 180 toneladas.")
       == "A máquina pesa 180 toneladas.", "tira 'Ele explicou que'")
checar(t.tirar_atribuicao("Além disso, o chip esquenta a 1.100 graus.")
       == "O chip esquenta a 1.100 graus.", "tira conectivo")
fr = "Ao ser questionado sobre o papel dos chips, ele riu."
checar(t.tirar_atribuicao(fr) == fr, "caso sem corte limpo volta intacto")

print("\n[4] so' o modofuturo tem abertura por fato no guia de voz")
checar(guia_voz.abre_por_fato("modofuturo"), "modofuturo: sim")
for c in ("truque.importado", "semanestesia.pod", "cozinha.importada"):
    checar(not guia_voz.abre_por_fato(c), f"{c}: nao")
bloco = guia_voz.bloco_prompt("modofuturo")
checar("ABERTURA (obrigatório)" in bloco and "ESTRUTURA" in bloco,
       "bloco do prompt traz abertura e estrutura")

print("\n[5] abertura visual: quando troca a imagem")
os.environ["CANAL_ESPERADO"] = "modofuturo"
base = {"abertura_mostra": "pessoa_falando", "momento_visual_s": 120.0}
checar(abertura_visual.instante(base, 100, 140) == 120.0, "rosto + momento dentro -> troca")
checar(abertura_visual.instante({**base, "abertura_mostra": "acao"}, 100, 140) is None,
       "ja' abre na acao -> nao mexe")
checar(abertura_visual.instante({**base, "momento_visual_s": 100.5}, 100, 140) is None,
       "momento colado no inicio -> nao mexe")
checar(abertura_visual.instante({**base, "momento_visual_s": 139.0}, 100, 140) is None,
       "momento sem 1,5 s antes do fim -> nao mexe")
checar(abertura_visual.instante({**base, "momento_visual_s": None}, 100, 140) is None,
       "sem momento -> nao mexe")
os.environ["CANAL_ESPERADO"] = "truque.importado"
checar(abertura_visual.instante(base, 100, 140) is None, "make -> nunca mexe")

print("\n[6] item 5 NAO descarta: marca e reordena")
os.environ["CANAL_ESPERADO"] = "modofuturo"
cl = [{"titulo": "estudio", "nota": 95, "abertura_mostra": "pessoa_falando",
       "momento_visual_s": None},
      {"titulo": "maquina", "nota": 92, "abertura_mostra": "acao",
       "momento_visual_s": 12.0}]
out = selecao.marcar_sem_assunto([dict(c) for c in cl])
checar(len(out) == 2, "os dois continuam")
checar(out[0].get("sem_assunto_na_tela") and out[0]["nota"] == 90
       and out[0]["nota_original"] == 95, "estudio marcado, -5 so' na ordem")
checar(selecao._bloco_canal() != "", "bloco extra de selecao no modofuturo")
os.environ["CANAL_ESPERADO"] = "semanestesia.pod"
checar(selecao.marcar_sem_assunto([dict(c) for c in cl])[0]["nota"] == 95,
       "outro canal: nada muda")
checar(selecao._bloco_canal() == "", "outro canal: sem bloco extra")

print("\n[7] a troca de imagem nao mexe no audio nem na duracao (ffmpeg real)")
with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    bruto, fonte = d / "bruto.mp4", d / "fonte.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "testsrc=size=640x360:rate=30:duration=5", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=5", "-shortest", "-c:v", "libx264",
                    "-c:a", "aac", str(bruto)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=red:size=1280x720:rate=25:duration=10",
                    "-c:v", "libx264", str(fonte)], check=True)
    saida = abertura_visual.aplicar(fonte, bruto, 4.0)
    from engine import midia
    checar(saida != bruto, "gerou a versao com abertura")
    checar(abs(midia.duracao(saida) - midia.duracao(bruto)) < 0.1, "mesma duracao")
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_name", "-of", "csv=p=0",
                        str(saida)], capture_output=True, text=True)
    checar(r.stdout.strip() == "aac", "audio original preservado")

os.environ.pop("CANAL_ESPERADO", None)
print("\ntudo verde" if not falhas else f"\n{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
