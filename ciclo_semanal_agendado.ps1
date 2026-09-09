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

# ⚠️ `ErrorActionPreference` VOLTA A 'Continue' SO' NESTA CHAMADA, e nao e'
# frescura: no Windows PowerShell 5.1, com 'Stop' ligado, QUALQUER linha que o
# python escreva em stderr sob `2>&1` vira um ErrorRecord terminante
# (NativeCommandError). O script morre AQUI — antes de escrever o log, antes do
# aviso no Telegram — e o unico sinal e' o exit 1 na tela do Agendador.
#
# MEDIDO em 09/09/2026: a tarefa do ciclo rodou as 13:00, gravou o radar, e nao
# deixou UMA linha de log. Reproduzido em duas linhas de PowerShell: um python
# que escreve em stderr e sai 1 mata o wrapper antes do `Add-Content`.
#
# ⚠️ E' o contrario do que o comentario abaixo promete. Um traceback e'
# EXATAMENTE o caso em que o log precisa existir — e era exatamente o caso em
# que ele deixava de existir.
$ErrorActionPreference = 'Continue'
$saida = & $python -X utf8 ciclo_semanal.py --todos 2>&1 | Out-String
$rc = $LASTEXITCODE
$ErrorActionPreference = 'Stop'

# ⚠️ O LOG SEPARA "NAO PRECISOU" DE "NAO CONSEGUIU". Sao a mesma linha pra
# quem le' rapido, e sao coisas opostas: o primeiro e' o sistema saudavel, o
# segundo e' o sistema cego. Foi confundir esses dois que deixou 1921
# passagens silenciosas do vigia esconderem um bruto parado por 2h.
$precisou = $saida -match '([1-9]\d*) canal\(is\) precisaram'
$abortou  = $saida -match 'abortado'

# ⚠️ NADA DE CARACTERE FORA DO ASCII DENTRO DE STRING NESTE ARQUIVO.
#
# MEDIDO em 08/09/2026: esta linha dizia "...do piso — nada a repor", com
# travessao. O arquivo nao tem BOM, entao o Windows PowerShell 5.1 o le' como
# cp1252 — e os bytes UTF-8 do travessao (E2 80 94) viram tres caracteres, o
# ultimo dos quais e' ASPA DUPLA. A string fechava no meio, o bloco perdia a
# chave, e o arquivo INTEIRO deixava de ser parseavel.
#
# A tarefa teria sido registrada com sucesso e morrido na primeira execucao,
# sem log nenhum. Em comentario o mesmo caractere e' inofensivo (comentario vai
# ate' o fim da linha) — por isso o wrapper do vigia convive com ele ha' meses.
if ($rc -eq 0 -and -not $precisou -and -not $abortou) {
    Add-Content -Path $log -Value "[$carimbo] todos acima do piso - nada a repor" -Encoding utf8
    exit 0
}

Add-Content -Path $log -Value "[$carimbo] (exit $rc)" -Encoding utf8
Add-Content -Path $log -Value $saida.TrimEnd() -Encoding utf8
Add-Content -Path $log -Value '' -Encoding utf8

# Avisa no Telegram quando houve trabalho ou quando travou. Passagem em que
# nada precisou ser feito NAO avisa: aviso diario que quase sempre diz "nada"
# deixa de ser lido, e ai' o dia em que ele diz algo tambem nao e'.
#
# ⚠️ A MENSAGEM VAI POR ARQUIVO, e nao por here-string nem por stdin.
#
# A primeira versao deste bloco usava `python -c @"..."@ <<< $txt`. O `<<<` e'
# here-string do BASH — em PowerShell nao existe, e o arquivo inteiro deixava
# de ser parseavel. A tarefa teria sido registrada com sucesso e morrido na
# primeira execucao, sem nunca ter rodado o ciclo, e o unico sinal seria a
# ausencia de log. Achado por `Parser::ParseFile` antes da primeira rodada.
$env:PYTHONIOENCODING = 'utf-8'
try {
    $txt = "Ciclo semanal ($carimbo)" + [Environment]::NewLine + [Environment]::NewLine + $saida.TrimEnd()
    if ($txt.Length -gt 3500) { $txt = $txt.Substring(0, 3500) + [Environment]::NewLine + '[...]' }
    $msg = Join-Path $env:TEMP 'ciclo_semanal_aviso.txt'
    Set-Content -Path $msg -Value $txt -Encoding utf8
    $codigo = 'import io,sys; sys.path.insert(0, sys.argv[1]); from engine import telegram; ' +
              'telegram.enviar(io.open(sys.argv[2], encoding="utf-8").read()) if telegram.configurado() else None'
    & $python -X utf8 -c $codigo $raiz $msg | Out-Null
    Remove-Item $msg -ErrorAction SilentlyContinue
} catch {
    Add-Content -Path $log -Value "[$carimbo] [!] aviso nao saiu no Telegram: $_" -Encoding utf8
}

exit $rc
