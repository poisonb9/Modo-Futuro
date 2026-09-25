"""Motor de cortes: Gemini escolhe, Groq legenda, ffmpeg monta."""


import os as _os
import re as _re

CADEIA_GEMINI = [m.strip() for m in _os.environ.get(
    "GEMINI_CADEIA", "gemini-3.8-flash,gemini-3.7-flash,gemini-3.6-flash,gemini-3.5-flash"
).split(",") if m.strip()]
_CAI = {429, 500, 503}
_MODELO_NA_URL = _re.compile(r"/models/(gemini-[0-9.]+-flash):(generateContent|streamGenerateContent)")


def _cadeia(url: str) -> list[str]:
    """A cadeia a tentar, se a URL e' uma geracao num modelo da cadeia."""
    m = _MODELO_NA_URL.search(url or "")
    if not m or m.group(1) not in CADEIA_GEMINI:
        return []
    return list(CADEIA_GEMINI)


def _trocar_modelo(url: str, modelo: str) -> str:
    return _MODELO_NA_URL.sub(lambda m: f"/models/{modelo}:{m.group(2)}", url, count=1)


def _chave_no_cabecalho() -> None:
    """Chave do Google vai no CABECALHO, nunca na URL (25/09/2026).

    Com `?key=` na URL, qualquer erro do `requests` imprime a chave inteira —
    e o log do Actions deste repo e' publico. Aqui toda chamada a
    `*.googleapis.com` com `key=` na query tem a chave movida para o header
    `x-goog-api-key` (aceito pela API do Gemini) antes de sair.
    """
    try:
        import requests
        from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
    except Exception:
        return
    original = requests.sessions.Session.request
    if getattr(original, "_chave_segura", False):
        return

    def request(self, method, url, *args, **kwargs):
        cadeia = _cadeia(url)
        if cadeia:
            # ⭐ 25/09 (dono): 3.8 -> 3.7 -> 3.6 -> 3.5. Sobrecarga (503) ou
            # cota (429/500) num modelo NAO espera: tenta o proximo na hora.
            # Em 25/09 a espera no 3.6 sobrecarregado custou 4 h e um clipe.
            r = None
            for modelo in cadeia:
                r = _chamar(self, method, _trocar_modelo(url, modelo), args, kwargs)
                if r.status_code not in _CAI:
                    if modelo != cadeia[0]:
                        print(f"   [gemini] respondeu no {modelo} (os anteriores falharam)")
                    return r
            return r
        return _chamar(self, method, url, args, kwargs)

    def _chamar(self, method, url, args, kwargs):
        kwargs = dict(kwargs)
        try:
            p = urlsplit(url)
            if p.hostname and p.hostname.endswith("googleapis.com") and "key=" in (p.query or ""):
                q = parse_qsl(p.query, keep_blank_values=True)
                chave = next((v for k, v in q if k == "key"), None)
                if chave and "youtube" not in (p.path or ""):
                    url = urlunsplit(p._replace(query=urlencode([(k, v) for k, v in q if k != "key"])))
                    h = dict(kwargs.get("headers") or {})
                    h.setdefault("x-goog-api-key", chave)
                    kwargs["headers"] = h
        except Exception:
            pass
        return original(self, method, url, *args, **kwargs)

    request._chave_segura = True
    requests.sessions.Session.request = request


_chave_no_cabecalho()
