# -*- coding: utf-8 -*-
"""FICHA DA SEMANA Nº N — o brinde colecionavel de cada canal (03/10/2026).

⭐ Dono: "A e B!!! crie de maneira extraordinaria, premium e organizada".
Engenharia reversa das capas teen (_privado/capricho/): o POSTER era o brinde
de 75 de 155 capas e subiu de 49% para 77% das capas entre 2000 e 2010. A
versao que conseguimos produzir TODA semana, sem problema de imagem de idol,
e' uma ficha editorial NUMERADA (Nº 1, Nº 2...) — o numero cria a colecao
(acervo: colecionavel/edicao limitada reengaja).

De onde vem o conteudo: SO' dos clipes que o canal publicou na semana
(manifesto). O Gemini ORGANIZA; nao inventa — a regra vai no prompt e o
`conferir()` recusa ficha com nome que nao esta' nas legendas.

    python -X utf8 ferramentas/ficha_semana.py --canal truque.importado     # previa
    python -X utf8 ferramentas/ficha_semana.py --todos                     # previas
    python -X utf8 ferramentas/ficha_semana.py --canal X --gravar          # avanca o Nº

Saida: _privado/previas/fichas/<canal>_N<numero>.html (pagina pronta para
celular e para imprimir/salvar em PDF). Nada e' publicado nem enviado daqui.
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SAIDA = RAIZ / "_privado" / "previas" / "fichas"
ESTADO = RAIZ / "estado" / "fichas_semana.json"
DIAS = 7

CANAIS = {
    "truque.importado": {
        "logo": "Achadinho Make",
        "marca": "ACHADINHO MAKE", "arroba": "@achadinho.make", "cor": "#D6336C",
        "fundo": "#FFF4F8", "ficha": "Make da Semana",
        "foco": "as makes das idols da semana: para cada uma, o PASSO A PASSO e o "
                "que ela usou (produto pelo que ele E', sem marca)",
        "secao": "A make", "itens": "Passo a passo", "extra": "O que foi usado",
    },
    "camarim.kpop": {
        "logo": "Camarim K-pop",
        "marca": "CAMARIM K-POP", "arroba": "@camarim.kpop", "cor": "#7B2FF7",
        "fundo": "#F6F0FF", "ficha": "Photocard da Semana",
        "foco": "os bastidores da semana: para cada idol, o momento, o que ele/ela "
                "disse e por que os fas amaram",
        "secao": "Bastidor", "itens": "O que rolou", "extra": "Para guardar",
    },
    "cozinha.importada": {
        "logo": "Achadinho Chef",
        "marca": "ACHADINHO CHEF", "arroba": "@achadinhochef", "cor": "#1F8A5F",
        "fundo": "#F1FAF5", "ficha": "Cardápio da Semana",
        "foco": "as receitas da semana: ingredientes JA em grama/ml/°C e o modo de "
                "preparo curto, como cardapio para a semana",
        "secao": "Receita", "itens": "Modo de preparo", "extra": "Ingredientes",
    },
    "semanestesia.pod": {
        "logo": "Sem Anestesia",
        "marca": "SEM ANESTESIA", "arroba": "@semanestesia.pod", "cor": "#D92B2B",
        "fundo": "#FFF3F2", "ficha": "Rotina da Semana",
        "foco": "as ideias da semana viradas em PROTOCOLO pratico: a ideia, quem "
                "disse, e as acoes concretas em checklist",
        "secao": "Protocolo", "itens": "Checklist", "extra": "Por que funciona",
    },
    "modofuturo": {
        "logo": "Modo Futuro",
        "marca": "MODO FUTURO", "arroba": "@modofuturo", "cor": "#1B5BFF",
        "fundo": "#F1F5FF", "ficha": "O Que Vem Aí",
        "foco": "as historias de tecnologia da semana: o fato, os numeros que a "
                "fala citou e o que observar daqui pra frente",
        "secao": "Historia", "itens": "Os fatos", "extra": "O que observar",
    },
    "atefalhar": {
        "logo": "Geração 2000",
        "marca": "GERACAO 2000", "arroba": "@atefalhar", "cor": "#E36414",
        "fundo": "#FFF6EE", "ficha": "Hora do Recreio",
        "foco": "as revelacoes da semana sobre os desenhos dos anos 2000: o "
                "segredo, a prova e o detalhe que ninguem viu quando crianca",
        "secao": "Revelacao", "itens": "A prova", "extra": "Voce reparou?",
    },
}

PROMPT = """Voce e' editor de uma revista teen brasileira (escola Capricho) e vai
montar "{ficha}" Nº {numero} do canal {marca}, usando SO' as legendas dos
videos da semana abaixo. Foco: {foco}.

REGRAS DURAS:
- NAO invente nada: nome, numero, produto, passo ou fala que nao estejam nas
  legendas ficam de fora. Na duvida, deixe de fora.
- Portugues do Brasil, leve e caprichado, como revista. Nomes como estao.
- Use {n_min} a {n_max} secoes (uma por video forte; junte repetidos).
- NAO use a palavra "ficha" e NAO repita "Nº" na capa (o numero ja' aparece no selo).
- Manchete de capa: nome em destaque + gatilho (SEGREDO, REVELA, DESCUBRA,
  ESPECIAL, INFALIVEL). NUMERO so' se for uma QUANTIDADE real das legendas
  ("3 passos", "14 dias"); nunca um numero solto no comeco ("19 SEGREDO" e
  "1 DESCUBRA" sairam errados em 03/10). Frase com sentido, de 3 a 7 palavras.
- No Camarim, cada secao e' UM idol pelo nome (nao o grupo inteiro).
- Itens COMPLETOS: nenhuma frase cortada no meio.

Responda SO' JSON, neste formato:
{{"capa": "chamada principal, ate' 60 caracteres",
  "subtitulo": "1 frase que vende a edicao, ate' 110 caracteres",
  "selo": "texto do selo estourado da capa, 2 a 4 palavras com exclamacao (ex: EXCLUSIVO!, 3 MAKES NOVAS!)",
  "secoes": [{{"nome": "nome em destaque (idol, prato, pessoa, empresa ou desenho)",
              "titulo": "chamada curta da secao, ate' 55 caracteres",
              "resumo": "1 a 2 frases",
              "itens": ["3 a 6 itens curtos de {itens}"],
              "extra": ["0 a 4 itens curtos de {extra}"]}}],
  "teste": {{"pergunta": "pergunta-TESTE sobre a propria leitora, ate' 70 caracteres",
             "opcoes": ["texto da opcao, sem letra na frente", "...", "..."]}},
  "proxima": "1 frase de gancho para a proxima ficha, sem prometer data"}}

Legendas da semana:
{legendas}"""


def numero_atual(canal: str) -> int:
    try:
        return int(json.loads(ESTADO.read_text(encoding="utf-8")).get(canal, 0)) + 1
    except Exception:  # noqa: BLE001
        return 1


def gravar_numero(canal: str, n: int) -> None:
    try:
        e = json.loads(ESTADO.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        e = {}
    e[canal] = n
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def clipes(canal: str, dias: int = DIAS) -> list[dict]:
    import agendar_buffer as ab
    man = ab.manifesto(ab._token_github(), None)
    desde = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    out = []
    for _, v in sorted(man.items(), reverse=True):
        if v.get("canal") != canal or v.get("quarentena") or v.get("nao_publicar"):
            continue
        if str(v.get("publicado_em") or "")[:10] < desde:
            continue
        if (v.get("titulo") or "").strip() and (v.get("legenda") or "").strip():
            out.append(v)
    return out


def _json(r: str | None) -> dict | None:
    if not r:
        return None
    m = re.search(r"\{.*\}", r, re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:  # noqa: BLE001
        return None


def conferir(d: dict, fonte: str) -> list[str]:
    """Nomes de secao que NAO aparecem nas legendas = inventados."""
    f = fonte.lower()
    ruins = []
    for s in d.get("secoes") or []:
        nome = (s.get("nome") or "").strip()
        palavras = [p for p in re.findall(r"[\wÀ-ú.]+", nome.lower()) if len(p) > 2]
        if palavras and not any(p in f for p in palavras):
            ruins.append(nome)
    return ruins


def montar_dados(canal: str, numero: int) -> dict | None:
    from engine import modelo_texto
    cfg = CANAIS[canal]
    cs = clipes(canal)
    if len(cs) < 2:
        print(f"  {canal}: so' {len(cs)} clipe(s) na semana — ficha nao sai")
        return None
    legendas = "\n\n".join(f"- {c['titulo']}\n{c['legenda'][:900]}" for c in cs[:10])
    p = PROMPT.format(numero=numero, n_min=min(3, len(cs)), n_max=min(5, len(cs)),
                      legendas=legendas, **{k: cfg[k] for k in ("ficha", "marca", "foco", "itens", "extra")})
    for _ in range(2):
        # 03/10: 3 tentativas caiam na reserva (OpenRouter) que pendurava; Gemini primeiro
        d = _json(modelo_texto.perguntar(p, tentativas=12))
        if not d or not d.get("secoes"):
            continue
        ruins = conferir(d, legendas)
        if ruins:
            print(f"  {canal}: secao com nome fora das legendas {ruins} — refazendo")
            continue
        d["_clipes"] = len(cs)
        return d
    print(f"  {canal}: o modelo nao entregou ficha confiavel")
    return None


CSS = """
:root{--cor:%(cor)s;--fundo:%(fundo)s;--tinta:#17141d;--suave:#5b5666;--linha:#ece7f0}
*{box-sizing:border-box;margin:0}
html{background:#fff;color-scheme:light only}
body{background:#fff;color:var(--tinta);font:16px/1.6 Inter,system-ui,sans-serif;
  -webkit-font-smoothing:antialiased}
.folha{max-width:760px;margin:0 auto;padding:clamp(20px,5vw,48px) clamp(16px,5vw,40px) 56px}
.topo{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;
  padding-bottom:14px;border-bottom:3px solid var(--tinta)}
.marca{font:800 13px/1 Inter,sans-serif;letter-spacing:.32em;color:var(--cor)}
.selo{font:700 12px/1 Inter,sans-serif;letter-spacing:.12em;text-transform:uppercase;
  border:2px solid var(--tinta);border-radius:999px;padding:8px 14px;white-space:nowrap}
.capa{position:relative;margin:28px 0 8px;padding:clamp(24px,5vw,40px);background:var(--fundo);
  border-radius:28px;overflow:hidden}
.capa::after{content:"Nº %(numero)s";position:absolute;right:-6px;bottom:-34px;
  font:900 clamp(110px,24vw,190px)/1 Fraunces,Georgia,serif;color:var(--cor);opacity:.12}
.ficha{font:700 14px/1 Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--cor)}
h1{margin:14px 0 12px;font:900 clamp(34px,7vw,56px)/1.02 Fraunces,Georgia,serif;
  letter-spacing:-.02em;text-wrap:balance;max-width:16ch;position:relative;z-index:1}
.sub{font-size:clamp(17px,2.6vw,19px);color:var(--suave);max-width:46ch;position:relative;z-index:1}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px;position:relative;z-index:1}
.meta span{background:#fff;border-radius:999px;padding:7px 13px;font:600 13px/1 Inter,sans-serif}
.indice{margin:30px 0 6px;font:800 12px/1 Inter,sans-serif;letter-spacing:.24em;color:var(--suave)}
.secao{display:grid;grid-template-columns:auto 1fr;gap:4px 18px;padding:26px 0;
  border-bottom:1px solid var(--linha);break-inside:avoid}
.num{grid-row:span 4;font:900 44px/1 Fraunces,Georgia,serif;color:var(--cor);min-width:1.4ch}
.nome{font:800 12px/1.2 Inter,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--cor)}
h2{font:800 clamp(22px,4vw,27px)/1.18 Fraunces,Georgia,serif;text-wrap:balance}
.resumo{color:var(--suave)}
.colunas{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin-top:10px}
.bloco{background:#fff;border:1.5px solid var(--linha);border-radius:18px;padding:16px 18px}
.bloco b{display:block;font:800 12px/1 Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;
  margin-bottom:10px}
ol,ul{padding-left:1.15em;display:grid;gap:6px}
li::marker{color:var(--cor);font-weight:800}
.teste{margin:34px 0 0;padding:clamp(22px,4vw,32px);border-radius:28px;background:var(--tinta);color:#fff}
.teste .ficha{color:#fff;opacity:.75}
.teste h3{margin:10px 0 16px;font:800 clamp(22px,4vw,28px)/1.2 Fraunces,Georgia,serif;text-wrap:balance}
.opcoes{display:grid;gap:10px}
.opcoes span{display:flex;gap:12px;align-items:center;background:rgba(255,255,255,.1);
  border-radius:14px;padding:13px 16px;font-weight:600}
.opcoes i{font:800 14px/1 Inter,sans-serif;font-style:normal;background:var(--cor);color:#fff;
  width:28px;height:28px;border-radius:50%%;display:grid;place-items:center;flex:none}
.teste p{margin-top:16px;opacity:.8;font-size:15px}
.proxima{margin-top:28px;text-align:center;font:italic 600 18px/1.5 Fraunces,Georgia,serif;color:var(--suave)}
.rodape{margin-top:26px;padding-top:16px;border-top:1px solid var(--linha);display:flex;
  justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:13px;color:var(--suave)}
.rodape a{color:var(--cor);font-weight:700;text-decoration:none}
@page{size:A4;margin:14mm}
.baixar{margin:30px 0 0;padding:24px;border:2px dashed var(--cor);border-radius:24px;text-align:center}
.baixar h3{font:800 22px/1.2 Fraunces,Georgia,serif;margin-bottom:6px}
.baixar p{color:var(--suave);font-size:15px}
.btn{display:inline-block;margin-top:14px;background:var(--cor);color:#fff;border:0;cursor:pointer;
  font:800 16px/1 Inter,sans-serif;padding:16px 26px;border-radius:999px;text-decoration:none}
.btn:focus-visible{outline:3px solid var(--tinta);outline-offset:3px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-top:16px}
.cards a{display:block;border-radius:14px;overflow:hidden;box-shadow:0 8px 20px -12px rgba(0,0,0,.4)}
.cards img{display:block;width:100%%;height:auto}
@media print{.folha{padding:0}.baixar{display:none}.capa,.teste{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


def _baixar(canal: str, numero: int, cards: list[str] | None) -> str:
    """O botao BAIXAR (03/10/2026, dono): photocards em PNG no Camarim; PDF nos outros."""
    if cards:
        e = html.escape
        miniaturas = "".join(f'<a href="{e(c)}" download><img src="{e(c)}" alt="Photocard {k} de {len(cards)}" loading="lazy"></a>'
                             for k, c in enumerate(cards, 1))
        return (f'<section class="baixar"><h3>Seus photocards Nº {numero:02d}</h3>'
                f'<p>Toque em cada um para baixar. Tamanho de tela de celular, pronto para wallpaper.</p>'
                f'<div class="cards">{miniaturas}</div></section>')
    return ('<section class="baixar"><h3>Guarde esta edição</h3>'
            '<p>Baixe em PDF para ler depois ou imprimir. No celular, escolha "Salvar como PDF".</p>'
            '<button class="btn" type="button" onclick="window.print()">Baixar em PDF</button></section>')


def render(canal: str, numero: int, d: dict, hoje: datetime.date | None = None,
           cards: list[str] | None = None) -> str:
    e = html.escape
    cfg = CANAIS[canal]
    hoje = hoje or datetime.date.today()
    semana = f"{(hoje - datetime.timedelta(days=DIAS - 1)):%d/%m} a {hoje:%d/%m/%Y}"
    secoes = []
    for i, s in enumerate(d.get("secoes") or [], 1):
        itens = "".join(f"<li>{e(str(x))}</li>" for x in (s.get("itens") or []))
        extra = "".join(f"<li>{e(str(x))}</li>" for x in (s.get("extra") or []))
        blocos = f'<div class="bloco"><b>{e(cfg["itens"])}</b><ol>{itens}</ol></div>' if itens else ""
        if extra:
            blocos += f'<div class="bloco"><b>{e(cfg["extra"])}</b><ul>{extra}</ul></div>'
        secoes.append(
            f'<article class="secao"><div class="num">{i:02d}</div>'
            f'<div class="nome">{e(cfg["secao"])} · {e(str(s.get("nome", "")))}</div>'
            f'<h2>{e(str(s.get("titulo", "")))}</h2>'
            f'<p class="resumo">{e(str(s.get("resumo", "")))}</p>'
            f'<div class="colunas">{blocos}</div></article>')
    t = d.get("teste") or {}
    opcoes = "".join(f"<span><i>{chr(65 + k)}</i>{e(str(o))}</span>"
                     for k, o in enumerate(re.sub(r"^[A-D][).:-]\s*", "", str(x)) for x in (t.get("opcoes") or [])[:4]))
    teste = (f'<section class="teste"><div class="ficha">Teste da semana</div>'
             f'<h3>{e(str(t.get("pergunta", "")))}</h3><div class="opcoes">{opcoes}</div>'
             f'<p>Responde no último vídeo do {e(cfg["arroba"])} 👇</p></section>') if t.get("pergunta") else ""
    css = CSS % {"cor": cfg["cor"], "fundo": cfg["fundo"], "numero": numero}
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only">
<title>{e(cfg["ficha"])} Nº {numero} · {e(cfg["marca"].title())}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800;9..144,900&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{css}</style></head><body><main class="folha">
<header class="topo"><span class="marca">{e(cfg["marca"])}</span><span class="selo">Exclusivo</span></header>
<section class="capa"><div class="ficha">{e(cfg["ficha"])} · Nº {numero}</div>
<h1>{e(str(d.get("capa", "")))}</h1><p class="sub">{e(str(d.get("subtitulo", "")))}</p>
<div class="meta"><span>Semana {semana}</span><span>{len(d.get("secoes") or [])} destaques</span><span>Edição para guardar</span></div></section>
<div class="indice">NESTA EDIÇÃO</div>
{"".join(secoes)}
{teste}
{_baixar(canal, numero, cards)}
<p class="proxima">{e(str(d.get("proxima", "")))}<br>A edição Nº {numero + 1} chega no seu e-mail.</p>
<footer class="rodape"><span>{e(cfg["ficha"])} Nº {numero} · feita com os vídeos da semana no {e(cfg["arroba"])}</span>
<a href="https://www.tiktok.com/{e(cfg["arroba"])}">Ver os vídeos →</a></footer>
</main></body></html>"""


FONTES = Path("C:/Windows/Fonts")


def _fonte(nome: str, tam: int):
    from PIL import ImageFont
    for n in (nome, "arialbd.ttf"):
        try:
            return ImageFont.truetype(str(FONTES / n), tam)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _quebrar(draw, texto: str, fonte, largura: int) -> list[str]:
    linhas, atual = [], ""
    for p in texto.split():
        t = (atual + " " + p).strip()
        if draw.textlength(t, font=fonte) <= largura:
            atual = t
        else:
            if atual:
                linhas.append(atual)
            atual = p
    return linhas + ([atual] if atual else [])


def photocards(canal: str, numero: int, d: dict) -> list[Path]:
    """Um PNG 1080x1920 (tela de celular) por destaque: o PHOTOCARD da semana.

    ⛔ SEM FOTO de idol (direito de imagem): e' arte nossa com o nome, a
    chamada da semana e o numero da colecao — o que o fa coleciona e troca.
    """
    from PIL import Image, ImageDraw
    cfg = CANAIS[canal]
    W, H, M = 1080, 1920, 96
    cor = tuple(int(cfg["cor"][i:i + 2], 16) for i in (1, 3, 5))
    fundo = tuple(int(cfg["fundo"][i:i + 2], 16) for i in (1, 3, 5))
    secoes = d.get("secoes") or []
    out = []
    for k, s in enumerate(secoes, 1):
        im = Image.new("RGB", (W, H), (255, 255, 255))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((40, 40, W - 40, H - 40), radius=64, fill=fundo, outline=cor, width=6)
        # numero gigante ao fundo
        dr.text((W - 60, H - 120), f"{numero:02d}", font=_fonte("georgiab.ttf", 520),
                fill=tuple(int(c + (255 - c) * .82) for c in cor), anchor="rs")
        dr.text((M, 150), cfg["marca"], font=_fonte("seguibl.ttf", 40), fill=cor)
        selo = f"PHOTOCARD Nº {numero:02d} · {k}/{len(secoes)}"
        dr.rounded_rectangle((M, 230, M + dr.textlength(selo, font=_fonte("segoeuib.ttf", 34)) + 56, 300),
                             radius=35, outline=(23, 20, 29), width=4)
        dr.text((M + 28, 265), selo, font=_fonte("segoeuib.ttf", 34), fill=(23, 20, 29), anchor="lm")
        y = 560
        for ln in _quebrar(dr, str(s.get("nome", "")).upper(), _fonte("georgiab.ttf", 150), W - 2 * M)[:3]:
            dr.text((M, y), ln, font=_fonte("georgiab.ttf", 150), fill=(23, 20, 29))
            y += 165
        y += 30
        dr.rectangle((M, y, M + 140, y + 12), fill=cor)
        y += 60
        for ln in _quebrar(dr, str(s.get("titulo", "")), _fonte("georgiab.ttf", 64), W - 2 * M)[:4]:
            dr.text((M, y), ln, font=_fonte("georgiab.ttf", 64), fill=(23, 20, 29))
            y += 80
        y += 24
        for ln in _quebrar(dr, str(s.get("resumo", "")), _fonte("segoeui.ttf", 42), W - 2 * M)[:5]:
            dr.text((M, y), ln, font=_fonte("segoeui.ttf", 42), fill=(91, 86, 102))
            y += 58
        dr.text((M, H - 150), cfg["arroba"], font=_fonte("segoeuib.ttf", 40), fill=cor)
        dr.text((M, H - 100), "coleção semanal · guarde e troque", font=_fonte("segoeui.ttf", 32),
                fill=(91, 86, 102))
        p = SAIDA / f"{canal}_N{numero:02d}_card{k}.png"
        im.save(p, optimize=True)
        out.append(p)
    return out


def gerar(canal: str, gravar: bool = False) -> Path | None:
    n = numero_atual(canal)
    d = montar_dados(canal, n)
    if not d:
        return None
    SAIDA.mkdir(parents=True, exist_ok=True)
    p = SAIDA / f"{canal}_N{n:02d}.html"
    # JSON primeiro: erro de layout nao pode jogar fora a resposta do modelo
    (SAIDA / f"{canal}_N{n:02d}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    cards = [c.name for c in photocards(canal, n, d)] if canal == "camarim.kpop" else None
    import edicao_design
    p.write_text(edicao_design.render(canal, CANAIS[canal], n, d, cards=cards), encoding="utf-8")
    (SAIDA / f"{canal}_N{n:02d}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    if gravar:
        gravar_numero(canal, n)
    print(f"  {canal}: Nº {n} com {len(d['secoes'])} secao(oes) de {d['_clipes']} clipe(s) -> {p.name}")
    return p


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--canal")
    a.add_argument("--todos", action="store_true")
    a.add_argument("--gravar", action="store_true", help="avanca o numero (so' na edicao que sai de verdade)")
    x = a.parse_args()
    for c in (CANAIS if x.todos else [x.canal]):
        if c not in CANAIS:
            sys.exit(f"canal desconhecido: {c}")
        gerar(c, x.gravar)


if __name__ == "__main__":
    main()
