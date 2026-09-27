"""Bio sem produto repetido (dono, 27/09/2026: "ta' cheio de produto repetido").

Os pares vieram dos prints da bio: mesmo produto em anuncios diferentes tem de
cair; produtos diferentes do mesmo canal tem de ficar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paginas"))
from publicar_bio import _parecido  # noqa: E402

REPETIDOS = [
    ("Espelho de maquiagem com luz led e três cores", "Espelho de mesa para maquiagem com LED"),
    ("Luva grip sapo de borracha para academia", "Grip de mão antiderrapante de magnésio"),
    ("Luva grip sapo de borracha para academia", "Luva de borracha para treino de academia"),
    ("Kit 12 peças de chave soquete com catraca", "Jogo de soquetes 46 peças com chave catraca"),
    ("Fone sem fio Lenovo LP40 Bluetooth 5.0", "Fone sem fio M25 TWS com redução de ruído"),
    ("Organizador de maquiagem giratório 360°", "Organizador de maquiagem giratório 360°"),
]
DIFERENTES = [
    ("Bálsamo e gloss labial da marca Skin", "Lápis labial fosco à prova d'água"),
    ("Conjunto de pincéis para maquiagem", "Organizador de maquiagem giratório 360°"),
    ("Carregador rápido 120W com 4 portas USB", "Fone sem fio Lenovo LP40 Bluetooth 5.0"),
    ("Pote hermético para grãos e espaguete", "Termômetro digital para alimentos TP300"),
    ("Cortador e fatiador de legumes 16 em 1", "3 tábuas de corte em aço inox laváveis"),
]
erros = 0
for a, b in REPETIDOS:
    ok = _parecido({"nome": a}, [{"nome": b}])
    erros += not ok
    print("  ok  " if ok else "  ERRO", "repetido:", a[:40])
for a, b in DIFERENTES:
    ok = not _parecido({"nome": a}, [{"nome": b}])
    erros += not ok
    print("  ok  " if ok else "  ERRO", "diferente:", a[:40])
ok = _parecido({"nome": "Kit A", "imagem": "x/1.jpg?w=2"}, [{"nome": "Tapete", "imagem": "x/1.jpg"}])
erros += not ok
print("  ok  " if ok else "  ERRO", "mesma foto = mesmo produto")
print("\ntudo verde" if not erros else f"\n{erros} ERRO(S)")
sys.exit(1 if erros else 0)
