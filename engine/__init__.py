"""Motor de cortes: Gemini escolhe, Groq legenda, ffmpeg monta."""


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
