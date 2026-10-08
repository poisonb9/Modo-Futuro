# Vigia de saude do abastecimento (pedido do dono 08/10/2026). Tarefa: ModoFuturo_Vigia_Saude, a cada 30 min.
# Reinicia o JDownloader mudo, reenvia pendentes perdidos, roda faxina se o disco apertar,
# liga/desliga o criterio de emergencia por canal e avisa no Telegram quando algo muda.
Set-Location -LiteralPath $PSScriptRoot
$log = Join-Path $PSScriptRoot "estado\vigia_saude.log"
python -X utf8 ferramentas\vigia_saude.py *>&1 | Out-File -Append -Encoding utf8 $log
