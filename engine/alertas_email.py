# -*- coding: utf-8 -*-
"""Avise-me por E-MAIL: quem deixou o e-mail no cartao recebe o aviso de queda.

    python -X utf8 -m engine.alertas_email            a rodada (tarefa agendada, de hora em hora)
    python -X utf8 -m engine.alertas_email --simular  diz quantos sairiam, sem mandar nada

⛔ RODA NA MAQUINA LOCAL, NUNCA NA NUVEM. O repositorio e os logs do Actions
sao PUBLICOS e isto mexe com e-mail de gente (LGPD). A lista vem do Supabase
com a chave mestra do `.env`; o registro do que saiu fica em `_privado/`
(fora do git); o log so' tem contagens, nunca um endereco.

A cada rodada:
  1. SAIDAS primeiro: cada pedido da pagina /sair com assinatura certa marca
     `contato.saiu_em`. Quem pediu pra sair nao recebe nem mais este.
  2. Os sinais de hoje (`alertas.sinais_de_hoje`, os MESMOS do Telegram) x
     quem pediu aviso daquele produto.
  3. Um e-mail por pessoa/produto/sinal/dia (mesma regra do Telegram), com
     teto por rodada abaixo do limite diario do Brevo (300).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENV = RAIZ / ".env"
ENVIADOS = RAIZ / "_privado" / "alertas_email_enviados.json"
BOAS_VINDAS = RAIZ / "_privado" / "boas_vindas_enviados.json"
SITE = "https://achadinhototal.com.br"
REF = "lwtqfwkfcknzyyzmuymg"
TETO_RODADA = 80
# produto "geral" = inscrito no quadro do Telegram (sem produto escolhido)
GERAL = "geral"


def _env(nome: str) -> str:
    for l in ENV.read_text(encoding="utf-8").splitlines():
        if l.startswith(nome + "="):
            return l.split("=", 1)[1].strip()
    return ""


def _segredo() -> bytes:
    """Chave da assinatura do link de sair. Nasce uma vez e fica no `.env`."""
    s = _env("ALERTA_EMAIL_SEGREDO")
    if not s:
        s = secrets.token_hex(32)
        with ENV.open("a", encoding="utf-8") as f:
            f.write(f"\nALERTA_EMAIL_SEGREDO={s}\n")
    return s.encode()


def assinatura(email: str) -> str:
    return hmac.new(_segredo(), email.strip().lower().encode(), hashlib.sha256).hexdigest()[:32]


def link_sair(email: str) -> str:
    e = email.strip().lower()
    return f"{SITE}/sair?" + urllib.parse.urlencode({"e": e, "s": assinatura(e)})


def _sql(q: str) -> list:
    r = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{REF}/database/query",
        data=json.dumps({"query": q}).encode(),
        headers={"Authorization": f"Bearer {_env('SUPABASE_PAT')}",
                 "Content-Type": "application/json", "user-agent": "achadinho-total/1.0"},
        method="POST")
    with urllib.request.urlopen(r, timeout=60) as x:
        return json.load(x)


def _lit(v: str) -> str:
    return "'" + str(v).replace("'", "''") + "'"


def tratar_saidas() -> int:
    n = 0
    for d in _sql("select id, lower(email) email, assinatura from saida_email "
                  "where tratado_em is null order by id limit 500"):
        valida = hmac.compare_digest(d["assinatura"], assinatura(d["email"]))
        if valida:
            _sql(f"update contato set saiu_em = now() where lower(email) = {_lit(d['email'])} "
                 "and saiu_em is null")
            n += 1
        _sql(f"update saida_email set tratado_em = now() where id = {int(d['id'])}")
    return n


def inscritos() -> dict[str, set[str]]:
    """{produto_id: {emails ativos que pediram aviso dele}}."""
    out: dict[str, set[str]] = {}
    for d in _sql("select distinct lower(email) email, produto from contato "
                  "where email is not null and saiu_em is null and produto is not null"):
        out.setdefault(str(d["produto"]), set()).add(d["email"])
    return out


def _enviados(arq: Path = ENVIADOS) -> dict:
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _hash(email: str) -> str:
    return hashlib.sha256(email.encode()).hexdigest()[:16]


def boas_vindas(insc: dict[str, set[str]], simular: bool, teto: int) -> int:
    """UMA vez por pessoa: o e-mail de boas-vindas (ferramentas/email_boas_vindas.py).
    O produto citado e' o primeiro que ela pediu para vigiar."""
    import email_boas_vindas as bv
    import publicar_bio as pb
    ja = _enviados(BOAS_VINDAS)
    pedido: dict[str, str] = {}
    for pid, emails in sorted(insc.items()):
        for em in emails:
            pedido.setdefault(em, pid)
    novos = [em for em in sorted(pedido) if _hash(em) not in ja][:teto]
    if not novos or simular:
        return len(novos)
    cat = {str(p.get("id")): p for p in pb.produtos_todos()}
    import email_isca as isca
    n = 0
    for em in novos:
        p = cat.get(pedido[em])
        if pedido[em] == GERAL:
            # ⭐ 04/10/2026: inscrito do quadro geral cita a maior queda de hoje
            p = max(cat.values(), key=lambda c: float(c.get("queda") or 0), default=None)
        try:
            # ⭐ 28/09/2026: quem pediu a ISCA de um canal (bio; ferramentas/
            # email_isca.py) recebe o e-mail do canal, nao o boas-vindas de preco. Sem receitas
            # bastantes ainda: espera (nao marca como enviado).
            if pedido[em] in isca.PRODUTOS:
                pronto = isca.pronto_para_enviar(pedido[em], sair_url=link_sair(em))
                if not pronto:
                    continue
                a, corpo = pronto
            else:
                a, corpo = bv.pronto_para_enviar(p, sair_url=link_sair(em))
            bv.enviar(em, a, corpo, tag="boas-vindas")
        except Exception as e:                           # noqa: BLE001
            print(f"alertas_email: boas-vindas falhou ({type(e).__name__})")
            continue
        ja[_hash(em)] = date.today().isoformat()
        n += 1
        BOAS_VINDAS.parent.mkdir(exist_ok=True)
        BOAS_VINDAS.write_text(json.dumps(ja, indent=0), encoding="utf-8")
    return n


BUSCAS_RESPONDIDAS = RAIZ / "_privado" / "buscas_respondidas.json"


def _br(v) -> str:
    return f"{float(v):.2f}".replace(".", ",")


def responder_buscas(simular: bool, teto: int = 30) -> int:
    """⭐ 05/10/2026 (dono: "nao achou? deixe seu e-mail e eu rastreio o melhor
    preco pra voce"). Contato com produto "busca:<termo>" recebe UMA vez os 4
    mais baratos que o catalogo inteiro (supabase/15, buscar_catalogo) achar.
    Nada achado = nao manda nada e tenta de novo amanha (o catalogo muda todo dia)."""
    import html as _h
    ja = _enviados(BUSCAS_RESPONDIDAS)
    pedidos = _sql("select distinct lower(email) email, produto from contato where email is not null "
                   "and saiu_em is null and produto like 'busca:%'")
    n = 0
    for d in pedidos:
        termo = d["produto"].split(":", 1)[1].strip()
        chave = f"{_hash(d['email'])}|{termo.lower()}"
        if chave in ja or n >= teto or len(termo) < 2:
            continue
        achados = _sql(f"select * from buscar_catalogo({_lit(termo)})")[:12]
        # variacao de sabor/cor vem com o MESMO nome (whey: 4x o mesmo pote) — 1 de cada
        unicos, vistos = [], set()
        for p in sorted(achados, key=lambda p: float(p["preco"])):
            if p["nome"].lower()[:45] not in vistos:
                vistos.add(p["nome"].lower()[:45])
                unicos.append(p)
        achados = unicos[:4]
        if not achados:
            continue
        if simular:
            n += 1
            continue
        linhas = "".join(
            f'<tr><td style="padding:10px 0;border-bottom:1px solid #eee">'
            f'<a href="{_h.escape(p["link"])}" style="color:#16141c;text-decoration:none">'
            f'<b>{_h.escape(p["nome"][:80])}</b><br>'
            f'<span style="font-size:18px;font-weight:700">R$ {_br(p["preco"])}</span>'
            f' <span style="color:#6b6776">· {_h.escape(p["loja"])}</span></a></td></tr>'
            for p in achados)
        corpo = (f'<div style="font-family:system-ui,sans-serif;max-width:520px;margin:auto;color:#16141c">'
                 f'<h2>Achei “{_h.escape(termo)}” pra você</h2>'
                 f'<p style="color:#6b6776">Os mais baratos de hoje nas lojas parceiras, preço conferido hoje.</p>'
                 f'<table style="width:100%;border-collapse:collapse">{linhas}</table>'
                 f'<p style="font-size:12px;color:#6b6776">Contém links de afiliado. '
                 f'<a href="{link_sair(d["email"])}">Não quero mais receber</a></p></div>')
        try:
            import email_boas_vindas as bv
            bv.enviar(d["email"], f"🔎 Achei {termo[:40]} pra você", corpo, tag="busca")
        except Exception as e:  # noqa: BLE001
            print(f"alertas_email: busca falhou ({type(e).__name__})")
            continue
        ja[chave] = date.today().isoformat()
        BUSCAS_RESPONDIDAS.parent.mkdir(exist_ok=True)
        BUSCAS_RESPONDIDAS.write_text(json.dumps(ja, indent=0), encoding="utf-8")
        n += 1
    return n


def rodada(simular: bool = False) -> dict:
    sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "paginas"))
    sys.path.insert(0, str(RAIZ / "ferramentas"))
    from engine import alertas
    import email_alerta as tpl

    saidas = 0 if simular else tratar_saidas()
    try:
        buscas = responder_buscas(simular)
    except Exception as e:  # noqa: BLE001 — a resposta de busca nunca derruba os alertas
        print(f"alertas_email: buscas nao respondidas ({type(e).__name__})")
        buscas = 0
    insc = inscritos()
    res = {"saidas": saidas, "buscas": buscas, "inscritos": sum(len(v) for v in insc.values()),
           "produtos_vigiados": len(insc), "boas_vindas": 0, "com_sinal": 0,
           "enviados": 0, "falhas": 0}
    if not insc:
        return res
    res["boas_vindas"] = boas_vindas(insc, simular, TETO_RODADA // 2)
    todos_sinais = alertas.sinais_de_hoje()
    sinais = {pid: v for pid, v in todos_sinais.items() if pid in insc}
    # ⭐ 04/10/2026 (dono: e-mail no quadro do Telegram): quem se inscreveu no
    # quadro GERAL recebe, no maximo uma vez por dia, o primeiro sinal do dia
    # (a mesma lista do Telegram). Mesma regra de saida e de teto.
    if insc.get(GERAL) and todos_sinais:
        pid0 = next(iter(todos_sinais))
        sinais.setdefault(pid0, todos_sinais[pid0])
        insc = dict(insc)
        insc[pid0] = set(insc.get(pid0, set())) | {
            em for em in insc[GERAL] if f"{_hash(em)}|{GERAL}|{date.today().isoformat()}" not in _enviados()}
    res["com_sinal"] = len(sinais)
    if not sinais:
        return res
    import publicar_bio as pb
    cat = {str(p.get("id")): p for p in pb.produtos_todos()}
    hoje = date.today().isoformat()
    env = _enviados()
    for pid, (sinal, cartao) in sinais.items():
        p = dict(cat.get(pid) or {}, id=pid)
        for k in ("nome", "link", "preco", "antes"):
            p.setdefault(k, cartao.get(k, ""))
        if not p.get("nome") or not p.get("preco"):
            continue
        foto = "" if simular else tpl.foto_hospedada(p)
        for email in sorted(insc[pid]):
            chave = f"{_hash(email)}|{pid}|{sinal}|{hoje}"
            if chave in env:
                continue
            if res["enviados"] >= TETO_RODADA:
                return res
            if simular:
                res["enviados"] += 1
                continue
            try:
                tpl.enviar(email, p, tpl.montar(p, sinal, sair_url=link_sair(email),
                                                foto=foto), tag="alerta")
            except Exception as e:                       # noqa: BLE001
                res["falhas"] += 1
                print(f"alertas_email: falha ({type(e).__name__})")
                continue
            env[chave] = 1
            if email in insc.get(GERAL, ()):
                env[f"{_hash(email)}|{GERAL}|{hoje}"] = 1
            res["enviados"] += 1
            ENVIADOS.parent.mkdir(exist_ok=True)
            ENVIADOS.write_text(json.dumps(env, indent=0), encoding="utf-8")
    return res


def main() -> None:
    r = rodada(simular="--simular" in sys.argv)
    print("alertas_email:", " | ".join(f"{k} {v}" for k, v in r.items()))


if __name__ == "__main__":
    main()
