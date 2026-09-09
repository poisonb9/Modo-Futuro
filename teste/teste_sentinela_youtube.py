# -*- coding: utf-8 -*-
"""A sentinela do YouTube: fila, intervalo, freio — e falha FECHADA.

⚠️ POR QUE ELA EXISTE, e o que este teste protege.

Em 09/09/2026 a VPS levou `Sign in to confirm you're not a bot` do YouTube
por baixar em rajada. Ordem do Bryan: nunca mais de uma chamada consecutiva
ou junta, em QUALQUER projeto, e quem chegar dentro do intervalo entra numa
FILA em vez de ser recusado.

O QUE PRECISA SER PROVADO

  1. o intervalo e' respeitado — quem chega cedo DORME, nao leva erro;
  2. ⚠️ CASO NEGATIVO, o principal: a PRIMEIRA chamada NAO espera. Uma
     sentinela que sempre dorme "nunca deixa passar rajada" e tambem nunca
     deixa passar nada. Foi o mesmo raciocinio do detector de 08/09 que
     acusava 100% dos casos;
  3. o freio RECUSA em vez de enfileirar. Depois do bot-check, esperar na
     fila e tentar de novo e' exatamente o que confirma o padrao de robo;
  4. o teto do dia recusa, e ele conta por dia UTC;
  5. cadeado abandonado e' recolhido — senao um processo morto tranca a
     operacao inteira em silencio, que e' pior que o problema original;
  6. o reconhecedor de bot-check pega o apostrofo tipografico do YouTube.
     ⚠️ Ele manda `you’re`, nao `you're`. Um detector que so' conhece o
     apostrofo reto nunca dispara — e o freio nunca seria puxado.

Roda com: python teste/teste_sentinela_youtube.py
"""
import os
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

falhas = 0


def checar(cond, recado):
    global falhas
    if cond:
        print(f"  ok  {recado}")
    else:
        print(f"  FALHOU  {recado}")
        falhas += 1


AJUSTES = ("SENTINELA_YT_INTERVALO", "SENTINELA_YT_ESPERA_MAX",
           "SENTINELA_YT_TETO_DIA", "SENTINELA_YT_FREIO_H")


def limpo(**env):
    """Estado novo num diretorio temporario, com os ajustes pedidos.

    ⚠️ APAGA os ajustes antigos antes. Sem isto o teste do PADRAO herdava a
    variavel do teste anterior e media outra coisa — foi o que aconteceu na
    primeira rodada: `limpo()` sem argumento leu intervalo 0 e teto 100, os
    valores do teste 4.
    """
    for k in AJUSTES:
        os.environ.pop(k, None)
    d = tempfile.mkdtemp()
    os.environ["SENTINELA_YT_DIR"] = d
    for k, v in env.items():
        os.environ[k] = str(v)
    return Path(d)


import engine.sentinela_youtube as s  # noqa: E402


print("1. CASO NEGATIVO: a PRIMEIRA chamada nao espera")
# Sem isto, uma sentinela que dorme sempre passaria em todos os outros
# testes e pararia a operacao inteira.
limpo(SENTINELA_YT_INTERVALO=30, SENTINELA_YT_TETO_DIA=100)
t = time.time()
s.esperar_vez("primeira")
checar(time.time() - t < 2, f"passou direto ({time.time() - t:.1f}s)")

print("\n2. a SEGUNDA espera o que falta, e nao leva erro")
limpo(SENTINELA_YT_INTERVALO=3, SENTINELA_YT_TETO_DIA=100)
s.esperar_vez("a")
t = time.time()
s.esperar_vez("b")          # nao levanta: dorme
gasto = time.time() - t
checar(2.0 <= gasto <= 6.0, f"dormiu {gasto:.1f}s do intervalo de 3s")

print("\n3. o freio RECUSA (nao enfileira)")
limpo(SENTINELA_YT_INTERVALO=1, SENTINELA_YT_TETO_DIA=100)
s.puxar_freio("Sign in to confirm you are not a bot", horas=1)
travado, por_que = s.freio_ativo()
checar(travado, "freio_ativo() diz que esta' travado")
try:
    s.esperar_vez("depois do freio")
    checar(False, "deixou passar com o freio puxado")
except s.Bloqueada:
    checar(True, "recusou com Bloqueada, em vez de dormir")
s.soltar_freio()
checar(not s.freio_ativo()[0], "--soltar destrava")

print("\n4. o teto do dia recusa")
limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_TETO_DIA=2)
s.esperar_vez("1")
s.esperar_vez("2")
try:
    s.esperar_vez("3")
    checar(False, "passou do teto de 2")
except s.Bloqueada as e:
    checar("teto" in str(e), "recusou a terceira no teto de 2")

print("\n5. cadeado abandonado e' recolhido")
d = limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_TETO_DIA=100,
          SENTINELA_YT_ESPERA_MAX=1)
# cadeado velho, de um processo que morreu ha' muito tempo
(d / "cadeado").write_text(f"99999 {time.time() - 99999:.0f}", encoding="utf-8")
t = time.time()
try:
    s.esperar_vez("apos abandono")
    checar(time.time() - t < 10, "recolheu o cadeado velho e seguiu")
except s.NaoConsegui:
    checar(False, "travou num cadeado abandonado")

print("\n6. cadeado VIVO segura (falha FECHADA)")
# ⚠️ O outro lado do 5: se recolhesse qualquer cadeado, nao haveria cadeado.
d = limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_TETO_DIA=100,
          SENTINELA_YT_ESPERA_MAX=2)
(d / "cadeado").write_text(f"{os.getpid()} {time.time():.0f}", encoding="utf-8")
try:
    s.esperar_vez("com cadeado vivo")
    checar(False, "passou por cima de um cadeado recente")
except s.NaoConsegui:
    checar(True, "recusou: falha FECHADA, nao 'vai assim mesmo'")

print("\n7. o reconhecedor pega o apostrofo do YouTube")
# ⚠️ O YouTube manda `you’re` (tipografico), nao `you're`.
checar(s.e_bloqueio("ERROR: Sign in to confirm you’re not a bot"),
       "pega o apostrofo TIPOGRAFICO (o que o YouTube manda de verdade)")
checar(s.e_bloqueio("sign in to confirm you're not a bot"),
       "pega o apostrofo reto")
checar(s.e_bloqueio("HTTP Error 429: Too Many Requests"), "pega o 429")
# CASO NEGATIVO: erro comum NAO pode puxar o freio de 24h.
checar(not s.e_bloqueio("ERROR: Video unavailable"),
       "video indisponivel NAO e' bot-check (freio de 24h por engano)")
checar(not s.e_bloqueio("ERROR: The page needs to be reloaded"),
       "desafio de JS NAO e' bot-check — foi o defeito de 09/09")
checar(not s.e_bloqueio(""), "texto vazio nao dispara")

print("\n8. o estado se le' sem quebrar, mesmo zerado")
limpo()
e = s.estado()
checar(e["freio"] is False and e["hoje"] == 0, "estado novo: sem freio, zero hoje")
checar(e["intervalo_s"] == 900, f"intervalo padrao 900s (veio {e['intervalo_s']})")
checar(e["teto_dia"] == 12, f"teto padrao 12 (veio {e['teto_dia']})")

if falhas:
    print(chr(10) + f"{falhas} FALHA(S)")
    sys.exit(1)
print(chr(10) + "tudo verde")
