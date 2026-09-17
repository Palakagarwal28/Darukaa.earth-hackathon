# Double-click / right-click > Run with PowerShell, or:  powershell -ExecutionPolicy Bypass -File run_local.ps1
# Serves the app at http://127.0.0.1:8000  (stays up until you close this window)
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path "api/main.py")) { Write-Host "Run this from the project folder."; Read-Host "Press Enter"; exit 1 }
python -m pip install -q -r requirements.txt
Write-Host "`n  Darukaa.Earth at  http://127.0.0.1:8000   (API docs: /docs)`n" -ForegroundColor Green
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
Read-Host "`nServer stopped. Press Enter to close"
