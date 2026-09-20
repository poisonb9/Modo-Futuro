"""O diario do site: uma entrada por publicacao CONFIRMADA no ar.

Ordem do Bryan (20/09/2026): "tudo que estamos fazendo, inclusive as
modificacoes no site, quero que voce versione e anote num documento, o que foi
feito e o motivo, sempre que subir o site — algo leve, rapido, e que nos da'
log historico".

AUTOMATICO DE PROPOSITO. Anotacao que depende de alguem lembrar nao sobrevive
a uma semana corrida. Isto roda no fim da publicacao, DEPOIS da verificacao no
ar — entao o diario so' registra o que de fato subiu, nunca o que se tentou.

A FONTE E' O PROPRIO COMMIT: assunto = o que foi feito, primeiro paragrafo do
corpo = o porque. Nada e' digitado duas vezes, e o diario nao pode divergir do
codigo.

NUNCA DERRUBA A PUBLICACAO: qualquer falha aqui vira aviso. O site no ar vale
mais do que a anotacao sobre ele.

Mora em `ferramentas/` e nao dentro do publicador porque a primeira tentativa
foi escrita por heredoc e os escapes colapsaram — um `\\x00` virou byte NUL de
verdade no meio do arquivo, e os `\\n` viraram quebras de linha dentro de
strings. Arquivo proprio, escrito de uma vez, nao tem essa classe de defeito.
"""
from __future__ import annotations

import datetime
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIARIO = RAIZ / "DIARIO_DO_SITE.md"

CABECA = (
    "# Diário do site — achadinhototal.com.br\n"
    "\n"
    "Uma entrada por publicação **confirmada no ar**, escrita pelo próprio\n"
    "publicador a partir do commit (assunto = o quê; primeiro parágrafo do\n"
    "corpo = o porquê). Mais novo primeiro.\n"
    "\n"
    "---\n"
    "\n"
)


def _do_commit() -> tuple[str, str, str]:
    """(sha curto, assunto, porque) do ultimo commit deste repositorio."""
    r = subprocess.run(
        ["git", "-C", str(RAIZ), "log", "-1", "--format=%h%n%s%n%b"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    partes = (r.stdout or "").split(chr(10), 2)
    sha = partes[0].strip() if partes else "?"
    assunto = partes[1].strip() if len(partes) > 1 else "(sem assunto)"
    corpo = partes[2] if len(partes) > 2 else ""
    # o motivo e' o primeiro paragrafo COM SUBSTANCIA. MEDIDO na estreia do
    # diario: o commit comecava com "Tres pedidos do Bryan (20/09)." e era
    # isso que ia para o campo "Por que" — um cabecalho, nao um motivo.
    candidatos = []
    for bloco in corpo.split(chr(10) + chr(10)):
        bloco = " ".join(bloco.split())
        if not bloco or bloco.startswith("Co-Authored-By"):
            continue
        candidatos.append(bloco)
    porque = ""
    for bloco in candidatos:
        if len(bloco) >= 90:
            porque = bloco
            break
    if not porque and candidatos:
        porque = candidatos[0]
    if len(porque) > 600:
        porque = porque[:597].rstrip() + "..."
    return sha or "?", assunto, porque


def anotar(marca: str, conferidos: list[str], tamanho_html: int) -> None:
    """Poe a entrada no TOPO do diario. Falha vira aviso, nunca excecao."""
    try:
        sha, assunto, porque = _do_commit()
        # o carimbo chega como `name="v" content="<sha>"`; no diario so' o sha
        so_sha = re.search(r'([0-9a-f]{8,})', marca or "")
        marca = so_sha.group(1) if so_sha else (marca or "?")
        agora = datetime.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M")
        linhas = [
            "## " + agora + " — `" + sha + "`",
            "",
            "**O quê:** " + assunto,
            "",
        ]
        if porque:
            linhas += ["**Por quê:** " + porque, ""]
        linhas += [
            "Carimbo no ar: `" + marca + "` · " + str(len(conferidos))
            + " endereço(s) conferidos · HTML " + str(tamanho_html // 1024) + " KB",
            "",
            "---",
            "",
        ]
        entrada = chr(10).join(linhas) + chr(10)
        velho = DIARIO.read_text(encoding="utf-8") if DIARIO.exists() else ""
        if velho.startswith(CABECA):
            velho = velho[len(CABECA):]
        DIARIO.write_text(CABECA + entrada + velho, encoding="utf-8", newline=chr(10))
        print("  diario: " + DIARIO.name + " atualizado (" + sha + ")")
    except Exception as e:  # noqa: BLE001
        print("  AVISO: nao consegui anotar no diario (" + str(e)
              + "). O site subiu igual.")
