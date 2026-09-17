# -*- coding: utf-8 -*-
"""Avise-me quando cair: colher /start, guardar, avisar uma vez. Sem rede.

## POR QUE EXISTE (17/09/2026) — selo 2 de CRITERIOS_DA_VITRINE.md

⭐ Casos: (1) so' `/start alerta_<id>` vira inscricao — qualquer outro texto
NAO (negativo por construcao); (2) a mesma pessoa duas vezes = 1 inscricao;
(3) o aviso sai UMA vez por pessoa/produto/sinal/dia, e so' pra quem pediu
AQUELE produto; (4) sem bot no ambiente, o link do botao e' "" (o site nao
mostra o botao) e colher/avisar sao no-op.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import alertas  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


def upd(i, chat, texto, nome="Ana"):
    return {"update_id": i, "message": {"text": texto, "chat": {"id": chat}, "from": {"first_name": nome}}}


tmp = Path(tempfile.mkdtemp())
orig = (alertas.INSCRICOES, alertas.ENVIADOS, alertas.OFFSET)
env_tok = os.environ.pop(alertas.ENV_TOKEN, None)
env_bot = os.environ.pop(alertas.ENV_BOT, None)
env_res = os.environ.pop(alertas.ENV_TOKEN_RESERVA, None)
try:
    alertas.INSCRICOES = tmp / "alertas.jsonl"
    alertas.ENVIADOS = tmp / "enviados.json"
    alertas.OFFSET = tmp / "offset.json"

    print("1. SO' /start alerta_<id> VIRA INSCRICAO")
    n = alertas.colher([upd(1, 111, "/start alerta_MLB1"),
                        upd(2, 222, "oi, tudo bem?"),
                        upd(3, 333, "/start"),
                        upd(4, 444, "/start outra_coisa"),
                        upd(5, 555, "alerta_MLB1")])
    insc = alertas.inscricoes()
    checar(n == 1 and insc == {"MLB1": {111}}, f"1 de 5 updates e' inscricao: {insc}")
    checar(json.loads(alertas.OFFSET.read_text())["offset"] == 6, "offset avanca para o ultimo update + 1")

    print()
    print("2. A MESMA PESSOA DUAS VEZES = 1")
    n = alertas.colher([upd(6, 111, "/start alerta_MLB1"), upd(7, 111, "/start alerta_777")])
    insc = alertas.inscricoes()
    checar(n == 1 and insc == {"MLB1": {111}, "777": {111}}, f"repetida ignorada, produto novo entra: {insc}")

    print()
    print("3. AVISO UMA VEZ POR PESSOA/PRODUTO/SINAL/DIA, SO' PRA QUEM PEDIU AQUELE PRODUTO")
    enviados = []
    cartao = {"nome": "Coador", "preco": "R$ 12,00", "antes": "R$ 15,00", "link": "https://x"}
    n = alertas.avisar({"MLB1": ("voltou_a_cair", cartao), "999": ("novo_minimo", cartao)},
                       enviar=lambda chat, texto: enviados.append((chat, texto)))
    checar(n == 1 and [c for c, _ in enviados] == [111], f"1 aviso, pro chat 111 ({[c for c, _ in enviados]})")
    checar("voltou a cair: R$ 12,00" in enviados[0][1] and "https://x" in enviados[0][1] and "R$ 15,00" in enviados[0][1],
           "o texto leva o fato, o preco, o 'ja esteve' e o link")
    n = alertas.avisar({"MLB1": ("voltou_a_cair", cartao)}, enviar=lambda c, t: enviados.append((c, t)))
    checar(n == 0 and len(enviados) == 1, "o mesmo sinal no mesmo dia NAO repete")
    n = alertas.avisar({"MLB1": ("novo_minimo", cartao)}, enviar=lambda c, t: enviados.append((c, t)))
    checar(n == 1, "sinal diferente no mesmo dia avisa")

    print()
    print("4. SEM BOT: link vazio, no-op")
    checar(alertas.link_para("MLB1") == "", "sem TELEGRAM_BOT_ALERTA o botao nao existe")
    checar(alertas.colher() == 0, "colher sem token = 0, sem estourar")
    os.environ[alertas.ENV_BOT] = "@AchadinhoTotalBot"
    checar(alertas.link_para("MLB1") == "https://t.me/AchadinhoTotalBot?start=alerta_MLB1",
           "com o @ no ambiente, o link e' o deep link do /start")
finally:
    alertas.INSCRICOES, alertas.ENVIADOS, alertas.OFFSET = orig
    os.environ.pop(alertas.ENV_BOT, None)
    if env_tok:
        os.environ[alertas.ENV_TOKEN] = env_tok
    if env_bot:
        os.environ[alertas.ENV_BOT] = env_bot
    if env_res:
        os.environ[alertas.ENV_TOKEN_RESERVA] = env_res

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
