"""Qual VOZ dubla este canal — e a guarda que impede a errada de passar.

POR QUE EXISTE

Ate 30/08/2026 o motor tinha uma voz so' por clipe, e ela era escolhida em
DOIS lugares fixos no codigo:

    config.VOZ_CLONADA_ATIVA = True             <- a voz clonada do Bryan
    dublagem.VOZ_PADRAO = "pt-BR-AntonioNeural" <- a alternativa, masculina

Nenhum dos dois lia o ambiente. Nao havia como pedir outra voz no disparo.

Isso travou o canal de MAQUIAGEM, decidido em 30/08: ele precisa de voz
FEMININA. Voz masculina num canal de maquiagem contradiz o publico — e' o
mesmo tipo de erro que fez o Cozinha descartar fonte muda: a peca nao combina
com o produto.

## A ARMADILHA QUE ESTA GUARDA EXISTE PRA PEGAR

`VOZ_CLONADA_ATIVA` vence: o `main.py` so' cai no edge-tts quando ela e'
falsa. Entao pedir voz feminina SEM desligar a clonagem produziria um clipe
com a voz do Bryan, **em silencio** — o parametro seria aceito e ignorado.

E' exatamente a classe de defeito que se repetiu tres vezes em 30/08: o
parametro passa, o resultado sai errado, e o run termina VERDE. Os cortes
orfaos, os clipes mudos e o face tracking desligado foram todos assim.

Por isso `conferir()` **derruba** essa combinacao em vez de escolher sozinha
qual vale. Um canal com voz errada nao tem desfazer bonito: o video sai, o
alcance conta, e apagar deixa ele em 0 pra sempre.

## COMO USAR NO DISPARO

    VOZ_CANAL=feminina  VOZ_CLONADA=0    -> pt-BR-FranciscaNeural
    VOZ_CANAL=thalita   VOZ_CLONADA=0    -> pt-BR-ThalitaNeural
    (nada)                               -> voz clonada do Bryan, como sempre

Sem `VOZ_CANAL` nada muda. Os disparos antigos seguem valendo identicos —
falha ABERTA pro que ja' existe, falha FECHADA so' pra combinacao nova e
contraditoria.
"""
from __future__ import annotations

import os

# Apelidos para nao ter que escrever o nome do edge-tts no disparo. Qualquer
# nome completo de voz do edge-tts tambem e' aceito, pra nao precisar mexer
# aqui a cada voz nova.
VOZES = {
    "masculina": "pt-BR-AntonioNeural",
    "antonio": "pt-BR-AntonioNeural",
    "feminina": "pt-BR-FranciscaNeural",
    "francisca": "pt-BR-FranciscaNeural",
    # ⚠️ O nome CERTO tem "Multilingual". Ate' 31/08/2026 esta linha dizia
    # `pt-BR-ThalitaNeural`, que NAO EXISTE no catalogo do edge-tts — medido
    # com `edge_tts.list_voices()`: so' ha' tres vozes pt-BR, e a Thalita e'
    # `pt-BR-ThalitaMultilingualNeural`. Ninguem tinha pedido a Thalita ainda,
    # entao a alternativa nunca foi exercida e o erro dormiu no mapa.
    "thalita": "pt-BR-ThalitaMultilingualNeural",
}

PADRAO = "pt-BR-AntonioNeural"

_FALSOS = ("0", "false", "nao", "não", "no", "")


def pedida() -> str | None:
    """O valor cru de VOZ_CANAL, ou None se ninguem pediu nada."""
    v = (os.environ.get("VOZ_CANAL") or "").strip()
    return v or None


def escolhida() -> str:
    """O nome de voz do edge-tts que este canal deve usar.

    Sem VOZ_CANAL devolve o padrao masculino de sempre.
    """
    v = pedida()
    if not v:
        return PADRAO
    return VOZES.get(v.lower(), v)


def clonada_ativa() -> bool:
    """Se a voz clonada (Chatterbox) esta' ligada.

    Default LIGADA: era o comportamento fixo antes desta mudanca, e canal
    nenhum pode mudar de voz porque alguem mexeu aqui.
    """
    v = os.environ.get("VOZ_CLONADA")
    if v is None:
        return True
    return v.strip().lower() not in _FALSOS


def conferir() -> None:
    """Derruba a combinacao que produziria a voz errada em silencio.

    Pedir VOZ_CANAL com a clonagem ligada nao e' ambiguo por descuido: sao
    duas ordens que se contradizem. Escolher uma delas por conta propria e'
    o que faria o clipe sair com a voz do Bryan num canal de maquiagem sem
    ninguem perceber ate' o video estar publicado.
    """
    v = pedida()
    if v and clonada_ativa():
        raise RuntimeError(
            f"VOZ_CANAL={v!r} foi pedida, mas a voz CLONADA esta' ligada e ela "
            f"vence — o clipe sairia com a voz do Bryan e o seu pedido seria "
            f"ignorado em silencio.\n"
            f"  Para usar {escolhida()}: passe tambem VOZ_CLONADA=0.\n"
            f"  Para usar a voz clonada: nao passe VOZ_CANAL.")
