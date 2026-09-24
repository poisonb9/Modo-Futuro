"""Guarda em `site_no_ar/` uma copia do que esta NO AR, e a configuracao do
Cloudflare que nao se refaz a partir deste repositorio.

Bryan, 20/09/2026: "deixa uma copia de backup na pasta do projeto de tudo que
voce subiu pra nuvem ... pra um dia precisar refazer".

DUAS COISAS DIFERENTES, e so' a segunda e' insubstituivel:

  1. OS BYTES SERVIDOS. Baixados DO AR, nao da pasta de build: a pasta de
     build e' apagada no fim da publicacao, e o que interessa guardar e' o
     que o visitante recebeu. Cada arquivo vai com sha256 no MANIFESTO.json.

  2. A CONFIGURACAO DO CLOUDFLARE (`cloudflare.json`). Esta NAO esta em
     lugar nenhum do repositorio: nomes dos projetos Pages, dominios
     ligados, branch de producao, rulesets. Sem isso, refazer e' adivinhar.

SEGREDO NAO ENTRA. O token e o id da conta ficam no `.env` e sao conferidos
contra a saida antes de escrever (se aparecerem, o script para). `env_vars`
de projeto, se um dia existirem, viram "(omitido)".

O QUE ESTE BACKUP NAO TEM, e o proprio arquivo diz isso: os registros de DNS
e as configuracoes de SSL da zona. O token de publicacao responde 403 neles.
Para refazer do zero, DNS e SSL sao trabalho manual no painel.

Uso:  python -X utf8 ferramentas/backup_do_ar.py
"""
from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import subprocess
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "site_no_ar"
MAE = "https://achadinhototal.com.br"
BIOS = ["oachadinho", "achadinhochef", "pagomenos", "achadinhodehoje", "meulivro"]
EXTERNAS = ["kabum", "nike", "lauri", "arno", "sharkninja", "exypna"]
# O Cloudflare responde 403 ao User-Agent padrao do Python. Sem isto o backup
# sai vazio COM CARA DE SUCESSO (29 falhas, 0 arquivos) — aconteceu em 20/09.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def _baixar(url: str) -> tuple[bytes, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return (r.read(), r.headers.get("Content-Type", ""),
                r.headers.get("Cache-Control", ""))


def _alvos() -> list[tuple[str, str]]:
    a = [(MAE + "/", "index.html"), (MAE + "/motor.js", "motor.js"),
         (MAE + "/links.json", "links.json"), (MAE + "/robots.txt", "robots.txt"),
         (MAE + "/sitemap.xml", "sitemap.xml"), (MAE + "/icone.png", "icone.png"),
         (MAE + "/parceiros/", "parceiros/index.html"),
         (MAE + "/privacidade/", "privacidade/index.html")]
    a += [(MAE + "/" + f + ".json", f + ".json") for f in EXTERNAS]
    # os baloes da inauguracao (24/09/2026): mesmos nomes da pasta de origem
    origem_baloes = Path(__file__).resolve().parent.parent / "paginas" / "baloes"
    a += [(MAE + "/baloes/" + f.name, "baloes/" + f.name)
          for f in sorted(origem_baloes.glob("*.webp"))]
    for b in BIOS:
        for rota, nome in (("/", "index.html"), ("/todos", "todos.html"),
                           ("/parceiros", "parceiros.html")):
            a.append(("https://" + b + ".pages.dev" + rota, "bios/" + b + "/" + nome))
    return a


def bytes_do_ar() -> int:
    manifesto: list[dict] = []
    total = falhas = 0
    for url, rel in _alvos():
        try:
            corpo, tipo, cache = _baixar(url)
        except Exception as e:  # noqa: BLE001
            manifesto.append({"url": url, "arquivo": rel, "ERRO": str(e)})
            falhas += 1
            print("  FALHOU " + rel + ": " + str(e))
            continue
        # ⚠️ o Pages responde 200 COM HTML para caminho que nao existe: uma
        # imagem que volta como text/html e' arquivo faltando no ar, nao backup.
        if rel.endswith((".webp", ".png")) and not str(tipo).startswith("image"):
            manifesto.append({"url": url, "arquivo": rel,
                              "ERRO": "veio " + str(tipo) + " no lugar de imagem"})
            falhas += 1
            print("  FALHOU " + rel + ": veio " + str(tipo) + " no lugar de imagem")
            continue
        destino = RAIZ / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(corpo)
        total += len(corpo)
        manifesto.append({"url": url, "arquivo": rel, "bytes": len(corpo),
                          "tipo": tipo, "cache": cache,
                          "sha256": hashlib.sha256(corpo).hexdigest()})
    commit = subprocess.run(["git", "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    io.open(RAIZ / "MANIFESTO.json", "w", encoding="utf-8", newline="\n").write(
        json.dumps({
            "baixado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "commit": commit,
            "origem": "baixado DO AR, nao da pasta de build",
            "total_bytes": total, "falhas": falhas, "arquivos": manifesto,
        }, ensure_ascii=False, indent=2))
    # FALHA NAO VIRA SUCESSO SILENCIOSO: backup incompleto tem de doer agora.
    if falhas:
        raise SystemExit(str(falhas) + " arquivo(s) nao baixaram — backup incompleto")
    print("  bytes do ar: %d arquivos, %.2f MB" % (len(manifesto), total / 1048576))
    return total


def _env() -> dict[str, str]:
    for base in (Path.cwd(), Path(__file__).resolve().parent.parent):
        p = base / ".env"
        if not p.exists():
            continue
        d = {}
        for linha in p.read_text(encoding="utf-8", errors="replace").splitlines():
            linha = linha.strip()
            if "=" in linha and not linha.startswith("#"):
                k, v = linha.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
        return d
    return dict(os.environ)


def config_do_cloudflare() -> None:
    env = _env()
    tok, conta = env.get("CF_API_TOKEN"), env.get("CF_ACCOUNT_ID")
    if not (tok and conta):
        print("  sem CF_API_TOKEN/CF_ACCOUNT_ID: pulei a configuracao")
        return

    def api(caminho: str) -> dict:
        req = urllib.request.Request(
            "https://api.cloudflare.com/client/v4" + caminho,
            headers={"Authorization": "Bearer " + tok})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001
            return {"success": False, "ERRO": str(e)}

    saida: dict = {
        "baixado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "conta_id": "(omitido de proposito — esta no .env)",
        "projetos": {},
    }
    for p in api("/accounts/" + conta + "/pages/projects").get("result", []):
        p.pop("id", None)
        for _amb, cfg in (p.get("deployment_configs") or {}).items():
            if cfg.get("env_vars"):
                cfg["env_vars"] = {k: "(omitido)" for k in cfg["env_vars"]}
        for chave in ("canonical_deployment", "latest_deployment"):
            d = p.get(chave)
            if isinstance(d, dict):
                p[chave] = {k: d.get(k) for k in
                            ("created_on", "modified_on", "environment", "url", "short_id")
                            if k in d}
        saida["projetos"][p["name"]] = p
    zonas = api("/zones").get("result", [])
    saida["zonas"] = [{"nome": z["name"], "name_servers": z.get("name_servers"),
                       "status": z.get("status"),
                       "plano": (z.get("plan") or {}).get("name")} for z in zonas]
    if zonas:
        rs = api("/zones/" + zonas[0]["id"] + "/rulesets")
        saida["rulesets"] = [{k: r.get(k) for k in
                              ("name", "phase", "kind", "description")}
                             for r in rs.get("result", [])]
    saida["NAO_CONSEGUI_LER"] = {
        "dns_records": ("403 — o token de publicacao nao tem DNS:Read. "
                        "Os registros do dominio NAO estao neste backup."),
        "settings_ssl": "403 — idem para SSL/TLS da zona.",
        "o_que_isso_significa": ("para refazer do zero, DNS e SSL sao trabalho manual "
                                 "no painel; o resto (projetos Pages, dominios, branch, "
                                 "rulesets, bytes servidos) esta guardado."),
    }
    texto = json.dumps(saida, ensure_ascii=False, indent=2)
    # A GUARDA QUE IMPORTA: segredo nao entra no repositorio, nem por descuido.
    for segredo in (tok, conta):
        if segredo and segredo in texto:
            raise SystemExit("ABORTEI: um segredo apareceu na saida do Cloudflare")
    io.open(RAIZ / "cloudflare.json", "w", encoding="utf-8", newline="\n").write(texto)
    print("  cloudflare: %d projeto(s), %d zona(s)"
          % (len(saida["projetos"]), len(saida["zonas"])))


def main() -> None:
    RAIZ.mkdir(parents=True, exist_ok=True)
    print("backup do que esta no ar:")
    bytes_do_ar()
    config_do_cloudflare()
    print("pronto: site_no_ar/")


if __name__ == "__main__":
    main()
