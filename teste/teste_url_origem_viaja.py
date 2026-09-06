# -*- coding: utf-8 -*-
"""A URL da fonte tem de chegar ao manifesto, e sem palpite.

⚠️ O DEFEITO, MEDIDO EM 06/09/2026: `url_origem` era None em **175 de 175**
clipes do manifesto. Ninguem sabia de que video do YouTube cada corte veio.

Consequencia pratica, tambem medida no mesmo dia: o radar do @modofuturo
sugeriu de novo o "Inside The Chip Factory 1,000 Times Cleaner Than a
Hospital" — que JA' estava no RAW como "Dentro de la fabrica de chips 1,000
veces mas limpia que un quirofano". Mesmo video, titulo em outro idioma.
Nenhuma comparacao de NOME casaria os dois; a de ID casa sempre.

⚠️ E a duplicata nao e' detalhe: e' a causa medida dos dois colapsos de
alcance do projeto (02/08 e 25/08). A unica guarda que existia era o sha256,
que so' age DEPOIS do run inteiro pago.

A corrente que este teste protege:

    enviar_bruto_drive.py --url  ->  description do arquivo no Drive
    baixar_bruto_drive.py        ->  fonte.url.txt
    main.py                      ->  url_origem com confianca "exata"
    publicar_release.py          ->  manifesto
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

ENVIAR = (RAIZ / "enviar_bruto_drive.py").read_text(encoding="utf-8")
BAIXAR = (RAIZ / "baixar_bruto_drive.py").read_text(encoding="utf-8")
MAIN = (RAIZ / "main.py").read_text(encoding="utf-8")


# ------------------------------------------------- a corrente existe

def teste_o_upload_aceita_e_grava_a_url():
    assert '"--url"' in ENVIAR, "enviar_bruto_drive nao aceita --url"
    assert 'meta["description"] = url' in ENVIAR, (
        "a url nao vai pra description do arquivo no Drive")


def teste_o_download_le_a_description_e_grava_o_arquivo():
    assert 'fields="name,description"' in BAIXAR, (
        "o download nao pede a description — a url nunca volta")
    assert '.url.txt' in BAIXAR, "o download nao grava fonte.url.txt"


def teste_o_motor_prefere_a_url_exata():
    """⚠️ ORDEM IMPORTA: a exata tem de ser lida ANTES do palpite, senao o
    `origem.descobrir()` responde primeiro e a exata nunca e' usada."""
    # ⚠️ Pela EXPRESSAO, nao pelo nome do arquivo: ".origem.txt" aparece antes
    # num COMENTARIO, e a primeira versao deste teste reprovou por casar com
    # ele. Procurar nome solto acha texto; procurar a chamada acha codigo.
    i_exata = MAIN.index('fonte.with_suffix(".url.txt")')
    i_palpite = MAIN.index('fonte.with_suffix(".origem.txt")')
    assert i_exata < i_palpite, "o palpite roda antes da url exata"
    assert '"confianca": "exata"' in MAIN


# ------------------------------------------------- os negativos

def teste_negativo_sem_url_o_upload_NAO_quebra():
    """⚠️ FALHA ABERTA de proposito. Perder a origem incomoda; perder o
    upload, nao. O `--url` tem default vazio e o `description` so' entra
    quando ha' url."""
    assert 'p.add_argument("--url", default="",' in ENVIAR
    assert 'if url:' in ENVIAR, "a description entra sempre, ate' vazia"


def teste_negativo_o_palpite_CONTINUA_existindo():
    """Os brutos antigos nao tem url gravada, e adivinhar mal e' melhor que
    nao ter nada — desde que va' MARCADO como palpite."""
    assert 'origem.descobrir' in MAIN or '_origem.descobrir' in MAIN
    assert 'url_origem_confianca' in MAIN


def teste_negativo_a_url_exata_nao_e_confundida_com_palpite():
    """⚠️ TEOREMATICO: se as duas escrevessem a mesma confianca, ninguem
    conseguiria separar dado de chute no manifesto depois — e foi confiar em
    chute que criou o problema."""
    i = MAIN.index('"confianca": "exata"')
    trecho = MAIN[i - 400:i + 200]
    assert 'descobrir' not in trecho, (
        "a url exata esta' sendo montada pelo mesmo caminho do palpite")


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
