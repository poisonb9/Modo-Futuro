# Wrapper do ciclo_semanal.py para o Agendador de Tarefas.
#
# Ordem do Bryan em 08/09/2026: "quando um canal comecar a ficar sem videos
# para cortar voce vai rodar um radar em cima dos 2 videos que mais
# viralizaram na semana, baixar 5 novas fontes e por pra cortar; testar isso
# sucessivamente por 1 mes".
#
# ⚠️ POR QUE UMA TAREFA AGENDADA, E NAO EU.
#
# Eu NAO rodo entre os turnos do Bryan. "Vou rodando o ciclo ao longo do mes"
# so' funciona se ele ficar me cutucando todo dia — que e' exatamente o que
# ele nao quer. O mesmo raciocinio que ja' esta' escrito no cortar_fila.yml.
#
# ⚠️ E POR QUE AQUI, E NAO NO GITHUB ACTIONS: o ciclo BAIXA video, e o
# YouTube bloqueia IP de datacenter. O `cortar.yml` nunca teve um success na
# vida por causa disso. O download so' funciona nesta maquina.
#
# Registrado como tarefa S4U, igual ao vigia — e' isso que impede a janela de
# piscar a cada execucao (o Telegram_Poll ja' teve esse problema em 28/07).

$ErrorActionPreference = 'Stop'

$raiz   = 'C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine'
$python = 'C:\Program Files\Python314\python.exe'
$log    = Join-Path $raiz 'estado\ciclo_semanal.log'

New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

if ((Test-Path $log) -and ((Get-Item $log).Length -gt 1MB)) {
    Move-Item $log "$log.old" -Force
}

$carimbo = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Set-Location $raiz

$saida = & $python -X utf8 ciclo_semanal.py --todos 2>&1 | Out-String
$rc = $LASTEXITCODE

# ⚠️ O LOG SEPARA "NAO PRECISOU" DE "NAO CONSEGUIU". Sao a mesma linha pra
# quem le' rapido, e sao coisas opostas: o primeiro e' o sistema saudavel, o
# segundo e' o sistema cego. Foi confundir esses dois que deixou 1921
# passagens silenciosas do vigia esconderem um bruto parado por 2h.
$precisou = $saida -match '([1-9]\d*) canal\(is\) precisaram'
$abortou  = $saida -match 'abortado'

if ($rc -eq 0 -and -not $precisou -and -not $abortou) {
    Add-Content -Path $log -Value "[$carimbo] todos acima do piso — nada a repor" -Encoding utf8
    exit 0
}

Add-Content -Path $log -Value "[$carimbo] (exit $rc)" -Encoding utf8
Add-Content -Path $log -Value $saida.TrimEnd() -Encoding utf8
Add-Content -Path $log -Value '' -Encoding utf8

# Avisa no Telegram quando houve trabalho ou quando travou. Passagem em que
# nada precisou ser feito NAO avisa: aviso diario que quase sempre diz "nada"
# deixa de ser lido, e ai' o dia em que ele diz algo tambem nao e'.
$env:PYTHONIOENCODING = 'utf-8'
try {
    $txt = "Ciclo semanal ($carimbo)`n`n" + $saida.TrimEnd()
    if ($txt.Length -gt 3500) { $txt = $txt.Substring(0, 3500) + "`n[...]" }
    & $python -X utf8 -c @"
import sys
sys.path.insert(0, r'$raiz')
from engine import telegram
if telegram.configurado():
    telegram.enviar(sys.stdin.read())
"@ <<< $txt | Out-Null
} catch {
    Add-Content -Path $log -Value "[$carimbo] [!] aviso nao saiu no Telegram: $_" -Encoding utf8
}

exit $rc
