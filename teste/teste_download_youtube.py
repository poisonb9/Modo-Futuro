# -*- coding: utf-8 -*-
"""O comando de download nao pode voltar a forcar um cliente morto.

⚠️ POR QUE ESTE TESTE EXISTE.

O download do YouTube ficou quebrado por dias, e o erro trocava de cara —
"The page needs to be reloaded", "Requested format is not available" e
"Sign in to confirm you're not a bot" — o que fez o projeto perseguir tres
causas diferentes (cookie, PO Token, bloqueio de IP). Era UM defeito so',
com duas partes.

MEDIDO em 09/09/2026 contra o video real Jh9pFp1oM7E, so' com `-F`
(listagem, sem baixar nada):

    player_client=android + cookie          ->  0 formatos
    player_client=android + cookie + ejs    ->  0 formatos
    padrao + cookie, sem ejs                ->  so' os 4 storyboard
    padrao + ejs, SEM cookie                -> 40+ formatos, ate' 4K

Ou seja: o `player_client=android` (posto la' pra escapar do bot-check em
IP de datacenter) passou a devolver ZERO formato em qualquer combinacao, e
faltava o solver do desafio de JavaScript.

O QUE PRECISA SER PROVADO

  1. `--remote-components ejs:github` esta' no comando. Sem ele o YouTube
     retem os streams e sobra storyboard.
  2. ⚠️ `player_client=android` NAO esta'. Este e' o guarda de verdade: a
     linha foi util um dia, esta' documentada em varios handoffs, e e'
     exatamente o tipo de coisa que alguem reintroduz "consertando" o
     bot-check daqui a dois meses.
  3. CASO NEGATIVO: o resto do comando continua inteiro. Um teste que so'
     olha o que foi tirado passaria com o `baixar()` vazio.

Roda com: python teste/teste_download_youtube.py
"""
import inspect
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import midia

falhas = 0


def checar(cond, recado):
    global falhas
    if cond:
        print(f"  ok  {recado}")
    else:
        print(f"  FALHOU  {recado}")
        falhas += 1


fonte_bruta = inspect.getsource(midia.baixar)

# ⚠️ So' o CODIGO, sem comentario. A explicacao de por que o android saiu
# CITA "player_client=android" — se o teste olhasse o arquivo inteiro, ele
# reprovaria por causa do proprio comentario que documenta o conserto, e a
# saida obvia seria apagar a explicacao. Guarda que pune documentacao acaba
# apagada junto com ela.
fonte = chr(10).join(l for l in fonte_bruta.split(chr(10))
                     if not l.lstrip().startswith("#"))

print("1. o solver do desafio de JavaScript esta' no comando")
checar('"--remote-components", "ejs:github"' in fonte
       or "'--remote-components', 'ejs:github'" in fonte,
       "--remote-components ejs:github presente")

print("\n2. ATENCAO: o cliente android NAO voltou")
checar("player_client=android" not in fonte,
       "player_client=android ausente (devolve 0 formatos desde 09/09)")

print("\n3. CASO NEGATIVO: o resto do comando continua inteiro")
# Sem isto, um `baixar()` esvaziado passaria nos dois testes de cima.
for pedaco, oq in [('"yt-dlp"', "chama o yt-dlp"),
                   ('"-f"', "seletor de formato"),
                   ("height<=480", "teto de 480p (custo de runner)"),
                   ('"--merge-output-format", "mp4"', "junta em mp4"),
                   ("YTDLP_COOKIES_FILE", "ainda aceita cookie se houver"),
                   ("YTDLP_POT_SERVER", "ainda aceita PO Token se houver")]:
    checar(pedaco in fonte, oq)

print("\n4. e o cookie e o PO Token continuam OPCIONAIS")
# ⚠️ Medido em 09/09: sem cookie e sem PO Token, so' com o ejs, o download
# lista 40+ formatos. Os dois viraram reforco, nao requisito — mas nenhum
# dos dois pode ter virado obrigatorio no caminho.
checar("if cookies and Path(cookies).exists():" in fonte,
       "cookie so' entra se o arquivo existir")
checar("if pot_server:" in fonte, "PO Token so' entra se o servidor existir")

if falhas:
    print(chr(10) + f"{falhas} FALHA(S)")
    sys.exit(1)
print(chr(10) + "tudo verde")
