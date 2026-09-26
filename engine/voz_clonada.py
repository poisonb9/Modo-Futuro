"""Dublagem com a voz clonada do Bryan (Chatterbox Multilingual, self-hosted,
grátis, MIT — ver [[modofuturo]] handoff 04/08/2026).

Roda 100% na nuvem do Actions (CPU, sem GPU) — não na máquina do Bryan, que é
fraca demais pra isso. Medido em 04/08/2026 (run #30867337829):
  - instalar dependências: ~165s
  - carregar o modelo:      ~48s
  - gerar 1 frase (24 palavras): ~154s

O modelo é caro de carregar (48s) — por isso fica em cache no módulo e só
carrega UMA VEZ por execução do main.py, reaproveitado entre todos os
clipes do lote (`--qtd`), não recarregado por clipe.

Watermarker (resemble-perth) tem um bug de ambiente (pkg_resources faltando
em alguns setups) que derruba o carregamento do modelo com
`TypeError: 'NoneType' object is not callable` — contornado com um stub
vazio antes do import, ao custo de o áudio sair sem o carimbo "gerado por
IA" da Resemble (não achamos alternativa: 3 tentativas de consertar a causa
raiz falharam, ver commits 61bc8b8/202e3f6/98bfa2a).
"""
import datetime
import re
import shutil
import time
from pathlib import Path

from . import conferencia, dinamica, midia

IDIOMA_PADRAO = "pt"
# resumo da conferencia do ULTIMO gerar_trilha (o main.py grava no post.json)
ULTIMO_QC: dict = {}
_MODELO = None
_PAUSA_ENTRE_FRASES_S = 0.15

# ⭐ CALIBRAGEM DA EXPRESSIVIDADE (26/09/2026, item 4 da dublagem, "urgente"
# pelo dono). Ate' aqui so' a `exaggeration` ia ao modelo (da dinamica do
# original, 0,35-0,75); o `cfg_weight` ficava no padrao 0,5. Os praticantes
# deixam a voz de IA natural soltando o controle e subindo o estilo (acervo
# F123413, F123435, F123795, na linguagem do ElevenLabs); no Chatterbox o par
# equivalente e' exaggeration + cfg_weight baixo (~0,3) — isso vem da
# documentacao do Chatterbox, NAO do acervo.
#
# ⚠️ None = padrao do modelo (comportamento de antes). O valor so' muda
# depois de o dono OUVIR a comparacao (`ferramentas/previa_voz.py`,
# workflow `previa_voz.yml`). Env `VOZ_CFG_PESO` sobrepoe, pra testar.
VOZ_CFG_PESO: float | None = None

# ⭐ Frase ancorada no tempo do original (item 2, ver `_ancorar`). Env
# `DUB_ANCORAR=0` volta ao modo antigo (frases emendadas desde 0 s).
import os as _os
ANCORAR_FRASES = _os.environ.get("DUB_ANCORAR", "1") != "0"

# ⭐ MOTOR DA VOZ = D (26/09/2026, decisao do dono apos ouvir a previa:
# "D para os dois" — Bryan e Bruna). O edge-tts INTERPRETA a frase (boa
# entonacao em pt-BR, ~2 s) e o ChatterboxVC (mesmo pacote, MIT) troca SO' o
# timbre pelo da amostra clonada. Medido na previa (run 36207479880): ~28 s
# por frase contra ~77 s da A, 2,7x mais rapida.
#
# ⚠️ Falha ABERTA para a A: sem o VC, sem rede pro edge, ou idioma que nao e'
# portugues, a frase sai no Chatterbox TTS de sempre — clipe com a voz antiga
# e' aceitavel, clipe sem voz nao. Env `VOZ_MOTOR=A` volta tudo pra A.
VOZ_MOTOR = (_os.environ.get("VOZ_MOTOR") or "D").strip().upper()
# voz do edge-tts que interpreta a frase, pelo DONO da amostra
EDGE_MASCULINA = "pt-BR-AntonioNeural"
EDGE_FEMININA = "pt-BR-ThalitaMultilingualNeural"
_VC = None
_VC_INDISPONIVEL = False
# refeita da conferencia na D (dono, 26/09: "refazer na D com outra
# velocidade"): o edge le' a mesma frase mais devagar -> leitura diferente,
# palavra engolida tende a sair inteira, e o clipe inteiro fica no MESMO
# timbre (refazer na A misturava a voz antiga no meio). motor "D-" = isto.
REFEITA_VELOCIDADE = "-10%"


def _bypass_watermarker():
    import perth

    class _SemMarcaDagua:
        def __init__(self, *a, **k):
            pass

        def apply_watermark(self, wav, sample_rate=None):
            return wav

    perth.PerthImplicitWatermarker = _SemMarcaDagua


def _carregar_modelo():
    global _MODELO
    if _MODELO is None:
        _bypass_watermarker()
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        print("      carregando modelo de voz clonada (Chatterbox)...")
        _MODELO = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    return _MODELO


def _enfase_aceita(modelo, enfase: float | None) -> dict:
    """`exaggeration` (e `cfg_weight`, se calibrado) que o modelo aceitar.

    ⚠️ DESCOBERTO EM EXECUCAO, NAO SUPOSTO. O Chatterbox nao roda na maquina
    do Bryan (nem cabe: a GPU e a CPU dela ja' vivem no limite), entao eu nao
    tinha como inspecionar a assinatura antes de escrever isto. Passar um
    parametro que a versao instalada nao conhece derrubaria TODA sintese com
    TypeError — e derrubaria depois de o run ja' ter pago corte e transcricao.
    Perguntar ao proprio modelo custa uma linha e nao pode errar.
    """
    import os
    extra = {}
    try:
        import inspect
        aceita = inspect.signature(modelo.generate).parameters
    except Exception:
        return {}
    if enfase is not None and "exaggeration" in aceita:
        extra["exaggeration"] = float(enfase)
    cfg = os.environ.get("VOZ_CFG_PESO") or VOZ_CFG_PESO
    if cfg not in (None, "") and "cfg_weight" in aceita:
        extra["cfg_weight"] = float(cfg)
    return extra


def _edge_da_amostra(amostra_voz: Path) -> str:
    """Voz do edge-tts do mesmo sexo da amostra (Thalita p/ Bruna, Antonio p/ Bryan)."""
    fem = Path(_os.environ.get("AMOSTRA_VOZ_FEMININO") or "bruna_amostra.wav").stem.lower()
    s = amostra_voz.stem.lower()
    return EDGE_FEMININA if (s == fem or "bruna" in s) else EDGE_MASCULINA


def _falar_d(texto: str, destino: Path, amostra_voz: Path,
            velocidade: str | None = None) -> Path | None:
    """Motor D: edge-tts -> ChatterboxVC(timbre da amostra). None = use a A."""
    global _VC, _VC_INDISPONIVEL
    if _VC_INDISPONIVEL:
        return None
    try:
        if _VC is None:
            _bypass_watermarker()
            from chatterbox.vc import ChatterboxVC
            print("      carregando conversor de timbre (ChatterboxVC)...", flush=True)
            _VC = ChatterboxVC.from_pretrained(device="cpu")
    except Exception as e:
        # uma vez so': sem o VC, o lote inteiro segue na A sem tentar de novo
        _VC_INDISPONIVEL = True
        print(f"        [voz D] ChatterboxVC indisponivel ({type(e).__name__}: "
              f"{str(e)[:80]}) — lote segue na voz A", flush=True)
        return None
    try:
        import torchaudio as ta
        from . import dublagem
        t0 = time.monotonic()
        base = destino.with_name(destino.stem + "_edge.mp3")
        # numero por extenso e Guia de voz: o `dublagem._sintetizar` ja' aplica
        dublagem._falar(texto, base, _edge_da_amostra(amostra_voz), velocidade)
        t1 = time.monotonic()
        wav = _VC.generate(audio=str(base), target_voice_path=str(amostra_voz))
        ta.save(str(destino), wav, _VC.sr)
        print(f"        [voz D] edge {t1 - t0:.1f}s + timbre "
              f"{time.monotonic() - t1:.1f}s", flush=True)
        return destino
    except Exception as e:
        print(f"        [voz D] falhou nesta frase ({type(e).__name__}: "
              f"{str(e)[:80]}) — usando a voz A", flush=True)
        return None


def _falar(texto: str, destino: Path, amostra_voz: Path, idioma: str,
           enfase: float | None = None, motor: str | None = None) -> Path:
    m = motor or VOZ_MOTOR
    if m in ("D", "D-") and (idioma or "").lower().startswith("pt"):
        vel = REFEITA_VELOCIDADE if m == "D-" else None
        if _falar_d(texto, destino, amostra_voz, vel):
            return destino
    import torchaudio as ta
    from . import numeros
    modelo = _carregar_modelo()
    # Numero por extenso SO' aqui, no ponto em que o texto vira audio. A
    # legenda na tela continua com o digito ("2030" le' melhor que "dois mil
    # e trinta" escrito), e o `timing` devolvido segue com o texto original.
    # ⭐ receita (26/09): "240 g" tem de sair "duzentos e quarenta GRAMAS", nao
    # "ge'". Unidade vira palavra ANTES do numeros.py (trazido do `pipeline`).
    # So' no modo receita: em chips, "5g" nao e' grama.
    import config
    if config.modo_receita():
        from . import conversoes
        texto = conversoes.para_fala(texto)
    falado = numeros.por_extenso(texto)
    # ⭐ 26/09: nome dito como o canal fala ("Risabae" -> "Rissabé"), pela
    # tabela de pronuncia do Guia de voz do canal. SO' aqui — a legenda nao muda.
    from . import guia_voz
    falado = guia_voz.para_fala(falado)
    # Os tres sub-passos sao marcados SEPARADAMENTE de proposito. Nos runs
    # #188 e #189 (31/08/2026) o processo congelou logo apos o Chatterbox
    # terminar a amostragem de uma frase — mas nao dava pra saber se parou
    # dentro do `generate`, no `ta.save` ou ja' na proxima chamada. Sem
    # separar, o log so' diria "parou em algum lugar de _falar".
    t0 = time.monotonic()
    print(f"        [tts] gerando ({len(falado)} chars)...", flush=True)
    extra = _enfase_aceita(modelo, enfase)
    wav = modelo.generate(falado, audio_prompt_path=str(amostra_voz),
                          language_id=idioma, **extra)
    t1 = time.monotonic()
    print(f"        [tts] gerado em {t1 - t0:.1f}s, gravando wav...",
          flush=True)
    ta.save(str(destino), wav, modelo.sr)
    print(f"        [tts] wav gravado em {time.monotonic() - t1:.1f}s",
          flush=True)
    return destino


def _ajustar_duracao(audio: Path, alvo_s: float, destino: Path) -> Path:
    """Encaixa o áudio no tamanho do clipe (`render.vertical` usa
    `-shortest`, então o áudio TEM que ter pelo menos a duração do vídeo,
    senão o vídeo final sai cortado).

    Narração mais CURTA que o clipe: preenche o resto com SILÊNCIO no
    final, sem mexer no ritmo da fala — esticar/desacelerar (como fazia
    antes, sempre) deixava a voz arrastada mesmo quando a diferença era
    pequena (Bryan reportou "ficou lenta" com um fator de só 0.86x, ou
    seja, eu tava desacelerando a fala em 14% à toa). Narração mais LONGA
    que o clipe: acelera (até 1.6x, acima disso fica robótico/irreconhecível
    — já tinha esse teto antes)."""
    dur = midia.duracao(audio)
    if dur <= 0:
        shutil.copy(audio, destino)
        return destino

    if dur <= alvo_s:
        falta = alvo_s - dur
        midia.roda(["ffmpeg", "-y", "-i", str(audio),
                    "-af", f"apad=pad_dur={falta:.3f}",
                    "-ar", "44100", str(destino)])
        return destino

    fator = min(1.6, dur / max(0.1, alvo_s))
    midia.roda(["ffmpeg", "-y", "-i", str(audio),
                "-filter:a", f"atempo={fator:.3f}",
                "-ar", "44100", str(destino)])
    return destino


# Abreviações comuns em português — o "." delas NÃO é fim de frase.
# Sem isso, "Dr. Yao" virava duas frases ("Dr." + "Yao..."), isolando
# "Yao" como uma síntese de TTS separada e curtíssima — o Chatterbox
# reagiu com uma pausa longa e um ruído de respiração ali (Bryan
# reportou em 05/08/2026 ouvindo o clipe 002).
_ABREVIACOES = {
    "dr", "dra", "sr", "sra", "srta", "prof", "profa", "eng", "engo",
    "gen", "cel", "cap", "pe", "irmã", "dom", "exmo", "exma",
    "jr", "mr", "mrs", "ms", "st",
}


# Limites da pausa copiada do original, em segundos.
#
# ⚠️ SEM TETO A DINAMICA VIRA BURACO. Podcast tem silencio de varios segundos;
# copiar isso pro corte de 90s destroi a retencao — e retencao e' o gargalo
# MEDIDO do @modofuturo (a audiencia sai em 0:02). O piso preserva a
# respiracao entre frases que ja' existia antes desta mudanca.
_PAUSA_MIN_S = 0.12
_PAUSA_MAX_S = 0.60


def _aplicar_ganho(caminho: Path, ganho: float) -> Path:
    """Reescreve o wav com o volume multiplicado por `ganho`.

    E' o item 2 do pedido: o envelope do original aplicado na dublagem — os
    picos e as quedas, nao o volume medio.

    ⚠️ FALHA ABERTA: se o ffmpeg reclamar, devolve o arquivo ORIGINAL e a
    frase entra sem envelope. Perder a dinamica de uma frase e' pequeno;
    perder a frase e' grande.
    """
    saida = caminho.with_name(caminho.stem + "_g.wav")
    try:
        midia.roda(["ffmpeg", "-y", "-v", "error", "-i", str(caminho),
                    "-af", f"volume={ganho:.4f}", str(saida)])
    except Exception as e:
        print(f"        [!] ganho nao aplicado ({str(e)[:50]})", flush=True)
        return caminho
    return saida if saida.exists() else caminho


def _janelas_por_segmento(segmentos: list[dict],
                          frases: list[str]) -> list[tuple[float, float]]:
    """(inicio, fim) de cada frase pela POSICAO dela no texto dos segmentos.

    As frases saem de juntar o texto dos segmentos e cortar na pontuacao, na
    mesma ordem — entao cada frase e' um trecho contiguo desse texto. Acha o
    trecho, ve' em que segmento(s) cai e interpola pelo numero de letras.
    Devolve [] se alguma frase nao for achada (ai' vale a divisao proporcional).
    """
    pedacos, texto, pos = [], "", 0
    for s in segmentos:
        t = (s.get("texto") or "").strip()
        if not t:
            continue
        if texto:
            texto += " "
            pos += 1
        pedacos.append((pos, pos + len(t), float(s["inicio"]), float(s["fim"])))
        texto += t
        pos += len(t)
    if not pedacos:
        return []

    def tempo(off: int) -> float:
        for a, b, ti, tf in pedacos:
            if off <= b:
                frac = min(1.0, max(0.0, (off - a) / max(1, b - a)))
                return ti + frac * (tf - ti)
        return pedacos[-1][3]

    janelas, cursor = [], 0
    for f in frases:
        achou = texto.find(f.strip(), cursor)
        if achou < 0:
            return []
        fim_off = achou + len(f.strip())
        janelas.append((tempo(achou), tempo(fim_off)))
        cursor = fim_off
    return janelas


def _janelas_das_frases(segmentos: list[dict],
                        frases: list[str]) -> list[tuple[float, float]]:
    """Onde cada frase sintetizada cai no VIDEO ORIGINAL.

    ⚠️ E' APROXIMACAO, e precisa ser dita como tal. As frases da dublagem nao
    correspondem uma a uma aos segmentos da transcricao — o texto e' traduzido
    e reescrito, entao a contagem muda. Aqui o intervalo falado do original e'
    dividido proporcionalmente ao TAMANHO de cada frase, que e' a melhor
    correspondencia disponivel sem alinhamento forcado.

    Consequencia honesta: a dinamica segue o CONTORNO do original (onde ele
    sobe e onde cai), nao o instante exato de cada palavra.
    """
    validos = [s for s in segmentos
               if s.get("inicio") is not None and s.get("fim") is not None]
    if not validos or not frases:
        return []
    # ⭐ 26/09: primeiro tenta achar cada frase DENTRO do texto do seu
    # segmento e interpolar o tempo ali. A divisao proporcional abaixo espalha
    # pelo intervalo inteiro e ignora onde cada segmento comeca (a ultima
    # frase de um teste caiu 1,5 s antes da fala original dela).
    por_segmento = _janelas_por_segmento(validos, frases)
    if por_segmento:
        return por_segmento
    ini = float(min(s["inicio"] for s in validos))
    fim = float(max(s["fim"] for s in validos))
    if fim <= ini:
        return []
    total = sum(max(1, len(f)) for f in frases)
    janelas, cursor = [], ini
    for f in frases:
        largura = (fim - ini) * (max(1, len(f)) / total)
        janelas.append((cursor, min(fim, cursor + largura)))
        cursor += largura
    return janelas


def _dividir_frases(texto: str) -> list[str]:
    """Divide pela pontuação de fim de frase (. ! ?), não por janela de
    tempo arbitrária — cada pedaço vira uma chamada de TTS curta, que é o
    regime em que o Chatterbox soa bem (ver módulo: ~154s pra 24 palavras;
    um texto de 90s inteiro numa síntese só saiu arrastado e com dicção
    ruim, medido com o Bryan em 05/08/2026).

    Protege abreviações (Dr., Sr., etc.) antes de cortar — o "." delas não
    marca fim de frase."""
    texto = texto.strip()

    def _proteger(m: re.Match) -> str:
        return m.group(0)[:-1] + "\x00"

    padrao_abrev = r"\b(?:" + "|".join(re.escape(a) for a in _ABREVIACOES) + r")\."
    protegido = re.sub(padrao_abrev, _proteger, texto, flags=re.IGNORECASE)

    partes = re.split(r"(?<=[.!?])\s+", protegido)
    return [p.replace("\x00", ".").strip() for p in partes if p.strip()]


def _concatenar_com_pausas(caminhos: list[Path], destino: Path,
                            pausa_s: float = _PAUSA_ENTRE_FRASES_S,
                            pausas: list[float] | None = None) -> Path:
    """Junta os áudios de cada frase em sequência, com uma pausa curta e
    fixa entre elas (o silêncio natural de troca de frase de um narrador,
    não o silêncio de início/fim que o TTS já bota em cada pedaço isolado)."""
    if len(caminhos) == 1:
        shutil.copy(caminhos[0], destino)
        return destino

    cmd = ["ffmpeg", "-y"]
    for c in caminhos:
        cmd += ["-i", str(c)]

    n = len(caminhos)
    filtros, rotulos = [], []
    for i in range(n):
        if i < n - 1:
            # ⚠️ A PAUSA DO ORIGINAL, quando ha' medida. `pausas[i+1]` e' o
            # silencio que existia ANTES da proxima fala — e' o que quebra o
            # ritmo constante de emendar frase atras de frase.
            #
            # ⚠️ COM TETO. Uma pausa de 4s no meio do clipe mata a retencao,
            # e o TikTok nao perdoa buraco. O piso mantem a respiracao minima
            # que ja' existia; sem medida, cai no valor fixo de antes.
            p_i = pausa_s
            if pausas and i + 1 < len(pausas):
                p_i = min(_PAUSA_MAX_S, max(_PAUSA_MIN_S, pausas[i + 1]))
            filtros.append(f"[{i}:a]apad=pad_dur={p_i:.3f}[a{i}]")
            rotulos.append(f"[a{i}]")
        else:
            rotulos.append(f"[{i}:a]")
    filtro = ";".join(filtros) + ";" + "".join(rotulos) + f"concat=n={n}:v=0:a=1[out]"

    cmd += ["-filter_complex", filtro, "-map", "[out]", "-ar", "44100", str(destino)]
    midia.roda(cmd)
    return destino


def _ancorar(duracoes: list[float], janelas: list[tuple[float, float]],
             pausa_min: float = _PAUSA_MIN_S) -> list[float]:
    """Inicio de cada frase: quando a fala ORIGINAL dela comeca, ou logo
    depois da anterior se esta ainda estiver falando.

    ⭐ 26/09/2026 (item 2 da dublagem). MEDIDO nas 12 ultimas runs: de 71
    clipes dublados, 70 terminavam a narracao CEDO — 2,5 a 35,7 s de silencio
    no fim (tipico ~19 s). As frases eram emendadas desde 0 s com pausa de no
    maximo 0,6 s, entao a fala corria na frente da imagem e acabava antes do
    video. Ancorada, a voz acompanha o original ate' o fim.
    """
    inicios, fim_ant = [], 0.0
    for i, dur in enumerate(duracoes):
        alvo = janelas[i][0] if i < len(janelas) else fim_ant
        ini = max(alvo, fim_ant + (pausa_min if i else 0.0))
        inicios.append(ini)
        fim_ant = ini + dur
    return inicios


def _montar_ancorado(caminhos: list[Path], inicios: list[float],
                     destino: Path) -> Path:
    """Cada frase no seu instante (adelay), somadas sem normalizar."""
    cmd = ["ffmpeg", "-y"]
    for c in caminhos:
        cmd += ["-i", str(c)]
    filtros = [f"[{i}:a]aresample=44100,adelay={int(t * 1000)}:all=1[a{i}]"
               for i, t in enumerate(inicios)]
    filtro = (";".join(filtros) + ";" + "".join(f"[a{i}]" for i in range(len(caminhos)))
              + f"amix=inputs={len(caminhos)}:normalize=0:duration=longest[out]")
    cmd += ["-filter_complex", filtro, "-map", "[out]", "-ar", "44100", str(destino)]
    midia.roda(cmd)
    return destino


def _amostra_do_genero(genero: str | None, padrao: Path) -> Path:
    """Qual arquivo de voz clonar para um falante deste genero.

    ⚠️ Falha ABERTA: genero desconhecido, vazio, "varios" ou "indefinido" cai
    na amostra padrao do disparo. Um clipe com voz unica e' aceitavel; um
    clipe SEM voz porque o genero veio estranho, nao.

    ⚠️ E se a amostra do genero nao existir no disco, tambem cai no padrao. As
    amostras sao baixadas por um passo do workflow, e um canal pode disparar
    com uma so'.
    """
    import os
    g = (genero or "").strip().lower()
    nome = os.environ.get(f"AMOSTRA_VOZ_{g.upper()}") if g else None
    if not nome:
        return padrao
    caminho = padrao.parent / nome
    return caminho if caminho.exists() else padrao


def _blocos_por_falante(segmentos: list[dict], falantes: list[dict] | None
                        ) -> list[tuple[str | None, list[dict]]]:
    """Agrupa os segmentos em blocos contiguos do MESMO falante.

    Devolve [(genero, [segmentos])], na ordem do tempo.

    ⚠️ Agrupa em BLOCO, nao por frase. A sintese frase a frase existe porque o
    Chatterbox soa mal em textos longos (ver `_dividir_frases`), mas a VOZ tem
    de mudar so' quando a pessoa muda. Trocar de voz a cada frase seria o
    "dinamismo" que o VOZ_MULTIPLA.md chama de ruido.

    Sem `falantes`, devolve um bloco so' com genero None — que e' o
    comportamento de sempre.
    """
    if not falantes:
        return [(None, segmentos)]

    def quem(seg) -> tuple[str | None, str | None]:
        # o falante cujo intervalo mais cobre este segmento
        meio = (float(seg.get("inicio", 0)) + float(seg.get("fim", 0))) / 2
        for f in falantes:
            try:
                if float(f["inicio_s"]) <= meio <= float(f["fim_s"]):
                    return f.get("quem"), f.get("genero")
            except (KeyError, TypeError, ValueError):
                continue
        return None, None

    blocos: list[tuple[str | None, list[dict]]] = []
    atual_quem = object()
    for seg in segmentos:
        q, g = quem(seg)
        if q != atual_quem:
            blocos.append((g, [seg]))
            atual_quem = q
        else:
            blocos[-1][1].append(seg)
    return blocos


def gerar_trilha(segmentos: list[dict], duracao_total: float, trabalho: Path,
                  amostra_voz: Path, idioma: str = IDIOMA_PADRAO,
                  falantes: list[dict] | None = None,
                  fonte: Path | None = None
                  ) -> tuple[Path | None, list[dict]]:
    """Mesma interface de dublagem.gerar_trilha, mas com a voz clonada.

    Sintetiza FRASE POR FRASE (não um trechinho por janela de ~4s, que
    cortava no meio da frase e dessincronizava as pausas da legenda; nem o
    trecho inteiro numa síntese só, que saiu arrastado e com dicção ruim —
    o Chatterbox não é feito pra 90s contínuos, ver `_dividir_frases`),
    concatena com uma pausa curta fixa entre frases, e só então ajusta a
    duração total do resultado pro tamanho do clipe (um único atempo suave
    no final, não por pedaço).

    Devolve (caminho_do_audio, timing) — timing é [{frase, inicio, fim}]
    no timeline REAL do áudio final (já contando a pausa entre frases e o
    atempo aplicado no fim). O timing do texto original (baseado no vídeo
    fonte) não bate mais com esse áudio — a legenda tem que usar ESSE
    timing, não o dos `segmentos` de entrada (Bryan reportou legenda
    "correndo" em 05/08/2026 quando ela ainda seguia o timing antigo)."""
    # zera ANTES de tudo: saida cedo nao pode deixar a nota do clipe anterior
    global ULTIMO_QC
    ULTIMO_QC = {}
    if not segmentos:
        return None, []
    if not amostra_voz.exists():
        raise RuntimeError(f"amostra de voz não encontrada: {amostra_voz}")

    # Um bloco por falante, em ordem. Sem `falantes`, um bloco so' — e o
    # comportamento fica identico ao de antes.
    blocos = _blocos_por_falante(segmentos, falantes)
    pares: list[tuple[str, Path]] = []      # (frase, amostra daquele falante)
    for genero, segs in blocos:
        texto = " ".join(s2["texto"].strip() for s2 in segs
                         if s2.get("texto", "").strip())
        if not texto:
            continue
        amostra = _amostra_do_genero(genero, amostra_voz)
        for fr in _dividir_frases(texto):
            pares.append((fr, amostra))
    frases = [f for f, _ in pares]
    if not frases:
        return None, []
    if len({str(a) for _, a in pares}) > 1:
        print(f"      [voz] {len(blocos)} bloco(s) de falante, "
              f"{len({str(a) for _, a in pares})} voz(es) diferentes",
              flush=True)

    # ---- DINAMICA DO ORIGINAL (pedido do Bryan em 01/09/2026) ----------
    #
    # Tres aproximacoes, aplicadas em TODO video daqui pra frente: enfase por
    # frase, envelope de volume e as pausas do original. Ver engine/dinamica.py
    # — ⚠️ nao e' transferencia de entonacao, e o modulo explica por que nao da'.
    #
    # ⚠️ FALHA ABERTA. Sem a fonte, ou se a medicao nao der certo, tudo fica
    # como era: enfase None (padrao do modelo), ganho 1.0, pausa fixa. Uma
    # dublagem sem dinamica e' pior; uma dublagem que NAO SAI por causa de uma
    # medicao e' muito pior.
    enfases: list[float | None] = [None] * len(frases)
    ganhos: list[float] = [1.0] * len(frases)
    pausas: list[float] = []
    # onde cada frase cai no original — serve a' dinamica E a' ancoragem
    janelas = _janelas_das_frases(segmentos, frases)
    if fonte is not None and Path(fonte).exists() and janelas:
        try:
            medidas = dinamica.medir_blocos(Path(fonte), janelas)
            enfases = dinamica.enfase_por_bloco(medidas)
            ganhos = dinamica.ganho_por_bloco(medidas)
            pausas = dinamica.pausas_originais(janelas)
            print(f"      [voz] dinamica do original: enfase "
                  f"{min(enfases):.2f}-{max(enfases):.2f}, ganho "
                  f"{min(ganhos):.2f}-{max(ganhos):.2f}x", flush=True)
        except Exception as e:
            print(f"      [!] dinamica indisponivel ({str(e)[:60]}) — "
                  "sintetizando sem ela", flush=True)
            enfases = [None] * len(frases)
            ganhos = [1.0] * len(frases)
            pausas = []

    trabalho.mkdir(parents=True, exist_ok=True)
    partes, duracoes = [], []
    # ⚠️ BATIMENTO POR FRASE — nao e' log decorativo, e' o instrumento.
    #
    # Os runs #188 e #189 queimaram 12h de runner e o log nao disse onde
    # pararam: a unica saida era a barra de progresso interna do Chatterbox.
    # Com hora absoluta em cada linha, o proximo travamento diz a frase, o
    # sub-passo e o minuto — e o `flush=True` garante que a linha chegue ao
    # log do Actions ANTES do congelamento, nao presa num buffer.
    t_lote = time.monotonic()
    notas: list[float | None] = []
    refeitas = 0
    print(f"      [voz] {len(frases)} frase(s) para sintetizar", flush=True)
    for i, frase in enumerate(frases):
        p = trabalho / f"voz_frase_{i:03d}.wav"
        agora = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"      [voz] frase {i + 1}/{len(frases)} as {agora} "
              f"(acumulado {time.monotonic() - t_lote:.0f}s)", flush=True)
        _falar(frase, p, pares[i][1], idioma,
               enfase=enfases[i] if i < len(enfases) else None)
        # ⭐ 26/09 (item 3): a voz falou o que devia? Refaz UMA vez a frase
        # abaixo do limiar e fica com a melhor. Ver engine/conferencia.py.
        nota_i = None
        if conferencia.LIGADO:
            r = conferencia.nota(p, frase, idioma)
            if r:
                nota_i = r[0]
                if (nota_i < conferencia.LIMIAR
                        and refeitas < conferencia.MAX_REFEITAS_POR_CLIPE):
                    print(f"        [qc] nota {nota_i:.2f} — ouviu {r[1][:70]!r}; "
                          "refazendo a frase", flush=True)
                    p2 = trabalho / f"voz_frase_{i:03d}_b.wav"
                    # na D: mesma voz, leitura 10% mais lenta (ver
                    # REFEITA_VELOCIDADE); fora da D, a A de sempre
                    _falar(frase, p2, pares[i][1], idioma,
                           enfase=enfases[i] if i < len(enfases) else None,
                           motor="D-" if VOZ_MOTOR == "D" else "A")
                    refeitas += 1
                    r2 = conferencia.nota(p2, frase, idioma)
                    if r2 and r2[0] > nota_i:
                        p, nota_i = p2, r2[0]
                    print(f"        [qc] ficou nota {nota_i:.2f}", flush=True)
        notas.append(nota_i)
        if i < len(ganhos) and abs(ganhos[i] - 1.0) > 0.01:
            p = _aplicar_ganho(p, ganhos[i])
        partes.append(p)
        # ⚠️ Isto e' um ffprobe. Se o travamento for aqui, o TIMEOUT_SONDA do
        # midia.py (120s) derruba com erro em 2 min em vez de 6h em silencio.
        print("        [tts] medindo duracao (ffprobe)...", flush=True)
        duracoes.append(midia.duracao(p))
    print(f"      [voz] as {len(frases)} frases prontas em "
          f"{time.monotonic() - t_lote:.0f}s", flush=True)
    ULTIMO_QC = conferencia.resumo(notas, refeitas)
    if ULTIMO_QC.get("conferidas"):
        print(f"      [qc] dublagem: media {ULTIMO_QC['media']:.2f}, pior "
              f"{ULTIMO_QC['min']:.2f}, {refeitas} frase(s) refeita(s)", flush=True)

    if ANCORAR_FRASES and len(janelas) == len(frases):
        inicios = _ancorar(duracoes, janelas)
        concatenado = _montar_ancorado(partes, inicios, trabalho / "voz_ancorada.wav")
        print(f"      [voz] frases ancoradas no tempo do original "
              f"(1a em {inicios[0]:.1f}s, ultima termina em "
              f"{inicios[-1] + duracoes[-1]:.1f}s)", flush=True)
    else:
        concatenado = trabalho / "voz_concatenada.wav"
        _concatenar_com_pausas(partes, concatenado, pausas=pausas)
        # ⚠️ o timing tem de somar AS MESMAS pausas do audio. Antes somava
        # sempre 0,15 s enquanto o audio usava as pausas do original (ate'
        # 0,6 s): a legenda escorregava pra frente da voz frase a frase.
        inicios, t = [], 0.0
        for i, dur in enumerate(duracoes):
            inicios.append(t)
            p_i = _PAUSA_ENTRE_FRASES_S
            if pausas and i + 1 < len(pausas):
                p_i = min(_PAUSA_MAX_S, max(_PAUSA_MIN_S, pausas[i + 1]))
            t += dur + p_i
    dur_concatenada = midia.duracao(concatenado)

    destino = trabalho / "trilha_dublada_clonada.wav"
    _ajustar_duracao(concatenado, duracao_total, destino)
    # narração mais curta que o clipe = preenchida com silêncio no final,
    # SEM mexer no ritmo (ver _ajustar_duracao) — o timing de cada frase
    # não muda. Só quando acelera (narração mais longa) é que o timing
    # precisa ser comprimido na mesma proporção.
    if dur_concatenada <= duracao_total:
        escala = 1.0
    else:
        dur_final = midia.duracao(destino)
        escala = (dur_final / dur_concatenada) if dur_concatenada > 0 else 1.0

    # diagnóstico: narração mais curta = sobra silêncio no fim (ritmo
    # natural, não desacelera mais); mais longa = acelera até 1.6x (acima
    # disso ainda fica corrido). Medir aqui em vez de adivinhar pela
    # duração do run (foi assim que achamos o problema de lentidão em
    # 05/08/2026, run 31037313597, sem esse print).
    if dur_concatenada <= duracao_total:
        print(f"      {len(frases)} frase(s), narração {dur_concatenada:.1f}s "
              f"pro clipe de {duracao_total:.1f}s "
              f"({duracao_total - dur_concatenada:.1f}s de silêncio no final, ritmo natural)")
    else:
        fator_atempo = min(1.6, dur_concatenada / max(0.1, duracao_total))
        print(f"      {len(frases)} frase(s), narração {dur_concatenada:.1f}s "
              f"pro clipe de {duracao_total:.1f}s (acelerando {fator_atempo:.2f}x"
              f"{' — NO TETO, ainda vai soar corrido' if fator_atempo >= 1.6 else ''})")

    timing = [{"frase": frase, "inicio": ini * escala, "fim": (ini + dur) * escala}
              for frase, ini, dur in zip(frases, inicios, duracoes)]

    return destino, timing
