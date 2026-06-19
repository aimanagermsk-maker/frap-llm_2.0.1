# Локальная сборка и запуск (Windows PowerShell).

$ErrorActionPreference = "Stop"

$ImageName = "frap-llm-helper-img"
$ContainerName = "frap-llm-helper-app"
$AppPort = 8000
$AppProfile = if ($env:APP_PROFILE) { $env:APP_PROFILE } else { "sandbox" }
$ProjectRoot = $PSScriptRoot
$ServerConfigDir = Join-Path $ProjectRoot "settings\server"

docker stop $ContainerName 2>$null
if ($LASTEXITCODE -gt 1) { exit $LASTEXITCODE }

docker rm $ContainerName 2>$null
if ($LASTEXITCODE -gt 1) { exit $LASTEXITCODE }

docker image rm -f $ImageName 2>$null
if ($LASTEXITCODE -gt 1) { exit $LASTEXITCODE }

docker build -t $ImageName $ProjectRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# -v: yaml settings/server/{profile}.yaml с хоста перезаписывает и дополняет свойства конфига профиля из образа
docker run -d `
  -p "${AppPort}:${AppPort}" `
  --restart unless-stopped `
  --name $ContainerName `
  -e "APP_PROFILE=$AppProfile" `
  -v "${ServerConfigDir}:/app/settings/server:ro" `
  $ImageName

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Started $ContainerName with APP_PROFILE=$AppProfile"
Write-Host "http://localhost:${AppPort}/hello"
Write-Host "http://localhost:${AppPort}/docs"
