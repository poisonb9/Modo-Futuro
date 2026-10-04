# Abastecimento de TODOS os canais como TAREFA DO WINDOWS (04/10/2026).
#
# Por que aqui e nao no GitHub: o YouTube bloqueia download de IP de nuvem
# ("Sign in to confirm you're not a bot", medido em 29/09/2026). Esta VPS
# baixa; o resto (corte, fila, Buffer) continua na nuvem.
#
# Por que tarefa e nao loop: ate' 04/10 o abastecer_loop.py rodava num loop
# aberto a mao. A sessao fechou em 30/09 e o @achadinho.make ficou sem video
# novo ate' a fila zerar. A tarefa roda a cada 30 min, sobrevive a reinicio, e
# abre o JDownloader se ele estiver fechado. A vigia de postagem (GitHub, 3x/dia)
# avisa no Telegram se mesmo assim algum canal ficar sem os 4 do dia.
$ErrorActionPreference = 'Continue'
$raiz = $PSScriptRoot
$log  = Join-Path $raiz 'estado\abastecer_agendado.log'
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 2MB)) { Move-Item $log "$log.old" -Force }
function Anota($m) { "$(Get-Date -Format 'dd/MM HH:mm') $m" | Out-File $log -Append -Encoding utf8 }

# uma passada por vez: se a anterior ainda roda (download longo), sai
$trava = Join-Path $raiz 'estado\abastecer.lock'
if (Test-Path $trava) {
    $pidAnt = Get-Content $trava -ErrorAction SilentlyContinue
    if ($pidAnt -and (Get-Process -Id $pidAnt -ErrorAction SilentlyContinue)) { Anota "anterior ainda rodando (pid $pidAnt)"; exit 0 }
}
$PID | Out-File $trava -Encoding ascii

try {
    $jd = Join-Path $env:LOCALAPPDATA 'JDownloader 2\JDownloader2.exe'
    if (-not (Get-Process JDownloader2 -ErrorAction SilentlyContinue)) {
        Anota "JDownloader fechado - abrindo"
        Start-Process $jd
        Start-Sleep -Seconds 120
    }
    Set-Location $raiz
    & python -X utf8 abastecer_loop.py --uma-vez *>> $log
    Anota "passada terminou (exit $LASTEXITCODE)"
} finally {
    Remove-Item $trava -Force -ErrorAction SilentlyContinue
}
