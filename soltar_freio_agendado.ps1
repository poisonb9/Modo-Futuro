# Solta o freio dos cortes na hora combinada, e empurra pro repositorio.
#
# Ordem do Bryan em 09/09/2026: "vamos parar o uso ate' amanha, preciso desse
# combustivel para outro projeto; amanha por volta do meio dia voce pode
# reabilitar os cortes em cadeia, 1 de cada vez" — e, quando eu disse que nao
# rodo entre os turnos dele: "registra a tarefa agendada para rodar
# automaticamente amanha meio dia".
#
# ⚠️ POR QUE UMA TAREFA, E NAO EU. Eu nao rodo entre os turnos. Um freio que
# depende de alguem lembrar de soltar fica puxado por dias, e a fabrica para
# sem ninguem notar — que e' o oposto do que a pausa quer.
#
# ⚠️ O FREIO SO' VALE NA NUVEM DEPOIS DO PUSH. O `cortar_fila` faz checkout do
# repositorio antes de rodar; soltar o arquivo aqui e nao empurrar deixaria a
# nuvem parada do mesmo jeito. Por isso este script COMMITA e EMPURRA, e trata
# o `rejected` — a nuvem grava estado sozinha varias vezes por dia.
#
# ⚠️ NADA DE CARACTERE FORA DO ASCII DENTRO DE STRING. O arquivo nao tem BOM e
# o PowerShell 5.1 o le' como cp1252; um travessao dentro de aspas quebra o
# parse do arquivo INTEIRO. Em comentario e' inofensivo. (Medido em 08/09.)

param([switch]$Simular)

$ErrorActionPreference = 'Stop'

$raiz   = 'C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine'
$python = 'C:\Program Files\Python314\python.exe'
$log    = Join-Path $raiz 'estado\soltar_freio.log'

Set-Location $raiz
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
$carimbo = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

function Anotar($txt) { Add-Content -Path $log -Value "[$carimbo] $txt" -Encoding utf8 }

if (-not (Test-Path (Join-Path $raiz 'PAUSA_CORTES'))) {
    Anotar 'freio ja estava solto - nada a fazer'
    exit 0
}

if ($Simular) {
    Anotar 'SIMULACAO: soltaria o freio, commitaria e empurraria'
    Write-Output 'SIMULACAO ok: o freio existe e seria solto'
    exit 0
}

# ⚠️ 'Continue' SO' na chamada nativa: com 'Stop', uma linha em stderr vira
# erro terminante no PowerShell 5.1 e o script morre ANTES de logar. Foi o que
# apagou o log do ciclo semanal em 09/09/2026.
$ErrorActionPreference = 'Continue'
$saida = & $python -X utf8 -c "import sys; sys.path.insert(0, '.'); from engine import freio; print('solto' if freio.soltar() else 'ja estava solto')" 2>&1 | Out-String
$rc = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
Anotar "soltar: (exit $rc) $($saida.Trim())"

if ($rc -ne 0) { Anotar 'ABORTADO: o soltar falhou, nao commito'; exit $rc }

$ErrorActionPreference = 'Continue'
& git add -A PAUSA_CORTES 2>&1 | Out-Null
& git commit -q -m 'freio solto: volta dos cortes em cadeia, 1 de cada vez (tarefa agendada de 09/09)' 2>&1 | Out-Null

$token = (Get-Content (Join-Path $raiz 'github_token.txt') -Raw).Trim()
$auth  = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("x-access-token:$token"))
$push  = & git -c "http.extraheader=Authorization: Basic $auth" push origin main 2>&1 | Out-String

if ($push -match 'rejected|non-fast-forward') {
    # A nuvem commitou por cima (desempenho.yml grava estado varias vezes ao
    # dia). Os commits dela tocam so' arquivos de estado, entao rebase resolve.
    Anotar 'push recusado; rebase e nova tentativa'
    & git stash push -m 'auto antes do rebase' 2>&1 | Out-Null
    & git pull --rebase origin main 2>&1 | Out-Null
    & git stash pop 2>&1 | Out-Null
    $push = & git -c "http.extraheader=Authorization: Basic $auth" push origin main 2>&1 | Out-String
}
$ErrorActionPreference = 'Stop'
Anotar "push: $($push.Trim())"

$ok = -not ($push -match 'rejected|error:|fatal:')
if ($ok) { Anotar 'FREIO SOLTO e no ar. Cortes voltam em cadeia, 1 de cada vez.' }
else     { Anotar 'ATENCAO: o freio saiu do disco mas o push NAO passou - a nuvem continua parada.' }

$env:PYTHONIOENCODING = 'utf-8'
try {
    if ($ok) {
        $txt = "Freio dos cortes SOLTO ($carimbo). A fila volta a andar, 1 de cada vez (teto_em_voo=1 ate' 12/09)."
    } else {
        $txt = "ATENCAO ($carimbo): soltei o freio no disco mas o PUSH NAO PASSOU. A nuvem continua sem cortar. Saida: " + $push.Trim()
    }
    $msg = Join-Path $env:TEMP 'soltar_freio_aviso.txt'
    Set-Content -Path $msg -Value $txt -Encoding utf8
    $codigo = 'import io,sys; sys.path.insert(0, sys.argv[1]); from engine import telegram; ' +
              'telegram.enviar(io.open(sys.argv[2], encoding="utf-8").read()) if telegram.configurado() else None'
    & $python -X utf8 -c $codigo $raiz $msg | Out-Null
    Remove-Item $msg -ErrorAction SilentlyContinue
} catch {
    Anotar "[!] aviso nao saiu no Telegram: $_"
}

if ($ok) { exit 0 } else { exit 1 }
