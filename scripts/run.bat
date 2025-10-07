@echo off
title Multi-Platform Spam Moderator
color 0A

echo ========================================
echo   Multi-Platform Spam Moderator
echo   Version 2.0.0
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak terinstall!
    pause
    exit /b 1
)

echo [OK] Python detected
echo.

REM Run main bot
echo Starting bot...
echo.
python src\main.py

pause
