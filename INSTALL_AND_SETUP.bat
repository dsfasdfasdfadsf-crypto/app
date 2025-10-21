@echo off
REM ============================================
REM  Polymarket Arbitrage Bot - Installer
REM  Double-click to install and run!
REM ============================================

REM Check for admin rights and request elevation if needed
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title Polymarket Arbitrage Bot - Installation
color 0A

echo.
echo ========================================
echo   POLYMARKET ARBITRAGE BOT
echo   One-Click Installer
echo ========================================
echo.
timeout /t 2 /nobreak >nul

REM ============================================
REM Check Python
REM ============================================
echo [1/4] Checking Python...
echo.

REM Try python3 first, then python
set PYTHON_CMD=
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    echo [OK] Python3 found!
    python3 --version
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
        echo [OK] Python found!
        python --version
    ) else (
        echo [X] Python NOT installed!
        echo.
        echo Opening download page...
        echo.
        echo Please:
        echo  1. Download Python 3.8+
        echo  2. CHECK "Add Python to PATH"
        echo  3. Install Python
        echo  4. Run this installer again
        echo.
        start https://www.python.org/downloads/
        pause
        exit /b 1
    )
)
echo.

REM ============================================
REM Upgrade pip
REM ============================================
echo [2/4] Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip --quiet
echo [OK] Ready!
echo.

REM ============================================
REM Install packages
REM ============================================
echo [3/4] Installing packages (~50MB, 1-2 min)...
echo.
echo Installing core dependencies (demo mode)...
echo.

cd polymarket-arbitrage-bot\app
%PYTHON_CMD% -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [!] Trying individual install...
    %PYTHON_CMD% -m pip install PyQt6
    %PYTHON_CMD% -m pip install aiohttp
    %PYTHON_CMD% -m pip install pyyaml
    %PYTHON_CMD% -m pip install python-dotenv
)

cd ..\..

echo.
echo [OK] Packages installed!
echo.

REM ============================================
REM Create Desktop Shortcut
REM ============================================
echo [4/4] Creating desktop shortcut...
echo.

set SCRIPT_DIR=%~dp0

REM Create VBScript for shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Polymarket Arbitrage Bot.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%SCRIPT_DIR%polymarket-arbitrage-bot\app\launcher.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%SCRIPT_DIR%polymarket-arbitrage-bot\app" >> CreateShortcut.vbs
echo oLink.Description = "Polymarket Arbitrage Bot" >> CreateShortcut.vbs
echo oLink.IconLocation = "C:\Windows\System32\shell32.dll,21" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript CreateShortcut.vbs >nul
del CreateShortcut.vbs

echo [OK] Desktop shortcut created!
echo.

REM ============================================
REM Done!
REM ============================================
echo.
echo ========================================
echo   INSTALLATION COMPLETE!
echo ========================================
echo.
echo Desktop shortcut: "Polymarket Arbitrage Bot"
echo.
echo Or run: polymarket-arbitrage-bot\app\launcher.bat
echo.
echo ========================================
echo.
echo Launching in 3 seconds...
timeout /t 3 /nobreak >nul

start "" "%SCRIPT_DIR%polymarket-arbitrage-bot\app\launcher.bat"

timeout /t 2 /nobreak >nul
exit
