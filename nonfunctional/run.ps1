$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw "Python virtual environment not found: $python"
}
$env:PYTHONPATH = $root
$env:MYSQL_DATABASE = 'news_app_test'
$env:REDIS_DB = '15'
Push-Location $root
try {
    & $python -m nonfunctional.run_suite @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
