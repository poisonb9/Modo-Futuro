# -*- coding: utf-8 -*-
"""E-mail de INAUGURACAO do Achadinho Total (24/09/2026).

    python ferramentas/email_inauguracao.py                 gera o HTML (previa)
    python ferramentas/email_inauguracao.py --teste EMAIL   manda UM para EMAIL

Estrutura pelo acervo (Maestros, e-mail de lancamento): assunto + preheader
trabalhando juntos; motivo concreto para abrir AGORA (as maiores quedas de
hoje, dado real -- nao promessa); produtos em destaque; uma linha de quem
garimpa (o toque pessoal); UM botao principal. Em tabela e estilo em linha:
e-mail nao roda CSS moderno. Arte de topo em PNG publicada em /baloes/.

⛔ Envio para a LISTA nao sai daqui: a lista ainda nao existe (contatos em
construcao). Este script so' gera a previa e o envio de TESTE.
"""
import json, sys, html, urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "paginas"))
SITE = "https://achadinhototal.com.br"
UTM = "utm_source=email&utm_medium=inauguracao&utm_campaign=inauguracao_2026_09"
ASSUNTO = "🎈 Inauguramos: eu garimpo, você paga menos"
PREHEADER = "As maiores quedas de preço de hoje, conferidas por mim. Sem enrolação."


def top3():
    import publicar_bio as pb
    dados = pb.produtos_todos()
    from engine import foto_julga
    # ⛔ a mesma guarda da capa: colagem e texto queimado NAO abrem e-mail
    # (1a previa trouxe a Luz LED da colagem "Desk/Stairs/Porch").
    cand = [p for p in dados if p.get("imagem") and (p.get("queda") or 0) >= 5 and p.get("antes")
            and foto_julga.serve_de_capa(p["imagem"], 7)]
    cand.sort(key=lambda p: (-(p.get("vitrine_nota") or 0), -(p.get("queda") or 0)))
    return cand[:3]


def miniatura(u):
    return u + "_350x350.jpg" if ("aliexpress-media.com" in u or "alicdn.com" in u) and u.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) else u


def cartao(p):
    e = html.escape
    url = f"{SITE}/?p={p['id']}&{UTM}"
    return f'''
<td width="33%" valign="top" style="padding:6px">
 <a href="{url}" style="text-decoration:none;color:#16141c">
  <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eeeaf2;border-radius:14px">
   <tr><td align="center" style="padding:10px"><img src="{e(miniatura(p['imagem']))}" width="150" alt="{e(p['nome'][:60])}" style="display:block;width:100%;max-width:150px;height:auto;border-radius:10px"></td></tr>
   <tr><td style="padding:0 12px;font:600 13px/1.35 Arial,Helvetica,sans-serif;color:#16141c;height:54px;vertical-align:top">{e(p['nome'][:58])}</td></tr>
   <tr><td style="padding:6px 12px 2px;font:800 20px/1.1 Arial,Helvetica,sans-serif;color:#16141c">{e(p['preco'])}</td></tr>
   <tr><td style="padding:0 12px 12px;font:12px/1.3 Arial,Helvetica,sans-serif;color:#8a8696"><s>{e(p['antes'])}</s> &nbsp;<b style="color:#1f7a45">↓ {round(p['queda'])}%</b></td></tr>
  </table>
 </a>
</td>'''


def montar():
    ps = top3()
    hora = datetime.now().strftime("%d/%m")
    cards = "".join(cartao(p) for p in ps)
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><title>{html.escape(ASSUNTO)}</title></head>
<body style="margin:0;padding:0;background:#ffffff">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{html.escape(PREHEADER)}&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;</div>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff"><tr><td align="center" style="padding:20px 12px">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px">
 <tr><td align="center"><a href="{SITE}/?{UTM}"><img src="{SITE}/baloes/email_inauguracao.png" width="600" alt="Inauguração do Achadinho Total" style="display:block;width:100%;max-width:600px;height:auto"></a></td></tr>
 <tr><td align="center" style="padding:8px 20px 0;font:12px/1 Arial,Helvetica,sans-serif;letter-spacing:4px;color:#6b6776">ACHADINHO TOTAL</td></tr>
 <tr><td align="center" style="padding:10px 20px 6px;font:800 30px/1.15 Arial,Helvetica,sans-serif;color:#16141c">Eu garimpo.<br>Você <span style="color:#c8921c">paga menos</span>.</td></tr>
 <tr><td align="center" style="padding:6px 28px 18px;font:16px/1.55 Arial,Helvetica,sans-serif;color:#3b3845">
   O Achadinho Total abriu as portas. Todo dia eu confiro o preço de mais de <b>1.600 produtos</b> em várias lojas e só mostro o que <b>caiu de verdade</b> — comparando com o que eu mesmo vi antes, não com o "de" inflado do vendedor.</td></tr>
 <tr><td align="center" style="padding:4px 20px 8px;font:700 17px/1.2 Arial,Helvetica,sans-serif;color:#16141c">As maiores quedas de hoje ({hora})</td></tr>
 <tr><td><table width="100%" cellpadding="0" cellspacing="0"><tr>{cards}</tr></table></td></tr>
 <tr><td align="center" style="padding:22px 20px 8px">
   <a href="{SITE}/?{UTM}" style="display:inline-block;background:#f2c94c;color:#16141c;text-decoration:none;font:700 17px/1 Arial,Helvetica,sans-serif;padding:16px 34px;border-radius:999px">Ver todos os achadinhos →</a></td></tr>
 <tr><td align="center" style="padding:18px 34px 6px;font:italic 15px/1.55 Georgia,serif;color:#3b3845">
   "Eu fiz o site que eu queria ter: sem propaganda enganosa, sem precisar ficar caçando cupom. Se o preço cair, você fica sabendo."</td></tr>
 <tr><td align="center" style="padding:0 20px 20px;font:13px/1.4 Arial,Helvetica,sans-serif;color:#8a8696">— quem garimpa no Achadinho Total</td></tr>
 <tr><td align="center" style="padding:16px 24px;border-top:1px solid #eeeaf2;font:14px/1.5 Arial,Helvetica,sans-serif;color:#3b3845">
   Quer saber na hora quando um produto cair? <a href="https://t.me/achadinhototal" style="color:#1f6fd1;font-weight:700;text-decoration:none">Entre no Telegram do Achadinho Total</a>.</td></tr>
 <tr><td align="center" style="padding:10px 24px 24px;font:11px/1.5 Arial,Helvetica,sans-serif;color:#9a96a3">
   Você está recebendo isto porque pediu para receber ofertas do Achadinho Total.<br>
   Contém links de afiliado: se você comprar, a loja me paga uma comissão, sem custo para você.<br>
   <a href="{{{{ unsubscribe }}}}" style="color:#9a96a3">Não quero mais receber</a> · <a href="{SITE}/privacidade" style="color:#9a96a3">Privacidade</a></td></tr>
</table></td></tr></table></body></html>'''


def enviar(para, corpo):
    k = next(l.split("=", 1)[1].strip() for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines() if l.startswith("BREVO_API_KEY="))
    body = {"sender": {"name": "Achadinho Total", "email": "ofertas@achadinhototal.com.br"},
            "to": [{"email": para}], "subject": ASSUNTO, "htmlContent": corpo, "tags": ["inauguracao-teste"]}
    r = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(body).encode(),
        headers={"api-key": k, "content-type": "application/json", "accept": "application/json",
                 "user-agent": "achadinho-total/1.0"}, method="POST")
    with urllib.request.urlopen(r, timeout=30) as x:
        print("enviado:", x.status, json.load(x))


if __name__ == "__main__":
    corpo = montar()
    saida = RAIZ / "_privado" / "email_inauguracao.html"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(corpo, encoding="utf-8")
    print("previa:", saida)
    if "--teste" in sys.argv:
        enviar(sys.argv[sys.argv.index("--teste") + 1], corpo)
