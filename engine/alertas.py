# -*- coding: utf-8 -*-
"""Avise-me quando cair: o alerta por produto, no Telegram da pessoa.

    python -m engine.alertas --colher            le' os /start novos do bot
    python -m engine.alertas --avisar            manda DM pra quem pediu, se caiu
    python -m engine.alertas --colher --avisar   a rodada da nuvem (precos.yml)

## POR QUE EXISTE (Bryan, 17/09/2026)

Selo 2 de CRITERIOS_DA_VITRINE.md: o botao "avise-me quando cair" no cartao.
E' o Keepa brasileiro para Ali + ML + Nike/Kabum juntos. Quem pede alerta
compra quando o alerta chega — e volta sozinho.

## COMO FUNCIONA, E POR QUE ASSIM

O botao abre `t.me/<bot>?start=alerta_<id do produto>`. O Telegram entrega
isso ao bot como `/start alerta_<id>`, com o chat_id da pessoa. Nao ha'
formulario, nao ha' contato guardado no site: o Telegram e' a identidade.

⚠️ SEM RECEPTOR LIGADO 24h. A maquina local nao aguenta processo em segundo
plano e o Actions nao fica de pe'. Entao a NUVEM COLHE de hora em hora
(`precos.yml` ja' roda 24x/dia): `getUpdates` com offset guardado, cada
/start vira uma linha em `estado/alertas.jsonl` (commitado). A confirmacao
chega em ate' 1h — o texto do /start no BotFather diz isso.

⛔ BOT PROPRIO, nunca o `bryan_fxv_fila_bot`: ligar getUpdates/webhook num
bot que outro processo ja' escuta e' 409 e briga de poll. O token vem de
`TELEGRAM_BOT_ALERTA` ou, na falta, `TELEGRAM_BOT_TOKEN` (o bot da
operacao — Bryan, 17/09); sem nenhum, tudo aqui e' no-op com aviso — e o
site nao mostra o botao.

## O QUE DISPARA O AVISO

Os mesmos sinais de `engine/sinais.py` (voltou_a_cair, novo_minimo,
ultima_chance) e o Recorde do cartao. Um aviso por pessoa/produto/sinal/dia,
registrado em `estado/alertas_enviados.json`.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
INSCRICOES = RAIZ / "estado" / "alertas.jsonl"
ENVIADOS = RAIZ / "estado" / "alertas_enviados.json"
OFFSET = RAIZ / "estado" / "alertas_offset.json"
ENV_TOKEN = "TELEGRAM_BOT_ALERTA"
ENV_TOKEN_RESERVA = "TELEGRAM_BOT_TOKEN"
ENV_BOT = "TELEGRAM_BOT_ALERTA_USERNAME"
API = "https://api.telegram.org/bot{token}/{metodo}"
PREFIXO = "alerta_"


def token() -> str | None:
    """TELEGRAM_BOT_ALERTA; sem ele, o bot da operacao (TELEGRAM_BOT_TOKEN)
    — decisao do Bryan em 17/09/2026: "voce ja' tem o token".

    ⚠️ Esse bot e' o mesmo do bot_telegram.py (/mais, /fila), que le' por
    getUpdates quando alguem o roda A MAO. Dois leitores no mesmo bot dao
    409 e um rouba as mensagens do outro: enquanto o "avise-me" colher na
    nuvem, o bot_telegram.py nao pode ficar escutando ao mesmo tempo."""
    return ((os.getenv(ENV_TOKEN) or "").strip()
            or (os.getenv(ENV_TOKEN_RESERVA) or "").strip() or None)


def bot_username() -> str | None:
    """O @ do bot, para o link do botao. Do ambiente; senao, pergunta ao
    Telegram (getMe) uma vez por processo."""
    v = (os.getenv(ENV_BOT) or "").strip()
    if v:
        return v.lstrip("@")
    t = token()
    if not t:
        return None
    try:
        r = requests.get(API.format(token=t, metodo="getMe"), timeout=20).json()
        return (r.get("result") or {}).get("username")
    except Exception:                                 # noqa: BLE001
        return None


def link_para(pid) -> str:
    """O link do botao "avise-me" deste produto ("" sem bot)."""
    u = bot_username()
    return f"https://t.me/{u}?start={PREFIXO}{pid}" if u else ""


def _chamar(metodo: str, **params) -> dict:
    t = token()
    if not t:
        raise RuntimeError(f"falta {ENV_TOKEN}")
    r = requests.post(API.format(token=t, metodo=metodo), json=params, timeout=40)
    r.raise_for_status()
    return r.json()


def _ler_jsonl(arq: Path) -> list[dict]:
    if not arq.exists():
        return []
    saida = []
    for linha in arq.read_text(encoding="utf-8").splitlines():
        try:
            saida.append(json.loads(linha))
        except ValueError:
            continue
    return saida


def inscricoes() -> dict[str, set[int]]:
    """{produto_id: {chat_id, ...}} — quem quer aviso de que."""
    saida: dict[str, set[int]] = {}
    for d in _ler_jsonl(INSCRICOES):
        if d.get("cancelado"):
            saida.get(str(d.get("produto")), set()).discard(int(d.get("chat") or 0))
            continue
        saida.setdefault(str(d.get("produto")), set()).add(int(d.get("chat") or 0))
    return saida


def interpretar(update: dict) -> tuple[int, str, str] | None:
    """(chat_id, produto_id, nome) de um update que e' `/start alerta_<id>`;
    None para qualquer outra coisa. ⚠️ So' texto que COMECA com /start e'
    inscricao: o resto do que a pessoa escrever nao vira nada."""
    msg = update.get("message") or {}
    texto = (msg.get("text") or "").strip()
    chat = (msg.get("chat") or {}).get("id")
    if not chat or not texto.startswith("/start"):
        return None
    partes = texto.split(maxsplit=1)
    if len(partes) < 2 or not partes[1].startswith(PREFIXO):
        return None
    pid = partes[1][len(PREFIXO):].strip()
    if not pid:
        return None
    nome = ((msg.get("from") or {}).get("first_name") or "").strip()
    return int(chat), pid, nome


def colher(updates: list[dict] | None = None) -> int:
    """Le' os /start novos e grava as inscricoes. Devolve quantas.
    `updates` injetado e' para teste; sem ele, chama getUpdates."""
    if updates is None:
        if not token():
            print(f"alertas: sem {ENV_TOKEN} — nada colhido")
            return 0
        offset = 0
        if OFFSET.exists():
            try:
                offset = int(json.loads(OFFSET.read_text(encoding="utf-8")).get("offset") or 0)
            except (ValueError, OSError):
                offset = 0
        r = _chamar("getUpdates", offset=offset, timeout=0, allowed_updates=["message"])
        updates = r.get("result") or []
    ja = inscricoes()
    n = 0
    maior = 0
    INSCRICOES.parent.mkdir(parents=True, exist_ok=True)
    with INSCRICOES.open("a", encoding="utf-8") as f:
        for u in updates:
            maior = max(maior, int(u.get("update_id") or 0))
            r = interpretar(u)
            if not r:
                continue
            chat, pid, nome = r
            if chat in ja.get(pid, set()):
                continue
            f.write(json.dumps({"chat": chat, "produto": pid, "nome": nome,
                                "quando": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                               ensure_ascii=False) + chr(10))
            ja.setdefault(pid, set()).add(chat)
            n += 1
            if token():
                try:
                    _chamar("sendMessage", chat_id=chat,
                            text="Combinado! Eu aviso aqui quando o preço cair. "
                                 "Eu confiro o preço toda hora.")
                except Exception as e:                # noqa: BLE001
                    print(f"alertas: confirmacao falhou pra {chat}: {e}")
    if maior and updates:
        OFFSET.write_text(json.dumps({"offset": maior + 1}), encoding="utf-8")
    print(f"alertas: {n} inscricao(oes) nova(s); {sum(len(v) for v in ja.values())} no total")
    return n


def _enviados() -> dict:
    if not ENVIADOS.exists():
        return {}
    try:
        return json.loads(ENVIADOS.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def texto_do_aviso(p: dict, sinal: str) -> str:
    """O aviso: fato medido, preco, link. Uma mensagem de texto (Hormozi)."""
    frases = {
        "voltou_a_cair": "voltou a cair",
        "novo_minimo": "está no menor preço que eu já vi",
        "ultima_chance": "subiu — mas ainda está abaixo do que já esteve",
        "recorde": "bateu o menor preço da história aqui",
    }
    linhas = [f"📉 {p.get('nome', '')}", f"{frases.get(sinal, sinal)}: {p.get('preco', '')}"]
    if p.get("antes"):
        linhas.append(f"já esteve a {p['antes']}")
    if p.get("link"):
        linhas += ["", p["link"]]
    return chr(10).join(linhas)


def avisar(sinais_por_produto: dict[str, tuple[str, dict]],
           enviar=None) -> int:
    """{produto_id: (sinal, cartao)} -> DM pra cada inscrito, uma vez por
    pessoa/produto/sinal/dia. `enviar(chat, texto)` injetado e' para teste.
    Devolve quantos avisos saíram."""
    insc = inscricoes()
    if not insc:
        return 0
    hoje = date.today().isoformat()
    env = _enviados()
    if enviar is None:
        if not token():
            print(f"alertas: sem {ENV_TOKEN} — nada avisado")
            return 0

        def enviar(chat, texto):
            _chamar("sendMessage", chat_id=chat, text=texto, disable_web_page_preview=False)
    n = 0
    for pid, (sinal, p) in sinais_por_produto.items():
        for chat in sorted(insc.get(str(pid), set())):
            chave = f"{chat}|{pid}|{sinal}|{hoje}"
            if chave in env:
                continue
            try:
                enviar(chat, texto_do_aviso(p, sinal))
            except Exception as e:                    # noqa: BLE001
                print(f"alertas: aviso falhou pra {chat}: {e}")
                continue
            env[chave] = 1
            n += 1
    ENVIADOS.parent.mkdir(parents=True, exist_ok=True)
    ENVIADOS.write_text(json.dumps(env, indent=0), encoding="utf-8")
    print(f"alertas: {n} aviso(s) enviado(s)")
    return n


def sinais_de_hoje() -> dict[str, tuple[str, dict]]:
    """Os produtos com sinal hoje, no formato de `avisar`. Usa
    `engine/sinais.py` sobre a serie — a mesma leitura do canal."""
    from . import sinais as _s
    saida: dict[str, tuple[str, dict]] = {}
    for s in _s.de_hoje():
        pid = str(s.get("id") or "")
        if pid and s.get("tipo") in ("voltou_a_cair", "novo_minimo", "ultima_chance"):
            reg = s.get("registro") or {}
            cartao = {"nome": reg.get("nome", ""), "link": reg.get("link", ""),
                      "preco": f"R$ {float(s.get('hoje') or 0):.2f}".replace(".", ","),
                      "antes": (f"R$ {float(s.get('maior') or 0):.2f}".replace(".", ",")
                                if s.get("maior") else "")}
            saida[pid] = (s["tipo"], cartao)
    return saida


def main() -> None:
    import argparse
    a = argparse.ArgumentParser(description="avise-me quando cair")
    a.add_argument("--colher", action="store_true")
    a.add_argument("--avisar", action="store_true")
    o = a.parse_args()
    if o.colher:
        colher()
    if o.avisar:
        avisar(sinais_de_hoje())
    if not (o.colher or o.avisar):
        insc = inscricoes()
        print(f"{sum(len(v) for v in insc.values())} inscricao(oes) em {len(insc)} produto(s)")


if __name__ == "__main__":
    main()
