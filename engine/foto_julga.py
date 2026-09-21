# -*- coding: utf-8 -*-
"""A foto serve de CAPA? Quem responde e' um modelo de visao, nao um proxy.

## ⛔ POR QUE ESTE MODULO EXISTE (21/09/2026)

A regua da capa escolheu um produto impecavel em numero -- 62.879 vendas,
19,4% de ganho, 61,5% de queda, 8 pontos de serie -- e a foto era uma
COLAGEM de quatro cenas com o texto "Desk / Restroom / Stairs / Porch"
queimado por cima. O produto aparecia pequeno em cada quadro.

Nenhuma medida nossa pegava isso, e nao por descuido:

    `foto_limpa` (OCR)  mede TEXTO ....... esta foto tem 0,0356, ABAIXO da
                                          mediana de 0,0568 das 920 medidas
    `fidelidade` (CLIP) mede SEMELHANCA .. contra a foto principal -- e esta
                                          E' a principal

O handoff do mesmo dia ja' tinha escrito a frase inteira: *"o que separa e'
'a foto mostra o produto INTEIRO', que nenhuma das duas mede"*. Os dois sao
PROXIES. Este modulo pergunta a coisa em si.

## ⭐ O QUE FOI MEDIDO ANTES DE LIGAR ISTO

Rodada de aferição em 6 fotos, `gemini-3.6-flash`, temperatura 0:

    Organizador de panelas ..... colagem=nao  quadros=1  texto=nao  nota 9
    Pulverizador de jardim ..... colagem=nao  quadros=1  texto=nao  nota 8
    Bolsa tatica ............... colagem=nao  quadros=1  texto=SIM  nota 6
    Fita organizadora .......... colagem=nao  quadros=1  texto=nao  nota 6
    Carregador GaN ............. colagem=nao  quadros=1  texto=SIM  nota 5
    Luz LED (a capa do dia) .... colagem=SIM  quadros=4  texto=SIM  nota 3

⭐ UMA acusacao em seis, na certa, e as outras cinco GRADUADAS -- a nota 9 e'
a foto limpa, as 5 e 6 sao as que tem texto ou fundo poluido. Isso e' o CASO
NEGATIVO que a casa exige: um detector que acusa tudo passaria no positivo.

## ⚠️ A PROCEDENCIA DISTO E' `AFIRMADO`, NAO MEDIDO

E' julgamento de modelo, nao regua deterministica. Por isso:

  - a resposta e' CACHEADA por URL e fica versionada, para dar pra auditar
    e para o mesmo julgamento nao mudar de publicacao em publicacao;
  - foto SEM julgamento NAO reprova. Ela cai na regua antiga. Guarda que
    trava a publicacao quando a API esta' fora e' pior que guarda nenhuma.

## ⚠️ A DISPONIBILIDADE E' INSTAVEL, MEDIDO NO MESMO DIA

Para o `gemini-3.6-flash` responder uma vez foram precisas CINCO chaves:
duas devolveram `503 high demand`, uma `403`, uma `429`. Por isso o rodizio
de `engine.keys` e o `queimar()` em 429/403 -- e por isso o modulo trabalha
por LOTE, salvando o cache a cada resposta, para nunca perder o que ja' foi
pago em tempo.

⛔ `gemini-2.5-flash` MORREU: devolve 404 com "no longer available to new
users. Please update your code to use models/gemini-3.6-flash".
"""
import base64
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MEDIDAS = RAIZ / "estado" / "fotos_julgadas.json"

# ⭐ O 3.6 e' o que a propria API manda usar no lugar do 2.5 aposentado.
# O 3.5 tambem responde e deu o MESMO veredito na foto da colagem; fica como
# reserva porque em 21/09 ele atendeu de primeira enquanto o 3.6 pediu cinco
# chaves. Modelo de reserva nao e' luxo aqui: o 503 e' frequente.
MODELOS = ("gemini-3.6-flash", "gemini-3.8-flash",
           "gemini-3-flash-preview", "gemini-3.5-flash")

# ⭐ QUATRO PORTAS, E NAO UMA. MEDIDO em 21/09/2026 com o lote rodando: o
# gargalo deixou de ser cota (as chaves queimadas pararam em 9 de 28) e
# passou a ser `503 high demand` do modelo. Com uma porta so', cada foto
# gastava minutos batendo na mesma que estava cheia.
#
# ⚠ E AS QUATRO SAO CONFIAVEIS PORQUE FORAM TRIANGULADAS, nao porque
# estavam na lista. Na foto da colagem, tres modelos independentes deram o
# veredito IDENTICO:
#
#   gemini-3.6-flash ........ colagem=True quadros=4 nota=3
#   gemini-3.8-flash ........ colagem=True quadros=4 nota=3
#   gemini-3-flash-preview .. colagem=True quadros=4 nota=3
#
# ⛔ O `gemini-3.1-flash-lite` NAO entra, mesmo sendo 10x mais rapido: ele
# acusou colagem onde nao havia e inflou notas (ver o cabecalho deste
# arquivo). Velocidade nao compra veredito.

# ⭐ A FOTO VAI REDUZIDA A 512 px. MEDIDO: 374 KB -> 42 KB, e cinco
# tentativas caem de 36 s para 7,3 s. O ganho nao e' no acerto -- e' no
# CUSTO DA FALHA, que e' o que domina quando a maioria das tentativas
# devolve 503. O julgamento (colagem, texto, produto inteiro) nao precisa de
# resolucao: sao perguntas de composicao, nao de detalhe.
LADO_MAX = 512

RUBRICA = (
    "Voce julga a FOTO PRINCIPAL de um anuncio para uma vitrine de ofertas. "
    "Responda SO' com JSON, sem markdown, neste formato exato:\n"
    '{"colagem": true|false, "quadros": <int>, "texto_queimado": true|false, '
    '"produto_inteiro": true|false, "fundo_limpo": true|false, '
    '"nota": <0 a 10>, "porque": "<ate 12 palavras>"}\n\n'
    "Definicoes:\n"
    "- colagem: a imagem e' dividida em 2 ou mais quadros/cenas separadas.\n"
    "- quadros: quantos quadros distintos. 1 se for foto unica.\n"
    "- texto_queimado: ha' texto/legenda desenhado sobre a imagem.\n"
    "- produto_inteiro: o produto aparece por completo e grande na cena.\n"
    "- fundo_limpo: fundo neutro ou cena simples, sem poluicao.\n"
    "- nota: quanto esta foto serve como CAPA de vitrine (10 = perfeita)."
)

_TRAVA = threading.Lock()
_CACHE: dict | None = None


def _cache() -> dict:
    global _CACHE
    if _CACHE is None:
        try:
            _CACHE = json.loads(MEDIDAS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _CACHE = {}
    return _CACHE


def _gravar() -> None:
    MEDIDAS.parent.mkdir(parents=True, exist_ok=True)
    MEDIDAS.write_text(
        json.dumps(_cache(), ensure_ascii=False, sort_keys=True, indent=0),
        encoding="utf-8")


def julgado(url: str) -> dict:
    """O julgamento em cache, ou {} se a foto nunca foi julgada.

    ⚠️ NAO chama a API. E' o que o publicador usa: ele tem de ser rapido e
    nao pode depender de rede na hora de montar a pagina.
    """
    return _cache().get(str(url or "")) or {}


def serve_de_capa(url: str, piso: int = 7) -> bool:
    """A foto pode abrir a vitrine?

    ⚠ FALHA ABERTA, DE PROPOSITO. Foto sem julgamento devolve True: a
    guarda existe para BARRAR colagem, nao para esvaziar a capa quando a API
    esta' fora ou o cache ainda nao cobriu a foto nova do dia.
    """
    j = julgado(url)
    if not j:
        return True
    if j.get("colagem"):
        return False
    if j.get("texto_queimado"):
        # ⛔ TEXTO QUEIMADO NA CAPA BRIGA COM OS NOSSOS CHIPS. MEDIDO no ar
        # em 21/09/2026: a capa do Carregador 120W tem "120W Output" desenhado
        # na foto, e o selo de queda e a estrela caem EM CIMA dele -- dois
        # textos disputando o mesmo canto. Nenhum leito de CSS conserta isso,
        # porque o ruido esta' DENTRO da imagem.
        # ⚠ O proprio juiz ja' avisava: nota 8, "otima qualidade e fundo
        # limpo, porem contem texto sobreposto". O dado estava la' e a regua
        # nao lia.
        # ⭐ E da' para exigir: dos 14 candidatos, 5 tem foto sem colagem E
        # sem texto -- tres deles com nota 10.
        return False
    return int(j.get("nota") or 0) >= piso


def melhor_foto(principal: str, extras=(), piso: int = 7) -> str:
    """A melhor foto JULGADA entre a principal e as extras do anuncio.

    ⭐ ESCOLHER, E NAO EDITAR. MEDIDO em 21/09/2026: 160 dos 165 produtos do
    instantaneo guardam fotos extras, com mediana de 5 por produto -- a capa
    daquele dia tinha 5, e a colagem era so' UMA delas. Nao ha' motivo para
    pedir a um modelo que desenhe nada: basta olhar as que ja' temos.

    ⛔ E EDITAR A FOTO ESTA' FORA, por medida do proprio projeto. O
    `engine/fidelidade.py` registra que o inpainting REFEZ o produto com
    menos detalhe e ainda assim tirou 0,9786 -- acima de qualquer limiar util.
    A guarda de fidelidade NAO pega degradacao de qualidade. Redesenhar o
    produto quebraria a ordem de 15/09 ("nao pode ir pra internet o produto
    que nao e' de acordo") sem que nada ficasse vermelho.
    """
    cands = [u for u in ([principal] + list(extras or [])) if u]
    julgadas = [(int(julgado(u).get("nota") or 0), u) for u in cands if julgado(u)]
    if not julgadas:
        return principal
    boa = [(n, u) for n, u in julgadas
           if not julgado(u).get("colagem") and n >= piso]
    if boa:
        boa.sort(key=lambda x: -x[0])
        return boa[0][1]
    return principal


def _baixar(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    bruta = urllib.request.urlopen(req, timeout=60).read()
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(bruta)).convert("RGB")
        im.thumbnail((LADO_MAX, LADO_MAX))
        bo = io.BytesIO()
        im.save(bo, "JPEG", quality=82)
        return bo.getvalue()
    except Exception:  # noqa: BLE001
        return bruta          # sem PIL, manda a original: pior, nao quebrado


def _pedir(modelo: str, chave: str, img: bytes) -> tuple[str, str]:
    corpo = {
        "contents": [{"parts": [
            {"text": RUBRICA},
            {"inline_data": {"mime_type": "image/jpeg",
                             "data": base64.b64encode(img).decode()}},
        ]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 8192},
    }
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}"
           f":generateContent?key={chave}")
    req = urllib.request.Request(
        url, data=json.dumps(corpo).encode(),
        headers={"Content-Type": "application/json"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        return str(e.code), ""
    except Exception:  # noqa: BLE001
        return "rede", ""
    try:
        partes = d["candidates"][0].get("content", {}).get("parts") or []
        return "ok", "".join(p.get("text", "") for p in partes).strip()
    except Exception:  # noqa: BLE001
        return "vazio", ""


def _json_do_texto(txt: str) -> dict:
    """⚠️ O modelo as vezes embrulha em ```json ... ``` mesmo mandado nao."""
    t = txt.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t[:4].lower() == "json":
            t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return {}
    try:
        return json.loads(t[i:j + 1])
    except ValueError:
        return {}


# ⭐ NO 503 A GENTE INSISTE (ordem do Bryan, 21/09). E a razao e' que os
# tres erros NAO sao a mesma coisa:
#
#   503 high demand .. FILA do lado do Google. Passa sozinho. Insistir.
#   429 sem cota ..... a CHAVE acabou por hoje. Queimar e trocar.
#   403 sem acesso ... a CHAVE nao pode. Queimar e trocar.
#
# ⛔ Ate' agora eu tratava os tres como "falhou" e desistia em 3 tentativas
# por modelo -- jogando fora foto que ia passar na rodada seguinte. MEDIDO
# nas 28 chaves de uma vez: 14 devolveram 503 e so' 5 devolveram 429.
# Desistir do 503 era desistir da METADE do parque.
TETO_RODADAS = 40
ESPERA_MAX = 30


def _julgar_uma(url: str, rod) -> dict:
    """Baixa, reduz e julga UMA foto, insistindo enquanto for fila.

    ⚠ So' desiste quando a rodada inteira foi 429/403 -- ai' nao e' fila,
    e' parque sem cota, e esperar nao resolve.
    """
    import time
    try:
        img = _baixar(url)
    except Exception:  # noqa: BLE001
        return {}
    for rodada in range(TETO_RODADAS):
        houve_fila = False
        for modelo in MODELOS:
            for _ in range(2):
                chave = rod.proxima()
                estado, txt = _pedir(modelo, chave, img)
                if estado == "ok":
                    v = _json_do_texto(txt)
                    if v:
                        v["modelo"] = modelo
                        v["rodadas"] = rodada + 1
                        return v
                elif estado in ("429", "403"):
                    rod.queimar(chave)
                else:
                    houve_fila = True       # 503 ou erro de rede
        if not houve_fila:
            return {}
        time.sleep(min(3 * (rodada + 1), ESPERA_MAX))
    return {}

# ⭐ EM PARALELO, e o numero saiu de MEDIDA. Em 21/09/2026 eu testei as 28
# chaves com uma chamada cada, ao mesmo tempo:
#
#   503 high demand ... 14     429 (sem cota) ... 5
#   403 (sem acesso) ...  2     erro de rede ..... 4
#   atenderam ..........  3
#
# ⛔ EU TINHA CONCLUIDO "a cota acabou" E ESTAVA ERRADO. A cota explica 5 de
# 28; o que domina e' o 503, que e' fila do lado do Google e PASSA. Serial,
# cada foto esperava a fila inteira; em paralelo, as que pegam porta aberta
# andam enquanto as outras esperam.
#
# ⚠ 8 E NAO 28: o gargalo nao e' a nossa maquina, e martelar com 28
# threads em cima de um servico que ja' responde 503 e' pedir para virar
# 429 de verdade. Com 3 chaves atendendo por vez, 8 ja' satura.
PARALELO = 8


def medir(urls, forcar: bool = False, teto: int = 0, paralelo: int = PARALELO) -> dict:
    """Julga as fotos que faltam e grava o cache. Devolve o que julgou agora."""
    from concurrent.futures import ThreadPoolExecutor
    from engine import keys
    rod = keys.gemini()
    novos: dict = {}
    pendentes = [u for u in dict.fromkeys(urls)
                 if u and (forcar or not julgado(u))]
    if teto:
        pendentes = pendentes[:teto]
    total = len(pendentes)
    print(f"julgando {total} foto(s) com {len(rod)} chave(s), {paralelo} em paralelo")
    feitas = [0]

    def tarefa(url: str) -> None:
        v = _julgar_uma(url, rod)
        with _TRAVA:
            feitas[0] += 1
            n = feitas[0]
            if v:
                _cache()[url] = v
                novos[url] = v
                _gravar()   # ⭐ a cada resposta: 503 no meio do lote nao
                            # pode custar o que ja foi obtido
                print(f"  [{n}/{total}] colagem={v.get('colagem')} "
                      f"quadros={v.get('quadros')} nota={v.get('nota')} "
                      f"{str(v.get('porque'))[:38]}")
            else:
                print(f"  [{n}/{total}] sem resposta -- fica sem julgamento")

    with ThreadPoolExecutor(max_workers=paralelo) as ex:
        list(ex.map(tarefa, pendentes))
    return novos

def _distribuicao() -> None:
    c = _cache()
    if not c:
        print("nenhuma foto julgada ainda")
        return
    notas = [v.get("nota") for v in c.values() if isinstance(v.get("nota"), int)]
    colagens = sum(1 for v in c.values() if v.get("colagem"))
    textos = sum(1 for v in c.values() if v.get("texto_queimado"))
    inteiros = sum(1 for v in c.values() if v.get("produto_inteiro"))
    print(f"julgadas: {len(c)}")
    print(f"  colagem .......... {colagens} ({colagens * 100 // max(len(c), 1)}%)")
    print(f"  texto queimado ... {textos} ({textos * 100 // max(len(c), 1)}%)")
    print(f"  produto inteiro .. {inteiros} ({inteiros * 100 // max(len(c), 1)}%)")
    print("  notas:")
    for n in range(10, -1, -1):
        q = notas.count(n)
        if q:
            print(f"    {n:2}  {'#' * min(q, 50)} {q}")
    for piso in (9, 8, 7, 6, 5):
        ok = sum(1 for v in c.values()
                 if not v.get("colagem") and (v.get("nota") or 0) >= piso)
        print(f"  passariam com 'sem colagem e nota >= {piso}': {ok}")


if __name__ == "__main__":
    sys.path.insert(0, str(RAIZ))
    sys.path.insert(0, str(RAIZ / "paginas"))
    if "--distribuicao" in sys.argv:
        _distribuicao()
        raise SystemExit
    import publicar_bio as pb
    fotos = [p.get("imagem") for p in pb.produtos_todos() if p.get("imagem")]
    teto = 0
    if "--teto" in sys.argv:
        teto = int(sys.argv[sys.argv.index("--teto") + 1])
    par = PARALELO
    if "--paralelo" in sys.argv:
        par = int(sys.argv[sys.argv.index("--paralelo") + 1])
    medir(fotos, forcar="--forcar" in sys.argv, teto=teto, paralelo=par)
    print()
    _distribuicao()
