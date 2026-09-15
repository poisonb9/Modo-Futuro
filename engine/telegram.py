"""Telegram: manda legenda pro celular e recebe comandos.

Existe porque o rascunho do TikTok NÃO carrega legenda (a API de inbox só
aceita o arquivo de vídeo), então a legenda é colada na mão no celular.
Telegram é a ponte: legenda sai do desktop e chega no celular já formatada,
uma mensagem por clipe — dá pra tocar e copiar.

Setup (1x):
  1. no Telegram, fale com @BotFather -> /newbot -> copie o token
  2. .env:  TELEGRAM_BOT_TOKEN=...
  3. mande qualquer mensagem pro seu bot (bot não pode iniciar conversa)
  4. python bot_telegram.py --descobrir-chat
"""
import json
import os

import requests
from dotenv import load_dotenv

import config

load_dotenv()

API = "https://api.telegram.org/bot{token}/{metodo}"
LIMITE_MSG = 4000          # o limite real é 4096, deixa folga
# ⚠️ Legenda de FOTO é outro limite, quatro vezes menor (o real é 1024).
LIMITE_LEGENDA = 1000


def configurado() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN"))


def _token() -> str:
    t = os.getenv("TELEGRAM_BOT_TOKEN")
    if not t:
        raise RuntimeError(
            "Falta TELEGRAM_BOT_TOKEN no .env. Fale com @BotFather no Telegram, "
            "/newbot, e ponha o token no .env.")
    return t


def chat_id() -> str | None:
    return os.getenv("TELEGRAM_CHAT_ID")


def chamar(metodo: str, **params) -> dict:
    r = requests.post(API.format(token=_token(), metodo=metodo),
                      json=params, timeout=40)
    r.raise_for_status()
    return r.json()


def enviar(texto: str, destino: str | None = None) -> bool:
    """Manda uma mensagem. Devolve False (sem estourar) se não configurado —
    o envio pro TikTok não deve falhar só porque o Telegram não está pronto."""
    destino = destino or chat_id()
    if not configurado() or not destino:
        return False
    try:
        for pedaco in _picar(texto):
            chamar("sendMessage", chat_id=destino, text=pedaco,
                   disable_web_page_preview=True)
        return True
    except Exception as e:
        print(f"      [!] Telegram falhou: {e}")
        return False


def enviar_foto(imagem: bytes, legenda: str = "",
                destino: str | None = None,
                botao: tuple[str, str] | None = None) -> bool:
    """Manda uma FOTO com legenda. Devolve False (sem estourar) se nao deu.

    ⚠️ A LEGENDA DA FOTO TEM OUTRO LIMITE, e e' quatro vezes menor: 1024
    caracteres contra os 4096 da mensagem de texto. Nao e' detalhe — um post
    que passa do limite volta `400 MEDIA_CAPTION_TOO_LONG` e o produto NAO vai
    ao ar. Quando nao cabe, a foto vai sem legenda e o texto vai logo atras,
    em mensagem propria: duas bolhas em vez de uma, bem melhor do que nada.

    ⭐ E O `botao` EXISTE POR CAUSA DE UM NUMERO MEDIDO, em 15/09/2026: o link
    de afiliado do AliExpress tem **1.065 caracteres** (mediana de 277 posts),
    entao 272 dos 277 estouravam a legenda SO' pelo link. Url de botao NAO
    conta pra legenda — com ele o post volta a caber numa bolha so', e de
    quebra a pessoa toca num rotulo em vez de num paredao de caracteres.

    ⚠️ E O `sendPhoto` NAO ACEITA JSON como o `chamar()` faz: arquivo vai por
    multipart. Por isso este envio nao passa por la'.
    """
    destino = destino or chat_id()
    if not configurado() or not destino:
        return False
    cabe = len(legenda) <= LIMITE_LEGENDA
    campos = {"chat_id": destino, "caption": legenda if cabe else ""}
    if botao:
        campos["reply_markup"] = json.dumps(
            {"inline_keyboard": [[{"text": botao[0], "url": botao[1]}]]})
    try:
        r = requests.post(
            API.format(token=_token(), metodo="sendPhoto"),
            data=campos,
            files={"photo": ("cartaz.jpg", imagem, "image/jpeg")},
            timeout=60)
        r.raise_for_status()
        # ⚠️ 200 NAO PROVA NADA — a API do Telegram responde 200 com
        # `{"ok": false}` no corpo. Ler o corpo, sempre.
        if not r.json().get("ok"):
            print(f"      [!] Telegram recusou a foto: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"      [!] Telegram falhou na foto: {e}")
        return False
    if not cabe and legenda:
        return enviar(legenda, destino)
    return True


def _picar(texto: str) -> list[str]:
    """Quebra em pedaços dentro do limite do Telegram, cortando em linha."""
    if len(texto) <= LIMITE_MSG:
        return [texto]
    pedacos, atual = [], ""
    for linha in texto.splitlines(keepends=True):
        if len(atual) + len(linha) > LIMITE_MSG:
            pedacos.append(atual)
            atual = ""
        atual += linha
    if atual:
        pedacos.append(atual)
    return pedacos


def atualizacoes(offset: int | None = None, espera: int = 50) -> list[dict]:
    """Long polling. `espera` alto = menos requisições, sem perder mensagem."""
    params = {"timeout": espera}
    if offset is not None:
        params["offset"] = offset
    return chamar("getUpdates", **params).get("result", [])


def descobrir_chat() -> str:
    """Acha o chat_id pelas mensagens recentes e grava no .env."""
    chats = {}
    for upd in atualizacoes(espera=0):
        msg = upd.get("message") or upd.get("channel_post") or {}
        chat = msg.get("chat") or {}
        if chat.get("id"):
            chats[str(chat["id"])] = (chat.get("username")
                                      or chat.get("first_name")
                                      or chat.get("title", "?"))
    if not chats:
        raise RuntimeError("Nenhuma mensagem encontrada. Mande qualquer mensagem "
                           "pro seu bot no Telegram e rode de novo.")

    for cid, nome in chats.items():
        print(f"  chat_id={cid}  ({nome})")
    cid = next(iter(chats))
    _gravar_env("TELEGRAM_CHAT_ID", cid)
    print(f"\nGravado TELEGRAM_CHAT_ID={cid} no .env")
    return cid


def _gravar_env(chave: str, valor: str):
    env = config.RAIZ / ".env"
    texto = env.read_text(encoding="utf-8") if env.exists() else ""
    if f"{chave}=" in texto:
        linhas = [f"{chave}={valor}" if l.startswith(f"{chave}=") else l
                  for l in texto.splitlines()]
        env.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    else:
        env.write_text(texto.rstrip() + f"\n{chave}={valor}\n", encoding="utf-8")
