# ============================================================================
#  SWIPLY - START ALL SERVICES (PowerShell Version)
#  One command to start the entire microservices architecture
# ============================================================================

$ErrorActionPreference = "Continue"
$RootPath = "c:\Users\hp\Downloads\WTJ"
Set-Location $RootPath

Write-Host "`n" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  🚀 SWIPLY COMPLETE SYSTEM STARTUP" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor White

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Function to start a service in a new terminal
function Start-Service {
    param(
        [string]$ServiceName,
        [string]$Port,
        [string]$Command,
        [int]$Index,
        [int]$Total
    )
    
    Write-Host "[$Index/$Total] Starting $ServiceName on port $Port..." -ForegroundColor Yellow
    
    $encodedCommand = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($Command))
    Start-Process powershell.exe -ArgumentList "-NoExit", "-EncodedCommand", $encodedCommand -WindowStyle Normal
    
    Start-Sleep -Seconds 2
}

$services = @(
    @{ Name = "Frontend (React Vite)"; Port = "5173"; Path = "frontend"; Command = "cd frontend; npm run dev" },
    @{ Name = "Auth Service"; Port = "8001"; Path = "services\auth"; Command = "cd services\auth; python -m uvicorn app.main:app --reload --port 8001" },
    @{ Name = "Profile Service"; Port = "8004"; Path = "services\profile"; Command = "cd services\profile; python -m uvicorn app.main:app --reload --port 8004" },
    @{ Name = "Job Service"; Port = "8003"; Path = "services\job"; Command = "cd services\job; python -m uvicorn app.main:app --reload --port 8003" },
    @{ Name = "Credential Service"; Port = "8009"; Path = "services\credential"; Command = "cd services\credential; python -m uvicorn app.main:app --reload --port 8009" },
    @{ Name = "Email Service"; Port = "8007"; Path = "services\email"; Command = "cd services\email; python -m uvicorn app.main:app --reload --port 8007" },
    @{ Name = "Automation Service"; Port = "8006"; Path = "services\automation"; Command = "cd services\automation; python -m uvicorn app.main:app --reload --port 8006" },
    @{ Name = "AI Service"; Port = "8010"; Path = "services\ai"; Command = "cd services\ai; python -m uvicorn app.main:app --reload --port 8010" },
    @{ Name = "WTTJ Service"; Port = "8012"; Path = "services\wttj"; Command = "cd services\wttj; python -m uvicorn app.main:app --reload --port 8012" },
    @{ Name = "API Gateway"; Port = "8000"; Path = "."; Command = "python api_gateway.py" },
    @{ Name = "Gmail Integration"; Port = "8008"; Path = "."; Command = "python gmail_integration_service.py" }
)

$total = $services.Count
$index = 1

Write-Host "Starting all services...`n" -ForegroundColor Cyan

foreach ($service in $services) {
    Start-Service -ServiceName $service.Name -Port $service.Port -Command $service.Command -Index $index -Total $total
    $index++
}

Write-Host "`n" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  ✅ ALL SERVICES STARTED" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor White

Write-Host "📍 Services Available At:" -ForegroundColor Green
Write-Host "`n" -ForegroundColor White

$endpoints = @(
    "Frontend              → http://localhost:5173",
    "API Gateway           → http://localhost:8000",
    "Auth Service          → http://localhost:8001",
    "Job Service           → http://localhost:8003",
    "Profile Service       → http://localhost:8004",
    "Automation Service    → http://localhost:8006",
    "Email Service         → http://localhost:8007",
    "Gmail Integration     → http://localhost:8008",
    "Credential Service    → http://localhost:8009",
    "AI Service            → http://localhost:8010",
    "WTTJ Service          → http://localhost:8012"
)

foreach ($endpoint in $endpoints) {
    Write-Host "   $endpoint" -ForegroundColor Cyan
}

Write-Host "`n" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  🎯 QUICK START" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor White

Write-Host "1. Wait 15 seconds for all services to initialize" -ForegroundColor Yellow
Write-Host "2. Open browser: " -ForegroundColor Yellow -NoNewline
Write-Host "http://localhost:5173" -ForegroundColor Cyan
Write-Host "3. Register/Login to Swiply" -ForegroundColor Yellow
Write-Host "4. Go to Dashboard and connect WTTJ account" -ForegroundColor Yellow
Write-Host "5. Go to Job Swipe and start swiping!" -ForegroundColor Yellow

Write-Host "`n" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  📊 SYSTEM ARCHITECTURE" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor White

Write-Host "Frontend Layer:" -ForegroundColor Green
Write-Host "   • React Vite SPA (5173)" -ForegroundColor White

Write-Host "`nMicroservices:" -ForegroundColor Green
Write-Host "   • Auth Service (8001) - User authentication" -ForegroundColor White
Write-Host "   • Profile Service (8002) - User profile management" -ForegroundColor White
Write-Host "   • Job Service (8003) - Job matching & recommendations" -ForegroundColor White
Write-Host "   • Credential Service (8004) - Career site credentials" -ForegroundColor White
Write-Host "   • Email Service (8005) - Email management" -ForegroundColor White
Write-Host "   • Automation Service (8006) - Ollama AI automation" -ForegroundColor White
Write-Host "   • Gmail Integration (8008) - Gmail OAuth & emails" -ForegroundColor White

Write-Host "`nAPI Layer:" -ForegroundColor Green
Write-Host "   • API Gateway (8000) - Main orchestrator" -ForegroundColor White

Write-Host "`n" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  ⚠️  IMPORTANT NOTES" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor White

Write-Host "• Each service runs in its own terminal window" -ForegroundColor Yellow
Write-Host "• Do NOT close windows while using the application" -ForegroundColor Yellow
Write-Host "• Check individual windows for error messages" -ForegroundColor Yellow
Write-Host "• Logs are displayed in each service's terminal" -ForegroundColor Yellow
Write-Host "• If a service crashes, close its window and manually restart it" -ForegroundColor Yellow
Write-Host "• First startup may take 30-60 seconds for all services to initialize" -ForegroundColor Yellow

Write-Host "`n" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  ✨ READY TO USE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor White
