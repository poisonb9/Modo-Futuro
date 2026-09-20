"""Uma publicacao por vez. Sem isto, duas se atropelam no meio do deploy.

MEDIDO em 20/09/2026, e por isso este arquivo existe:

  18:1x  eu disparei `publicar_bio.py --subir` a mao
  18:20  a tarefa `AchadinhoTotal_Publicar_Ao_Mudar` disparou SOZINHA
  18:2x  a minha verificacao acusou "NAO ESTA' NO AR em: pagomenos/todos,
         achadinhodehoje/todos, meulivro/todos"

Os dois publicadores estavam enviando para os MESMOS seis projetos do
Cloudflare Pages ao mesmo tempo. O upload direto substitui o diretorio
inteiro; dois de uma vez deixam o conjunto em estado misto — parte dos
enderecos com os bytes novos, parte com os velhos, e nenhum erro em lugar
nenhum. A guarda de verificacao pegou, que e' o trabalho dela; mas pegar
depois custa um deploy inteiro.

POR QUE ISSO IA REPETIR: o vigia compara, a cada 10 minutos, o hash de
`paginas/todos.html` e de `paginas/publicar_bio.py` no `origin/main`.
Ou seja, TODO push meu que toca a pagina agenda uma publicacao automatica
dentro de 10 minutos. Publicar a mao logo depois de empurrar e' a
colisao esperada, nao o azar.

A trava e' um arquivo com PID e carimbo. Vence sozinha (padrao 25 min)
para que um processo morto nao deixe o site travado para sempre.
"""
from __future__ import annotations

import datetime
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TRAVA = RAIZ / "estado" / "publicando.lock"
MINUTOS_ATE_VENCER = 25


def _vivo(pid: int) -> bool:
    """O processo da trava ainda existe? Windows nao tem sinal 0 util aqui."""
    try:
        import subprocess
        r = subprocess.run(["tasklist", "/FI", "PID eq " + str(pid)],
                           capture_output=True, text=True, timeout=20)
        return str(pid) in (r.stdout or "")
    except Exception:  # noqa: BLE001
        # nao consegui saber: trato como vivo e deixo o tempo resolver
        return True


def pegar() -> bool:
    """True se a trava e' minha. False = ja' tem publicacao rodando."""
    agora = datetime.datetime.now()
    try:
        if TRAVA.exists():
            try:
                pid_txt, quando_txt = TRAVA.read_text(encoding="utf-8").split(chr(10))[:2]
                pid = int(pid_txt.strip())
                quando = datetime.datetime.fromisoformat(quando_txt.strip())
            except Exception:  # noqa: BLE001
                pid, quando = -1, agora - datetime.timedelta(hours=1)
            idade = (agora - quando).total_seconds() / 60
            if idade < MINUTOS_ATE_VENCER and pid != os.getpid() and _vivo(pid):
                print("NAO PUBLIQUEI: ja' existe uma publicacao em andamento "
                      f"(pid {pid}, ha' {idade:.0f} min).")
                print("  Duas ao mesmo tempo deixam os 6 projetos do Pages em "
                      "estado misto — foi o que aconteceu em 20/09/2026 as 18:20.")
                print(f"  Se a outra morreu, a trava vence sozinha em "
                      f"{MINUTOS_ATE_VENCER - idade:.0f} min, ou apague "
                      f"{TRAVA}")
                return False
        TRAVA.parent.mkdir(parents=True, exist_ok=True)
        TRAVA.write_text(str(os.getpid()) + chr(10) + agora.isoformat(),
                         encoding="utf-8")
        return True
    except Exception as e:  # noqa: BLE001
        # a trava nunca pode impedir uma publicacao por defeito proprio
        print(f"  AVISO: nao consegui usar a trava ({e}). Seguindo sem ela.")
        return True


def soltar() -> None:
    try:
        if TRAVA.exists():
            TRAVA.unlink()
    except Exception:  # noqa: BLE001
        pass
