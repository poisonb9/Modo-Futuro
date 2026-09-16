# Publicacao diaria do site mae — Agendador de Tarefas, 11:30 UTC.
#
# ⭐ POR QUE EXISTE (16/09/2026): a humanizacao dos nomes so' rodava a mao
# (cache parado em 14/09, 36 titulos crus na pagina) e a publicacao do site
# dependia do Claude estar numa sessao. O garimpo da nuvem (10:23 UTC) e o ML
# ja' commitam o estado; falta alguem puxar, dar nome, e por no ar.
#
# ⚠️ POR QUE AQUI, E NAO NO GITHUB ACTIONS: o workflow nao tem chave de
# modelo (Gemini/OpenRouter) nem o CF_API_TOKEN do Pages — tudo isso vive no
# `.env` desta maquina. Mesmo raciocinio do ciclo_semanal_agendado.ps1.
#
# ⚠️ Registrada como S4U (sem janela), igual ao vigia.

$ErrorActionPreference = 'Stop'
$raiz   = 'C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine'
$python = 'C:\Program Files\Python314\python.exe'
$log    = Join-Path $raiz 'estado\publicar_diario.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 1MB)) { Move-Item $log "$log.old" -Force }
$carimbo = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Set-Location $raiz
# ⚠️ A SESSAO S4U NAO TEM O PATH DO USUARIO: o primeiro disparo (16/09 20:52)
# morreu em FileNotFoundError porque o publicador chama `git` e `npx`.
$env:PATH = 'C:\Program Files\nodejs;C:\Program Files\Git\cmd;C:\Program Files\Git\mingw64\bin;C:\Program Files\Git\usr\bin;C:\Program Files\GitHub CLI;' + $env:PATH

# ⚠️ 'Continue' durante os nativos: com 'Stop', qualquer stderr do python vira
# erro terminante e o log nem e' escrito (medido em 09/09 no ciclo).
$ErrorActionPreference = 'Continue'
$saida = ''
# 1. o estado da nuvem (garimpo, ML, precos). `stash` protege sujeira local.
$saida += (& git stash -q -u 2>&1 | Out-String)
$saida += (& git pull --rebase -q 2>&1 | Out-String)
$saida += (& git stash pop -q 2>&1 | Out-String)
# 2. nomes curtos (Gemini -> OpenRouter -> ModelScope; sem cota, fica o corte)
$saida += (& $python -X utf8 -m engine.nome_produto 2>&1 | Out-String)
# 3. publica e CONFERE no ar (estoura se nao subiu)
$saida += (& $python -X utf8 paginas/publicar_bio.py --subir 2>&1 | Out-String)
$rc = $LASTEXITCODE
# 4. devolve o cache de nomes pra nuvem (o garimpo de la' tambem le)
if (Test-Path 'estado\nomes_curtos.json') {
    $saida += (& git add -f estado/nomes_curtos.json 2>&1 | Out-String)
    $saida += (& git commit -q -m 'nomes: cache do dia (publicacao diaria)' 2>&1 | Out-String)
    $saida += (& git push -q 2>&1 | Out-String)
}
$ErrorActionPreference = 'Stop'

$ok = ($rc -eq 0) -and ($saida -match 'nenhum faltando')
$linha = if ($ok) { "OK  publicado e conferido" } else { "FALHOU rc=$rc" }
Add-Content -Path $log -Value "[$carimbo] $linha"
Add-Content -Path $log -Value ($saida -split "`n" | Where-Object { $_ -match 'catalogo:|multometro:|nome\(s\) novo|endereco\(s\)|NAO |Error|Traceback|File "|line ' } | ForEach-Object { "    $_" })
exit $rc
