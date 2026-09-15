"""Guardas do filtro de subcategoria e da comissao com prazo (Mercado Livre).

⚠️ OFFLINE. Nada aqui chama a API — o que se prova e' a DECISAO, nao o ML.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from engine import mercadolivre as ml  # noqa: E402

falhas = []


def checar(cond, oque):
    print(("  ok   " if cond else "  FALHA ") + oque)
    if not cond:
        falhas.append(oque)


print("1. AS SUBCATEGORIAS QUE TROUXERAM PAPEL HIGIENICO ESTAO VETADAS")
# ⚠️ MEDIDO em 15/09/2026: puxar a categoria MAE `MLB1246` (Beleza) devolveu
# papel higienico nos dois primeiros lugares, porque `Higiene Pessoal` e
# `Farmacia` sao filhas dela. Se alguem tirar daqui, o papel volta.
checar("MLB198312" in ml.FORA, "Higiene Pessoal vetada (e' onde mora o papel)")
checar("MLB431646" in ml.FORA, "Farmacia vetada")

print("\n2. A COMISSAO VALE POR PRAZO, E FORA DELE NAO VALE")
_velho = ml._arquivo_comissao()
_backup = _velho.read_text(encoding="utf-8") if _velho.exists() else None
try:
    ml.anotar_comissao("T_RECENTE", 26.0)
    ml.anotar_comissao("T_VELHO", 16.0, "2020-01-01")
    checar((ml.comissao_valida("T_RECENTE") or {}).get("pct") == 26.0,
           "comissao anotada hoje vale")
    # ⛔ Fora do prazo NAO e' "provavelmente ainda vale": e' desconhecido. Se
    # esta guarda cair, a pagina passa a afirmar um numero que ninguem
    # conferiu — e o que sustenta a pagina e' ser verificavel.
    checar(ml.comissao_valida("T_VELHO") is None,
           "comissao vencida NAO vale (o produto sai do catalogo)")
    checar(ml.comissao_valida("T_INEXISTENTE") is None,
           "produto sem anotacao nenhuma nao entra")
finally:
    if _backup is None:
        _velho.unlink(missing_ok=True)
    else:
        _velho.write_text(_backup, encoding="utf-8")

print("\n3. SO' ENTRA NO SITE O QUE MONETIZA")
# ⭐ Ordem do Bryan em 15/09: so' publicar o que paga, e sumir quando parar.
_amostra = [{"nome": "paga", "comissao": 26.0},
            {"nome": "nao paga", "comissao": None},
            {"nome": "vencida", "comissao": None}]
_passou = [p["nome"] for p in ml.so_monetizados(_amostra)]
checar(_passou == ["paga"], f"so' o que tem comissao passa (passou: {_passou})")
# ⛔ O caso negativo: sem ele, uma funcao que devolve TUDO passaria no teste
# acima se a amostra so' tivesse item bom.
checar(ml.so_monetizados([{"nome": "x", "comissao": None}]) == [],
       "lista so' com produto sem comissao devolve VAZIO")

print("\n4. O MODULO DIZ QUE A COMISSAO NAO VEM DA API")
# ⚠️ Medido em 15/09: a ficha do produto nao tem campo de comissao e as
# quatro rotas de afiliado dao 404. Isso tem de continuar escrito, senao
# alguem vai procurar de novo e perder a mesma tarde.
_fonte = Path("engine/mercadolivre.py").read_text(encoding="utf-8")
checar("404" in _fonte and "NAO VEM DA API" in _fonte,
       "o modulo registra que a comissao nao vem da API")
checar("VALIDADE_COMISSAO_DIAS" in _fonte, "e o prazo e' uma constante nomeada")

print("\n" + ("FALHOU: " + "; ".join(falhas) if falhas else "tudo verde"))
sys.exit(1 if falhas else 0)
