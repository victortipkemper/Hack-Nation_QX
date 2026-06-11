# Autocomply starten — Doppelklick auf start.bat
$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "  AUTOCOMPLY START" -ForegroundColor Cyan
Write-Host "  ================" -ForegroundColor Cyan
Write-Host ""

function Stop-Port($port) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

$apiPort = 8010

Write-Host "[1/5] Alte Prozesse beenden (Port 3000, 3001, $apiPort)..." -ForegroundColor Yellow
Stop-Port 3000
Stop-Port 3001
Stop-Port $apiPort
Start-Sleep -Seconds 2

Write-Host "[2/5] API starten (Port $apiPort)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\api'; " +
    "Write-Host '>>> API: http://localhost:$apiPort' -ForegroundColor Green; " +
    "Write-Host '>>> Docs: http://localhost:$apiPort/docs' -ForegroundColor Gray; " +
    "python -m uvicorn main:app --host 127.0.0.1 --port $apiPort --reload"
)

Write-Host "[3/5] Warte auf kalibrierte Checkliste-API..." -ForegroundColor Yellow
$apiReady = $false
for ($i = 1; $i -le 25; $i++) {
    Start-Sleep -Seconds 1
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:$apiPort/api/health" -TimeoutSec 2
        if ($h.checklist_version -and $h.version -like "*checklist*") {
            Write-Host "  API bereit: $($h.version) / $($h.checklist_version)" -ForegroundColor Green
            $apiReady = $true
            break
        }
        Write-Host "  ... falsche API-Version: $($h.version)" -ForegroundColor Gray
    } catch {
        Write-Host "  ... $i s" -ForegroundColor Gray
    }
}
if (-not $apiReady) {
    Write-Host "  WARNUNG: API antwortet nicht korrekt auf Port $apiPort" -ForegroundColor Red
}

Write-Host "[4/5] Frontend starten (Port 3000, API -> $apiPort)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\frontend'; " +
    "`$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:$apiPort'; " +
    "Write-Host '>>> Frontend: http://localhost:3000' -ForegroundColor Green; " +
    "Write-Host '>>> API proxy: http://127.0.0.1:$apiPort' -ForegroundColor Gray; " +
    "npm run dev"
)

Write-Host "[5/5] Warte auf Frontend..." -ForegroundColor Yellow
$ready = $false
for ($i = 1; $i -le 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Write-Host "  ... $i s" -ForegroundColor Gray
}

if ($ready) {
    Write-Host ""
    Write-Host "  FERTIG! Oeffne http://localhost:3000" -ForegroundColor Green
    Start-Process "http://localhost:3000"
} else {
    Write-Host ""
    Write-Host "  Frontend braucht noch etwas. Oeffne manuell:" -ForegroundColor Yellow
    Write-Host "  http://localhost:3000" -ForegroundColor White
    Write-Host "  (oder http://localhost:3001 falls Port 3000 belegt)" -ForegroundColor Gray
    Start-Process "http://localhost:3000"
}

Write-Host ""
Write-Host "  Zwei PowerShell-Fenster muessen offen bleiben!" -ForegroundColor Cyan
Write-Host "  Zum Beenden: Fenster schliessen oder Ctrl+C" -ForegroundColor Gray
Write-Host ""
