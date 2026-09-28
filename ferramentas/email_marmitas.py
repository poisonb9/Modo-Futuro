# -*- coding: utf-8 -*-
"""E-mail do CARDAPIO DE MARMITAS do Achadinho Chef (28/09/2026).

    python ferramentas/email_marmitas.py                 previa em _privado/
    python ferramentas/email_marmitas.py --teste EMAIL   manda UM de teste

Quem deixa o e-mail no bloco "cardapio de marmitas" da bio do Achadinho Chef
(`contato.produto = "receitas_marmita"`) recebe, UMA vez, as receitas do
canal ja' escritas em grama e °C (o `receita_texto` que vai na legenda).
Sai pela mesma rodada do `engine/alertas_email.py` (maquina local, LGPD).

⛔ HONESTIDADE: com menos de MIN_RECEITAS receitas no manifesto o e-mail NAO
sai (a pessoa espera; o registro nao marca como enviado). Cardapio de uma
receita so' e' promessa quebrada no primeiro e-mail.
"""
import html
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "ferramentas"))

PRODUTO = "receitas_marmita"
CANAL = "cozinha.importada"
PERFIL = "https://www.tiktok.com/@achadinhochef"
BIO = "https://achadinhochef.pages.dev"
MIN_RECEITAS = 3
MAX_RECEITAS = 7
VERDE = "#1F8A5F"


def receitas() -> list[dict]:
    """[{titulo, texto}] das receitas do canal, as mais novas primeiro."""
    import agendar_buffer as ab
    man = ab.manifesto(ab._token_github(), None)
    out = []
    for chave, v in sorted(man.items(), reverse=True):
        if v.get("canal") != CANAL:
            continue
        titulo = (v.get("titulo") or "").strip()
        leg = (v.get("legenda") or "").strip()
        corpo = leg[len(titulo):].strip() if leg.startswith(titulo) else leg
        corpo = re.sub(r"(?:\s*#\w+)+\s*$", "", corpo).strip()   # tira as hashtags
        # so' entra o que tem MEDIDA (g, ml, °C): e' o produto do canal
        if titulo and re.search(r"\d\s*(g|ml|kg|°C)\b", corpo):
            out.append({"titulo": titulo, "texto": corpo[:1400]})
        if len(out) >= MAX_RECEITAS:
            break
    return out


def assunto() -> str:
    return "Seu cardápio de marmitas: medida em grama e °C 🍱"


def montar(rs: list[dict], sair_url: str = "") -> str:
    e = html.escape
    blocos = "".join(
        f'<tr><td style="padding:14px 24px;border-top:1px solid #eeeaf2">'
        f'<div style="font:800 17px/1.3 Arial,Helvetica,sans-serif;color:#16141c">{i}. {e(r["titulo"])}</div>'
        f'<div style="padding-top:8px;font:15px/1.6 Arial,Helvetica,sans-serif;color:#3b3845;white-space:pre-line">{e(r["texto"])}</div>'
        f'</td></tr>' for i, r in enumerate(rs, 1))
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><title>{e(assunto())}</title></head>
<body style="margin:0;padding:0;background:#ffffff">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff"><tr><td align="center" style="padding:20px 12px">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px">
 <tr><td align="center" style="padding:6px 20px 0;font:12px/1 Arial,Helvetica,sans-serif;letter-spacing:4px;color:{VERDE}">ACHADINHO CHEF</td></tr>
 <tr><td align="center" style="padding:12px 20px 6px;font:800 28px/1.15 Arial,Helvetica,sans-serif;color:#16141c">Receita gringa,<br><span style="color:{VERDE}">medida brasileira.</span></td></tr>
 <tr><td align="center" style="padding:6px 28px 14px;font:16px/1.55 Arial,Helvetica,sans-serif;color:#3b3845">
   Aqui estão as marmitas do canal, já em grama e °C. Rendem a semana, custam pouco e têm proteína.</td></tr>
 {blocos}
 <tr><td align="center" style="padding:22px 20px 8px">
   <a href="{PERFIL}" style="display:inline-block;background:{VERDE};color:#ffffff;text-decoration:none;font:700 17px/1 Arial,Helvetica,sans-serif;padding:16px 34px;border-radius:999px">Ver os vídeos das receitas →</a></td></tr>
 <tr><td align="center" style="padding:6px 20px 20px;font:14px/1.5 Arial,Helvetica,sans-serif;color:#6b6776">
   Os potes e utensílios que eu uso estão em <a href="{BIO}" style="color:{VERDE}">achadinhochef.pages.dev</a>.</td></tr>
 <tr><td align="center" style="padding:10px 24px 24px;border-top:1px solid #eeeaf2;font:11px/1.5 Arial,Helvetica,sans-serif;color:#9a96a3">
   Você recebeu isto porque pediu o cardápio de marmitas na página do Achadinho Chef.<br>
   Contém links de afiliado: se você comprar, a loja me paga uma comissão, sem custo para você.<br>
   <a href="{e(sair_url or 'https://achadinhototal.com.br/sair')}" style="color:#9a96a3">Não quero mais receber</a> · <a href="https://achadinhototal.com.br/privacidade" style="color:#9a96a3">Privacidade</a></td></tr>
</table></td></tr></table></body></html>'''


def pronto_para_enviar(sair_url: str = "") -> tuple[str, str] | None:
    """(assunto, html), ou None se ainda nao ha' receitas bastantes."""
    rs = receitas()
    if len(rs) < MIN_RECEITAS:
        return None
    return assunto(), montar(rs, sair_url)


if __name__ == "__main__":
    rs = receitas()
    print(f"{len(rs)} receita(s) com medida no manifesto (minimo {MIN_RECEITAS})")
    corpo = montar(rs or [{"titulo": "Exemplo: frango com arroz para 5 marmitas",
                           "texto": "500 g de peito de frango\n300 g de arroz\nForno a 200 °C por 25 min"}])
    saida = RAIZ / "_privado" / "email_marmitas.html"
    saida.write_text(corpo, encoding="utf-8")
    print("previa:", saida)
    if "--teste" in sys.argv:
        import email_boas_vindas as bv
        bv.enviar(sys.argv[sys.argv.index("--teste") + 1], assunto(), corpo)
