# -*- coding: utf-8 -*-
"""Clipe de um canal nao pode ser agendado noutro.

POR QUE EXISTE — custou 3 horas de margem

Em 31/08/2026 o run #191 produziu os 4 primeiros cortes do @truque.importado.
Deu tudo certo: critério de procedimento, voz feminina, 4 de 4 aprovados.
Ai' o `agendar_buffer` leu o manifesto INTEIRO do repositorio e encheu as 10
vagas do canal de MAQUIAGEM com clipes de CHIPS do @modofuturo:

    31/08 14:26  A Lei de Moore REALMENTE Morreu? Nvidia, Intel e IBM...
    31/08 19:25  O Segredo dos Chips do Futuro: A Inovacao CFET Revelada
    ... e mais 8

O primeiro sairia em 3h12. Publicar no canal errado nao tem desfazer: o post
sai, o alcance conta, e apagar deixa o video em 0 pra sempre.

A GUARDA QUE EXISTIA NAO TINHA COMO PEGAR

`CANAL_ESPERADO` confere o DESTINO — que o token abre o canal certo. Ela
passou, e corretamente: o token era mesmo o do @truque.importado. O que
faltava era a guarda de ORIGEM: de quem sao os CLIPES. Sao duas coisas, e so'
existia uma.

⚠️ So' apareceu naquele dia porque foi o PRIMEIRO run de um canal
nao-@modofuturo a TERMINAR neste repositorio. Os do @atefalhar e do
@semanestesia.pod morreram todos no teto de 6h, e a cozinha usa outro repo. O
defeito estava la' desde que o segundo canal nasceu, invisivel.

O CASO NEGATIVO E' O QUE MAIS IMPORTA AQUI

Um filtro de origem apertado demais para o @modofuturo — que tem 66 clipes
SEM o campo `canal`, porque sao anteriores a ele. Se vazio nao contasse como
modofuturo, o canal principal pararia de ser abastecido em silencio, e o
sintoma ("a fila secou") nao apontaria pra ca'.

Roda com: python teste/teste_canal_origem.py
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

os.environ.setdefault("BUFFER_TOKEN", "x-para-o-teste")
os.environ.setdefault("GITHUB_TOKEN", "x-para-o-teste")

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def filtro(canal_do_run: str):
    """Recria `e_deste_canal` como o agendador o monta, sem tocar na rede."""
    alvo = (canal_do_run or "").strip().lower()

    def e_deste_canal(v) -> bool:
        if not alvo:
            return True
        return (v.get("canal") or "modofuturo").strip().lower() == alvo
    return e_deste_canal


print(__doc__.splitlines()[0])

# Amostra fiel ao manifesto real: os antigos sem campo, os novos com.
ANTIGO = {"titulo": "A Lei de Moore REALMENTE Morreu?"}                 # sem canal
CHIPS = {"titulo": "EUA vs China", "canal": "modofuturo"}
MAQUIAGEM = {"titulo": "TUTORIAL DE CUT CREASE", "canal": "truque.importado"}
PODCAST = {"titulo": "Mental Toughness", "canal": "atefalhar"}

# --- 1. o caso que estourou -----------------------------------------------
print("\n[1] rodando PARA a maquiagem, clipe de chips nao passa")
f = filtro("truque.importado")
checar(not f(CHIPS), "clipe do @modofuturo e' recusado")
checar(not f(ANTIGO), "clipe ANTIGO (sem campo) tambem e' recusado")
checar(not f(PODCAST), "clipe do @atefalhar e' recusado")
checar(f(MAQUIAGEM), "clipe do proprio canal PASSA")

# --- 2. o caso NEGATIVO: o canal principal nao pode parar -----------------
print("\n[2] rodando para o @modofuturo, os 66 clipes ANTIGOS continuam valendo")
f = filtro("modofuturo")
checar(f(ANTIGO),
       "clipe sem campo `canal` conta como modofuturo (senao a fila seca)")
checar(f(CHIPS), "clipe marcado como modofuturo passa")
checar(not f(MAQUIAGEM), "clipe de maquiagem NAO vaza pro canal principal")
checar(not f(PODCAST), "clipe do @atefalhar NAO vaza pro canal principal")

# --- 3. sem a variavel, nada muda (falha ABERTA) --------------------------
print("\n[3] sem CANAL_ESPERADO, o comportamento antigo continua")
f = filtro("")
checar(all(f(x) for x in (ANTIGO, CHIPS, MAQUIAGEM, PODCAST)),
       "tudo passa — disparo antigo sem a variavel segue funcionando")

# --- 4. caixa e espaco nao driblam ----------------------------------------
print("\n[4] caixa alta e espaco em volta nao driblam a guarda")
checar(filtro("  TRUQUE.IMPORTADO  ")(MAQUIAGEM), "alvo com caixa/espaco casa")
checar(not filtro("truque.importado")({"canal": " MODOFUTURO "}),
       "valor do manifesto com caixa/espaco tambem e' normalizado")

# --- 5. o codigo de verdade tem as duas pontas ----------------------------
print("\n[5] as duas pontas existem no codigo, nao so' neste teste")
ag = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")
pub = (RAIZ / "publicar_release.py").read_text(encoding="utf-8")
yml = (RAIZ / ".github" / "workflows" / "cortar_de_bruto.yml").read_text(
    encoding="utf-8")
checar("e_deste_canal" in ag, "agendar_buffer filtra pela origem")
checar("if not e_deste_canal(v):" in ag, "o filtro e' chamado dentro de cabe()")
checar('"canal":' in pub, "publicar_release grava o campo `canal`")
checar(yml.count("CANAL_ESPERADO") >= 2,
       "o workflow passa CANAL_ESPERADO na Release E no Buffer")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
