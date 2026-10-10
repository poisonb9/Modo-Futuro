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

function JdResponde {
    try { Invoke-WebRequest 'http://127.0.0.1:3128/jd/version' -UseBasicParsing -TimeoutSec 30 | Out-Null; return $true }
    catch { return $false }
}
function AvisaTelegram($texto) {
    # 05/10/2026 (dono: "me avisa se travar porque o JDownloader deu problema")
    $env_ = @{}
    Get-Content (Join-Path $raiz '.env') -Encoding UTF8 | Where-Object { $_ -match '^[A-Z_0-9]+=' } |
        ForEach-Object { $k, $v = $_ -split '=', 2; $env_[$k] = $v.Trim() }
    if (-not ($env_.TELEGRAM_BOT_ALERTA -and $env_.TELEGRAM_CHAT_DONO)) { return }
    try {
        Invoke-RestMethod "https://api.telegram.org/bot$($env_.TELEGRAM_BOT_ALERTA)/sendMessage" -Method Post `
            -ContentType 'application/json; charset=utf-8' `
            -Body ([Text.Encoding]::UTF8.GetBytes((@{ chat_id = $env_.TELEGRAM_CHAT_DONO; text = $texto } | ConvertTo-Json))) | Out-Null
    } catch { Anota "telegram falhou: $($_.Exception.Message)" }
}

try {
    $jd = Join-Path $env:LOCALAPPDATA 'JDownloader 2\JDownloader2.exe'
    # 05/10/2026 (dono: "reabrir ele quando ele fechar sozinho"): fechado ->
    # abre; ABERTO MAS SEM RESPONDER (travado) -> fecha e reabre; e se nem
    # assim voltar, avisa no Telegram (uma vez por hora, no maximo).
    $falhas = Join-Path $raiz 'estado\jd_falhas.txt'
    if (JdResponde) { '0' | Out-File $falhas -Encoding ascii }
    else {
        # 05/10/2026: em 01:27 uma resposta lenta (JD ocupado baixando) fez a
        # tarefa MATAR um JDownloader que funcionava. Aberto e sem responder:
        # so' reinicia na 3a falha seguida (~1h30); antes so' anota e espera.
        $nf = 1 + [int]("0" + (Get-Content $falhas -ErrorAction SilentlyContinue))
        "$nf" | Out-File $falhas -Encoding ascii
        # 10/10/2026: JD "aberto" com < 150 MB ha' mais de 5 min nao esta'
        # ocupado baixando: travou na abertura (visto 01:38, 40 MB, API muda).
        # Esse nao espera 3 passadas: reinicia ja'.
        $travadoNaAbertura = Get-Process JDownloader2 -ErrorAction SilentlyContinue |
            Where-Object { $_.WorkingSet64 -lt 150MB -and $_.StartTime -lt (Get-Date).AddMinutes(-5) }
        $pularJd = $false
        if ((Get-Process JDownloader2 -ErrorAction SilentlyContinue) -and $nf -lt 3 -and -not $travadoNaAbertura) {
            # 10/10/2026: antes era `exit 0` e a passada INTEIRA parava (subir
            # ao Drive, expirar pendente, radar) por ate' 1h30. So' o JD espera;
            # o resto roda (o abastecer_loop ja' trata JD sem resposta).
            Anota "JDownloader sem responder ($nf/3) - espero a proxima passada para reiniciar; o resto da passada segue"
            $pularJd = $true
        }
        if (-not $pularJd) {
        if (Get-Process JDownloader2 -ErrorAction SilentlyContinue) {
            Anota "JDownloader sem responder ou travado na abertura - reiniciando"
            Get-Process JDownloader2 | Stop-Process -Force
            Start-Sleep -Seconds 10
        } else { Anota "JDownloader fechado - abrindo" }
        Start-Process $jd
        for ($i = 0; $i -lt 18 -and -not (JdResponde); $i++) { Start-Sleep -Seconds 10 }
        if (JdResponde) { Anota "JDownloader voltou" }
        else {
            Anota "[!] JDownloader NAO voltou em 3 min"
            $marca = Join-Path $raiz 'estado\jd_avisado.txt'
            $ultimo = if (Test-Path $marca) { (Get-Item $marca).LastWriteTime } else { [datetime]::MinValue }
            if ((Get-Date) - $ultimo -gt [timespan]::FromHours(1)) {
                AvisaTelegram "⚠️ JDownloader travado na VPS: reabri e ele nao voltou em 3 min. Sem ele nenhum canal recebe video novo. Confira a janela dele (atualizacao/aviso) ou a opcao 'Deprecated API'."
                Get-Date | Out-File $marca
            }
        }
        }
    }
    Set-Location $raiz
    # *>> no PowerShell 5 grava UTF-16 no meio do log UTF-8 (log ilegivel, 05/10)
    & python -X utf8 abastecer_loop.py --uma-vez 2>&1 | Out-File $log -Append -Encoding utf8
    Anota "passada terminou (exit $LASTEXITCODE)"
} finally {
    Remove-Item $trava -Force -ErrorAction SilentlyContinue
}
