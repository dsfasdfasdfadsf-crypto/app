@echo off
title Polymarket Arbitrage Bot
cd /d "%~dp0"

REM Find Python command
set PYTHON_CMD=python3
python3 --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=python
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python not found! Please run INSTALLER.py first.
        pause
        exit /b 1
    )
)

REM Launch app
echo ⚡ Starting Polymarket Arbitrage Bot...
%PYTHON_CMD% main.py

REM Keep window open on error
if errorlevel 1 (
    echo.
    echo ❌ Error occurred - check the message above
    pause
)
