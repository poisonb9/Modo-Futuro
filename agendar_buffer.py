# -*- coding: utf-8 -*-
"""Enfileira clipes no Buffer, na ordem certa, respeitando o teto do plano.

POR QUE EXISTE
O plano gratuito do Buffer guarda no máximo 10 posts agendados por canal. Não
é limite de total, é de FILA: a cada post enviado, um slot volta. Então a fila
não precisa ser profunda — precisa ser reabastecida. Este script faz isso.

AS TRÊS REGRAS, todas pedidas pelo Bryan e todas com motivo:

1. ORDEM CRONOLÓGICA DENTRO DO MESMO VÍDEO-FONTE. Ordenar por nota embaralha a
   narrativa: no run #159 a nota 95 estava aos 141s do fonte, a 93 aos 1210s e
   a 92 aos 54s — o trecho dos 20 minutos ia ao ar antes do trecho do primeiro
   minuto. Ordena por `inicio_s`, que o `publicar_release.py` carrega até o
   manifesto.

2. UMA VAGA SEMPRE LIVRE. Enche até 9 dos 10, pro Bryan conseguir encaixar algo
   na mão sem precisar apagar nada.

3. RÓTULO DE IA SEMPRE MARCADO (`isAiGenerated`). A interface do Buffer não
   expõe esse campo — a API expõe. É a única forma de marcar esses vídeos.

DEDUPLICAÇÃO SEM REGISTRO LOCAL: compara o texto dos posts que já estão no
Buffer com a legenda do clipe. Arquivo de registro não serviria, porque este
script roda tanto na VPS quanto no runner do GitHub, e no runner ele nasce
vazio a cada execução.

Uso:
    python agendar_buffer.py --simular    # mostra o que faria, não manda nada
    python agendar_buffer.py              # enfileira de verdade
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

from engine import registro_clipes

from engine import buffer_cota as cota, dedup, estreia
from engine import adiados, rejeitados

API_BUFFER = "https://api.buffer.com/"
API_GITHUB = "https://api.github.com"
REPO = os.environ.get("GITHUB_REPO", "poisonb9/Modo-Futuro")

# Teto do plano gratuito, medido em 25/08/2026 (o app avisa "1 post left" com
# 9 na fila).
#
# RESERVA passou de 1 pra 0 em 25/08, a pedido do Bryan: ele prefere a fila
# sempre cheia. Se ele quiser encaixar algo na mão, apaga um post ou usa
# --reserva 1 numa rodada. A regra 2 lá em cima descreve o comportamento
# antigo e fica aqui como histórico da decisão.
LIMITE_FILA = 10
RESERVA_MANUAL = 0
# Teto de páginas por consulta de posts. Cada página é uma requisição, e o
# histórico só cresce — sem teto, a consulta fica mais cara a cada semana.
MAX_PAGINAS = 4

# Horários de postagem (São Paulo). O `addToQueue` usaria a agenda do canal no
# Buffer, que não reflete isto — então o agendamento é explícito.
# Cortado de 6 pra 5 slots em 26/08/2026, decisao do Bryan. Motivo medido: os
# dois melhores dias do canal tiveram 5 e 2 posts (medianas 726 e 434) e o dia
# de 15 posts foi o pior de julho (115). O slot das 13:07 foi o escolhido pra
# sair porque era o par mais apertado da grade (1h34 depois das 11:33), e em
# 26/08 os dois posts do meio-dia foram os piores medidos do dia (22 e 11).
# 29/08/2026: 5 -> 4. Saiu o slot das 20:50, que era o par mais apertado da
# grade (1h47 depois das 19:03) e o mais tarde do dia.
#
# E o 19:03 virou 19:30 no mesmo dia: o Bryan pediu **no minimo 3 horas** entre
# posts, e o par 16:27-19:03 dava 2h36. Com a mudanca o menor intervalo da
# grade passa a ser 3h03.
#
#   08:15  ->  11:33   3h18
#   11:33  ->  16:27   4h54
#   16:27  ->  19:30   3h03   (era 2h36)
#
# ⚠️ VARIACAO_MIN sorteia ±8 min em cada slot, entao o pior caso real e' 3h03
# menos 16 = 2h47. Se os 3h forem regra dura e nao alvo, o jeito de garantir
# e' aumentar a folga aqui, nao reduzir a variacao — ela existe pra nao
# parecer robo.
SLOTS_SP = [(8, 15), (11, 33), (16, 27), (19, 30)]
# Teto DURO de posts por dia (SP), contando o que ja' foi enviado. A grade
# sozinha nunca segurou o volume: 25/08 saiu com 8 posts e 26/08 com 11, ambos
# acima dos 6 slots que existiam. Isso acontece porque um slot que ja' disparou
# some de `scheduled`, e uma rodada seguinte do agendador enxerga o dia vazio.
#
# 29/08/2026: 5 -> 4, pedido do Bryan, pra ver se os posts com 0 view param.
# ⚠️ RESSALVA REGISTRADA NA HORA: os zeros medidos ate' aqui NAO sao de alcance,
# sao metrica velha do Buffer — todo post que mostrava 0 tinha `metricsUpdatedAt`
# ANTERIOR ao proprio `sentAt`, e o print do TikTok mostrava 347 e 373 onde o
# Buffer dizia 0. Cadencia nao deve mexer nisso. Se os zeros sumirem depois
# desta mudanca, desconfie de coincidencia antes de creditar a cadencia.
MAX_POR_DIA = 4
VARIACAO_MIN = 8      # minuto varia ±8 pra não parecer robô

# Intervalo MINIMO entre dois posts do mesmo dia, em horas. Ordem do Bryan em
# 29/08/2026. E' regra DURA, verificada depois do sorteio da variacao — nao um
# alvo que a grade tenta cumprir.
#
# A diferenca importa: com a grade sozinha, o par 16:27-19:30 da' 3h03, mas a
# variacao de ±8 em cada ponta pode virar 2h47. Foi o que aconteceu no
# primeiro agendamento de 29/08 (16:32 -> 19:22 = 2h50). Confiar na folga da
# grade e' confiar num sorteio.
INTERVALO_MIN_H = 3.0
FUSO_SP_H = 3         # America/Sao_Paulo = UTC-3

RAIZ = Path(__file__).resolve().parent


def _token_buffer() -> str:
    v = (os.environ.get("BUFFER_TOKEN") or "").strip()
    if v:
        return v
    arq = RAIZ / "buffer_token.txt"
    if arq.exists():
        return arq.read_text(encoding="utf-8").strip()
    sys.exit("Falta BUFFER_TOKEN (variável de ambiente ou buffer_token.txt).")


def _token_github() -> str:
    for nome in ("GITHUB_TOKEN", "GH_TOKEN"):
        v = (os.environ.get(nome) or "").strip()
        if v:
            return v
    arq = RAIZ / "github_token.txt"
    if arq.exists():
        return arq.read_text(encoding="utf-8").strip()
    sys.exit("Falta GITHUB_TOKEN — sem ele não dá pra ler o manifesto.")


def consultar(token: str, query: str, variaveis: dict | None = None) -> dict:
    # Orçamento ANTES da rede: em 25/08/2026 a conta bateu no rate limit de 24h
    # e a fila ficou intocável por um dia. Ver engine/buffer_cota.py.
    cota.checar(1)
    cota.registrar(1)
    r = requests.post(API_BUFFER,
                      headers={"Authorization": f"Bearer {token}",
                               "Content-Type": "application/json"},
                      json={"query": query, "variables": variaveis or {}},
                      timeout=180)
    d = r.json()
    if "errors" in d:
        raise RuntimeError(json.dumps(d["errors"], ensure_ascii=False)[:400])
    return d["data"]


def contexto_buffer(token: str, fresco: bool = False) -> tuple[str, str, list[dict]]:
    """Devolve (organizationId, channelId do TikTok, posts já agendados).

    `fresco=True` ignora o cache. QUEM VAI ESCREVER PRECISA DISSO.

    Em 29/08/2026 o agendador rodou logo depois de eu apagar e recriar posts,
    leu o cache de 15 minutos e nao enxergou o que ja' estava na fila —
    agendou "Por que o 3D V-Cache esquentava tanto?" DUAS VEZES, 16:31 e
    16:32. Duplicata e' a causa medida dos colapsos de alcance de 02/08 e
    25/08, entao o cache barato custou exatamente o que ele deveria proteger.

    Ler pode usar cache. Decidir o que agendar, nao: a dedup compara contra
    esta lista, e uma lista velha e' uma dedup cega.
    """
    org = consultar(token, "{ account { organizations { id } } }")
    org_id = org["account"]["organizations"][0]["id"]

    canais = consultar(token, """
      query($i: ChannelsInput!) { channels(input: $i) { id service name } }""",
      {"i": {"organizationId": org_id}})["channels"]
    tiktok = [c for c in canais if c["service"] == "tiktok"]
    if not tiktok:
        sys.exit("Nenhum canal TikTok conectado nesta conta do Buffer.")

    # GUARDA DE CANAL. Confere que o token abriu a conta que se esperava.
    #
    # Em 30/08/2026 o workflow `cortar_de_bruto.yml` cortou um PODCAST pro Sem
    # Anestesia e, no fim, chamou este script com o `secrets.BUFFER_TOKEN` —
    # que e' o do @modofuturo. Os clipes de neurociencia iriam pra fila do
    # canal de chips. So' nao foram porque eu enchi a fila ate' o teto do
    # plano na mao, minutos antes.
    #
    # As guardas locais nao pegariam: `estado/buffer_cota.json` e
    # `estado/rejeitados.json` estao no .gitignore, entao o runner nasce com
    # os dois vazios.
    #
    # Por que comparar o NOME do canal e nao o secret: o defeito nao e' "o
    # secret errado foi passado", e' "o token abriu um canal que nao e' o
    # deste corte". Comparar o destino real pega qualquer origem do erro —
    # secret trocado, secret renomeado, canal reconectado noutra conta.
    #
    # FALHA FECHADA de proposito: sem CANAL_ESPERADO nada muda (os disparos
    # antigos seguem valendo), mas COM ele um destino errado aborta antes de
    # publicar. Publicar no canal errado nao tem desfazer bonito: o post sai,
    # o alcance conta, e apagar deixa o video em 0 pra sempre.
    esperado = (os.environ.get("CANAL_ESPERADO") or "").strip().lower()
    if esperado:
        nomes = [(c.get("name") or "").strip().lower() for c in tiktok]
        if esperado not in nomes:
            sys.exit(
                f"CANAL ERRADO — abortando antes de publicar.\n"
                f"  esperado : {esperado}\n"
                f"  conectado: {', '.join(nomes) or '(nenhum)'}\n"
                f"  O BUFFER_TOKEN desta execucao abriu outra conta. Corrija o\n"
                f"  secret do canal antes de rodar de novo.")
        tiktok = [c for c in tiktok
                  if (c.get("name") or "").strip().lower() == esperado]
        print(f"canal confirmado: {tiktok[0].get('name')}")

    # Cache primeiro: a fila muda no máximo 4x/dia (é a cadência de postagem),
    # então reler a cada poucos minutos era desperdício puro.
    guardado = None if fresco else cota.cache_valido()
    if guardado is not None:
        return org_id, guardado["canal"], guardado["posts"]

    agendados, cursor, paginas = [], None, 0
    while True:
        paginas += 1
        if paginas > MAX_PAGINAS:
            print(f"  [!] parei em {MAX_PAGINAS} páginas pra não gastar orçamento; "
                  "a dedup usa o que veio (os mais recentes).")
            break
        d = consultar(token, """
          query($i: PostsInput!, $a: String) { posts(input: $i, after: $a) {
            pageInfo { hasNextPage endCursor }
            edges { node { id status text dueAt } } } }""",
          {"i": {"organizationId": org_id,
                 # "sent" JUNTO com "scheduled": a deduplicacao compara o texto
                 # dos posts que o Buffer ja' conhece, e clipe PUBLICADO tambem
                 # conta. Sem isso, um clipe que saiu de manha voltava pra fila
                 # a' tarde — republicacao acidental, o oposto do que o Bryan
                 # pediu. Aconteceu de verdade em 25/08/2026 com "A industria
                 # que controla todas as outras industrias".
                 "filter": {"status": ["scheduled", "sent"],
                            "channelIds": [tiktok[0]["id"]]}}, "a": cursor})["posts"]
        agendados += [e["node"] for e in d["edges"]]
        if not d["pageInfo"]["hasNextPage"]:
            break
        cursor = d["pageInfo"]["endCursor"]
    cota.guardar_cache({"canal": tiktok[0]["id"], "posts": agendados})
    return org_id, tiktok[0]["id"], agendados


def manifesto(token_gh: str, tag: str | None = None) -> dict:
    """Lê o manifesto.json das releases de clipes.

    Junta TODAS as releases `clipes-*`, não só a do mês: um clipe de fim de mês
    pode ser agendado no mês seguinte, e ele mora na release antiga.
    """
    h = {"Authorization": f"Bearer {token_gh}", "Accept": "application/vnd.github+json"}
    r = requests.get(f"{API_GITHUB}/repos/{REPO}/releases?per_page=100", headers=h, timeout=60)
    r.raise_for_status()
    tudo = {}
    for rel in r.json():
        if tag and rel["tag_name"] != tag:
            continue
        if not tag and not rel["tag_name"].startswith("clipes-"):
            continue
        for a in rel.get("assets", []):
            if a["name"] == "manifesto.json":
                try:
                    # `?t=` derruba o cache do CDN do GitHub. MEDIDO em 25/08/2026: o asset
                    # tinha 16 clipes no servidor e a URL sem parametro devolvia 11 — versao
                    # antiga. Sem isto o agendador ignora silenciosamente todo lote novo.
                    tudo.update(requests.get(
                        a["browser_download_url"] + f"?t={int(time.time())}",
                        timeout=60).json())
                except Exception as e:
                    print(f"  [!] manifesto de {rel['tag_name']} ilegível: {str(e)[:70]}")
    return tudo


def _primeira_linha(texto) -> str:
    """A primeira linha de uma legenda — que e' onde mora o titulo."""
    return str(texto or "").strip().split("
")[0]


def _chave_texto(t: str) -> str:
    """Normaliza pra comparar legenda de clipe com texto de post do Buffer.

    Sem acento, sem hashtag, sem pontuação, minúsculo. O Buffer às vezes
    devolve o texto com espaçamento diferente do que foi enviado, então
    comparação literal não serve.
    """
    # SO' A PRIMEIRA LINHA (o titulo). Antes a chave usava os 70 primeiros
    # caracteres do texto inteiro — e isso quebrou em 28/08/2026, quando as
    # legendas foram reescritas com a descricao premium: o titulo continuava
    # igual, o corpo mudou, e a chave mudou junto. Os 8 posts reescritos
    # ficaram INVISIVEIS pra dedup, e um deles foi reagendado em duplicata.
    #
    # O titulo e' o que identifica o clipe. A descricao e' editorial e muda —
    # amarrar a identidade a ela e' amarrar no que nao e' estavel.
    t = (t or "").split("\n")[0].split("#")[0]
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", t.lower())[:70]


def ordenar(clipes: dict) -> list[tuple[str, dict]]:
    """Ordem de postagem: por vídeo-fonte, e dentro dele por posição no original.

    Os vídeos-fonte entram na ordem em que foram publicados na release; dentro
    de cada um, o corte mais no início do vídeo vai primeiro. É a regra 1.
    """
    itens = list(clipes.items())
    primeira_aparicao = {}
    for _, v in itens:
        f = v.get("fonte") or ""
        d = v.get("publicado_em") or ""
        if f not in primeira_aparicao or d < primeira_aparicao[f]:
            primeira_aparicao[f] = d

    def chave(par):
        _, v = par
        # Republicacao vai pro FIM da fila, sempre. Sao clipes que ja' foram ao
        # ar uma vez (ou que foram tirados da fila por terem sido postados sem
        # rotulo de IA) e voltam pelo pipeline. Sem isto eles entrariam na
        # FRENTE, porque a ordenacao usa a data de publicacao na release e o
        # lote deles e' mais antigo — o oposto do que o Bryan pediu em 25/08.
        rep = 1 if v.get("republicacao") else 0
        # Adiado vai atras de TODO mundo, republicacao inclusive. A chave sai
        # da LEGENDA (titulo como reserva), igual ao `cabe()` — calcular pelo
        # titulo nao bate, e foi assim que tres clipes que o Bryan tinha
        # vetado entraram na fila em 27/08/2026. Ver engine/adiados.py.
        adi = 1 if adiados.adiado(
            _chave_texto(v.get("legenda") or v.get("titulo") or "")) else 0
        fonte = v.get("fonte") or ""
        # inicio_s ausente (clipe antigo, de antes do manifesto) cai pro fim do
        # seu grupo em vez de quebrar a ordenação
        inicio = v.get("inicio_s")
        return (adi, rep, primeira_aparicao.get(fonte, ""), fonte,
                float("inf") if inicio is None else float(inicio))

    return sorted(itens, key=chave)


def proximos_horarios(agendados: list[dict], quantos: int,
                      conhecidos: list[dict] | None = None
                      ) -> list[datetime.datetime]:
    """Próximos slots livres da grade, em horário de São Paulo.

    Pula slot já ocupado (compara pela HORA, não pelo minuto exato, porque o
    minuto varia de propósito), slot que já passou, e dia que já bateu
    `MAX_POR_DIA`.

    `conhecidos` deve trazer agendados E enviados: a contagem por dia precisa
    do que já foi ao ar, senão um post que disparou de manhã deixa de contar e
    o dia estoura o teto. Sem isso, 26/08/2026 fechou com 11 posts.
    """
    def _dia_hora(p):
        if not p.get("dueAt"):
            return None
        d = (datetime.datetime.fromisoformat(p["dueAt"].replace("Z", "+00:00"))
             - datetime.timedelta(hours=FUSO_SP_H))
        return d.date(), d.hour

    ocupados = set()
    # Os INSTANTES exatos do que ja' esta' agendado. O conjunto `ocupados` so'
    # guarda (dia, hora) e nao serve pra medir intervalo — 16:32 e 19:22 sao
    # horas diferentes e mesmo assim distam 2h50.
    instantes: list[datetime.datetime] = []
    for p in agendados:
        dh = _dia_hora(p)
        if dh:
            ocupados.add(dh)
        if p.get("dueAt"):
            instantes.append(
                (datetime.datetime.fromisoformat(p["dueAt"].replace("Z", "+00:00"))
                 - datetime.timedelta(hours=FUSO_SP_H)).replace(tzinfo=None))

    por_dia: dict[datetime.date, int] = {}
    for p in (conhecidos if conhecidos is not None else agendados):
        dh = _dia_hora(p)
        if dh:
            por_dia[dh[0]] = por_dia.get(dh[0], 0) + 1
    agora = (datetime.datetime.now(datetime.timezone.utc)
             - datetime.timedelta(hours=FUSO_SP_H)).replace(tzinfo=None)
    saida, dia = [], agora.date()
    while len(saida) < quantos:
        for h, m in SLOTS_SP:
            if len(saida) >= quantos:
                break
            minuto = min(57, max(3, m + random.randint(-VARIACAO_MIN, VARIACAO_MIN)))
            cand = datetime.datetime.combine(dia, datetime.time(h, minuto))
            if cand <= agora + datetime.timedelta(minutes=20):
                continue
            if (dia, h) in ocupados:
                continue
            if por_dia.get(dia, 0) >= MAX_POR_DIA:
                break
            # INTERVALO MINIMO, verificado DEPOIS da variacao. Compara com o
            # que ja' esta' no Buffer e com o que esta' sendo montado agora —
            # os dois grupos existem no mesmo dia e nenhum sozinho basta.
            vizinhos = [x for x in instantes + saida if x.date() == dia]
            perto = [x for x in vizinhos
                     if abs((cand - x).total_seconds()) < INTERVALO_MIN_H * 3600]
            if perto:
                # Empurra pra frente do vizinho mais tardio, em vez de
                # descartar o slot: descartar deixaria buraco no dia sem
                # necessidade.
                cand = max(perto) + datetime.timedelta(hours=INTERVALO_MIN_H)
                if cand.date() != dia or cand.hour >= 23:
                    continue          # nao cabe mais hoje, tenta amanha
                if any(abs((cand - x).total_seconds()) < INTERVALO_MIN_H * 3600
                       for x in vizinhos):
                    continue
            ocupados.add((dia, h))
            por_dia[dia] = por_dia.get(dia, 0) + 1
            saida.append(cand)
        dia += datetime.timedelta(days=1)
    return saida


def enfileirar(token: str, canal: str, clipe: dict, simular: bool,
               quando_sp: datetime.datetime | None = None) -> str:
    legenda = (clipe.get("legenda") or clipe.get("titulo") or "").strip()
    titulo = (clipe.get("titulo") or legenda.split("#")[0]).strip()[:90]
    if simular:
        return "SIMULADO"
    m = """mutation($input: CreatePostInput!) {
      createPost(input: $input) { __typename
        ... on PostActionSuccess { post { id status dueAt } }
        ... on RestProxyError { code message }
        ... on LimitReachedError { message }
        ... on InvalidInputError { message }
        ... on UnauthorizedError { message }
        ... on UnexpectedError { message } } }"""
    d = consultar(token, m, {"input": {
        "channelId": canal,
        "text": legenda,
        "mode": "customScheduled" if quando_sp else "addToQueue",
        "schedulingType": "automatic",
        **({"dueAt": (quando_sp + datetime.timedelta(hours=FUSO_SP_H))
             .strftime("%Y-%m-%dT%H:%M:%S.000Z")} if quando_sp else {}),
        "assets": [{"video": {"url": clipe["url"]}}],
        "metadata": {"tiktok": {"isAiGenerated": True, "title": titulo}},
    }})["createPost"]
    if d["__typename"] != "PostActionSuccess":
        raise RuntimeError(f"{d['__typename']}: {d.get('message', '')[:160]}")
    return d["post"].get("dueAt") or "sem horário"


def main() -> None:
    p = argparse.ArgumentParser(description="Enfileira clipes no Buffer")
    p.add_argument("--simular", action="store_true",
                   help="mostra o que faria, sem mandar nada")
    p.add_argument("--tag", help="usa só uma release (padrão: todas as clipes-*)")
    p.add_argument("--reserva", type=int, default=RESERVA_MANUAL,
                   help="vagas deixadas livres pro Bryan (padrão 1)")
    a = p.parse_args()

    tb, tg = _token_buffer(), _token_github()
    # fresco=True: vamos ESCREVER na fila, e a dedup compara contra esta
    # lista. Ver o docstring de contexto_buffer.
    _, canal, conhecidos = contexto_buffer(tb, fresco=True)
    # `conhecidos` traz agendados E enviados (pra dedup). A CONTAGEM de vagas
    # usa so' os agendados — enviado ja' liberou o slot.
    agendados = [p for p in conhecidos if p.get("status") == "scheduled"]
    alvo = LIMITE_FILA - a.reserva
    vagas = alvo - len(agendados)
    print(f"fila: {len(agendados)}/{LIMITE_FILA} agendados, "
          f"{a.reserva} reservada(s) -> {max(0, vagas)} vaga(s) pra encher")
    if vagas <= 0:
        print("nada a fazer: fila cheia.")
        return

    todos = manifesto(tg, a.tag)
    if not todos:
        print("manifesto vazio — nenhum clipe publicado em release ainda.")
        return

    # Dois conjuntos diferentes de propósito:
    #  - `ja_na_fila`: o que está agendado agora. NADA pode repetir isso.
    #  - `ja_publicado`: o que o Buffer já enviou. Bloqueia clipe normal, mas
    #    NÃO bloqueia republicação: quando o Bryan apaga um vídeo do TikTok
    #    pra postar de novo pelo pipeline, o Buffer continua com o post antigo
    #    como "sent" — e tratar isso como duplicata apagaria justamente o que
    #    ele quer refazer. Aconteceu em 25/08 com "Exército Cria Baratas" e
    #    "A VERDADEIRA CORRIDA DA IA": eu removi os dois da fila por engano.
    ja_na_fila = {_chave_texto(x["text"]) for x in conhecidos
                  if x.get("status") == "scheduled"}
    ja_publicado = {_chave_texto(x["text"]) for x in conhecidos
                    if x.get("status") == "sent"}
    # A consulta acima para em MAX_PAGINAS pra nao gastar orcamento, entao ela
    # e' CEGA pro que e' antigo — foi essa cegueira que republicou um clipe em
    # 25/08/2026. `estado/publicados.json` guarda o historico completo em disco
    # e nao custa requisicao. Import tardio de proposito: historico.py importa
    # este modulo, e no topo isso seria circular.
    try:
        import historico
        offline = set(historico._ler_publicados())
        so_no_disco = offline - ja_publicado
        ja_publicado |= offline
        if so_no_disco:
            print(f"dedup: +{len(so_no_disco)} texto(s) so' no registro offline "
                  f"(alem dos {len(conhecidos)} que o Buffer devolveu)")
    except Exception as e:
        print(f"  [!] registro offline indisponivel ({str(e)[:80]}); "
              "dedup usando so' o que o Buffer devolveu.")

    rejeitados_ = rejeitados.chaves()

    # ⚠️ GUARDA DE ORIGEM. A `CANAL_ESPERADO` confere o DESTINO (que o token
    # abre o canal certo). Esta confere a ORIGEM (que o clipe e' deste canal).
    #
    # Sem ela, em 31/08/2026 o primeiro run do @truque.importado encheu a fila
    # do canal de maquiagem com 10 clipes de chips: o manifesto e' unico pro
    # repositorio e o agendador pegou os primeiros da ordenacao.
    #
    # Clipe sem `canal` e' anterior ao campo — todos os 66 de entao sao do
    # @modofuturo, entao vazio conta como modofuturo. Assim os antigos seguem
    # sendo agendados normalmente e nada para de funcionar.
    canal_deste_run = (os.environ.get("CANAL_ESPERADO") or "").strip().lower()

    def e_deste_canal(v) -> bool:
        if not canal_deste_run:
            return True          # sem a variavel, nada muda (falha ABERTA)
        return (v.get("canal") or "modofuturo").strip().lower() == canal_deste_run

    # ⚠️ RECUSA DE CANAL EM ESTREIA, ANTES DE OLHAR CLIPE NENHUM. Nao adianta
    # filtrar clipe: o problema nao e' QUAL clipe vai, e' que NENHUM pode ir.
    # Filtrar por clipe deixaria a porta aberta pro proximo.
    if estreia.em_estreia(canal_deste_run):
        print(f"NADA ENFILEIRADO: {estreia.motivo(canal_deste_run)}")
        return

    def cabe(v):
        # A origem vem PRIMEIRO: nem adianta olhar dedup de um clipe que nem
        # e' deste canal.
        if not e_deste_canal(v):
            return False
        # ⚠️ RECUSA POR CONTEUDO, ANTES DE QUALQUER COMPARACAO DE TEXTO.
        #
        # Todas as guardas abaixo comparam TEXTO, e texto foi o que falhou em
        # 31/08/2026: a fila da cozinha tinha 6 posts com 6 titulos e 6
        # legendas diferentes apontando pro MESMO arquivo. Nenhuma dedup de
        # texto podia ver isso — os textos eram, de fato, todos diferentes.
        #
        # O sha vem do manifesto (posto la' pelo publicar_release, onde o
        # arquivo esta' na mao). Clipe antigo nao tem sha: nesse caso esta
        # guarda nao opina e as de texto seguem valendo.
        sha = v.get("sha")
        if sha and registro_clipes.ja_postado(sha):
            return False
        # ⚠️ E TAMBEM PELO TITULO, contra o REGISTRO — nao contra o Buffer.
        #
        # Esta e' a guarda que faltava em 01/09/2026. Ao abrir a fila dos
        # canais novos, o agendador enfileirou QUATRO videos que ja' estavam
        # no ar: o Bryan os tinha postado na mao, e postagem manual nao passa
        # pelo Buffer. A dedup de texto compara contra o que o Buffer conhece,
        # entao nao tinha como ver.
        #
        # O registro sabe, porque guarda as tres origens: buffer, mao e print.
        # Clipe antigo sem sha e' justamente o caso desses quatro — por isso a
        # consulta por titulo, e nao so' por conteudo.
        chave_reg = registro_clipes.sha_por_titulo(
            str(v.get("titulo") or "") or _primeira_linha(v.get("legenda")))
        if chave_reg and registro_clipes.ja_postado(chave_reg):
            return False
        k = _chave_texto(v.get("legenda") or v.get("titulo") or "")
        # Comparacao por PREFIXO, nao por igualdade: 88 dos 101 posts reais
        # deste canal tem titulo e descricao na mesma linha, e a chave deles
        # vira titulo+descricao — nunca casaria com a de um clipe novo, que
        # e' so' o titulo. Foi assim que o #185 reagendou dois publicados.
        # Ver engine/dedup.py.
        if dedup.ja_visto(k, ja_na_fila):
            return False
        # Apagado da fila pelo Bryan = decisão editorial, nunca reagendar.
        # Apagar post agendado não deixa rastro no Buffer, então sem esta lista
        # o clipe volta a parecer disponível — empurrei o mesmo três vezes em
        # 26/08/2026. Ver engine/rejeitados.py.
        # Por PREFIXO, pelo mesmo motivo da dedup: a chave guardada e' o
        # titulo curto, e o texto publicado traz titulo+descricao na mesma
        # linha. Medido contra os 101 posts reais — igualdade pega 9, prefixo
        # pega 11, e os +2 sao rejeicoes de verdade ("666 MILHOES" e "chips
        # 3D"). Os outros 90 nao casam: zero falso positivo.
        if dedup.ja_visto(k, rejeitados_):
            return False
        return (v.get("republicacao")
                or not dedup.ja_visto(k, ja_publicado))

    fila = [(k, v) for k, v in ordenar(todos) if cabe(v)]
    print(f"{len(todos)} clipe(s) no manifesto, {len(fila)} ainda não agendado(s)\n")

    horarios = proximos_horarios(agendados, max(0, vagas), conhecidos)
    enviados = 0
    for (chave, clipe), quando in zip(fila, horarios):
        if enviados >= vagas:
            break
        titulo = (clipe.get("titulo") or "")[:56]
        try:
            quando_txt = enfileirar(tb, canal, clipe, a.simular, quando_sp=quando)
        except Exception as e:
            print(f"  [!] {titulo}: {str(e)[:140]}")
            continue
        ini = clipe.get("inicio_s")
        pos = f"{float(ini):.0f}s do fonte" if ini is not None else "posição ?"
        print(f"  nota {clipe.get('nota', 0):.0f}  {pos:>14}  {titulo}")
        print(f"       -> {quando_txt}")
        enviados += 1

    print(f"\n{enviados} clipe(s) {'simulado(s)' if a.simular else 'enfileirado(s)'}; "
          f"{len(fila) - enviados} esperando a próxima vaga.")


if __name__ == "__main__":
    main()
