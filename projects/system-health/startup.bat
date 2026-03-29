@echo off
REM ═══════════════════════════════════════════
REM YNAI5 Startup Automation v1.0
REM Runs at Windows login via Startup folder
REM ═══════════════════════════════════════════

SET WORKSPACE=C:\Users\shema\OneDrive\Desktop\YNAI5-SU
SET LOG=%WORKSPACE%\projects\system-health\logs\startup-log.txt

echo [%DATE% %TIME%] YNAI5 Startup triggered >> "%LOG%"

REM Wait for desktop/network to be ready
timeout /t 20 /nobreak >nul

REM Quick health snapshot
echo [%DATE% %TIME%] Health snapshot... >> "%LOG%"
python "%WORKSPACE%\projects\system-health\health-check.py" --quick 2>> "%LOG%"

REM Start Crypto Price Alert — PAUSED 2026-03-29 (moving to Oracle VM)
REM echo [%DATE% %TIME%] Starting price-alert... >> "%LOG%"
REM start /MIN "YNAI5-PriceAlert" python "%WORKSPACE%\projects\crypto-monitoring\price-alert.py"

REM Start Telegram Bridge (minimized)
echo [%DATE% %TIME%] Starting telegram-bridge... >> "%LOG%"
start /MIN "YNAI5-TelegramBridge" python "%WORKSPACE%\projects\personal-ai-infrastructure\telegram-claude-bridge.py"

echo [%DATE% %TIME%] YNAI5 startup complete >> "%LOG%"
