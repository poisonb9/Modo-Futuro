# -*- coding: utf-8 -*-
"""O freio de mao dos cortes: um arquivo, e ninguem corta.

Ordem do Bryan em 07/09/2026: "pausa os cortes por enquanto — eu preciso dos
tokens do Gemini para outro projeto".

## POR QUE UM ARQUIVO NO REPOSITORIO, E NAO UM BOTAO

O corte e' disparado de TRES lugares, e nenhum deles conversa com os outros:

    vigia_raw.py       aqui na maquina, a cada passada, quando ve bruto novo
    cortar_fila.py     na nuvem, pelo cron de 30 min, consumindo a fila
    workflow_dispatch  a mao, por quem abrir o Actions

Desligar so' o vigia deixaria o cron cortando 29 itens. Desligar so' o cron
deixaria o vigia despachando bruto novo. Um freio que nao pega nos tres nao
e' freio — e' meia pausa, que e' pior, porque parece pausa.

Um ARQUIVO versionado pega nos tres pelo mesmo motivo: o workflow faz
checkout do repositorio antes de rodar qualquer coisa, entao a nuvem le' o
mesmo `PAUSA_CORTES` que esta' aqui no disco. Puxar o freio e' um commit;
soltar e' outro. Fica no historico quem parou, quando e por que.

⚠️ E O FREIO NAO IMPEDE DE BAIXAR NEM DE SUBIR PRO DRIVE. So' o CORTE gasta
Gemini. Baixar fonte e subir bruto continuam liberados de proposito: e' assim
que da' pra encher o estoque durante a pausa e ter o que cortar no minuto em
que ela sair. O vigia vai ver os brutos, dizer que estao esperando, e NAO
despachar.

Uso:
    from engine import freio
    if freio.puxado():
        print(freio.motivo()); return

    python -c "from engine import freio; freio.puxar('cota pro outro projeto')"
    python -c "from engine import freio; freio.soltar()"
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# ⚠️ NA RAIZ E COM NOME GRITADO, de proposito. Quem abrir o repositorio tem
# de tropecar nele. Freio escondido em `estado/` e' freio que fica puxado por
# uma semana sem ninguem notar — e ai' a pergunta vira "por que nao esta'
# saindo clipe?", que custa muito mais caro que um arquivo feio na raiz.
ARQUIVO = RAIZ / "PAUSA_CORTES"


def puxado() -> bool:
    """Os cortes estao pausados?"""
    return ARQUIVO.exists()


def motivo() -> str:
    """O texto que o arquivo carrega — quem parou, quando e por que.

    ⚠️ Devolve algo util MESMO se o arquivo estiver vazio. Um freio sem
    explicacao ja' e' ruim; um freio que ainda por cima imprime linha vazia
    faz o log parecer defeito.
    """
    try:
        txt = ARQUIVO.read_text(encoding="utf-8").strip()
    except Exception:
        txt = ""
    return txt or ("CORTES PAUSADOS por PAUSA_CORTES (sem motivo escrito). "
                   "Pra soltar: apague o arquivo e commite.")


def puxar(por_que: str, quem: str = "Claude") -> str:
    """Cria o freio. Devolve o texto gravado."""
    txt = (f"CORTES PAUSADOS\n\n"
           f"quem:    {quem}\n"
           f"quando:  {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
           f"por que: {por_que}\n\n"
           f"Enquanto este arquivo existir:\n"
           f"  - o vigia NAO despacha corte de bruto novo;\n"
           f"  - o cortar_fila NAO consome a fila;\n"
           f"  - baixar fonte e subir bruto pro Drive CONTINUAM liberados.\n\n"
           f"Pra soltar o freio: apague este arquivo e commite.\n")
    ARQUIVO.write_text(txt, encoding="utf-8")
    return txt


def soltar() -> bool:
    """Tira o freio. Devolve se havia algum."""
    if not ARQUIVO.exists():
        return False
    ARQUIVO.unlink()
    return True
