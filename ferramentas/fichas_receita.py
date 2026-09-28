# -*- coding: utf-8 -*-
"""FICHAS DE RECEITA do Achadinho Chef (modelo C5 "caramelo", aprovado 28/09/2026).

    python -X utf8 ferramentas/fichas_receita.py --previa saida/   # grava os HTML

Le' o manifesto (clipes da cozinha com receita escrita na legenda), monta uma
ficha por receita e a lista das ultimas N para o bloco "Ultimas receitas" da
bio (paginas/contra_capa.html, `var RECEITAS`). O publicar_bio sobe as fichas
em `/receitas/<slug>/` no mesmo deploy das bios.

⛔ NADA INVENTADO: so' entra o que esta' na receita do video. Sem "ponto
critico", custo ou proteina quando a fala nao disse (o prototipo tinha um
"ponto critico" escrito a mao — nao vale para a versao automatica).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

CANAL = "cozinha.importada"
N_BIO = 3
FOTOS = RAIZ / "paginas" / "receitas_fotos"
DOMINIO = "chef.achadinhototal.com.br"

# a receita_texto sai sem acento (engine/receita_texto.py); conserto das
# palavras que mais aparecem — so' troca palavra INTEIRA
ACENTOS = {
    "porcoes": "porções", "porcao": "porção", "ate": "até", "medio": "médio",
    "media": "média", "parmesao": "parmesão", "consistencia": "consistência",
    "alcool": "álcool", "deglacar": "deglaçar", "acucar": "açúcar",
    "limao": "limão", "feijao": "feijão", "pure": "purê", "file": "filé",
    "oregano": "orégano", "agua": "água", "oleo": "óleo", "mao": "mão",
    "voce": "você", "tambem": "também", "tempero": "tempero", "po": "pó",
    "cafe": "café", "creme de leite": "creme de leite", "graos": "grãos",
    "pimentao": "pimentão", "salmao": "salmão", "camarao": "camarão",
    "macarrao": "macarrão", "requeijao": "requeijão", "calda": "calda",
    "minutos": "minutos", "gratinado": "gratinado", "facil": "fácil",
    "rapido": "rápido", "proteina": "proteína", "cha": "chá",
}


def acentuar(t: str) -> str:
    def _f(m):
        w = m.group(0)
        a = ACENTOS.get(w.lower())
        if not a:
            return w
        return a.capitalize() if w[0].isupper() else a
    return re.sub(r"[A-Za-z]+", _f, t or "")


def slug(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def ler_receita(legenda: str, titulo: str) -> dict | None:
    """Separa a legenda do modo receita em blocos. None = nao tem receita."""
    if "INGREDIENTES" not in (legenda or ""):
        return None
    txt = legenda.replace("\r", "")
    antes, _, resto = txt.partition("INGREDIENTES")
    ing_txt, _, resto = resto.partition("MODO DE PREPARO")
    prep_txt, _, resto = resto.partition("SUBSTITUICOES")
    subs_txt = re.split(r"\n\s*#", resto)[0]
    prep_txt = re.split(r"\n\s*#", prep_txt)[0]
    ing = [l.strip(" -•\t") for l in ing_txt.splitlines() if l.strip(" -•\t")]
    passos = [re.sub(r"^\d+[.)]\s*", "", l.strip()) for l in prep_txt.splitlines()
              if re.match(r"^\s*\d+[.)]", l)]
    subs = [l.strip(" -•\t") for l in subs_txt.splitlines() if l.strip(" -•\t")]
    blocos = [b.strip() for b in antes.split("\n\n") if b.strip()]
    sub = blocos[1] if len(blocos) > 1 and blocos[0] == titulo.strip() else ""
    m = re.search(r"Rende\s+(\d+)\s+por[cç]\w*\s*[-·]\s*([^\n]+)", antes, re.I)
    rende = m.group(1) if m else ""
    # "Rende 1 travessa média - 6 h 30 min": sem porções, mas o tempo vale
    t = m or re.search(r"Rende\s+[^\n]*?\s[-·]\s*(\d[^\n]*)", antes, re.I)
    tempo = t.group(t.lastindex).strip() if t else ""
    if not ing or not passos:
        return None
    return {"titulo": titulo.strip(), "sub": acentuar(sub.split(". ")[0].rstrip(".")),
            "rende": rende, "tempo": acentuar(tempo),
            "ing": [acentuar(i) for i in ing], "passos": [acentuar(p) for p in passos],
            "subs": [acentuar(s).replace("->", "→") for s in subs]}


def _qtd(item: str) -> tuple[str, str]:
    """'240 ml de xerez seco' -> ('240 ml', 'xerez seco'); 'Sal a gosto' -> ('a gosto','Sal')."""
    m = re.match(r"^([\d.,/½¼¾]+\s*(?:kg|g|mg|ml|l|litros?|colheres? de (?:sopa|chá|cha)|"
                 r"xícaras?|xicaras?|unidades?|dentes?|fatias?|latas?|pitadas?)?)\s+(?:de\s+)?(.+)$",
                 item, re.I)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if re.search(r"a gosto", item, re.I):
        nome = re.sub(r"\s*a gosto\s*", " ", item, flags=re.I).strip()
        return "a gosto", nome
    return "", item


CSS = """*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#FAF6EF;--sup:#fff;--txt:#2A211B;--sec:rgba(42,33,27,.66);--linha:#EAE1D3;--pop:#C98A2E;--popesc:#9A6414}
body{max-width:480px;margin:0 auto;background:var(--bg);color:var(--txt);font-family:Inter,system-ui,sans-serif}
.head{padding:22px 20px 0;display:flex;justify-content:space-between;font-size:11px;letter-spacing:.14em;font-weight:800;color:var(--sec)}
.head a{color:var(--sec);text-decoration:none}.head span{color:var(--popesc)}
h1{font-family:Fraunces,Georgia,serif;font-size:34px;line-height:1.02;padding:10px 20px 0}
.sub{padding:6px 20px 0;color:var(--sec)}
.foto{margin:18px 20px 0;aspect-ratio:4/3;border-radius:18px;background:#e9dfcf center/cover;position:relative;overflow:hidden}
.foto:before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 55%,rgba(0,0,0,.45))}
.foto span{position:absolute;z-index:1;left:12px;bottom:12px;background:var(--pop);color:#fff;font-weight:800;font-size:11px;letter-spacing:.1em;padding:6px 10px;border-radius:8px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:16px 20px 0}
.cel{background:var(--sup);border-radius:14px;padding:12px 10px;box-shadow:0 1px 0 rgba(42,33,27,.06),0 6px 18px rgba(42,33,27,.05)}
.cel b{display:block;font-family:Fraunces,Georgia,serif;font-size:22px;color:var(--popesc)}
.cel small{font-size:10px;letter-spacing:.1em;color:var(--sec);text-transform:uppercase}
.t{padding:22px 20px 8px;font-size:11px;letter-spacing:.16em;font-weight:800;color:var(--sec)}
.lin{display:grid;grid-template-columns:22px 118px 1fr;gap:10px;align-items:center;padding:9px 20px;border-top:1px solid var(--linha);font-size:15px;cursor:pointer}
.lin b{color:var(--popesc);font-size:14px}
.lin input{appearance:none;width:18px;height:18px;border:2px solid var(--pop);border-radius:5px;margin:0}
.lin input:checked{background:var(--pop)}.lin input:checked~span{text-decoration:line-through;opacity:.55}
.p{display:grid;grid-template-columns:44px 1fr;padding:10px 20px;border-top:1px solid var(--linha);font-size:15px;line-height:1.45}
.p b{font-family:Fraunces,Georgia,serif;font-size:26px;line-height:1;color:rgba(201,138,46,.6)}
.box{margin:18px 20px 0;border-left:5px solid #8A7B6A;background:#EFE7DA;border-radius:14px;padding:12px 14px;font-size:14px;line-height:1.45}
.box b{display:block;font-size:11px;letter-spacing:.12em;margin-bottom:4px;color:#6B5D4F}
.col{display:block;margin:22px 20px 0;border-radius:16px;padding:16px;background:var(--popesc);color:#fff;text-align:center;text-decoration:none;box-shadow:0 10px 26px rgba(201,138,46,.25)}
.col b{display:block;font-family:Fraunces,Georgia,serif;font-size:20px}.col span{font-size:13px;opacity:.9}
.pe{padding:22px 20px 30px;font-size:12px;color:var(--sec);line-height:1.6}
.et{padding:16px 20px 6px;font-family:Fraunces,Georgia,serif;font-size:17px;color:var(--popesc)}
@media print{.col{display:none}body{background:#fff}}"""

FONTES = ('<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;'
          '9..144,800&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">')


def ficha_html(r: dict, numero: int, total: int, capa: str, credito: str) -> str:
    e = html.escape
    lin = "".join(
        f'<label class="lin"><input type="checkbox"><b>{e(q) or "—"}</b><span>{e(n)}</span></label>'
        for q, n in ((q, n[:1].lower() + n[1:]) for q, n in (_qtd(i) for i in r["ing"])))
    pas, k = "", 0
    for nome, passos in r.get("etapas") or [("", r["passos"])]:
        if nome and len(r.get("etapas") or []) > 1:
            pas += f'<div class="et">{e(nome)}</div>'
        for t in passos:
            k += 1
            pas += f'<div class="p"><b>{k:02d}</b><span>{e(t)}</span></div>'
    cel = "".join(f'<div class="cel"><b>{e(v)}</b><small>{e(l)}</small></div>'
                  for v, l in ((r["rende"], "porções"), (r["tempo"], "tempo"),
                               (str(len(r["ing"])), "ingredientes")) if v)
    subs = "".join(f'<div class="box"><b>SUBSTITUIÇÃO</b>{e(s)}</div>' for s in r["subs"])
    foto = f' style="background-image:url(\'{e(capa)}\')"' if capa else ""
    sub = f'<p class="sub">{e(r["sub"])}</p>' if r["sub"] else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(r['titulo'])} · Achadinho Chef</title>
<meta name="description" content="{e(r['titulo'])} — receita em grama, ml e °C.">
{FONTES}<style>{CSS}</style></head><body>
<div class="head"><a href="/">ACHADINHO CHEF · FICHA</a><span>Nº {numero:03d}</span></div>
<h1>{e(r['titulo'])}</h1>{sub}
<div class="foto"{foto}><span>GRAMA · ML · °C</span></div>
<div class="grid">{cel}</div>
<div class="t">INGREDIENTES · marque ao separar</div>{lin}
<div class="t">PREPARO</div>{pas}{subs}
<a class="col" href="/"><b>Esta é a ficha {numero} de {total}</b><span>Receba as próximas no e-mail · {DOMINIO}</span></a>
<div class="pe">{e(credito)}</div></body></html>"""


def _credito(fonte: str) -> str:
    # o nome do canal nao vem no arquivo com seguranca ("No-Bake Dessert" nao
    # e' canal): credita com o LINK do video original, que e' verificavel.
    vid = (fonte or "").split("__", 1)[0]
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        return f"Receita adaptada do vídeo original: youtube.com/watch?v={vid}"
    return "Receita adaptada de um vídeo do YouTube"


def _chave_ing(item: str) -> str:
    """Nome do ingrediente sem quantidade/"a gosto"/plural, p/ juntar repetidos."""
    _, nome = _qtd(item)
    nome = re.sub(r"\(.*?\)|\ba gosto\b|:", " ", nome.lower())
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    return " ".join(re.sub(r"s$", "", w) for w in re.findall(r"[a-z]+", nome))


def _juntar(partes: list[dict]) -> dict:
    """1 video = 1 receita = 1 ficha (dono, 28/09: "o tiramisu tudo em uma
    ficha so'"). As partes vem em ordem do video (inicio_s); a 1a da' o
    titulo/subtitulo/porcoes. Ingrediente repetido entra 1 vez, preferindo o
    que tem quantidade. O preparo guarda os passos de cada parte, na ordem."""
    base = dict(partes[0])
    if len(partes) == 1:
        base["etapas"] = [("", base["passos"])]
        return base
    ing, vistos = [], {}
    for r in partes:
        for i in r["ing"]:
            k = _chave_ing(i)
            if k in vistos:
                if not _qtd(ing[vistos[k]])[0] and _qtd(i)[0]:
                    ing[vistos[k]] = i
                continue
            vistos[k] = len(ing)
            ing.append(i)
    base["ing"] = ing
    base["etapas"] = [(r["titulo"], r["passos"]) for r in partes]
    base["passos"] = [p for r in partes for p in r["passos"]]
    base["subs"] = list(dict.fromkeys(s for r in partes for s in r["subs"]))
    # o tempo da receita e' o da parte mais longa (a do mascarpone inclui
    # 6 h de geladeira: "15 min" da 1a parte enganaria quem vai fazer)
    def _min(t):
        h = re.search(r"(\d+)\s*h", t or "")
        m = re.search(r"(\d+)\s*min", t or "")
        return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)
    base["tempo"] = max((r["tempo"] for r in partes), key=_min, default="")
    return base


ORDEM = RAIZ / "paginas" / "receitas_ordem.json"


def _numerar(itens: list[dict]) -> None:
    """Numero FIXO por receita, na ordem em que foi PUBLICADA (dono, 28/09: a
    cebola saiu Nº 004 sendo o 1o post). Guardado em paginas/receitas_ordem.json
    (versionado): uma vez dado, o numero nunca muda; receita nova pega o proximo."""
    try:
        ordem = json.loads(ORDEM.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        ordem = {}
    for r in itens:
        if r["vid"] not in ordem:
            ordem[r["vid"]] = max(ordem.values(), default=0) + 1
        r["numero"] = ordem[r["vid"]]
    try:
        ORDEM.write_text(json.dumps(ordem, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    itens.sort(key=lambda r: r["numero"])


def coletar(manifesto: dict | None = None) -> list[dict]:
    """Receitas do Chef (1 por video de origem), da mais antiga para a mais nova."""
    if manifesto is None:
        import agendar_buffer as ab
        manifesto = ab.manifesto(ab._token_github(), None)
    from engine import canais_registro
    grupos: dict[str, list[dict]] = {}
    for k, v in sorted(manifesto.items()):
        can = canais_registro.canonico(v.get("canal") or v.get("canal_esperado") or "")
        if can != CANAL and "INGREDIENTES" not in str(v.get("legenda") or ""):
            continue
        if v.get("quarentena") or v.get("nao_publicar"):
            continue   # nao foi ao ar: nao ganha ficha
        r = ler_receita(str(v.get("legenda") or ""), str(v.get("titulo") or ""))
        if not r:
            continue
        fonte = v.get("fonte") or ""
        vid = fonte.split("__", 1)[0] or k
        r.update(credito=_credito(fonte), chave=k, fonte=fonte, vid=vid,
                 capa=v.get("capa_url") or "", ini=float(v.get("inicio_s") or 0),
                 fim=float(v.get("fim_s") or 0) or None)
        grupos.setdefault(vid, []).append(r)
    itens = []
    for partes in grupos.values():
        r = _juntar(sorted(partes, key=lambda x: x["ini"]))
        r["slug"] = slug(r["titulo"])
        itens.append(r)
    _numerar(itens)
    return itens


def foto_do_prato(fonte: str, ini: float, fim: float) -> bytes | None:
    """Foto LIMPA do prato, do BRUTO (sem baloes/aviao/legenda do publicado).
    O bruto vai pra lixeira do Drive depois do corte, mas a API ainda baixa.
    Falha aberta: None (a ficha usa a capa do manifesto)."""
    import shutil
    import tempfile
    try:
        import contas_drive
        from googleapiclient.http import MediaIoBaseDownload
        from engine import capa_prato
        d = contas_drive.servico(contas_drive.conta_por_nome("reserva"))
        nome = fonte.replace("'", "\'")
        fs = d.files().list(q=f"name = '{nome}'", fields="files(id,size)",
                            includeItemsFromAllDrives=False).execute().get("files", [])
        if not fs:
            return None
        tmp = Path(tempfile.mkdtemp())
        v = tmp / "b.mp4"
        with open(v, "wb") as fh:
            dl = MediaIoBaseDownload(fh, d.files().get_media(fileId=fs[0]["id"]))
            feito = False
            while not feito:
                _, feito = dl.next_chunk()
        jpg = capa_prato.escolher(v, ini, fim)
        shutil.rmtree(tmp, ignore_errors=True)   # PC com pouco disco
        return jpg
    except Exception as e:  # noqa: BLE001
        print(f"  [!] foto do prato falhou ({type(e).__name__}: {str(e)[:80]})")
        return None


def gerar(manifesto: dict | None = None, fotos: bool = True) -> tuple[dict, list[dict]]:
    """({caminho relativo: html|bytes}, lista p/ a bio com as N mais recentes)."""
    itens = coletar(manifesto)
    total = max(30, len(itens))
    arquivos = {}
    for r in itens:
        n = r["numero"]
        # foto guardada no repo depois da 1a vez: nao rebaixa o bruto a cada
        # publicacao da bio (rede instavel + PC com pouco disco, 28/09)
        guardada = FOTOS / f"{r['slug']}.jpg"
        jpg = guardada.read_bytes() if guardada.exists() else None
        for _ in range(3 if (fotos and not jpg and r.get("fonte")) else 0):
            jpg = foto_do_prato(r["fonte"], r["ini"], r["fim"])
            if jpg:
                FOTOS.mkdir(parents=True, exist_ok=True)
                guardada.write_bytes(jpg)
                break
        if jpg:
            if True:
                arquivos[f"receitas/{r['slug']}/prato.jpg"] = jpg
                r["capa"] = f"/receitas/{r['slug']}/prato.jpg"
        arquivos[f"receitas/{r['slug']}/index.html"] = ficha_html(r, n, total, r["capa"], r["credito"])
    bio = [{"titulo": r["titulo"], "url": f"/receitas/{r['slug']}/", "capa": r["capa"],
            "rende": r["rende"], "tempo": r["tempo"], "numero": r["numero"]}
           for r in reversed(itens[-N_BIO:])]
    return arquivos, bio


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--previa", type=Path, help="pasta onde gravar os HTML")
    a = ap.parse_args()
    arquivos, bio = gerar()
    print(f"{len(arquivos)} ficha(s); bio: {json.dumps(bio, ensure_ascii=False)[:400]}")
    if a.previa:
        for rel, corpo in arquivos.items():
            f = a.previa / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            (f.write_bytes(corpo) if isinstance(corpo, bytes)
             else f.write_text(corpo, encoding="utf-8"))
        (a.previa / "receitas_bio.json").write_text(json.dumps(bio, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
