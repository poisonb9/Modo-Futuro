# Wrapper do vigia_raw.py para o Agendador de Tarefas.
#
# Existe por dois motivos: fixar o diretório de trabalho (o vigia_raw lê o
# .env a partir dele) e guardar log, senão a tarefa roda cega e não há como
# saber por que um vídeo não foi processado.
#
# Registrado como tarefa S4U (ver REGISTRAR_VIGIA.ps1), que roda sem sessão
# interativa — é isso que impede a janela de piscar a cada execução.

$ErrorActionPreference = 'Stop'

$raiz   = 'C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine'
$python = 'C:\Program Files\Python314\python.exe'
$log    = Join-Path $raiz 'estado\vigia_raw.log'

New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

# Mantém o log num tamanho civilizado: acima de 1 MB, começa outro e guarda
# o anterior como .old (só uma geração — não vale a pena mais que isso).
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 1MB)) {
    Move-Item $log "$log.old" -Force
}

$carimbo = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Set-Location $raiz

# stderr junto do stdout: se o Python estourar, o traceback tem que cair no
# log em vez de sumir.
$saida = & $python -X utf8 vigia_raw.py --uma-vez 2>&1 | Out-String
$rc = $LASTEXITCODE

# Só registra passagem silenciosa numa linha; quando houve trabalho ou erro,
# grava a saída inteira. Senão o log vira parede de "nada novo".
if ($rc -eq 0 -and $saida -match 'Nada novo') {
    Add-Content -Path $log -Value "[$carimbo] nada novo" -Encoding utf8
} else {
    Add-Content -Path $log -Value "[$carimbo] (exit $rc)" -Encoding utf8
    Add-Content -Path $log -Value $saida.TrimEnd() -Encoding utf8
    Add-Content -Path $log -Value '' -Encoding utf8
}

exit $rc
