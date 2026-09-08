# -*- coding: utf-8 -*-
"""Nenhum .ps1 pode ter caractere fora do ASCII DENTRO de string.

⚠️ MEDIDO em 08/09/2026, e o defeito era invisivel do pior jeito.

O `ciclo_semanal_agendado.ps1` tinha esta linha:

    Add-Content -Value "[$carimbo] todos acima do piso — nada a repor"

O arquivo nao tem BOM, entao o Windows PowerShell 5.1 o le' como cp1252. Os
bytes UTF-8 do travessao (E2 80 94) viram tres caracteres nessa leitura, e o
ultimo (0x94) e' **aspa dupla**. A string fechava no meio da frase, o bloco
`if` perdia a chave, e o ARQUIVO INTEIRO deixava de ser parseavel.

O que isso teria custado: a tarefa agendada foi registrada com sucesso e
teria morrido na primeira execucao, as 13h do dia seguinte, sem escrever uma
linha de log. O unico sinal seria a ausencia de sinal — e o ciclo de um mes
que o Bryan pediu nunca teria comecado.

⚠️ EM COMENTARIO O MESMO CARACTERE E' INOFENSIVO: comentario vai ate' o fim da
linha, entao a aspa mangled nao abre string nenhuma. E' por isso que o
`vigia_raw_agendado.ps1` convive com acento ha' meses sem problema — e por
isso este teste olha SO' o que esta' dentro de aspas.

## POR QUE EM PYTHON E NAO CHAMANDO O POWERSHELL

O parser do PowerShell acharia isto na hora — foi ele que achou. Mas a suite
tem de rodar em qualquer maquina, inclusive no runner Linux, e um teste que
depende do `powershell.exe` vira teste que nao roda. Um teste que nao roda e'
pior que teste nenhum: ele conta como cobertura.
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Aspas duplas: sao as que interpolam e as que o byte 0x94 fecha. Aspas
# simples tem o mesmo risco de fechamento (0x92 e' aspa simples direita),
# entao entram tambem.
ASPAS = re.compile(r'"[^"\n]*"' r"|'[^'\n]*'")


def _linhas_uteis(txt: str):
    """As linhas sem a parte comentada.

    ⚠️ Corta no primeiro `#` que NAO esteja dentro de aspas — cortar em
    qualquer `#` acusaria `"#hashtag"`, que e' legitimo.
    """
    for n, linha in enumerate(txt.splitlines(), 1):
        fora, aspa = [], None
        for c in linha:
            if aspa:
                fora.append(c)
                if c == aspa:
                    aspa = None
                continue
            if c in "\"'":
                aspa = c
                fora.append(c)
                continue
            if c == "#":
                break
            fora.append(c)
        yield n, "".join(fora)


def teste_positivo_o_detector_pega_o_caso_que_originou_ele():
    """⚠️ Sem isto, um detector que nunca acusa passaria neste arquivo."""
    linha = 'Add-Content -Value "[$c] todos acima do piso — nada a repor"'
    achou = [s for s in ASPAS.findall(linha) if not s.isascii()]
    assert achou, "o detector nao pega o travessao dentro da string"


def teste_negativo_acento_em_COMENTARIO_passa():
    """O wrapper do vigia tem acento em comentario ha' meses e funciona."""
    linha = '# roda sem sessao interativa — impede a janela de piscar'
    for _, util in _linhas_uteis(linha):
        assert not [s for s in ASPAS.findall(util) if not s.isascii()]


def teste_negativo_hashtag_dentro_de_string_nao_e_comentario():
    linha = '$t = "assunto #chips"'
    (_, util), = _linhas_uteis(linha)
    assert "#chips" in util, "cortou no # que estava dentro de aspas"


def teste_todos_os_ps1_do_repo_estao_limpos():
    ps1 = sorted(RAIZ.glob("*.ps1")) + sorted(RAIZ.glob("**/*.ps1"))
    ps1 = sorted(set(ps1))
    assert ps1, "nenhum .ps1 encontrado — o teste estaria passando a toa"
    problemas = []
    for p in ps1:
        txt = p.read_text(encoding="utf-8", errors="replace")
        for n, util in _linhas_uteis(txt):
            for s in ASPAS.findall(util):
                if not s.isascii():
                    problemas.append(f"{p.name}:{n}  {s[:60]}")
    assert not problemas, (
        "caractere fora do ASCII dentro de string em .ps1 — o PowerShell 5.1 "
        "le' o arquivo como cp1252 e a string fecha no meio:\n  "
        + "\n  ".join(problemas))


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
