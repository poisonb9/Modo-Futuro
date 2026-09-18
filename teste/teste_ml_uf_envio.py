"""A UF do envio do ML sai do NOME do estado (18/09/2026: o id virou token). Sem rede."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.mercadolivre import uf_de

falhas = []
def checar(ok, msg):
    print(("  ok   " if ok else "  FALHOU: ") + msg); ok or falhas.append(msg)

print("1. o formato novo (token no id, nome legivel)")
checar(uf_de({"id": "TUxCUFJJT08xODM5Zg", "name": "Rio de Janeiro"}) == "RJ", "Rio de Janeiro -> RJ")
checar(uf_de({"id": "TUxCUFNBT085N2E4", "name": "São Paulo"}) == "SP", "Sao Paulo com acento -> SP")
print("2. o formato antigo, se voltar")
checar(uf_de({"id": "BR-MG", "name": "Minas Gerais"}) == "MG", "BR-MG -> MG")
print("3. NEGATIVO: o que eu nao conheco vira vazio, nunca token")
checar(uf_de({"id": "TUxC", "name": "Narnia"}) == "", "estado desconhecido -> ''")
checar(uf_de(None) == "" and uf_de("BR-SP") == "", "sem dict -> ''")
print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
