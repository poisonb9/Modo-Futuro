# -*- coding: utf-8 -*-
"""Item 16 do plano de ofertas: trecho de DEMONSTRACAO do produto, tirado do
YouTube PELO PC (a nuvem leva "Sign in to confirm you're not a bot").

    python -X utf8 ferramentas/demo_local.py            # ofertas de hoje
    python -X utf8 ferramentas/demo_local.py --id 1005012058103385

Esteira (decidida pelo dono em 30/09/2026 00:40):
  1. Produto sem video oficial do vendedor (esse vem SEMPRE primeiro).
  2. Busca na YouTube Data API (chaves do .env) com consulta em ingles.
     Pre-filtro: canal/titulo em portugues fora (decisao do dono 29/09: sem
     canal BR), duracao 20 s - 15 min, canal OFICIAL da marca na frente.
  3. O Gemini ASSISTE os 3 melhores e compara com a FOTO do anuncio.
     ⛔ Regra-mae do dono: NUNCA mostrar produto diferente do anunciado —
     so' passa `mesmo_produto` >= 9. Tambem pede: produto em uso, sem marca
     d'agua grande, e o segundo exato do melhor momento.
  4. JDownloader (API local :3128) baixa o video.
  5. ffmpeg corta so' o trecho (DEMO_S + 4 s: o video_oferta pula 3 s).
  6. Sobe o TRECHO pro Drive da conta com folga, pasta `DEMOS OFERTAS`,
     leitura publica (o workflow baixa sem login); apaga TUDO do PC.
  7. Grava `estado/demos_drive.json` {id: link} — o `video_oferta` usa.

Registro (ordem do dono 30/09: "tudo documentado, o que fez e que horas"):
  cada passo vira uma linha em `estado/demo_local.jsonl` e em
  `handoff/abastecimento/DIARIO_DEMOS.md`.
Trava: respeita `estado/demo_youtube_parado.json` (o botao de parar do dono).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from datetime import date, datetime
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "ferramentas"))

import contas_drive as cd  # noqa: E402
import enviar_bruto_drive as eb  # noqa: E402

JD = "http://127.0.0.1:3128"
BAIXADOS = Path.home() / "Downloads" / "abastecer" / "_demos"
DEMOS = RAIZ / "estado" / "demos_drive.json"
REG = RAIZ / "estado" / "demo_local.jsonl"
DIARIO = RAIZ / "handoff" / "abastecimento" / "DIARIO_DEMOS.md"
TRAVA = RAIZ / "estado" / "demo_youtube_parado.json"
PASTA_DRIVE = "DEMOS OFERTAS"
MODELO = "gemini-3.6-flash"
DUR_MIN, DUR_MAX = 20, 900
ESPERA_DOWNLOAD_S = 20 * 60

PT = re.compile(r"[ãõç]|\b(de|do|da|que|com|para|muito|vale a pena|comprei|testei|"
                r"resenha|análise|analise|mercado livre|shopee)\b", re.I)

PEDIDO = """Voce confere se um video do YouTube mostra EXATAMENTE o produto do anuncio.
Anuncio: "{nome}". A imagem anexa e' a foto do anuncio.
Assista ao video e responda com RIGOR:
- mesmo_produto (0-10): e' o MESMO produto da foto (formato, cor, portas, detalhes)? 10 = identico; produto parecido de outro modelo = no maximo 4.
- em_uso (0-10): mostra o produto funcionando/sendo usado, com close?
- marca_dagua (0-10): 10 = sem marca d'agua/texto grande por cima.
- melhor_segundo: o segundo (inteiro) onde comeca o melhor trecho de 8 s mostrando o produto em uso.
- motivo: uma frase.
Responda SO' JSON: {{"mesmo_produto":0,"em_uso":0,"marca_dagua":0,"melhor_segundo":0,"motivo":""}}"""


# ------------------------------------------------------------------ registro

def registrar(evento: str, **dados) -> None:
    agora = datetime.now()
    linha = {"quando": agora.isoformat(timespec="seconds"), "evento": evento, **dados}
    with REG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    DIARIO.parent.mkdir(parents=True, exist_ok=True)
    extra = " · ".join(f"{k}: {v}" for k, v in dados.items() if k != "pid")
    with DIARIO.open("a", encoding="utf-8") as f:
        f.write(f"- {agora:%d/%m/%Y %H:%M:%S} **{evento}** `{dados.get('pid', '')}` {extra}\n")
    print(f"[{agora:%H:%M:%S}] {evento} {extra}"[:220], flush=True)


# ------------------------------------------------------------------ busca

def _chaves_yt() -> list[str]:
    try:
        from dotenv import load_dotenv
        load_dotenv(RAIZ / ".env")
    except ImportError:
        pass
    ks = [os.getenv("YOUTUBE_API_KEY", "")] + [os.getenv(f"YOUTUBE_API_KEY_{i}", "") for i in range(2, 21)]
    return [k.strip() for k in ks if k and k.strip()]


def _yt_api(caminho: str, params: dict) -> dict:
    for k in _chaves_yt():
        r = requests.get(f"https://www.googleapis.com/youtube/v3/{caminho}",
                         params={**params, "key": k}, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code not in (403, 429):
            break
    return {}


def _dur_s(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return 0 if not m else int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + int(m[3] or 0)


def buscar(nome: str) -> tuple[str, list[dict]]:
    from demo_youtube import _marca, busca_em_ingles
    q = busca_em_ingles(nome)
    res = _yt_api("search", {"part": "snippet", "q": q, "type": "video", "maxResults": 15,
                             "relevanceLanguage": "en", "safeSearch": "strict"})
    ids = [i["id"]["videoId"] for i in res.get("items", [])]
    if not ids:
        return q, []
    det = _yt_api("videos", {"part": "contentDetails,statistics,snippet", "id": ",".join(ids)})
    marca = _marca(nome)
    out = []
    for v in det.get("items", []):
        tit, canal = v["snippet"]["title"], v["snippet"]["channelTitle"]
        dur = _dur_s(v["contentDetails"]["duration"])
        if not (DUR_MIN <= dur <= DUR_MAX) or PT.search(tit) or PT.search(canal):
            continue
        out.append({"id": v["id"], "url": f"https://www.youtube.com/watch?v={v['id']}",
                    "titulo": tit, "canal": canal, "dur": dur,
                    "views": int(v["statistics"].get("viewCount", 0)),
                    "oficial": bool(marca) and marca in canal.lower().replace(" ", "")})
    out.sort(key=lambda v: (not v["oficial"], -v["views"]))
    return q, out


# ------------------------------------------------------------------ gemini

def conferir(v: dict, nome: str, foto_url: str) -> dict:
    from engine import keys
    try:
        img = requests.get(foto_url, timeout=30).content
    except Exception as e:
        return {"erro": f"foto: {e}"}
    rot = keys.gemini()
    for _ in range(min(5, len(rot))):
        k = rot.proxima().strip()
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent?key={k}",
            json={"contents": [{"parts": [
                {"file_data": {"file_uri": v["url"]}},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(img).decode()}},
                {"text": PEDIDO.format(nome=nome)}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}},
            timeout=300)
        if r.status_code in (403, 429, 503):
            rot.queimar(k)
            continue
        if r.status_code != 200:
            return {"erro": r.status_code}
        try:
            return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
        except Exception as e:
            return {"erro": f"json {e}"}
    return {"erro": "chaves esgotadas"}


# ------------------------------------------------------------------ baixar/cortar/subir

def baixar_jd(url: str, pid: str) -> Path | None:
    destino = BAIXADOS / pid
    q = {"links": url, "autostart": True, "destinationFolder": str(destino),
         "overwritePackagizerRules": True}
    r = requests.get(f"{JD}/linkgrabberv2/addLinks", params={"query": json.dumps(q)}, timeout=30)
    if r.status_code != 200:
        return None
    t0 = time.time()
    while time.time() - t0 < ESPERA_DOWNLOAD_S:
        mp4 = [f for f in destino.rglob("*.mp4")] if destino.exists() else []
        if mp4:
            a = mp4[0].stat().st_size
            time.sleep(15)
            if mp4[0].exists() and mp4[0].stat().st_size == a:
                return mp4[0]
        time.sleep(15)
    return None


def cortar(origem: Path, ini: float, saida: Path) -> bool:
    from video_oferta import DEMO_S
    ini = max(0.0, ini - 3)  # o video_oferta pula 3 s de "logo"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ini:.1f}", "-i", str(origem),
                        "-t", f"{DEMO_S + 4:.1f}", "-an", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "20", "-vf", "scale='min(1080,iw)':-2", str(saida)],
                       capture_output=True)
    return r.returncode == 0 and saida.exists()


def limpar(pasta: Path) -> None:
    if not pasta.exists():
        return
    for f in sorted(pasta.rglob("*"), reverse=True):
        try:
            f.unlink() if f.is_file() else f.rmdir()
        except Exception:
            pass
    try:
        pasta.rmdir()
    except Exception:
        pass


# ------------------------------------------------------------------ produto

def fazer(pid: str) -> bool:
    import video_oferta as vo
    demos = json.loads(DEMOS.read_text(encoding="utf-8")) if DEMOS.exists() else {}
    if pid in demos:
        registrar("ja_tem_demo", pid=pid, link=demos[pid]["link"])
        return True
    d = vo.dados(pid, exigir_queda=False)
    if d.get("video"):
        registrar("tem_video_oficial", pid=pid, nome=d["nome"])
        return True
    nome, foto = d["nome"], (d.get("imagens") or [""])[0]
    registrar("inicio", pid=pid, nome=nome)
    q, cands = buscar(nome)
    registrar("busca", pid=pid, consulta=q, candidatos=len(cands))
    escolhido = None
    for v in cands[:3]:
        g = conferir(v, nome, foto)
        ok = (g.get("mesmo_produto", 0) >= 9 and g.get("em_uso", 0) >= 7 and g.get("marca_dagua", 0) >= 6)
        registrar("gemini", pid=pid, video=v["url"], canal=v["canal"], oficial=v["oficial"],
                  mesmo_produto=g.get("mesmo_produto"), em_uso=g.get("em_uso"),
                  marca_dagua=g.get("marca_dagua"), aprovado=ok, motivo=g.get("motivo", g.get("erro")))
        if ok:
            escolhido = (v, g)
            break
    if not escolhido:
        registrar("sem_demo", pid=pid, nome=nome,
                  motivo="nenhum video passou em mesmo_produto>=9 — fica a foto (regra-mae)")
        return False
    v, g = escolhido
    pasta = BAIXADOS / pid
    try:
        arq = baixar_jd(v["url"], pid)
        if not arq:
            registrar("download_falhou", pid=pid, video=v["url"])
            return False
        registrar("baixado", pid=pid, arquivo=arq.name, mb=round(arq.stat().st_size / 1e6))
        trecho = pasta / f"demo_{pid}.mp4"
        if not cortar(arq, float(g.get("melhor_segundo") or 0), trecho):
            registrar("corte_falhou", pid=pid)
            return False
        conta = cd.escolher(1.0)
        s = cd.servico(conta)
        dest = eb._achar_ou_criar_subpasta(s, conta["raiz"], PASTA_DRIVE)
        fid = eb.enviar(trecho, dest, apagar_local=True, conta=conta["nome"], subpasta="", url=v["url"])
        link = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
        demos[pid] = {"link": link, "drive_id": fid, "conta": conta["nome"], "fonte": v["url"],
                      "canal_youtube": v["canal"], "titulo_youtube": v["titulo"],
                      "segundo": g.get("melhor_segundo"), "mesmo_produto": g.get("mesmo_produto"),
                      "quando": datetime.now().isoformat(timespec="seconds")}
        DEMOS.write_text(json.dumps(demos, ensure_ascii=False, indent=1), encoding="utf-8")
        registrar("pronto", pid=pid, conta=conta["nome"], drive_id=fid, fonte=v["url"],
                  segundo=g.get("melhor_segundo"))
        return True
    finally:
        limpar(pasta)
        registrar("pc_limpo", pid=pid, pasta=str(pasta))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", action="append")
    ap.add_argument("--estoque", type=int, default=0,
                    help="varre as N melhores elegiveis sem video (nao so' as de hoje)")
    a = ap.parse_args()
    # ⛔ A trava e' o botao de parar do DONO. So' ele solta (apagando o
    # arquivo). Nenhum codigo decide ignorar.
    if TRAVA.exists():
        registrar("parado", motivo=json.loads(TRAVA.read_text(encoding="utf-8")).get("motivo"),
                  obs="botao de parar do dono (estado/demo_youtube_parado.json)")
        return
    from engine import ofertas
    if a.id:
        pids = a.id
    elif a.estoque:
        # ⭐ 30/09/2026: varre TODAS as elegiveis (nao so' as de hoje) pra o
        # video ja' existir quando o produto for escolhido. Pula quem ja' tem
        # video e quem ja' foi tentado sem sucesso nos ultimos 7 dias.
        tentados = set()
        if REG.exists():
            corte = (datetime.now().timestamp() - 7 * 86400)
            for l in REG.read_text(encoding="utf-8").splitlines():
                try:
                    x = json.loads(l)
                except ValueError:
                    continue
                if x.get("evento") == "sem_demo" and                         datetime.fromisoformat(x["quando"]).timestamp() > corte:
                    tentados.add(x.get("pid"))
        pids = [o["id"] for o in ofertas.candidatas(date.today())
                if not o["tem_video"] and o["id"] not in tentados][:a.estoque]
    else:
        pids = [o["id"] for os_ in ofertas.do_dia(date.today()).values() for o in os_]
    registrar("rodada", produtos=len(pids))
    for pid in pids:
        try:
            fazer(pid)
        except Exception as e:  # noqa: BLE001 — um produto nao derruba a rodada
            registrar("erro", pid=pid, erro=f"{type(e).__name__}: {str(e)[:150]}")


if __name__ == "__main__":
    main()
