@echo off
REM ============================================
REM  Polymarket Arbitrage Bot - Launcher
REM ============================================

REM Check for admin rights and request elevation if needed
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title Polymarket Arbitrage Bot

REM Change to the directory where this script is located
cd /d "%~dp0"

REM Find Python command
set PYTHON_CMD=
python3 -c "import PyQt6" 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=python3
) else (
    python -c "import PyQt6" 2>nul
    if not errorlevel 1 (
        set PYTHON_CMD=python
    ) else (
        echo.
        echo ========================================
        echo   MISSING DEPENDENCIES
        echo ========================================
        echo.
        echo Please run the installer:
        echo INSTALL_AND_SETUP.bat
        echo.
        pause
        exit /b 1
    )
)

REM Launch app
echo.
echo Starting Polymarket Arbitrage Bot...
echo.
%PYTHON_CMD% main.py

REM Keep window open on error
if errorlevel 1 (
    echo.
    echo ========================================
    echo   ERROR OCCURRED
    echo ========================================
    echo.
    echo Check the error message above
    echo.
    pause
)
