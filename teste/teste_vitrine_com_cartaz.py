# -*- coding: utf-8 -*-
"""A vitrine posta o CARTAZ, e nao perde o post quando o cartaz falha.

O que estas guardas vigiam:

1. A FOTO CHEGA ATE' A VITRINE. Ela ja' viajava no manifesto; o
   `produto.normalizar` era o unico lugar que a descartava, e por isso o canal
   postou texto puro desde que existe. Defeito silencioso: nada quebrava.

2. FALHA ABERTA NO CARTAZ. Foto que nao baixa nao pode levar o post junto — a
   imagem e' moldura, o link e' conteudo.

3. O SELO CONTINUA PRESO AO PAR DE PRECOS, atravessando TRES modulos
   (`garimpo` -> `produto` -> `vitrine` -> `cartaz`). E' o caminho por onde a
   queda falsa de 15/09 voltaria, agora impressa numa imagem.

⭐ Cada uma roda tambem contra o caso que ela tem de reprovar.
"""
import io
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests                              # noqa: E402
from PIL import Image                        # noqa: E402

from engine import garimpo                   # noqa: E402
from engine import produto as _produto       # noqa: E402
from engine import telegram                  # noqa: E402
from engine import vitrine                   # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


vitrine.JA_POSTADOS = Path(tempfile.mkdtemp()) / "vitrine_postados.json"
os.environ[vitrine.ENV_CANAL] = "@canal_de_mentira"

FOTO = io.BytesIO()
Image.new("RGB", (800, 800), (180, 120, 90)).save(FOTO, format="JPEG")
FOTO = FOTO.getvalue()

P = {"nome": "Conjunto de esponjas de maquiagem",
     "preco": "R$ 13,52", "preco_antes": "R$ 16,50",
     "loja": "Beauty Store", "preco_em": "2026-09-16",
     "imagem": "https://ae01.alicdn.com/kf/exemplo.jpg",
     "link": "https://exemplo.com/esponjas"}


class _Resposta:
    def __init__(self, conteudo): self.content = conteudo
    def raise_for_status(self): pass


class _TelegramFalso:
    """Dubla o telegram e ANOTA por qual porta o post saiu."""

    def __init__(self, foto_vai=True):
        self.fotos, self.textos, self.foto_vai = [], [], foto_vai

    def enviar_foto(self, imagem, legenda="", destino=None, botao=None):
        self.fotos.append((imagem, legenda, botao))
        return self.foto_vai

    def enviar(self, texto, destino=None):
        self.textos.append(texto)
        return True


def _com_rede(conteudo):
    """Troca o `requests.get` por um que devolve `conteudo` — ou estoura."""
    def falso(url, **kw):
        if isinstance(conteudo, Exception):
            raise conteudo
        return _Resposta(conteudo)
    return falso


print("1. a FOTO atravessa o normalizador (era ela que se perdia)")
n = _produto.normalizar(P)
checar(n.get("imagem") == P["imagem"], "o campo `imagem` sobrevive")
checar(n.get("preco_antes") == "R$ 16,50", "o campo `preco_antes` sobrevive")
# ⛔ caso negativo: sem preco nao ha' preco antigo. Preco antigo sozinho seria
# um "de R$ 16,50" pendurado em nada.
sem_preco = _produto.normalizar(dict(P, preco="", preco_antes="R$ 16,50"))
checar(sem_preco["preco_antes"] == "",
       "sem preco de hoje, o preco antigo NAO passa")
# e um produto que nunca teve foto continua valido — o campo e' opcional
sem_foto = _produto.normalizar({k: v for k, v in P.items() if k != "imagem"})
checar(sem_foto is not None and sem_foto["imagem"] == "",
       "produto sem foto continua valido (o campo e' opcional)")

print("\n2. o cartaz e' montado, e sai pela porta de FOTO")
tg, real = _TelegramFalso(), vitrine.telegram
vitrine.telegram = tg
guardado = requests.get
requests.get = _com_rede(FOTO)
try:
    t = vitrine.postar(P, "truque.importado")
    checar(t is not None, "o post foi entregue")
    checar(len(tg.fotos) == 1 and len(tg.textos) == 0,
           "saiu UMA foto e nenhum texto solto")
    if tg.fotos:
        img = Image.open(io.BytesIO(tg.fotos[0][0]))
        checar(img.size == (1080, 1920), "o cartaz entregue e' 9x16")
        legenda, botao = tg.fotos[0][1], tg.fotos[0][2]
        checar("13,52" in legenda, "a legenda leva o preco")
        checar(len(legenda) <= 1024,
               f"a legenda cabe no limite do Telegram ({len(legenda)} chars)")
        checar(botao is not None and botao[1] == P["link"],
               "o LINK viaja no botao (1.065 chars nao cabem na legenda)")
        checar(P["link"] not in legenda,
               "e nao se repete na legenda — era o que estourava o limite")
finally:
    requests.get = guardado
    vitrine.telegram = real

print("\n3. FALHA ABERTA — cartaz que nao monta nao leva o post junto")
for oq, efeito in (("a rede cai", requests.exceptions.Timeout("estourou")),
                   ("o JPEG vem corrompido", b"isto nao e' uma imagem")):
    tg, real = _TelegramFalso(), vitrine.telegram
    vitrine.telegram = tg
    guardado = requests.get
    requests.get = _com_rede(efeito)
    try:
        t = vitrine.postar(dict(P, link=f"https://exemplo.com/{len(oq)}"),
                           "truque.importado")
        checar(t is not None, f"{oq}: o post SAIU assim mesmo")
        checar(len(tg.textos) == 1 and len(tg.fotos) == 0,
               f"{oq}: saiu pela porta de texto")
    finally:
        requests.get = guardado
        vitrine.telegram = real

print("\n3b. o Telegram RECUSA a foto - o post cai pro texto COM link")
tg, real = _TelegramFalso(foto_vai=False), vitrine.telegram
vitrine.telegram = tg
guardado = requests.get
requests.get = _com_rede(FOTO)
try:
    t = vitrine.postar(dict(P, link="https://exemplo.com/recusada"),
                       "truque.importado")
    checar(t is not None, "o post saiu")
    checar(len(tg.fotos) == 1 and len(tg.textos) == 1,
           "tentou a foto, e caiu pro texto")
    # ⛔ O DEFEITO QUE ESTA GUARDA EXISTE PRA IMPEDIR: com o link no botao, um
    # caminho que caisse pro texto SEM link poria o produto no feed sem para
    # onde ir. Pior que nao ter postado.
    checar(bool(tg.textos) and "https://exemplo.com/recusada" in tg.textos[0],
           "o texto de reserva leva o LINK - post sem link nao pode existir")
finally:
    requests.get = guardado
    vitrine.telegram = real

print("\n4. sem foto no produto, nada muda (o caminho antigo continua)")
checar(vitrine.cartaz_de({k: v for k, v in P.items() if k != "imagem"}) is None,
       "produto sem `imagem` nao tenta montar cartaz")
checar(vitrine.cartaz_de(dict(P, preco="")) is None,
       "produto sem preco legivel nao monta cartaz")

print("\n5. o SELO continua preso ao par de precos, ponta a ponta")
guardado = requests.get
requests.get = _com_rede(FOTO)
try:
    from engine import cartaz as _c

    def verde(b):
        import numpy as np
        a = np.asarray(Image.open(io.BytesIO(b)).convert("RGB"), dtype=np.int16)
        return int((np.abs(a - np.array(_c.VERDE, dtype=np.int16)).max(axis=2)
                    <= 28).sum())

    com = vitrine.cartaz_de(P)
    sem = vitrine.cartaz_de(dict(P, preco_antes=""))
    # ⭐ o caso POSITIVO primeiro: sem ele, um cartaz que nunca desenha selo
    # passaria na linha de baixo.
    checar(verde(com) > 2000, "com par de precos, o selo aparece")
    checar(verde(sem) < 200, "sem `preco_antes`, o selo NAO aparece")
    mentira = vitrine.cartaz_de(dict(P, preco_antes="R$ 10,00"))
    checar(verde(mentira) < 200,
           "`preco_antes` MENOR que o preco de hoje nao vira desconto")
finally:
    requests.get = guardado

print("\n6. o preco antigo so' nasce quando a queda foi MEDIDA")
h = {7: [16.50, 15.90, 13.52]}
bruto = {"product_id": 7, "product_title": "Esponjas", "target_sale_price": "13.52",
         "promotion_link": "https://exemplo.com/x"}
maior = garimpo.maior_visto(bruto, h)
q, _ = garimpo.desconto_honesto(bruto, h)
checar(maior == 16.50, "`maior_visto` devolve o maior que NOS vimos")
checar(garimpo.para_produto(bruto, q, maior)["preco_antes"] == "R$ 16,50",
       "com queda, o preco antigo e' o preco VISTO (nao reconstruido)")
# ⛔ o caso que produziria o centavo inventado
reconstruido = 13.52 / (1 - round(q, 1) / 100)
checar(abs(reconstruido - 16.50) > 0.001,
       f"a reconstrucao pela queda daria R$ {reconstruido:.2f} — por isso "
       f"ela nao e' usada")
sem_serie = garimpo.para_produto(bruto, 0.0, 0.0)
checar(sem_serie["preco_antes"] == "", "sem queda, o campo sai VAZIO")

print("\n7. legenda longa demais nao derruba o post")
checar(telegram.LIMITE_LEGENDA < telegram.LIMITE_MSG,
       "o limite da legenda de foto e' menor que o da mensagem")

print("\n" + ("FALHOU: " + " | ".join(falhas) if falhas
              else "tudo verde — a vitrine posta cartaz e nao perde post"))
sys.exit(1 if falhas else 0)
