# -*- coding: utf-8 -*-
"""E-mail de ALERTA DE PRECO do Achadinho Total — o "avise-me" por e-mail.

    python ferramentas/email_alerta.py                    previa com um produto real que caiu hoje
    python ferramentas/email_alerta.py --produto ID       previa com esse produto
    python ferramentas/email_alerta.py --teste EMAIL      manda UM de teste para EMAIL

Quem deixou o e-mail no "avise-me" do site (tabela `contato`, com o produto)
recebe ESTE e-mail quando o produto dispara um dos sinais de
`engine.alertas.sinais_de_hoje` — os mesmos do aviso no Telegram.

Um produto por e-mail, um motivo so': o preco que a pessoa pediu para vigiar
caiu. Assunto com o produto e o preco (o motivo de abrir esta' no assunto);
o sino em cima e' a marca do aviso. Clique vai DIRETO ao link de afiliado
(regra do dono, 24/09). Tabela e estilo em linha: e-mail nao roda CSS moderno.

⛔ Envio para a LISTA nao sai daqui. So' previa e teste para um endereco.
"""
import base64, html, json, sys, urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "paginas"))
SITE = "https://achadinhototal.com.br"
UTM = "utm_source=email&utm_medium=alerta&utm_campaign=alerta_preco"
SINO_URL = f"{SITE}/baloes/email_sino.png"
# ⭐ 25/09: topo animado (sino + confete + serpentinas). 1o quadro ja' e' bonito
# parado, porque o Outlook do PC so' mostra ele.
TOPO_URL = f"{SITE}/baloes/email_topo_festa.gif"
SINO_LOCAL = RAIZ / "_privado" / "camada" / "ativos" / "email_sino.webp"

FRASE = {
    "voltou_a_cair": "voltou a cair",
    "novo_minimo": "está no menor preço que eu já vi",
    "ultima_chance": "subiu um pouco, mas ainda está abaixo do que já esteve",
    "recorde": "bateu o menor preço da história aqui",
}


def _curto(nome: str, n: int = 42) -> str:
    return nome if len(nome) <= n else nome[:n - 2].rsplit(" ", 1)[0] + "…"


def assunto(p: dict) -> str:
    return f"🔔 Caiu: {_curto(p['nome'], 34)} por {p['preco']}"


def preheader(p: dict) -> str:
    base = "Você pediu para eu avisar."
    return f"{base} Já esteve a {p['antes']}." if p.get("antes") else base


def _miniatura(u: str) -> str:
    if ("aliexpress-media.com" in u or "alicdn.com" in u) and u.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")):
        return u + "_350x350.jpg"
    return u


REF = "lwtqfwkfcknzyyzmuymg"
BALDE = "email-fotos"
_CHAVE_SERVICO: list[str] = []


def _env(nome: str) -> str:
    for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith(nome + "="):
            return l.split("=", 1)[1].strip()
    return ""


def _chave_servico() -> str:
    """Chave de servico do Supabase, pedida na hora com a chave mestra (nao fica em disco)."""
    if not _CHAVE_SERVICO:
        r = urllib.request.Request(f"https://api.supabase.com/v1/projects/{REF}/api-keys?reveal=true",
            headers={"Authorization": "Bearer " + _env("SUPABASE_PAT"), "user-agent": "achadinho-total/1.0"})
        with urllib.request.urlopen(r, timeout=30) as x:
            _CHAVE_SERVICO.append(next(k["api_key"] for k in json.load(x) if k.get("name") == "service_role"))
    return _CHAVE_SERVICO[0]


def foto_hospedada(p: dict) -> str:
    """A foto do produto copiada para o NOSSO armazenamento (Supabase, balde
    publico `email-fotos`). ⭐ 25/09: a foto direto do AliExpress pode nao
    abrir em leitor de e-mail que busca imagem por servidor proprio (o Mail
    do iPhone). Falha aqui = devolve a original; o e-mail nunca deixa de sair."""
    orig = _miniatura(p.get("imagem") or "")
    if not orig:
        return ""
    try:
        import io
        from PIL import Image
        r = urllib.request.Request(orig, headers={"user-agent": "Mozilla/5.0"})
        with urllib.request.urlopen(r, timeout=30) as x:
            im = Image.open(io.BytesIO(x.read())).convert("RGB")
        im.thumbnail((480, 480))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=85, optimize=True)
        nome = "".join(c for c in str(p.get("id") or "x") if c.isalnum() or c in "-_")[:64] + ".jpg"
        k = _chave_servico()
        up = urllib.request.Request(f"https://{REF}.supabase.co/storage/v1/object/{BALDE}/{nome}",
            data=buf.getvalue(), method="POST",
            headers={"Authorization": "Bearer " + k, "apikey": k, "Content-Type": "image/jpeg",
                     "x-upsert": "true", "cache-control": "86400", "user-agent": "achadinho-total/1.0"})
        urllib.request.urlopen(up, timeout=30).close()
        return f"https://{REF}.supabase.co/storage/v1/object/public/{BALDE}/{nome}"
    except Exception:                                    # noqa: BLE001
        return orig


def montar(p: dict, sinal: str, sino_src: str = TOPO_URL, sair_url: str = "",
           foto: str = "") -> str:
    e = html.escape
    url = p.get("link") or f"{SITE}/?p={p['id']}&{UTM}"
    hora = datetime.now().strftime("%d/%m às %H:%M")
    queda = (f'&nbsp;<b style="color:#1f7a45">↓{round(p["queda"])}%</b>'
             if p.get("queda") else "")
    antes = (f'<div style="padding-top:4px;font:14px/1.3 Arial,Helvetica,sans-serif;color:#8a8696">'
             f'já esteve a <s>{e(p["antes"])}</s>{queda}</div>') if p.get("antes") else ""
    img = (f'<a href="{url}"><img src="{e(foto or _miniatura(p["imagem"]))}" width="240" alt="{e(_curto(p["nome"]))}" '
           f'style="display:block;width:240px;max-width:100%;height:auto;border-radius:14px;margin:0 auto"></a>'
           if p.get("imagem") else "")
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><title>{e(assunto(p))}</title></head>
<body style="margin:0;padding:0;background:#ffffff">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(preheader(p))}&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;</div>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff"><tr><td align="center" style="padding:20px 12px">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:520px">
 <tr><td align="center" style="padding:0"><img src="{sino_src}" width="520" alt="" style="display:block;width:100%;max-width:520px;height:auto"></td></tr>
 <tr><td align="center" style="padding:6px 20px 0;font:12px/1 Arial,Helvetica,sans-serif;letter-spacing:4px;color:#6b6776">ACHADINHO TOTAL</td></tr>
 <tr><td align="center" style="padding:12px 24px 4px;font:800 26px/1.2 Arial,Helvetica,sans-serif;color:#16141c">Você pediu, eu avisei:<br><span style="color:#c8921c">o preço caiu</span>.</td></tr>
 <tr><td align="center" style="padding:6px 28px 18px;font:16px/1.5 Arial,Helvetica,sans-serif;color:#3b3845">
   O produto que você me pediu para vigiar {e(FRASE.get(sinal, "mudou de preço"))}.</td></tr>
 <tr><td align="center" style="padding:18px 20px;border:1px solid #eeeaf2;border-radius:18px">
   {img}
   <div style="padding-top:12px;font:600 15px/1.4 Arial,Helvetica,sans-serif;color:#16141c">{e(_curto(p["nome"], 80))}</div>
   <div style="padding-top:8px;font:800 30px/1.1 Arial,Helvetica,sans-serif;color:#16141c;white-space:nowrap">{e(p["preco"])}</div>
   {antes}
   <div style="padding-top:18px"><a href="{url}" style="display:inline-block;background:#f2c94c;color:#16141c;text-decoration:none;font:700 17px/1 Arial,Helvetica,sans-serif;padding:16px 34px;border-radius:999px">Ver na loja →</a></div>
   <div style="padding-top:10px;font:12px/1.4 Arial,Helvetica,sans-serif;color:#9a96a3">Preço conferido em {hora}. Pode mudar a qualquer momento.</div>
 </td></tr>
 <tr><td align="center" style="padding:22px 20px 6px;font:15px/1.5 Arial,Helvetica,sans-serif;color:#3b3845">
   <a href="{SITE}/?{UTM}" style="color:#1f6fd1;font-weight:700;text-decoration:none">Ver outras quedas de hoje no site</a></td></tr>
 <tr><td align="center" style="padding:10px 24px 24px;font:11px/1.5 Arial,Helvetica,sans-serif;color:#9a96a3">
   Você recebeu isto porque pediu um aviso de queda de preço no Achadinho Total.<br>
   Contém link de afiliado: se você comprar, a loja me paga uma comissão, sem custo para você.<br>
   <a href="{e(sair_url or SITE + '/sair')}" style="color:#9a96a3">Não quero mais receber avisos</a> · <a href="{SITE}/privacidade" style="color:#9a96a3">Privacidade</a></td></tr>
</table></td></tr></table></body></html>'''


def exemplo(pid: str | None = None) -> tuple[dict, str]:
    """Um produto REAL para a previa: o pedido, ou o de maior queda com foto."""
    import publicar_bio as pb
    dados = pb.produtos_todos()
    if pid:
        p = next(x for x in dados if str(x.get("id")) == str(pid))
        return p, "voltou_a_cair"
    cand = [x for x in dados if x.get("imagem") and x.get("antes") and (x.get("queda") or 0) >= 10]
    cand.sort(key=lambda x: (-(x.get("vitrine_nota") or 0), -(x.get("queda") or 0)))
    return cand[0], "voltou_a_cair"


def enviar(para: str, p: dict, corpo: str, tag: str = "alerta-teste") -> None:
    k = next(l.split("=", 1)[1].strip() for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines()
             if l.startswith("BREVO_API_KEY="))
    body = {"sender": {"name": "Achadinho Total", "email": "ofertas@achadinhototal.com.br"},
            "to": [{"email": para}], "subject": assunto(p), "htmlContent": corpo,
            "tags": [tag]}
    r = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(body).encode(),
        headers={"api-key": k, "content-type": "application/json", "accept": "application/json",
                 "user-agent": "achadinho-total/1.0"}, method="POST")
    with urllib.request.urlopen(r, timeout=30) as x:
        if tag == "alerta-teste":
            print("enviado:", x.status, json.load(x))


if __name__ == "__main__":
    pid = sys.argv[sys.argv.index("--produto") + 1] if "--produto" in sys.argv else None
    p, sinal = exemplo(pid)
    # previa local: o sino embutido (a URL publica so' existe depois de publicar o site)
    from PIL import Image
    import io
    sino = "data:image/gif;base64," + base64.b64encode(
        (RAIZ / "paginas" / "baloes" / "email_topo_festa.gif").read_bytes()).decode()
    saida = RAIZ / "_privado" / "email_alerta.html"
    saida.write_text(montar(p, sinal, sino), encoding="utf-8")
    print("assunto:", assunto(p)); print("preheader:", preheader(p)); print("previa:", saida)
    if "--teste" in sys.argv:
        enviar(sys.argv[sys.argv.index("--teste") + 1], p, montar(p, sinal, foto=foto_hospedada(p)))
