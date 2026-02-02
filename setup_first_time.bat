@echo off
title LagSense - First Time Setup
color 0B

echo.
echo =========================================
echo    LAGSENSE - FIRST TIME SETUP
echo =========================================
echo.
echo This script will:
echo   1. Create virtual environments
echo   2. Install all dependencies
echo   3. Setup the database
echo.
echo This may take 5-10 minutes...
echo.
pause

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ first
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js 16+ first
    pause
    exit /b 1
)

echo.
echo ========================================
echo  STEP 1/3: Backend Setup
echo ========================================
cd backend

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing backend dependencies...
pip install fastapi uvicorn[standard] sqlalchemy pydantic pydantic[email] passlib[argon2] argon2-cffi python-multipart
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

echo Backend setup complete!
cd ..

echo.
echo ========================================
echo  STEP 2/3: Agent Setup
echo ========================================
cd agent

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing agent dependencies...
pip install psutil==5.9.8 requests==2.31.0 pywin32==311 python-dotenv==1.0.0 numpy==2.3.5 win10toast==0.9
if errorlevel 1 (
    echo ERROR: Failed to install agent dependencies
    pause
    exit /b 1
)

echo Agent setup complete!
cd ..

echo.
echo ========================================
echo  STEP 3/3: Electron Setup
echo ========================================
cd electron

echo Installing node modules...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install node modules
    pause
    exit /b 1
)

echo Electron setup complete!
cd ..

echo.
echo =========================================
echo    SETUP COMPLETE!
echo =========================================
echo.
echo You can now run LagSense using:
echo   - start_lagsense.bat (automated)
echo   - OR manually in VS Code terminals
echo.
echo Next steps:
echo   1. Apply the fixes from QUICK_FIXES.md
echo   2. Run start_lagsense.bat
echo   3. Open http://localhost:8000 to verify backend
echo   4. Register a new account in the app
echo.
pause
