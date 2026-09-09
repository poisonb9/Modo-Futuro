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


AJUSTES = ("SENTINELA_YT_INTERVALO", "SENTINELA_YT_INTERVALO_LEVE",
           "SENTINELA_YT_ESPERA_MAX", "SENTINELA_YT_TETO_DIA",
           "SENTINELA_YT_FREIO_H", "SENTINELA_YT_FREIO_TAXA_LEVE_H")


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
print(chr(10) + "8b. LEVE tem preferencia sobre PESADO")
# ⚠️ Ordem do Bryan: 'para video eu nao me importo, mas legenda pode
# priorizar". Enquanto houver pedido leve na fila, o pesado CEDE a vez.
limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_INTERVALO_LEVE=0,
      SENTINELA_YT_TETO_DIA=100, SENTINELA_YT_ESPERA_MAX=3)
s._marcar_leve(True)
try:
    s.esperar_vez("video com legenda na fila", peso="pesado")
    checar(False, "o pesado passou por cima do pedido leve")
except s.NaoConsegui:
    checar(True, "o pesado CEDE enquanto ha' legenda esperando")
s._marcar_leve(False)
t = time.time()
s.esperar_vez("sem legenda na fila", peso="pesado")
checar(time.time() - t < 3, "sem pedido leve, o pesado passa normalmente")

print(chr(10) + "8c. quem dorme NAO segura o cadeado")
# ⚠️ Na primeira versao o processo pegava a porta e SO ENTAO dormia —
# uma legenda ficava presa atras de um video por ate 10 min, a toa.
d = limpo(SENTINELA_YT_INTERVALO=3600, SENTINELA_YT_INTERVALO_LEVE=0,
          SENTINELA_YT_TETO_DIA=100, SENTINELA_YT_ESPERA_MAX=2)
s.esperar_vez("primeira", peso="leve")
checar(not (d / "cadeado").exists(), "cadeado solto entre uma chamada e outra")


print("\n8. o estado se le' sem quebrar, mesmo zerado")
limpo()
e = s.estado()
checar(e["freio"] is False and e["hoje"] == 0, "estado novo: sem freio, zero hoje")
# ⚠️ Duas faixas desde 09/09: video 600s, legenda/metadado 300s. O cadeado
# continua UM so' — a faixa muda a espera, nunca a simultaneidade.
checar(e["intervalo_s"] == 600, f"video: 600s (veio {e['intervalo_s']})")
checar(e["intervalo_leve_s"] == 300,
       f"leve: 300s (veio {e['intervalo_leve_s']})")
checar(e["teto_dia"] == 12, f"teto padrao 12 (veio {e['teto_dia']})")

print(chr(10) + "9. cadeado VAZIO e' novo, nao abandonado")
# ⚠️ O DEFEITO, achado em 09/09/2026 relendo a propria sentinela: o arquivo
# nasce vazio no `O_CREAT` e so' recebe o pid no `os.write` seguinte. Nesse
# instante outro processo le' e nao acha carimbo. Com o fallback antigo
# (`nasceu = 0.0`) isso virava "abandonado ha' 56 anos", o cadeado recem-criado
# era APAGADO e os dois processos passavam — DOIS downloads ao mesmo tempo,
# pela funcao que existe pra impedir exatamente isso.
d = limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_INTERVALO_LEVE=0,
          SENTINELA_YT_TETO_DIA=100, SENTINELA_YT_ESPERA_MAX=1)
cad = d / "cadeado"
cad.write_text("", encoding="utf-8")          # o instante entre criar e escrever
try:
    s._pegar_cadeado(1)
    checar(False, "arrombou um cadeado VAZIO — a corrida continua aberta")
except s.NaoConsegui:
    checar(True, "cadeado vazio e' tratado como NOVO: espera, nao arromba")
checar(cad.exists(), "e o cadeado do outro processo continua la'")

print(chr(10) + "9b. NEGATIVO: cadeado velho de verdade AINDA e' recolhido")
# ⚠️ Sem esta metade, a correcao acima poderia ter travado a operacao pra
# sempre — que e' pior que o defeito. Um processo morto nao pode deixar a
# porta trancada.
d = limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_INTERVALO_LEVE=0,
          SENTINELA_YT_TETO_DIA=100, SENTINELA_YT_ESPERA_MAX=1)
cad = d / "cadeado"
cad.write_text("", encoding="utf-8")
velho = time.time() - 7200                    # duas horas atras
os.utime(cad, (velho, velho))
try:
    s._pegar_cadeado(1)
    checar(True, "cadeado vazio e ANTIGO e' recolhido (processo morto)")
except s.NaoConsegui:
    checar(False, "nao recolheu cadeado abandonado — a operacao trava pra "
                  "sempre depois de um processo morrer")

print(chr(10) + "10. UMA de cada vez: a porta fica na mao enquanto o comando roda")
# ⚠️ O DEFEITO, achado em 09/09/2026 relendo a sentinela: `esperar_vez()`
# SOLTA o cadeado ao voltar — de proposito, pra quem dorme nao trancar a porta.
# So' que o comando roda DEPOIS disso. O que sobrava era espacamento entre
# INICIOS: um download de 40 min com intervalo de 10 deixava QUATRO rodando
# juntos, dentro da guarda que existe pra impedir exatamente isso.
import threading  # noqa: E402

d = limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_INTERVALO_LEVE=0,
          SENTINELA_YT_TETO_DIA=100, SENTINELA_YT_ESPERA_MAX=30)
dentro = threading.Event()
solta = threading.Event()
juntos = []


def _segundo():
    dentro.wait(5)
    t0 = time.time()
    with s.vez("segundo", peso="pesado"):
        # se a porta estivesse livre, este bloco comecaria com o primeiro
        # AINDA dentro — que e' a simultaneidade proibida
        juntos.append(solta.is_set())
    return time.time() - t0


t = threading.Thread(target=_segundo, daemon=True)
t.start()
with s.vez("primeiro", peso="pesado"):
    dentro.set()
    time.sleep(3)
    solta.set()
t.join(20)
checar(juntos == [True],
       f"o segundo so' entrou DEPOIS do primeiro sair (viu {juntos})")

print(chr(10) + "10b. NEGATIVO: com a porta livre, o segundo NAO espera")
# Sem esta metade, um `vez()` que travasse pra sempre passaria no teste de
# cima e pararia a operacao inteira.
d = limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_INTERVALO_LEVE=0,
          SENTINELA_YT_TETO_DIA=100, SENTINELA_YT_ESPERA_MAX=30)
with s.vez("um", peso="pesado"):
    pass
t0 = time.time()
with s.vez("dois", peso="pesado"):
    pass
checar(time.time() - t0 < 3, "porta livre: passa direto, sem fila fantasma")
checar(not (d / "cadeado").exists(), "e a porta fica solta no fim")

print(chr(10) + "11. porta ocupada e' FILA, nao recusa")
# ⚠️ REGRESSAO QUE O PROPRIO `vez()` criou, achada no mesmo dia: com a porta
# agora SEGURA durante o comando, encontrar o cadeado fechado virou o caso
# normal. O `_pegar_cadeado(60)` de dentro do `esperar_vez` levanta
# `NaoConsegui` em 60s — e isso transformaria a fila numa RECUSA sempre que
# houvesse um download em curso. E' o contrario da ordem: quem chega cedo
# espera, nunca leva erro. Recusar faz cada chamador inventar seu retry, que
# foi o que queimou a VPS.
# ⚠️ A tentativa de cadeado cai pra 1s SO' NESTE TESTE. Com os 60s de
# producao, uma porta segurada por 3s nem chegaria a levantar `NaoConsegui` —
# o teste passaria no codigo ANTIGO tambem, e nao provaria nada.
s._TENTATIVA_CADEADO_S = 1
d = limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_INTERVALO_LEVE=0,
          SENTINELA_YT_TETO_DIA=100, SENTINELA_YT_ESPERA_MAX=120)
segurou = threading.Event()
fim = threading.Event()
resultado = []


def _dono():
    with s.vez("dono demorado", peso="pesado"):
        segurou.set()
        fim.wait(8)


t = threading.Thread(target=_dono, daemon=True)
t.start()
segurou.wait(5)
t0 = time.time()
try:
    # a porta fica ocupada por mais tempo que UMA tentativa de cadeado: no
    # jeito antigo, isto levantava NaoConsegui em vez de enfileirar
    def _libera():
        time.sleep(4)          # > _TENTATIVA_CADEADO_S: a porta FICA ocupada
        fim.set()
    threading.Thread(target=_libera, daemon=True).start()
    s.esperar_vez("chegou depois", peso="pesado")
    checar(True, "esperou a porta abrir em vez de recusar")
except s.NaoConsegui:
    checar(False, "RECUSOU em vez de enfileirar — a fila virou erro")
t.join(15)
s._TENTATIVA_CADEADO_S = 60      # devolve o valor de producao

print(chr(10) + "11b. NEGATIVO: a espera nao e' infinita")
# Sem esta metade, "esperar sempre" travaria o processo pra sempre quando o
# dono da porta nunca soltasse.
d = limpo(SENTINELA_YT_INTERVALO=0, SENTINELA_YT_INTERVALO_LEVE=0,
          SENTINELA_YT_TETO_DIA=100, SENTINELA_YT_ESPERA_MAX=2)
(d / "cadeado").write_text(f"999999 {time.time():.0f}", encoding="utf-8")
t0 = time.time()
try:
    s.esperar_vez("porta trancada pra sempre", peso="pesado")
    checar(False, "passou por cima de um cadeado vivo")
except s.NaoConsegui:
    checar(time.time() - t0 < 90, "desiste dentro do teto de espera")

if falhas:
    print(chr(10) + f"{falhas} FALHA(S)")
    sys.exit(1)
print(chr(10) + "tudo verde")
