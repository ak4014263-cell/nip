@echo off
REM ============================================================================
REM  SWIPLY - START ALL SERVICES
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "c:\Users\hp\Downloads\WTJ"

echo.
echo ============================================================================
echo  STARTING ALL SERVICES
echo ============================================================================
echo.

REM Profile Service - Port 8004
echo [1/6] Starting Profile Service on port 8004...
start "Profile Service" cmd /k "cd /d c:\Users\hp\Downloads\WTJ\services\profile & python -m uvicorn app.main:app --reload --port 8004"
timeout /t 2 /nobreak

REM Credential Service - Port 8009
echo [2/6] Starting Credential Service on port 8009...
start "Credential Service" cmd /k "cd /d c:\Users\hp\Downloads\WTJ\services\credential & python -m uvicorn app.main:app --reload --port 8009"
timeout /t 2 /nobreak

REM Email Service - Port 8007
echo [3/6] Starting Email Service on port 8007...
start "Email Service" cmd /k "cd /d c:\Users\hp\Downloads\WTJ\services\email & python -m uvicorn app.main:app --reload --port 8007"
timeout /t 2 /nobreak

REM Automation Service - Port 8006
echo [4/6] Starting Automation Service on port 8006...
start "Automation Service" cmd /k "cd /d c:\Users\hp\Downloads\WTJ\services\automation & python -m uvicorn app.main:app --reload --port 8006"
timeout /t 2 /nobreak

REM Gmail Integration Service - Port 8008
echo [5/6] Starting Gmail Integration Service on port 8008...
start "Gmail Integration" cmd /k "cd /d c:\Users\hp\Downloads\WTJ & python gmail_integration_service.py"
timeout /t 2 /nobreak

REM AI Service - Port 8010
echo [6/8] Starting AI Service on port 8010...
start "AI Service" cmd /k "cd /d c:\Users\hp\Downloads\WTJ\services\ai & python -m uvicorn app.main:app --reload --port 8010"
timeout /t 2 /nobreak

REM WTTJ Microservice - Port 8012
echo [7/8] Starting WTTJ Microservice on port 8012...
start "WTTJ Service" cmd /k "cd /d c:\Users\hp\Downloads\WTJ\services\wttj & python -m uvicorn app.main:app --reload --port 8012"
timeout /t 2 /nobreak

echo [8/8] All services queued to start
echo.
echo ============================================================================
echo  SERVICES STATUS
echo ============================================================================
echo.
echo Running:
echo   Port 5173 - Frontend
echo   Port 8000 - API Gateway
echo   Port 8001 - Auth Service
echo   Port 8003 - Job Service
echo.
echo Starting Now:
echo   Port 8004 - Profile Service
echo   Port 8006 - Automation Service
echo   Port 8007 - Email Service
echo   Port 8008 - Gmail Integration
echo   Port 8009 - Credential Service
echo   Port 8010 - AI Service
echo   Port 8012 - WTTJ Service
echo.
echo ============================================================================
echo.
pause



