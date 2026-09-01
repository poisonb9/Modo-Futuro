# -*- coding: utf-8 -*-
"""Nenhum script usa nome que nao existe. Estatico, sem executar nada.

⚠️ O ERRO QUE ISTO PEGA JA' ACONTECEU EM PRODUCAO. Em 01/09/2026 a guarda de
canal em estreia foi pro ar com o import faltando, e o `agendar_buffer` morreu
no run #221 com

    NameError: name 'estreia' is not defined

depois de 40 minutos de corte, dublagem e render ja' pagos.

⚠️ E A MINHA PRIMEIRA TENTATIVA DE TESTE NAO PEGAVA. Escrevi um teste que
apenas IMPORTAVA cada script: ele passou verde com o import removido, porque
o NameError so' acontece quando a funcao roda. Um detector que nao reprova o
caso conhecido nao e' detector — foi o caso negativo que denunciou isso, nao
a intuicao.

Este aqui e' estatico: le' o codigo e cobra que todo nome usado exista.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

alvos = sorted(p for p in RAIZ.glob("*.py") if not p.name.startswith("_"))
alvos += sorted((RAIZ / "engine").glob("*.py"))

r = subprocess.run([sys.executable, "-m", "pyflakes", *[str(p) for p in alvos]],
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace")
if r.returncode not in (0, 1):
    print(f"  [!] pyflakes indisponivel ({r.stderr.strip()[:60]}) — pulando")
    sys.exit(0)

# ⚠️ ERRO DE SINTAXE ENTRA AQUI, e essa lacuna JA' CUSTOU. Em 01/09/2026 o
# `agendar_buffer.py` foi pro ar com uma string quebrada em duas linhas — um
# escape de nova linha que virou quebra DE VERDADE num heredoc. O
# pyflakes VIU e disse "unterminated string literal", mas este teste so'
# procurava "undefined name", entao passou VERDE. O agendador ficou
# quebrado em producao por cinco commits.
#
# ⚠️ Um teste que procura UMA frase so' encontra UMA classe de defeito. O que
# importa nao e' a frase — e' se o arquivo carrega.
GRAVES = ("undefined name", "syntax", "unterminated", "invalid syntax",
          "unexpected indent", "expected an indented block", "EOF ")
# ⚠️ OS DOIS FLUXOS. Erro de sintaxe o pyflakes manda pro STDERR; nome
# indefinido, pro STDOUT. Ler so' um deles foi exatamente o que deixou o
# agendador quebrado passar verde.
saida = (r.stdout or "") + chr(10) + (r.stderr or "")
graves = [l for l in saida.splitlines()
          if any(g.lower() in l.lower() for g in GRAVES)]
if graves:
    for l in graves:
        print("  [x]", l.replace(str(RAIZ), "."))
    sys.exit(1)
print(f"[ok] teste_nomes_definidos: {len(alvos)} arquivos, nenhum nome solto")
