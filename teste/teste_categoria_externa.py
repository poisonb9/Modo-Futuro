# -*- coding: utf-8 -*-
"""A categoria externa (Nike) nasce fora da pagina e so' baixa ao clicar. Sem rede.

## ⛔ O QUE ESTA GUARDA PROTEGE

Decisao do Bryan em 16/09/2026: "nao quero o site lento". A Nike ate' R$ 150
sao 905 cartoes (372 KB) — quase dobra a pagina. Entao:

1. o cartao da Nike NAO pode estar no HTML do catalogo — so' o indice
   (nome, arquivo, contagem, passo);
2. o arquivo ao lado leva os cartoes no MESMO formato do AliExpress, e a
   pagina os trata igual (selo "novo", grafico so' com 3 dias);
3. instantaneo com mais de 24h => categoria FORA, nao categoria com preco
   velho (a mesma trava dos 24h que tirou 14 precos errados do ar em 15/09);
4. `guardar_catalogo` com feed vazio NAO sobrescreve o instantaneo anterior.

⚠️ Os casos negativos (3 e 4) sao TEOREMATICOS: idade > limite implica {}
por construcao da funcao, e lista vazia implica SystemExit antes do write.
Nao dependem de intuicao sobre o dado.
"""
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "paginas"))
import publicar_bio  # noqa: E402
from engine import awin  # noqa: E402

falhas = []


def checar(ok, oq):
    print(("  ok   " if ok else "  [x]  ") + oq)
    if not ok:
        falhas.append(oq)


def _iso(delta_h: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=delta_h)
            ).isoformat(timespec="seconds")


def _instantaneo(pasta: Path, idade_h: float, produtos: list) -> None:
    (pasta / "estado").mkdir(parents=True, exist_ok=True)
    (pasta / "estado" / "awin_catalogo.json").write_text(json.dumps(
        {"quando": _iso(idade_h), "teto": 150, "produtos": produtos}),
        encoding="utf-8")


NIKE = [
    {"id": "77", "nome": "Tênis Nike Court Vision", "preco": 149.99,
     "imagem": "https://x/a.jpg", "link": "https://www.awin1.com/pclick.php?p=77",
     "loja": "Nike BR", "categoria": "Calçados", "marca": "Nike", "origem": "awin"},
    {"id": "12", "nome": "Meia Nike Everyday", "preco": 59.98,
     "imagem": "https://x/b.jpg", "link": "https://www.awin1.com/pclick.php?p=12",
     "loja": "Nike BR", "categoria": "Meias", "marca": "Nike", "origem": "awin"},
    {"id": "33", "nome": "Boné Nike Heritage", "preco": 99.0,
     "imagem": "", "link": "https://www.awin1.com/pclick.php?p=33",
     "loja": "Nike BR", "categoria": "Acessórios", "marca": "Nike", "origem": "awin"},
    # ⚠️ loja SEM mapeamento em EXTERNAS: nao pode virar categoria sozinha
    {"id": "90", "nome": "Chuteira Outra Loja", "preco": 80.0,
     "imagem": "", "link": "https://www.awin1.com/pclick.php?p=90",
     "loja": "Loja Sem Mapa", "categoria": "", "marca": "", "origem": "awin"},
]

tmp = Path(tempfile.mkdtemp())
raiz_real = publicar_bio.RAIZ
try:
    publicar_bio.RAIZ = tmp

    print("1. INSTANTANEO FRESCO VIRA CATEGORIA, SO' A LOJA MAPEADA, MAIS BARATO PRIMEIRO")
    _instantaneo(tmp, 2, NIKE)
    ext = publicar_bio.produtos_externos()
    checar(list(ext) == ["Nike"], f"uma categoria, 'Nike' (veio {list(ext)})")
    prods = ext.get("Nike", {}).get("produtos", [])
    checar(len(prods) == 3, f"3 produtos da Nike BR, a outra loja fica fora ({len(prods)})")
    checar([p["preco"] for p in prods] == ["R$ 59,98", "R$ 99,00", "R$ 149,99"],
           "ordenados do mais barato pro mais caro, no formato R$ x,yy")
    p0 = prods[0] if prods else {}
    checar(p0.get("canal") == "Nike" and p0.get("id") == "awin:12",
           "canal 'Nike' e id prefixado 'awin:' (nao colide com o AliExpress)")
    checar(p0.get("loja") == "Nike", "a loja da externa e' a propria categoria (selo Nike)")
    checar(p0.get("pontos") == 0 and p0.get("serie") == [] and p0.get("queda") == 0,
           "sem serie: 0 pontos, sem grafico, sem queda — cai em 'achados novos'")
    checar(ext["Nike"]["passo"] == 50 and ext["Nike"]["arquivo"] == "nike.json",
           "passo 50 e arquivo nike.json (pedido do Bryan)")
    chaves = set(p0)
    esperadas = {"nome", "preco", "link", "imagem", "queda", "vendas", "ganho",
                 "antes", "dias", "pontos", "serie", "visto", "canal", "id", "combina",
                 "loja"}   # loja: campo do cartao desde 16/09 (selo + seletor)
    chaves -= {"nota", "ja_esteve", "vendeu", "vendedores", "fogo", "vitrine", "conferido"}   # so' o AliExpress / ML tem
    checar(chaves == esperadas, f"o cartao tem EXATAMENTE os campos do AliExpress (dif: {chaves ^ esperadas})")

    print()
    print("2. A SERIE GRADUA O PRODUTO — 3 dias viram grafico, mesma leitura do AliExpress")
    with (tmp / "estado" / "precos_vistos.jsonl").open("w", encoding="utf-8") as f:
        for d, v in (("2026-09-13", 79.9), ("2026-09-14", 69.9), ("2026-09-15", 59.98)):
            f.write(json.dumps({"id": "awin:12", "preco": v, "quando": d}) + "\n")
    ext = publicar_bio.produtos_externos()
    p0 = ext["Nike"]["produtos"][0]
    checar(p0["pontos"] == 3 and len(p0["serie"]) == 3,
           "3 dias na serie => 3 pontos e grafico de 3 pontos")
    checar(p0["queda"] > 0 and p0["antes"] == "R$ 79,90",
           f"queda medida contra o MAIOR dia visto (R$ 79,90), nao inventada (queda={p0['queda']})")

    print()
    print("3. ⛔ CASO NEGATIVO: instantaneo com 25h => categoria FORA")
    _instantaneo(tmp, 25, NIKE)
    checar(publicar_bio.produtos_externos() == {},
           "25h > 24h => {} (a trava dos 24h vale pra Nike como vale pro AliExpress)")
    _instantaneo(tmp, 23, NIKE)
    checar("Nike" in publicar_bio.produtos_externos(),
           "23h < 24h => entra (a guarda e' sensivel ao limite, nao reprova tudo)")

    print()
    print("4. O HTML LEVA O INDICE, NAO OS CARTOES")
    html, arquivos = publicar_bio.montar_catalogo()
    checar('"Nike": {"arquivo": "nike.json", "n": 3, "passo": 50}' in html,
           "var EXTERNOS traz nome, arquivo, contagem e passo")
    checar("Meia Nike Everyday" not in html,
           "o nome do produto da Nike NAO esta' no HTML (e' isso que mantem a pagina leve)")
    checar(set(arquivos) == {"nike.json"}, f"um arquivo ao lado: nike.json ({list(arquivos)})")
    j = json.loads(arquivos.get("nike.json", "{}"))
    checar(len(j.get("produtos", [])) == 3 and j.get("categoria") == "Nike",
           "nike.json tem os 3 cartoes e o nome da categoria")
    carimbado, marca = publicar_bio._carimbar_json(arquivos["nike.json"])
    checar(marca in carimbado and json.loads(carimbado)["carimbo"],
           "o carimbo entra no JSON e o JSON continua valido")

    print()
    print("5. SEM INSTANTANEO, A PAGINA SAI IGUAL A DE HOJE")
    (tmp / "estado" / "awin_catalogo.json").unlink()
    html, arquivos = publicar_bio.montar_catalogo()
    checar("  var EXTERNOS = {};" in html and arquivos == {},
           "EXTERNOS vazio e nenhum arquivo — nada muda pra quem ja' esta' no ar")

    print()
    print("6. ⛔ guardar_catalogo COM FEED VAZIO NAO APAGA O INSTANTANEO ANTERIOR")
    awin_estado = tmp / "estado" / "awin_catalogo.json"
    awin_estado.write_text('{"quando": "ANTES", "produtos": [1]}', encoding="utf-8")
    cat_real, est_real, pre_real = awin.catalogo, awin.CATALOGO_ESTADO, awin.PRECOS
    try:
        awin.CATALOGO_ESTADO = awin_estado
        awin.PRECOS = tmp / "estado" / "precos_vistos.jsonl"
        awin.catalogo = lambda teto=0.0, piso=0.0: []
        estourou = False
        try:
            awin.guardar_catalogo(teto=150)
        except SystemExit:
            estourou = True
        checar(estourou, "feed vazio levanta SystemExit")
        checar(awin_estado.read_text(encoding="utf-8") == '{"quando": "ANTES", "produtos": [1]}',
               "e o instantaneo anterior esta' INTACTO, byte a byte")

        print()
        print("7. A SERIE SO' GANHA PONTO QUANDO O PRECO MUDA")
        awin.PRECOS.write_text("", encoding="utf-8")
        awin.catalogo = lambda teto=0.0, piso=0.0: [dict(x) for x in NIKE[:2]]
        awin.guardar_catalogo(teto=150)
        n1 = len(awin.PRECOS.read_text(encoding="utf-8").splitlines())
        awin.guardar_catalogo(teto=150)          # mesmo preco
        n2 = len(awin.PRECOS.read_text(encoding="utf-8").splitlines())
        mudado = [dict(x) for x in NIKE[:2]]
        mudado[0]["preco"] = 139.99
        awin.catalogo = lambda teto=0.0, piso=0.0: mudado
        awin.guardar_catalogo(teto=150)
        n3 = len(awin.PRECOS.read_text(encoding="utf-8").splitlines())
        checar((n1, n2, n3) == (2, 2, 3),
               f"estreia grava 2, repeticao grava 0, uma mudanca grava 1 (veio {(n1, n2, n3)})")
        inst = json.loads(awin_estado.read_text(encoding="utf-8"))
        checar(len(inst["produtos"]) == 2 and inst["quando"] != "ANTES",
               "o instantaneo foi reescrito com os 2 produtos e data nova")
    finally:
        awin.catalogo, awin.CATALOGO_ESTADO, awin.PRECOS = cat_real, est_real, pre_real
finally:
    publicar_bio.RAIZ = raiz_real
    shutil.rmtree(tmp, ignore_errors=True)

print()
print("8. A PAGINA: estrutura que faz o 'so' baixa ao clicar' existir")
HTML = (RAIZ / "paginas" / "todos.html").read_text(encoding="utf-8")
CODIGO = "\n".join(re.sub(r"\s*//.*$", "", L) for L in HTML.splitlines())
checar("  var EXTERNOS = {};" in HTML, "o marcador var EXTERNOS = {} existe")
seg = re.search(r"function soNoSegmento\(p\) \{(.*?)\n  \}", CODIGO, re.S)
checar(bool(seg) and "externa(p.canal)" in seg.group(1),
       "toda externa e' so'-no-segmento (nunca no rolar principal)")
des = re.search(r"function desenhar\(\) \{(.*?)\n  \}", CODIGO, re.S)
checar(bool(des) and "carregarExterno(canal, desenhar)" in des.group(1),
       "desenhar() baixa a externa antes de desenhar")
car = re.search(r"function carregarExterno\(nome, depois\) \{(.*?)\n  \}", CODIGO, re.S)
corpo = car.group(1) if car else ""
checar("fetch(EXTERNOS[nome].arquivo" in corpo, "o fetch usa o arquivo do indice (relativo)")
checar("r.json()" in corpo and ".catch(" in corpo and "tentar de novo" in corpo,
       "HTML no lugar de JSON cai no aviso com 'tentar de novo', nao em grade vazia")
url = re.search(r"function daUrl\(\) \{(.*?)\n  \}", CODIGO, re.S)
checar(bool(url) and "Object.keys(EXTERNOS)" in url.group(1),
       "/#nike abre a categoria mesmo antes de ela estar em PRODUTOS")
checar("EXTERNOS[canal].passo" in CODIGO, "o passo do 'ver mais' vem do indice (50 na Nike)")
checar('externa(canal) && atual === "todos"' in CODIGO,
       "a externa abre pelos mais baratos quando o filtro e' 'tudo'")

print()
print("tudo verde" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
