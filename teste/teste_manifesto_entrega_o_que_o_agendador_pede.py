# -*- coding: utf-8 -*-
"""Todo campo que o agendador PEDE do manifesto, o publicar_release ESCREVE.

⚠️ A CLASSE DE DEFEITO QUE ESTE ARQUIVO EXISTE PRA MATAR, tres instancias no
mesmo dia (09/09/2026):

    produto           morria no `meta` do main.py
    cauda_aparada_s   morria no item do manifesto
    quarentena        morria no item do manifesto  <- a mais cara

Sao DUAS copias POR NOMES em sequencia — o `meta` do `main.py` e o item do
manifesto no `publicar_release.py`. O que nao esta' nomeado nelas deixa de
existir, sem erro, sem log, com todo o resto funcionando.

⚠️ O CASO DA QUARENTENA MOSTRA O TAMANHO. O agendador tem uma guarda inteira,
escrita e comentada, recusando clipe traduzido pela reserva (Nemotron) —
decisao do Bryan em 02/09/2026, "quem decide isso e' ele, olhando". Ela le'
`v.get("quarentena")` de um item de manifesto que nunca teve o campo: devolvia
falso SEMPRE. A guarda existia e nao guardava nada.

⚠️ E POR ISSO ESTE TESTE NAO E' SOBRE UM CAMPO. Conferir campo a campo e' o
que ja' se fez tres vezes hoje. Aqui as duas listas sao LIDAS e comparadas: se
alguem acrescentar `v.get("campo_novo")` no agendador sem por o campo no
manifesto, o teste acusa no mesmo commit.
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

AGENDADOR = (RAIZ / "agendar_buffer.py").read_text(encoding="utf-8")
RELEASE = (RAIZ / "publicar_release.py").read_text(encoding="utf-8")

# `v` e' o nome do item de manifesto no agendador, por convencao do arquivo
# inteiro (`for k, v in ordenar(todos)`, `def cabe(v)`).
PEDIDOS = set(re.findall(r'v\.get\("([a-z_]+)"', AGENDADOR))

# O que o item do manifesto recebe no publicar_release. Pega tanto
# `"campo": ...` quanto o `**({"campo": ...} if ...)` do produto.
ESCRITOS = set(re.findall(r'"([a-z_]+)":', RELEASE))

# ⚠️ EXCECOES DECLARADAS, COM MOTIVO. Estes dois NAO vem do pipeline: sao
# anotacoes que o Bryan (ou um script de manutencao) poe no manifesto DEPOIS,
# pra mudar o destino de um clipe que ja' existe. Nascer ausente e' o estado
# certo deles — ausente quer dizer "nao anotado".
DE_FORA = {
    "nao_publicar": "anotacao manual: aposentado, nunca mais vai ao ar "
                    "(decisao de 02/09/2026 sobre os 6 da republicacao)",
    "republicacao": "anotacao manual: LIBERA passar por cima do 'ja' "
                    "publicado', pra quando ele QUER repostar",
}

falhas = []

faltando = PEDIDOS - ESCRITOS - set(DE_FORA)
for campo in sorted(faltando):
    falhas.append(f"o agendador le' `{campo}` do manifesto e o "
                  f"publicar_release NAO escreve — a guarda que depende dele "
                  f"e' silenciosamente falsa")

# ⚠️ CASO NEGATIVO 1: as duas leituras tem de estar VENDO alguma coisa. Duas
# listas vazias tambem dao diferenca vazia, e o teste passaria sem ler nada.
if len(PEDIDOS) < 8:
    falhas.append(f"so' {len(PEDIDOS)} campo(s) lidos do agendador — a busca "
                  "quebrou (eram 13 em 09/09/2026)")
if len(ESCRITOS) < 8:
    falhas.append(f"so' {len(ESCRITOS)} campo(s) lidos do publicar_release — "
                  "a busca quebrou")

# ⚠️ CASO NEGATIVO 2: a regra tem de saber ACUSAR. Um campo inventado, que o
# agendador pediria e ninguem escreve, precisa cair na conta.
if "campo_que_ninguem_escreve" in ESCRITOS or \
        "campo_que_ninguem_escreve" in DE_FORA:
    falhas.append("caso negativo mal montado")
else:
    fingido = ({"campo_que_ninguem_escreve"} | PEDIDOS) - ESCRITOS - set(DE_FORA)
    if "campo_que_ninguem_escreve" not in fingido:
        falhas.append("NEGATIVO: a regra nao acusaria um campo pedido e nunca "
                      "escrito")

# os tres que custaram o dia continuam cobertos, nominalmente
for campo in ("quarentena", "traduzido_por", "produto", "cauda_aparada_s"):
    if campo not in ESCRITOS:
        falhas.append(f"`{campo}` saiu do manifesto — ja' custou uma vez")

# excecao orfa esconde o proximo defeito
for campo, motivo in DE_FORA.items():
    if campo not in PEDIDOS:
        falhas.append(f"`{campo}` esta' na lista de excecao e o agendador nem "
                      "pede mais — excecao orfa")
    if not motivo.strip():
        falhas.append(f"`{campo}` esta' fora sem motivo escrito")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_manifesto_entrega_o_que_o_agendador_pede: "
      f"{len(PEDIDOS)} campo(s) pedidos, {len(DE_FORA)} de fora por anotacao "
      "manual, nenhum orfao")
