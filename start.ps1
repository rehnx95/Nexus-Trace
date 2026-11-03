$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$Python = Join-Path $BackendDir "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Backend environment is missing. Run: cd backend; .\setup.ps1"
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $FrontendDir
    npm.cmd install
    Pop-Location
}

$backendCommand = "Set-Location '$BackendDir'; `& '$Python' -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
$frontendCommand = "Set-Location '$FrontendDir'; npm.cmd run dev -- --host 127.0.0.1 --port 5173"

Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "Backend:  http://127.0.0.1:8000/health"
Write-Host "Frontend: http://127.0.0.1:5173"
