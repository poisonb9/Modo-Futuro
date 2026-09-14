# -*- coding: utf-8 -*-
"""Gera a versao PUBLICA da contra-capa, mascarada, e sobe pro repo `bio`.

    python paginas/publicar_bio.py            gera em paginas/_publicado/
    python paginas/publicar_bio.py --subir    gera, empurra E PUBLICA

## 🚨 LEIA ISTO ANTES DE DIZER QUE ALGUMA COISA "ESTA' NO AR"

⚠️ **EMPURRAR PRO `poisonb9/bio` NAO PUBLICA NADA.** Os projetos do Cloudflare
Pages sao de **upload direto** (`"source": null` na API), e NAO estao ligados
ao repositorio. O repo e' historico; quem serve o site e' o deploy.

Medido em 12/09/2026 as 21:57: o `--subir` tinha empurrado o commit certo e eu
anunciei "no ar". O site continuava com os botoes de WhatsApp, de um deploy
das 21:14. O `git push` deu certo e o SITE ESTAVA VELHO — nada no push avisa.

⭐ **A regra que sobrou disso: o unico jeito de saber e' BAIXAR A PAGINA DO
AR e procurar a mudanca nela.** `curl https://<projeto>.pages.dev/` e conferir.
Status de push, "Deployment complete" e commit verde nao sao prova; a prova e'
o byte que o visitante recebe. Por isso o `--subir` agora publica e CONFERE, e
estoura se o ar nao tiver a mudanca.

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
import os
from pathlib import Path

from dotenv import load_dotenv

# ⚠️ O .env NAO SE CARREGA SOZINHO num script solto. Sem isto o passo de
# publicar reclamava de credencial que existe — e a tentacao seria
# concluir que o token acabou.
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# ⚠️ E O .env TRAZ UM `GITHUB_TOKEN` JUNTO, que e' o PAT fine-grained e NAO
# alcanca o repo `bio` — quem alcanca e' o `gh` logado nesta maquina. Com a
# variavel presente o git obedece a ela e o push morre com 128, sem dizer
# por que. Medido em 12/09/2026: sem a linha abaixo, o publicador para de
# funcionar no dia em que alguem carregar o .env.
os.environ.pop('GITHUB_TOKEN', None)
os.environ.pop('GH_TOKEN', None)

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "paginas" / "contra_capa.html"
# ⚠️ A PAGINA DO ANUNCIANTE, e nao da bio. Ela vai como ROTA `/parceiros`
# dentro dos MESMOS projetos, e nao num projeto novo: a conta bateu o teto
# de 10 projetos no Cloudflare (medido em 14/09/2026, os 10 ocupados, 4
# deles enderecos reservados do Ate Falhar).
#
# ⭐ E isto resolve o problema real: o Awin aceita UM endereco no perfil.
# Apontar pra `/parceiros` faz o avaliador ver a operacao inteira sem
# poluir a bio do canal, que tem outro trabalho (converter quem veio do
# video).
PARCEIROS = RAIZ / "paginas" / "quem_somos.html"
DESTINO = RAIZ / "paginas" / "_publicado"
SEGREDOS = (RAIZ.parent.parent.parent / "BACKUP_SISTEMA" / "SEGREDOS_NAO_SUBIR")
REPO = "poisonb9/bio"

# ⚠️ CADA CANAL TEM SEU ENDERECO NO CLOUDFLARE PAGES, e o endereco e' o que
# vai na bio. O nome do projeto e' a porta: a pagina le' `location.hostname`
# e sabe qual canal e'.
#
# ⚠️ NOME TOMADO NAO DA' ERRO NA CLOUDFLARE — ela cria com um sufixo aleatorio
# (`olivro` virou `olivro-oe0`). Medido em 12/09/2026 criando um nome sem
# sentido, que saiu limpo: sufixo significa "e' de outra pessoa". Conferir o
# `subdomain` da resposta e' a unica forma de saber.
PORTAS = {
    "oachadinho": "c1",        # Achadinho Make
    "meulivro": "c2",          # Sem Anestesia — reservado, fora da bio ate' a Kiwify
    "achadinhochef": "c5",
    "pagomenos": "c6",         # Fatura Chora
    "achadinhodehoje": "c7",
}

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


def tirar_previa(html: str) -> str:
    """Remove a caixa de previa — ela e' ferramenta nossa, nao pagina.

    ⚠️ MEDIDO em 12/09/2026, olhando a pagina JA' PUBLICADA: a caixa estava no
    ar. Ela diz, com todas as letras, "previa · nao vai ao ar" — e foi ao ar.
    Junto vinham as abas de trocar de canal: quem chegasse pelo TikTok do
    @achadinho.make via um quadro tracejado e botoes pros outros seis canais.

    A primeira versao deste publicador tirava comentario e achava que bastava.
    Comentario e' o que EXPLICA a ferramenta; a caixa e' a ferramenta.
    """
    return re.sub(r'\s*<section class="previa">.*?</section>', "", html,
                  flags=re.S)


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
        "não vai ao ar": "a CAIXA DE PREVIA (ela foi ao ar em 12/09)",
        'class="abas"': "as abas de trocar de canal",
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


# ⚠️ OS PROJETOS QUE ESTAO NO AR. Nao e' a mesma lista de PORTAS: ha' projeto
# reservado sem pagina (os cinco do Ate Falhar) e ha' projeto que existe mas
# fica fora da bio (o `meulivro`, ate' a Kiwify). Publicar so' nestes.
PROJETOS = ("oachadinho", "achadinhochef", "pagomenos", "achadinhodehoje",
            "meulivro")


def publicar_no_ar(html: str, parceiros: str = "") -> None:
    """Sobe pro Cloudflare Pages e CONFERE no ar. Estoura se nao subiu.

    ⚠️ ISTO E' O PASSO QUE FALTAVA, e a falta dele fez eu anunciar uma pagina
    que nao existia. O `git push` do repo `bio` nao dispara deploy nenhum: os
    projetos sao de upload direto. Ver o cabecalho do arquivo.
    """
    import shutil
    import tempfile
    tok = os.getenv("CF_API_TOKEN")
    conta = os.getenv("CF_ACCOUNT_ID")
    if not (tok and conta):
        raise SystemExit("faltam CF_API_TOKEN / CF_ACCOUNT_ID no .env")
    amb = dict(os.environ, CLOUDFLARE_API_TOKEN=tok,
               CLOUDFLARE_ACCOUNT_ID=conta)
    pasta = Path(tempfile.mkdtemp())
    (pasta / "index.html").write_text(html, encoding="utf-8")
    # ⚠️ UPLOAD DIRETO SUBSTITUI O DIRETORIO INTEIRO. Se a rota nao for
    # junto neste mesmo deploy, o deploy seguinte a APAGA — sem erro, sem
    # aviso, e o link que esta no perfil do Awin vira 404.
    if parceiros:
        (pasta / "parceiros").mkdir()
        (pasta / "parceiros" / "index.html").write_text(
            parceiros, encoding="utf-8")
    try:
        for proj in PROJETOS:
            subprocess.run(["npx", "--yes", "wrangler", "pages", "deploy",
                            str(pasta), "--project-name", proj,
                            "--commit-dirty=true"],
                           env=amb, check=True, capture_output=True,
                           shell=(os.name == "nt"))
            print(f"  publicado: {proj}")
    finally:
        shutil.rmtree(pasta, ignore_errors=True)


def conferir_no_ar(marca: str, marca_parceiros: str = "") -> list[str]:
    """Baixa cada pagina DO AR e procura a marca. Devolve quem nao tem.

    ⚠️ A PROVA E' O BYTE QUE O VISITANTE RECEBE. "Deployment complete" e commit
    verde ja' mentiram juntos uma vez — em 12/09/2026, e foi assim que a
    pagina com os botoes velhos ficou 40 minutos no ar sendo anunciada como
    nova.
    """
    import requests
    faltando = []
    for proj in PROJETOS:
        try:
            r = requests.get(f"https://{proj}.pages.dev/", timeout=30)
            if marca not in r.text:
                faltando.append(proj)
        except Exception as e:
            faltando.append(f"{proj} (nao respondeu: {e})")
        if not marca_parceiros:
            continue
        # ⚠️ A ROTA SE CONFERE SOZINHA. A raiz estar nova nao prova que
        # `/parceiros` subiu: sao dois arquivos no mesmo deploy, e e' o
        # segundo que esta' escrito no perfil do Awin.
        try:
            r = requests.get(f"https://{proj}.pages.dev/parceiros",
                             timeout=30)
            if marca_parceiros not in r.text:
                faltando.append(f"{proj}/parceiros")
        except Exception as e:
            faltando.append(f"{proj}/parceiros (nao respondeu: {e})")
    return faltando


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subir", action="store_true", help="empurra pro repo bio")
    a = p.parse_args()

    html = mascarar(tirar_previa(
        tirar_comentarios(ORIGEM.read_text(encoding="utf-8"))))

    # ⚠️ A pagina do anunciante passa pelo MESMO detector de vazamento. Ela
    # nao tem comentario de motor, mas tem nome de canal — e o detector ja'
    # pegou o nome do dono no rodape na primeira versao dela.
    parceiros = (PARCEIROS.read_text(encoding="utf-8")
                 if PARCEIROS.exists() else "")
    sobrou = conferir(html) + conferir(parceiros)
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
    # ⚠️ IDENTIDADE LOCAL, no clone. O `user.name` global desta maquina esta'
    # VAZIO, e sem identidade o `git commit` falha — foi assim que a primeira
    # tentativa morreu. Local, e nao global, pra nao mexer na configuracao da
    # maquina por causa de um script.
    subprocess.run(["git", "-C", str(tmp), "config", "user.name",
                    "poisonb9"], check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.email",
                    "poisonb9@users.noreply.github.com"], check=True)

    # ⚠️ UMA PASTA POR CANAL, pro endereco ficar `/bio/c1` em vez de
    # `/bio/?c=c1`. E' o mesmo arquivo copiado: o Pages serve arquivo, nao
    # rota, entao "rota bonita" aqui e' literalmente uma pasta com um
    # index.html dentro.
    #
    # Custa ~129 KB por canal. Nao vale inventar redirecionamento pra economizar
    # isso: redirecionamento e' um salto a mais antes de a pagina aparecer, e
    # quem vem do TikTok desiste no salto.
    for codigo in sorted(set(CODIGOS.values())):
        pasta = tmp / codigo
        pasta.mkdir(exist_ok=True)
        (pasta / "index.html").write_text(html, encoding="utf-8")
    print(f"  {len(set(CODIGOS.values()))} pastas de canal (/c1 ... /c7)")
    if parceiros:
        (tmp / "parceiros").mkdir(exist_ok=True)
        (tmp / "parceiros" / "index.html").write_text(
            parceiros, encoding="utf-8")

    subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True)
    # ⚠️ `check=True` no commit. Estava `False`, e o commit falhou CALADO — o
    # push seguinte reclamou de um branch sem commit nenhum, e a mensagem de
    # erro apontava pro lugar errado. Passo que pode falhar tem de falhar alto.
    r = subprocess.run(["git", "-C", str(tmp), "commit", "-m", "pagina de bio"],
                       capture_output=True, text=True)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        raise SystemExit("commit falhou:\n" + r.stdout + r.stderr)
    subprocess.run(["git", "-C", str(tmp), "push", "-u", "origin", "HEAD:main"],
                   check=True)
    print(f"\nempurrado para {REPO} (historico — isto NAO publica)")

    print("\npublicando no Cloudflare Pages:")
    publicar_no_ar(html, parceiros)

    # ⚠️ A MARCA E' UMA COISA QUE SO' A VERSAO NOVA TEM. Conferir "existe
    # pagina no ar" nao prova nada: a pagina velha tambem existe.
    # ⚠️ MARCA PROPRIA pra rota: uma frase que SO' existe na pagina do
    # anunciante. Procurar a marca da bio em `/parceiros` daria falso
    # negativo eterno (o Telegram aparece nas duas).
    marca_p = "search bidding" if parceiros else ""
    marca = "t.me/achadinhototal"
    print(f"\nconferindo no ar (procurando {marca!r}):")
    faltando = conferir_no_ar(marca, marca_p)
    if faltando:
        raise SystemExit(
            "NAO ESTA' NO AR em: " + ", ".join(faltando) +
            "\nO push pode ter dado certo e o site continuar velho "
            "— foi exatamente isso em 12/09/2026. Nao anuncie como publicado.")
    print(f"  confirmado em {len(PROJETOS)} projeto(s)")


if __name__ == "__main__":
    main()
