# -*- coding: utf-8 -*-
"""Video de OFERTA (9:16) de um produto do catalogo — canal Pago Menos.

    python -X utf8 ferramentas/video_oferta.py --id 1005012058103385 --saida oferta.mp4

⭐ 29/09/2026 (dono): "sempre confianca, sempre". Por isso o video so' afirma o
que a serie de precos prova:
  - o "antes" e' a MEDIANA dos ultimos dias da serie (`precos_vistos.jsonl`),
    nunca o "de" que a loja inventa — e a tela diz de onde saiu;
  - o "agora" e' o instantaneo (`precos_agora.json`), com a hora da conferencia;
  - sem queda real (>= QUEDA_MIN) nao ha' video: `ValueError`.
Fotos: as oficiais do anuncio. Nunca video de terceiro (direito autoral).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
FONTES = RAIZ / "engine" / "fontes"
W, H, FPS, DUR = 1080, 1920, 30, 20.0
QUEDA_MIN = 0.25
FUNDO, OURO, OURO2, CINZA, BRANCO = (14, 13, 18), (232, 190, 84), (198, 146, 40), (150, 148, 160), (250, 248, 244)
VOZ = "pt-BR-AntonioNeural"


def fonte(nome: str, t: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTES / nome), t)


def reais(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def dados(pid: str, exigir_queda: bool = True) -> dict:
    serie = []
    for l in open(RAIZ / "estado" / "precos_vistos.jsonl", encoding="utf-8"):
        x = json.loads(l)
        if str(x["id"]) == pid:
            serie.append((x["quando"], x["preco"]))
    agora = json.load(open(RAIZ / "estado" / "precos_agora.json", encoding="utf-8"))[pid]
    hoje = agora["quando"][:10]
    antes = [p for q, p in sorted(serie) if q < hoje][-30:]
    if len(antes) < 7 and exigir_queda:
        raise ValueError(f"serie curta demais ({len(antes)} dias) — sem prova de queda")
    ref = statistics.median(antes) if antes else agora["preco"]
    queda = 1 - agora["preco"] / ref
    if queda < QUEDA_MIN and exigir_queda:
        raise ValueError(f"queda de {queda:.0%} nao justifica video")
    # ⛔ "provada" decide se o video pode dizer CAIU e mostrar o riscado. Sem
    # ela o video mostra so' o preco de hoje — nunca uma queda inventada.
    provada = len(antes) >= 7 and queda >= QUEDA_MIN
    nome = json.load(open(RAIZ / "estado" / "nomes_curtos.json", encoding="utf-8"))[pid]
    sp = datetime.fromisoformat(agora["quando"]).astimezone(timezone(timedelta(hours=-3)))
    return {"nome": nome, "agora": agora["preco"], "ref": ref, "dias": len(antes),
            "queda": queda, "hora": sp.strftime("%d/%m às %H:%M"), "imagens": agora["imagens"][:4],
            "nota": agora.get("nota"), "vendas": agora.get("vendas"),
            "marca": "PAGO MENOS", "numero": None, "provada": provada,
            "video": agora.get("video") or "", "gancho": ""}


# ⭐ 29/09/2026 (plano aprovado, ideias 5 e 10): a marca de cada canal no topo
# e a serie "ACHADO DO DIA #N" — numero por canal, contado no registro das
# ofertas feitas (nunca chutado: mesma regra do selo PARTE N).
MARCAS = {"fatura.chora": "PAGO MENOS", "achadinhos.instantaneos": "ACHADINHOS INSTANTÂNEOS",
          "achadinhototal": "ACHADINHO TOTAL"}


def proximo_numero(canal: str) -> int:
    from engine import ofertas
    return 1 + sum(1 for f in ofertas._feitas() if f.get("canal") == canal)


def vendas_curto(n: int) -> str:
    return f"{n / 1000:.1f}".replace(".0", "").replace(".", ",") + " mil" if n >= 1000 else str(n)


def legenda_post(d: dict) -> str:
    """A legenda do post no TikTok (30/09/2026).

    Mesma regra-mae do video ("sempre confianca, sempre"): so' afirma o que a
    nossa serie prova — o preco de hoje, a mediana dos nossos N dias e a loja.
    Estrutura do acervo (gancho -> prova -> oferta com chamada clara):
    afirma, nunca pergunta. Max 3 hashtags (legenda_post do motor, 28/09).
    """
    queda = round(float(d["queda"]) * 100)
    num = f" #{d['numero']}" if d.get("numero") else ""
    return (f"Achado do dia{num}: {d['nome']} caiu {queda}% 📉\n"
            f"Hoje {reais(d['agora'])} — o normal dele, nos nossos {d['dias']} dias "
            f"de acompanhamento, é {reais(d['ref'])}.\n"
            f"Loja nota {str(d['nota']).replace('.', ',')} · {vendas_curto(int(d['vendas']))} vendidos.\n"
            f"🔗 Link na bio → Achado do dia{num}\n"
            f"#achadinhos #promoção #aliexpress")


def comentario_fixado(d: dict) -> str:
    """Ideia 6: o texto que o dono cola e fixa (o TikTok nao tem API pra isso)."""
    return (f"Preço conferido em {d['hora']}: {reais(d['agora'])}. "
            f"Se mudar, eu aviso no Telegram 🔔 (link da bio)")


def baixar(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for tent in range(3):
        try:
            return Image.open(BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
        except OSError:
            if tent == 2:
                raise


def centro(d: ImageDraw.ImageDraw, y: int, txt: str, f, cor):
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, y), txt, font=f, fill=cor)
    return w


def pilula(d, x0, y0, x1, y1, cor):
    d.rounded_rectangle([x0, y0, x1, y1], (y1 - y0) // 2, fill=cor)


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def base_fundo() -> Image.Image:
    im = Image.new("RGB", (W, H), FUNDO)
    brilho = Image.new("L", (W, H), 0)
    ImageDraw.Draw(brilho).ellipse([-200, 300, W + 200, 1500], fill=38)
    brilho = brilho.filter(ImageFilter.GaussianBlur(160))
    return Image.composite(Image.new("RGB", (W, H), OURO2), im, brilho)


def cartao(foto: Image.Image, lado: int) -> Image.Image:
    c = Image.new("RGB", (lado, lado), (255, 255, 255))
    f = foto.copy()
    f.thumbnail((int(lado * 0.9), int(lado * 0.9)))
    c.paste(f, ((lado - f.width) // 2, (lado - f.height) // 2))
    return c


DEMO_S = 8.0   # ⭐ ideia 12: segundos do video OFICIAL do vendedor no cartao


def quadro(t: float, d: dict, fundo: Image.Image, cartoes: list[Image.Image],
           demo: Image.Image | None = None) -> Image.Image:
    im = fundo.copy()
    dr = ImageDraw.Draw(im)
    # topo: marca + selo de confianca
    centro(dr, 92 if d.get("numero") else 110, d.get("marca") or "PAGO MENOS",
           fonte("Poppins-Bold.ttf", 44), OURO)
    if d.get("numero"):
        centro(dr, 146, f"ACHADO DO DIA #{d['numero']}", fonte("Poppins-Bold.ttf", 26), BRANCO)
    fs = fonte("Poppins-Bold.ttf", 30)
    selo = f"preço conferido {d['hora']}"
    sw = dr.textlength(selo, font=fs) + 44          # + o visto desenhado
    x0 = (W - sw) / 2
    y0 = 200 if d.get("numero") else 180
    pilula(dr, x0 - 28, y0, x0 + sw + 28, y0 + 56, (36, 34, 44))
    dr.line([(x0 + 2, y0 + 30), (x0 + 12, y0 + 41), (x0 + 30, y0 + 16)], fill=(88, 200, 120), width=6, joint="curve")
    dr.text((x0 + 44, y0 + 6), selo, font=fs, fill=BRANCO)

    # foto: cartao branco arredondado, zoom lento, troca com fusao a cada 3 s
    lado = 820
    n = min(len(cartoes), 4)
    k = int(t // 3.2) % n
    frac = (t % 3.2) / 3.2
    z = 1.0 + 0.06 * frac
    a = cartoes[k].resize((int(lado * z),) * 2, Image.LANCZOS).crop(
        (int(lado * (z - 1) / 2),) * 2 + (int(lado * (z - 1) / 2) + lado,) * 2)
    if frac > 0.85 and n > 1:
        b = cartoes[(k + 1) % n].resize((lado, lado))
        a = Image.blend(a, b, (frac - 0.85) / 0.15)
    if demo is not None:
        a = demo          # o produto FUNCIONANDO, no lugar da foto parada
    mask = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, lado - 1, lado - 1], 48, fill=255)
    y_foto = 290
    im.paste(a, ((W - lado) // 2, y_foto), mask)

    # gancho (0-3 s): faixa ouro por cima da foto
    if t < 3.2:
        e = ease(t / 0.4) * (1 - ease((t - 2.8) / 0.4))
        fg = fonte("Anton-Regular.ttf", 120)
        if d.get("gancho"):
            txt = d["gancho"]              # problema -> solucao, AFIRMANDO
        elif d.get("provada"):
            txt = "CAIU PELA METADE" if d["queda"] >= 0.5 else f"CAIU {round(d['queda'] * 100)}%"
        else:
            txt = "ACHADO DO DIA"
        while dr.textlength(txt, font=fg) > W - 160 and fg.size > 60:
            fg = fonte("Anton-Regular.ttf", fg.size - 6)
        tw = dr.textlength(txt, font=fg)
        camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(camada)
        pilula(cd, (W - tw) / 2 - 50, 960, (W + tw) / 2 + 50, 1130, OURO + (int(255 * e),))
        cd.text(((W - tw) / 2, 968), txt, font=fg, fill=FUNDO + (int(255 * e),))
        im.paste(camada, (0, 0), camada)
        dr = ImageDraw.Draw(im)

    # nome
    fn = fonte("Poppins-Bold.ttf", 46)
    while dr.textlength(d["nome"], font=fn) > W - 100 and fn.size > 30:
        fn = fonte("Poppins-Bold.ttf", fn.size - 2)    # nome longo nao vaza da tela
    centro(dr, 1140, d["nome"], fn, BRANCO)
    # ideia 10: a confianca da LOJA, lida na API (nunca inventada)
    if d.get("nota") and d.get("vendas"):
        loja = f"loja nota {str(d['nota']).replace('.', ',')}  ·  {vendas_curto(d['vendas'])} vendidos"
        centro(dr, 1200, loja, fonte("Poppins-Bold.ttf", 30), CINZA)

    # preco (a partir de 3,5 s)
    if t >= 3.5:
        e = ease((t - 3.5) / 0.6)
        y = int(1270 + 40 * (1 - e))
        fa = fonte("Poppins-Bold.ttf", 52)
        fp = fonte("Anton-Regular.ttf", 200)
        if d.get("provada"):
            antes = f"antes {reais(d['ref'])}"
            aw = centro(dr, y, antes, fa, CINZA)
            dr.line([((W - aw) / 2, y + 36), ((W + aw) / 2, y + 36)], fill=CINZA, width=5)
            centro(dr, y + 70, reais(d["agora"]), fp, OURO)
            fb = fonte("Poppins-Bold.ttf", 44)
            badge = f"-{round(d['queda'] * 100)}%"
            bw = dr.textlength(badge, font=fb)
            bx = (W + aw) / 2 + 40
            pilula(dr, bx - 22, y - 6, bx + bw + 22, y + 60, (200, 46, 60))
            dr.text((bx, y - 2), badge, font=fb, fill=BRANCO)
            nota = f"“antes” = preço mais comum nos últimos {d['dias']} dias"
        else:
            centro(dr, y, "preço de hoje", fa, CINZA)
            centro(dr, y + 70, reais(d["agora"]), fp, OURO)
            nota = "sem desconto inventado: é o preço da loja agora"
        centro(dr, y + 330, nota, fonte("Poppins-Bold.ttf", 28), CINZA)

    # chamada final (a partir de 15 s)
    if t >= 15:
        e = ease((t - 15) / 0.5)
        fc = fonte("Poppins-Bold.ttf", 56)
        txt = "link na bio"
        tw = dr.textlength(txt, font=fc) + 60        # + a seta desenhada
        x0 = (W - tw) / 2
        y = int(1720 + 30 * (1 - e))
        pilula(dr, x0 - 50, y, x0 + tw + 50, y + 96, OURO)
        dr.text((x0, y + 12), txt, font=fc, fill=FUNDO)
        ax = x0 + tw - 22
        dr.polygon([(ax - 18, y + 38), (ax + 18, y + 38), (ax, y + 62)], fill=FUNDO)
    return im


def narracao(d: dict, destino: Path) -> None:
    import edge_tts
    from engine import numeros
    r, a = d["ref"], d["agora"]
    hoje = f"{int(a)} reais e {round((a - int(a)) * 100)} centavos"
    abre = (d["gancho"].capitalize() + ". ") if d.get("gancho") else ""
    # ⭐ 30/09/2026 (dono: "a dublagem esta' horrivel"): roteiro na ordem do
    # acervo (gancho -> prova -> oferta, FTA "How This Funnel Sold 100,000
    # Books", DEMONSTRADO), frase curta de conversa, e SO' o que a serie prova.
    # ⭐ ENTONACAO DE VENDA (dono, 30/09: "entonacao propria para vendas", +acervo).
    # Cada parte com o seu ritmo: acelerar na emocao, PAUSAR, desacelerar no
    # ponto importante (FTA Jeremy Miner, AFIRMADO); 135-185 palavras/min
    # (FTA sGakuNs9mT4); voz de IA um pouco acima de 1x soa mais natural
    # (roboverse987, DEMONSTRADO). (texto, velocidade edge-tts, pausa depois s)
    if d.get("provada"):
        queda = round(float(d["queda"]) * 100)
        partes = [(f"{abre}Olha isso! {d['nome']} caiu {queda} por cento.", "+14%", 0.25),
                  (f"Eu acompanho o preço dele há {d['dias']} dias. O normal é {int(r)} reais.", "+6%", 0.40),
                  (f"Hoje... tá {hoje}.", "-4%", 0.35),
                  ("O link tá na bio!", "+12%", 0.0)]
    else:
        partes = [(f"{abre}Olha isso! {d['nome']}.", "+14%", 0.25),
                  (f"Hoje... tá {hoje}.", "-4%", 0.35),
                  ("O link tá na bio!", "+12%", 0.0)]
    txt = " ".join(p[0] for p in partes)
    # Mesma voz dos canais de corte: edge-tts -> ChatterboxVC com o timbre da
    # amostra (motor D do engine/voz_clonada), uma parte por vez. Sem amostra ou
    # sem o modelo, volta pra voz simples — video sem voz nao sai.
    amostra = Path(os.environ.get("AMOSTRA_VOZ_OFERTA") or "vozes/bryan_amostra.wav")
    if amostra.exists():
        from engine import voz_clonada
        pedacos, ok = [], True
        for k, (frase, vel, pausa) in enumerate(partes):
            wav = destino.with_name(f"parte{k}.wav")
            if not voz_clonada._falar_d(frase, wav, amostra, vel):
                ok = False
                break
            pedacos.append((wav, pausa))
        if ok:
            lista = destino.with_name("partes.txt")
            linhas = []
            for k, (wav, pausa) in enumerate(pedacos):
                linhas.append(f"file '{wav.as_posix()}'")
                if pausa:
                    sil = destino.with_name(f"sil{k}.wav")
                    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                                    "anullsrc=r=24000:cl=mono", "-t", str(pausa), str(sil)], check=True)
                    linhas.append(f"file '{sil.as_posix()}'")
            lista.write_text("\n".join(linhas), encoding="utf-8")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                            "-ar", "24000", "-ac", "1",
                            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", str(destino)], check=True)
            return
        print("  [!] voz clonada falhou — uso a voz simples", flush=True)
    asyncio.run(edge_tts.Communicate(numeros.por_extenso(txt), voice=VOZ, rate="+4%").save(str(destino)))


def _leitor_demo(url: str, tmp: Path):
    """Quadros 820x820 do video do vendedor (os DEMO_S primeiros segundos)."""
    if Path(url).exists():             # trecho ja' baixado (ex.: demo_youtube)
        arq = Path(url)
    else:
        arq = tmp / "demo.mp4"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        arq.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    lado = 820
    # a maioria dos videos de vendedor abre com 1-2 s de logo: pula quando da'
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True)
    try:
        dur = float(r.stdout.strip())
    except ValueError:
        dur = 0.0
    pulo = "3" if dur >= DEMO_S + 4 else "0"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", pulo, "-i", str(arq), "-t", str(DEMO_S), "-an",
                          "-vf", f"fps={FPS},scale={lado}:{lado}:force_original_aspect_ratio=increase,"
                                 f"crop={lado}:{lado}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    ultimo = None
    while True:
        b = p.stdout.read(lado * lado * 3)
        if len(b) < lado * lado * 3:
            break
        ultimo = Image.frombytes("RGB", (lado, lado), b)
        yield ultimo
    while True:               # video curto: segura o ultimo quadro
        yield ultimo


def gerar(pid: str, saida: Path, canal: str | None = None, numero: int | None = None,
          exigir_queda: bool = True, gancho: str = "", demo_arquivo: Path | None = None) -> dict:
    d = dados(pid, exigir_queda)
    d["gancho"] = gancho.upper()
    if demo_arquivo and Path(demo_arquivo).exists():
        d["video"] = str(demo_arquivo)
    elif not d.get("video"):
        # ⭐ item 16 (30/09/2026): trecho de demo que o PC tirou do YouTube,
        # conferido pelo Gemini contra a foto do anuncio (mesmo_produto >= 9),
        # e subiu pro Drive. Ver ferramentas/demo_local.py.
        demos = RAIZ / "estado" / "demos_drive.json"
        if demos.exists():
            reg = json.loads(demos.read_text(encoding="utf-8")).get(str(pid))
            if reg:
                d["video"] = reg["link"]
    if canal:
        d["marca"] = MARCAS.get(canal, d["marca"])
        d["numero"] = numero or proximo_numero(canal)
    tmp = Path(tempfile.mkdtemp())
    cartoes = [cartao(baixar(u), 820) for u in d["imagens"]]
    voz = tmp / "voz.mp3"
    narracao(d, voz)
    fundo = base_fundo()
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(voz),
                          "-filter_complex", "[1:a]adelay=600|600,apad[a]", "-map", "0:v", "-map", "[a]",
                          "-t", str(DUR), "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                          "-movflags", "+faststart", str(saida)], stdin=subprocess.PIPE)
    demo = None
    if d.get("video"):
        try:
            demo = _leitor_demo(d["video"], tmp)
            primeiro = next(demo)
            if primeiro is None:
                demo = None
        except Exception as e:  # noqa: BLE001 — sem demo, volta pra foto
            print(f"  [!] video do vendedor indisponivel ({type(e).__name__}); uso as fotos")
            demo = None
    for i in range(int(DUR * FPS)):
        t = i / FPS
        dq = next(demo) if (demo is not None and t < DEMO_S) else None
        p.stdin.write(quadro(t, d, fundo, cartoes, dq).tobytes())
    p.stdin.close()
    p.wait()
    d["comentario"] = comentario_fixado(d)
    d["legenda"] = legenda_post(d)
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--saida", type=Path, required=True)
    ap.add_argument("--canal")
    ap.add_argument("--sem-queda", action="store_true", help="mostra so' o preco de hoje")
    ap.add_argument("--gancho", default="")
    ap.add_argument("--demo", type=Path, help="trecho de demonstracao ja' baixado")
    a = ap.parse_args()
    print(gerar(a.id, a.saida, a.canal, exigir_queda=not a.sem_queda, gancho=a.gancho,
                demo_arquivo=a.demo))
