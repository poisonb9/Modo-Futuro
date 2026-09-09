# -*- coding: utf-8 -*-
"""Baixa fontes do YouTube em LOTE, espacadas no tempo, aqui na maquina.

Pedido do Bryan em 07/09/2026: "o YouTube barra quando baixa em lote; assim
como no projeto do livro, se baixarmos em intervalos a gente consegue — la'
baixamos mais de 40 legendas. Tenta isso com os videos".

## O QUE FOI MEDIDO ANTES DE ESCREVER ISTO

⚠️ **Esta maquina NAO esta' bloqueada.** Medido em 07/09/2026: um download
solto de 85 MB (Japanese Souffle Pancakes, 5,4 min) levou ~1 minuto, sem
espera, sem erro, sem CAPTCHA.

O bloqueio que o projeto conhece e' OUTRO: e' o do runner do GitHub, que sai
por IP de datacenter — e' por isso que o `cortar.yml` nunca teve um success
na vida e que todo download acontece aqui. Ver o handoff de 28/07/2026.

⚠️ Entao o espacamento aqui **nao esta' consertando um bloqueio observado**.
Ele e' seguro de lote: 1 download nao apanha, 40 seguidos podem. O custo de
espacar e' tempo de relogio, que sobra; o custo de apanhar e' o IP desta
maquina degradado, e ai' o projeto inteiro perde o unico caminho que funciona.

Ou seja: e' apolice, nao remedio. Se um dia o download solto TAMBEM falhar,
este arquivo nao e' a explicacao — procure o bloqueio de verdade.

## O QUE ELE NAO FAZ, DE PROPOSITO

**Nao sobe pro Drive e nao dispara corte.** Os dois ficam fora porque a pasta
do Drive e' que decide o CANAL, e foi exatamente ai' que nasceu o defeito de
04/09: o Yampolskiy caiu em SEM ANESTESIA e rendeu 8 clipes de IA publicados
no canal de comportamento. Baixar e' reversivel — e' um arquivo em disco.
Subir nao e': o vigia despacha em minutos.

Uso:
    python baixar_em_intervalos.py --radar radar_cozinha.json --max 5
    python baixar_em_intervalos.py --lista urls.txt --intervalo 240
    python baixar_em_intervalos.py --radar radar_cozinha.json --simular
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import registro_videos
from engine import cadencia
from engine import sentinela_youtube as sentinela

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "trabalho" / "brutos"
REGISTRO = RAIZ / "estado" / "baixados_em_intervalos.json"

# Espera entre um download e o seguinte. Tres minutos e' o meio-termo entre
# "some no ruido do trafego normal" e "40 videos em 2 horas".
#
# ⚠️ O NUMERO NAO E' MEDIDO — nao houve bloqueio pra calibrar contra. Ele vem
# da ordem de grandeza que funcionou com as legendas no projeto do livro (40+
# baixadas espacadas). Se algum dia aparecer um 429 de verdade, ESTE e' o
# numero pra mexer, e ai' ele passa a ser medido.
INTERVALO_S = 180

# Sorteio de +-30% em cima do intervalo. Espera exata e' padrao de robo: o
# proprio ritmo constante denuncia. Sortear custa nada.
JITTER = 0.30

# Formato: video ate' 1080p + audio, juntados em mp4. Acima de 1080 o arquivo
# dobra e o corte nao fica melhor — o destino e' um video 9x16 de celular.
FORMATO = "bv*[height<=1080]+ba/b[height<=1080]"


def _carregar() -> dict:
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _gravar(d: dict) -> None:
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                        encoding="utf-8")


def alvos(a) -> list[dict]:
    """A lista de (url, titulo), venha ela de um radar ou de um txt."""
    if a.radar:
        d = json.loads(Path(a.radar).read_text(encoding="utf-8"))
        # ⚠️ Respeita a ordem que o radar deu: ele ja' ordenou por nota, e a
        # nota dele ja' pondera o criterio do canal. Reordenar aqui seria
        # decidir de novo, com menos informacao.
        if a.so_na_faixa:
            d = [v for v in d if v.get("na_faixa")]
        return [{"url": v["url"], "titulo": v.get("titulo", "")} for v in d]
    # ⚠️ COMENTARIO NO FIM DA LINHA TAMBEM SAI. MEDIDO em 07/09/2026, na
    # primeira rodada de verdade: a lista tinha
    #
    #     https://youtube.com/watch?v=RaLzxZryEoA   # 5.4min 22252061 views
    #
    # e a linha INTEIRA virava a chave do registro. O yt-dlp engoliu a URL com
    # o comentario junto e baixou; o registro guardou a chave suja; e o video
    # que eu ja' tinha baixado foi baixado DE NOVO, porque a chave limpa nao
    # casava com a suja. Deduplicacao que nao dedupica e' pior que nenhuma:
    # ela da' a impressao de que o problema esta' resolvido.
    fora = []
    for l in Path(a.lista).read_text(encoding="utf-8").splitlines():
        l = l.split("#")[0].strip()
        if l:
            fora.append({"url": l, "titulo": ""})
    return fora


def baixar(url: str, canal: str = "") -> tuple[bool, str]:
    """Um download. Devolve (deu certo, mensagem).

    ⚠️ A CADENCIA E' COBRADA AQUI DENTRO, e nao em quem chama. Ordem do Bryan
    em 08/09/2026: "os downloads nunca podem coincidir de nenhum canal".
    Se a trava morasse no laco de `main()`, bastaria o `ciclo_semanal --todos`
    disparar dois canais em sequencia — ou alguem baixar a mao enquanto a
    tarefa agendada roda — pra ela ser contornada sem ninguem perceber. Aqui
    e' o unico ponto por onde todo download passa. Ver engine/cadencia.py.
    """
    with cadencia.vez(canal=canal, motivo=url[-24:]):
        return _baixar_agora(url)


def _baixar_agora(url: str) -> tuple[bool, str]:
    """O download em si. NAO chame direto — passe por `baixar`.

    ⚠️ DUAS TRAVAS, E ATE' 09/09/2026 ELAS ERAM DUAS PORTAS. A `cadencia` guarda
    o intervalo POR CANAL, com cadeado em `estado/cadencia_download.lock`; a
    `sentinela` guarda o YouTube inteiro, com cadeado em `~/.sentinela_youtube`.
    Sao arquivos diferentes: quem entrava por aqui nao era visto por quem
    entrava pelo `midia.baixar()`, e os dois podiam falar com o YouTube ao
    mesmo tempo — a REGRA ABSOLUTA da `PIPELINE.md` §8 violada por duas guardas
    que nao se conheciam. E' o mesmo molde de erro que a `FASE2.md` §1.2 ja'
    tinha registrado com o nome do canal.

    Agora as duas sao encadeadas: a cadencia continua contando por canal, e a
    sentinela e' a porta unica. O sono da sentinela acontece com o cadeado dela
    solto, entao esperar aqui nao tranca ninguem alem deste download.
    """
    cmd = [
        "yt-dlp", "-f", FORMATO, "--merge-output-format", "mp4",
        "--no-warnings", "--no-progress",
        # ⚠️ A retentativa do proprio yt-dlp com espera CRESCENTE. Se o
        # YouTube reclamar no meio, insistir rapido e' o pior que da' pra
        # fazer — e' o que transforma reclamacao em bloqueio.
        "--retries", "5", "--retry-sleep", "exp=5:120",
        # O id na frente do nome e' o que faz o `--auditar` do vigia
        # conseguir casar o bruto depois. Sem ele, todo arquivo e' acusado.
        "-o", str(DESTINO / "%(id)s__%(title).80s.%(ext)s"), url,
    ]
    # ⚠️ `vez()` mantem a porta fechada durante o download inteiro; o
    # `esperar_vez` sozinho so' garantia o espacamento entre inicios.
    with sentinela.vez(f"baixar {url[-24:]}", "pesado"):
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3600)
    if r.returncode != 0:
        bruto = (r.stderr or r.stdout or "").strip()
        # ⚠️ O FREIO E' PUXADO AQUI, no ponto que ve' o erro. Este script
        # devolve (False, motivo) em vez de levantar, e o `main()` segue pro
        # proximo da fila — sem isto, um bot-check viraria uma RAJADA de
        # tentativas, que e' exatamente o que confirma o padrao de robo.
        if sentinela.e_bloqueio(bruto):
            sentinela.puxar_freio(bruto[:300])
            return False, "BOT-CHECK: freio da sentinela puxado por 24h"
        erro = bruto.splitlines()
        return False, (erro[-1][:150] if erro else f"exit {r.returncode}")
    return True, "ok"


def main() -> None:
    p = argparse.ArgumentParser()
    fonte = p.add_mutually_exclusive_group(required=True)
    fonte.add_argument("--radar", help="json de radar (usa a ordem dele)")
    fonte.add_argument("--lista", help="arquivo com uma URL por linha")
    p.add_argument("--max", type=int, default=5,
                   help="quantos baixar nesta rodada (padrao 5)")
    p.add_argument("--intervalo", type=int, default=INTERVALO_S,
                   help=f"segundos entre downloads (padrao {INTERVALO_S})")
    p.add_argument("--so-na-faixa", action="store_true",
                   help="do radar, so' o que caiu na faixa de duracao boa")
    p.add_argument("--simular", action="store_true",
                   help="mostra o plano e a agenda, nao baixa nada")
    a = p.parse_args()

    DESTINO.mkdir(parents=True, exist_ok=True)
    feito = _carregar()
    fila = [v for v in alvos(a) if v["url"] not in feito][:a.max]

    if not fila:
        print("Nada novo pra baixar — tudo desta lista ja' esta' no registro.")
        return

    espera_media = a.intervalo
    total_min = (len(fila) - 1) * espera_media / 60
    print(f"{len(fila)} video(s), 1 a cada ~{espera_media}s "
          f"(+-{int(JITTER*100)}%) -> ~{total_min:.0f} min de relogio\n")

    for i, v in enumerate(fila, 1):
        rotulo = (v["titulo"] or v["url"])[:58]
        print(f"[{i}/{len(fila)}] {rotulo.encode('ascii', 'replace').decode()}")
        if a.simular:
            print("        SIMULADO (nada baixado)")
        else:
            t0 = time.time()
            ok, msg = baixar(v["url"], canal=getattr(a, "canal", "") or "")
            dur = time.time() - t0
            if ok:
                feito[v["url"]] = {"quando": datetime.now(timezone.utc).isoformat(),
                                   "titulo": v["titulo"], "segundos": round(dur)}
                _gravar(feito)
                # ⚠️ E TAMBEM NO REGISTRO MESTRE, que e' o que sobrevive ao
                # bruto. Ordem do Bryan em 07/09/2026: "sempre deixe salvo no
                # arquivo mestre de todos os videos que ja' baixamos e seus
                # links, para que no futuro possamos rebaixar qualquer coisa".
                #
                # O registro mestre existe desde 29/07 e e' indexado pelo ID
                # do YouTube — mas ate' hoje ele NAO guardava a URL. O id
                # sozinho reconstroi o link, so' que exige saber disso; o
                # pedido foi explicito, e campo explicito nao depende de quem
                # le' saber a convencao.
                yt = registro_videos._id_youtube(v["url"])
                if yt:
                    try:
                        registro_videos.anotar(
                            yt, url=v["url"], titulo=v["titulo"],
                            baixado_em=datetime.now(timezone.utc).isoformat()[:19],
                            origem="baixar_em_intervalos")
                    except Exception as e:
                        # ⚠️ Falhar aqui NAO pode perder o download. Mas tem
                        # de aparecer: registro silenciosamente incompleto e'
                        # pior que registro ausente, porque parece completo.
                        print(f"        [!] NAO entrou no registro mestre: "
                              f"{str(e)[:70]}")
                print(f"        ok em {dur:.0f}s")
            else:
                # ⚠️ NAO REGISTRA O QUE FALHOU: a proxima rodada tenta de
                # novo. Registrar erro como se fosse feito e' como o clipe
                # orfao da cozinha nasce — sucesso aparente, nada no fim.
                print(f"        [!] FALHOU: {msg}")
                print("        parando a rodada. Se for bloqueio, insistir "
                      "agora e' o pior que da' pra fazer.")
                break

        # ⚠️ NAO HA' MAIS SLEEP AQUI. A espera passou pra `engine/cadencia`,
        # que a cobra ANTES de cada download e vale entre canais e entre
        # processos. Dormir aqui tambem so' somaria espera em cima de espera,
        # e daria a impressao falsa de que e' este laco que protege o IP.
        pass

    print(f"\nBaixados nesta rodada em: {DESTINO}")
    print("⚠️ NADA foi subido pro Drive e NENHUM corte foi disparado.")
    print("   A pasta do Drive e' que decide o canal — e' ali que nasceu o")
    print("   defeito de 04/09. Subir e' passo separado e deliberado:")
    print("   python enviar_bruto_drive.py --arquivo <arq> --pasta-id <pasta>")


if __name__ == "__main__":
    main()
