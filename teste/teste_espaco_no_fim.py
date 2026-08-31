# -*- coding: utf-8 -*-
"""O .txt termina com espaco vazio; o post publicado NAO.

Pedido do Bryan em 31/08/2026: no celular o seletor de texto agarra melhor
quando sobra area vazia depois da ultima linha.

⚠️ O CASO NEGATIVO E' O QUE IMPORTA AQUI. A mesma legenda vira o corpo do
post no Buffer e a mensagem do Telegram. Se a sobra vazasse pra `montar`,
todo post publicado sairia com oito linhas em branco no fim — um estrago
visivel em publico pra resolver um conforto de copiar. Por isso sao duas
funcoes, e por isso o teste vigia as duas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import legenda_post  # noqa: E402

META = {"titulo": "Um titulo", "descricao": "Uma descricao.",
        "legenda_premium": "Bloco premium.", "tags": ["um", "dois"]}

falhas = []

arq = legenda_post.para_arquivo(META)
post = legenda_post.montar(META)

# 1. o arquivo tem sobra de verdade
if not arq.endswith("\n" * legenda_post.LINHAS_VAZIAS_NO_FIM):
    falhas.append("o .txt nao termina com as linhas vazias")
if legenda_post.LINHAS_VAZIAS_NO_FIM < 3:
    falhas.append("sobra pequena demais pra ajudar no celular")

# 2. NEGATIVO — o post publicado nao pode ter sobra
if post != post.rstrip():
    falhas.append("o texto do post/Telegram esta' com espaco sobrando no fim")

# 3. e o conteudo tem de ser o MESMO, tirando a sobra
if arq.rstrip("\n") != post:
    falhas.append("o .txt e o post divergem no conteudo, nao so' no espaco")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_espaco_no_fim: {legenda_post.LINHAS_VAZIAS_NO_FIM} linhas "
      "no .txt, nenhuma no post")
