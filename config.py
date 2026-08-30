"""Configuração central do motor. Ajuste aqui, não espalhe constantes pelo código."""
from pathlib import Path

RAIZ = Path(__file__).parent
TRABALHO = RAIZ / "trabalho"      # intermediários (áudio, json) - descartável
SAIDA = RAIZ / "saida"            # o que você posta

# ---------------------------------------------------------------- Gemini
# Flash aguenta 9,5h de áudio por prompt e é barato. Pro só se a escolha
# ficar fraca em vídeo muito técnico.
GEMINI_MODELO = "gemini-3.6-flash"

# Cascata de reserva — VAZIA DE PROPÓSITO (testado em 27/07/2026).
#
# A ideia era: como a cota gratuita é de 20 req/dia POR MODELO, cair pro
# próximo modelo quando o principal esgota devolveria capacidade na hora.
# A máquina funciona (`engine/selecao.py:_pedir`), mas os candidatos
# REPROVARAM no teste de qualidade (`teste/comparar_modelos.py`, mesmo
# vídeo da Bermuda, mesma referência de 6 clipes do 3.6-flash):
#
#   gemini-3-flash-preview  ->  1 clipe de 6, e ERRADO: escolheu 18-138s
#                               (a introdução) e deu a ele um título sobre
#                               o resseguro de US$1,5 tri, que está em
#                               1300-1356s. Título não bate com o conteúdo.
#   gemini-3.5-flash        ->  0 clipes.
#
# O modo de falha é traiçoeiro: o post.json sai completo e bonito (título
# forte, nota 92, taxonomia cheia), então passaria despercebido — a gente
# só descobriria vendo o vídeo. Produzir 1 clipe mislabeled é PIOR que não
# produzir: melhor o motor falhar alto e esperar a cota virar (~4-5h da
# manhã, meia-noite no Pacífico).
#
# Pra reabilitar: rode o comparar_modelos.py com os 3 modelos na mesma
# rodada (precisa de cota do 3.6-flash) e só religue o que reencontrar a
# maioria dos clipes da referência.
GEMINI_MODELOS_RESERVA = []

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"

# ---------------------------------------------------------------- Groq
# turbo = 12% WER, $0.04/h | large-v3 = 10.3% WER, $0.111/h
# Como só transcrevemos clipes de ~1 min, o custo é irrelevante:
# vale usar o mais preciso, porque erro em legenda queimada é permanente.
GROQ_MODELO = "whisper-large-v3"
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_LIMITE_MB = 25              # free tier

# ---------------------------------------------------------------- clipes
QTD_CLIPES = 10

# DUR_MIN = 65: REGRA DE DINHEIRO, não de estética (27/07/2026).
# O TikTok só conta "visualização qualificada" — a única que paga — em
# vídeo com MAIS DE 60 segundos. É o achado mais corroborado da destilação
# (8 vídeos independentes, ver sabedoria/PLAYBOOK_TIKTOK.md §1). Clipe
# abaixo disso rende ZERO por mais que viralize: o corpus cita um vídeo de
# 9s com 20 milhões de views e receita nenhuma.
# Prova em casa: o lote da Bermuda (saida/2026-07-26_2346) saiu com 6
# clipes de notas 83-95 e TODOS entre 42 e 56s — nenhum podia monetizar.
# Os 65 (e não 61) são margem: `MARGEM` e o corte em pausa natural mexem
# no tempo final, e ficar em 60,4s seria perder tudo por 0,4s.
DUR_MIN = 65                     # segundos

# DUR_MAX = 110: acima disso fica difícil sustentar os ~50% de retenção
# que a visualização qualificada também exige. Era 120.
DUR_MAX = 110

# ------------------------------------------------- corte de silêncios
# "Decupagem": remover as pausas mortas é o ajuste de RETENÇÃO de maior
# impacto da destilação (PLAYBOOK_TIKTOK.md §4.4) e ainda conta como
# camada de edição real pro bônus de originalidade.
# ATENÇÃO: encurta o clipe. Como DUR_MIN=65 é o que garante monetização,
# o main.py só aplica se o resultado continuar acima de DUR_MIN.
CORTAR_SILENCIOS = True
SILENCIO_LIMIAR_DB = -32     # abaixo disso é considerado silêncio
SILENCIO_DUR_MIN_S = 0.35    # pausa menor que isso é respiração natural, fica
SILENCIO_FOLGA_S = 0.10      # deixa nas pontas pra fala não soar cortada
MARGEM = 0.4                     # respiro antes/depois do corte (s)
CONGELAMENTO_MAX_S = 4.5         # bloco contínuo travado acima disso descarta o candidato

# ------------------------------------------------- pós-produção (03/08/2026)
# Estabilização (vidstab) e grade de cor cinematográfica — só ffmpeg nativo,
# sem GPU, sem asset externo. Ver engine/pos_producao.py.
ESTABILIZAR = True
GRADE_CINEMATICO = True

# ------------------------------------------------- voz clonada (04/08/2026)
# Chatterbox Multilingual, self-hosted, MIT, grátis — clona a voz do Bryan
# a partir de uma amostra. Só entra em ação com --dublar. Ver engine/voz_clonada.py.
VOZ_CLONADA_ATIVA = True
VOZ_CLONADA_AMOSTRA = RAIZ / "vozes" / "bryan_amostra.wav"

# Piso de gancho (0-10). O Gemini já devolve `forca_gancho` por clipe, mas
# até 29/07/2026 esse número era gravado no post.json e nunca usado.
#
# Por que filtrar: o ECR — proporção que assiste além de ~5s — é o que prevê
# sustentação de atenção, e watch time é o sinal dominante da decisão de
# promover (sabedoria/PLAYBOOK_TIKTOK.md §22, N=50 papers). Clipe que abre
# fraco perde na janela que mais pesa.
#
# ⚠️ 6.0 é GUARDA-CORPO, não número calibrado. Ninguém mediu ainda se
# forca_gancho prevê desempenho real — isso só se sabe com o loop do
# desempenho.py rodando. Escolhido conservador de propósito: derruba o que é
# claramente fraco sem esvaziar o lote. Ajustar quando houver dado.
GANCHO_MIN = 6.0

# ---------------------------------------------------------------- voice-over
# VOICE-OVER: o audio ORIGINAL continua audivel por baixo, abaixado, e a voz
# dublada entra por cima. E' como documentario e' dublado ha' decadas.
#
# POR QUE EXISTE (decidido em 30/08/2026, pro canal Sem Anestesia)
#
# O modo padrao TROCA a trilha: o original some. Pra narracao de contexto isso
# e' certo — quem fala e' o canal. Mas em corte de podcast a voz E' parte do
# argumento: a intensidade do Goggins nao esta' no que ele diz, esta' em COMO
# ele diz. Trocar por outra voz apaga metade do conteudo.
#
# E ha' um risco pior que perder intensidade: CONFUSAO DE AUTORIA. Se a voz do
# Bryan fala as palavras do Huberman em primeira pessoa, o espectador entende
# que o Bryan esta' afirmando aquilo. Em saude mental e neurociencia, e'
# exatamente onde nao se quer ambiguidade.
#
# A alternativa obvia — legenda — tem custo MEDIDO: a retencao do @modofuturo
# ficou em 14% e a audiencia saiu em 0:01, e o diagnostico foi "o corte abre
# com cartao de texto sobre imagem parada; ler leva tempo". Legendar 60s de
# ingles e' pedir leitura o tempo todo.
#
# Voice-over resolve os dois: ouve-se a voz real (autoridade preservada,
# autoria obvia) e nao se le' (retencao preservada).
VOICE_OVER = False               # ligado por canal; padrao continua trocando a trilha

# Volume do audio ORIGINAL sob a narracao. 0.18 e' ~-15 dB: audivel o
# suficiente pra reconhecer a voz e a emocao, baixo o suficiente pra nao
# disputar com a dublagem. Abaixo de 0.10 o original vira ruido e o efeito de
# autoridade se perde — que e' o unico motivo do modo existir.
VOICE_OVER_VOL_ORIGINAL = 0.18

# ---------------------------------------------------------------- descoberta (YouTube Data API v3)
# Objetivo: achar vídeos com potencial de hype/monetização, sem nicho fixo.
YOUTUBE_URL = "https://www.googleapis.com/youtube/v3"

# Canais fixos que você quer sempre monitorar (handle com @ ou ID UC...).
CANAIS_MONITORADOS: list[str] = [
    # "@algumcanal",
]

# Termos pra busca aberta (descoberta de hype fora dos canais fixos).
#
# ESCOLHIDOS PELO QUE MEDIDAMENTE FUNCIONOU (30/08/2026). Os tres melhores
# clipes da historia do canal vieram todos da mesma familia — fabrica, maquina
# e contaminacao, contadas pelo lado FISICO e EXTREMO:
#
#     1826  As regras extremas para entrar na fabrica mais limpa
#     1008  Como 1 poeira pode destruir 1 milhao de dolares
#      726  A maquina de 400 milhoes de dolares que cria os chips
#
# E o que rendeu pouco foi analise e geopolitica, sempre:
#
#      300  Analise do TSMC (Lex Fridman)      — mediana da fonte
#        0  Semiconductor is the next OIL      — mediana da fonte
#
# Entao os termos miram processo, maquina e numero absurdo. Nada de "chip war",
# "tensions" ou "market" — e' exatamente o que nao performou.
TERMOS_HYPE: list[str] = [
    "how computer chips are made",
    "inside semiconductor fab",
    "semiconductor cleanroom",
    "EUV lithography machine",
    "ASML machine",
    "silicon wafer manufacturing",
    "chip factory tour",
    "nanometer chip technology",
]

# 7 -> 30 dias. A janela curta existe pra pegar HYPE, e faz sentido em
# noticia. Mas os campeoes deste canal sao documentario tecnico, que nao
# envelhece: o video da ASML que gerou o 1826 nao tinha nada de recente.
# Com 7 dias a busca voltava quase vazia pra estes termos.
JANELA_DIAS = 30                 # só considera vídeos publicados nos últimos N dias
DESCOBERTA_DUR_MIN_S = 180       # ignora vídeo curto demais pra valer cortar (3 min)

# peso de cada critério na nota final (soma não precisa ser 1, é só proporção)
PESO_VIEWS = 0.35
PESO_VELOCIDADE = 0.40           # views/hora desde a publicação — o motor de hype
PESO_ENGAJAMENTO = 0.25          # (likes + comentários) / views

FILA_QTD = 20                    # quantos vídeos a fila devolve por rodada

# ---------------------------------------------------------------- descoberta: podcasts
# Seção separada: episódios de podcast recentes, de canais que você AINDA não
# cortou, numa faixa de views que costuma indicar "bombando mas ainda dá tempo".
# Termos do 3o canal (Sem Anestesia, criado em 30/08/2026): cortes de fala
# forte sobre comportamento, mente e vida.
#
# ⚠️ SO' FONTE ESTRANGEIRA — EUA e Europa. Ordem do Bryan em 30/08/2026.
# O valor do canal e' trazer o que ninguem traduziu, a mesma tese do Cozinha
# Importada (onde Ana Maria Braga saiu da lista por ja' estar em portugues,
# sem nada a traduzir). Podcast brasileiro nao tem o que dublar, e cortar o
# que o proprio dono ja' corta em portugues e' competir sem vantagem.
#
# A primeira rodada, em portugues, foi descartada inteira por isso.
PODCAST_TERMOS_HYPE: list[str] = [
    "hard truths about life podcast",
    "psychologist explains podcast interview",
    "life advice podcast episode",
    "mental health podcast full episode",
    "neuroscientist podcast interview",
    "discipline and mindset podcast",
]

# Buscar DENTRO destes e' mais confiavel que busca aberta: garante o idioma e
# garante que e' episodio, nao recorte de terceiro.
#
# ⚠️ The Diary Of A CEO domina o nicho e por isso mesmo e' o canal MAIS
# cortado do mundo — dezenas de canais brasileiros vivem de cortar esses
# episodios. Huberman e Rich Roll sao menos saturados em portugues.
PODCAST_CANAIS: list[str] = [
    "@TheDiaryOfACEO",       # Steven Bartlett (Reino Unido)
    "@hubermanlab",          # Andrew Huberman (EUA) — neurociencia aplicada
    "@ChrisWillx",           # Modern Wisdom (Reino Unido)
    "@MelRobbins",           # EUA
    "@richroll",             # EUA
    "@TheSchoolOfLifeTV",    # Reino Unido
    "@lexfridman",           # EUA
]

# Canal de CORTES esta' fora, sempre. A primeira rodada trouxe "Cortes de
# Mentalidade" e "Motivadores do Impacto" bem colocados — os dois cortam
# episodio dos outros. Cortar corte alheio e' caminho curto pro strike e pro
# conteudo repetido; o valor do canal e' ser a primeira mao.
PODCAST_EXCLUIR_CANAL = ("cortes", "clips", "shorts", "highlights",
                         "melhores momentos", "best of", "compilation")

# ⚠️ Episodio de podcast passa de 90 min e o main.py cai pra modo SO'-AUDIO
# (o Gemini recusa video com muitos frames). Funciona e sai mais barato, mas
# ele escolhe os momentos sem ver a imagem. Pra podcast isso pesa pouco — o
# valor esta' na fala — mas o comportamento muda e e' bom saber.
JANELA_HORAS_PODCAST = 48        # só vídeos publicados nas últimas N horas
VIEWS_MIN_PODCAST = 100_000
VIEWS_MAX_PODCAST = 500_000

# canais já cortados ficam registrados aqui e saem da fila de podcasts
REGISTRO_CANAIS_CORTADOS = RAIZ / "estado" / "canais_cortados.json"

# ---------------------------------------------------------------- fila do TikTok
# Clipes já mandados pro rascunho do TikTok, pra não repetir.
REGISTRO_ENVIADOS_TIKTOK = RAIZ / "estado" / "enviados_tiktok.json"

# O TikTok recusa novo rascunho com `spam_risk_too_many_pending_share`
# depois de ~5 pendentes no inbox. Então o fluxo é: manda um punhado,
# usuário posta, manda mais.
TIKTOK_LOTE = 5

# Lotes de saída que NÃO devem ser postados. Renderizados antes da correção
# do WrapStyle na legenda (texto estoura a borda do vídeo) — o defeito está
# queimado no arquivo, só re-render resolve.
LOTES_IGNORADOS: list[str] = [
    "2026-07-26_0152",
    "2026-07-26_0634",
]

# ---------------------------------------------------------------- render
# GTX 1650 tem NVENC -> encoding por hardware. Se rodar em máquina sem
# NVIDIA, o motor detecta e cai pra libx264 sozinho.
NVENC = "h264_nvenc"
CPU_ENC = "libx264"
VERTICAL = (1080, 1920)          # 9:16 Shorts
HORIZONTAL = (1920, 1080)        # 16:9 tela cheia

# Face tracking: o quadro persegue o rosto no crop vertical.
# Suavização alta = movimento menos "nervoso".
SUAVIZACAO = 0.88
AMOSTRA_FPS = 4                  # quantos frames/s analisar p/ achar rosto

# Trocar palavra sensivel por grafia adaptada na legenda (morte -> m0rte).
# DESLIGADO em 25/08/2026, no mesmo dia em que foi escrito, depois que o Bryan
# perguntou "tem certeza que isso vai confundir o algoritmo?" — e nao vai:
#   - o §22 do PLAYBOOK (`[PAPER]`) diz que a entrega inicial e' alocada por
#     EMBEDDING do conteudo; "m0rte" e "morte" caem no mesmo ponto do espaco
#     vetorial. Troca de letra engana casador de string, nao modelo;
#   - o AUDIO continua dizendo a palavra, e o TikTok transcreve audio — a
#     protecao era contornada pelo proprio video;
#   - "m0rte" na tela piora a leitura, e leitura e' retencao, que e' o unico
#     gargalo que a gente MEDIU.
# Dano certo contra ganho hipotetico. O modulo fica pronto caso apareca
# evidencia de verdade. Ver engine/suavizar.py.
SUAVIZAR_TEXTO = False

# ------------------------------------------------- legenda premium
# A descricao leva o CONTEXTO que nao coube nos 90s do corte: pano de
# fundo, 3 fatos que ficaram de fora, e por que importa. Ver
# engine/legenda_premium.py. Ideia do Bryan em 28/08/2026, depois de
# ver a receita em texto funcionar no canal de comida.
#
# ATENCAO: os fatos vem do conhecimento do MODELO, nao da fala do video.
# O prompt proibe inventar numero e data, mas vale conferir os primeiros.
LEGENDA_PREMIUM = True
