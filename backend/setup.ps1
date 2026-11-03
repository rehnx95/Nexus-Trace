param(
    [string]$PythonVersion = "3.12"
)

$ErrorActionPreference = "Stop"
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $BackendDir "venv"

Set-Location $BackendDir

Write-Host "NexusTrace backend setup"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python $PythonVersion from https://www.python.org/downloads/"
}

$python312 = py -3.12 -c "import sys; print(sys.executable)" 2>$null
if (-not $python312) {
    throw "Python 3.12 is required. Install it from https://www.python.org/downloads/release/python-31210/"
}

$version = py -3.12 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
Write-Host "Using Python $version"

if (Test-Path $VenvDir) {
    Write-Host "Removing the incompatible existing virtual environment..."
    Remove-Item -LiteralPath $VenvDir -Recurse -Force
}

py -3.12 -m venv $VenvDir
$python = Join-Path $VenvDir "Scripts\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

Write-Host "Backend dependencies installed successfully."
