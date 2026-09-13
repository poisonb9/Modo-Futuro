# -*- coding: utf-8 -*-
"""O mesmo clipe pode ir pras DUAS plataformas, e nao pode repetir em uma.

⚠️ Duplicata na MESMA plataforma derrubou o alcance duas vezes (02/08 e
25/08). Esta guarda separa isso de publicacao simultanea, que e' legitima.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import registro_clipes as reg  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok  " if ok else "  [x] ") + oq)
    if not ok:
        falhas.append(oq)


# ⚠️ registro de mentira: sem isto o teste escreveria no estado de producao
reg.ARQUIVO = Path(tempfile.mkdtemp()) / "registro.json"
SHA = "a" * 64
reg.registrar(SHA, arquivo="c.mp4", titulo="Um clipe", canal="modofuturo")

print("1. clipe novo nao foi postado em lugar nenhum")
checar(not reg.ja_postado(SHA), "em nenhum lugar")
checar(not reg.ja_postado(SHA, "tiktok"), "nem no tiktok")
checar(not reg.ja_postado(SHA, "instagram"), "nem no instagram")

print("\n2. postou no TikTok")
reg.marcar_postado(SHA, origem="buffer", quando="2026-09-13T12:00:00Z",
                   plataforma="tiktok")
checar(reg.ja_postado(SHA, "tiktok"), "tiktok: sim")

print("\n3. ⭐ E ISSO NAO PODE BLOQUEAR O INSTAGRAM")
# ⚠️ Este e' o defeito que existia: `ja_postado` olhava qualquer postagem, e
# o Instagram nunca publicaria — sem erro nenhum, so' silencio.
checar(not reg.ja_postado(SHA, "instagram"),
       "instagram: NAO — plataformas sao independentes")

print("\n4. o sentido antigo continua valendo pra quem nao pergunta")
# ⚠️ agendar_buffer e publicar_release chamam sem plataforma. Pra eles nada
# muda, e mudar seria reagendar coisa ja' publicada.
checar(reg.ja_postado(SHA), "sem plataforma -> 'saiu em algum lugar' = True")

print("\n5. NEGATIVO — repetir NA MESMA plataforma continua sendo duplicata")
reg.marcar_postado(SHA, origem="buffer", quando="2026-09-13T12:00:00Z",
                   plataforma="tiktok")
n = len(reg._ler()["clipes"][SHA]["postagens"])
checar(n == 1, f"mesma hora, mesma origem, mesma plataforma -> nao duplica ({n})")

print("\n6. ⭐ MAS SIMULTANEO NO MESMO MINUTO TEM DE ENTRAR")
# ⚠️ Publicacao simultanea sai no mesmo minuto e pela mesma origem. Sem a
# plataforma na comparacao, a segunda seria engolida como repetida.
reg.marcar_postado(SHA, origem="buffer", quando="2026-09-13T12:00:00Z",
                   plataforma="instagram")
n = len(reg._ler()["clipes"][SHA]["postagens"])
checar(n == 2, f"tiktok e instagram no mesmo minuto -> as DUAS ({n})")
checar(reg.plataformas_de(SHA) == {"tiktok", "instagram"}, "saiu nas duas")

print("\n7. NEGATIVO — plataforma escrita errado FALHA ALTO")
# ⚠️ Aceitar texto livre faria 'instagran' virar plataforma nova e silenciosa,
# e a guarda pararia de proteger sem ninguem notar.
for torta in ("instagran", "TikTok", "youtube", ""):
    try:
        reg.marcar_postado(SHA, origem="buffer", quando="x", plataforma=torta)
        checar(False, f"{torta!r} passou — NAO deveria")
    except ValueError:
        checar(True, f"{torta!r} recusado")
try:
    reg.ja_postado(SHA, "instagran")
    checar(False, "ja_postado aceitou plataforma torta")
except ValueError:
    checar(True, "ja_postado tambem recusa plataforma torta")

print("\n8. postagem ANTIGA, sem o campo, conta como TikTok")
# ⚠️ Tudo publicado ate' 13/09/2026 foi no TikTok — nao havia outra ligada.
# E' leitura do historico, nao chute.
d = reg._ler()
d["clipes"][SHA]["postagens"] = [{"origem": "mao", "quando": "2026-08-01T10:00:00Z",
                                  "canal": "modofuturo", "detalhe": ""}]
reg._gravar(d)
checar(reg.ja_postado(SHA, "tiktok"), "sem campo -> tiktok")
checar(not reg.ja_postado(SHA, "instagram"), "e NAO instagram")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
