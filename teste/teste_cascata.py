# -*- coding: utf-8 -*-
"""A cascata so' entra onde foi ligada, e nunca com o selo de outro canal."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import cascata  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


print("1. ⭐ NASCE DESLIGADA — producao nao muda sem decisao do Bryan")
checar(cascata.CANAIS_COM_CASCATA == set(), "o conjunto vem vazio")
for c in ("atefalhar", "modofuturo", "truque.importado"):
    checar(not cascata.ligado(c), f"{c}: desligado")

print("\n2. ligar resolve pelo REGISTRO, nao pelo texto cru")
# ⚠️ O mesmo canal chega escrito de tres jeitos. Comparar texto deixaria a
# cascata ligada num e desligada noutro sem ninguem perceber.
cascata.CANAIS_COM_CASCATA.add("atefalhar")
for jeito in ("atefalhar", "@atefalhar"):
    checar(cascata.ligado(jeito), f"{jeito!r} -> ligado")
checar(not cascata.ligado("modofuturo"), "e o modofuturo segue desligado")
checar(not cascata.ligado("canal_que_nao_existe"), "canal inexistente: nao")
cascata.CANAIS_COM_CASCATA.clear()

print("\n3. ⭐ NEGATIVO — sem o selo do canal, NAO usa o de outro")
# ⚠️ O @ mora DENTRO da imagem. Cair no selo de outro canal mandaria a
# audiencia pro perfil errado, e isso nao levanta erro nenhum.
for tem in ("atefalhar", "modofuturo", "semanestesia.pod",
            "achadinhos.instantaneos"):
    checar(cascata.selos_do_canal(tem) is not None, f"{tem}: tem os tres selos")

# ⭐ O SELO DIZ O NOME DO CANAL, NAO O @ — e isso resolve sozinho um problema
# que eu tinha levantado: o @ MUDA entre plataformas (@modofuturo no TikTok e'
# @modo_futuro_ no Instagram). Com o nome, o mesmo selo serve nas duas.
# ⚠️ ESTA LISTA E' O QUE FALTA HOJE, e vai encolhendo conforme o Bryan gera
# os selos. Quando esvaziar, o assert vira trivial — e ai' o que protege e' a
# checagem de par completo logo acima.
for sem in ("fatura.chora", "truque.importado", "cozinha.importada"):
    checar(cascata.selos_do_canal(sem) is None,
           f"{sem}: sem selo proprio -> None (nao cai no de outro)")
print("")
print("4. ⭐ NUNCA por cima da legenda — e a checagem e' na hora")
from PIL import Image  # noqa: E402
from engine import legendas  # noqa: E402
LARG, ALT = 1080, 1920
lw, lh = [], []
for png, m in zip(cascata.selos_do_canal("atefalhar"), cascata.ESCALA_POR_SELO):
    im = Image.open(png)
    w = int(LARG * cascata.LARGURA_FRAC * m)
    lw.append(w)
    lh.append(round(im.size[1] * w / im.size[0]))
pos = cascata.colocar(LARG, ALT, lw, lh)
checar(pos is not None, "as tres zonas cabem")
topo_leg, base_leg = legendas.faixa_ocupada(ALT)
for (x, y, d), h, w in zip(pos, lh, lw):
    checar(y + h < topo_leg or y > base_leg,
           f"selo em {y}-{y+h} nao toca a legenda ({topo_leg}-{base_leg})")
    # ⚠️ A FAIXA DA PLATAFORMA FALTAVA na guarda ate' 13/09: o SIGA aumentado
    # terminava em 0,889 e passou. Guarda que nao olha uma das bordas e' sorte.
    checar(y + h <= int(ALT * cascata.UI_BASE_FRAC),
           f"selo termina em {y+h}, dentro da area visivel")
    checar(x >= 0 and x + w <= LARG, "cabe na largura")

print("")
print("5. ⭐ ONDE FICA e DE ONDE VEM sao separados")
for (x, y, d), (lado, _fr, entra) in zip(pos, cascata.ZONAS):
    comeca = x + d
    checar(d != 0, f"{lado}/{entra}: tem deslocamento")
    if entra != lado:
        # ⚠️ Entrando pelo lado OPOSTO, tem de comecar FORA da tela. Com o
        # deslocamento fixo de 320 o selo brotava no meio do video.
        fora = comeca >= LARG if entra == "dir" else comeca + lw[0] <= 0
        checar(fora, f"cruza a tela: comeca em {comeca}")

print("")
print("6. o filtro escalona: cada selo entra depois do anterior")
f = cascata.montar_filtro(pos, 12.0)
import re  # noqa: E402
entradas = [float(x) for x in re.findall(r"fade=t=in:st=([\d.]+)", f)]
checar(len(entradas) == 3, f"tres fades de entrada ({len(entradas)})")
checar(entradas == sorted(entradas) and len(set(entradas)) == 3,
       f"em ordem e distintos: {entradas}")
checar(abs((entradas[1] - entradas[0]) - cascata.ESCALONA_S) < 1e-6,
       "o intervalo e' o ESCALONA_S")

print("\n7. NEGATIVO — as virgulas NAO levam barra invertida")
# ⚠️ As expressoes vao entre aspas simples no overlay=x='...'. Barra invertida
# em f-string gerada por heredoc foi o defeito que mais se repetiu hoje.
checar("\," not in f, "nenhuma virgula escapada na cadeia")
checar("min(1,max(0," in f, "as expressoes estao inteiras")

print("\n8. NEGATIVO — a animacao e' de POSICAO, nao de escala")
# ⚠️ Escala negativa derruba o ffmpeg com Invalid argument -22; posicao
# negativa so' poe o selo fora da tela. Foi a licao de 13/09.
checar("scale=" not in f, "nao ha' filtro scale na cadeia")
checar("overlay=x='" in f, "a animacao esta' no x do overlay")

print("\n9. sem som — decisao do Bryan em 13/09")
checar("amix" not in f and "adelay" not in f, "nenhum filtro de audio")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
