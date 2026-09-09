# -*- coding: utf-8 -*-
"""O wrapper da tarefa agendada tem de SOBREVIVER ao stderr do python.

⚠️ O DEFEITO, medido em 09/09/2026. A tarefa `ModoFuturo_Ciclo_Semanal` rodou
as 13:00, gravou o radar, saiu com exit 1 — e nao deixou UMA LINHA de log.

A causa e' do Windows PowerShell 5.1: com `$ErrorActionPreference = 'Stop'`,
qualquer linha que o python escreva em STDERR sob `2>&1` vira um ErrorRecord
TERMINANTE (NativeCommandError). O script morre na propria chamada — antes do
`Add-Content`, antes do aviso no Telegram. O unico sinal e' o exit code, que
ninguem esta' olhando.

⚠️ E' O CONTRARIO DO QUE O WRAPPER PROMETE. O comentario do vigia diz, com
todas as letras: "se o Python estourar, o traceback tem que cair no log em vez
de sumir". Traceback vai pro stderr. Ou seja: o unico caso em que o log
importava era exatamente o caso em que ele deixava de existir.

⚠️ E O VIGIA RODA A CADA 10 MINUTOS. Ele nunca tinha escrito em stderr, entao
o defeito estava dormindo — nao consertado, adormecido.

Reproduzido em duas linhas de PowerShell antes do conserto.
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# a chamada nativa que engole stderr: `& $python ... 2>&1 | Out-String`
CHAMADA = re.compile(r"&\s*\$python[^\r\n]*2>&1")

falhas = []
vistos = 0

for arq in sorted(RAIZ.glob("*_agendado.ps1")):
    txt = arq.read_text(encoding="utf-8")
    for m in CHAMADA.finditer(txt):
        vistos += 1
        antes = txt[:m.start()]
        # ⚠️ Vale a ULTIMA atribuicao antes da chamada, nao a existencia da
        # palavra em qualquer lugar do arquivo: os dois wrappers ligam 'Stop'
        # no topo de proposito, e devem VOLTAR pra ele depois.
        ligadas = re.findall(r"\$ErrorActionPreference\s*=\s*'(\w+)'", antes)
        if not ligadas or ligadas[-1] != "Continue":
            falhas.append(
                f"{arq.name}: a chamada ao python roda com "
                f"ErrorActionPreference='{ligadas[-1] if ligadas else 'Stop (padrao do arquivo)'}' "
                "— uma linha em stderr mata o wrapper antes de ele logar")
        # e tem de VOLTAR pro Stop depois, senao o resto do script fica frouxo
        depois = txt[m.end():]
        volta = re.search(r"\$ErrorActionPreference\s*=\s*'(\w+)'", depois)
        if not volta or volta.group(1) != "Stop":
            falhas.append(f"{arq.name}: nao volta pra 'Stop' depois da chamada")

# ⚠️ CASO NEGATIVO 1: o teste tem de estar VENDO chamada. Zero achados tambem
# da' zero falhas, e passaria calado — que e' o mesmo tipo de cegueira que o
# defeito acima.
if vistos < 2:
    falhas.append(f"so' {vistos} chamada(s) encontrada(s); eram 2 em "
                  "09/09/2026 (ciclo_semanal e vigia_raw) — a busca quebrou")

# ⚠️ CASO NEGATIVO 2: a regra tem de saber ACUSAR o padrao ruim.
RUIM = ("$ErrorActionPreference = 'Stop'\n"
        "$saida = & $python -X utf8 x.py 2>&1 | Out-String\n")
m = CHAMADA.search(RUIM)
if m is None:
    falhas.append("caso negativo mal montado: o padrao nem acha a chamada")
else:
    ligadas = re.findall(r"\$ErrorActionPreference\s*=\s*'(\w+)'", RUIM[:m.start()])
    if ligadas and ligadas[-1] == "Continue":
        falhas.append("NEGATIVO: a regra nao acusaria o padrao que matou o "
                      "ciclo semanal")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_wrapper_agendado_loga_o_erro: {vistos} chamada(s) nativa(s), "
      "todas capazes de logar o proprio erro")
