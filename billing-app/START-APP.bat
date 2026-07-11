@echo off
title Shop Billing App
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo  Python is not installed on this computer.
    echo  Please install it first from:  https://www.python.org/downloads/
    echo  IMPORTANT: tick "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Installing required packages (only slow the first time)...
python -m pip install -r requirements.txt --quiet

echo.
echo  Starting Shop Billing App...
echo  Keep this window OPEN while using the app.
echo.
start "" http://localhost:5000
python app.py
pause
