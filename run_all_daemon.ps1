$env:PYTHONIOENCODING = "utf-8"
$env:DATABASE_URL = "sqlite:///./swiply.db"
$env:SECRET_KEY = "supersecretkey123456789012345678"

$processes = @()

Write-Host "Starting Frontend (5173)..."
$processes += Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "$PWD\frontend" -PassThru -NoNewWindow

Write-Host "Starting API Gateway (8000)..."
$processes += Start-Process -FilePath "python.exe" -ArgumentList "api_gateway.py" -WorkingDirectory $PWD -PassThru -NoNewWindow

Write-Host "Starting Auth Service (8001)..."
$processes += Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "services.auth.app.main:app --host 0.0.0.0 --port 8001 --no-access-log" -WorkingDirectory $PWD -PassThru -NoNewWindow

Write-Host "Starting Job Service (8003)..."
$processes += Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "services.job.app.main:app --host 0.0.0.0 --port 8003 --no-access-log" -WorkingDirectory $PWD -PassThru -NoNewWindow

Write-Host "Starting Profile Service (8004)..."
$processes += Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "services.profile.app.main:app --host 0.0.0.0 --port 8004 --no-access-log" -WorkingDirectory $PWD -PassThru -NoNewWindow

Write-Host "Starting Automation Service (8006)..."
$processes += Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "services.automation.app.main:app --host 0.0.0.0 --port 8006 --no-access-log" -WorkingDirectory $PWD -PassThru -NoNewWindow

Write-Host "Starting Credential Service (8009)..."
$processes += Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "services.credential.app.main:app --host 0.0.0.0 --port 8009 --no-access-log" -WorkingDirectory $PWD -PassThru -NoNewWindow

Write-Host "Starting AI Service (8010)..."
$processes += Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "services.ai.app.main:app --host 0.0.0.0 --port 8010 --no-access-log" -WorkingDirectory $PWD -PassThru -NoNewWindow

Write-Host "Starting WTTJ Service (8012)..."
$processes += Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "services.wttj.app.main:app --host 0.0.0.0 --port 8012 --no-access-log" -WorkingDirectory $PWD -PassThru -NoNewWindow

Write-Host "All services started. Waiting for processes..."
Wait-Process -InputObject $processes
