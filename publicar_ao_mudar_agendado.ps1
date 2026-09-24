# Publica o site QUANDO O RADAR MUDOU ALGO — Agendador de Tarefas, a cada 30 min.
#
# ⭐ POR QUE EXISTE (18/09/2026, ordem do Bryan): "atualizar sempre os dados do
# header... sempre que rodarmos o radar". O radar (precos.yml) roda 24x/dia na
# nuvem; a publicacao era 1x/dia (11:30 UTC). Entre uma e outra o heroi
# (achadinhos, baixaram, vendidos, R$ em quedas) envelhecia ate' 24 h.
#
# ⚠️ SO' PUBLICA SE MUDOU. A cada 30 min compara, no origin/main, o blob dos
# tres arquivos que o radar escreve (instantaneo de precos, catalogo Awin,
# registro de produtos) com o que foi publicado da ultima vez. Igual = nao faz
# nada (zero deploy, zero chamada). Diferente = pull, mede foto nova na nuvem
# (no-op sem pendente), publica e CONFERE no ar — o mesmo caminho da diaria.
#
# ⚠️ A DIARIA CONTINUA (nomes curtos, buscas do site): esta so' republica.
# S4U, sem janela, igual ao vigia. PATH da S4U nao tem git/npx/gh: vai fixo.

$ErrorActionPreference = 'Stop'
$raiz   = 'C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine'
$python = 'C:\Program Files\Python314\python.exe'
$log    = Join-Path $raiz 'estado\publicar_ao_mudar.log'
$marca  = Join-Path $raiz 'estado\publicado_ao_mudar.txt'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 1MB)) { Move-Item $log "$log.old" -Force }
$carimbo = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Set-Location $raiz
$env:PATH = 'C:\Program Files\nodejs;C:\Program Files\Git\cmd;C:\Program Files\Git\mingw64\bin;C:\Program Files\Git\usr\bin;C:\Program Files\GitHub CLI;' + $env:PATH

$ErrorActionPreference = 'Continue'
# 1. o que o radar escreveu, no remoto (sem tocar na arvore local ainda)
& git fetch -q origin main 2>&1 | Out-Null
# ⭐ e tambem o CODIGO da pagina/publicador (18/09): edicao no cartao vai ao
# ar sozinha, sem ninguem publicar a mao.
$agora = (& git rev-parse 'origin/main:estado/precos_agora.json' 2>$null) + ' ' +
         (& git rev-parse 'origin/main:estado/awin_catalogo.json' 2>$null) + ' ' +
         (& git rev-parse 'origin/main:estado/produtos_publicados.jsonl' 2>$null) + ' ' +
         (& git rev-parse 'origin/main:paginas/todos.html' 2>$null) + ' ' +
         (& git rev-parse 'origin/main:paginas/publicar_bio.py' 2>$null) + ' ' +
         (& git rev-parse 'origin/main:estado/fotos_ocr.json' 2>$null)
$antes = if (Test-Path $marca) { Get-Content $marca -Raw } else { '' }
if ($agora.Trim() -eq $antes.Trim()) {
    # nada mudou: uma linha curta no log a cada 30 min seria ruido; so' grava a cada hora cheia
    if ((Get-Date).Minute -lt 30) { Add-Content -Path $log -Value "[$carimbo] sem mudanca no radar" }
    exit 0
}

# 2. traz o estado, publica, confere
$saida = ''
# 22/09/2026: o pop so' roda se o stash GUARDOU algo. Sem nada a guardar,
# `git stash` nao cria entrada e o pop aplicava o stash ANTIGO do topo da
# pilha (um de 21/09) -- conflito com marcadores em DIARIO, radar,
# ml_raizes e fotos_ocr as 15:35, e um diario commitado com marcador.
$pilhaAntes = @(& git stash list 2>$null).Count
$saida += (& git stash -q -u 2>&1 | Out-String)
$guardou = @(& git stash list 2>$null).Count -gt $pilhaAntes
$saida += (& git pull --rebase -q 2>&1 | Out-String)
if ($guardou) { $saida += (& git stash pop -q 2>&1 | Out-String) }
$saida += (& $python -X utf8 -m engine.foto_limpa --medir --timeout 20 2>&1 | Out-String)
$saida += (& $python -X utf8 paginas/publicar_bio.py --subir 2>&1 | Out-String)
$rc = $LASTEXITCODE
$ErrorActionPreference = 'Stop'

# A MARCA TEM DE SER O QUE FOI PUBLICADO, nao o que se viu ao decidir.
# 20/09/2026: entre ler o hash (passo 1) e o `git pull` acima cabe um push.
# Quando isso acontece, publica-se o estado NOVO mas grava-se a marca do
# VELHO — e o ciclo seguinte republica identico, sem necessidade. Nao era
# defeito de correcao (o sistema se conserta sozinho em 10 min); era um
# deploy jogado fora. Relendo aqui, a marca casa com o byte que subiu.
$publicado = (& git rev-parse 'HEAD:estado/precos_agora.json' 2>$null) + ' ' +
             (& git rev-parse 'HEAD:estado/awin_catalogo.json' 2>$null) + ' ' +
             (& git rev-parse 'HEAD:estado/produtos_publicados.jsonl' 2>$null) + ' ' +
             (& git rev-parse 'HEAD:paginas/todos.html' 2>$null) + ' ' +
             (& git rev-parse 'HEAD:paginas/publicar_bio.py' 2>$null) + ' ' +
             (& git rev-parse 'HEAD:estado/fotos_ocr.json' 2>$null)
if ($publicado.Trim()) { $agora = $publicado }

$ok = ($rc -eq 0) -and ($saida -match 'nenhum faltando')
if ($ok) { Set-Content -Path $marca -Value $agora -Encoding utf8 }
# ⭐ BACKUP DO AR A CADA PUBLICACAO CONFERIDA (24/09/2026, Bryan: "quero que
# tenhamos um backup aqui na maquina do site sempre, porque se mudarmos de
# computador temos o backup"). So' depois do OK: backup de publicacao que
# falhou guardaria o site velho achando que e' o novo. Falha do backup NAO
# derruba a publicacao (ela ja' esta' no ar) -- vai pro log como BACKUP FALHOU.
if ($ok) {
    $bk = (& $python -X utf8 ferramentas/backup_do_ar.py 2>&1 | Out-String)
    $bkLinha = if ($LASTEXITCODE -eq 0) { "backup do ar atualizado em site_no_ar/" } else { "BACKUP FALHOU (rc=$LASTEXITCODE): " + (($bk.Trim() -split "`n")[-1]) }
    Add-Content -Path $log -Value "[$carimbo] $bkLinha"
}
# rc=2 e' a TRAVA, nao falha: outra publicacao estava em andamento e esta
# esperou a vez. Chamar isso de "FALHOU" no log faz o dono procurar defeito
# onde houve disciplina. A marca nao e' gravada nos dois casos, entao o
# ciclo seguinte tenta de novo do mesmo jeito.
$linha = if ($ok) { "OK  radar mudou -> publicado e conferido" }
         elseif ($rc -eq 2) { "na fila: outra publicacao rodando, tenta na proxima" }
         else { "FALHOU rc=$rc (publica de novo na proxima)" }
Add-Content -Path $log -Value "[$carimbo] $linha"
Add-Content -Path $log -Value ($saida -split "`n" | Where-Object { $_ -match 'catalogo:|multometro:|fotos:|endereco\(s\)|NAO |Error|Traceback|File "|line ' } | ForEach-Object { "    $_" })
exit $rc
