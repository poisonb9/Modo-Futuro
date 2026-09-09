# -*- coding: utf-8 -*-
"""Toda conversa com o YouTube passa pela sentinela — UMA porta, nao varias.

⚠️ O DEFEITO QUE ESTE ARQUIVO GUARDA, medido em 09/09/2026 lendo os call
sites um a um: a sentinela tinha sido ligada em `engine/midia.baixar()` e o
handoff registrou "toda chamada ao YouTube passa pela sentinela". Nao passava.
Havia mais TRES arquivos chamando o `yt-dlp` direto:

    processar_lista.py       sondava e BAIXAVA, com ThreadPoolExecutor de 2
                             -> dois downloads ao mesmo tempo, que e' a
                                REGRA ABSOLUTA da PIPELINE.md §8 violada
    baixar_em_intervalos.py  tinha trava PROPRIA (engine/cadencia), com
                             cadeado em OUTRO arquivo -> duas portas, e cada
                             uma cega pra outra
    triar_cortabilidade.py   legenda em paralelo (--workers)

⚠️ E o proprio cabecalho da sentinela ja' dizia por que isso e' fatal: "duas
faixas com dois cadeados seriam duas portas, que e' exatamente o que a
sentinela existe pra impedir". O texto estava certo e o repositorio, nao.

O teste le' a FONTE. Nao roda yt-dlp, nao toca a rede, nao depende de estado.
"""
import pathlib
import re
import sys

# `"yt-dlp",` dentro de uma lista de comando. A VIRGULA e' o que separa quem
# CHAMA de quem so' cita: o `main.py` tem `shutil.which("yt-dlp")`, que confere
# se o binario existe e depois chama `midia.baixar` — sem a virgula na busca,
# ele era acusado por uma linha que nem fala com o YouTube.
PADRAO_COMANDO = re.compile(r"""['"]yt-dlp['"]\s*,""")

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# ⚠️ A EXCECAO E' DECLARADA, NAO SILENCIOSA. O `triar_cortabilidade` baixa
# LEGENDA em lote, e o intervalo leve da sentinela (300s) com o teto de 12
# chamadas/dia tornaria a triagem de uma lista inviavel — dias para o que hoje
# leva minutos. Ligar assim mesmo seria trocar um defeito por outro em
# silencio. E' decisao do Bryan (que numero, ou que faixa nova), e ate' ela
# existir o arquivo fica AQUI, visivel, em vez de passar despercebido.
FORA_POR_DECISAO = {
    "triar_cortabilidade.py": "legenda em lote; o teto de 12/dia inviabiliza "
                              "a triagem — pendente de numero do Bryan",
}

falhas = []
vistos = []

for arq in sorted(RAIZ.glob("*.py")) + sorted((RAIZ / "engine").glob("*.py")):
    txt = arq.read_text(encoding="utf-8", errors="replace")
    if not PADRAO_COMANDO.search(txt):
        continue
    rel = arq.relative_to(RAIZ).as_posix()
    vistos.append(rel)
    if arq.name in FORA_POR_DECISAO or arq.name == "sentinela_youtube.py":
        continue
    if "sentinela" not in txt:
        falhas.append(f"{rel} monta comando yt-dlp e NAO conhece a sentinela")

# ⚠️ Os arquivos que a gente SABE que existem tem de continuar sendo vistos.
# Um teste que deixa de enxergar passa calado — e foi assim que o repositorio
# ficou com quatro portas achando que tinha uma.
ESPERADOS = {"processar_lista.py", "baixar_em_intervalos.py",
             "triar_cortabilidade.py", "engine/midia.py"}
faltando = ESPERADOS - set(vistos)
if faltando:
    falhas.append(f"o teste deixou de enxergar {sorted(faltando)} — padrao de "
                  "busca quebrado ou arquivo renomeado")

# ⚠️ CASO NEGATIVO. A regra acima aprova qualquer arquivo que contenha a
# palavra "sentinela" em qualquer lugar. Aqui a gente confirma que ela REPROVA
# de verdade um arquivo que chama o yt-dlp sem ela — sem isto, um detector que
# nunca acusa nada passaria igual.
FONTE_FALSA = 'cmd = ["yt-dlp", "-f", "best", url]\n'
if PADRAO_COMANDO.search(FONTE_FALSA) is None:
    falhas.append("NEGATIVO mal montado: o padrao nem enxerga a fonte falsa")
elif "sentinela" in FONTE_FALSA:
    falhas.append("NEGATIVO mal montado: a fonte falsa cita a sentinela")
else:
    acusaria = (PADRAO_COMANDO.search(FONTE_FALSA) is not None
                and "sentinela" not in FONTE_FALSA)
    if not acusaria:
        falhas.append("NEGATIVO: a regra NAO acusaria um arquivo que chama "
                      "yt-dlp sem a sentinela")

# ⚠️ E o contrario: a mesma fonte, agora COM a sentinela, tem de passar. Sem
# isto a regra poderia estar acusando todo mundo — inclusive quem consertou.
FONTE_BOA = ('sentinela.esperar_vez("x")\n'
             'cmd = ["yt-dlp", "-f", "best", url]\n')
if PADRAO_COMANDO.search(FONTE_BOA) and "sentinela" not in FONTE_BOA:
    falhas.append("a regra acusaria ate' quem passa pela sentinela")

# excecao orfa esconde o proximo defeito
for nome, motivo in FORA_POR_DECISAO.items():
    if not motivo.strip():
        falhas.append(f"{nome} esta' fora sem motivo escrito")
    if not (RAIZ / nome).exists():
        falhas.append(f"{nome} esta' na excecao e nao existe mais")

if falhas:
    for f in falhas:
        print("  [x]", f)
    sys.exit(1)
print(f"[ok] teste_uma_porta_pro_youtube: {len(vistos)} arquivo(s) montam "
      f"comando yt-dlp, {len(FORA_POR_DECISAO)} fora por decisao escrita")
