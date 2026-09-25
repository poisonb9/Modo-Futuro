# -*- coding: utf-8 -*-
"""E-mail de BOAS-VINDAS de quem deixou o e-mail no "avise-me" (25/09/2026).

    python ferramentas/email_boas_vindas.py                 previa (com um produto real)
    python ferramentas/email_boas_vindas.py --teste EMAIL   manda UM de teste para EMAIL

Sai UMA vez por pessoa, na primeira rodada de `engine/alertas_email.py` depois
do cadastro. Pelo acervo (e-mail de boas-vindas = o de maior conversao):
  1. confirma o que a pessoa pediu (o produto que ela quer vigiar) e o que
     esperar ("so' escrevo quando cair");
  2. da' um motivo para abrir o site JA': as 3 maiores quedas de hoje;
  3. um botao so', a assinatura "Fundador" e a saida em um toque.
Produto linka DIRETO ao afiliado (regra do dono); fotos hospedadas por nos.
"""
import html, sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "paginas"))
sys.path.insert(0, str(RAIZ / "ferramentas"))
import email_alerta as ea                                    # noqa: E402

SITE = ea.SITE
UTM = "utm_source=email&utm_medium=boas_vindas&utm_campaign=boas_vindas"


def assunto(p: dict | None) -> str:
    if p and p.get("nome"):
        return f"🔔 Pronto: estou de olho em {ea._curto(p['nome'], 34)}"
    return "🔔 Pronto: agora eu te aviso quando o preço cair"


def preheader() -> str:
    return "Só escrevo quando cair de verdade. E enquanto isso: as 3 maiores quedas de hoje."


def _cartao(p: dict, foto: str) -> str:
    e = html.escape
    url = p.get("link") or f"{SITE}/?p={p['id']}&{UTM}"
    nome = ea._curto(p["nome"], 40)
    queda = f'&nbsp;<b style="color:#1f7a45">↓{round(p["queda"])}%</b>' if p.get("queda") else ""
    antes = f'<s>{e(p["antes"])}</s>' if p.get("antes") else ""
    return f'''
<td width="33%" valign="top" style="padding:10px;border:1px solid #eeeaf2;border-radius:14px">
 <a href="{url}" style="text-decoration:none;color:#16141c;display:block">
  <img src="{e(foto)}" width="150" alt="{e(nome)}" style="display:block;width:100%;max-width:150px;height:auto;border-radius:10px;margin:0 auto 8px">
  <div style="font:600 13px/1.35 Arial,Helvetica,sans-serif;color:#16141c;height:54px;overflow:hidden">{e(nome)}</div>
  <div style="padding-top:6px;font:800 18px/1.1 Arial,Helvetica,sans-serif;color:#16141c;white-space:nowrap">{e(p["preco"])}</div>
  <div style="padding-top:3px;font:11px/1.3 Arial,Helvetica,sans-serif;color:#8a8696;white-space:nowrap">{antes}{queda}</div>
 </a>
</td>'''


def top3() -> list[dict]:
    import email_inauguracao as ei
    return ei.top3()


def montar(p: dict | None, destaques: list[dict], fotos: dict, sair_url: str = "",
           sino_src: str = ea.TOPO_URL) -> str:
    e = html.escape
    hoje = datetime.now().strftime("%d/%m")
    if p and p.get("nome"):
        pedido = (f'Você pediu para eu vigiar <b>{e(ea._curto(p["nome"], 60))}</b>'
                  + (f' (hoje: <b style="white-space:nowrap">{e(p["preco"])}</b>)' if p.get("preco") else "")
                  + ". Quando o preço cair, eu te escrevo na hora.")
    else:
        pedido = "Você pediu para eu avisar quando o preço cair. Quando cair, eu te escrevo na hora."
    cards = "".join(_cartao(d, fotos.get(str(d["id"])) or ea._miniatura(d["imagem"])) for d in destaques)
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><title>{e(assunto(p))}</title></head>
<body style="margin:0;padding:0;background:#ffffff">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(preheader())}&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;</div>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff"><tr><td align="center" style="padding:20px 12px">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px">
 <tr><td align="center" style="padding:0"><img src="{sino_src}" width="600" alt="" style="display:block;width:100%;max-width:600px;height:auto"></td></tr>
 <tr><td align="center" style="padding:6px 20px 0;font:12px/1 Arial,Helvetica,sans-serif;letter-spacing:4px;color:#6b6776">ACHADINHO TOTAL</td></tr>
 <tr><td align="center" style="padding:12px 20px 6px;font:800 28px/1.15 Arial,Helvetica,sans-serif;color:#16141c">Pronto. Agora eu<br><span style="color:#c8921c">fico de olho</span> pra você.</td></tr>
 <tr><td align="center" style="padding:6px 28px 8px;font:16px/1.55 Arial,Helvetica,sans-serif;color:#3b3845">{pedido}</td></tr>
 <tr><td align="center" style="padding:0 28px 18px;font:14px/1.55 Arial,Helvetica,sans-serif;color:#6b6776">
   Eu confiro o preço todo dia e comparo com o que eu mesmo já vi — não com o "de" inflado do vendedor. Só escrevo quando cair de verdade.</td></tr>
 <tr><td align="center" style="padding:4px 20px 8px;font:700 17px/1.2 Arial,Helvetica,sans-serif;color:#16141c">Enquanto isso, as maiores quedas de hoje ({hoje})</td></tr>
 <tr><td><table width="100%" cellpadding="0" cellspacing="6" style="border-collapse:separate"><tr>{cards}</tr></table></td></tr>
 <tr><td align="center" style="padding:22px 20px 8px">
   <a href="{SITE}/?{UTM}" style="display:inline-block;background:#f2c94c;color:#16141c;text-decoration:none;font:700 17px/1 Arial,Helvetica,sans-serif;padding:16px 34px;border-radius:999px">Ver todos os achadinhos →</a></td></tr>
 <tr><td align="center" style="padding:18px 34px 6px;font:italic 15px/1.55 Georgia,serif;color:#3b3845">
   "Eu fiz o site que eu queria ter: sem propaganda enganosa, sem precisar ficar caçando cupom. Se o preço cair, você fica sabendo."</td></tr>
 <tr><td align="center" style="padding:0 20px 20px;font:13px/1.4 Arial,Helvetica,sans-serif;color:#8a8696">— <b style="color:#3b3845">Fundador do Achadinho Total</b></td></tr>
 <tr><td align="center" style="padding:10px 24px 24px;border-top:1px solid #eeeaf2;font:11px/1.5 Arial,Helvetica,sans-serif;color:#9a96a3">
   Você recebeu isto porque deixou seu e-mail para receber avisos de queda de preço no Achadinho Total.<br>
   Contém links de afiliado: se você comprar, a loja me paga uma comissão, sem custo para você.<br>
   <a href="{e(sair_url or SITE + '/sair')}" style="color:#9a96a3">Não quero mais receber avisos</a> · <a href="{SITE}/privacidade" style="color:#9a96a3">Privacidade</a></td></tr>
</table></td></tr></table></body></html>'''


def pronto_para_enviar(p: dict | None, sair_url: str = "") -> tuple[str, str]:
    """(assunto, html) com as fotos ja' hospedadas por nos."""
    dest = top3()
    fotos = {str(d["id"]): ea.foto_hospedada(d) for d in dest}
    return assunto(p), montar(p, dest, fotos, sair_url=sair_url)


def enviar(para: str, assunto_: str, corpo: str, tag: str = "boas-vindas-teste") -> None:
    import json, urllib.request
    body = {"sender": {"name": "Achadinho Total", "email": "ofertas@achadinhototal.com.br"},
            "to": [{"email": para}], "subject": assunto_, "htmlContent": corpo, "tags": [tag]}
    r = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(body).encode(),
        headers={"api-key": ea._env("BREVO_API_KEY"), "content-type": "application/json",
                 "accept": "application/json", "user-agent": "achadinho-total/1.0"}, method="POST")
    with urllib.request.urlopen(r, timeout=30) as x:
        if tag.endswith("-teste"):
            print("enviado:", x.status, json.load(x))


if __name__ == "__main__":
    p, _ = ea.exemplo()
    a, corpo = pronto_para_enviar(p)
    saida = RAIZ / "_privado" / "email_boas_vindas.html"
    saida.write_text(corpo, encoding="utf-8")
    print("assunto:", a); print("preheader:", preheader()); print("previa:", saida)
    if "--teste" in sys.argv:
        enviar(sys.argv[sys.argv.index("--teste") + 1], a, corpo)
