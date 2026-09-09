# -*- coding: utf-8 -*-
"""Os melhores posts da semana, por canal — e de onde esse numero veio.

⚠️ POR QUE ISTO NAO LE' A VIEW DO BUFFER, que seria o obvio.

Ordem do Bryan em 08/09/2026: rodar um radar em cima dos 2 videos que mais
viralizaram na semana. A primeira ideia foi ranquear pela view do Buffer.
MEDIDO no mesmo dia, contra as views reais do app do TikTok:

    O plano real da SpaceX (Data Centers)     buffer 0    tiktok 338
    O segredo da rotina matinal inabalavel    buffer 0    tiktok 359
    DICA DE OURO PARA INICIANTES NA ACADEMIA  buffer 0    tiktok 142

Zero, zero e zero — em posts de 6 e 7 dias. Nao e' atraso: a metade que falta
nao chega depois. E onde ha' numero ele nao guarda proporcao com o real: numa
leitura anterior, 240 contra 338 (0,71), 64 contra 359 (0,18), 8 contra 142
(0,06).

⚠️ RAZOES DE 0,06 A 0,71 QUEREM DIZER QUE NEM A ORDEM SE PRESERVA. Ranquear
por esse campo e' quase sortear — e a escolha manda baixar 5 fontes e gastar
corte em cima dela.

## AS DUAS FONTES, NESTA ORDEM

    MANUAL    `estado/views_manuais.json`, preenchido a partir da print do
              perfil que o Bryan manda. E' o numero REAL do TikTok. Decisao
              dele em 08/09: "2 com a 1".

    CURTIDA   reserva automatica, das semanas em que a print nao vier. O
              Buffer entrega curtida de verdade — foi com ela que se mediu
              que o @semanestesia engaja 7x mais que os outros.

⚠️ A FONTE USADA VAI SEMPRE NA RESPOSTA. Um ranking de curtida apresentado
como se fosse de view e' pior que nao ter ranking: quem le' decide achando
que sabe. Ver `melhores()`, que devolve (lista, fonte, aviso).
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from engine import seguidores  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
MANUAL = RAIZ / "estado" / "views_manuais.json"
DESEMPENHO = RAIZ / "desempenho.jsonl"

# Depois disto a print manual e' velha demais pra chamar de "a semana".
VALIDADE_DIAS = 10

# Idade minima do post pra metrica valer. Regra do Bryan em 08/09 ("com 3-4
# dias voce ja' consegue buscar"), confirmada na medicao: a disponibilidade
# sobe de 15% (0-1 dia) para 55% (3-4 dias).
IDADE_MINIMA_DIAS = 3


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _do_manual(canal: str):
    try:
        d = json.loads(MANUAL.read_text(encoding="utf-8"))
    except Exception:
        return None, "sem arquivo de views manuais"
    bloco = d.get(canal)
    if not bloco or not bloco.get("posts"):
        return None, f"sem print recente do {canal}"
    quando = _dt(bloco.get("medido_em"))
    if quando:
        dias = (datetime.now(timezone.utc) - quando).days
        if dias > VALIDADE_DIAS:
            return None, (f"print do {canal} tem {dias} dias (limite "
                          f"{VALIDADE_DIAS}) — velha demais pra 'a semana'")
    postos = sorted(bloco["posts"], key=lambda p: -int(p.get("views", 0)))
    return postos, ""


def _da_curtida(canal: str):
    """Reserva: curtida do Buffer, uma leitura por post (a mais recente)."""
    if not DESEMPENHO.exists():
        return None, "sem desempenho.jsonl"
    agora = datetime.now(timezone.utc)
    ult = {}
    for linha in DESEMPENHO.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(linha)
        except Exception:
            continue
        if r.get("canal") != canal or not r.get("post_id"):
            continue
        pub = _dt(r.get("publicado_em"))
        if not pub or (agora - pub).days < IDADE_MINIMA_DIAS:
            continue
        p = ult.get(r["post_id"])
        if not p or r.get("lido_em", "") > p.get("lido_em", ""):
            ult[r["post_id"]] = r
    postos = [{"titulo": r.get("titulo", ""), "curtidas": r.get("curtidas", 0)}
              for r in ult.values()]
    if not postos:
        return None, f"nenhum post do {canal} com {IDADE_MINIMA_DIAS}+ dias"
    postos.sort(key=lambda p: -int(p.get("curtidas", 0)))
    return postos, ""


def _juntar_repetidos(postos: list[dict]) -> list[dict]:
    """Um post so' entra uma vez, mesmo tendo entrado por duas fontes.

    ⚠️ MEDIDO em 08/09/2026, e o efeito era o pior possivel: os "2 melhores"
    do @modofuturo vieram

        2473  As regras extremas para entrar na fabrica mais limpa
        2473  As regras extremas para entrar na fabrica mais limpa

    O MESMO post, duas vezes. Ele tinha entrado pela print (titulo curto, em
    caixa alta) e pelo export do Studio (titulo + descricao colados). Sao
    textos diferentes, entao o registro os tratou como dois posts.

    Consequencia: o ciclo enviesaria a busca com UM sinal achando que tinha
    dois — e o segundo melhor de verdade nunca seria considerado. Um ranking
    que repete o primeiro colocado nao e' um ranking de dois.

    A regra e' a mesma da dedup de publicacao: uma chave e' a outra quando
    uma e' PREFIXO da outra. O titulo da print e' prefixo do titulo do
    export, porque o export cola a descricao no fim.
    """
    vistos: list[dict] = []
    for p in sorted(postos, key=lambda x: -int(x.get("views", 0) or 0)):
        chave = _norm(p.get("titulo", ""))
        if not chave:
            continue
        for v in vistos:
            k = _norm(v["titulo"])
            # piso de 20 pra "bolo" nao virar prefixo de meio canal
            if len(chave) >= 20 and len(k) >= 20 and (
                    chave.startswith(k) or k.startswith(chave)):
                # fica o MAIOR numero e o titulo MAIS CURTO — o curto e' o
                # titulo de verdade; o longo tem a descricao grudada.
                v["views"] = max(int(v.get("views", 0) or 0),
                                 int(p.get("views", 0) or 0))
                if len(p.get("titulo", "")) < len(v["titulo"]):
                    v["titulo"] = p["titulo"]
                break
        else:
            vistos.append(dict(p))
    return sorted(vistos, key=lambda x: -int(x.get("views", 0) or 0))


def melhores(canal: str, n: int = 2):
    """Devolve (postos, fonte, aviso). `fonte` e' 'view_real' ou 'curtida'.

    ⚠️ NUNCA devolve numero sem dizer de onde ele veio. Ver o cabecalho.

    ⚠️ E DESDE 09/09/2026 o aviso tambem cobre o que a view NAO diz. Os 11
    posts do @modofuturo medidos um a um no Studio mostraram que view nao
    previu seguidor — os dois de 22/08 sao o caso limpo, mesmo dia e mesmo
    canal, e o de retencao PIOR converteu 28x mais. O ranking continua sendo
    por view (reordenar com n=11 e um outlier seria trocar sinal fraco por
    outro pior), mas quem o le' passa a ser avisado. Ver `engine/seguidores`.
    """
    postos, por_que = _do_manual(canal)
    if postos:
        postos, aviso = seguidores.anotar(_juntar_repetidos(postos)[:n], canal)
        return postos, "view_real", aviso
    postos, por_que2 = _da_curtida(canal)
    if postos:
        postos, aviso_seg = seguidores.anotar(_juntar_repetidos(postos)[:n], canal)
        aviso = (f"⚠️ SEM view real ({por_que}); ranqueado por CURTIDA. "
                 f"Curtida nao e' view — o ranking pode nao ser o mesmo.")
        return postos, "curtida", (aviso + " " + aviso_seg).strip()
    return [], "nenhuma", f"{por_que}; e {por_que2}"


def registrar_print(canal: str, posts: list[dict]) -> int:
    """Guarda os numeros lidos da print do perfil. Devolve quantos entraram.

    ⚠️ SUBSTITUI o bloco do canal, nao soma. A print e' um retrato do perfil
    naquele instante; misturar retratos de semanas diferentes criaria um
    ranking que nunca existiu em lugar nenhum.
    """
    try:
        d = json.loads(MANUAL.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    limpos = [{"titulo": p["titulo"], "views": int(p["views"])}
              for p in posts if p.get("titulo") and p.get("views") is not None]
    d[canal] = {"medido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "origem": "print do perfil no TikTok, lida pelo Bryan",
                "posts": limpos}
    MANUAL.parent.mkdir(parents=True, exist_ok=True)
    MANUAL.write_text(json.dumps(d, ensure_ascii=False, indent=1,
                                 sort_keys=True), encoding="utf-8")
    return len(limpos)
