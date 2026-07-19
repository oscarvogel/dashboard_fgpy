$ErrorActionPreference = 'Stop'

$backendDir = Join-Path $PSScriptRoot '..\backend'
$python = Join-Path $backendDir '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw "No existe $python. Cree el entorno con: py -m venv backend\.venv"
}

Push-Location $backendDir
try {
    & $python manage.py runserver
}
finally {
    Pop-Location
}
