# -*- coding: utf-8 -*-
"""Gera a versao PUBLICA da contra-capa, mascarada, e sobe pro repo `bio`.

    python paginas/publicar_bio.py            gera em paginas/_publicado/
    python paginas/publicar_bio.py --subir    gera e empurra pro repo bio

## POR QUE EXISTE

Ordem do Bryan em 12/09/2026: "evita por nomes que nao precise, use codigos,
deixe nosso repo mascarado".

A pagina que a gente edita e' cheia de comentario explicando o motor: nomes de
arquivo (`engine/canais_registro.py`), medicao (`playbook §23.9`), decisao de
negocio, data de incidente. Isso tudo e' util PRA GENTE e nao tem por que
estar num repositorio publico — quem abre o link quer os botoes, nao o mapa da
operacao.

⚠️ O QUE NAO DA' PRA MASCARAR, e nem deveria: o nome do canal, o @, a promessa
e os botoes. Eles SAO a pagina. Mascarar o que o visitante tem de ler seria
esconder o produto de quem ele existe pra servir.

⚠️ E O QUE SOBRA DE VERDADE depois do corte sao os nomes INTERNOS
(`truque.importado`, `cozinha.importada`) — eles nao aparecem na tela, so' no
codigo, e revelam a estrutura interna. Viram codigo aqui.

## A CHAVE DE LEITURA MORA FORA

O decodificador (qual codigo e' qual canal) vai pra
`BACKUP_SISTEMA\\SEGREDOS_NAO_SUBIR\\CODIGOS_DA_BIO.md`, que nao e' versionado.
Guardar a chave junto do texto cifrado e' nao cifrar nada.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "paginas" / "contra_capa.html"
DESTINO = RAIZ / "paginas" / "_publicado"
SEGREDOS = (RAIZ.parent.parent.parent / "BACKUP_SISTEMA" / "SEGREDOS_NAO_SUBIR")
REPO = "poisonb9/bio"

# nome interno -> codigo. So' entram os que NAO aparecem na tela.
CODIGOS = {
    "truque.importado": "c1",
    "semanestesia.pod": "c2",
    "atefalhar": "c3",
    "modofuturo": "c4",
    "cozinha.importada": "c5",
    "fatura.chora": "c6",
    "achadinhos.instantaneos": "c7",
}


def tirar_comentarios(html: str) -> str:
    """Tira comentario de JS, de CSS e de HTML.

    ⚠️ SO' A LINHA INTEIRA no caso do `//`: um `//` no meio da linha pode ser
    parte de uma URL (`https://...`), e cortar ali quebraria o link. A regra e'
    "linha cujo primeiro conteudo e' //", que e' exatamente o formato dos
    comentarios que a gente escreve.
    """
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"/\*.*?\*/", "", html, flags=re.S)
    linhas = [l for l in html.splitlines() if not l.lstrip().startswith("//")]
    # duas linhas em branco viram uma
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas))


def mascarar(html: str) -> str:
    """Troca os nomes internos por codigo, dentro das aspas."""
    for nome, codigo in CODIGOS.items():
        html = html.replace(f'banco: "{nome}"', f'banco: "{codigo}"')
    return html


def conferir(html: str) -> list[str]:
    """O que NAO pode sobrar na versao publica.

    ⚠️ Esta funcao e' o ponto do arquivo. Gerar mascarado e nao conferir e'
    confiar que a substituicao pegou tudo — e a substituicao erra calada.
    """
    proibido = {
        "engine/": "caminho de arquivo do motor",
        "playbook": "referencia ao playbook",
        "§23": "referencia a medicao",
        "canais_registro": "nome de modulo interno",
        "calibrag": "vocabulario interno",
        "manifesto": "vocabulario interno",
        "service_role": "CHAVE DE SERVICO",
        "sb_secret_": "CHAVE DE SERVICO",
        "MEDIDO": "nota de medicao",
        "Bryan": "nome do dono",
    }
    achados = []
    for termo, porque in proibido.items():
        if termo.lower() in html.lower():
            achados.append(f"{termo!r} ({porque})")

    # ⚠️ SO' OS NOMES QUE SAO DE VERDADE INTERNOS.
    #
    # A primeira versao desta guarda reprovava os sete, e estava errada: cinco
    # deles SAO o @ publico do canal (`@modofuturo`, `@atefalhar`...), aparecem
    # na tela e no link do TikTok. Exigir que sumissem seria exigir que a
    # pagina escondesse o proprio produto.
    #
    # Interno e' o nome que NAO bate com o @ publico: hoje sao dois, e sao
    # justamente os que revelam historia da operacao — o canal de maquiagem se
    # chama `truque.importado` por dentro, e a cozinha `cozinha.importada`.
    so_internos = [n for n in CODIGOS
                   if f"@{n}" not in html and n not in ("modofuturo",)]
    for nome in so_internos:
        # se o nome aparece SEM ser precedido de @, vazou
        if re.search(rf"(?<!@){re.escape(nome)}", html):
            achados.append(f"{nome!r} (nome interno de canal)")
    return achados


def escrever_decodificador() -> Path:
    linhas = ["# Códigos da página de bio — NAO SUBIR", "",
              "A página pública usa código no lugar do nome interno do canal.",
              "Esta é a chave de leitura, e ela mora FORA do repositório —",
              "guardar a chave junto do texto cifrado é não cifrar nada.", "",
              "| código | canal (nome_buffer) |", "|---|---|"]
    for nome, codigo in CODIGOS.items():
        linhas.append(f"| `{codigo}` | `{nome}` |")
    linhas += ["", "Gerado por `paginas/publicar_bio.py`. Se um canal mudar de",
               "nome, o código NÃO muda — é justamente para isso que ele serve."]
    SEGREDOS.mkdir(parents=True, exist_ok=True)
    alvo = SEGREDOS / "CODIGOS_DA_BIO.md"
    alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return alvo


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subir", action="store_true", help="empurra pro repo bio")
    a = p.parse_args()

    html = mascarar(tirar_comentarios(ORIGEM.read_text(encoding="utf-8")))

    sobrou = conferir(html)
    if sobrou:
        print("NAO PUBLIQUEI. Sobrou coisa interna na versao publica:")
        for s in sobrou:
            print("  -", s)
        sys.exit(1)

    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "index.html").write_text(html, encoding="utf-8")
    antes = len(ORIGEM.read_text(encoding="utf-8"))
    print(f"gerado: {DESTINO / 'index.html'}")
    print(f"  {antes // 1024} KB -> {len(html) // 1024} KB "
          f"({antes - len(html)} bytes de comentario a menos)")
    print(f"decodificador: {escrever_decodificador()}")

    if not a.subir:
        print("\n[sem --subir] nada foi empurrado.")
        return

    tmp = DESTINO / "_repo"
    subprocess.run(["rm", "-rf", str(tmp)], check=False)
    subprocess.run(["gh", "repo", "clone", REPO, str(tmp)], check=True)
    (tmp / "index.html").write_text(html, encoding="utf-8")
    (DESTINO / "LEIA.md").exists() and (tmp / "LEIA.md").write_text(
        (DESTINO / "LEIA.md").read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp), "commit", "-m",
                    "pagina de bio"], check=False)
    subprocess.run(["git", "-C", str(tmp), "push"], check=True)
    print(f"\nempurrado para {REPO}")


if __name__ == "__main__":
    main()
