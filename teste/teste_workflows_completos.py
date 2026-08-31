# -*- coding: utf-8 -*-
"""Todo workflow que CORTA tem de publicar — nao pode haver caminho cego.

POR QUE EXISTE

Em 31/08/2026 apareceram DOIS caminhos que cortavam e paravam antes de
publicar. Nos dois casos o clipe saia orfao: sem canal declarado, sem URL
publica, sem entrar em fila nenhuma.

  cozinha (repo pipeline)  so' chamava `previa_buffer.py` -> RASCUNHO
  cortar.yml (Modo-Futuro) parava no Drive

O `cortar.yml` tinha 4 runs na historia contra 197 do `cortar_de_bruto.yml`,
entao o defeito ficou invisivel por desuso. Mas ele e' o UNICO que corta
direto de uma URL — e essa falta custou trabalho manual no mesmo dia: foi
preciso baixar um bruto com yt-dlp local, subir pro Drive e disparar o outro
workflow, so' porque este nao tinha os parametros de canal e voz.

⚠️ O PADRAO DO DEFEITO, que se repetiu o dia inteiro: a peca existe e a ponta
que a liga ao mundo real falta. `VOZ_CANAL` sem o input no workflow.
`SELECAO_MODO` sem o input. `edge-tts` fora do requirements. `AMOSTRA_VOZ`
apontando pra um arquivo que nenhum passo baixava. Este teste olha as PONTAS.

Roda com: python teste/teste_workflows_completos.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import yaml  # noqa: E402

falhas = []


def checar(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


# workflows que produzem clipe pra publicar
CORTAM = ["cortar.yml", "cortar_de_bruto.yml"]

print(__doc__.splitlines()[0])

for arq in CORTAM:
    p = RAIZ / ".github" / "workflows" / arq
    print(f"\n=== {arq} ===")
    if not p.exists():
        checar(False, f"{arq} existe")
        continue
    bruto = p.read_text(encoding="utf-8")
    d = yaml.safe_load(bruto)
    ins = d[True]["workflow_dispatch"]["inputs"]
    passos = d["jobs"][list(d["jobs"])[0]]["steps"]
    nomes = [(s.get("name") or "") for s in passos]
    por_nome = {(s.get("name") or ""): s for s in passos}

    # --- os inputs que decidem destino e voz --------------------------
    for campo in ("canal", "dublar", "voz_clonada", "amostra_voz",
                  "selecao_modo", "estilo_legenda"):
        checar(campo in ins, f"tem o input `{campo}`")

    # --- publica ------------------------------------------------------
    rel = [n for n in nomes if "Release" in n]
    buf = [n for n in nomes if "Enfileirar no Buffer" in n]
    checar(bool(rel), "publica numa Release (URL publica)")
    checar(bool(buf), "enfileira no Buffer")
    if rel and buf:
        checar(nomes.index(rel[0]) < nomes.index(buf[0]),
               "a Release vem ANTES do Buffer")

    # --- a guarda de canal, no destino --------------------------------
    for n in rel + buf:
        env = por_nome[n].get("env") or {}
        checar("CANAL_ESPERADO" in env, f"{n[:30]}: tem CANAL_ESPERADO")

    # --- ⚠️ AS PONTAS: o que o passo Cortar promete, alguem cumpre? ---
    cortar = [n for n in nomes if n == "Cortar" or n.startswith("Cortar ")]
    checar(bool(cortar), "tem passo Cortar")
    if cortar:
        env = por_nome[cortar[0]].get("env") or {}
        cmd = " ".join(str(por_nome[cortar[0]].get("run", "")).split())

        # a amostra que o env aponta tem de ser baixada por algum passo
        if "AMOSTRA_VOZ" in env:
            baixa = [n for n in nomes if "amostra" in n.lower()]
            checar(bool(baixa),
                   "algum passo BAIXA a amostra que o env AMOSTRA_VOZ aponta")
            if baixa:
                checar(nomes.index(baixa[0]) < nomes.index(cortar[0]),
                       "e baixa ANTES de cortar")

        # as flags de dublagem tem de chegar na linha de comando
        checar("--dublar" in cmd,
               "a flag --dublar chega ao main.py")
        checar("--fala-literal" in cmd,
               "a flag --fala-literal chega ao main.py")
        checar("--estilo-legenda" in cmd,
               "a flag --estilo-legenda chega ao main.py")

        # os inputs de voz tem de chegar ao ambiente
        for v in ("VOZ_CANAL", "VOZ_CLONADA", "SELECAO_MODO", "VOICE_OVER"):
            checar(v in env, f"{v} chega ao ambiente do corte")

print()
if falhas:
    print(f"{len(falhas)} FALHA(S)")
    sys.exit(1)
print("tudo verde")
