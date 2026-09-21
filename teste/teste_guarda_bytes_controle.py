"""Guarda de bytes de controle no carimbador (21/09/2026).

O byte 0x08 (backspace) apareceu DUAS vezes neste projeto, e de uma delas saiu
por commit e por SUITE VERDE: em `externalizar_motor`, o `|` do
`(?![^>]*src=)` era um 0x08, a lookahead nunca casava e a funcao deixou de
pular `<script src=...>`. Erro que reincide vira guarda, nao nota.

Prova aqui:

1. POSITIVO: corpo com 0x08 estoura, e a mensagem diz o byte e a linha;
2. POSITIVO: 0x00 e 0x7f (DEL) tambem estouram;
3. NEGATIVO -- o que faz este teste valer alguma coisa: corpo LIMPO passa
   intacto, e tab/CR/LF/acento/emoji nao sao acusados. Sem este caso, uma
   guarda que reprovasse TUDO passaria nos itens 1 e 2;
4. os TRES carimbadores chamam a guarda (html, motor.js, json externo) -- e'
   o funil por onde todo byte publicado passa;
5. o proprio `publicar_bio.py` e o `todos.html` estao limpos HOJE, lidos em
   BYTES. `sed`/`cat` nao servem: o TERMINAL executa o backspace e apaga o
   caractere anterior NA TELA -- a linha parece consertada e nao esta'.
"""
import inspect
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
sys.argv = ["x"]
import publicar_bio as pb  # noqa: E402

FALHAS = 0


def checar(ok, msg):
    global FALHAS
    print(("  ok   " if ok else "  [x]  ") + msg)
    if not ok:
        FALHAS += 1


def estoura(corpo, nome="x"):
    """(estourou?, mensagem)"""
    try:
        pb.sem_bytes_de_controle(corpo, nome)
        return False, ""
    except SystemExit as e:
        return True, str(e)


print("1. POSITIVO: O 0x08, O MESMO QUE PASSOU POR COMMIT")
# Reproduz o defeito real, byte a byte, com chr(8) no lugar do `|` da
# lookahead -- e nao escrevendo o byte neste arquivo, que seria semear de
# volta exatamente o que a guarda existe para pegar.
ruim = "linha um\nvar r = /(?![^>]*src=" + chr(8) + "$)/;\nlinha tres\n"
ok, msg = estoura(ruim, "motor.js")
checar(ok, "corpo com 0x08 estoura")
checar("0x08" in msg, "a mensagem nomeia o byte (" + msg[:60] + ")")
checar("linha 2" in msg, "e a LINHA certa, a 2 (" + msg[:80] + ")")
checar("motor.js" in msg, "e o arquivo")

print()
print("2. POSITIVO: O NULO E O DEL TAMBEM")
checar(estoura("a" + chr(0) + "b")[0], "0x00 estoura")
checar(estoura("a" + chr(127) + "b")[0], "0x7f (DEL) estoura")

print()
print("3. NEGATIVO: O CASO QUE FAZ ESTE TESTE VALER")
# Sem isto, uma guarda que dissesse "nao" para tudo passava nos itens 1 e 2.
limpo = ('<!doctype html>\r\n\t<meta charset="utf-8">\n'
         'preço R$ 11,89 ⭐ ⚠️ acentuação\n')
mau, msg = estoura(limpo)
checar(not mau, "corpo limpo NAO estoura (" + msg[:60] + ")")
checar(pb.sem_bytes_de_controle(limpo, "html") == limpo,
       "e volta intacto, o mesmo texto")
checar(pb.sem_bytes_de_controle("", "vazio") == "", "vazio passa")

print()
print("4. OS TRES CARIMBADORES CHAMAM A GUARDA")
for fn, nome in ((pb._carimbar, "_carimbar"),
                 (pb._carimbar_js, "_carimbar_js"),
                 (pb._carimbar_json, "_carimbar_json")):
    checar("sem_bytes_de_controle(" in inspect.getsource(fn),
           nome + " chama a guarda")

# e a guarda barra pelo CAMINHO do carimbador, nao so' sozinha
try:
    pb._carimbar('<meta charset="utf-8">\n' + chr(8))
    checar(False, "_carimbar deixou passar 0x08")
except SystemExit:
    checar(True, "_carimbar barra 0x08 de ponta a ponta")

print()
print("5. OS ARQUIVOS DE HOJE, LIDOS EM BYTES")
for rel in ("paginas/publicar_bio.py", "paginas/todos.html"):
    b = (RAIZ / rel).read_bytes()
    ruins = sorted({c for c in b if c < 32 and c not in (9, 10, 13)}
                   | ({127} & set(b)))
    checar(not ruins, rel + " sem byte de controle" +
           ("" if not ruins else " " + str([hex(c) for c in ruins])))

print()
print("tudo verde" if not FALHAS else str(FALHAS) + " FALHA(S)")
sys.exit(1 if FALHAS else 0)
