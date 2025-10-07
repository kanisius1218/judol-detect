@echo off
title Multi-Platform Spam Moderator - Test
color 0A

echo ========================================
echo   Multi-Platform Spam Moderator
echo   Component Test
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak terinstall!
    echo.
    echo Silakan install Python dari: https://www.python.org/downloads/
    echo PENTING: Checklist "Add Python to PATH" saat install
    echo.
    pause
    exit /b 1
)

echo [OK] Python terdeteksi
python --version
echo.

REM Check if dependencies are installed
echo [INFO] Checking dependencies...
python -c "import googleapiclient" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Dependencies belum diinstall!
    echo.
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Gagal install dependencies!
        pause
        exit /b 1
    )
    echo.
)

echo [OK] Dependencies ready
echo.

REM Run test
echo ========================================
echo Running Component Tests...
echo ========================================
echo.

python test_all.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
echo.
pause
