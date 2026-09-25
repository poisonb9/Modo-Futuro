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
SITE = "https://achadinhototal.com.br"
REF = "lwtqfwkfcknzyyzmuymg"
TETO_RODADA = 80


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


def _enviados() -> dict:
    try:
        return json.loads(ENVIADOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def rodada(simular: bool = False) -> dict:
    sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "paginas"))
    sys.path.insert(0, str(RAIZ / "ferramentas"))
    from engine import alertas
    import email_alerta as tpl

    saidas = 0 if simular else tratar_saidas()
    insc = inscritos()
    res = {"saidas": saidas, "inscritos": sum(len(v) for v in insc.values()),
           "produtos_vigiados": len(insc), "com_sinal": 0, "enviados": 0, "falhas": 0}
    if not insc:
        return res
    sinais = {pid: v for pid, v in alertas.sinais_de_hoje().items() if pid in insc}
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
        for email in sorted(insc[pid]):
            chave = f"{hashlib.sha256(email.encode()).hexdigest()[:16]}|{pid}|{sinal}|{hoje}"
            if chave in env:
                continue
            if res["enviados"] >= TETO_RODADA:
                return res
            if simular:
                res["enviados"] += 1
                continue
            try:
                tpl.enviar(email, p, tpl.montar(p, sinal, sair_url=link_sair(email)), tag="alerta")
            except Exception as e:                       # noqa: BLE001
                res["falhas"] += 1
                print(f"alertas_email: falha ({type(e).__name__})")
                continue
            env[chave] = 1
            res["enviados"] += 1
            ENVIADOS.parent.mkdir(exist_ok=True)
            ENVIADOS.write_text(json.dumps(env, indent=0), encoding="utf-8")
    return res


def main() -> None:
    r = rodada(simular="--simular" in sys.argv)
    print("alertas_email:", " | ".join(f"{k} {v}" for k, v in r.items()))


if __name__ == "__main__":
    main()
