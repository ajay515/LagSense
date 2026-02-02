@echo off
title LagSense Launcher
color 0A

echo.
echo ========================================
echo    LAGSENSE - STARTUP LAUNCHER
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "backend" (
    echo ERROR: backend folder not found!
    echo Please run this script from the LagSense root folder
    pause
    exit /b 1
)

if not exist "agent" (
    echo ERROR: agent folder not found!
    echo Please run this script from the LagSense root folder
    pause
    exit /b 1
)

if not exist "electron" (
    echo ERROR: electron folder not found!
    echo Please run this script from the LagSense root folder
    pause
    exit /b 1
)

echo [1/3] Starting Backend Server...
start "LagSense Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 5 /nobreak >nul

echo [2/3] Starting Background Agent...
start "LagSense Agent" cmd /k "cd agent && venv\Scripts\activate && python lagsense_background_agent.py"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Electron App...
cd electron
call npm start

echo.
echo ========================================
echo    All services started!
echo ========================================
pause
