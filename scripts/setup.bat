@echo off
title Setup - Multi-Platform Spam Moderator
color 0A

echo ========================================
echo   Multi-Platform Spam Moderator
echo   Setup Script
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak terinstall!
    echo.
    echo Download dari: https://www.python.org/downloads/
    echo PENTING: Checklist "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python detected
python --version
echo.

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed
echo.

REM Create .env if not exists
if not exist .env (
    echo [INFO] Creating .env file...
    copy config\config.example.env .env
    echo [OK] .env file created
    echo.
    echo [IMPORTANT] Edit .env file with your API keys!
    echo.
) else (
    echo [INFO] .env file already exists
    echo.
)

REM Create directories
if not exist logs mkdir logs
if not exist reports mkdir reports

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: scripts\run.bat
echo.
pause
