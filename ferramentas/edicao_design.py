# -*- coding: utf-8 -*-
"""O DESENHO da Edicao da Semana: gramatica de capa de revista teen (03/10/2026).

Dono: "achei muito simples, cara de AI; vamos analisar profundamente como eles
fazem nas capas e aplicar". Lido em 8 capas reais (Capricho 1991-2004,
Seventeen 2008-2010) + 155 leituras do Gemini (_privado/capricho/):

  capa                                  | aqui
  --------------------------------------|---------------------------------------
  logo GIGANTE de ponta a ponta,        | marca do canal em letra cursiva enorme,
  a estrela da capa passa por cima      | o BALAO metalizado por cima do logo
  faixa de BONUS no topo                | faixa colorida com o brinde da edicao
  caixa "nº 891 · abril · R$ 3,50"      | caixa de edicao + codigo de barras
  + codigo de barras                    |
  selo estourado inclinado              | selo em estrela, girado
  ("6 POSTERS INCRIVEIS")               |
  chamadas empilhadas: NOME em caps     | coluna de chamadas: nome colorido + 2
  colorido + 2-3 linhas                 | linhas
  numero gigante (926, 763)             | numero da edicao em letra condensada
  manchete em 2 cores                   | manchete condensada, 1a palavra na cor
  rabiscos: estrela, coracao            | 3 rabiscos em SVG (pouco, nao enfeite)
  sumario com abas coloridas            | secoes com aba colorida + numero grande
  TESTE com caixa amarela               | teste em caixa amarela, opcoes com caixinha

Cores: a do canal + amarelo de capa + tinta preta, fundo BRANCO (ordem do dono:
so' fundo branco). Fontes: Grand Hotel (logo cursivo), Anton (condensada de
capa), Archivo (texto).
"""
from __future__ import annotations

import base64
import datetime
import html
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BALOES = RAIZ / "paginas" / "baloes"
FIGURINHAS = RAIZ / "paginas" / "figurinhas"

# o balao "estrela da capa" de cada canal (gerados em 03/10 por gerar_balao.py)
BALAO = {
    "truque.importado": "make_compacto", "camarim.kpop": "camarim_photocard",
    "cozinha.importada": "chef_panela", "semanestesia.pod": "semanestesia_ampulheta",
    "modofuturo": "modofuturo_foguete"  # 03/10: dono trocou o chip pelo foguete, "atefalhar": "nostalgia_tv",
}
RESERVA = {"truque.importado": "make_batom", "cozinha.importada": "chef_marmita",
           "semanestesia.pod": "semanestesia_cerebro", "modofuturo": "modofuturo_robo",
           "atefalhar": "nostalgia_controle", "camarim.kpop": "inaug_estrela"}

MESES = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

CSS = """
:root{--cor:@COR;--fundo:@FUNDO;--amarelo:#FFD60A;--tinta:#141118;--suave:#55505e;--linha:#ebe6ef;--papel:#ffffff;
 --logo:'Grand Hotel',cursive;--capa:Anton,Impact,'Arial Narrow',sans-serif;--texto:Archivo,system-ui,sans-serif}
*{box-sizing:border-box;margin:0}
html{background:var(--papel);color-scheme:light only}
body{background:var(--papel);color:var(--tinta);font:16px/1.55 var(--texto);-webkit-font-smoothing:antialiased}
.revista{max-width:780px;margin:0 auto;padding-inline:16px;padding-block:0 56px}
.faixa{margin-inline:-16px;background:var(--cor);color:#fff;font:400 clamp(15px,3.6vw,20px)/1 var(--capa);
 letter-spacing:.04em;text-transform:uppercase;padding:11px 16px;text-align:center}
.faixa b{color:var(--amarelo);font-weight:400}
.capa{position:relative;padding-top:6px;min-height:0}
.masthead{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.logo{font:400 clamp(64px,17vw,132px)/.9 var(--logo);color:var(--cor);letter-spacing:-.01em;
 text-shadow:3px 3px 0 var(--amarelo);margin-top:4px;max-width:72%}
.caixa{flex:none;margin-top:14px;text-align:right;font:700 11px/1.25 var(--texto);letter-spacing:.06em;text-transform:uppercase}
.caixa .n{display:block;font:400 34px/1 var(--capa);color:var(--tinta)}
.barras{display:block;margin:6px 0 0 auto;width:74px;height:26px;
 background:repeating-linear-gradient(90deg,var(--tinta) 0 2px,transparent 2px 4px,var(--tinta) 4px 5px,transparent 5px 8px,var(--tinta) 8px 11px,transparent 11px 12px)}
.estrela{position:absolute;right:-8px;top:clamp(70px,16vw,120px);width:clamp(150px,36vw,250px);height:auto;
 transform:rotate(8deg);filter:drop-shadow(0 18px 18px rgba(20,17,24,.18));z-index:2}
.chamadas{position:relative;z-index:3;display:grid;gap:16px;max-width:58%;margin-top:clamp(10px,3vw,22px)}
.chamada .k{display:block;font:400 clamp(20px,4.6vw,27px)/1 var(--capa);color:var(--cor);text-transform:uppercase;letter-spacing:.01em}
.chamada .t{font:600 15px/1.35 var(--texto);color:var(--tinta)}
.selo{position:absolute;z-index:4;right:clamp(4px,4vw,40px);top:clamp(300px,64vw,430px);width:118px;height:118px;
 display:grid;place-items:center;text-align:center;background:var(--amarelo);color:var(--tinta);transform:rotate(-12deg);
 clip-path:polygon(50% 0,61% 12%,76% 6%,79% 22%,95% 24%,89% 39%,100% 50%,89% 61%,95% 76%,79% 78%,76% 94%,61% 88%,50% 100%,39% 88%,24% 94%,21% 78%,5% 76%,11% 61%,0 50%,11% 39%,5% 24%,21% 22%,24% 6%,39% 12%);
 font:400 18px/1.02 var(--capa);text-transform:uppercase;padding:18px}
.manchete{position:relative;z-index:3;margin-top:26px;font:400 clamp(44px,11vw,84px)/.95 var(--capa);text-transform:uppercase;
 letter-spacing:-.005em;text-wrap:balance}
.manchete em{font-style:normal;color:var(--cor)}
.linha-fina{margin-top:12px;font:600 clamp(16px,3.4vw,19px)/1.4 var(--texto);color:var(--suave);max-width:46ch}
.rabisco{position:absolute;z-index:1;color:var(--cor)}
.rabisco.r1{right:2px;top:clamp(380px,90vw,520px);width:28px;transform:rotate(-14deg)}
.rabisco.r2{right:40%;top:clamp(300px,70vw,420px);width:26px;color:var(--amarelo)}
.rabisco.r3{right:6px;bottom:-30px;width:34px;transform:rotate(10deg)}
.sumario{margin-top:44px;border-top:4px solid var(--tinta);padding-top:10px}
.sumario h2{font:400 clamp(30px,7vw,44px)/1 var(--logo);color:var(--cor)}
.secao{display:grid;grid-template-columns:auto minmax(0,1fr);gap:4px 16px;padding:22px 0;border-bottom:2px dashed var(--linha)}
.secao .num{grid-row:span 5;font:400 clamp(52px,12vw,72px)/.85 var(--capa);color:var(--tinta);min-width:1.1ch}
.aba{justify-self:start;background:var(--cor);color:#fff;font:400 15px/1 var(--capa);letter-spacing:.06em;text-transform:uppercase;
 padding:6px 10px 5px;transform:rotate(-1.5deg)}
.secao:nth-child(even) .aba{background:var(--tinta);transform:rotate(1.2deg)}
.secao h3{margin-top:6px;font:400 clamp(24px,5.4vw,32px)/1.05 var(--capa);text-transform:uppercase;text-wrap:balance}
.secao .resumo{color:var(--suave)}
.listas{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:8px}
.lista b{display:inline-block;font:400 14px/1 var(--capa);letter-spacing:.08em;text-transform:uppercase;
 background:var(--amarelo);padding:5px 8px 4px;margin-bottom:8px}
.lista ol,.lista ul{list-style:none;padding:0;display:grid;gap:7px}
.lista li{position:relative;padding-left:26px;font-size:15px}
.lista ol{counter-reset:p}
.lista ol li::before{counter-increment:p;content:counter(p);position:absolute;left:0;top:1px;width:19px;height:19px;border-radius:50%;
 background:var(--cor);color:#fff;font:400 12px/19px var(--capa);text-align:center}
.lista ul li::before{content:"\\2714";position:absolute;left:2px;top:0;color:var(--cor);font-weight:800}
.teste{position:relative;margin-top:34px;background:var(--amarelo);padding:clamp(22px,5vw,32px);transform:rotate(-.6deg)}
.teste .rotulo{display:inline-block;background:var(--tinta);color:var(--amarelo);font:400 26px/1 var(--capa);letter-spacing:.06em;padding:6px 12px 4px}
.teste h3{margin:12px 0 14px;font:400 clamp(24px,5.6vw,34px)/1.05 var(--capa);text-transform:uppercase;text-wrap:balance}
.ops{display:grid;gap:10px}
.ops span{display:flex;gap:12px;align-items:flex-start;font:600 16px/1.35 var(--texto)}
.ops i{flex:none;width:22px;height:22px;border:3px solid var(--tinta);background:#fff;margin-top:1px}
.teste p{margin-top:14px;font:700 14px/1.3 var(--texto)}
.balao-teste{position:absolute;right:-10px;top:-46px;width:92px;transform:rotate(10deg)}
.baixar{margin-top:30px;border:3px solid var(--tinta);padding:22px;text-align:center}
.baixar h3{font:400 clamp(24px,5vw,30px)/1.05 var(--capa);text-transform:uppercase}
.baixar p{color:var(--suave);font-size:15px;margin-top:4px}
.btn{display:inline-block;margin-top:14px;background:var(--cor);color:#fff;border:0;cursor:pointer;font:400 19px/1 var(--capa);
 letter-spacing:.05em;text-transform:uppercase;padding:15px 26px 13px;box-shadow:4px 4px 0 var(--tinta);text-decoration:none}
.btn:focus-visible{outline:3px solid var(--tinta);outline-offset:3px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-top:16px}
.cards a{display:block;box-shadow:4px 4px 0 var(--tinta);border:2px solid var(--tinta)}
.cards a:nth-child(odd){transform:rotate(-2deg)}.cards a:nth-child(even){transform:rotate(2deg)}
.cards img{display:block;width:100%;height:auto}
.proxima{margin-top:30px;text-align:center;font:400 clamp(26px,6vw,34px)/1.1 var(--logo);color:var(--cor)}
.proxima small{display:block;margin-top:6px;font:700 13px/1.3 var(--texto);color:var(--suave);letter-spacing:.06em;text-transform:uppercase}
.rodape{margin-top:22px;padding-top:12px;border-top:2px solid var(--tinta);display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:13px;color:var(--suave)}
.rodape a{color:var(--cor);font-weight:800;text-decoration:none}
@media (max-width:520px){.chamadas{max-width:62%}.selo{width:100px;height:100px;font-size:15px}}
@page{size:A4;margin:12mm}
@media print{.baixar{display:none}.faixa,.teste,.aba,.selo,.lista b{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""

ESTRELA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.8-6.2 3.8 1.6-7L2 9.2l7.1-.6z"/></svg>'
CORACAO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M12 21s-7.5-4.6-9.6-9.2C1 8.6 3 5 6.5 5c2.2 0 3.6 1.2 5.5 3.3C13.9 6.2 15.3 5 17.5 5 21 5 23 8.6 21.6 11.8 19.5 16.4 12 21 12 21z"/></svg>'


def uri_balao(canal: str, pequeno: bool = False) -> str:
    for nome in (BALAO.get(canal), RESERVA.get(canal)):
        if not nome:
            continue
        p = BALOES / f"{nome}{'_p' if pequeno else ''}.webp"
        if p.exists():
            return "data:image/webp;base64," + base64.b64encode(p.read_bytes()).decode()
    return ""


def _manchete(t: str) -> str:
    """1a palavra (ou o numero) na cor do canal, como as manchetes de 2 cores."""
    e = html.escape
    partes = t.split(" ", 1)
    return f"<em>{e(partes[0])}</em> {e(partes[1])}" if len(partes) == 2 else e(t)


def render(canal: str, cfg: dict, numero: int, d: dict, cards: list[str] | None = None,
           hoje: datetime.date | None = None) -> str:
    e = html.escape
    hoje = hoje or datetime.date.today()
    secoes = d.get("secoes") or []
    balao = uri_balao(canal)
    chamadas = "".join(
        f'<div class="chamada"><span class="k">{e(str(s.get("nome", "")))}</span>'
        f'<p class="t">{e(str(s.get("titulo", "")))}</p></div>' for s in secoes[:4])
    blocos = []
    for i, s in enumerate(secoes, 1):
        itens = "".join(f"<li>{e(str(x))}</li>" for x in (s.get("itens") or []))
        extra = "".join(f"<li>{e(str(x))}</li>" for x in (s.get("extra") or []))
        listas = f'<div class="lista"><b>{e(cfg["itens"])}</b><ol>{itens}</ol></div>' if itens else ""
        if extra:
            listas += f'<div class="lista"><b>{e(cfg["extra"])}</b><ul>{extra}</ul></div>'
        blocos.append(
            f'<article class="secao"><div class="num">{i:02d}</div>'
            f'<span class="aba">{e(cfg["secao"])} · {e(str(s.get("nome", "")))}</span>'
            f'<h3>{e(str(s.get("titulo", "")))}</h3><p class="resumo">{e(str(s.get("resumo", "")))}</p>'
            f'<div class="listas">{listas}</div></article>')
    t = d.get("teste") or {}
    ops = "".join(f"<span><i></i>{e(str(o))}</span>" for o in (t.get("opcoes") or [])[:4])
    teste = (f'<section class="teste"><img class="balao-teste" src="{uri_teste()}" alt="" aria-hidden="true">'
             f'<span class="rotulo">TESTE</span><h3>{e(str(t.get("pergunta", "")))}</h3>'
             f'<div class="ops">{ops}</div><p>Marque a sua e responde no último vídeo do {e(cfg["arroba"])} 👇</p></section>'
             ) if t.get("pergunta") else ""
    if cards:
        miniaturas = "".join(f'<a href="{e(c)}" download><img src="{e(c)}" alt="Photocard {k} de {len(cards)}" loading="lazy"></a>'
                             for k, c in enumerate(cards, 1))
        baixar = (f'<section class="baixar"><h3>Seus {len(cards)} photocards Nº {numero:02d}</h3>'
                  f'<p>Toque em cada um para baixar. Tamanho de tela de celular.</p><div class="cards">{miniaturas}</div></section>')
        brinde = f"{len(cards)} photocards pra colecionar!"
    else:
        baixar = ('<section class="baixar"><h3>Guarde esta edição</h3><p>Baixe em PDF para ler depois ou imprimir.</p>'
                  '<button class="btn" type="button" onclick="window.print()">Baixar em PDF</button></section>')
        brinde = "edição pra guardar!"
    selo = e(str(d.get("selo") or ("Exclusivo!" if not cards else f"{len(cards)} photocards!")))
    css = CSS.replace("@COR", cfg["cor"]).replace("@FUNDO", cfg["fundo"])
    logo = cfg.get("logo") or cfg["marca"].title()
    # hifen que nao quebra ("K-" / "pop" quebrou no celular) e 1 palavra por linha
    logo_html = "<br>".join(e(w).replace("-", "‑") for w in logo.split())
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only">
<title>{e(cfg["ficha"])} Nº {numero} · {e(logo)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@500;600;700;800&family=Grand+Hotel&display=swap" rel="stylesheet">
<style>{css}</style></head><body><main class="revista">
<div class="faixa">Bônus: <b>{e(brinde)}</b></div>
<section class="capa">
 <div class="masthead"><div class="logo">{logo_html}</div>
  <div class="caixa"><span class="n">Nº {numero:02d}</span>{MESES[hoje.month - 1]} {hoje.year}<br>Grátis<span class="barras" aria-hidden="true"></span></div></div>
 {f'<img class="estrela" src="{balao}" alt="" aria-hidden="true">' if balao else ''}
 <span class="rabisco r1" aria-hidden="true">{ESTRELA}</span><span class="rabisco r2" aria-hidden="true">{ESTRELA}</span><span class="rabisco r3" aria-hidden="true">{CORACAO}</span>
 <div class="chamadas">{chamadas}</div>
 <div class="selo">{selo}</div>
 <h1 class="manchete">{_manchete(str(d.get("capa", "")))}</h1>
 <p class="linha-fina">{e(str(d.get("subtitulo", "")))}</p>
</section>
<section class="sumario"><h2>Nesta edição</h2>{"".join(blocos)}</section>
{teste}
{baixar}
{figurinhas(canal, numero)}
<p class="proxima">{e(str(d.get("proxima", "")))}<small>A edição Nº {numero + 1:02d} chega no seu e-mail</small></p>
<footer class="rodape"><span>{e(cfg["ficha"])} Nº {numero:02d} · feita com os vídeos da semana do {e(cfg["arroba"])}</span>
<a href="https://www.tiktok.com/{e(cfg["arroba"])}">Ver os vídeos →</a></footer>
</main></body></html>"""


def figurinhas(canal: str, numero: int) -> str:
    """Bloco "Baixar figurinhas" (04/10/2026): so' aparece se existir
    paginas/figurinhas/<canal>/<NN>/pacote.json com o link do Sticker.ly."""
    import json
    pasta = FIGURINHAS / canal / f"{numero:02d}"
    cfg = pasta / "pacote.json"
    if not cfg.exists():
        return ""
    d = json.loads(cfg.read_text(encoding="utf-8"))
    imgs = "".join(
        f'<img src="data:image/webp;base64,{base64.b64encode((pasta / f"{n}.webp").read_bytes()).decode()}" alt="" loading="lazy">'
        for n in d.get("ordem", []) if (pasta / f"{n}.webp").exists())
    return (f'<section class="baixar figurinhas"><h3>Figurinhas Nº {numero:02d} pro WhatsApp</h3>'
            f'<p>{len(d.get("ordem", []))} figurinhas exclusivas, só aqui.</p><div class="cards">{imgs}</div>'
            f'<a class="btn" href="{html.escape(d["link"])}" target="_blank" rel="noopener">Adicionar no WhatsApp</a></section>')


def uri_teste() -> str:
    for nome in ("teste_balao_fala_p", "inaug_coracao_p"):
        p = BALOES / f"{nome}.webp"
        if p.exists():
            return "data:image/webp;base64," + base64.b64encode(p.read_bytes()).decode()
    return ""
