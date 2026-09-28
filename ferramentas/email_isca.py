# -*- coding: utf-8 -*-
"""E-mail da ISCA de cada canal (28/09/2026, dono: "botao de e-mail para os
outros tambem, cada um personalizado").

    python ferramentas/email_isca.py                       previas em _privado/
    python ferramentas/email_isca.py --teste EMAIL PRODUTO manda UM de teste

Quem deixa o e-mail no bloco da bio (`contato.produto` = um dos PRODUTOS
abaixo) recebe UMA vez o e-mail do canal, montado com o que o canal ja'
publicou (manifesto). Sai pela rodada do `engine/alertas_email.py`
(maquina local, LGPD, com o link de sair).

⭐ BOAS-VINDAS = ENTREGAR O PRESENTE, NAO VENDER (dono + acervo, 28/09): o
e-mail entrega o prometido (F17366), diz a frequencia (F17367) e pede para
salvar o remetente (F17369). Oferta so' nas newsletters seguintes (F11097:
historia + oferta + CTA); aqui, no maximo a linha discreta do rodape.

⛔ HONESTIDADE: com menos de `minimo` itens o e-mail NAO sai (a pessoa espera
e o registro nao marca como enviado). Nunca prometer "toda semana" na bio
enquanto nao houver envio semanal.
"""
import html
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "ferramentas"))

SITE = "https://achadinhototal.com.br"

# produto -> como montar o e-mail daquele canal
PRODUTOS = {
    "receitas_marmita": {
        "canal": "cozinha.importada", "marca": "ACHADINHO CHEF", "cor": "#1F8A5F",
        "assunto": "Seu cardápio de marmitas: medida em grama e °C 🍱",
        "titulo": "Receita gringa,<br><span>medida brasileira.</span>",
        "abre": "Aqui estão as marmitas do canal, já em grama e °C. Rendem a semana, custam pouco e têm proteína.",
        "perfil": "https://www.tiktok.com/@achadinhochef", "bio": "https://chef.achadinhototal.com.br",
        "botao": "Ver os vídeos das receitas →",
        "rodape": "Você recebeu isto porque pediu o cardápio de marmitas na página do Achadinho Chef.",
        "medida": True, "minimo": 3, "maximo": 7, "corte": 1400,
    },
    "modofuturo_resumo": {
        "canal": "modofuturo", "marca": "MODO FUTURO", "cor": "#1B5BFF",
        "assunto": "A tecnologia por dentro, em 2 minutos de leitura ⚡",
        "titulo": "O que está mudando<br><span>o mundo agora.</span>",
        "abre": "As histórias mais recentes do canal — chips, fábricas e IA — explicadas sem enrolação.",
        "perfil": "https://www.tiktok.com/@modofuturo", "bio": SITE,
        "botao": "Ver os vídeos no TikTok →",
        "rodape": "Você recebeu isto porque pediu o resumo do Modo Futuro na página do canal.",
        "medida": False, "minimo": 3, "maximo": 5, "corte": 600,
    },
    "semanestesia_ideias": {
        "canal": "semanestesia.pod", "marca": "SEM ANESTESIA", "cor": "#D92B2B",
        "assunto": "Mente forte, com ciência: as ideias que mais pegaram 🧠",
        "titulo": "Disciplina não é<br><span>força de vontade.</span>",
        "abre": "As ideias do canal sobre disciplina, dopamina e hábitos — com a ciência por trás e de onde elas vieram.",
        "perfil": "https://www.tiktok.com/@semanestesia.pod", "bio": SITE,
        "botao": "Ver os vídeos no TikTok →",
        "rodape": "Você recebeu isto porque pediu as ideias do Sem Anestesia na página do canal.",
        "medida": False, "minimo": 3, "maximo": 5, "corte": 600,
    },
    "nostalgia_historias": {
        "canal": "atefalhar", "marca": "NOSTALGIA 2000", "cor": "#E36414",
        "assunto": "Os desenhos da sua infância, do jeito que ninguém contou 📺",
        "titulo": "Lembra disso?<br><span>Tem mais história.</span>",
        "abre": "As histórias por trás dos desenhos que a gente assistia no começo dos anos 2000.",
        "perfil": "https://www.tiktok.com/@atefalhar", "bio": SITE,
        "botao": "Ver os vídeos no TikTok →",
        "rodape": "Você recebeu isto porque pediu as histórias de nostalgia na página do canal.",
        "medida": False, "minimo": 3, "maximo": 5, "corte": 600,
        # so' cortes da fase NOSTALGIA (nao os de treino antigos do canal)
        "desde": "2026-09-28",
    },
    "make_achados": {
        "canal": "truque.importado", "marca": "ACHADINHO MAKE", "cor": "#D6336C",
        "assunto": "As makes dos vídeos, com o preço conferido 💄",
        "titulo": "A make que viraliza,<br><span>pelo menor preço.</span>",
        "abre": "O que as idols usaram nos vídeos do canal. Eu confiro o preço e te aviso quando cair.",
        "perfil": "https://www.tiktok.com/@achadinho.make", "bio": SITE,
        "botao": "Ver os vídeos no TikTok →",
        "rodape": "Você recebeu isto porque pediu as makes do Achadinho Make na página do canal.",
        "medida": False, "minimo": 3, "maximo": 5, "corte": 450,
    },
}


def itens(produto: str) -> list[dict]:
    """[{titulo, texto}] do canal do produto, os mais novos primeiro."""
    cfg = PRODUTOS[produto]
    import agendar_buffer as ab
    man = ab.manifesto(ab._token_github(), None)
    out = []
    for _, v in sorted(man.items(), reverse=True):
        if v.get("canal") != cfg["canal"]:
            continue
        if cfg.get("desde") and str(v.get("publicado_em") or "")[:10] < cfg["desde"]:
            continue
        titulo = (v.get("titulo") or "").strip()
        leg = (v.get("legenda") or "").strip()
        corpo = leg[len(titulo):].strip() if leg.startswith(titulo) else leg
        corpo = re.sub(r"(?:\s*#\w+)+\s*$", "", corpo).strip()
        if not titulo or not corpo:
            continue
        # receita so' entra com MEDIDA (g, ml, °C): e' o produto do canal
        if cfg["medida"] and not re.search(r"\d\s*(g|ml|kg|°C)\b", corpo):
            continue
        texto = corpo[:cfg["corte"]]
        if len(corpo) > cfg["corte"]:
            texto = texto.rsplit(" ", 1)[0] + "…"
        out.append({"titulo": titulo, "texto": texto})
        if len(out) >= cfg["maximo"]:
            break
    return out


def montar(produto: str, rs: list[dict], sair_url: str = "") -> str:
    cfg, e = PRODUTOS[produto], html.escape
    cor = cfg["cor"]
    titulo = cfg["titulo"].replace("<span>", f'<span style="color:{cor}">')
    blocos = "".join(
        f'<tr><td style="padding:14px 24px;border-top:1px solid #eeeaf2">'
        f'<div style="font:800 17px/1.3 Arial,Helvetica,sans-serif;color:#16141c">{i}. {e(r["titulo"])}</div>'
        f'<div style="padding-top:8px;font:15px/1.6 Arial,Helvetica,sans-serif;color:#3b3845;white-space:pre-line">{e(r["texto"])}</div>'
        f'</td></tr>' for i, r in enumerate(rs, 1))
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><title>{e(cfg["assunto"])}</title></head>
<body style="margin:0;padding:0;background:#ffffff">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff"><tr><td align="center" style="padding:20px 12px">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px">
 <tr><td align="center" style="padding:6px 20px 0;font:12px/1 Arial,Helvetica,sans-serif;letter-spacing:4px;color:{cor}">{e(cfg["marca"])}</td></tr>
 <tr><td align="center" style="padding:12px 20px 6px;font:800 28px/1.15 Arial,Helvetica,sans-serif;color:#16141c">{titulo}</td></tr>
 <tr><td align="center" style="padding:6px 28px 14px;font:16px/1.55 Arial,Helvetica,sans-serif;color:#3b3845">{e(cfg["abre"])}</td></tr>
 {blocos}
 <tr><td align="center" style="padding:22px 20px 8px">
   <a href="{cfg["perfil"]}" style="display:inline-block;background:{cor};color:#ffffff;text-decoration:none;font:700 17px/1 Arial,Helvetica,sans-serif;padding:16px 34px;border-radius:999px">{e(cfg["botao"])}</a></td></tr>
 <tr><td align="center" style="padding:6px 20px 20px;font:14px/1.5 Arial,Helvetica,sans-serif;color:#6b6776">
   O que aparece nos vídeos está em <a href="{cfg["bio"]}" style="color:{cor}">{e(cfg["bio"].split("//")[1])}</a>.</td></tr>
 <tr><td align="center" style="padding:4px 28px 18px;font:13px/1.55 Arial,Helvetica,sans-serif;color:#6b6776">
   Daqui pra frente eu só escrevo quando tiver coisa boa de verdade — nada de e-mail todo dia.<br>
   <b>Chegou em Promoções?</b> Arraste para a Principal ou salve este remetente, senão os próximos se perdem.</td></tr>
 <tr><td align="center" style="padding:10px 24px 24px;border-top:1px solid #eeeaf2;font:11px/1.5 Arial,Helvetica,sans-serif;color:#9a96a3">
   {e(cfg["rodape"])}<br>
   Contém links de afiliado: se você comprar, a loja me paga uma comissão, sem custo para você.<br>
   <a href="{e(sair_url or SITE + '/sair')}" style="color:#9a96a3">Não quero mais receber</a> · <a href="{SITE}/privacidade" style="color:#9a96a3">Privacidade</a></td></tr>
</table></td></tr></table></body></html>'''


def pronto_para_enviar(produto: str, sair_url: str = "") -> tuple[str, str] | None:
    """(assunto, html), ou None se ainda nao ha' itens bastantes."""
    rs = itens(produto)
    if len(rs) < PRODUTOS[produto]["minimo"]:
        return None
    return PRODUTOS[produto]["assunto"], montar(produto, rs, sair_url)


if __name__ == "__main__":
    for prod in PRODUTOS:
        rs = itens(prod)
        print(f"{prod}: {len(rs)} item(ns) (minimo {PRODUTOS[prod]['minimo']})")
        saida = RAIZ / "_privado" / f"email_isca_{prod}.html"
        saida.write_text(montar(prod, rs or [{"titulo": "Exemplo", "texto": "texto de exemplo"}]),
                         encoding="utf-8")
    if "--teste" in sys.argv:
        i = sys.argv.index("--teste")
        para, prod = sys.argv[i + 1], sys.argv[i + 2]
        import email_boas_vindas as bv
        a, corpo = PRODUTOS[prod]["assunto"], montar(prod, itens(prod))
        bv.enviar(para, a, corpo)
