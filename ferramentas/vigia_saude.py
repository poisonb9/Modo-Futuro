# -*- coding: utf-8 -*-
"""TRAVAS do abastecimento: acha o que esta' travando o fluxo, conserta o que da'
e avisa o resto. Tarefa ModoFuturo_Vigia_Saude, a cada 30 min.

08/10/2026 (dono: "cria um sistema, uma trava, que identifique esse e outros
problemas que estao travando nosso fluxo automatico de abastecimento"). O que
travou de 06 a 08/10, e ninguem viu:
  - JDownloader MUDO desde 06/10 22:25 (processo vivo, API 3128 sem resposta);
    `addLinks` falhava calado e 5 pendentes ficaram 2 dias parados.
  - Gemini reavaliando os MESMOS reprovados a cada passada (um video 32 vezes)
    -> cota queimada -> "chaves esgotadas" -> nada novo aprovado.
  - Estoque 0 em todos os canais com criterio nota >= 9.
  - Disco perto do freio (3,5 GB).
Acervo (+acervo, 08/10): constancia de publicacao mantem resultado; banco de
reserva + alerta de falha em automacao de producao.

O FLUXO e as travas checadas, na ordem:
  loop vivo -> radar -> Gemini -> JD -> upload -> Drive -> corte (GitHub) -> estoque
  + disco + tarefas agendadas.
Cada trava vira {etapa, nivel, msg, conserto}. Nivel: "auto" (consertado
sozinho), "alerta" (precisa de gente). Tudo vai para `estado/travas.json` (para
painel/handoff) e o Telegram recebe SO' quando o conjunto muda (ou a cada 6 h
se persistir) -- alerta repetido vira ruido.

    python -X utf8 ferramentas/vigia_saude.py            # checa e conserta
    python -X utf8 ferramentas/vigia_saude.py --so-ler   # so' diagnostica
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import abastecer_loop as al  # noqa: E402

ESTADO = RAIZ / "estado" / "vigia_saude.json"
TRAVAS = RAIZ / "estado" / "travas.json"
EMERGENCIA = RAIZ / "estado" / "criterio_emergencia.json"
VIGIA_RAW_LOG = RAIZ / "estado" / "vigia_raw.log"
JD_EXE = Path.home() / "AppData" / "Local" / "JDownloader 2" / "JDownloader2.exe"
REPO, WORKFLOW = "poisonb9/Modo-Futuro", "cortar_de_bruto.yml"

DISCO_MIN_GB = 5.0
HORAS_ZERADO = 12
HORAS_SEM_UPLOAD = 24
HORAS_SEM_APROVADO = 48
MIN_LOOP_PARADO = 90
PENDENTE_VELHO_H = 2
PENDENTE_PRESO_H = 12
CORTE_PRESO_H = 6
FALHAS_CORTE_12H = 3
REPETIR_ALERTA_H = 6
#: tarefas agendadas: 0 = ok, 267009 = rodando, 267011 = ainda nao rodou
RESULTADO_OK = {"0", "267009", "267011"}


def _ler(p: Path, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return padrao


def _gravar(p: Path, d) -> None:
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


class Travas:
    def __init__(self, so_ler: bool):
        self.so_ler = so_ler
        self.lista: list[dict] = []

    def auto(self, etapa: str, msg: str) -> None:
        self.lista.append({"etapa": etapa, "nivel": "auto", "msg": msg})

    def alerta(self, etapa: str, msg: str, conserto: str = "") -> None:
        self.lista.append({"etapa": etapa, "nivel": "alerta", "msg": msg, "conserto": conserto})


# ------------------------------------------------------------- diario

def linhas_diario(horas: float) -> list[tuple[datetime, str]]:
    """Linhas datadas do DIARIO_LOOP nas ultimas `horas`."""
    try:
        txt = al.DIARIO.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    agora, ano, out = datetime.now(), datetime.now().year, []
    for l in txt[-4000:]:
        m = re.match(r"- (\d\d)/(\d\d) (\d\d):(\d\d) (.*)", l)
        if not m:
            continue
        d, mo, h, mi = map(int, m.groups()[:4])
        try:
            q = datetime(ano, mo, d, h, mi)
        except ValueError:
            continue
        if agora - q <= timedelta(hours=horas):
            out.append((q, m.group(5)))
    return out


# ------------------------------------------------------------- etapas

def chk_loop(t: Travas) -> None:
    ls = linhas_diario(48)
    if not ls:
        t.alerta("loop", "DIARIO_LOOP sem nenhuma linha em 48 h — o abastecer_loop nao roda",
                 "conferir a tarefa ModoFuturo_Abastecer e estado/abastecer_agendado.log")
        return
    idade = (datetime.now() - ls[-1][0]).total_seconds() / 60
    if idade > MIN_LOOP_PARADO:
        t.alerta("loop", f"abastecer_loop sem escrever no diario ha' {idade:.0f} min",
                 "conferir ModoFuturo_Abastecer / estado/abastecer.lock preso")


def chk_radar(t: Travas) -> None:
    """Radar ESGOTADO: varias passadas seguidas com <= 2 ineditos."""
    por: dict[str, list[int]] = {}
    for _, l in linhas_diario(24):
        m = re.match(r"([a-z.]+): \d+ no radar, (\d+) ineditos", l)
        if m:
            por.setdefault(m.group(1), []).append(int(m.group(2)))
        if "radar sem arquivo" in l:
            t.alerta("radar", l[:120], "o radar do canal quebrou — rodar o radar.py a mao e ver o erro")
    for canal, ns in por.items():
        if len(ns) >= 3 and max(ns[-3:]) <= 2:
            t.alerta("radar", f"{canal}: radar ESGOTADO ({ns[-1]} ineditos nas ultimas passadas)",
                     "ampliar fontes/termos do radar do canal")


def chk_filtro(t: Travas) -> None:
    """Radar COM material mas filtro de alcance/engajamento barrando tudo.
    08/10/2026: atefalhar tinha 155 ineditos e modofuturo 36, e ZERO passavam
    no eng >= 2,5% (nostalgia engaja ~0,7%, chip ~1,4%). Parecia "radar seco"."""
    usados = al.ids_usados(al.ler_estado())
    rep = al._ler_reprovados()
    for c, cfg in al.CANAIS.items():
        try:
            r = json.loads((RAIZ / cfg["json"]).read_text(encoding="utf-8"))
        except Exception:
            continue
        v = [i for i in r if i.get("id") not in usados and i.get("id") not in rep
             and i.get("views", 0) >= cfg["min_views"]]
        ok = [i for i in v if i.get("eng", 0) >= cfg.get("min_eng", 2.5)]
        if len(v) >= 5 and not ok:
            e = sorted(i.get("eng", 0) for i in v)
            t.alerta("criterio", f"{c}: {len(v)} ineditos com views, 0 passam no eng >= "
                     f"{cfg.get('min_eng', 2.5)}% (mediana {e[len(e) // 2]:.2f}%)",
                     "ajustar min_eng do canal em abastecer_loop.CANAIS (o Gemini segue filtrando)")


def chk_gemini(t: Travas) -> None:
    ok = falha = 0
    for _, l in linhas_diario(6):
        m = re.match(r"\s+(?:✅|·) (\S+) — ", l)
        if not m:
            continue
        try:
            float(m.group(1))
            ok += 1
        except ValueError:
            falha += 1
    if ok + falha >= 6 and falha / (ok + falha) > 0.7:
        t.alerta("gemini", f"Gemini falhou em {falha} de {ok + falha} avaliacoes nas ultimas 6 h "
                 "(cota/rede)", "mais chaves ou plano pago; reprovados ja' nao sao reavaliados")


def chk_aprovacao(t: Travas, estoque: dict) -> None:
    aprov = {}
    canal = None
    for _, l in linhas_diario(HORAS_SEM_APROVADO):
        m = re.match(r"\*\*([a-z.]+)\*\*", l)
        if m:
            canal = m.group(1)
        if l.strip().startswith("✅") and canal:
            aprov[canal] = aprov.get(canal, 0) + 1
    for c, n in estoque.items():
        if n < al.PISO and not aprov.get(c) and c in al.CANAIS:
            t.alerta("criterio", f"{c}: nenhum video aprovado em {HORAS_SEM_APROVADO} h com estoque {n}",
                     "radar sem material bom ou criterio alto demais (emergencia liga com 12 h zerado)")


def jd_vivo() -> bool:
    try:
        return requests.get(f"{al.JD}/jd/version", timeout=15).status_code == 200
    except Exception:
        return False


def reiniciar_jd() -> bool:
    subprocess.run(["taskkill", "/F", "/IM", "JDownloader2.exe"], capture_output=True)
    time.sleep(5)
    subprocess.Popen([str(JD_EXE)], creationflags=0x00000008)  # DETACHED_PROCESS
    for _ in range(36):  # ate' 3 min
        time.sleep(5)
        if jd_vivo():
            return True
    return False


def nomes_no_jd() -> list[str]:
    nomes = []
    for rota in ("downloadsV2", "linkgrabberv2"):
        try:
            r = requests.get(f"{al.JD}/{rota}/queryLinks", params={"query": "{}"}, timeout=30)
            nomes += [al.norm(x.get("name", "")) for x in r.json().get("data", [])]
        except Exception:
            pass
    return nomes


def chk_jd(t: Travas, est: dict) -> None:
    if not jd_vivo():
        if t.so_ler:
            t.alerta("jd", "JDownloader sem resposta na API 3128", "reiniciar o JDownloader")
            return
        if reiniciar_jd():
            t.auto("jd", "JDownloader estava mudo — reiniciado")
        else:
            t.alerta("jd", "JDownloader mudo e NAO voltou apos reiniciar",
                     "abrir o JDownloader a mao e ver se pede atualizacao/login")
            return
    loop = _ler(al.ESTADO, {"pendentes": {}})
    nomes = nomes_no_jd()
    tentativas = est.setdefault("reenvios", {})
    agora = datetime.now()
    for vid, p in loop.get("pendentes", {}).items():
        try:
            # o relogio recomeca a cada reenvio (senao o reenviado ja' nasce "preso")
            idade = agora - max(datetime.fromisoformat(p.get("quando", "")),
                                datetime.fromisoformat(est.get("reenvio_quando", {}).get(vid, "2000-01-01")))
        except Exception:
            continue
        if idade < timedelta(hours=PENDENTE_VELHO_H):
            continue
        chave = al.norm(p["titulo"])[:25]
        no_jd = bool(chave) and any(chave in n for n in nomes)
        if not no_jd and nomes:
            if tentativas.get(vid, 0) >= 2:
                t.alerta("jd", f"pendente perdido apos 2 reenvios: {p['canal']} — {p['titulo'][:50]}",
                         "video pode ter saido do ar/bloqueado; tirar de pendentes")
            elif not t.so_ler and al.mandar_jd(p["canal"], [p]):
                tentativas[vid] = tentativas.get(vid, 0) + 1
                est.setdefault("reenvio_quando", {})[vid] = agora.isoformat(timespec="minutes")
                t.auto("jd", f"reenviado ao JD: {p['canal']} — {p['titulo'][:50]}")
        elif no_jd and idade > timedelta(hours=PENDENTE_PRESO_H):
            t.alerta("upload", f"pendente ha' {idade.total_seconds() / 3600:.0f} h no JD sem subir: "
                     f"{p['titulo'][:50]}",
                     "se o JD marca 'Finished' e nao ha' .mp4 em Downloads/abastecer, e' DUPLICADO de "
                     "download antigo (JD nao baixa de novo): tirar dos pendentes ou apagar do JD e reenviar")


def chk_upload(t: Travas) -> None:
    ups = [q for q, l in linhas_diario(24 * 7) if l.startswith("⬆️")]
    if not ups or datetime.now() - ups[-1] > timedelta(hours=HORAS_SEM_UPLOAD):
        t.alerta("upload", "nenhum upload ao Drive desde "
                 + (ups[-1].strftime("%d/%m %H:%M") if ups else "> 7 dias"),
                 "ver JD e pendentes")
    for _, l in linhas_diario(6):
        if "TODAS as contas do Drive sem folga" in l:
            t.alerta("drive", "todas as contas do Drive sem espaco", "esvaziar a lixeira do Drive")
            break
        if "upload falhou" in l:
            t.alerta("drive", l[:120], "ver token/credencial da conta do Drive")
            break


def chk_corte(t: Travas) -> None:
    try:
        r = subprocess.run(["gh", "run", "list", "-R", REPO, "-w", WORKFLOW, "-L", "30",
                            "--json", "databaseId,status,conclusion,createdAt"],
                           capture_output=True, text=True, timeout=60)
        runs = json.loads(r.stdout or "[]")
    except Exception as e:
        t.alerta("corte", f"nao consegui ler os cortes no GitHub ({type(e).__name__})", "gh auth status")
        return
    agora = datetime.now(timezone.utc)
    recentes = [x for x in runs
                if agora - datetime.fromisoformat(x["createdAt"].replace("Z", "+00:00")) < timedelta(hours=12)]
    falhas = [x for x in recentes if x.get("conclusion") == "failure"]
    if len(falhas) >= FALHAS_CORTE_12H:
        t.alerta("corte", f"{len(falhas)} de {len(recentes)} cortes FALHARAM nas ultimas 12 h",
                 f"gh run view {falhas[0]['databaseId']} -R {REPO} --log-failed")
    for x in runs:
        if x["status"] in ("in_progress", "queued"):
            h = (agora - datetime.fromisoformat(x["createdAt"].replace("Z", "+00:00"))).total_seconds() / 3600
            if h > CORTE_PRESO_H:
                t.alerta("corte", f"corte {x['databaseId']} {x['status']} ha' {h:.0f} h (preso)",
                         f"gh run cancel {x['databaseId']} -R {REPO}")
    # fila do vigia RAW parada no mesmo numero o dia todo = gargalo de vagas
    try:
        cauda = VIGIA_RAW_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]
        filas = [int(m.group(1)) for l in cauda for m in [re.search(r"(\d+) na fila", l)] if m]
        if len(filas) >= 30 and min(filas[-30:]) >= 5:
            t.alerta("corte", f"fila do corte com >= {min(filas[-30:])} brutos esperando ha' horas",
                     "cortes levam 2-4 h e so' 3 rodam juntos — gargalo de vagas")
    except Exception:
        pass


def chk_brutos_no_pc(t: Travas) -> None:
    """O ciclo_semanal / baixar_em_intervalos baixa para trabalho/brutos e NAO
    sobe ("Subir e' passo separado e deliberado"). Foi assim que 17 brutos
    ficaram dias no PC sem nunca virar estoque (07/10/2026)."""
    pasta = RAIZ / "trabalho" / "brutos"
    if not pasta.exists():
        return
    limite = time.time() - 86400
    velhos = [f for f in pasta.iterdir() if f.is_file()
              and f.suffix.lower() in (".mp4", ".mkv", ".webm") and f.stat().st_mtime < limite]
    if velhos:
        gb = sum(f.stat().st_size for f in velhos) / 2**30
        t.alerta("brutos", f"{len(velhos)} bruto(s) ha' > 1 dia em trabalho/brutos ({gb:.1f} GB) — "
                 "baixados e nunca subidos", "triar com o Gemini e subir para RAW/<canal>")


def chk_disco(t: Travas) -> float:
    livre = shutil.disk_usage("C:\\").free / 2**30
    if livre < DISCO_MIN_GB and not t.so_ler:
        subprocess.run([sys.executable, "-X", "utf8", "ferramentas/faxina.py", "--apagar"],
                       cwd=RAIZ, capture_output=True, timeout=1800)
        novo = shutil.disk_usage("C:\\").free / 2**30
        t.auto("disco", f"faxina rodada: disco {livre:.1f} -> {novo:.1f} GB")
        livre = novo
    if livre < DISCO_MIN_GB:
        t.alerta("disco", f"disco com {livre:.1f} GB livres (o loop para < 3,5)",
                 "apagar algo grande fora do projeto ou subir o que esta' no PC")
    return livre


def chk_estoque(t: Travas, est: dict) -> dict:
    estoque, _ = al.estoque_drive()
    agora = datetime.now()
    zerado = est.setdefault("zerado_desde", {})
    emerg = _ler(EMERGENCIA, {})
    for canal, n in estoque.items():
        if n == 0:
            zerado.setdefault(canal, agora.isoformat(timespec="minutes"))
            h = (agora - datetime.fromisoformat(zerado[canal])).total_seconds() / 3600
            if h >= HORAS_ZERADO:
                t.alerta("estoque", f"{canal}: estoque 0 ha' {h:.0f} h", "")
                if not t.so_ler and not emerg.get(canal):
                    emerg[canal] = agora.isoformat(timespec="minutes")
                    t.auto("estoque", f"{canal}: criterio de emergencia LIGADO (nota >= 8)")
        else:
            zerado.pop(canal, None)
            if n >= al.PISO and canal in emerg and not t.so_ler:
                emerg.pop(canal)
                t.auto("estoque", f"{canal}: estoque {n} — criterio normal de volta")
    if not t.so_ler:
        _gravar(EMERGENCIA, emerg)
    return estoque


def chk_tarefas(t: Travas) -> None:
    try:
        r = subprocess.run(["schtasks", "/query", "/fo", "csv", "/v"], capture_output=True,
                           text=True, timeout=60, encoding="mbcs", errors="replace")
        vistas = set()
        for d in csv.DictReader(io.StringIO(r.stdout)):
            nome = d.get("TaskName", "")
            if "ModoFuturo" not in nome or nome in vistas or nome.endswith("Vigia_Saude"):
                continue
            vistas.add(nome)
            res = (d.get("Last Result") or "").strip()
            if res and res not in RESULTADO_OK:
                t.alerta("tarefas", f"{nome.strip(chr(92))}: ultima execucao terminou com codigo {res}",
                         "abrir o log da tarefa")
            if (d.get("Scheduled Task State") or "").lower() == "disabled":
                t.alerta("tarefas", f"{nome.strip(chr(92))} esta' DESATIVADA", "reativar no Agendador")
    except Exception as e:
        t.alerta("tarefas", f"nao consegui ler o Agendador ({type(e).__name__})", "")


# ------------------------------------------------------------- principal

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-ler", action="store_true")
    a = ap.parse_args()
    est = _ler(ESTADO, {})
    t = Travas(a.so_ler)
    agora = datetime.now()

    chk_loop(t)
    chk_radar(t)
    chk_filtro(t)
    chk_gemini(t)
    chk_jd(t, est)
    chk_upload(t)
    chk_corte(t)
    chk_brutos_no_pc(t)
    livre = chk_disco(t)
    try:
        estoque = chk_estoque(t, est)
    except Exception as e:
        estoque = {}
        t.alerta("drive", f"nao consegui ler o estoque no Drive ({str(e)[:80]})", "rede/credencial do Drive")
    chk_aprovacao(t, estoque)
    chk_tarefas(t)

    resumo = (f"{agora:%d/%m %H:%M} disco {livre:.1f} GB | estoque "
              + ", ".join(f"{k.split('.')[0]} {v}" for k, v in estoque.items()))
    print(resumo)
    for x in t.lista:
        print(("  🔧 " if x["nivel"] == "auto" else "  ⛔ ") + f"[{x['etapa']}] {x['msg']}"
              + (f"\n       → {x['conserto']}" if x.get("conserto") else ""))
    if a.so_ler:
        return 0

    _gravar(TRAVAS, {"quando": agora.isoformat(timespec="minutes"), "resumo": resumo,
                     "travas": t.lista})
    for x in t.lista:
        if x["nivel"] == "auto":
            al.log(f"🩺 {x['msg']}")

    alertas = [x for x in t.lista if x["nivel"] == "alerta"]
    autos = [x for x in t.lista if x["nivel"] == "auto"]
    assinatura = "|".join(sorted(x["etapa"] + ":" + re.sub(r"\d+", "#", x["msg"]) for x in alertas))
    ultimo = est.get("ultimo_alerta")
    repetir = bool(ultimo) and agora - datetime.fromisoformat(ultimo) > timedelta(hours=REPETIR_ALERTA_H)
    if autos or assinatura != est.get("assinatura") or (alertas and repetir):
        from engine import telegram
        corpo = ["🩺 Travas do abastecimento — " + resumo]
        corpo += ["🔧 " + x["msg"] for x in autos]
        corpo += ["⛔ [%s] %s%s" % (x["etapa"], x["msg"], ("\n   → " + x["conserto"]) if x.get("conserto") else "")
                  for x in alertas]
        if not alertas:
            corpo.append("✅ nenhuma trava aberta")
        telegram.enviar("\n".join(corpo))
        est["ultimo_alerta"] = agora.isoformat(timespec="minutes")
    est["assinatura"] = assinatura
    _gravar(ESTADO, est)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
