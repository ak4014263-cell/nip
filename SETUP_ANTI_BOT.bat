@echo off
echo ================================================================================
echo ANTI-BOT DETECTION SOLUTION - SETUP SCRIPT
echo ================================================================================
echo.
echo This script will install all required dependencies for the anti-bot solution.
echo.
echo Components:
echo   - Playwright with stealth mode
echo   - Playwright-stealth library
echo   - HTTP client (httpx)
echo   - Enhanced adapters and utilities
echo.
echo ================================================================================
echo.

pause

echo.
echo [1/4] Installing Python dependencies...
echo ================================================================================
cd services\automation
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Installing Playwright browsers...
echo ================================================================================
python -m playwright install chromium

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Playwright browsers
    pause
    exit /b 1
)

echo.
echo [3/4] Installing playwright-stealth (optional enhancement)...
echo ================================================================================
pip install playwright-stealth

if errorlevel 1 (
    echo.
    echo WARNING: playwright-stealth installation failed (optional)
    echo Continuing anyway...
)

cd ..\..

echo.
echo [4/4] Verifying installation...
echo ================================================================================
python -c "import playwright; print('✓ Playwright installed')"
python -c "import httpx; print('✓ httpx installed')"
python -c "import asyncio; print('✓ asyncio available')"

echo.
echo ================================================================================
echo ✓ SETUP COMPLETE!
echo ================================================================================
echo.
echo Next steps:
echo   1. Run tests: python test_anti_bot_solution.py
echo   2. Read guide: ANTI_BOT_SOLUTION_GUIDE.md
echo   3. Test stealth browser: cd services\automation\app ^&^& python stealth_browser.py
echo.
echo Optional:
echo   - Set WTTJ_API_KEY environment variable if you have an API key
echo   - Configure residential proxies in stealth_browser.py (recommended)
echo.
echo ================================================================================
echo.

pause
