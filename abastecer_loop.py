# -*- coding: utf-8 -*-
"""Abastece TODOS os canais em loop: radar -> Gemini escolhe -> JDownloader
baixa -> sobe pro Drive (RAW/<CANAL>) -> apaga do PC -> vigia da VPS corta ->
o workflow enfileira no Buffer.

Ordem do dono em 30/09/2026: "organizar, fazer a puxada, baixar, subir e
apagar o temp da maquina local, encadear no vigia e deixar na fila para o
buffer, faz em loop" + "busca bem apurada e criteriosa" (+acervo).

## Criterio de escolha (acervo marketing-e-oferta, 30/09/2026)
- DEMONSTRADO: pedir a IA do Google que ASSISTA o video e de nota aos
  trechos; ficar com as maiores notas.
- DEMONSTRADO: partir de video que ja' provou alcance.
- AFIRMADO: gancho nos 3 s -> retencao -> recompensa.
  => pre-filtro por metrica (views, engajamento, max 2 por criador) e o
  Gemini assiste pelo link e da' nota a gancho, autossuficiencia, imagem que
  se mexe e tema. So' entra nota >= 9, imagem >= 8, tema >= 9.

## Travas
- ⚠️ `atefalhar` HOJE E' O GERACAO 2000 (nostalgia), desde 28/09. O radar
  `canais/atefalhar/radar.py` ainda e' de academia — NAO usar. O deste canal
  e' o `radar_nostalgia.py`. Em 30/09 cinco videos de academia foram parar
  na pasta dele por causa disso.
- Nada repetido: qualquer id de YouTube em qualquer .json do projeto, na
  fila deste loop, ou na `description` de bruto no Drive, esta' fora.
- A copia local so' e' apagada depois de conferir o tamanho no Drive.

    python abastecer_loop.py            # loop (30 min)
    python abastecer_loop.py --uma-vez  # uma passada
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

import contas_drive as cd  # noqa: E402
import enviar_bruto_drive as eb  # noqa: E402

PISO = 3            # abaixo disto o canal busca mais (mesmo piso do ciclo_semanal)
POR_REPOSICAO = 5   # quantas fontes entram por reposicao
AO_GEMINI = 10      # quantos candidatos o Gemini assiste por reposicao
INTERVALO_S = 30 * 60
JD = "http://127.0.0.1:3128"
BAIXADOS = Path.home() / "Downloads" / "abastecer"
ESTADO = RAIZ / "estado" / "abastecer_loop.json"
DIARIO = RAIZ / "handoff" / "abastecimento" / "DIARIO_LOOP.md"
MODELO = "gemini-3.6-flash"

CANAIS = {
    "semanestesia.pod": {
        "pasta": "SEM ANESTESIA", "radar": "canais/semanestesia.pod/radar.py",
        "json": "radar_semanestesia.json", "min_views": 300_000,
        "tema": "podcast/entrevista de disciplina, mentalidade, saude e "
                "performance (Huberman, Goggins, Jocko) — fala forte, sem rodeio"},
    "cozinha.importada": {
        "pasta": "COZINHA", "radar": "canais/cozinha.importada/radar.py",
        "json": "radar_cozinha.json", "min_views": 300_000,
        "tema": "receita pratica passo a passo, ingredientes e medidas claras, "
                "mao na massa na tela"},
    "truque.importado": {
        "pasta": "TRUQUE IMPORTADO", "radar": "canais/truque.importado/radar.py",
        "json": "radar_truque_importado.json", "min_views": 300_000,
        "tema": "tutorial de maquiagem passo a passo, close no rosto, "
                "procedimento que da' pra seguir"},
    # ⭐ 02/10/2026 (dono): Camarim K-pop — mesmas configs do make, angulo
    # de BASTIDOR (reacao, humor, fofura das idols).
    "camarim.kpop": {
        "pasta": "CAMARIM KPOP", "radar": "canais/camarim.kpop/radar.py",
        "json": "radar_camarim_kpop.json", "min_views": 100_000,
        "tema": "bastidores de idols de K-pop: reacoes, humor, fofura e conversa "
                "com fala (programa da Risabae, variedades), idol famosa com nome"},
    "modofuturo": {
        "pasta": "MODO FUTURO", "radar": "canais/modofuturo/radar.py",
        "json": "radar_modofuturo.json", "min_views": 150_000,
        "tema": "chips, semicondutores, fabricas e engenharia de ponta com "
                "imagem que se mexe (NAO slideshow, NAO analise/geopolitica)"},
    "atefalhar": {  # = Geracao 2000 (nostalgia) desde 28/09
        "pasta": "GERACAO 2000", "radar": "canais/atefalhar/radar_nostalgia.py",
        "json": "radar_nostalgia.json", "min_views": 300_000,
        "tema": "nostalgia de desenhos animados e cultura pop dos anos 90/2000 "
                "(teorias, curiosidades, bastidores) — NADA de academia/treino"},
}

PEDIDO = """Voce e' curador de videos-fonte para cortes de TikTok do canal com tema: {tema}.
Assista ao video e avalie com RIGOR — nota 9+ so' para o excepcional. Criterios:
1) GANCHO: ha' pelo menos 5 momentos que prendem nos 3 primeiros segundos?
2) AUTOSSUFICIENCIA: trechos de 30-90 s fazem sentido sozinhos (gancho, retencao, recompensa)?
3) IMAGEM: a cena se mexe (nao e' slideshow, tela parada, so' narracao sobre fotos)?
4) TEMA: fica 100% no tema do canal?
Responda SO' JSON: {{"nota":0-10,"gancho":0-10,"autossuficiencia":0-10,"imagem":0-10,"tema":0-10,"motivo":"uma frase"}}"""


# ------------------------------------------------------------------ util

def log(msg: str) -> None:
    linha = f"- {datetime.now():%d/%m %H:%M} {msg}"
    print(linha, flush=True)
    DIARIO.parent.mkdir(parents=True, exist_ok=True)
    with DIARIO.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", (s or "").lower()) if c.isascii())
    return re.sub(r"[^a-z0-9]", "", s)


def ler_estado() -> dict:
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except Exception:
        return {"pendentes": {}, "feitos": []}


def gravar_estado(e: dict) -> None:
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def ids_usados(estado: dict) -> set:
    u = set(estado["pendentes"]) | set(estado["feitos"])
    for f in glob.glob(str(RAIZ / "*.json")) + glob.glob(str(RAIZ / "estado" / "**" / "*.json"), recursive=True):
        if "radar_" in Path(f).name:
            continue
        try:
            u |= set(re.findall(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
                                Path(f).read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            pass
    return u


def titulos_usados() -> list[str]:
    """Titulos (normalizados, 25 letras) de brutos que ja' passaram pelo Drive.

    ⭐ 02/10/2026: o JDownloader salva o bruto SEM o id do YouTube no nome, e
    o `raw_vistos.json` guarda so' o nome do arquivo. A trava por id deixou o
    video do Hyunjin (Risabae) ir pro Camarim depois de ja' ter ido pro Make.
    """
    try:
        d = json.loads((RAIZ / "estado" / "raw_vistos.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    return [t for t in (_chave_titulo(Path(v.get("nome", "")).stem)[:25] for v in d.values()) if len(t) >= 10]


def _chave_titulo(t: str) -> str:
    """Como o `norm`, mas MANTEM letra de qualquer alfabeto (coreano, japones):
    o `norm` reduzia "18분동안 현진이..." a "18" e casava titulo diferente."""
    t = re.sub(r"_?\[[A-Za-z0-9_-]{11}\]$", "", t)          # id no fim do nome
    t = re.sub(r"\((?:\d{3,4}p|BQ|Description|[A-Za-z]+_ASR)[^)]*\)", "", t)  # sufixo do JD
    return "".join(c for c in unicodedata.normalize("NFKC", t).lower() if c.isalnum())


def ja_usado_pelo_titulo(titulo: str, usados_t: list[str]) -> bool:
    t = _chave_titulo(titulo)
    return bool(t) and any(u in t or t[:25] in u for u in usados_t)


# ------------------------------------------------------------------ drive

def _subpastas(s, pai: str) -> list:
    return s.files().list(
        q=f"'{pai}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id,name)").execute().get("files", [])


def estoque_drive() -> tuple[dict, set]:
    """Brutos esperando corte em RAW/<PASTA> (todas as contas) + ids de YouTube
    que ja' estao no Drive (description)."""
    est = {k: 0 for k in CANAIS}
    ids = set()
    pasta_canal = {v["pasta"]: k for k, v in CANAIS.items()}
    for c in cd.CONTAS:
        try:
            s = cd.servico(c)
            for p in _subpastas(s, c["raw"]):
                canal = pasta_canal.get(p["name"])
                fila = [p["id"]]
                while fila:
                    atual = fila.pop()
                    fila += [x["id"] for x in _subpastas(s, atual)]
                    arqs = s.files().list(
                        q=f"'{atual}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false",
                        fields="files(name,description)", pageSize=500).execute().get("files", [])
                    for a in arqs:
                        ids |= set(re.findall(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", a.get("description", "")))
                        if canal and a["name"].lower().endswith((".mp4", ".mkv", ".webm")):
                            est[canal] += 1
        except Exception as e:
            log(f"[!] Drive {c['nome']}: {str(e)[:90]}")
    return est, ids


# ------------------------------------------------------------------ escolha

def gemini_nota(url: str, tema: str) -> dict:
    from engine import keys
    rot = keys.gemini()
    for _ in range(min(5, len(rot))):
        k = rot.proxima().strip()
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent?key={k}",
                json={"contents": [{"parts": [{"file_data": {"file_uri": url}},
                                              {"text": PEDIDO.format(tema=tema)}]}],
                      "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                           "mediaResolution": "MEDIA_RESOLUTION_LOW"}},
                timeout=300)
        except Exception as e:
            return {"erro": str(e)[:80]}
        if r.status_code in (403, 429, 503):
            rot.queimar(k)
            continue
        if r.status_code != 200:
            return {"erro": r.status_code}
        try:
            return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
        except Exception as e:
            return {"erro": f"json: {str(e)[:60]}"}
    return {"erro": "chaves esgotadas"}


def escolher(canal: str, cfg: dict, usados: set) -> list:
    log(f"**{canal}** — rodando radar `{cfg['radar']}`")
    subprocess.run([sys.executable, "-X", "utf8", cfg["radar"]], cwd=RAIZ,
                   timeout=1800, capture_output=True)
    try:
        radar = json.loads((RAIZ / cfg["json"]).read_text(encoding="utf-8"))
    except Exception as e:
        log(f"[!] {canal}: radar sem arquivo ({e}) — nao baixo no escuro")
        return []
    usados_t = titulos_usados()
    novos = [i for i in radar if i.get("id") not in usados
             and not ja_usado_pelo_titulo(i.get("titulo", ""), usados_t)
             and i.get("views", 0) >= cfg["min_views"] and i.get("eng", 0) >= 2.5]
    novos.sort(key=lambda i: -i.get("nota", 0))
    por, cand = {}, []
    for i in novos:
        cri = (i.get("canal") or "").strip()
        if por.get(cri, 0) >= 2:
            continue
        por[cri] = por.get(cri, 0) + 1
        cand.append(i)
        if len(cand) == AO_GEMINI:
            break
    log(f"{canal}: {len(radar)} no radar, {len(novos)} ineditos e com alcance, "
        f"{len(cand)} vao ao Gemini")
    aprovados = []
    for i in cand:
        g = gemini_nota(i["url"], cfg["tema"])
        i["gemini"] = g
        ok = (isinstance(g.get("nota"), (int, float)) and g["nota"] >= 9
              and g.get("imagem", 0) >= 8 and g.get("tema", 0) >= 9)
        log(f"  {'✅' if ok else '·'} {g.get('nota', g.get('erro'))} — {i['titulo'][:60]} — {g.get('motivo', '')[:90]}")
        if ok:
            aprovados.append(i)
    aprovados.sort(key=lambda i: (-i["gemini"]["nota"], -i["gemini"].get("imagem", 0), -i.get("views", 0)))
    return aprovados[:POR_REPOSICAO]


def mandar_jd(canal: str, itens: list) -> bool:
    q = {"links": "\n".join(i["url"] for i in itens), "autostart": True,
         "destinationFolder": str(BAIXADOS / canal), "overwritePackagizerRules": True}
    try:
        r = requests.get(f"{JD}/linkgrabberv2/addLinks", params={"query": json.dumps(q)}, timeout=30)
        return r.status_code == 200
    except Exception:
        return False


# ------------------------------------------------------------------ subir

def subir_prontos(estado: dict) -> None:
    if not BAIXADOS.exists():
        return
    for v in list(BAIXADOS.rglob("*.mp4")):
        a = v.stat().st_size
        time.sleep(8)
        if not v.exists() or v.stat().st_size != a:
            continue  # ainda baixando
        base = norm(v.name)
        vid = next((k for k, p in estado["pendentes"].items()
                    if norm(p["titulo"])[:25] and norm(p["titulo"])[:25] in base), None)
        if not vid:
            continue
        p = estado["pendentes"][vid]
        conta = cd.escolher()
        if not conta:
            log("[!] TODAS as contas do Drive sem folga — esvazie a lixeira. Parei de subir.")
            return
        try:
            s = cd.servico(conta)
            dest = eb._achar_ou_criar_subpasta(s, conta["raw"], CANAIS[p["canal"]]["pasta"])
            eb.enviar(v, dest, apagar_local=True, conta=conta["nome"], subpasta="", url=p["url"])
        except Exception as e:
            log(f"[!] upload falhou ({p['titulo'][:40]}): {str(e)[:90]}")
            continue
        if not v.exists():
            estado["pendentes"].pop(vid)
            estado["feitos"].append(vid)
            gravar_estado(estado)
            log(f"⬆️ {p['canal']} → {conta['nome']}/RAW/{CANAIS[p['canal']]['pasta']}: {p['titulo'][:60]}")


def limpar_temp() -> None:
    """Apaga o que o JDownloader deixa junto (audio, legenda, capa, descricao)
    depois de 1 h parado — o .mp4 ja' subiu e foi apagado."""
    if not BAIXADOS.exists():
        return
    agora = time.time()
    for f in BAIXADOS.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".m4a", ".opus", ".srt", ".jpg", ".txt", ".webm", ".part") \
                and agora - f.stat().st_mtime > 3600:
            try:
                f.unlink()
            except Exception:
                pass
    for d in sorted(BAIXADOS.rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()


# ------------------------------------------------------------------ ciclo

def passada() -> None:
    estado = ler_estado()
    subir_prontos(estado)
    limpar_temp()
    est, ids_drive = estoque_drive()
    usados = ids_usados(estado) | ids_drive
    for canal, cfg in CANAIS.items():
        na_fila = sum(1 for p in estado["pendentes"].values() if p["canal"] == canal)
        if est[canal] + na_fila >= PISO:
            continue
        log(f"{canal}: estoque {est[canal]} no Drive + {na_fila} baixando < piso {PISO} — reposicao")
        # ⭐ 02/10/2026 (dono): o limite do JDownloader e' o DISCO, nao o dia.
        import shutil
        livre = shutil.disk_usage(RAIZ.anchor).free / 1e9
        if livre < 5:
            log(f"[!] disco com {livre:.1f} GB livres (< 5; < 3 e' critico) — sem download nesta passada")
            return
        itens = escolher(canal, cfg, usados)
        if not itens:
            log(f"{canal}: nenhum candidato passou no criterio — nao baixo nada fraco")
            continue
        if not mandar_jd(canal, itens):
            log(f"[!] JDownloader nao respondeu em {JD} — confira Deprecated API ligada")
            return
        for i in itens:
            estado["pendentes"][i["id"]] = {"canal": canal, "titulo": i["titulo"], "url": i["url"],
                                            "nota": i["gemini"].get("nota"),
                                            "quando": datetime.now().isoformat(timespec="minutes")}
            usados.add(i["id"])
        gravar_estado(estado)
        log(f"⬇️ {canal}: {len(itens)} no JDownloader")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uma-vez", action="store_true")
    a = p.parse_args()
    while True:
        try:
            passada()
        except Exception as e:
            log(f"[!] passada falhou: {type(e).__name__} {str(e)[:120]}")
        if a.uma_vez:
            break
        # durante downloads, volta mais cedo pra subir o que terminou
        time.sleep(300 if ler_estado()["pendentes"] else INTERVALO_S)


if __name__ == "__main__":
    main()
