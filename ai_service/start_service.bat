@echo off
REM Startup script for AI service (Windows)

echo ==========================================
echo AGBOT AI Pest Detection Service
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Start the service
echo.
echo Starting AI service on http://localhost:8000
echo Press Ctrl+C to stop
echo.
python main.py
