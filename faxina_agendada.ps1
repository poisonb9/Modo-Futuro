# Faxina diaria do disco (pedido do dono 07/10/2026). Tarefa: ModoFuturo_Faxina, 05:00.
# Bruto/orfao so' sai do PC se o Drive tiver o MESMO arquivo (nome + bytes).
Set-Location -LiteralPath $PSScriptRoot
$log = Join-Path $PSScriptRoot "estado\faxina.log"
"==== $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Out-File -Append -Encoding utf8 $log
python -X utf8 ferramentas\faxina.py --apagar *>&1 | Out-File -Append -Encoding utf8 $log
