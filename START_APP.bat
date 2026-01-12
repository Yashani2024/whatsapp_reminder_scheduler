@echo off
REM WhatsApp Reminder Manager - Windows Launcher

echo ========================================
echo   WhatsApp Reminder Manager
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    pause
    exit /b 1
)

echo Starting application...
python main.py

echo Application closed.
pause