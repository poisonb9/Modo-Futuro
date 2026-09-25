# Aviso de queda por E-MAIL — Agendador de Tarefas, de hora em hora (:45).
# Roda NA MAQUINA de proposito: mexe com e-mail de gente (LGPD) e o repo e
# os logs do Actions sao publicos. Ver engine/alertas_email.py.
# O log em _privado/ (fora do git) so' guarda CONTAGENS, nunca endereco.
$ErrorActionPreference = 'Continue'
$raiz   = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = 'C:\Program Files\Python314\python.exe'
$log    = Join-Path $raiz '_privado\alertas_email.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 1MB)) { Move-Item $log "$log.old" -Force }
Set-Location $raiz
$carimbo = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$saida = (& $python -X utf8 -m engine.alertas_email 2>&1 | Out-String)
$rc = $LASTEXITCODE
$linha = ($saida.Trim() -split "`n" | Where-Object { $_ -match 'alertas_email' } | Select-Object -Last 1)
if (-not $linha) { $linha = "rc=$rc " + (($saida.Trim() -split "`n")[-1]) }
Add-Content -Path $log -Value "[$carimbo] $linha"
